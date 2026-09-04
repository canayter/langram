"""XP and streaks: the playful layer on top of the graded exercises.

Deliberately separate from bkt.py and scheduling.py. Nothing pedagogical reads
xp or streak, and record_practice() reads nothing pedagogical either, so a bug
here cannot corrupt what the tutor teaches or when a review comes due.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .db.models import User

XP_PER_CORRECT_ANSWER = 10


@dataclass(frozen=True)
class PracticeResult:
    xp_awarded: int
    xp_total: int
    streak: int
    # True on the first answer of a new calendar day, whether that continues
    # yesterday's streak or starts a fresh one. False on a same-day repeat,
    # since the streak count cannot have changed either way.
    streak_extended: bool


def record_practice(user: User, *, correct: bool, today: dt.date) -> PracticeResult:
    """Mutates `user` in place, mirroring how tutor.record_mastery treats the
    ORM row it is handed. Every answer counts toward the streak; only a
    correct one earns XP: showing up is what keeps a streak alive, getting it
    right is what a lesson is actually for.
    """
    xp_awarded = XP_PER_CORRECT_ANSWER if correct else 0
    user.xp += xp_awarded

    streak_extended = user.last_practiced_on != today
    if streak_extended:
        user.current_streak = (
            user.current_streak + 1
            if user.last_practiced_on == today - dt.timedelta(days=1)
            else 1
        )
        user.last_practiced_on = today
        user.longest_streak = max(user.longest_streak, user.current_streak)

    return PracticeResult(
        xp_awarded=xp_awarded,
        xp_total=user.xp,
        streak=user.current_streak,
        streak_extended=streak_extended,
    )
