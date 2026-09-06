"""Composing more than one word into a single exercise.

inflect() and every generator built before this assume one lexeme, one
surface form out. Existential var/yok (bende param yok), postpositions
(arkadaşım ile), and eventually the question particle all need more than
that: a short, ordered sequence of words, some inflected, some fixed, joined
into one answer. This module adds that composition without touching
engine.py or Language.inflect() at all -- a phrase is rendered by calling
the exact same inflect() every single-word exercise already calls, once per
inflected part, so nothing here is a special case the engine needs to know
about.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

from .models import DerivationStep


@dataclass(frozen=True)
class Word:
    """One inflected word: a lemma plus a suffix chain, exactly what
    Language.inflect() already takes."""
    lemma: str
    suffixes: Sequence[str] = ()


@dataclass(frozen=True)
class Literal:
    """A fixed word that never inflects: var, yok, ile, için, gibi, kadar."""
    text: str


Part = Union[Word, Literal]


@dataclass(frozen=True)
class PhraseResult:
    surface: str
    words: tuple[str, ...]                 # each part's own rendered surface, in order
    derivation: tuple[DerivationStep, ...]


def render(language, parts: Sequence[Part]) -> PhraseResult:
    """Each part rendered independently, in order, then joined with spaces.

    A Word goes through the same inflect() any single-word exercise already
    uses, so its own derivation steps need no translation; a phrase's trace
    is several ordinary ones concatenated, not a new kind of step.
    """
    surfaces: list[str] = []
    steps: list[DerivationStep] = []
    for part in parts:
        if isinstance(part, Literal):
            surfaces.append(part.text)
            steps.append(DerivationStep(
                "literal", f"{part.text!r} never inflects", "attached as its own word",
                part.text,
            ))
        else:
            result = language.inflect(part.lemma, list(part.suffixes))
            surfaces.append(result.surface)
            steps.extend(result.steps)
    return PhraseResult(surface=" ".join(surfaces), words=tuple(surfaces), derivation=tuple(steps))
