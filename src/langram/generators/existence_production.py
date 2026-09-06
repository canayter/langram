"""Free output for existence/possession: say it in Turkish, unprompted.

A thin wrapper around existence.py's "type" mode, the same way cued_recall.py
wraps type_the_form.py: a curriculum exercise's registered generator name has
to match its own single stage, and existence.py's own name is already taken
by the structured_input (recognition) half.
"""
from __future__ import annotations

import random

from . import GeneratedItem
from . import existence as _base

GENERATOR = "existence_production"
DEFAULT_PROMPT = "Say this in Turkish."


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    return _base.build(exercise, language, rng, mode="type")


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    return _base.assemble(exercise, language, spec, generator=GENERATOR,
                          default_prompt=DEFAULT_PROMPT)
