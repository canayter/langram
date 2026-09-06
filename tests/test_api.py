"""The learning loop, end to end.

The two tests that matter most are test_answer_never_leaves_the_server, because
an exercise whose answer is in the payload is not an exercise, and
test_feedback_escalates, because prompting before recasting is the pedagogy the
whole app claims to implement.
"""
import datetime as dt
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from langram.api.deps import get_language, get_session
from langram.api.main import create_app
from langram.api.security import read_item_token
from langram import bkt
from langram.db.models import (
    Base, Concept, Exercise, Response, ReviewCard, User, UserConceptMastery,
)
from langram.db.seed import seed
from langram.generators import assemble
from langram.tutor import ExerciseSpec


@pytest.fixture(scope="module")
def factory(tmp_path_factory):
    path = tmp_path_factory.mktemp("api") / "test.db"
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
def client(factory):
    app = create_app()

    def _session():
        with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _session
    with TestClient(app) as c:
        yield c


@pytest.fixture
def learner(client):
    token = client.post("/api/auth/guest").json()
    client.headers["Authorization"] = f"Bearer {token['access_token']}"
    client.user_id = token["user_id"]
    return client


def _first_item(learner):
    """The first real exercise, skipping over a concept's one-time intro.

    Mirrors exactly what the frontend does: an intro is dismissed with a
    click that calls next() again, never with a POST to /answer.
    """
    for _ in range(10):
        r = learner.get("/api/session/next")
        assert r.status_code == 200, r.text
        item = r.json()
        if item["payload"]["kind"] != "intro":
            return item
    raise AssertionError("stuck behind intros")


def _answer(learner, item, option, attempt=1, latency=None):
    body = {"item_token": item["item_token"], "answer": option, "attempt": attempt}
    if latency is not None:
        body["latency_ms"] = latency
    return learner.post("/api/session/answer", json=body).json()


def _rebuild(factory, item):
    """The item as the server sees it, so a test can answer any kind correctly.

    Uses the same token and the same generator the endpoint uses, rather than
    guessing from the payload, which would only work for multiple choice.
    """
    token = read_item_token(item["item_token"])
    with factory() as s:
        exercise = s.get(Exercise, token["e"])
        concept = s.get(Concept, token["c"])
        return assemble(ExerciseSpec.of(exercise, concept), get_language(), token["s"])


def _right(factory, item):
    return _rebuild(factory, item).answer


def _wrong(factory, item):
    """An answer that is definitely not the right one."""
    correct = _right(factory, item)
    options = item["payload"].get("options") or []
    if options and isinstance(options[0], dict):
        options = [o["id"] for o in options]
    for option in options:
        if option != correct:
            return option
    return correct + "x"


class TestAuth:
    def test_health(self, client):
        assert client.get("/api/health").json() == {"status": "ok"}

    def test_register_then_login(self, client):
        created = client.post("/api/auth/register",
                              json={"email": "a@example.com", "password": "correct horse"})
        assert created.status_code == 201, created.text
        assert created.json()["is_guest"] is False

        ok = client.post("/api/auth/login",
                         json={"email": "a@example.com", "password": "correct horse"})
        assert ok.status_code == 200
        assert ok.json()["access_token"]

    def test_duplicate_email_is_refused(self, client):
        body = {"email": "dupe@example.com", "password": "correct horse"}
        assert client.post("/api/auth/register", json=body).status_code == 201
        assert client.post("/api/auth/register", json=body).status_code == 409

    def test_wrong_password_is_refused(self, client):
        client.post("/api/auth/register",
                    json={"email": "b@example.com", "password": "correct horse"})
        bad = client.post("/api/auth/login",
                          json={"email": "b@example.com", "password": "wrong horse"})
        assert bad.status_code == 401

    def test_password_is_never_stored_in_the_clear(self, client, factory):
        client.post("/api/auth/register",
                    json={"email": "c@example.com", "password": "correct horse"})
        with factory() as s:
            user = s.scalars(select(User).where(User.email == "c@example.com")).one()
        assert "correct horse" not in user.password_hash
        assert user.password_hash.startswith("$argon2")

    def test_guest_can_claim_an_account_and_keep_their_id(self, client):
        guest = client.post("/api/auth/guest").json()
        assert guest["is_guest"] is True
        client.headers["Authorization"] = f"Bearer {guest['access_token']}"
        claimed = client.post("/api/auth/claim",
                              json={"email": "claimed@example.com", "password": "correct horse"})
        assert claimed.status_code == 200
        assert claimed.json()["user_id"] == guest["user_id"]
        assert claimed.json()["is_guest"] is False

    def test_the_loop_needs_an_account(self, client):
        assert client.get("/api/session/next").status_code == 401


class TestCurriculum:
    def test_units_are_public_and_carry_their_rationale(self, client):
        units = client.get("/api/units").json()
        assert [u["order"] for u in units] == [1, 2, 3, 4, 5, 6, 7]
        first = units[0]
        assert first["research_refs"], "a unit with no citations should not exist"
        assert len(first["rationale"]) > 40
        assert first["concepts"][0]["why_hard"]

    def test_fourfold_harmony_recurs_in_every_later_i_type_concept(self, client):
        """The one concrete recurs_in claim in this curriculum: every later
        concept whose suffixes are I-type genuinely re-tests fourfold
        harmony as a side effect of teaching something else."""
        units = client.get("/api/units").json()
        by_id = {c["id"]: c for u in units for c in u["concepts"]}
        assert set(by_id["fourfold-harmony"]["recurs_in"]) == {
            "predication-without-a-verb", "possessive-suffixes",
            "buffer-segments", "stem-alternation", "verb-person-marking",
        }

    def test_bibliography_is_public_and_matches_what_units_cite(self, client):
        """WhyPanel used to be able to show only the bare key from
        research_refs, never the author or the actual claim, because nothing
        exposed content/bibliography.yaml at all. Every ref a unit names has
        to resolve to a real entry here, or the resolution silently drops it."""
        units = client.get("/api/units").json()
        bibliography = client.get("/api/bibliography").json()
        assert bibliography
        keys = {entry["key"] for entry in bibliography}
        for unit in units:
            for ref in unit["research_refs"]:
                assert ref in keys, ref
        first = bibliography[0]
        assert first["claim"]
        assert first["status"] in ("verified", "needs_citation")


class TestServedWordInfo:
    """A word-info panel is meant to support an item, not answer it. Two
    generators break that if handled the same as every other: vocab_recognition
    IS "what does this word mean", and form_meaning_match's buffer mode always
    names the correct one of its three word options as the item's own lemma."""

    @staticmethod
    @pytest.fixture(scope="class")
    def language():
        from langram.loader import load_language
        return load_language("tr")

    def test_vocab_recognition_gets_no_panel(self, language):
        from langram.api.routers.session import _served_word_info
        item = SimpleNamespace(generator="vocab_recognition", lemma="ev", extra={})
        assert _served_word_info(item, language) is None

    def test_buffer_mode_gets_no_panel(self, language):
        from langram.api.routers.session import _served_word_info
        item = SimpleNamespace(generator="form_meaning_match", lemma="kutu",
                               extra={"mode": "buffer"})
        assert _served_word_info(item, language) is None

    def test_other_form_meaning_match_modes_still_get_one(self, language):
        from langram.api.routers.session import _served_word_info
        for mode in ("gloss", "trigger"):
            item = SimpleNamespace(generator="form_meaning_match", lemma="ev",
                                   extra={"mode": mode})
            info = _served_word_info(item, language)
            assert info is not None, mode
            assert info.lemma == "ev"

    def test_an_ordinary_generator_still_gets_one(self, language):
        from langram.api.routers.session import _served_word_info
        item = SimpleNamespace(generator="type_the_form", lemma="ev", extra={})
        info = _served_word_info(item, language)
        assert info is not None
        assert info.lemma == "ev"


class TestTheLoop:
    def test_serves_an_item(self, learner):
        item = _first_item(learner)
        assert item["prompt"]
        assert item["payload"]["kind"]
        assert item["unit_id"] == "unit-01-vowel-harmony"

    def test_comprehension_comes_before_production(self, learner):
        """Input before output is a commitment, so the first thing a learner
        meets must not ask them to produce anything."""
        item = _first_item(learner)
        assert item["stage"] == "structured_input"

    def test_answer_never_leaves_the_server(self, learner, factory):
        item = _first_item(learner)
        assert "answer" not in item
        assert "derivation" not in item
        payload = item["payload"]
        assert "answer" not in payload
        # The right option is necessarily among them; nothing may say which.
        assert not any(k in payload for k in ("correct", "correct_index", "is_correct"))
        assert _right(factory, item), "the server can still work out the answer"

    def test_a_correct_answer_returns_the_derivation(self, learner, factory):
        item = _first_item(learner)
        good = _answer(learner, item, _right(factory, item), latency=1500)
        assert good["correct"]
        assert good["derivation"], "the trace is the product, not a debug aid"
        assert good["due_at"], "a correct answer should schedule a review"
        assert 0 < good["mastery"] <= 1

    def test_a_wrong_answer_is_classified_by_cause(self, learner, factory):
        item = _first_item(learner)
        result = _answer(learner, item, _wrong(factory, item), attempt=1)
        assert not result["correct"]
        assert result["tags"], "a wrong answer should name the rule that was missed"
        assert result["kind"] == "clarification"

    def test_feedback_escalates(self, learner, factory):
        """Prompts before recasts: three pushes before the answer is handed over."""
        item = _first_item(learner)
        wrong = _wrong(factory, item)
        kinds = [_answer(learner, item, wrong, attempt=n)["kind"] for n in (1, 2, 3, 4)]
        assert kinds == ["clarification", "metalinguistic", "elicitation", "explicit"]

        final = _answer(learner, item, wrong, attempt=4)
        assert final["answer"], "the last rung gives the form"
        assert final["derivation"]

    def test_responses_are_persisted_with_latency(self, learner, factory):
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item), latency=2750)
        with factory() as s:
            row = s.scalars(select(Response).order_by(Response.id.desc())).first()
        assert row.latency_ms == 2750
        assert row.raw_answer

    def test_a_settled_item_becomes_a_review_card(self, learner, factory):
        item = _first_item(learner)
        assert _answer(learner, item, _right(factory, item))["correct"]
        with factory() as s:
            cards = s.scalars(select(ReviewCard)).all()
        assert cards
        assert all(c.fsrs_state.get("stability") is not None for c in cards)
        # The spec is stored so the same item can come back on review.
        assert all(c.item_spec.get("lemma") for c in cards)

    def test_interleaving_avoids_the_concept_just_seen(self, learner, factory):
        """`after` reflects a settled item, the way the frontend sends it: only
        once a response has actually been recorded, which is also what takes a
        concept out of "just introduced, must be practiced next" priority.
        Passing `after` for an item nobody has actually answered is not a
        scenario the real app produces."""
        first = _first_item(learner)
        seen = first["concept_id"]
        assert _answer(learner, first, _right(factory, first))["correct"]
        following = learner.get(f"/api/session/next?after={seen}").json()
        assert following["concept_id"] != seen


class TestExplicitNavigation:
    """?concept=... lets a learner jump straight to a concept by id, on
    purpose bypassing everything next_item() otherwise decides for them:
    due reviews, unit prerequisites, mastery, interleaving. Free-roam by
    design -- a concept several units ahead of anything the learner has
    touched is reachable, not just concepts already unlocked."""

    def test_jumps_straight_to_a_concept_never_unlocked(self, learner):
        item = learner.get("/api/session/next?concept=verb-person-marking").json()
        assert item["concept_id"] == "verb-person-marking"
        assert item["unit_id"] == "unit-05-present-tense"

    def test_shows_the_concept_intro_first_like_any_other_path(self, learner):
        item = learner.get("/api/session/next?concept=verb-person-marking").json()
        assert item["payload"]["kind"] == "intro"

    def test_stays_on_the_requested_concept_across_calls(self, learner):
        learner.get("/api/session/next?concept=verb-person-marking")  # dismiss the intro
        for _ in range(6):
            item = learner.get("/api/session/next?concept=verb-person-marking").json()
            assert item["concept_id"] == "verb-person-marking"

    def test_an_unknown_concept_id_is_rejected_not_silently_ignored(self, learner):
        r = learner.get("/api/session/next?concept=not-a-real-concept")
        assert r.status_code == 503


class TestRevisitingMasteredMaterial:
    """Regression for a real bug found by simulating a learner well past full
    mastery: next_item()'s "everything is mastered, revisit rather than
    stop" fallback used to pick by (unit, stage) tier exactly the way new
    material does, which collapses onto whichever two concepts share the
    very first tier -- each one's streak resets the moment the other gets a
    turn, so BLOCK_SIZE's cap never trips between just two, and every later
    concept is never served again."""

    def test_rotates_through_more_than_the_first_two_concepts(self, learner, factory):
        seen_concepts = set()
        for _ in range(220):
            item = _first_item(learner)
            seen_concepts.add(item["concept_id"])
            result = _answer(learner, item, _right(factory, item))
            assert result["correct"], result
        # The curriculum has 11 concepts; the bug capped this at exactly 2.
        assert len(seen_concepts) >= 8, seen_concepts


class TestStageProgression:
    """Regression for a real bug reported by a user and confirmed by
    simulation: unit 1's two concepts both start with structured_input, and
    interleaving-avoidance (never repeat the concept just answered) means
    they trade turns without either ever being answered twice in a row.
    BLOCK_SIZE's cap is the only other thing that can hand a turn to a
    later stage, and a streak that never reaches 2 never reaches 5 either,
    so a fresh learner was stuck seeing "Notice" for both concepts turns 4
    through 13 straight, in the exact simulation that first caught this."""

    def test_a_fresh_learner_reaches_production_within_a_reasonable_number_of_turns(
        self, learner, factory
    ):
        stages_seen = set()
        for _ in range(60):
            item = _first_item(learner)
            stages_seen.add(item["stage"])
            result = _answer(learner, item, _right(factory, item))
            assert result["correct"], result
        assert stages_seen - {"structured_input"}, (
            "60 turns in and nothing but structured_input was ever served"
        )


class TestConceptIntros:
    """Explicit information about a concept is a required stage before
    structured input, not an optional preamble (VanPatten, Processing
    Instruction). These tests are what test_comprehension_comes_before_production
    already assumes: that _first_item has something to skip."""

    def test_a_new_learner_meets_the_intro_before_any_exercise(self, learner):
        r = learner.get("/api/session/next")
        item = r.json()
        assert item["payload"]["kind"] == "intro"
        assert item["source"] == "intro"
        assert item["payload"]["text"]
        assert item["unit_id"] == "unit-01-vowel-harmony"
        # An intro is not answerable: no exercise or spec a wrong guess could hit.
        assert item["stage"] == "intro"

    def test_the_first_concept_introduced_is_always_the_units_first_one(self, client):
        """Unit 1 has two concepts that both start with a structured_input
        exercise, sharing tutor.next_item's first tier. Regression for a bug
        where the interleaving shuffle ran before the intro scan, so which
        concept's intro was served first was a coin flip: a new learner could
        meet harmony-is-not-spelling's intro, "The rule you just saw...",
        with nothing shown yet, because twofold-harmony had not been
        introduced first as the content assumes."""
        for _ in range(15):
            token = client.post("/api/auth/guest").json()
            r = client.get("/api/session/next", headers={"Authorization": f"Bearer {token['access_token']}"})
            item = r.json()
            assert item["payload"]["kind"] == "intro"
            assert item["concept_id"] == "twofold-harmony"

    def test_dismissing_the_intro_leads_to_a_real_exercise_for_the_same_concept(self, learner):
        intro = learner.get("/api/session/next").json()
        exercise = learner.get("/api/session/next").json()
        assert exercise["payload"]["kind"] != "intro"
        assert exercise["concept_id"] == intro["concept_id"]

    def test_the_intro_is_shown_exactly_once(self, learner, factory):
        intro = learner.get("/api/session/next").json()
        item = _first_item(learner)
        assert _answer(learner, item, _right(factory, item))["correct"]
        # Same concept could come up again on interleaving; its intro must not.
        for _ in range(6):
            nxt = learner.get(f"/api/session/next?after={item['concept_id']}").json()
            assert not (nxt["payload"]["kind"] == "intro"
                       and nxt["concept_id"] == intro["concept_id"])

    def test_an_intro_is_not_evidence_of_mastery(self, learner, factory):
        """Being shown the explanation is not the same as demonstrating the
        rule. The mastery row an intro creates must still read at the prior."""
        intro = learner.get("/api/session/next").json()
        with factory() as s:
            row = s.scalars(
                select(UserConceptMastery).where(
                    UserConceptMastery.user_id == learner.user_id,
                    UserConceptMastery.concept_id == intro["concept_id"],
                )
            ).first()
            assert row is not None
            assert row.ability_estimate == bkt.DEFAULTS.prior
            assert row.state.get("opportunities", 0) == 0
            assert row.intro_seen_at is not None

    def test_answering_afterwards_does_not_erase_that_the_intro_was_seen(self, learner, factory):
        """bkt.update() replaces `state` wholesale with only its own three
        keys, so intro_seen_at has to live outside `state` or a real answer
        would silently wipe it."""
        intro = learner.get("/api/session/next").json()
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item))
        with factory() as s:
            row = s.scalars(
                select(UserConceptMastery).where(
                    UserConceptMastery.user_id == learner.user_id,
                    UserConceptMastery.concept_id == intro["concept_id"],
                )
            ).first()
            assert row.intro_seen_at is not None
            assert row.state.get("opportunities", 0) >= 1

    def test_the_vowel_harmony_intro_carries_its_chart(self, learner):
        """twofold-harmony is guaranteed to be the first concept introduced
        (see the tutor.next_item ordering regression above), so this is a
        stable way to check visual_aid actually reaches the client."""
        item = learner.get("/api/session/next").json()
        assert item["payload"]["visual_aid"] == "vowel_chart"


class TestGamification:
    """Streaks and XP: playful, but pure bookkeeping. Nothing here reads or
    writes mastery or scheduling state, so these tests never touch bkt."""

    def test_a_correct_answer_awards_xp(self, learner, factory):
        item = _first_item(learner)
        result = _answer(learner, item, _right(factory, item))
        assert result["xp_awarded"] == 10
        assert result["xp_total"] == 10

    def test_a_wrong_answer_awards_no_xp(self, learner, factory):
        item = _first_item(learner)
        result = _answer(learner, item, _wrong(factory, item))
        assert result["xp_awarded"] == 0
        assert result["xp_total"] == 0

    def test_the_first_answer_of_the_day_extends_the_streak(self, learner, factory):
        item = _first_item(learner)
        result = _answer(learner, item, _right(factory, item))
        assert result["streak"] == 1
        assert result["streak_extended"] is True

    def test_a_second_answer_the_same_day_does_not_extend_the_streak(self, learner, factory):
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item))
        item2 = _first_item(learner)
        result = _answer(learner, item2, _right(factory, item2))
        assert result["streak"] == 1
        assert result["streak_extended"] is False

    def test_missing_a_day_resets_the_streak(self, learner, factory):
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item))
        with factory() as s:
            user = s.get(User, learner.user_id)
            user.last_practiced_on = user.last_practiced_on - dt.timedelta(days=3)
            user.current_streak = 5
            s.commit()
        item2 = _first_item(learner)
        result = _answer(learner, item2, _right(factory, item2))
        assert result["streak"] == 1
        assert result["streak_extended"] is True

    def test_session_next_reports_the_running_totals(self, learner, factory):
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item))
        nxt = learner.get(f"/api/session/next?after={item['concept_id']}").json()
        assert nxt["xp_total"] == 10
        assert nxt["streak"] == 1


class TestResetProgress:
    """No account recovery exists (guest only), so this is the only "start
    over" a learner has -- everything it touches has to actually go, not
    just the numbers a screen happens to show."""

    def test_wipes_responses_review_cards_and_mastery(self, learner, factory):
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item))
        with factory() as s:
            assert s.scalar(select(Response).where(Response.user_id == learner.user_id))
            assert s.scalar(select(ReviewCard).where(ReviewCard.user_id == learner.user_id))
            assert s.scalar(
                select(UserConceptMastery).where(UserConceptMastery.user_id == learner.user_id)
            )

        assert learner.delete("/api/progress").status_code == 204

        with factory() as s:
            assert not s.scalar(select(Response).where(Response.user_id == learner.user_id))
            assert not s.scalar(select(ReviewCard).where(ReviewCard.user_id == learner.user_id))
            assert not s.scalar(
                select(UserConceptMastery).where(UserConceptMastery.user_id == learner.user_id)
            )

    def test_resets_marks_and_chain_to_zero(self, learner, factory):
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item))

        assert learner.delete("/api/progress").status_code == 204

        with factory() as s:
            user = s.get(User, learner.user_id)
            assert user.xp == 0
            assert user.current_streak == 0
            assert user.longest_streak == 0
            assert user.last_practiced_on is None

    def test_practice_starts_over_cleanly_afterward(self, learner, factory):
        """A concept's intro is gated on UserConceptMastery.intro_seen_at;
        wiping that table has to bring intros back too, or a returning
        learner would see exercises for a concept they were never
        (re-)introduced to."""
        item = _first_item(learner)
        _answer(learner, item, _right(factory, item))
        assert learner.delete("/api/progress").status_code == 204

        first_after_reset = _first_item(learner)
        assert first_after_reset["unit_id"] == "unit-01-vowel-harmony"


class TestVowelChart:
    def test_the_vowel_inventory_matches_the_phonology_table(self, client):
        rows = client.get("/api/language/vowels").json()
        by_symbol = {v["symbol"]: v for v in rows}
        assert len(rows) == 8
        assert by_symbol["a"] == {"symbol": "a", "back": True, "rounded": False, "high": False}
        assert by_symbol["ü"] == {"symbol": "ü", "back": False, "rounded": True, "high": True}


class TestItemTokens:
    def test_a_tampered_token_is_refused(self, learner):
        item = _first_item(learner)
        forged = item["item_token"][:-4] + "AAAA"
        r = learner.post("/api/session/answer",
                         json={"item_token": forged, "answer": "x", "attempt": 1})
        assert r.status_code == 400

    def test_a_garbage_token_is_refused(self, learner):
        r = learner.post("/api/session/answer",
                         json={"item_token": "not.a.token", "answer": "x", "attempt": 1})
        assert r.status_code == 400
