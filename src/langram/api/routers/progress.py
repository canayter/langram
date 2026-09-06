"""What the learner is weak on, and why it is hard.

A percentage score is not actionable. This report is per linguistic feature and
per concept, so it can say that backness harmony is reliable while rounding
harmony is landing six times in ten, which tells a learner what to do next.

Rates are errors over opportunities. Every response records the rules the target
form gave the learner a chance to apply, so an error count is always divided by
the number of chances to make it.
"""
from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import delete, select

from ...bkt import MAX_GUESS
from ...db.models import Concept, ReviewCard, Response, Unit, UserConceptMastery
from ...skills import LABELS, describe
from ...tutor import MASTERY_THRESHOLD, MIN_OPPORTUNITIES, is_mastered
from ..deps import SessionDep, UserDep
from ..schemas import ConceptProgressOut, ProgressOut, SkillReportOut

router = APIRouter(prefix="/api", tags=["progress"])

# Below this many opportunities a rate is noise rather than a signal.
ENOUGH = 5


@router.get("/progress", response_model=ProgressOut)
def progress(session: SessionDep, user: UserDep) -> ProgressOut:
    responses = session.scalars(
        select(Response).where(Response.user_id == user.id)
    ).all()

    answered = len(responses)
    correct = sum(1 for r in responses if r.correct)

    # ── per rule ─────────────────────────────────────────────────────────────
    # A rate needs errors that can be pinned on a rule. A right answer shows the
    # learner applied everything the form exercised. A wrong one counts only
    # against the rules the diagnosis actually named: rejecting a well formed
    # word, or picking the wrong meaning, says nothing about which rule was
    # missed, so those responses stay out of the rates rather than quietly
    # inflating or deflating them. They still count in overall accuracy and in
    # concept mastery.
    opportunities: dict[str, int] = {}
    errors: dict[str, int] = {}
    for response in responses:
        if response.correct:
            for skill in response.skills or ():
                opportunities[skill] = opportunities.get(skill, 0) + 1
            continue
        for tag in response.error_tags or ():
            if tag in LABELS:
                opportunities[tag] = opportunities.get(tag, 0) + 1
                errors[tag] = errors.get(tag, 0) + 1

    skills = []
    for skill in sorted(set(opportunities) | set(errors)):
        seen = opportunities.get(skill, 0)
        missed = errors.get(skill, 0)
        accuracy = (seen - missed) / seen if seen else None
        skills.append(SkillReportOut(
            skill=skill,
            label=LABELS.get(skill, skill),
            opportunities=seen,
            errors=missed,
            accuracy=round(accuracy, 4) if accuracy is not None else None,
            summary=describe(skill, accuracy, seen),
            confident=seen >= ENOUGH,
        ))
    # Weakest first: that is the thing worth reading.
    skills.sort(key=lambda s: (s.accuracy if s.accuracy is not None else 1.0, -s.opportunities))

    # ── per concept ──────────────────────────────────────────────────────────
    mastery = {
        row.concept_id: row for row in session.scalars(
            select(UserConceptMastery).where(UserConceptMastery.user_id == user.id)
        )
    }
    rows = session.execute(
        select(Concept, Unit).join(Unit, Concept.unit_id == Unit.id).order_by(Unit.order)
    ).all()

    concepts = []
    for concept, unit in rows:
        row = mastery.get(concept.id)
        state = (row.state if row else None) or {}
        seen = int(state.get("opportunities", 0))
        p_known = float(row.ability_estimate) if row else 0.0
        concepts.append(ConceptProgressOut(
            id=concept.id,
            name=concept.name,
            unit_id=unit.id,
            unit_title=unit.title,
            why_hard=concept.why_hard,
            p_known=round(p_known, 4),
            opportunities=seen,
            correct=int(state.get("correct", 0)),
            status=("not started" if not seen
                    else "known" if row is not None and is_mastered(row)
                    else "learning"),
        ))

    weakest = next((s for s in skills if s.confident and (s.accuracy or 0) < 0.9), None)
    return ProgressOut(
        answered=answered,
        correct=correct,
        accuracy=round(correct / answered, 4) if answered else None,
        headline=_headline(answered, weakest),
        skills=skills,
        concepts=concepts,
        # Stated rather than assumed: a mastery number that came from two option
        # items means less than one that came from typing, and the reader should
        # know which they are looking at.
        note=(f"Mastery is the probability you know a rule, not a score. It needs "
              f"at least {MIN_OPPORTUNITIES} attempts as well as a high probability, "
              f"and multiple choice items are discounted, since they can be guessed "
              f"up to {int(MAX_GUESS * 100)} percent of the time."),
    )


@router.delete("/progress", status_code=status.HTTP_204_NO_CONTENT)
def reset_progress(session: SessionDep, user: UserDep) -> None:
    """Start over: every response, review card and mastery estimate for this
    user is gone, and the day chain and marks reset to zero. There is no
    account recovery in this app (guest only, see StartScreen), so this is
    the only "start fresh" a learner has -- irreversible on purpose, which is
    exactly why the client is expected to confirm before calling it, not
    this endpoint.
    """
    session.execute(delete(Response).where(Response.user_id == user.id))
    session.execute(delete(ReviewCard).where(ReviewCard.user_id == user.id))
    session.execute(delete(UserConceptMastery).where(UserConceptMastery.user_id == user.id))
    user.xp = 0
    user.current_streak = 0
    user.longest_streak = 0
    user.last_practiced_on = None
    session.commit()


def _headline(answered: int, weakest) -> str:
    if not answered:
        return "Nothing answered yet."
    if weakest is None:
        return "Nothing is standing out as a weakness yet."
    return weakest.summary
