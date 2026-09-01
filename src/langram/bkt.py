"""Bayesian Knowledge Tracing, per concept.

Four parameters, each of which means something you can argue about:

  prior   how likely a learner already knows this before any evidence
  learn   how likely one opportunity teaches it
  slip    how likely they get it wrong anyway when they do know it
  guess   how likely they get it right when they do not

The point of BKT here is not accuracy for its own sake. It is that a mastery
number should mean "probably knows this rule" rather than "got the last few
right", so unlocking and the diagnostic report rest on something interpretable.

The guess rate is per item rather than global. A two option judgement can be
guessed half the time and a typed answer essentially cannot, and treating them
the same is the quickest way to convince yourself a learner knows something they
do not.

The parameter values below are defaults, not fitted values. Fitting them per
concept needs learner data, which does not exist yet. Everything required to fit
them later is already logged.
"""
from __future__ import annotations

from dataclasses import dataclass

# Guessing a free typed Turkish form is close to impossible, but not quite: a
# learner can produce the right string for the wrong reason.
TYPED_GUESS = 0.03
MAX_GUESS = 0.5

# Certainty is absorbing. At p_known exactly 1 the posterior is 1 whatever
# happens next, so a learner on a good run could never afterwards be shown to
# have lost it. Certainty is also a claim this model has no business making
# about a person, so it is capped just short of it.
CEILING = 0.999


@dataclass(frozen=True)
class Parameters:
    prior: float = 0.15
    learn: float = 0.12
    slip: float = 0.08
    guess: float = 0.20

    def with_guess(self, guess: float) -> "Parameters":
        return Parameters(self.prior, self.learn, self.slip, min(max(guess, 0.0), MAX_GUESS))


DEFAULTS = Parameters()


@dataclass(frozen=True)
class State:
    """What is believed about one learner and one concept."""
    p_known: float
    opportunities: int = 0
    correct: int = 0

    def to_dict(self) -> dict:
        return {"p_known": round(self.p_known, 6),
                "opportunities": self.opportunities,
                "correct": self.correct}

    @classmethod
    def from_dict(cls, raw: dict | None, parameters: Parameters = DEFAULTS) -> "State":
        if not raw:
            return cls(p_known=parameters.prior)
        try:
            return cls(
                p_known=float(raw.get("p_known", parameters.prior)),
                opportunities=int(raw.get("opportunities", 0)),
                correct=int(raw.get("correct", 0)),
            )
        except (TypeError, ValueError):
            return cls(p_known=parameters.prior)


def guess_rate(option_count: int | None) -> float:
    """How often this item shape can be got right without knowing anything."""
    if not option_count or option_count < 2:
        return TYPED_GUESS
    return min(1.0 / option_count, MAX_GUESS)


def observe(state: State, correct: bool, parameters: Parameters = DEFAULTS) -> State:
    """One opportunity, one update.

    Posterior first: given what happened, how likely is it they knew it. Then
    the chance the opportunity itself taught them.
    """
    p = state.p_known
    if correct:
        likely_if_known = 1.0 - parameters.slip
        likely_if_not = parameters.guess
    else:
        likely_if_known = parameters.slip
        likely_if_not = 1.0 - parameters.guess

    numerator = p * likely_if_known
    denominator = numerator + (1.0 - p) * likely_if_not
    posterior = numerator / denominator if denominator else p

    learned = posterior + (1.0 - posterior) * parameters.learn
    return State(
        p_known=min(max(learned, 0.0), CEILING),
        opportunities=state.opportunities + 1,
        correct=state.correct + (1 if correct else 0),
    )


def update(raw_state: dict | None, correct: bool, *, option_count: int | None = None,
           parameters: Parameters = DEFAULTS) -> State:
    tuned = parameters.with_guess(guess_rate(option_count))
    return observe(State.from_dict(raw_state, tuned), correct, tuned)
