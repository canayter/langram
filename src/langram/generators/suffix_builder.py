"""The suffix builder.

The learner is given a stem and a suffix, and picks which shape the suffix takes.
The options are the suffix's real allomorphs, derived by running the engine over
probe stems from the lexicon rather than listed anywhere. That is the whole point:
if a new allomorph became possible tomorrow, this exercise would offer it without
anyone editing content.
"""
from __future__ import annotations

import random
from typing import Iterable, Sequence

from ..models import Lexeme
from . import GeneratedItem


def _syllable_count(language, form: str) -> int:
    return sum(1 for ch in form if language.phonology.is_vowel(ch))


def _ends_in_vowel(language, form: str) -> bool:
    return bool(form) and language.phonology.is_vowel(form[-1])


def realisation(language, lexeme: Lexeme, suffix_ids: Sequence[str]) -> str:
    """The material the suffixes contribute, with the stem removed.

    InflectionResult.stem_form is the stem after syncope and voicing, so the
    remainder is exactly what the suffixes added.
    """
    result = language.inflect(lexeme, suffix_ids)
    return result.surface[len(result.stem_form):]


def allomorphs(language, suffix_id: str, *, consonant_final: bool | None = None) -> list[str]:
    """Every shape this suffix takes, derived from the grammar.

    Probes are real lexemes chosen to cover the four harmony classes in both
    consonant-final and vowel-final shapes. No Turkish string is written here.
    """
    seen: dict[str, None] = {}
    for lexeme in _probe_lexemes(language):
        if consonant_final is not None:
            if _ends_in_vowel(language, lexeme.lemma) == consonant_final:
                continue
        try:
            seen.setdefault(realisation(language, lexeme, [suffix_id]), None)
        except Exception:                      # a probe that cannot take it teaches nothing
            continue
    return sorted(seen)


def _probe_lexemes(language) -> list[Lexeme]:
    """One clean probe per harmony class per stem shape.

    Stems that alternate or delete a vowel are skipped: they would change the
    stem as well as the suffix, and the suffix is what is being measured.
    """
    wanted: dict[tuple, Lexeme] = {}
    for lexeme in language.lexemes.values():
        if lexeme.final_voicing or lexeme.vowel_deletion or lexeme.review:
            continue
        vowel = language.phonology.last_vowel(lexeme.lemma)
        if vowel is None:
            continue
        key = (
            language.phonology.is_back(vowel) if lexeme.harmony_class is None
            else lexeme.harmony_class == "back",
            language.phonology.is_rounded(vowel),
            _ends_in_vowel(language, lexeme.lemma),
        )
        wanted.setdefault(key, lexeme)
    return list(wanted.values())


def candidate_lexemes(language, params: dict) -> list[Lexeme]:
    """Lexemes this exercise is allowed to draw on."""
    wanted = params.get("lexeme_filter", {}) or {}
    minimum = params.get("min_syllables")
    mix = params.get("stem_mix")
    obstruents = set(language.phonology.final_voicing)

    out = []
    for lexeme in language.lexemes.values():
        if lexeme.pos not in ("noun", "adjective"):
            continue
        # Anything a native speaker has not confirmed stays out of a learner's way.
        if lexeme.review:
            continue
        if "final_voicing" in wanted and lexeme.final_voicing != wanted["final_voicing"]:
            continue
        if wanted.get("ends_in_obstruent") and lexeme.lemma[-1] not in obstruents:
            continue
        if minimum and _syllable_count(language, lexeme.lemma) < minimum:
            continue
        if mix and not _matches_mix(language, lexeme, mix):
            continue
        out.append(lexeme)
    return out


def _matches_mix(language, lexeme: Lexeme, mix: Iterable[str]) -> bool:
    vowel_final = _ends_in_vowel(language, lexeme.lemma)
    return ("vowel_final" in mix and vowel_final) or ("consonant_final" in mix and not vowel_final)


def _suffix_ids(params: dict) -> list[str]:
    if params.get("suffix"):
        return [params["suffix"]]
    if params.get("persons"):
        return list(params["persons"])
    return []


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})
    choices = _suffix_ids(params)
    if not choices:
        raise ValueError(f"{exercise.id}: suffix_builder needs a suffix or persons parameter")
    suffix_id = rng.choice(choices)

    pool = candidate_lexemes(language, params)
    if not pool:
        raise ValueError(f"{exercise.id}: no lexeme satisfies {params.get('lexeme_filter')}")
    lexeme = rng.choice(pool)
    return assemble(exercise, language, lexeme.lemma, [suffix_id], rng)


def assemble(exercise, language, lemma: str, suffix_ids: Sequence[str],
             rng: random.Random) -> GeneratedItem:
    """Build the item for a known stem and suffix.

    Separate from build() so a scheduled review can reconstruct the same item
    rather than drawing a new one, which is what makes spaced repetition of a
    specific form possible at all.
    """
    lexeme = language.lexeme(lemma)
    suffix_id = suffix_ids[0]

    result = language.inflect(lexeme, [suffix_id])
    correct = realisation(language, lexeme, [suffix_id])

    # Options are the suffix's other shapes for the same stem shape, so a
    # distractor is always a form the learner could plausibly reach for.
    options = allomorphs(language, suffix_id, consonant_final=not _ends_in_vowel(language, lexeme.lemma))
    if correct not in options:
        options.append(correct)
    rng.shuffle(options)

    suffix = language.suffix(suffix_id)
    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator="suffix_builder",
        stage=exercise.stage,
        prompt=exercise.prompt or "Attach the suffix.",
        spec={"lemma": lexeme.lemma, "suffixes": [suffix_id]},
        payload={
            "stem": lexeme.lemma,
            "gloss": lexeme.gloss,
            "suffix": {
                "id": suffix.id,
                "notation": suffix.surface,
                "glosses": list(suffix.glosses),
            },
            "options": options,
        },
        answer=result.surface,
        derivation=tuple(
            {"rule": step.rule, "condition": step.condition,
             "result": step.result, "form": step.form}
            for step in result.steps
        ),
    )
