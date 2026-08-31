"""Scheduled recall.

The same task as free output, reached by the review scheduler rather than by
working through a unit. Kept separate because the stage differs, and stage is
what the tutor orders by.
"""
from __future__ import annotations

import random

from . import GeneratedItem
from . import type_the_form as _free

DEFAULT_PROMPT = "You have seen this before. Say it in Turkish."


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    item = _free.build(exercise, language, rng)
    return assemble(exercise, language, item.spec)


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    return _free.assemble(exercise, language, spec,
                          generator="cued_recall", default_prompt=DEFAULT_PROMPT)
