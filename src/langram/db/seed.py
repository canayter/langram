"""Load content/ into the database.

Content tables are a projection of content/, so seeding upserts them and prunes
whatever content no longer defines. Learner state is never touched: if seeding
could lose a learner's history, the split between content and state would not be
real, and it would be lost quietly rather than loudly.

    python -m langram.db.seed --database-url sqlite:///langram.db
    python -m langram.db.seed --database-url postgresql+psycopg://...
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from ..loader import CONTENT_ROOT, load_language
from ..validate import validate
from .models import Base, Concept, Exercise, Lexeme, Suffix, Unit

DEFAULT_URL = "sqlite:///langram.db"


def _units_from_content(content_root: Path) -> list[dict]:
    unit_dir = content_root / "l2" / "tr" / "curriculum"
    units = []
    for path in sorted(unit_dir.glob("unit-*.yaml")):
        with path.open(encoding="utf-8") as fh:
            units.append(yaml.safe_load(fh))
    return sorted(units, key=lambda u: u["order"])


def seed(session: Session, content_root: Path | None = None) -> dict[str, int]:
    """Bring the content tables in line with content/. Returns a count per table.

    Upsert rather than delete and recreate. responses.exercise_id is a foreign
    key with ON DELETE SET NULL, so wiping the exercises table would silently
    detach every historical response from the exercise that produced it. Rows
    that have genuinely disappeared from content are removed at the end, where
    that detaching is the correct outcome.
    """
    content_root = content_root or CONTENT_ROOT
    language = load_language("tr", root=content_root)

    for lexeme in language.lexemes.values():
        session.merge(Lexeme(
            id=lexeme.id,
            lemma=lexeme.lemma,
            pos=lexeme.pos,
            gloss=lexeme.gloss,
            frequency_band=None,          # absent until a real corpus list, see provenance
            properties={
                "final_voicing": lexeme.final_voicing,
                "vowel_deletion": lexeme.vowel_deletion,
                "harmony_class": lexeme.harmony_class,
                "etymology": lexeme.etymology,
                "review": list(lexeme.review),
            },
            needs_review=bool(lexeme.review),
        ))

    lexeme_ids = {lx.id for lx in language.lexemes.values()}

    for suffix in language.suffixes.values():
        session.merge(Suffix(
            id=suffix.id,
            archiphoneme_form=suffix.surface,
            category=suffix.category,
            slot=suffix.slot,
            properties={
                "glosses": list(suffix.glosses),
                "triggers_pronominal_n": suffix.triggers_pronominal_n,
                "cannot_follow": list(suffix.cannot_follow),
                "review": list(suffix.review),
            },
        ))

    suffix_ids = set(language.suffixes)
    unit_ids: set[str] = set()
    concept_ids: set[str] = set()
    exercise_ids: set[str] = set()

    counts = {"lexemes": len(language.lexemes), "suffixes": len(language.suffixes),
              "units": 0, "concepts": 0, "exercises": 0}

    for unit in _units_from_content(content_root):
        session.merge(Unit(
            id=unit["id"],
            order=unit["order"],
            title=unit["title"],
            rationale=" ".join(unit["rationale"].split()),
            research_refs=list(unit["research_refs"]),
            prerequisites=list(unit.get("prerequisites", [])),
        ))
        unit_ids.add(unit["id"])
        counts["units"] += 1
        for concept in unit["concepts"]:
            session.merge(Concept(
                id=concept["id"],
                unit_id=unit["id"],
                name=concept["name"],
                type=concept["type"],
                why_hard=" ".join(concept["why_hard"].split()),
                intro=" ".join(concept["intro"].split()),
                teaches_suffixes=list(concept.get("teaches_suffixes", [])),
            ))
            concept_ids.add(concept["id"])
            counts["concepts"] += 1
            for exercise in concept["exercises"]:
                session.merge(Exercise(
                    # Exercise ids are unique within a concept, so the stored id
                    # is qualified. Nothing outside this function assumes the shape.
                    id=f"{concept['id']}:{exercise['id']}",
                    concept_id=concept["id"],
                    stage=exercise["stage"],
                    generator=exercise["generator"],
                    prompt=exercise.get("prompt", ""),
                    params=exercise.get("params", {}),
                    difficulty=exercise.get("difficulty", 1),
                ))
                exercise_ids.add(f"{concept['id']}:{exercise['id']}")
                counts["exercises"] += 1

    session.flush()

    # The one place a content row is deleted. Detaching a historical response
    # from an exercise that no longer exists is the correct outcome here, which
    # is exactly why the wholesale delete above it would not have been.
    pruned = 0
    for model, keep in (
        (Exercise, exercise_ids), (Concept, concept_ids), (Unit, unit_ids),
        (Suffix, suffix_ids), (Lexeme, lexeme_ids),
    ):
        statement = delete(model) if not keep else delete(model).where(model.id.not_in(keep))
        pruned += session.execute(statement).rowcount or 0
    if pruned:
        counts["pruned"] = pruned

    session.flush()
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="langram-seed", description=__doc__)
    parser.add_argument("--database-url", default=DEFAULT_URL)
    parser.add_argument("--create-tables", action="store_true",
                        help="create tables directly instead of running migrations. "
                             "For a scratch database only; production uses alembic upgrade head.")
    parser.add_argument("--skip-validation", action="store_true",
                        help="seed even if content is invalid. Never use this in CI.")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):    # pragma: no cover
            pass

    if not args.skip_validation:
        report = validate()
        if not report.ok:
            for err in report.errors:
                print(f"  ERROR: {err}", file=sys.stderr)
            print("refusing to seed invalid content", file=sys.stderr)
            return 1

    engine = create_engine(args.database_url)
    if args.create_tables:
        Base.metadata.create_all(engine)

    with Session(engine) as session:
        counts = seed(session)
        session.commit()

    for table, n in counts.items():
        print(f"  {n:>4}  {table}")
    print(f"seeded {args.database_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
