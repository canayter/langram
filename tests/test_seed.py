"""Seeding tests.

The load-bearing one is test_learner_state_survives_a_reseed. The brief's
central architectural claim is that content is disposable and learner state is
not, and that claim is only true if re-running the seed cannot touch a response,
a review card or a mastery estimate.

SQLite has foreign key enforcement off by default, which would make that test
pass for the wrong reason, so it is switched on here.
"""
import shutil

import pytest
import sqlalchemy as sa
import yaml
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from langram.db.models import (
    Base, Concept, Exercise, Lexeme, Response, ReviewCard, Suffix, Unit,
    User, UserConceptMastery,
)
from langram.db.seed import seed
from langram.loader import CONTENT_ROOT


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def content(tmp_path):
    dest = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, dest)
    return dest


def _count(session, model):
    return session.scalar(select(func.count()).select_from(model))


class TestSeeding:
    def test_populates_every_content_table(self, session):
        counts = seed(session)
        for table in ("lexemes", "suffixes", "units", "concepts", "exercises"):
            assert counts[table] > 0, table
        assert _count(session, Unit) == counts["units"]
        assert _count(session, Exercise) == counts["exercises"]

    def test_counts_match_the_content_files(self, session):
        seed(session)
        with (CONTENT_ROOT / "l2" / "tr" / "lexicon" / "lexemes.yaml").open(encoding="utf-8") as fh:
            lexemes = yaml.safe_load(fh)
        assert _count(session, Lexeme) == len(lexemes)

    def test_a_unit_arrives_whole(self, session):
        seed(session)
        unit = session.get(Unit, "unit-01-vowel-harmony")
        assert unit.order == 1
        assert "harmony" in unit.title.lower()
        assert "vanpatten-input-processing" in unit.research_refs
        assert len(unit.concepts) >= 1

    def test_exercise_ids_are_qualified_by_concept(self, session):
        seed(session)
        ids = session.scalars(select(Exercise.id)).all()
        assert all(":" in i for i in ids)
        assert len(set(ids)) == len(ids)

    def test_review_flags_are_queryable(self, session):
        """The point of storing needs_review is being able to ask for the list."""
        seed(session)
        flagged = session.scalars(select(Lexeme).where(Lexeme.needs_review.is_(True))).all()
        assert flagged, "some lexemes are flagged in content, so some must be flagged here"
        assert all(lx.properties["review"] for lx in flagged)

    def test_is_idempotent(self, session):
        first = seed(session)
        before = _count(session, Exercise)
        second = seed(session)
        assert first == second
        assert _count(session, Exercise) == before


class TestContentStateSplit:
    def test_learner_state_survives_a_reseed(self, session):
        seed(session)
        session.commit()

        exercise_id = session.scalars(select(Exercise.id)).first()
        concept_id = session.scalars(select(Concept.id)).first()
        user = User(email="learner@example.com", password_hash="x")
        session.add(user)
        session.flush()
        session.add_all([
            Response(user_id=user.id, exercise_id=exercise_id, concept_id=concept_id,
                     correct=False, latency_ms=2400, raw_answer="arabaler",
                     error_tags=["harmony_backness"]),
            UserConceptMastery(user_id=user.id, concept_id=concept_id, ability_estimate=0.42),
            ReviewCard(user_id=user.id, item_type="lexeme", item_ref="kitap",
                       fsrs_state={"stability": 3.1}, due_at=sa.func.now()),
        ])
        session.commit()

        seed(session)
        session.commit()

        assert _count(session, User) == 1
        response = session.scalars(select(Response)).one()
        assert response.exercise_id == exercise_id, "reseeding detached a response from its exercise"
        assert response.latency_ms == 2400
        assert response.error_tags == ["harmony_backness"]
        assert session.scalars(select(UserConceptMastery)).one().ability_estimate == 0.42
        assert session.scalars(select(ReviewCard)).one().fsrs_state == {"stability": 3.1}

    def test_retired_content_is_pruned(self, session, content):
        seed(session, content)
        session.commit()
        before = _count(session, Unit)

        (content / "l2" / "tr" / "curriculum" / "unit-03-possession.yaml").unlink()
        counts = seed(session, content)
        session.commit()

        assert _count(session, Unit) == before - 1
        assert session.get(Unit, "unit-03-possession") is None
        assert counts.get("pruned", 0) > 0
        # Concepts and exercises go with it rather than dangling.
        assert session.get(Concept, "possessive-suffixes") is None

    def test_edited_content_is_updated_in_place(self, session, content):
        seed(session, content)
        session.commit()

        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        with path.open(encoding="utf-8") as fh:
            unit = yaml.safe_load(fh)
        unit["title"] = "Vowel harmony, revised"
        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(unit, fh, allow_unicode=True, sort_keys=False)

        seed(session, content)
        session.commit()

        assert session.get(Unit, "unit-01-vowel-harmony").title == "Vowel harmony, revised"
        assert _count(session, Unit) == 9


class TestSchemaPortability:
    def test_no_type_is_postgres_only(self):
        """SQLite is a local convenience; Postgres is the target. Anything that
        only compiles on one of them would be found far too late."""
        from sqlalchemy.dialects import postgresql, sqlite
        for dialect in (postgresql.dialect(), sqlite.dialect()):
            for table in Base.metadata.sorted_tables:
                sa.schema.CreateTable(table).compile(dialect=dialect)
