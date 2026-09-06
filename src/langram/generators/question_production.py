"""Free output for yes/no questions: ask it in Turkish, unprompted.

A thin wrapper around question.py's "type" mode, the same way
existence_production.py wraps existence.py.
"""
from __future__ import annotations

import random

from . import GeneratedItem
from . import question as _base

GENERATOR = "question_production"
DEFAULT_PROMPT = "Ask this in Turkish."


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    return _base.build(exercise, language, rng, mode="type")


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    return _base.assemble(exercise, language, spec, generator=GENERATOR,
                          default_prompt=DEFAULT_PROMPT)
