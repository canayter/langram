"""Yes/no questions with mI: öğrenci misin?, geliyor musun?, gelebilir misin?

Across every predicate type already taught except existence, the person
ending moves off the predicate and onto the question particle rather than
staying where a statement would put it: geliyor musun, never geliyorsun mu.
Built on phrase.py's QuestionParticle, which does that suffix-attachment
itself; this generator only has to pick which base predicate (nominal,
present progressive, ability) the question is asked about.

Existence's var mı / yok mu is its own case, handled in existence.py
instead: var and yok never carry a person suffix in the first place (it
already lives on the possessed noun), so there is no suffix-transfer for
this generator to model there.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, MORPHOLOGICAL, GeneratedItem, GenerationError
from ._common import candidate_lexemes, english_cue
from .. import phrase

GENERATOR = "question"
DEFAULT_PROMPT = "What does this ask?"

PERSONS = ["PRED1SG", "PRED2SG", "PRED1PL", "PRED2PL"]

BASES = {
    "nominal": (),
    "progressive": ("PROG",),
    "ability": ("ABIL", "ABILTENSE"),
}


def build(exercise, language, rng: random.Random, mode: str = "meaning") -> GeneratedItem:
    params = dict(exercise.params or {})
    pool = candidate_lexemes(language, params)
    if not pool:
        raise GenerationError(f"{exercise.id}: no lexeme available")
    lexeme = rng.choice(pool)
    base = params.get("base", "nominal")
    if base not in BASES:
        raise GenerationError(f"{exercise.id}: unknown question base {base!r}")
    person = rng.choice(params.get("persons") or PERSONS)
    return assemble(exercise, language, {
        "mode": mode, "lemma": lexeme.lemma, "base": base, "person": person,
    })


def assemble(exercise, language, spec: dict, generator: str = GENERATOR,
             default_prompt: str = DEFAULT_PROMPT) -> GeneratedItem:
    mode = spec.get("mode", "meaning")
    lemma, base, person = spec["lemma"], spec["base"], spec["person"]
    lexeme = language.lexeme(lemma)
    base_suffixes = list(BASES[base])
    result = phrase.render(language, [
        phrase.Word(lemma, base_suffixes), phrase.QuestionParticle([person]),
    ])
    # Same plain, non-idiomatic composition type_the_form already uses for
    # units 5 and 6 ("come, made is, is -ing and I am"): the question
    # reading is carried by the exercise's own prompt, not by inventing
    # English question-inversion grammar the content does not have.
    cue = english_cue(language, lexeme, base_suffixes + [person])

    if mode == "type":
        payload = {
            "kind": "type", "cue": cue, "stem": lexeme.lemma, "gloss": lexeme.gloss,
            "suffix": {"id": person, "notation": language.suffix(person).surface,
                       "glosses": list(language.suffix(person).glosses)},
        }
        diagnosis = MORPHOLOGICAL
    else:
        # Every person on the same lemma and base: a genuine choice (who
        # is being asked about), never a coincidental repeat.
        options = sorted({english_cue(language, lexeme, base_suffixes + [p]) for p in PERSONS})
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
        suffixes=tuple(base_suffixes + [person]),
        extra={"mode": mode, "base": base},
    )
