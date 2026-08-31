"""Exercise item generators.

Curriculum content specifies a generator by name. A name that is not here is a
validation error, so a unit cannot quietly reference something that will never
run. A generator that is declared but not built yet reports itself as such,
which is visible rather than hidden.

Items are generated from the grammar. Nothing here contains a Turkish surface
form; every string a learner sees comes out of the engine.
"""
from __future__ import annotations

from dataclasses import dataclass


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
            "they heard or read. Comprehension only, no production.",
        ),
        Generator(
            "form_meaning_match",
            "structured_input",
            "The target form is the only cue to the meaning, so it cannot be skipped.",
        ),
        Generator(
            "grammaticality_judgement",
            "structured_input",
            "Is this a possible Turkish word or sentence. Built from engine output and "
            "deliberately broken variants of it.",
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
            "A gap in a sentence with an inventory of suffixes to choose from.",
        ),
        Generator(
            "type_the_form",
            "free_output",
            "Produce the Turkish for an English prompt, scored against engine output.",
        ),
        Generator(
            "cued_recall",
            "review",
            "Scheduled recall of a previously introduced item.",
        ),
    ]
}


def unimplemented() -> list[str]:
    return sorted(name for name, g in REGISTRY.items() if not g.implemented)


@dataclass(frozen=True)
class GeneratedItem:
    """One item, ready to be served.

    `answer` and `derivation` never reach the client before the learner has
    answered. The spec is signed into a token instead, so the server can derive
    the answer again on submission without keeping session state.
    """
    exercise_id: str
    concept_id: str
    generator: str
    stage: str
    prompt: str
    spec: dict              # stem plus suffix ids: enough to reproduce the item
    payload: dict           # what the client renders
    answer: str
    derivation: tuple


def generate(exercise, language, rng) -> GeneratedItem:
    """Build one item for an exercise row.

    `exercise` is anything with id, concept_id, generator, prompt and params.
    """
    from . import suffix_builder

    builders = {"suffix_builder": suffix_builder.build}
    try:
        builder = builders[exercise.generator]
    except KeyError:
        raise NotImplementedError(
            f"generator {exercise.generator!r} is registered but not built yet"
        ) from None
    return builder(exercise, language, rng)
