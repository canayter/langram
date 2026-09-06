"""Postpositions that take a bare noun: araba için, çocuk gibi.

için (for) and gibi (like) both govern the bare, unmarked noun with an
ordinary noun (the genitive is only needed before a pronoun, which this
lexicon does not have yet, so that alternation is out of scope here, not
overlooked). Neither noun needs any naturalness curation the way existence's
var/yok did: "for a car" and "like a car" are natural for essentially any
noun, unlike "I have a car" or "you are a car".

Built on phrase.py the same way existence.py is, since the answer is two
words, a noun and an invariant postposition, not one inflected stem.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, MORPHOLOGICAL, GeneratedItem, GenerationError
from ._common import candidate_lexemes
from .. import phrase

GENERATOR = "postposition"
DEFAULT_PROMPT = "What does this mean?"

POSTPOSITIONS = {
    "için": "for",
    "gibi": "like",
}


def _cue(postposition: str, gloss: str) -> str:
    return f"{POSTPOSITIONS[postposition]} {gloss}"


def build(exercise, language, rng: random.Random, mode: str = "meaning") -> GeneratedItem:
    params = dict(exercise.params or {})
    pool = candidate_lexemes(language, params)
    if not pool:
        raise GenerationError(f"{exercise.id}: no lexeme available")
    lexeme = rng.choice(pool)
    postposition = rng.choice(params.get("postpositions") or list(POSTPOSITIONS))
    return assemble(exercise, language, {"mode": mode, "lemma": lexeme.lemma,
                                         "postposition": postposition})


def assemble(exercise, language, spec: dict, generator: str = GENERATOR,
             default_prompt: str = DEFAULT_PROMPT) -> GeneratedItem:
    mode = spec.get("mode", "meaning")
    lemma, postposition = spec["lemma"], spec["postposition"]
    lexeme = language.lexeme(lemma)
    result = phrase.render(language, [phrase.Word(lemma), phrase.Literal(postposition)])
    cue = _cue(postposition, lexeme.gloss)

    if mode == "type":
        payload = {"kind": "type", "cue": cue, "stem": lexeme.lemma, "gloss": lexeme.gloss,
                   "suffix": {"id": postposition, "notation": postposition, "glosses": []}}
        diagnosis = MORPHOLOGICAL
    else:
        # The other postposition on the same noun: a genuine minimal
        # contrast (için vs gibi), never a coincidental repeat, and never
        # a choice that turns on the noun instead of the postposition.
        options = sorted({_cue(p, lexeme.gloss) for p in POSTPOSITIONS})
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
        suffixes=(),
        extra={"mode": mode, "postposition": postposition},
    )
