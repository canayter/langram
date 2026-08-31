"""Which shape does the suffix take.

The learner is given a stem and a suffix, and picks the shape. The options are
the suffix's real allomorphs, derived by running the engine over probe stems
rather than listed anywhere. If a new allomorph became possible tomorrow, this
exercise would offer it without anyone editing content.
"""
from __future__ import annotations

import random

from . import MORPHOLOGICAL, GeneratedItem
from ._common import allomorphs, ends_in_vowel, pick_lexeme, realisation, require_suffixes


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})
    suffix_id = rng.choice(require_suffixes(exercise, params))
    lexeme = pick_lexeme(language, params, rng)
    return assemble(exercise, language, {"lemma": lexeme.lemma, "suffixes": [suffix_id]})


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    lemma, suffix_ids = spec["lemma"], list(spec["suffixes"])
    lexeme = language.lexeme(lemma)
    suffix = language.suffix(suffix_ids[0])

    result = language.inflect(lexeme, suffix_ids)
    correct = realisation(language, lexeme, suffix_ids)

    # Distractors are the suffix's other shapes for this stem shape, so every
    # wrong option is one a learner could plausibly reach for.
    options = allomorphs(language, suffix_ids[0],
                         consonant_final=not ends_in_vowel(language, lemma))
    if correct not in options:
        options.append(correct)
    random.Random(f"{lemma}|{suffix.id}").shuffle(options)

    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator="suffix_builder",
        stage=exercise.stage,
        prompt=exercise.prompt or "Attach the suffix.",
        spec={"lemma": lemma, "suffixes": suffix_ids},
        payload={
            "kind": "choose_form",
            "stem": lexeme.lemma,
            "gloss": lexeme.gloss,
            "suffix": {"id": suffix.id, "notation": suffix.surface,
                       "glosses": list(suffix.glosses)},
            "options": options,
            "option_prefix": lexeme.lemma,
        },
        answer=result.surface,
        # Typing the whole word and picking the shape are both right.
        accepted=(result.surface, correct),
        derivation=tuple(
            {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
            for s in result.steps
        ),
        diagnosis=MORPHOLOGICAL,
        lemma=lemma,
        suffixes=tuple(suffix_ids),
    )
