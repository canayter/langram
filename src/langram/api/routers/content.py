"""The curriculum, readable without an account.

This is the transparency page from the brief: every unit, what it teaches, and
the sources behind the sequencing. It costs nothing to expose and is the whole
credibility claim of an app that says it is research grounded.
"""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from ...db.models import Unit
from ..deps import SessionDep
from ..schemas import ConceptOut, UnitOut

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
                           teaches_suffixes=c.teaches_suffixes)
                for c in sorted(unit.concepts, key=lambda c: c.id)
            ],
        )
        for unit in rows
    ]
