"""The learning loop, end to end.

The two tests that matter most are test_answer_never_leaves_the_server, because
an exercise whose answer is in the payload is not an exercise, and
test_feedback_escalates, because prompting before recasting is the pedagogy the
whole app claims to implement.
"""
import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from langram.api.deps import get_language, get_session
from langram.api.main import create_app
from langram.api.security import read_item_token
from langram.db.models import Base, Concept, Exercise, Response, ReviewCard, User
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
    token = client.post("/api/auth/guest").json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def _first_item(learner):
    r = learner.get("/api/session/next")
    assert r.status_code == 200, r.text
    return r.json()


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
        assert [u["order"] for u in units] == [1, 2, 3]
        first = units[0]
        assert first["research_refs"], "a unit with no citations should not exist"
        assert len(first["rationale"]) > 40
        assert first["concepts"][0]["why_hard"]


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

    def test_interleaving_avoids_the_concept_just_seen(self, learner):
        first = _first_item(learner)
        seen = first["concept_id"]
        following = learner.get(f"/api/session/next?after={seen}").json()
        assert following["concept_id"] != seen


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
