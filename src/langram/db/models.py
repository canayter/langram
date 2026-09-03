"""Database schema.

The split the brief insists on: content tables are a projection of the YAML in
content/ and can be dropped and rebuilt from it at any time. Learner state
tables are the only place anything unrecoverable lives.

Postgres is the target. SQLite is fine for local work, so every type here is one
both understand, with JSONB used on Postgres where it helps.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# JSON everywhere, JSONB where the database can index it.
Json = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


# ── content: rebuilt from content/, never edited in place ────────────────────

class Lexeme(Base):
    __tablename__ = "lexemes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lemma: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    pos: Mapped[str] = mapped_column(String(16))
    gloss: Mapped[str] = mapped_column(Text, default="")
    frequency_band: Mapped[int | None] = mapped_column(Integer, nullable=True)
    properties: Mapped[dict] = mapped_column(Json, default=dict)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class Suffix(Base):
    __tablename__ = "suffixes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    archiphoneme_form: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(16), index=True)
    slot: Mapped[int] = mapped_column(Integer)
    properties: Mapped[dict] = mapped_column(Json, default=dict)


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order: Mapped[int] = mapped_column("order_index", Integer, unique=True)
    title: Mapped[str] = mapped_column(String(128))
    rationale: Mapped[str] = mapped_column(Text)
    research_refs: Mapped[list] = mapped_column(Json, default=list)
    prerequisites: Mapped[list] = mapped_column(Json, default=list)

    concepts: Mapped[list["Concept"]] = relationship(back_populates="unit", cascade="all, delete-orphan")


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(32))
    why_hard: Mapped[str] = mapped_column(Text)
    # Explicit information shown once before the learner meets any exercise
    # for this concept, so noticing the pattern is not the first thing being
    # asked of them. See tutor.py's intro gate.
    intro: Mapped[str] = mapped_column(Text, default="")
    teaches_suffixes: Mapped[list] = mapped_column(Json, default=list)

    unit: Mapped[Unit] = relationship(back_populates="concepts")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="concept", cascade="all, delete-orphan")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(24), index=True)
    generator: Mapped[str] = mapped_column(String(64))
    prompt: Mapped[str] = mapped_column(Text, default="")
    params: Mapped[dict] = mapped_column(Json, default=dict)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

    concept: Mapped[Concept] = relationship(back_populates="exercises")


# ── learner state: the only irreplaceable data here ──────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    native_language: Mapped[str] = mapped_column(String(8), default="en")
    settings: Mapped[dict] = mapped_column(Json, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserConceptMastery(Base):
    __tablename__ = "user_concept_mastery"
    __table_args__ = (UniqueConstraint("user_id", "concept_id", name="uq_user_concept"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    # The probability the learner knows this concept, from Bayesian Knowledge
    # Tracing. Kept as a plain float because everything reads it; the counts
    # behind it live in state.
    ability_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[dict] = mapped_column(Json, default=dict)
    # Set the moment a concept's intro is shown, independent of BKT state.
    # Kept as its own column rather than a key inside `state`, because
    # bkt.update() replaces `state` wholesale with only its own three keys on
    # every real answer, which would silently erase a flag stored inside it.
    intro_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ReviewCard(Base):
    __tablename__ = "review_cards"
    __table_args__ = (
        UniqueConstraint("user_id", "item_type", "item_ref", name="uq_user_item"),
        Index("ix_review_due", "user_id", "due_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    item_type: Mapped[str] = mapped_column(String(24))
    item_ref: Mapped[str] = mapped_column(String(96))
    # Enough to rebuild the exact item on review. item_ref identifies the card;
    # this says what to show. A judgement item, for instance, has to come back
    # with the same form and the same well formed or not, which the ref alone
    # cannot express.
    item_spec: Mapped[dict] = mapped_column(Json, default=dict)
    fsrs_state: Mapped[dict] = mapped_column(Json, default=dict)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True)
    concept_id: Mapped[str | None] = mapped_column(
        ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    correct: Mapped[bool] = mapped_column(Boolean)
    # Response time is a proxy for automatization and is logged from day one
    # even though nothing reads it yet.
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_answer: Mapped[str] = mapped_column(Text, default="")
    error_tags: Mapped[list] = mapped_column(Json, default=list)
    # The rules this form gave the learner a chance to apply. Errors divided by
    # opportunities is the only way an error count means anything.
    skills: Mapped[list] = mapped_column(Json, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Recording(Base):
    """Empty until the audio work starts. See docs/deferred-audio.md."""
    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_word: Mapped[str] = mapped_column(String(64))
    audio_url: Mapped[str] = mapped_column(Text)
    f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    f2: Mapped[float | None] = mapped_column(Float, nullable=True)
    f0: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PerceptionTrial(Base):
    """Empty until the audio work starts. See docs/deferred-audio.md."""
    __tablename__ = "perception_trials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    contrast_id: Mapped[str] = mapped_column(String(64), index=True)
    talker_id: Mapped[str] = mapped_column(String(64))
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


CONTENT_TABLES = (Exercise, Concept, Unit, Suffix, Lexeme)
