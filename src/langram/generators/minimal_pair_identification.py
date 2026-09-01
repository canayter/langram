"""Two forms, one of them possible Turkish.

Comprehension only: the learner picks, and produces nothing. The wrong option is
made by running the engine with one rule suppressed, so it is wrong for exactly
one nameable reason.

Modality is text. The content parameter says so rather than the prompt implying
a recording that does not exist yet; when talkers are recorded, this generator
gains an audio payload and the parameter flips. See docs/deferred-audio.md.
"""
from __future__ import annotations

import random

from . import MORPHOLOGICAL, GeneratedItem
from ._common import one_broken_form, pick_lexeme, require_suffixes

_PREFERRED = {
    "wrong_harmony": "harmony_backness",
    "wrong_rounding": "harmony_rounding",
    "wrong_backness": "harmony_backness",
    "stem_final_consonant": "stem_alternation",
}


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})

    # A person contrast puts two well formed words side by side, differing only
    # in who is being talked about. On paper the answer is simply readable, so
    # the item only means anything once there is a recording to listen to.
    if str(params.get("contrast")) == "person" and params.get("modality") != "text":
        from . import GenerationError
        raise GenerationError(
            f"{exercise.id}: a person contrast needs recorded talkers. "
            f"See docs/deferred-audio.md"
        )

    suffix_id = rng.choice(require_suffixes(exercise, params))
    prefer = _PREFERRED.get(str(params.get("distractor") or params.get("contrast") or ""))

    # A handful of draws rather than one, because not every stem can break every
    # rule: a stem that does not alternate has no alternation distractor.
    for _ in range(12):
        lexeme = pick_lexeme(language, params, rng)
        try:
            tag, _form = one_broken_form(language, lexeme, [suffix_id], rng, prefer=prefer)
        except Exception:
            continue
        return assemble(exercise, language,
                        {"lemma": lexeme.lemma, "suffixes": [suffix_id], "tag": tag})
    raise_no_pair(exercise)


def raise_no_pair(exercise):
    from . import GenerationError
    raise GenerationError(f"{exercise.id}: no stem in the pool yields a minimal pair")


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    lemma, suffix_ids = spec["lemma"], list(spec["suffixes"])
    lexeme = language.lexeme(lemma)
    result = language.inflect(lexeme, suffix_ids)

    rng = random.Random(f"{lemma}|{'+'.join(suffix_ids)}|{spec.get('tag')}")
    tag, wrong = one_broken_form(language, lexeme, suffix_ids, rng, prefer=spec.get("tag"))

    options = [result.surface, wrong]
    random.Random(f"pair|{lemma}|{tag}").shuffle(options)

    suffix = language.suffix(suffix_ids[0])
    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator="minimal_pair_identification",
        stage=exercise.stage,
        prompt=exercise.prompt or "Which one is possible Turkish?",
        spec={"lemma": lemma, "suffixes": suffix_ids, "tag": tag},
        payload={
            "kind": "choose_form",
            "stem": lexeme.lemma,
            "gloss": lexeme.gloss,
            "suffix": {"id": suffix.id, "notation": suffix.surface,
                       "glosses": list(suffix.glosses)},
            "options": options,
            "modality": params_modality(exercise),
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
        extra={"broken_rule": tag},
    )


def params_modality(exercise) -> str:
    return str((exercise.params or {}).get("modality", "text"))
