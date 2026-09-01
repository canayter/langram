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

from . import bkt
from .db.models import Concept, Exercise, ReviewCard, Unit, UserConceptMastery
from .generators import REGISTRY, GenerationError, assemble, generate

# Comprehension before production. A concept's guided output is only reached
# when its structured input has no generator, which is temporary.
STAGE_ORDER = {"structured_input": 0, "guided_output": 1, "free_output": 2,
               "perception": 3, "review": 4}

# The probability of knowing a concept at which it stops being served as new
# material and its unit counts as finished. High enough that a lucky run does
# not clear it, low enough to be reachable.
MASTERY_THRESHOLD = 0.85

# Mastery needs evidence as well as probability. Five correct answers on two
# option items is five coin flips, and BKT will happily call that knowledge
# without a floor on how much was actually seen.
MIN_OPPORTUNITIES = 6


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
        row.concept_id: is_mastered(row)
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

    open_units = _open_units(rows, mastery)
    candidates = [
        (exercise, concept, unit) for exercise, concept, unit in rows
        if _implemented(exercise.generator)
        and unit.id in open_units
        and not mastery.get(concept.id, False)
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


def is_mastered(row) -> bool:
    """Known enough to stop teaching, and seen enough to believe it."""
    seen = int((row.state or {}).get("opportunities", 0))
    return row.ability_estimate >= MASTERY_THRESHOLD and seen >= MIN_OPPORTUNITIES


def _open_units(rows, mastery: dict[str, bool]) -> set[str]:
    """Units whose prerequisites are finished.

    A unit is finished when every concept in it is above the threshold. Ordering
    by unit alone would let a learner meet nominalised subordination in their
    second session; the prerequisites in the content exist to stop that, and
    this is where they take effect.
    """
    concepts_by_unit: dict[str, set[str]] = {}
    prerequisites: dict[str, list[str]] = {}
    for _exercise, concept, unit in rows:
        concepts_by_unit.setdefault(unit.id, set()).add(concept.id)
        prerequisites[unit.id] = list(unit.prerequisites or [])

    def finished(unit_id: str) -> bool:
        concepts = concepts_by_unit.get(unit_id, set())
        return bool(concepts) and all(mastery.get(c, False) for c in concepts)

    return {
        unit_id for unit_id in concepts_by_unit
        if all(finished(p) for p in prerequisites.get(unit_id, []))
    }


def record_mastery(session: Session, user_id: int, concept_id: str, correct: bool,
                   option_count: int | None = None) -> float:
    """Update the belief that this learner knows this concept.

    Bayesian Knowledge Tracing rather than a running average, so the number
    means "probably knows this rule" rather than "got the last few right". The
    guess rate comes from the item: a two option judgement is guessable and a
    typed answer is not, and treating them alike is the fastest way to believe a
    learner knows something they do not.
    """
    row = session.scalars(
        select(UserConceptMastery).where(
            UserConceptMastery.user_id == user_id,
            UserConceptMastery.concept_id == concept_id,
        )
    ).first()
    if row is None:
        row = UserConceptMastery(user_id=user_id, concept_id=concept_id,
                                 ability_estimate=bkt.DEFAULTS.prior, state={})
        session.add(row)

    state = bkt.update(row.state, correct, option_count=option_count)
    row.state = state.to_dict()
    row.ability_estimate = round(state.p_known, 6)
    return row.ability_estimate
