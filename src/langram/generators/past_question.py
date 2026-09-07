"""Yes/no questions in the past tense: geldin mi?, okudun mu?

The past tense breaks the rule question.py teaches for every other predicate
type. There, the person ending moves off the predicate and onto mI
(geliyor musun, never geliyorsun mu). Here it does not: -DI's own person
paradigm (unit 10) stays on the verb exactly where a statement puts it, and
mI just follows, bare -- geldin mi, never geldi misin. Confirmed directly:
Göksel and Kerslake describe the past and conditional as the two tenses
where the personal ending is retained on the verb and mI attaches with no
further inflection, unlike every predicative-type ending.

Same phrase.py shape existence.py's var mı / yok mu already uses (a
QuestionParticle with no suffix chain, harmonizing bare against whatever
precedes it), not question.py's shape (a QuestionParticle that itself takes
the moved person suffix): the verb is inflected in full first, -DI and
person together, and mI is a second, invariant word after it.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, MORPHOLOGICAL, GeneratedItem, GenerationError
from ._common import candidate_lexemes, english_cue
from .. import phrase

GENERATOR = "past_question"
DEFAULT_PROMPT = "What does this ask?"

PERSONS = ["PAST1SG", "PAST2SG", "PAST1PL", "PAST2PL"]


def build(exercise, language, rng: random.Random, mode: str = "meaning") -> GeneratedItem:
    params = dict(exercise.params or {})
    pool = candidate_lexemes(language, params)
    if not pool:
        raise GenerationError(f"{exercise.id}: no lexeme available")
    lexeme = rng.choice(pool)
    person = rng.choice(params.get("persons") or PERSONS)
    return assemble(exercise, language, {"mode": mode, "lemma": lexeme.lemma, "person": person})


def assemble(exercise, language, spec: dict, generator: str = GENERATOR,
             default_prompt: str = DEFAULT_PROMPT) -> GeneratedItem:
    mode = spec.get("mode", "meaning")
    lemma, person = spec["lemma"], spec["person"]
    lexeme = language.lexeme(lemma)
    suffix_ids = ["DI", person]
    # No suffix chain on the particle, unlike question.py: the person stays
    # on the verb, so mI just harmonizes against it and stops there.
    result = phrase.render(language, [
        phrase.Word(lemma, suffix_ids), phrase.QuestionParticle(),
    ])
    cue = english_cue(language, lexeme, suffix_ids)

    if mode == "type":
        payload = {
            "kind": "type", "cue": cue, "stem": lexeme.lemma, "gloss": lexeme.gloss,
            "suffix": {"id": person, "notation": language.suffix(person).surface,
                       "glosses": list(language.suffix(person).glosses)},
        }
        diagnosis = MORPHOLOGICAL
    else:
        # Every person on the same lemma: a genuine choice (who is being
        # asked about), never a coincidental repeat.
        options = sorted({english_cue(language, lexeme, ["DI", p]) for p in PERSONS})
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
        suffixes=tuple(suffix_ids),
        extra={"mode": mode},
    )
