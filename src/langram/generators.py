"""Registry of exercise item generators.

Curriculum content specifies a generator by name. A name that is not here is a
validation error, so a unit cannot quietly reference something that will never
run. Generators themselves arrive in Phase 4; until then they are declared,
described and unimplemented, which is visible rather than hidden.
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
            "Archiphoneme suffix tiles are dragged onto a stem and the engine resolves "
            "the surface form live, so the learner watches harmony operate.",
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
