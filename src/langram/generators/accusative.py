"""The accusative marks specificity, not objecthood: kitap istiyorum (I want a
book, any book) versus kitabı istiyorum (I want the book, a specific one).
This is exactly VanPatten's structured-input case: the suffix has to be the
only cue to the meaning, or a learner skips right over it the way English
speakers reliably do, since English marks this distinction with an article
("a" vs "the") rather than a suffix on the object.

Built on phrase.py the same way existence.py is: the object noun is one Word,
istemek (want) in the present progressive, first person, is a second, fixed
Word. "iste" is used rather than a food- or reading-specific verb (oku, iç)
so any concrete noun is a natural object without curating a verb-by-object
pairing list.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, MORPHOLOGICAL, GeneratedItem, GenerationError
from ._common import candidate_lexemes
from .. import phrase

GENERATOR = "accusative"
DEFAULT_PROMPT = "What does this mean?"

VERB_SUFFIXES = ["PROG", "PRED1SG"]


def _cue(gloss: str, specific: bool) -> str:
    return f"I want the {gloss} (that one)" if specific else f"I want {gloss} (in general, any)"


def build(exercise, language, rng: random.Random, mode: str = "meaning") -> GeneratedItem:
    params = dict(exercise.params or {})
    pool = candidate_lexemes(language, params)
    if not pool:
        raise GenerationError(f"{exercise.id}: no lexeme available")
    lexeme = rng.choice(pool)
    specific = rng.choice([True, False])
    return assemble(exercise, language, {
        "mode": mode, "lemma": lexeme.lemma, "specific": specific,
    })


def assemble(exercise, language, spec: dict, generator: str = GENERATOR,
             default_prompt: str = DEFAULT_PROMPT) -> GeneratedItem:
    mode = spec.get("mode", "meaning")
    lemma, specific = spec["lemma"], bool(spec["specific"])
    lexeme = language.lexeme(lemma)
    object_suffixes = ["ACC"] if specific else []
    result = phrase.render(language, [
        phrase.Word(lemma, object_suffixes), phrase.Word("iste", VERB_SUFFIXES),
    ])
    cue = _cue(lexeme.gloss, specific)

    if mode == "type":
        payload = {
            "kind": "type", "cue": cue, "stem": lexeme.lemma, "gloss": lexeme.gloss,
            "suffix": {"id": "ACC", "notation": language.suffix("ACC").surface,
                       "glosses": list(language.suffix("ACC").glosses)},
        }
        diagnosis = MORPHOLOGICAL
    else:
        options = sorted({_cue(lexeme.gloss, s) for s in (True, False)})
        payload = {"kind": "choose_meaning", "form": result.surface, "gloss": "",
                   "options": options}
        diagnosis = COMPREHENSION

    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator=generator,
        stage=exercise.stage,
        prompt=exercise.prompt or default_prompt,
        spec=spec,
        payload=payload,
        answer=result.surface if mode == "type" else cue,
        accepted=(result.surface,) if mode == "type" else (cue,),
        derivation=tuple(
            {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
            for s in result.derivation
        ),
        diagnosis=diagnosis,
        lemma=lemma,
        suffixes=tuple(object_suffixes),
        extra={"mode": mode, "specific": specific},
    )
