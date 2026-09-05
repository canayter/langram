"""Shared machinery for the generators.

Two things matter here. Lexeme selection never returns a word a native speaker
has not confirmed, so an unresolved review flag cannot reach a learner. And
allomorphs are derived by running the engine over probe stems rather than being
listed, so a generator offers exactly the shapes the grammar produces.
"""
from __future__ import annotations

import random
from dataclasses import replace
from typing import Iterable, Sequence

from ..models import Lexeme
from . import GenerationError


def syllable_count(language, form: str) -> int:
    return sum(1 for ch in form if language.phonology.is_vowel(ch))


def ends_in_vowel(language, form: str) -> bool:
    return bool(form) and language.phonology.is_vowel(form[-1])


def realisation(language, lexeme: Lexeme, suffix_ids: Sequence[str]) -> str:
    """The material the suffixes contribute, with the stem removed.

    InflectionResult.stem_form is the stem after syncope and voicing, so the
    remainder is exactly what the suffixes added.
    """
    result = language.inflect(lexeme, list(suffix_ids))
    return result.surface[len(result.stem_form):]


def probe_lexemes(language) -> list[Lexeme]:
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
            ends_in_vowel(language, lexeme.lemma),
        )
        wanted.setdefault(key, lexeme)
    return list(wanted.values())


def allomorphs(language, suffix_id: str, *, consonant_final: bool | None = None) -> list[str]:
    """Every shape this suffix takes, derived from the grammar."""
    seen: dict[str, None] = {}
    for lexeme in probe_lexemes(language):
        if consonant_final is not None and ends_in_vowel(language, lexeme.lemma) == consonant_final:
            continue
        try:
            seen.setdefault(realisation(language, lexeme, [suffix_id]), None)
        except Exception:
            continue
    return sorted(seen)


def candidate_lexemes(language, params: dict) -> list[Lexeme]:
    """Lexemes this exercise is allowed to draw on."""
    wanted = params.get("lexeme_filter", {}) or {}
    minimum = params.get("min_syllables")
    mix = params.get("stem_mix")
    obstruents = set(language.phonology.final_voicing)

    # A verbal suffix (negation, tense) attached to a noun or adjective is
    # not a distractor, it is nonsense ("kucuguyor"): the default pool stays
    # noun/adjective for every exercise already written against it, and an
    # exercise that actually wants verbs says so explicitly, rather than
    # verbs joining the default pool and leaking into nominal exercises that
    # never asked for a pos filter at all.
    allowed_pos = (wanted["pos"],) if "pos" in wanted else ("noun", "adjective")

    out = []
    for lexeme in language.lexemes.values():
        if lexeme.pos not in allowed_pos:
            continue
        # Anything a native speaker has not confirmed stays out of a learner's way.
        if lexeme.review:
            continue
        if "final_voicing" in wanted and lexeme.final_voicing != wanted["final_voicing"]:
            continue
        # A predicative exercise ("we are ___") needs a word someone would
        # actually say that about. Adjectives are exempt -- almost any
        # adjective is a natural personal predicate -- so this only screens
        # nouns, against predicate_natural in the lexicon.
        if wanted.get("predicative_only") and lexeme.pos == "noun" and not lexeme.predicate_natural:
            continue
        if wanted.get("ends_in_obstruent") and lexeme.lemma[-1] not in obstruents:
            continue
        if minimum and syllable_count(language, lexeme.lemma) < minimum:
            continue
        if mix and not _matches_mix(language, lexeme, mix):
            continue
        out.append(lexeme)
    return out


def _matches_mix(language, lexeme: Lexeme, mix: Iterable[str]) -> bool:
    vowel_final = ends_in_vowel(language, lexeme.lemma)
    return ("vowel_final" in mix and vowel_final) or ("consonant_final" in mix and not vowel_final)


def pick_lexeme(language, params: dict, rng: random.Random) -> Lexeme:
    pool = candidate_lexemes(language, params)
    if not pool:
        raise GenerationError(f"no lexeme satisfies {params!r}")
    return rng.choice(pool)


def chain(params: dict, suffix_id: str) -> list[str]:
    """The full suffix chain for one choice, with any fixed prefix prepended.

    Nominal predication needs only one suffix (ev + PRED1SG), which is all
    every generator built before this. A verb's person needs two (gel + PROG
    + PRED1SG): tense is fixed for a given exercise, person is what varies,
    and inflect() needs both in slot order. base_suffixes is that fixed
    prefix; a generator that never sets it behaves exactly as before.
    """
    return list(params.get("base_suffixes", ())) + [suffix_id]


def suffix_choices(params: dict) -> list[str]:
    """The suffixes an exercise may use, however its params spell it."""
    if params.get("suffix"):
        return [params["suffix"]]
    for key in ("persons", "suffixes"):
        if params.get(key):
            return list(params[key])
    return []


def require_suffixes(exercise, params: dict) -> list[str]:
    """The suffixes this exercise may use.

    An exercise that names none inherits the ones its concept teaches, which is
    already in the content. Repeating them on every exercise would be a second
    place to keep them in step.
    """
    choices = suffix_choices(params) or list(getattr(exercise, "teaches_suffixes", ()) or ())
    if not choices:
        raise GenerationError(
            f"{exercise.id}: no suffix parameter, and its concept teaches none"
        )
    return choices


# ── deliberately wrong forms ─────────────────────────────────────────────────
# Distractors are produced by running the engine with one rule disabled, so a
# wrong option is always a form a learner could plausibly reach for, and is
# always wrong for a reason the diagnosis can name.

def _unrounded_twin(language, vowel: str) -> str | None:
    """The vowel that differs from this one only by being unrounded.

    Derived from the feature table rather than listed, so a language with a
    different vowel inventory gets the same treatment for free.
    """
    phonology = language.phonology
    if not phonology.is_vowel(vowel) or not phonology.is_rounded(vowel):
        return None
    for other in phonology.vowels:
        if (not phonology.is_rounded(other)
                and phonology.is_back(other) == phonology.is_back(vowel)
                and phonology.is_high(other) == phonology.is_high(vowel)):
            return other
    return None


def rounding_error(language, lexeme: Lexeme, suffix_ids: Sequence[str]) -> str | None:
    """The form a learner produces when they apply backness and forget rounding.

    Backness and rounding are one rule in the grammar and two habits in a
    learner, and rounding is the one English speakers drop. Flipping the whole
    stem would produce a backness error instead, which is a different mistake,
    so only the suffix vowels are unrounded here.
    """
    result = language.inflect(lexeme, list(suffix_ids))
    suffix_part = result.surface[len(result.stem_form):]
    rebuilt = "".join(_unrounded_twin(language, ch) or ch for ch in suffix_part)
    if rebuilt == suffix_part:
        return None
    return result.stem_form + rebuilt


def broken_variants(language, lexeme: Lexeme, suffix_ids: Sequence[str]) -> dict[str, str]:
    """Ungrammatical forms, keyed by the rule that was suppressed."""
    correct = language.inflect(lexeme, list(suffix_ids)).surface
    out: dict[str, str] = {}

    vowel = language.phonology.last_vowel(lexeme.lemma)
    if vowel is not None:
        back = (language.phonology.is_back(vowel) if lexeme.harmony_class is None
                else lexeme.harmony_class == "back")
        out["harmony_backness"] = replace(lexeme, harmony_class="front" if back else "back")
    if lexeme.final_voicing:
        out["stem_alternation"] = replace(lexeme, final_voicing=False)
    if lexeme.vowel_deletion:
        out["vowel_deletion"] = replace(lexeme, vowel_deletion=False)

    forms: dict[str, str] = {}
    for tag, variant in out.items():
        try:
            form = language.inflect(variant, list(suffix_ids)).surface
        except Exception:
            continue
        if form != correct:
            forms[tag] = form

    rounding = rounding_error(language, lexeme, suffix_ids)
    if rounding and rounding != correct:
        forms["harmony_rounding"] = rounding
    return forms


def one_broken_form(language, lexeme: Lexeme, suffix_ids: Sequence[str],
                    rng: random.Random, prefer: str | None = None) -> tuple[str, str]:
    """A single wrong form and the rule it breaks."""
    variants = broken_variants(language, lexeme, suffix_ids)
    if prefer and prefer in variants:
        return prefer, variants[prefer]
    if not variants:
        raise GenerationError(f"no distractor available for {lexeme.lemma}")
    tag = rng.choice(sorted(variants))
    return tag, variants[tag]


def english_cue(language, lexeme: Lexeme, suffix_ids: Sequence[str]) -> str:
    """An English prompt built from the glosses in content.

    Deliberately plain. Composing idiomatic English from glosses would mean
    inventing English morphology the content does not have.
    """
    parts = [language.suffix(s).glosses[0] for s in suffix_ids
             if language.suffix(s).glosses]
    if not parts:
        return lexeme.gloss
    return f"{lexeme.gloss}, made {' and '.join(parts)}"
