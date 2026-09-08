"""Free output for the accusative specificity contrast: say it in Turkish,
unprompted. A thin wrapper around accusative.py's "type" mode, the same way
question_production.py wraps question.py.
"""
from __future__ import annotations

import random

from . import GeneratedItem
from . import accusative as _base

GENERATOR = "accusative_production"
DEFAULT_PROMPT = "Say this in Turkish."


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    return _base.build(exercise, language, rng, mode="type")


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    return _base.assemble(exercise, language, spec, generator=GENERATOR,
                          default_prompt=DEFAULT_PROMPT)
