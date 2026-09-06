"""Free output for postpositions: say it in Turkish, unprompted.

A thin wrapper around postposition.py's "type" mode, the same way
existence_production.py wraps existence.py: a curriculum exercise's
registered generator name has to match its own single stage.
"""
from __future__ import annotations

import random

from . import GeneratedItem
from . import postposition as _base

GENERATOR = "postposition_production"
DEFAULT_PROMPT = "Say this in Turkish."


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    return _base.build(exercise, language, rng, mode="type")


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    return _base.assemble(exercise, language, spec, generator=GENERATOR,
                          default_prompt=DEFAULT_PROMPT)
