"""Which rules a form actually exercises.

An error count on its own says nothing. Ten backness mistakes out of five
hundred opportunities is fluency; ten out of twelve is a gap. So every response
records the rules the target form gave the learner a chance to apply, and the
report divides one by the other.

The rules come from the derivation rather than from a table, so a form exercises
exactly what the engine did to build it.
"""
from __future__ import annotations

from typing import Sequence

BACKNESS = "harmony_backness"
ROUNDING = "harmony_rounding"
ALTERNATION = "stem_alternation"
DELETION = "vowel_deletion"
BUFFER = "buffer_missing"

# Named for the learner rather than for the engine. These are the labels the
# diagnostic report speaks in.
LABELS = {
    BACKNESS: "backness harmony",
    ROUNDING: "rounding harmony",
    ALTERNATION: "stem alternation",
    DELETION: "vowel deletion",
    BUFFER: "buffer consonants",
}

# What a learner is actually doing wrong when they miss it, in one line.
EXPLANATIONS = {
    BACKNESS: "matching the suffix vowel to the last vowel of the stem for front or back",
    ROUNDING: "matching the suffix vowel for rounding as well as backness",
    ALTERNATION: "softening the final consonant of stems that alternate before a vowel",
    DELETION: "dropping the stem vowel in words that lose one before a vowel",
    BUFFER: "supplying the segment that keeps two vowels apart",
}


def _harmony_skills(language, archiphoneme: str) -> set[str]:
    """Backness alone, or backness and rounding.

    Read off the archiphoneme's own resolution table: a two way split is
    backness, a four way split is backness crossed with rounding.
    """
    spec = language.phonology.archiphonemes.get(archiphoneme)
    if not spec or spec.get("type") != "vowel":
        return set()
    return {BACKNESS, ROUNDING} if len(spec["resolves"]) > 2 else {BACKNESS}


def _archiphoneme_of(language, vowel: str) -> str | None:
    """Which archiphoneme could have produced this vowel.

    The two vowel archiphonemes resolve to disjoint sets, so a resolved vowel
    identifies its source without the engine having to say.
    """
    for name, spec in language.phonology.archiphonemes.items():
        if spec.get("type") == "vowel" and vowel in set(spec["resolves"].values()):
            return name
    return None


def skills_in(language, result) -> tuple[str, ...]:
    """The rules an InflectionResult gave the learner a chance to apply."""
    found: set[str] = set()
    for step in result.steps:
        detail = dict(step.detail or {})
        if step.rule == "final_voicing":
            found.add(ALTERNATION)
        elif step.rule == "vowel_deletion":
            found.add(DELETION)
        elif step.rule == "harmony":
            found |= _harmony_skills(language, detail.get("archiphoneme", ""))
        elif step.rule == "buffer":
            segment = detail.get("segment")
            if not segment:
                continue
            if language.phonology.is_vowel(segment):
                # A vowel buffer is the suffix's own harmonising vowel, so this
                # step is a harmony opportunity as well as a buffer one.
                archiphoneme = _archiphoneme_of(language, segment)
                if archiphoneme:
                    found |= _harmony_skills(language, archiphoneme)
            else:
                found.add(BUFFER)
    return tuple(sorted(found))


def skills_for(language, lemma: str, suffix_ids: Sequence[str]) -> tuple[str, ...]:
    try:
        return skills_in(language, language.inflect(lemma, list(suffix_ids)))
    except Exception:
        return ()


def describe(skill: str, accuracy: float | None, opportunities: int) -> str:
    """One sentence a learner can act on.

    A percentage is not actionable. Naming the rule and how reliably it is being
    applied is, which is the whole point of tagging errors by cause.
    """
    label = LABELS.get(skill, skill)
    if not opportunities:
        return f"You have not met {label} yet."
    if accuracy is None:
        return f"{label.capitalize()}: not enough attempts yet."
    percent = round(accuracy * 100)
    if opportunities < 5:
        return f"Too few attempts at {label} to say much yet."
    if accuracy >= 0.9:
        return f"You are applying {label} reliably."
    if accuracy >= 0.7:
        return f"{label.capitalize()} is mostly there, landing {percent} percent of the time."
    return (f"{label.capitalize()} is landing {percent} percent of the time. "
            f"The part to watch is {EXPLANATIONS.get(skill, label)}.")
