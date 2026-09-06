"""The curriculum, readable without an account.

This is the transparency page from the brief: every unit, what it teaches, and
the sources behind the sequencing. It costs nothing to expose and is the whole
credibility claim of an app that says it is research grounded.
"""
from __future__ import annotations

import yaml
from fastapi import APIRouter
from sqlalchemy import select

from ...db.models import Unit
from ...loader import CONTENT_ROOT
from ..deps import LanguageDep, SessionDep
from ..schemas import BibliographyEntryOut, ConceptOut, UnitOut, VowelOut

router = APIRouter(prefix="/api", tags=["content"])


@router.get("/units", response_model=list[UnitOut])
def units(session: SessionDep) -> list[UnitOut]:
    rows = session.scalars(select(Unit).order_by(Unit.order)).all()
    return [
        UnitOut(
            id=unit.id, order=unit.order, title=unit.title, rationale=unit.rationale,
            research_refs=unit.research_refs, prerequisites=unit.prerequisites,
            concepts=[
                ConceptOut(id=c.id, name=c.name, type=c.type, why_hard=c.why_hard,
                           intro=c.intro, teaches_suffixes=c.teaches_suffixes,
                           recurs_in=c.recurs_in)
                for c in sorted(unit.concepts, key=lambda c: c.id)
            ],
        )
        for unit in rows
    ]


@router.get("/bibliography", response_model=list[BibliographyEntryOut])
def bibliography() -> list[BibliographyEntryOut]:
    """Every source a unit's research_refs is allowed to point at, read
    straight off content/bibliography.yaml. Unexposed until now: WhyPanel
    could only show a learner the bare keys (research_refs is a list of
    strings), never the authors or the actual claim a citation makes."""
    path = CONTENT_ROOT / "bibliography.yaml"
    with path.open(encoding="utf-8") as fh:
        entries = yaml.safe_load(fh)
    return [BibliographyEntryOut(**entry) for entry in entries]


@router.get("/language/vowels", response_model=list[VowelOut])
def vowels(language: LanguageDep) -> list[VowelOut]:
    """The vowel inventory behind harmony, for the chart on Unit 1's intro
    and the reference panel. Reads language.phonology.vowels directly rather
    than a copy in the database, so it is the same table every derivation
    already runs on, not a second one that can drift from it."""
    return [
        VowelOut(symbol=symbol, back=bool(features["back"]),
                  rounded=bool(features["rounded"]), high=bool(features["high"]))
        for symbol, features in language.phonology.vowels.items()
    ]
