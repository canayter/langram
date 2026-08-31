"""Free output: produce the Turkish.

No options. The learner types, and the answer is compared with engine output
after Turkish-aware normalisation, so a capital I does not count as a mistake
the learner did not make.
"""
from __future__ import annotations

import random

from . import MORPHOLOGICAL, GeneratedItem
from ._common import english_cue, pick_lexeme, require_suffixes

GENERATOR = "type_the_form"
DEFAULT_PROMPT = "Say this in Turkish."


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})
    suffix_id = rng.choice(require_suffixes(exercise, params))
    lexeme = pick_lexeme(language, params, rng)
    return assemble(exercise, language, {"lemma": lexeme.lemma, "suffixes": [suffix_id]})


def assemble(exercise, language, spec: dict, generator: str = GENERATOR,
             default_prompt: str = DEFAULT_PROMPT) -> GeneratedItem:
    lemma, suffix_ids = spec["lemma"], list(spec["suffixes"])
    lexeme = language.lexeme(lemma)
    result = language.inflect(lexeme, suffix_ids)
    suffix = language.suffix(suffix_ids[0])

    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator=generator,
        stage=exercise.stage,
        prompt=exercise.prompt or default_prompt,
        spec={"lemma": lemma, "suffixes": suffix_ids},
        payload={
            "kind": "type",
            "cue": english_cue(language, lexeme, suffix_ids),
            "stem": lexeme.lemma,
            "gloss": lexeme.gloss,
            "suffix": {"id": suffix.id, "notation": suffix.surface,
                       "glosses": list(suffix.glosses)},
        },
        answer=result.surface,
        accepted=(result.surface,),
        derivation=tuple(
            {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
            for s in result.steps
        ),
        diagnosis=MORPHOLOGICAL,
        lemma=lemma,
        suffixes=tuple(suffix_ids),
    )
