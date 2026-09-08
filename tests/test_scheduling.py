"""Scheduling tests.

No test file existed for this module before -- desired_retention's exposure
is the first change scheduling.py has had, and the first real regression it
could introduce is silent: a wrong rating mapping or a parameter that looks
wired up but has no actual effect on the interval FSRS picks.
"""
import datetime as dt

from langram.scheduling import DEFAULT_DESIRED_RETENTION, new_card, rate, review
from fsrs import Rating


class TestRating:
    def test_wrong_is_always_again(self):
        assert rate(correct=False, attempts=1, used_hints=False) == Rating.Again
        assert rate(correct=False, attempts=3, used_hints=True) == Rating.Again

    def test_right_first_try_no_hints_is_good(self):
        assert rate(correct=True, attempts=1, used_hints=False) == Rating.Good

    def test_right_after_a_retry_or_a_hint_is_hard(self):
        assert rate(correct=True, attempts=2, used_hints=False) == Rating.Hard
        assert rate(correct=True, attempts=1, used_hints=True) == Rating.Hard


class TestReview:
    def test_a_new_card_schedules_into_the_future(self):
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        state, due = review(None, correct=True, now=now)
        assert due > now
        assert state  # a real FSRS state dict, not empty

    def test_default_desired_retention_is_unchanged_from_before_this_was_exposed(self):
        """The whole point of exposing the parameter was to not change
        anything for a caller that does not pass it. card_id is a fresh
        timestamp per Card(), excluded rather than asserted on."""
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        default_state, default_due = review(None, correct=True, now=now)
        explicit_state, explicit_due = review(
            None, correct=True, now=now, desired_retention=DEFAULT_DESIRED_RETENTION)
        default_state.pop("card_id"), explicit_state.pop("card_id")
        assert default_state == explicit_state
        assert default_due == explicit_due

    def _graduate_to_review_state(self, desired_retention: float, now: dt.datetime):
        """A brand new card's first couple of reviews move through FSRS's
        own fixed learning_steps regardless of desired_retention -- that is
        precisely the acquisition-phase behavior this module's docstring
        says FSRS already provides for free. desired_retention only governs
        the expanding intervals once a card has graduated to State.Review,
        so a test of its effect has to get a card there first rather than
        checking a brand new card's very first interval."""
        state = None
        for _ in range(3):
            state, due = review(state, correct=True, now=now,
                                desired_retention=desired_retention)
            now = due
        return state, due

    def test_desired_retention_actually_changes_the_interval_once_reviewing(self):
        """Once a card is in FSRS's own long-interval Review state, a lower
        retention target means FSRS is willing to wait longer before the
        next review, per Cepeda et al.'s ridgeline result (docs/research-
        spec.md section 1.1) that a longer retention goal wants a longer
        gap. Confirms the parameter has a real effect, not just that it is
        accepted and silently ignored."""
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        _, due_high = self._graduate_to_review_state(0.95, now)
        _, due_low = self._graduate_to_review_state(0.70, now)
        assert due_low > due_high

    def test_a_stale_or_corrupt_state_does_not_crash_scheduling(self):
        state, due = review({"not": "a real card"}, correct=True)
        assert due > dt.datetime.now(dt.timezone.utc)

    def test_new_card_has_no_due_date_conflict_with_review(self):
        card = new_card()
        assert card.due is not None
