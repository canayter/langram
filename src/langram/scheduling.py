"""FSRS scheduling.

py-fsrs owns the algorithm; this only maps the app's idea of an answer onto a
rating and keeps the card in a JSON column. FSRS rather than SM-2 because it
fits its parameters to the individual learner's history, which is the whole
reason the brief specifies it.
"""
from __future__ import annotations

import datetime as dt

from fsrs import Card, Rating, Scheduler

_scheduler = Scheduler()


def new_card() -> Card:
    return Card()


def load_card(state: dict | None) -> Card:
    if not state:
        return new_card()
    try:
        return Card.from_dict(state)
    except Exception:
        # A card written by an older version is not worth losing a session over.
        return new_card()


def rate(correct: bool, attempts: int, used_hints: bool) -> Rating:
    """Turn what happened into an FSRS rating.

    Getting there after three prompts is not the same as knowing it, so hints
    cap the rating at Hard. Anything wrong is Again.
    """
    if not correct:
        return Rating.Again
    if attempts > 1 or used_hints:
        return Rating.Hard
    return Rating.Good


def review(state: dict | None, correct: bool, attempts: int = 1,
           used_hints: bool = False, now: dt.datetime | None = None) -> tuple[dict, dt.datetime]:
    card, _log = _scheduler.review_card(
        load_card(state), rate(correct, attempts, used_hints), now
    )
    return card.to_dict(), card.due
