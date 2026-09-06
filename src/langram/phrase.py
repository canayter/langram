"""Composing more than one word into a single exercise.

inflect() and every generator built before this assume one lexeme, one
surface form out. Existential var/yok (bende param yok), postpositions
(arkadaşım ile), and the question particle all need more than that: a
short, ordered sequence of words, some inflected, some fixed, joined into
one answer. This module adds that composition without touching engine.py
or Language.inflect() at all -- a phrase is rendered by calling the exact
same inflect() every single-word exercise already calls, once per inflected
part, so nothing here is a special case the engine needs to know about.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

from .engine import inflect
from .models import DerivationStep, Lexeme


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


@dataclass(frozen=True)
class QuestionParticle:
    """mI: harmonizes fourfold against whatever precedes it (var mı,
    öğrenci mi, geliyor mu), written as its own word but otherwise acting
    exactly like a suffix on the word before it.

    Unlike a suffix, though, mI can itself take a further suffix chain --
    typically a person ending, which moves off the predicate and onto mI
    with a present-tense or aorist-shaped verb, and with an ordinary
    nominal predicate too (öğrenci misin?, never öğrencisin mi?). var/yok
    are the exception: nothing ever attaches to them in the first place
    (see existence.py), so mI just follows bare (var mı?, yok mu?).
    """
    suffixes: Sequence[str] = ()


Part = Union[Word, Literal, QuestionParticle]


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
        elif isinstance(part, QuestionParticle):
            if not surfaces:
                raise ValueError("a question particle needs a preceding part to harmonize against")
            preceding = surfaces[-1]
            vowel = language.phonology.resolve("I", preceding)
            resolved = "m" + vowel
            steps.append(DerivationStep(
                "harmony", f"preceding word ends in {preceding[-1]!r}",
                f"fourfold harmony resolves the question particle's vowel to {vowel}", resolved,
                {"archiphoneme": "I", "resolved": vowel},
            ))
            if part.suffixes:
                # mI takes a further suffix chain (typically person) the
                # same way any other stem does; a synthetic lexeme lets it
                # go through the exact same inflect() rather than a second
                # code path. harmony_class=None so backness and rounding
                # come from mI's own resolved vowel, not from whatever the
                # original predicate's class was -- exactly the harmony_back
                # reset every other chained suffix already relies on.
                stem = Lexeme(id="_mI", lemma=resolved, pos="particle", gloss="")
                result = inflect(stem, [language.suffix(s) for s in part.suffixes],
                                 language.phonology)
                surfaces.append(result.surface)
                steps.extend(result.steps)
            else:
                surfaces.append(resolved)
        else:
            result = language.inflect(part.lemma, list(part.suffixes))
            surfaces.append(result.surface)
            steps.extend(result.steps)
    return PhraseResult(surface=" ".join(surfaces), words=tuple(surfaces), derivation=tuple(steps))
