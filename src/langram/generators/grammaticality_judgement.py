"""Is this a possible Turkish word.

Half the items show engine output and half show engine output with one rule
suppressed, so a yes is only right when the form really is well formed. Still
comprehension: the learner judges rather than produces.
"""
from __future__ import annotations

import random

from . import JUDGEMENT, GeneratedItem, GenerationError
from ._common import one_broken_form, pick_lexeme, require_suffixes

YES, NO = "yes", "no"

_PREFERRED = {
    "wrong_rounding": "harmony_rounding",
    "wrong_harmony": "harmony_backness",
    "missing_or_extra_buffer": None,
}


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})
    if params.get("compare"):
        # A register judgement rather than a grammaticality one: both forms are
        # well formed and one is merely more natural. That claim is flagged for
        # native speaker review in the content, so it is not served yet.
        raise GenerationError(
            f"{exercise.id}: register comparison needs the -DIr claim confirmed first"
        )

    suffix_id = rng.choice(require_suffixes(exercise, params))
    grammatical = rng.random() < 0.5
    prefer = _PREFERRED.get(str(params.get("distractor") or ""))

    for _ in range(12):
        lexeme = pick_lexeme(language, params, rng)
        if grammatical:
            return assemble(exercise, language, {"lemma": lexeme.lemma,
                                                 "suffixes": [suffix_id], "grammatical": True})
        try:
            tag, _form = one_broken_form(language, lexeme, [suffix_id], rng, prefer=prefer)
        except Exception:
            continue
        return assemble(exercise, language, {"lemma": lexeme.lemma, "suffixes": [suffix_id],
                                             "grammatical": False, "tag": tag})
    raise GenerationError(f"{exercise.id}: no stem in the pool yields a broken form")


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    lemma, suffix_ids = spec["lemma"], list(spec["suffixes"])
    grammatical = bool(spec.get("grammatical", True))
    lexeme = language.lexeme(lemma)
    result = language.inflect(lexeme, suffix_ids)

    tag = spec.get("tag")
    if grammatical:
        shown = result.surface
    else:
        rng = random.Random(f"gj|{lemma}|{tag}")
        tag, shown = one_broken_form(language, lexeme, suffix_ids, rng, prefer=tag)

    suffix = language.suffix(suffix_ids[0])
    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator="grammaticality_judgement",
        stage=exercise.stage,
        prompt=exercise.prompt or "Is this a possible Turkish word?",
        spec={"lemma": lemma, "suffixes": suffix_ids,
              "grammatical": grammatical, **({"tag": tag} if tag else {})},
        payload={
            "kind": "judge",
            "form": shown,
            "gloss": lexeme.gloss,
            "suffix": {"id": suffix.id, "notation": suffix.surface,
                       "glosses": list(suffix.glosses)},
            "options": [YES, NO],
        },
        answer=YES if grammatical else NO,
        accepted=(YES,) if grammatical else (NO,),
        derivation=tuple(
            {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
            for s in result.steps
        ),
        diagnosis=JUDGEMENT,
        lemma=lemma,
        suffixes=tuple(suffix_ids),
        extra={"shown": shown, "well_formed": grammatical, "broken_rule": tag},
    )
