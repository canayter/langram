"""What to serve next.

Two rules do most of the work. Anything due for review comes first, because a
review is worth more than new material. Otherwise the earliest unfinished
concept wins, at the earliest stage that has a generator, so comprehension is
served before production wherever both exist.

Interleaving is deliberate: consecutive items avoid the concept just seen.
Blocked practice looks better inside a session and is worse a week later.
"""
from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db.models import Concept, Exercise, ReviewCard, Unit, UserConceptMastery
from .generators import REGISTRY, GenerationError, assemble, generate

# Comprehension before production. A concept's guided output is only reached
# when its structured input has no generator, which is temporary.
STAGE_ORDER = {"structured_input": 0, "guided_output": 1, "free_output": 2,
               "perception": 3, "review": 4}

MASTERY_THRESHOLD = 0.85


@dataclass(frozen=True)
class ExerciseSpec:
    """What a generator needs, without handing it a database row.

    teaches_suffixes comes from the concept, so an exercise that does not narrow
    the suffix set inherits it rather than repeating it.
    """
    id: str
    concept_id: str
    generator: str
    stage: str
    prompt: str
    params: dict
    teaches_suffixes: tuple[str, ...] = ()

    @classmethod
    def of(cls, exercise: Exercise, concept: Concept) -> "ExerciseSpec":
        return cls(
            id=exercise.id, concept_id=exercise.concept_id, generator=exercise.generator,
            stage=exercise.stage, prompt=exercise.prompt, params=dict(exercise.params or {}),
            teaches_suffixes=tuple(concept.teaches_suffixes or ()),
        )


@dataclass(frozen=True)
class Served:
    item: object                 # GeneratedItem
    source: str                  # "review" or "new"
    unit_id: str
    unit_title: str
    concept_name: str


def _ref(exercise_id: str, lemma: str, suffix_ids) -> str:
    return f"{exercise_id}|{lemma}|{'+'.join(suffix_ids)}"


def parse_ref(ref: str) -> tuple[str, str, list[str]]:
    exercise_id, lemma, suffixes = ref.split("|", 2)
    return exercise_id, lemma, [s for s in suffixes.split("+") if s]


def card_ref(item) -> str:
    return _ref(item.exercise_id, item.spec["lemma"], item.spec["suffixes"])


def _implemented(generator: str) -> bool:
    entry = REGISTRY.get(generator)
    return bool(entry and entry.implemented)


def _due_review(session: Session, user_id: int, now: dt.datetime) -> ReviewCard | None:
    return session.scalars(
        select(ReviewCard)
        .where(ReviewCard.user_id == user_id, ReviewCard.due_at <= now)
        .order_by(ReviewCard.due_at)
        .limit(1)
    ).first()


def next_item(session: Session, user_id: int, language, rng: random.Random | None = None,
              avoid_concept: str | None = None, now: dt.datetime | None = None) -> Served:
    rng = rng or random.Random()
    now = now or dt.datetime.now(dt.timezone.utc)

    due = _due_review(session, user_id, now)
    if due is not None:
        exercise_id, lemma, suffix_ids = parse_ref(due.item_ref)
        exercise = session.get(Exercise, exercise_id)
        if exercise is not None and _implemented(exercise.generator):
            concept = session.get(Concept, exercise.concept_id)
            unit = session.get(Unit, concept.unit_id)
            spec = dict(due.item_spec or {}) or {"lemma": lemma, "suffixes": suffix_ids}
            try:
                item = assemble(ExerciseSpec.of(exercise, concept), language, spec)
                return Served(item, "review", unit.id, unit.title, concept.name)
            except (GenerationError, KeyError, ValueError):
                # The card refers to something the content no longer supports.
                session.delete(due)
        # The exercise it referred to is gone, so the card is stale.
        session.delete(due)

    mastery = {
        row.concept_id: row.ability_estimate
        for row in session.scalars(
            select(UserConceptMastery).where(UserConceptMastery.user_id == user_id)
        )
    }

    rows = session.execute(
        select(Exercise, Concept, Unit)
        .join(Concept, Exercise.concept_id == Concept.id)
        .join(Unit, Concept.unit_id == Unit.id)
        .order_by(Unit.order)
    ).all()

    candidates = [
        (exercise, concept, unit) for exercise, concept, unit in rows
        if _implemented(exercise.generator)
        and mastery.get(concept.id, 0.0) < MASTERY_THRESHOLD
    ]
    if not candidates:
        # Everything available is mastered, so revisit rather than stop.
        candidates = [(e, c, u) for e, c, u in rows if _implemented(e.generator)]
    if not candidates:
        raise LookupError("no exercise has an implemented generator yet")

    fresh = [c for c in candidates if c[1].id != avoid_concept] or candidates

    # Work outwards from the earliest unit and the earliest stage. An exercise
    # that cannot build an item right now is skipped rather than fatal: one
    # unbuildable spec should not end a session.
    ordered = sorted(fresh, key=lambda row: (row[2].order, STAGE_ORDER.get(row[0].stage, 9)))
    for tier_key in dict.fromkeys((u.order, STAGE_ORDER.get(e.stage, 9)) for e, c, u in ordered):
        tier = [row for row in ordered
                if (row[2].order, STAGE_ORDER.get(row[0].stage, 9)) == tier_key]
        rng.shuffle(tier)
        for exercise, concept, unit in tier:
            try:
                item = generate(ExerciseSpec.of(exercise, concept), language, rng)
            except (GenerationError, NotImplementedError):
                continue
            return Served(item, "new", unit.id, unit.title, concept.name)

    raise LookupError("no exercise can produce an item for this learner yet")


def record_mastery(session: Session, user_id: int, concept_id: str, correct: bool) -> float:
    """A running estimate, deliberately simple.

    Bayesian Knowledge Tracing per concept is Phase 7. This is a placeholder that
    is honest about being one: it moves in the right direction and is replaced
    wholesale rather than tuned.
    """
    row = session.scalars(
        select(UserConceptMastery).where(
            UserConceptMastery.user_id == user_id,
            UserConceptMastery.concept_id == concept_id,
        )
    ).first()
    if row is None:
        row = UserConceptMastery(user_id=user_id, concept_id=concept_id, ability_estimate=0.0)
        session.add(row)
    row.ability_estimate = round(0.7 * row.ability_estimate + 0.3 * (1.0 if correct else 0.0), 4)
    return row.ability_estimate
