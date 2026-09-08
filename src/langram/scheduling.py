"""FSRS scheduling.

py-fsrs owns the algorithm; this only maps the app's idea of an answer onto a
rating and keeps the card in a JSON column. FSRS rather than SM-2 because it
fits its parameters to the individual learner's history, which is the whole
reason the brief specifies it.

docs/research-spec.md section 3.6 (Suzuki & DeKeyser 2017) asks for two
scheduling phases -- short, dense gaps while a structure is still being
proceduralized, expanding gaps once it is durably known -- and section 1.1
(Cepeda et al. 2008) asks for a tunable "how aggressively should intervals
expand" knob. Both already exist inside FSRS itself rather than needing a
second system built beside it: `learning_steps` is exactly the short-gap
acquisition phase (a card starts in State.Learning and is not handed to the
long-interval algorithm until it graduates to State.Review), and
`desired_retention` is exactly the expansion-aggressiveness knob -- lower it
and every interval FSRS picks gets longer, for the same reason Cepeda's
ridgeline result gives a longer optimal gap for a longer retention goal.
What was missing was exposing the second one at all; it was hardcoded to
the library default. See the pedagogy-rationale.md entry this shipped with
for why a full target_retention_days user setting was deliberately not
built alongside it.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache

from fsrs import Card, Rating, Scheduler

DEFAULT_DESIRED_RETENTION = 0.9


@lru_cache(maxsize=8)
def _scheduler_for(desired_retention: float) -> Scheduler:
    return Scheduler(desired_retention=desired_retention)


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
           used_hints: bool = False, now: dt.datetime | None = None,
           desired_retention: float = DEFAULT_DESIRED_RETENTION) -> tuple[dict, dt.datetime]:
    """Schedule the next review.

    desired_retention is FSRS's own probability-of-recall target for when a
    card comes due again: 0.9 (the default, unchanged from before this was
    exposed) reviews sooner and more often; something like 0.75 spaces
    reviews out further, appropriate for a learner with a longer retention
    goal. Not yet wired to a per-user setting -- there is no onboarding flow
    that asks for one yet -- but this is where it plugs in once there is.
    """
    card, _log = _scheduler_for(desired_retention).review_card(
        load_card(state), rate(correct, attempts, used_hints), now
    )
    return card.to_dict(), card.due
