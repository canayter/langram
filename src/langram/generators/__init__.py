"""Exercise item generators.

Curriculum content specifies a generator by name. A name that is not here is a
validation error, so a unit cannot quietly reference something that will never
run. A generator that is declared but not built yet reports itself as such,
which is visible rather than hidden.

Items are generated from the grammar. Nothing here contains a Turkish surface
form; every string a learner sees comes out of the engine.

Every generator provides build() and assemble(). build() draws a fresh item;
assemble() rebuilds the identical item from its spec. The second is what makes
the server able to mark an answer without keeping session state, and what makes
spaced repetition of one specific form possible.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Generator:
    name: str
    stage: str
    description: str
    implemented: bool = False


REGISTRY: dict[str, Generator] = {
    g.name: g for g in [
        Generator(
            "minimal_pair_identification",
            "structured_input",
            "Two forms differing only in the target feature. The learner picks the one "
            "that is possible Turkish. Comprehension only, no production.",
            implemented=True,
        ),
        Generator(
            "form_meaning_match",
            "structured_input",
            "The target form is the only cue to the meaning, so it cannot be skipped.",
            implemented=True,
        ),
        Generator(
            "grammaticality_judgement",
            "structured_input",
            "Is this a possible Turkish word. Built from engine output and deliberately "
            "broken variants of it.",
            implemented=True,
        ),
        Generator(
            "suffix_builder",
            "guided_output",
            "The learner attaches a suffix to a stem and picks its shape from the "
            "allomorphs the engine derives, so harmony is applied rather than recalled.",
            implemented=True,
        ),
        Generator(
            "cloze_suffix_choice",
            "guided_output",
            "Which suffix, rather than which shape. Tests the grammatical choice that "
            "the suffix builder takes as given.",
            implemented=True,
        ),
        Generator(
            "type_the_form",
            "free_output",
            "Produce the Turkish for an English prompt, scored against engine output.",
            implemented=True,
        ),
        Generator(
            "cued_recall",
            "review",
            "Scheduled recall of a previously introduced form.",
            implemented=True,
        ),
    ]
}


def unimplemented() -> list[str]:
    return sorted(name for name, g in REGISTRY.items() if not g.implemented)


# How a wrong answer should be explained. Morphological errors get the rule they
# missed; a comprehension item is not a production error and should not be told
# it is one.
MORPHOLOGICAL = "morphological"
COMPREHENSION = "comprehension"
JUDGEMENT = "judgement"


@dataclass(frozen=True)
class GeneratedItem:
    """One item, ready to be served.

    `answer` and `derivation` never reach the client before the learner has
    answered. The spec is signed into a token instead, so the server can rebuild
    the item on submission without keeping session state.
    """
    exercise_id: str
    concept_id: str
    generator: str
    stage: str
    prompt: str
    spec: dict               # everything assemble() needs to reproduce this item
    payload: dict            # what the client renders
    answer: str              # the canonical correct answer, for display
    accepted: tuple[str, ...] = ()      # every answer that counts as correct
    derivation: tuple = ()
    diagnosis: str = MORPHOLOGICAL
    # The morphological item this stands for, when there is one. Diagnosis and
    # scheduling both key off it.
    lemma: str | None = None
    suffixes: tuple[str, ...] = ()
    extra: dict = field(default_factory=dict)

    def accepts(self, given: str, normalize) -> bool:
        candidates = self.accepted or (self.answer,)
        return normalize(given) in {normalize(c) for c in candidates}

    def answer_form(self) -> str:
        """The well formed Turkish this item is about.

        For most items that is the answer. For a judgement the answer is yes or
        no, and the form is the last thing the derivation produced.
        """
        if self.derivation:
            return self.derivation[-1]["form"]
        return self.answer


class GenerationError(RuntimeError):
    """This exercise cannot produce an item right now.

    Raised rather than returning something wrong. The tutor moves on to the next
    exercise, which keeps one unbuildable spec from breaking a session.
    """


def _modules() -> dict:
    from . import (
        cloze_suffix_choice, cued_recall, form_meaning_match,
        grammaticality_judgement, minimal_pair_identification, suffix_builder,
        type_the_form,
    )
    return {
        "suffix_builder": suffix_builder,
        "minimal_pair_identification": minimal_pair_identification,
        "form_meaning_match": form_meaning_match,
        "grammaticality_judgement": grammaticality_judgement,
        "cloze_suffix_choice": cloze_suffix_choice,
        "type_the_form": type_the_form,
        "cued_recall": cued_recall,
    }


def generate(exercise, language, rng: random.Random) -> GeneratedItem:
    """Draw a fresh item for an exercise row."""
    try:
        module = _modules()[exercise.generator]
    except KeyError:
        raise NotImplementedError(
            f"generator {exercise.generator!r} is registered but not built yet"
        ) from None
    return module.build(exercise, language, rng)


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    """Rebuild the exact item a spec describes."""
    try:
        module = _modules()[exercise.generator]
    except KeyError:
        raise NotImplementedError(
            f"generator {exercise.generator!r} is registered but not built yet"
        ) from None
    return module.assemble(exercise, language, dict(spec))
