"""Existence and possession: param yok, arkadaşımın arabası var.

Turkish has no verb "to have": possession is "the possessor's thing
exists". The possessed noun carries an ordinary possessive suffix (already
taught in unit 3) and var or yok stands in for a verb where English needs
one. Negation of existence is always yok, never değil -- a specific, well
documented fact, not an oversight that -mA or a bare negative copula could
cover.

The first generator built on phrase.py rather than a single inflect() call:
the possessed noun is inflected exactly the way any other exercise inflects
one, and var/yok is appended as a second, invariant word. This module is
the recognition (structured_input) half; existence_production.py is the
free_output half, a thin wrapper the same way cued_recall.py wraps
type_the_form.py, since a curriculum exercise's registered generator name
has to match its own single stage.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, MORPHOLOGICAL, GeneratedItem, GenerationError
from ._common import candidate_lexemes
from .. import phrase

GENERATOR = "existence"
DEFAULT_PROMPT = "What does this mean?"

POSSESSIVE = ["POSS1SG", "POSS2SG", "POSS1PL", "POSS2PL", "POSS3SG"]
PARTICLES = ["var", "yok"]

# Deliberately plain, the same stance english_cue() already takes elsewhere
# in this codebase: composing "I have" from a possessive suffix's own gloss
# ("my") would mean inventing English subject-verb agreement the content
# does not have, so the mapping is written out instead of derived.
_SUBJECT_VERB = {
    "POSS1SG": ("I", "have", "do not have"),
    "POSS2SG": ("you", "have", "do not have"),
    "POSS1PL": ("we", "have", "do not have"),
    "POSS2PL": ("you (plural)", "have", "do not have"),
    "POSS3SG": ("he, she or it", "has", "does not have"),
}


def _cue(suffix_id: str, particle: str, gloss: str) -> str:
    subject, have, have_not = _SUBJECT_VERB[suffix_id]
    return f"{subject} {have if particle == 'var' else have_not} {gloss}"


def build(exercise, language, rng: random.Random, mode: str = "meaning") -> GeneratedItem:
    params = dict(exercise.params or {})
    pool = candidate_lexemes(language, params)
    if not pool:
        raise GenerationError(f"{exercise.id}: no lexeme available")
    lexeme = rng.choice(pool)
    suffix_id = rng.choice(params.get("suffixes") or POSSESSIVE)
    particle = rng.choice(params.get("particles") or PARTICLES)
    return assemble(exercise, language, {
        "mode": mode, "lemma": lexeme.lemma, "suffixes": [suffix_id], "particle": particle,
        "question": bool(params.get("question")),
    })


def assemble(exercise, language, spec: dict, generator: str = GENERATOR,
             default_prompt: str = DEFAULT_PROMPT) -> GeneratedItem:
    mode = spec.get("mode", "meaning")
    lemma, suffix_ids, particle = spec["lemma"], list(spec["suffixes"]), spec["particle"]
    lexeme = language.lexeme(lemma)
    # var/yok never carry a person suffix (it already lives on the
    # possessed noun), so a question here is just mI added bare, unlike
    # question.py's nominal/progressive/ability bases where the person
    # ending moves onto the particle.
    parts = [phrase.Word(lemma, suffix_ids), phrase.Literal(particle)]
    if spec.get("question"):
        parts.append(phrase.QuestionParticle())
    result = phrase.render(language, parts)
    cue = _cue(suffix_ids[0], particle, lexeme.gloss)

    if mode == "type":
        payload = {
            "kind": "type", "cue": cue, "stem": lexeme.lemma, "gloss": lexeme.gloss,
            "suffix": {"id": suffix_ids[0], "notation": language.suffix(suffix_ids[0]).surface,
                       "glosses": list(language.suffix(suffix_ids[0]).glosses)},
        }
        diagnosis = MORPHOLOGICAL
    else:
        # Every person on the same noun and particle: guarantees a genuine
        # choice (who has it), never a coincidental repeat.
        options = sorted({_cue(sid, particle, lexeme.gloss) for sid in POSSESSIVE})
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
        extra={"mode": mode, "particle": particle},
    )
