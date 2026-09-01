"""The learner model: what is believed, and what the learner is told.

Two claims are load-bearing. A mastery number has to mean "probably knows this
rule" rather than "got the last few right", which is why the guess rate is per
item. And an error count has to be divided by the chances to make that error,
which is why every response records the rules the form exercised.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from langram import bkt
from langram.api.deps import get_language, get_session
from langram.api.main import create_app
from langram.api.security import read_item_token
from langram.db.models import Base, Concept, Exercise, Response, UserConceptMastery
from langram.db.seed import seed
from langram.generators import assemble
from langram.generators._common import broken_variants
from langram.loader import load_language
from langram.skills import (
    ALTERNATION, BACKNESS, BUFFER, DELETION, ROUNDING, describe, skills_for,
)
from langram.tutor import MASTERY_THRESHOLD, MIN_OPPORTUNITIES, ExerciseSpec


@pytest.fixture(scope="module")
def language():
    return load_language("tr")


class TestBkt:
    def test_correct_raises_and_wrong_lowers(self):
        start = bkt.update(None, True, option_count=None)
        higher = bkt.update(start.to_dict(), True, option_count=None)
        lower = bkt.update(start.to_dict(), False, option_count=None)
        assert higher.p_known > start.p_known > lower.p_known

    def test_a_guessable_item_is_worth_less(self):
        """Getting a two option judgement right says much less than typing the
        form, and the model has to know the difference."""
        typed = bkt.update(None, True, option_count=None)
        four = bkt.update(None, True, option_count=4)
        two = bkt.update(None, True, option_count=2)
        assert typed.p_known > four.p_known > two.p_known

    def test_counts_are_kept(self):
        state = None
        for correct in (True, False, True):
            state = bkt.update(state.to_dict() if state else None, correct)
        assert state.opportunities == 3
        assert state.correct == 2

    def test_state_round_trips(self):
        """Stored to six decimals on purpose: the extra digits are noise in a
        model whose parameters are not fitted yet."""
        state = bkt.update(None, True)
        restored = bkt.State.from_dict(state.to_dict())
        assert restored.p_known == pytest.approx(state.p_known, abs=1e-6)
        assert (restored.opportunities, restored.correct) == (state.opportunities, state.correct)

    def test_a_corrupt_state_does_not_crash_a_session(self):
        assert bkt.State.from_dict({"p_known": "nonsense"}).p_known == bkt.DEFAULTS.prior
        assert bkt.State.from_dict(None).p_known == bkt.DEFAULTS.prior

    def test_mastery_is_never_absorbing(self):
        """Certainty would be permanent: at exactly 1 the posterior stays 1
        whatever happens next, so a learner could never be shown to have lost
        something they once had."""
        state = None
        for _ in range(40):
            state = bkt.update(state.to_dict() if state else None, True, option_count=None)
        assert state.p_known < 1.0

        peak = state.p_known
        for _ in range(4):
            state = bkt.update(state.to_dict(), False, option_count=None)
        assert state.p_known < peak / 2

    def test_one_slip_does_not_undo_mastery(self):
        """The other half of the same claim: a single wrong answer after a long
        run is a slip, not evidence of forgetting."""
        state = None
        for _ in range(20):
            state = bkt.update(state.to_dict() if state else None, True, option_count=None)
        before = state.p_known
        after = bkt.update(state.to_dict(), False, option_count=None).p_known
        assert after > before * 0.95


class TestSkillOpportunities:
    def test_a_form_exercises_what_the_engine_did_to_build_it(self, language):
        assert skills_for(language, "araba", ["PL"]) == (BACKNESS,)
        assert set(skills_for(language, "doktor", ["POSS1SG"])) == {BACKNESS, ROUNDING}
        assert ALTERNATION in skills_for(language, "kitap", ["POSS1SG"])
        assert DELETION in skills_for(language, "burun", ["POSS3SG"])
        assert BUFFER in skills_for(language, "araba", ["ACC"])

    def test_twofold_harmony_is_not_a_rounding_opportunity(self, language):
        """The plural cannot test rounding, so a learner who has only done
        plurals should not be told anything about their rounding."""
        assert ROUNDING not in skills_for(language, "araba", ["PL"])

    def test_an_unknown_form_is_not_an_opportunity_for_anything(self, language):
        assert skills_for(language, "not-a-word", ["PL"]) == ()

    def test_summaries_are_actionable_rather_than_numeric(self):
        assert "reliably" in describe(BACKNESS, 0.95, 20)
        weak = describe(ROUNDING, 0.6, 20)
        assert "60 percent" in weak
        assert "rounding" in weak
        assert "few" in describe(BACKNESS, 0.5, 2), "a rate from two attempts is noise"


@pytest.fixture(scope="module")
def factory(tmp_path_factory):
    path = tmp_path_factory.mktemp("progress") / "test.db"
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    maker = sessionmaker(engine, expire_on_commit=False)
    with maker() as s:
        seed(s)
        s.commit()
    return maker


@pytest.fixture
def learner(factory):
    app = create_app()

    def _session():
        with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _session
    with TestClient(app) as client:
        token = client.post("/api/auth/guest").json()
        client.headers["Authorization"] = f"Bearer {token['access_token']}"
        client.user_id = token["user_id"]
        yield client


def _answer_one(learner, factory, correct: bool):
    """Answer the next item, right or plausibly wrong.

    Plausibly matters: typing nonsense produces an error no diagnosis can pin on
    a rule, which is exactly the case the rates deliberately exclude. A learner's
    wrong answers are real forms built by the wrong rule, so the test uses those.
    """
    item = learner.get("/api/session/next").json()
    token = read_item_token(item["item_token"])
    language = get_language()
    with factory() as s:
        built = assemble(ExerciseSpec.of(s.get(Exercise, token["e"]),
                                         s.get(Concept, token["c"])),
                         language, token["s"])

    answer = built.answer
    if not correct:
        options = [o for o in (built.payload.get("options") or [])
                   if isinstance(o, str) and o != built.answer]
        if options:
            answer = options[0]
        elif built.lemma:
            broken = broken_variants(language, language.lexeme(built.lemma),
                                     list(built.suffixes))
            answer = next(iter(broken.values()), built.answer + "zz")
        else:
            answer = built.answer + "zz"

    return learner.post("/api/session/answer", json={
        "item_token": item["item_token"], "answer": answer,
        "attempt": 4 if not correct else 1,
    }).json()


class TestUnlocking:
    def test_a_new_learner_only_meets_the_first_unit(self, learner):
        units = {learner.get("/api/session/next").json()["unit_id"] for _ in range(12)}
        assert units == {"unit-01-vowel-harmony"}

    def test_a_later_unit_opens_once_its_prerequisite_is_known(self, learner, factory):
        """Sequencing is the point of the prerequisites in the content: a
        learner should not meet unit two before unit one is finished."""
        with factory() as s:
            first = s.scalars(
                select(Concept).join(Concept.unit).where(Concept.unit_id == "unit-01-vowel-harmony")
            ).all()
            for concept in first:
                s.add(UserConceptMastery(user_id=learner.user_id, concept_id=concept.id,
                                         ability_estimate=0.95,
                                         state={"p_known": 0.95, "opportunities": 9, "correct": 9}))
            s.commit()

        units = {learner.get("/api/session/next").json()["unit_id"] for _ in range(12)}
        assert "unit-02-predication" in units
        assert "unit-03-possession" not in units, "unit three still waits for unit two"


class TestProgressReport:
    def test_an_empty_report_says_so(self, learner):
        report = learner.get("/api/progress").json()
        assert report["answered"] == 0
        assert report["accuracy"] is None
        assert "Nothing" in report["headline"]
        # Concepts are listed before anything is answered, so the curriculum is
        # visible rather than revealed.
        assert len(report["concepts"]) >= 8
        assert all(c["status"] == "not started" for c in report["concepts"])

    def test_it_reports_rules_rather_than_a_score(self, learner, factory):
        # Enough wrong answers for a rule to clear the threshold below which a
        # rate is noise. Backness is exercised by almost every form, so it is
        # the one that gets there first.
        for _ in range(14):
            _answer_one(learner, factory, correct=False)
        report = learner.get("/api/progress").json()

        assert report["answered"] >= 6
        assert report["skills"], "wrong answers should name the rules behind them"
        weakest = report["skills"][0]
        assert weakest["opportunities"] > 0
        assert weakest["errors"] > 0
        assert weakest["label"] in report["headline"] or "percent" in report["headline"]
        assert weakest["accuracy"] <= 1.0

    def test_every_rate_has_its_opportunities(self, learner, factory):
        _answer_one(learner, factory, correct=True)
        report = learner.get("/api/progress").json()
        for skill in report["skills"]:
            assert skill["opportunities"] >= skill["errors"]
            if skill["accuracy"] is not None:
                assert 0.0 <= skill["accuracy"] <= 1.0

    def test_concepts_carry_why_they_are_hard(self, learner):
        report = learner.get("/api/progress").json()
        assert all(c["why_hard"] for c in report["concepts"])

    def test_answering_moves_a_concept_off_not_started(self, learner, factory):
        _answer_one(learner, factory, correct=True)
        report = learner.get("/api/progress").json()
        started = [c for c in report["concepts"] if c["status"] != "not started"]
        assert started
        assert all(0.0 <= c["p_known"] <= 1.0 for c in report["concepts"])

    def test_mastery_is_explained_rather_than_presented_as_a_score(self, learner):
        note = learner.get("/api/progress").json()["note"]
        assert "probability" in note
        assert "guessed" in note

    def test_a_response_records_its_opportunities(self, learner, factory):
        _answer_one(learner, factory, correct=True)
        with factory() as s:
            latest = s.scalars(select(Response).order_by(Response.id.desc())).first()
        assert latest.skills, "a response with no opportunities cannot be a rate"


class TestMasteryNeedsEvidence:
    def test_a_high_probability_on_two_answers_is_not_mastery(self, learner, factory):
        """Five correct answers on two option items is five coin flips. The
        probability can look convincing long before the evidence does."""
        with factory() as s:
            s.add(UserConceptMastery(user_id=learner.user_id, concept_id="stem-alternation",
                                     ability_estimate=0.95,
                                     state={"p_known": 0.95, "opportunities": 2, "correct": 2}))
            s.commit()
        report = learner.get("/api/progress").json()
        entry = next(c for c in report["concepts"] if c["id"] == "stem-alternation")
        assert entry["status"] == "learning"

    def test_the_note_says_what_mastery_requires(self, learner):
        note = learner.get("/api/progress").json()["note"]
        assert str(MIN_OPPORTUNITIES) in note


class TestThresholdIsShared:
    def test_the_report_and_the_tutor_agree(self, learner, factory):
        """A concept called known in the report must be one the tutor stops
        serving as new material, or the two disagree in front of the learner."""
        with factory() as s:
            s.add(UserConceptMastery(user_id=learner.user_id, concept_id="buffer-segments",
                                     ability_estimate=MASTERY_THRESHOLD,
                                     state={"p_known": MASTERY_THRESHOLD,
                                            "opportunities": MIN_OPPORTUNITIES,
                                            "correct": MIN_OPPORTUNITIES}))
            s.commit()
        report = learner.get("/api/progress").json()
        entry = next(c for c in report["concepts"] if c["id"] == "buffer-segments")
        assert entry["status"] == "known"
