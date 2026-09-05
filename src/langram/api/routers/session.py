"""The learning loop: ask for an item, answer it, get told what to fix.

The answer never leaves the server before the learner has committed to one. What
goes out is a signed token carrying the item's specification, which comes back on
submission and is rebuilt by the generator that made it. Nothing here knows what
kind of exercise it is handling.
"""
from __future__ import annotations

import datetime as dt
import random

import jwt
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from ... import tutor
from ...db.models import Concept, Exercise, Response, ReviewCard
from ...diagnosis import feedback_for_item, normalize
from ...gamification import record_practice
from ...generators import GenerationError, assemble
from ...ipa import CAVEAT as IPA_CAVEAT
from ...ipa import transcribe
from ...scheduling import review
from ...skills import skills_for
from ..deps import LanguageDep, SessionDep, UserDep
from ..schemas import AnswerIn, AnswerOut, ItemOut, WordInfoOut
from ..security import create_item_token, read_item_token

router = APIRouter(prefix="/api/session", tags=["session"])

# The number of prompts before the form is handed over. Rung four is the recast.
LAST_RUNG = 4


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
        item_token=create_item_token({"e": item.exercise_id, "c": item.concept_id,
                                      "s": item.spec}),
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
        word_info=_served_word_info(item, language),
        xp_total=user.xp,
        streak=user.current_streak,
    )


def _served_word_info(item, language) -> WordInfoOut | None:
    """None when a word-info panel would hand over the answer instead of
    supporting it, rather than the panel a learner otherwise gets for every
    item's underlying word.

    vocab_recognition's whole question is "what does this word mean", so its
    own gloss would hand over the answer underneath the exercise before it is
    even attempted. form_meaning_match's buffer mode has the same problem
    from a different direction: its three options are three different words,
    one of which needed a buffer, and spec["lemma"] (see its "buffer" branch)
    is always that one, so a single-word panel would silently name the
    correct option regardless of what the options themselves show. The three
    options already carry their own ipa and gloss in the payload,
    symmetrically, which is the right place for this information here.
    """
    if item.generator == "vocab_recognition":
        return None
    if item.generator == "form_meaning_match" and getattr(item, "extra", {}).get("mode") == "buffer":
        return None
    return _word_info(language, getattr(item, "lemma", None))


def _word_info(language, lemma: str | None) -> WordInfoOut | None:
    """Meaning and a generated pronunciation sketch for the word an item is
    actually about. Never the inflected surface form: several exercise kinds
    show that as the answer, and the stem shown in the prompt is always safe
    to describe further.
    """
    if not lemma:
        return None
    try:
        lexeme = language.lexeme(lemma)
    except KeyError:
        return None
    return WordInfoOut(
        lemma=lexeme.lemma,
        gloss=lexeme.gloss,
        ipa=transcribe(language.phonology, lexeme.lemma),
        ipa_caveat=IPA_CAVEAT,
        etymology=lexeme.etymology,
    )


@router.post("/answer", response_model=AnswerOut)
def answer(body: AnswerIn, session: SessionDep, language: LanguageDep, user: UserDep) -> AnswerOut:
    try:
        token = read_item_token(body.item_token)
        exercise_id, concept_id, spec = token["e"], token["c"], token["s"]
    except (jwt.PyJWTError, KeyError, TypeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "that item has expired") from None

    exercise = session.get(Exercise, exercise_id)
    concept = session.get(Concept, concept_id)
    if exercise is None or concept is None:
        raise HTTPException(status.HTTP_410_GONE, "that item no longer exists")

    try:
        item = assemble(tutor.ExerciseSpec.of(exercise, concept), language, spec)
    except (GenerationError, KeyError, ValueError, NotImplementedError):
        raise HTTPException(status.HTTP_410_GONE, "that item no longer exists") from None

    given = _as_answered(language, item, body.answer)
    correct = item.accepts(given, normalize) or item.accepts(body.answer, normalize)
    result = feedback_for_item(language, item, given, body.attempt, correct=correct)

    session.add(Response(
        user_id=user.id,
        exercise_id=exercise.id,
        concept_id=concept.id,
        correct=correct,
        latency_ms=body.latency_ms,
        raw_answer=body.answer[:512],
        error_tags=list(result.get("tags", [])),
        # What this form gave them a chance to apply, right or wrong. Errors
        # without opportunities are not a rate.
        skills=list(skills_for(language, item.lemma, item.suffixes)) if item.lemma else [],
    ))

    mastery = due_at = None
    # Rate the card once the item is settled: solved, or given up on.
    if correct or body.attempt >= LAST_RUNG:
        mastery = tutor.record_mastery(session, user.id, concept.id, correct,
                                       option_count=_option_count(item))
        due_at = _reschedule(session, user.id, item, correct=correct, attempts=body.attempt)

    # Every attempt counts toward today's streak, not just a settled one:
    # showing up is what a streak measures, and gating it behind the ladder
    # running out would make hard items worth less than easy ones.
    practice = record_practice(user, correct=correct, today=dt.datetime.now(dt.timezone.utc).date())

    session.commit()
    return AnswerOut(
        correct=correct,
        kind=result["kind"],
        message=result["message"],
        tags=result.get("tags", []),
        elicitation=result.get("elicitation"),
        answer=result.get("answer") or (item.answer if correct else None),
        derivation=list(item.derivation) if (correct or result["kind"] == "explicit") else None,
        mastery=mastery,
        due_at=due_at,
        xp_awarded=practice.xp_awarded,
        xp_total=practice.xp_total,
        streak=practice.streak,
        streak_extended=practice.streak_extended,
    )


def _option_count(item) -> int | None:
    """How many ways there were to answer, which sets the guess rate.

    A two option judgement is guessable half the time and a typed answer is not.
    """
    options = item.payload.get("options")
    return len(options) if isinstance(options, list) and options else None


def _as_answered(language, item, given: str) -> str:
    """What the learner meant, as a full form where there is one.

    Picking the shape of a suffix and typing the whole word are the same answer.
    The diagnosis works on whole forms, so a bare suffix is completed here.
    """
    if not item.lemma or item.diagnosis != "morphological":
        return given
    try:
        stem_form = language.inflect(language.lexeme(item.lemma), list(item.suffixes)).stem_form
    except Exception:
        return given
    if normalize(given).startswith(normalize(stem_form)[:2]):
        return given
    return stem_form + given


def _reschedule(session, user_id: int, item, *, correct: bool, attempts: int) -> dt.datetime:
    ref = tutor.card_ref(item)
    card = session.scalars(
        select(ReviewCard).where(ReviewCard.user_id == user_id,
                                 ReviewCard.item_type == "form",
                                 ReviewCard.item_ref == ref)
    ).first()
    state, due = review(card.fsrs_state if card else None, correct=correct,
                        attempts=attempts, used_hints=attempts > 1)
    if card is None:
        card = ReviewCard(user_id=user_id, item_type="form", item_ref=ref,
                          item_spec=dict(item.spec), fsrs_state=state, due_at=due)
        session.add(card)
    else:
        card.item_spec = dict(item.spec)
        card.fsrs_state = state
        card.due_at = due
    return due
