"""Request and response shapes."""
from __future__ import annotations

import datetime as dt

from typing import Any

from pydantic import BaseModel, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_guest: bool


class WordInfoOut(BaseModel):
    """Meaning and pronunciation for the stem an item is about. Never leaks
    an inflected surface form: only the lemma an exercise already shows."""
    lemma: str
    gloss: str
    ipa: str
    ipa_caveat: str
    etymology: str | None = None


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
    # Generator specific by design: a judgement shows a form and yes or no, a
    # cloze shows suffixes, a typing item shows an English cue. Pinning one
    # shape here would mean every new exercise type edits this file. The
    # discriminator is payload["kind"].
    payload: dict[str, Any]
    source: str
    word_info: WordInfoOut | None = None


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
    intro: str
    teaches_suffixes: list[str]


class UnitOut(BaseModel):
    id: str
    order: int
    title: str
    rationale: str
    research_refs: list[str]
    prerequisites: list[str]
    concepts: list[ConceptOut]


class SkillReportOut(BaseModel):
    """One linguistic rule, and how reliably it is being applied."""
    skill: str
    label: str
    opportunities: int
    errors: int
    accuracy: float | None
    summary: str
    confident: bool


class ConceptProgressOut(BaseModel):
    id: str
    name: str
    unit_id: str
    unit_title: str
    why_hard: str
    p_known: float
    opportunities: int
    correct: int
    status: str


class ProgressOut(BaseModel):
    answered: int
    correct: int
    accuracy: float | None
    headline: str
    skills: list[SkillReportOut]
    concepts: list[ConceptProgressOut]
    note: str
