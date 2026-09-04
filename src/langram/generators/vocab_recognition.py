"""Vocabulary recognition: the bare word, not the grammar.

Every other generator here exercises a suffix. This one exercises the
lexicon itself, deliberately: connecting a form to its meaning is a meaning
task, not the isolated paradigm drill the working agreement's
long-focus-on-form citation warns against (that citation is about grammar
taught apart from meaning-primary activity; this generator's whole content
*is* meaning). See docs/pedagogy-rationale.md.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, GeneratedItem, GenerationError
from ._common import candidate_lexemes

OPTION_COUNT = 4


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})
    pool = candidate_lexemes(language, params)
    if len(pool) < OPTION_COUNT:
        raise GenerationError(f"{exercise.id}: not enough reviewed lexemes for {OPTION_COUNT} options")

    target = rng.choice(pool)
    others = [lx for lx in pool if lx.id != target.id and lx.gloss != target.gloss]
    distractors = rng.sample(others, min(OPTION_COUNT - 1, len(others)))

    return assemble(exercise, language, {
        "lemma": target.lemma,
        "distractors": [lx.lemma for lx in distractors],
    })


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    lemma = spec["lemma"]
    lexeme = language.lexeme(lemma)
    distractor_glosses = [language.lexeme(l).gloss for l in spec["distractors"]]

    options = [lexeme.gloss] + distractor_glosses
    # Deterministic: assemble() has to rebuild the identical item a review
    # card refers to, not just an item with the same right answer.
    random.Random(f"vocab|{lemma}|{'+'.join(spec['distractors'])}").shuffle(options)

    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator="vocab_recognition",
        stage=exercise.stage,
        prompt=exercise.prompt or "What does this word mean?",
        spec=spec,
        payload={"kind": "choose_meaning", "form": lexeme.lemma, "gloss": "", "options": options},
        answer=lexeme.gloss,
        accepted=(lexeme.gloss,),
        diagnosis=COMPREHENSION,
        lemma=lemma,
    )
