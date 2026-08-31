"""Request and response shapes."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_guest: bool


class SuffixOut(BaseModel):
    id: str
    notation: str
    glosses: list[str]


class ItemPayload(BaseModel):
    stem: str
    gloss: str
    suffix: SuffixOut
    options: list[str]


class ItemOut(BaseModel):
    """What the client renders. The answer is deliberately absent."""
    item_token: str
    exercise_id: str
    concept_id: str
    concept_name: str
    unit_id: str
    unit_title: str
    stage: str
    generator: str
    prompt: str
    payload: ItemPayload
    source: str


class AnswerIn(BaseModel):
    item_token: str
    answer: str = Field(max_length=128)
    attempt: int = Field(default=1, ge=1, le=10)
    latency_ms: int | None = Field(default=None, ge=0, le=1000 * 60 * 30)


class DerivationStepOut(BaseModel):
    rule: str
    condition: str
    result: str
    form: str


class AnswerOut(BaseModel):
    correct: bool
    kind: str
    message: str
    tags: list[str] = []
    elicitation: str | None = None
    answer: str | None = None
    derivation: list[DerivationStepOut] | None = None
    mastery: float | None = None
    due_at: dt.datetime | None = None


class ConceptOut(BaseModel):
    id: str
    name: str
    type: str
    why_hard: str
    teaches_suffixes: list[str]


class UnitOut(BaseModel):
    id: str
    order: int
    title: str
    rationale: str
    research_refs: list[str]
    prerequisites: list[str]
    concepts: list[ConceptOut]
