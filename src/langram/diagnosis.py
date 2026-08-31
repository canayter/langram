"""What went wrong, and what to say about it.

Two things live here. Classification names the linguistic cause of a wrong
answer, so a report can say "you apply backness reliably and rounding about half
the time" instead of showing a percentage. Feedback turns that into a prompt that
pushes the learner to fix it themselves.

Both work by re-running the engine with one rule switched off. If disabling final
voicing reproduces exactly what the learner typed, that is what they missed. No
string heuristics, no guessing.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from .models import Lexeme

# Turkish casing is not English casing: "I".lower() is not "ı".
_LOWER = str.maketrans({"I": "ı", "İ": "i"})


def normalize(form: str) -> str:
    return form.strip().translate(_LOWER).lower()


def _counterfactuals(language, lexeme: Lexeme) -> dict[str, Lexeme]:
    """One variant per rule, each with a single rule suppressed."""
    variants: dict[str, Lexeme] = {}

    vowel = language.phonology.last_vowel(lexeme.lemma)
    if vowel is not None:
        back = language.phonology.is_back(vowel) if lexeme.harmony_class is None \
            else lexeme.harmony_class == "back"
        variants["harmony_backness"] = replace(lexeme, harmony_class="front" if back else "back")

    if lexeme.final_voicing:
        variants["stem_alternation"] = replace(lexeme, final_voicing=False)
    if lexeme.vowel_deletion:
        variants["vowel_deletion"] = replace(lexeme, vowel_deletion=False)
    return variants


def classify(language, lexeme: Lexeme, suffix_ids: Sequence[str],
             given: str, expected: str) -> tuple[str, ...]:
    """Name the rule the learner did not apply. Empty when they are right."""
    given_n, expected_n = normalize(given), normalize(expected)
    if given_n == expected_n:
        return ()

    tags: list[str] = []
    for tag, variant in _counterfactuals(language, lexeme).items():
        try:
            if normalize(language.inflect(variant, list(suffix_ids)).surface) == given_n:
                tags.append(tag)
        except Exception:                       # a variant the grammar refuses proves nothing
            continue

    if not tags and _differs_only_in_rounding(language, given_n, expected_n):
        tags.append("harmony_rounding")
    if not tags and _looks_like_a_missing_buffer(language, given_n, expected_n):
        tags.append("buffer_missing")
    return tuple(tags) or ("unclassified",)


def _differs_only_in_rounding(language, given: str, expected: str) -> bool:
    if len(given) != len(expected):
        return False
    phonology = language.phonology
    differences = [(g, e) for g, e in zip(given, expected) if g != e]
    if not differences:
        return False
    return all(
        phonology.is_vowel(g) and phonology.is_vowel(e)
        and phonology.is_back(g) == phonology.is_back(e)
        and phonology.is_rounded(g) != phonology.is_rounded(e)
        for g, e in differences
    )


def _looks_like_a_missing_buffer(language, given: str, expected: str) -> bool:
    """The learner produced the expected form minus one consonant."""
    if len(given) != len(expected) - 1:
        return False
    for i, char in enumerate(expected):
        if language.phonology.is_vowel(char):
            continue
        if expected[:i] + expected[i + 1:] == given:
            return True
    return False


# ── corrective feedback ──────────────────────────────────────────────────────
# Prompts before recasts. The learner is pushed to self-correct three times
# before the answer is handed over, which is the escalation the brief specifies.

_CLUES = {
    "harmony_backness": "The suffix vowel has to match the last vowel of the stem for backness. "
                        "Look at that vowel again.",
    "harmony_rounding": "Backness is right. This suffix also has to match the stem for rounding, "
                        "which is the half that is easy to drop.",
    "stem_alternation": "The stem itself changes here. A vowel is following it, and this word is "
                        "one of the ones whose final consonant softens.",
    "vowel_deletion": "This stem loses a vowel when something vowel-initial follows it.",
    "buffer_missing": "Two vowels cannot sit next to each other. Something has to come between them.",
    "unclassified": "Not quite. Compare the shape of the suffix with the last vowel of the stem.",
}


def feedback(language, lexeme: Lexeme, suffix_ids: Sequence[str], given: str,
             expected: str, attempt: int) -> dict:
    """One rung of the ladder. attempt is 1-based."""
    tags = classify(language, lexeme, suffix_ids, given, expected)
    if not tags:
        return {"kind": "correct", "tags": [], "message": "Correct."}

    tag = tags[0]
    if attempt <= 1:
        return {"kind": "clarification", "tags": list(tags),
                "message": "Not quite. Have another look at the end of the word."}
    if attempt == 2:
        return {"kind": "metalinguistic", "tags": list(tags), "message": _CLUES[tag]}
    if attempt == 3:
        return {"kind": "elicitation", "tags": list(tags),
                "message": "Try once more, one piece at a time.",
                "elicitation": f"{lexeme.lemma} + {'-'.join(suffix_ids)}"}

    result = language.inflect(lexeme, list(suffix_ids))
    return {
        "kind": "explicit",
        "tags": list(tags),
        "message": f"The form is {result.surface}. Here is how it is built.",
        "answer": result.surface,
        "derivation": [
            {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
            for s in result.steps
        ],
    }
