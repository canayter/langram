"""Which suffix, rather than which shape.

The suffix builder takes the grammatical choice as given and asks for the
phonology. This asks the opposite: here is a meaning, which suffix expresses it.
Options are shown in archiphoneme notation, so choosing does not leak the shape.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, GeneratedItem, GenerationError
from ._common import pick_lexeme, suffix_choices


def _options(language, params: dict) -> list[str]:
    chosen = suffix_choices(params)
    if len(chosen) >= 2:
        return chosen
    # A single suffix is not a choice. Fall back to its whole category, which is
    # the set a learner actually has to choose between.
    if chosen:
        category = language.suffix(chosen[0]).category
    else:
        category = str(params.get("category") or "possessive")
    return [s.id for s in language.suffixes.values() if s.category == category]


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})
    options = _options(language, params)
    if len(options) < 2:
        raise GenerationError(f"{exercise.id}: a cloze needs at least two suffixes to choose from")
    lexeme = pick_lexeme(language, params, rng)
    return assemble(exercise, language, {
        "lemma": lexeme.lemma,
        "suffixes": [rng.choice(options)],
        "options": sorted(options),
    })


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    lemma, suffix_ids = spec["lemma"], list(spec["suffixes"])
    lexeme = language.lexeme(lemma)
    result = language.inflect(lexeme, suffix_ids)
    suffix = language.suffix(suffix_ids[0])

    options = [
        {"id": sid, "notation": language.suffix(sid).surface,
         "gloss": (language.suffix(sid).glosses or (sid,))[0]}
        for sid in spec["options"]
    ]
    random.Random(f"cloze|{lemma}").shuffle(options)

    meaning = (suffix.glosses or (suffix.id,))[0]
    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator="cloze_suffix_choice",
        stage=exercise.stage,
        prompt=exercise.prompt or "Which suffix expresses this?",
        spec=spec,
        payload={
            "kind": "choose_suffix",
            "stem": lexeme.lemma,
            "gloss": lexeme.gloss,
            "meaning": meaning,
            "options": options,
        },
        answer=suffix.id,
        # The id, the notation, and the finished word all identify the same choice.
        accepted=(suffix.id, suffix.surface, result.surface),
        derivation=tuple(
            {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
            for s in result.steps
        ),
        diagnosis=COMPREHENSION,
        lemma=lemma,
        suffixes=tuple(suffix_ids),
        extra={"surface": result.surface},
    )
