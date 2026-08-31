"""Lexeme, Suffix, and the derivation record."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Lexeme:
    id: str
    lemma: str
    pos: str
    gloss: str
    final_voicing: bool = False
    vowel_deletion: bool = False
    harmony_class: str | None = None      # "front" | "back" | None (derive it)
    review: tuple[str, ...] = ()

    @property
    def needs_review(self) -> bool:
        return bool(self.review)


@dataclass(frozen=True)
class Suffix:
    id: str
    surface: str                           # archiphoneme notation, e.g. "-(y)I"
    category: str
    slot: int
    glosses: tuple[str, ...] = ()
    triggers_pronominal_n: bool = False
    review: tuple[str, ...] = ()

    @property
    def is_overt(self) -> bool:
        return bool(self.surface)


@dataclass(frozen=True)
class DerivationStep:
    """One rule application, written to be read by a learner.

    The trace is a product feature, not a debugging aid: it is what makes the
    app teach the rule instead of the form.
    """
    rule: str                              # machine id, e.g. "final_voicing"
    condition: str                         # why it fired
    result: str                            # what it did
    form: str                              # the form after it fired
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InflectionResult:
    lexeme: Lexeme
    suffixes: tuple[Suffix, ...]
    surface: str
    stem_form: str                         # the stem after syncope and voicing
    steps: tuple[DerivationStep, ...]

    @property
    def suffix_region(self) -> str:
        """Everything the suffixes contributed, including any buffer segments."""
        return self.surface[len(self.stem_form):]

    def render_trace(self) -> str:
        """The learner-facing derivation.

        Bookkeeping steps that did not change the form are dropped here. They
        stay in .steps, which is the machine-readable record.
        """
        chain = " + ".join([self.lexeme.lemma] + [s.id for s in self.suffixes])
        lines = [chain]
        n = 0
        previous = self.steps[0].form if self.steps else ""
        for step in self.steps[1:]:
            if step.rule in ("attach", "zero_marker") and step.form == previous:
                continue
            n += 1
            lines.append(f"  {n}. {step.condition}")
            lines.append(f"     -> {step.result} [{step.rule}]: {step.form}")
            previous = step.form
        lines.append(f"  = {self.surface}")
        return "\n".join(lines)
