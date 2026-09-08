"""Izafet: the genitive-possessive construction. Unit 3 taught possessive
suffixes on a noun already named (kitabım, my book), which presupposes a
possessor already in the conversation. This teaches the other half: naming
the possessor explicitly, which is two suffixes on two different words
working together, not one -- öğrencinin kitabı, the student's book. The
possessor carries the genitive (-(n)In) and the possessed noun carries the
same POSS3SG (-(s)I) unit 3 already taught, never POSS1SG or any other
person: the possessor's identity is the noun phrase itself, not a pronoun,
so third person singular is the only shape this construction ever takes.

Built on phrase.py exactly like existence.py and accusative.py: two Words,
no Literal between them, since nothing but the two suffixes marks the
relationship.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, MORPHOLOGICAL, GeneratedItem, GenerationError
from ._common import candidate_lexemes
from .. import phrase

GENERATOR = "izafet"
DEFAULT_PROMPT = "What does this mean?"


def _cue(possessor_gloss: str, possessed_gloss: str, swapped: bool) -> str:
    if swapped:
        return f"the {possessed_gloss}'s {possessor_gloss}"
    return f"the {possessor_gloss}'s {possessed_gloss}"


def build(exercise, language, rng: random.Random, mode: str = "meaning") -> GeneratedItem:
    params = dict(exercise.params or {})
    possessor_params = dict(params.get("possessor_filter") or {"pos": "noun", "predicative_only": True})
    possessed_params = dict(params.get("possessed_filter") or {"pos": "noun", "possession_only": True})
    possessors = candidate_lexemes(language, {**params, "lexeme_filter": possessor_params})
    possessed_pool = candidate_lexemes(language, {**params, "lexeme_filter": possessed_params})
    if not possessors or not possessed_pool:
        raise GenerationError(f"{exercise.id}: no lexeme pair available")
    possessor = rng.choice(possessors)
    possessed = rng.choice([lx for lx in possessed_pool if lx.lemma != possessor.lemma] or possessed_pool)
    return assemble(exercise, language, {
        "mode": mode, "lemma": possessor.lemma, "possessed": possessed.lemma,
    })


def assemble(exercise, language, spec: dict, generator: str = GENERATOR,
             default_prompt: str = DEFAULT_PROMPT) -> GeneratedItem:
    mode = spec.get("mode", "meaning")
    # "lemma" rather than "possessor": every generator's spec carries a
    # "lemma" key card_ref() (tutor.py) relies on for review-card identity.
    # A caught-by-the-full-suite bug, not a stylistic choice -- izafet was
    # the first generator with two lexemes in one item and the first to
    # miss this.
    possessor_lemma, possessed_lemma = spec["lemma"], spec["possessed"]
    possessor = language.lexeme(possessor_lemma)
    possessed = language.lexeme(possessed_lemma)
    result = phrase.render(language, [
        phrase.Word(possessor_lemma, ["GEN"]), phrase.Word(possessed_lemma, ["POSS3SG"]),
    ])
    cue = _cue(possessor.gloss, possessed.gloss, swapped=False)

    if mode == "type":
        payload = {
            "kind": "type", "cue": cue, "stem": possessor.lemma, "gloss": possessor.gloss,
            "suffix": {"id": "GEN", "notation": language.suffix("GEN").surface,
                       "glosses": list(language.suffix("GEN").glosses)},
        }
        diagnosis = MORPHOLOGICAL
    else:
        # The swapped reading is the genuine distractor: same two nouns, same
        # two suffixes in the same slots, only which noun plays which role
        # reversed -- exactly the confusion an English speaker reaching for
        # "the book's student" instead would make.
        options = sorted({
            _cue(possessor.gloss, possessed.gloss, swapped=False),
            _cue(possessor.gloss, possessed.gloss, swapped=True),
        })
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
        lemma=possessor_lemma,
        suffixes=("GEN",),
        extra={"mode": mode, "possessed": possessed_lemma},
    )
