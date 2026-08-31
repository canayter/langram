"""The learning loop: ask for an item, answer it, get told what to fix.

The answer never leaves the server before the learner has committed to one. What
goes out is a signed token carrying the item's specification, which comes back on
submission and is re-derived by the engine.
"""
from __future__ import annotations

import datetime as dt
import random

import jwt
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from ... import tutor
from ...db.models import Concept, Exercise, Response, ReviewCard
from ...diagnosis import feedback, normalize
from ...scheduling import review
from ..deps import LanguageDep, SessionDep, UserDep
from ..schemas import AnswerIn, AnswerOut, ItemOut
from ..security import create_item_token, read_item_token

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/next", response_model=ItemOut)
def next_item(session: SessionDep, language: LanguageDep, user: UserDep,
              after: str | None = Query(default=None,
                                        description="concept just answered, so it is not repeated")
              ) -> ItemOut:
    try:
        served = tutor.next_item(session, user.id, language, random.Random(), avoid_concept=after)
    except LookupError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from None
    session.commit()

    item = served.item
    return ItemOut(
        item_token=create_item_token({
            "exercise_id": item.exercise_id,
            "concept_id": item.concept_id,
            **item.spec,
        }),
        exercise_id=item.exercise_id,
        concept_id=item.concept_id,
        concept_name=served.concept_name,
        unit_id=served.unit_id,
        unit_title=served.unit_title,
        stage=item.stage,
        generator=item.generator,
        prompt=item.prompt,
        payload=item.payload,
        source=served.source,
    )


@router.post("/answer", response_model=AnswerOut)
def answer(body: AnswerIn, session: SessionDep, language: LanguageDep, user: UserDep) -> AnswerOut:
    try:
        spec = read_item_token(body.item_token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "that item has expired") from None

    lemma, suffix_ids = spec["lemma"], spec["suffixes"]
    exercise_id, concept_id = spec["exercise_id"], spec["concept_id"]

    try:
        lexeme = language.lexeme(lemma)
        expected = language.inflect(lexeme, suffix_ids).surface
    except KeyError:
        raise HTTPException(status.HTTP_410_GONE, "that item no longer exists") from None

    # The learner may type the whole word or only the suffix they chose.
    given = normalize(body.answer)
    if given and not given.startswith(normalize(lexeme.lemma)[:1]):
        given_full = normalize(language.inflect(lexeme, suffix_ids).stem_form + body.answer)
    else:
        given_full = given
    correct = given_full == normalize(expected)

    result = feedback(language, lexeme, suffix_ids, given_full, expected, body.attempt)

    exercise = session.get(Exercise, exercise_id)
    session.add(Response(
        user_id=user.id,
        exercise_id=exercise.id if exercise else None,
        concept_id=concept_id if session.get(Concept, concept_id) else None,
        correct=correct,
        latency_ms=body.latency_ms,
        raw_answer=body.answer[:512],
        error_tags=list(result.get("tags", [])),
    ))

    mastery = due_at = None
    # Rate the card once the item is settled: solved, or given up on.
    if correct or body.attempt >= 4:
        mastery = tutor.record_mastery(session, user.id, concept_id, correct)
        due_at = _reschedule(session, user.id, exercise_id, lemma, suffix_ids,
                             correct=correct, attempts=body.attempt)

    session.commit()
    return AnswerOut(
        correct=correct,
        kind=result["kind"],
        message=result["message"],
        tags=result.get("tags", []),
        elicitation=result.get("elicitation"),
        answer=result.get("answer") or (expected if correct else None),
        derivation=result.get("derivation") or (_derivation(language, lexeme, suffix_ids)
                                                if correct else None),
        mastery=mastery,
        due_at=due_at,
    )


def _derivation(language, lexeme, suffix_ids) -> list[dict]:
    """Shown on success too. Watching the rule fire is the point of the app."""
    return [
        {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
        for s in language.inflect(lexeme, suffix_ids).steps
    ]


def _reschedule(session, user_id: int, exercise_id: str, lemma: str, suffix_ids,
                *, correct: bool, attempts: int) -> dt.datetime:
    ref = f"{exercise_id}|{lemma}|{'+'.join(suffix_ids)}"
    card = session.scalars(
        select(ReviewCard).where(ReviewCard.user_id == user_id,
                                 ReviewCard.item_type == "form",
                                 ReviewCard.item_ref == ref)
    ).first()
    state, due = review(card.fsrs_state if card else None, correct=correct,
                        attempts=attempts, used_hints=attempts > 1)
    if card is None:
        card = ReviewCard(user_id=user_id, item_type="form", item_ref=ref,
                          fsrs_state=state, due_at=due)
        session.add(card)
    else:
        card.fsrs_state = state
        card.due_at = due
    return due
