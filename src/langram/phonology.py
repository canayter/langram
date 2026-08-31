"""Turkish phonological primitives.

Every fact this module knows comes from content/l2/tr/morphology/phonology.yaml.
Nothing about Turkish is written into the code, so correcting the language means
editing YAML, and adding a related language (Tatar, Azerbaijani) means adding a
file rather than branching the engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Phonology:
    vowels: Mapping[str, Mapping[str, bool]]
    voiceless: frozenset[str]
    archiphonemes: Mapping[str, Mapping]
    final_voicing: Mapping[str, str]
    final_voicing_exceptions: tuple

    # ── features ─────────────────────────────────────────────────────────────
    def is_vowel(self, char: str) -> bool:
        return char in self.vowels

    def is_back(self, vowel: str) -> bool:
        return bool(self.vowels[vowel]["back"])

    def is_rounded(self, vowel: str) -> bool:
        return bool(self.vowels[vowel]["rounded"])

    def is_high(self, vowel: str) -> bool:
        return bool(self.vowels[vowel]["high"])

    def is_voiceless(self, char: str) -> bool:
        return char in self.voiceless

    def last_vowel(self, form: str) -> str | None:
        for char in reversed(form):
            if char in self.vowels:
                return char
        return None

    # ── archiphoneme resolution ──────────────────────────────────────────────
    def resolve(self, archiphoneme: str, context: str, back: bool | None = None) -> str:
        """Resolve one archiphoneme against the form it is being attached to.

        `back` overrides the backness read off the context, which is how a
        disharmonic loan takes front suffixes despite a back final vowel.
        """
        spec = self.archiphonemes[archiphoneme]
        if spec["type"] == "consonant":
            voiced = not (context and self.is_voiceless(context[-1]))
            return spec["resolves"]["voiced" if voiced else "voiceless"]

        vowel = self.last_vowel(context)
        if vowel is None:
            raise ValueError(f"cannot resolve {archiphoneme!r} against {context!r}: no vowel")
        is_back = self.is_back(vowel) if back is None else back
        table = spec["resolves"]
        if archiphoneme == "A":
            return table["back" if is_back else "front"]
        rounded = self.is_rounded(vowel)
        key = f"{'back' if is_back else 'front'}_{'rounded' if rounded else 'unrounded'}"
        return table[key]

    # ── stem alternations ────────────────────────────────────────────────────
    def voice_final(self, stem: str) -> str:
        """Voice a stem-final obstruent. Caller decides whether it applies."""
        if not stem:
            return stem
        for exc in self.final_voicing_exceptions:
            ending = exc["when_stem_ends_with"]
            if stem.endswith(ending):
                return stem[: -len(exc["replace"])] + exc["with"]
        voiced = self.final_voicing.get(stem[-1])
        return stem[:-1] + voiced if voiced else stem

    def can_voice_final(self, stem: str) -> bool:
        return bool(stem) and stem[-1] in self.final_voicing

    def delete_last_vowel(self, stem: str) -> str:
        """Syncope: drop the vowel of the final syllable. burun -> burn."""
        for i in range(len(stem) - 1, -1, -1):
            if stem[i] in self.vowels:
                return stem[:i] + stem[i + 1:]
        return stem

    @classmethod
    def from_dict(cls, data: Mapping) -> "Phonology":
        return cls(
            vowels=data["vowels"],
            voiceless=frozenset(data["voiceless"]),
            archiphonemes=data["archiphonemes"],
            final_voicing=data["final_voicing"],
            final_voicing_exceptions=tuple(data.get("final_voicing_exceptions", ())),
        )
