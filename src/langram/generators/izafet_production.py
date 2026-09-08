"""Free output for izafet: say "the student's book" in Turkish, unprompted.
A thin wrapper around izafet.py's "type" mode, the same way question_production.py
wraps question.py.
"""
from __future__ import annotations

import random

from . import GeneratedItem
from . import izafet as _base

GENERATOR = "izafet_production"
DEFAULT_PROMPT = "Say this in Turkish."


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    return _base.build(exercise, language, rng, mode="type")


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    return _base.assemble(exercise, language, spec, generator=GENERATOR,
                          default_prompt=DEFAULT_PROMPT)
