"""Load a language's content files into memory.

Content is version-controlled YAML. This module reads it, validates the things
that must not be silently wrong, and hands back an immutable Language.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from .engine import inflect
from .models import InflectionResult, Lexeme, Suffix
from .phonology import Phonology

CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content"


class ContentError(ValueError):
    """A content file says something the engine cannot act on."""


@dataclass(frozen=True)
class Language:
    code: str
    phonology: Phonology
    lexemes: Mapping[str, Lexeme]
    suffixes: Mapping[str, Suffix]

    def inflect(self, lemma: str | Lexeme, suffix_ids: Sequence[str] = ()) -> InflectionResult:
        lexeme = lemma if isinstance(lemma, Lexeme) else self.lexeme(lemma)
        suffixes = [self.suffix(s) for s in suffix_ids]
        return inflect(lexeme, suffixes, self.phonology)

    def lexeme(self, lemma: str) -> Lexeme:
        try:
            return self.lexemes[lemma]
        except KeyError:
            raise KeyError(f"no lexeme {lemma!r} in the {self.code} lexicon") from None

    def suffix(self, suffix_id: str) -> Suffix:
        try:
            return self.suffixes[suffix_id]
        except KeyError:
            raise KeyError(f"no suffix {suffix_id!r} in the {self.code} morphology") from None

    @property
    def needs_review(self) -> list[Lexeme | Suffix]:
        items = [x for x in self.lexemes.values() if x.review]
        items += [x for x in self.suffixes.values() if x.review]
        return items


def _read(path: Path):
    if not path.exists():
        raise ContentError(f"missing content file: {path}")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_language(code: str = "tr", root: Path | None = None) -> Language:
    base = (root or CONTENT_ROOT) / "l2" / code
    phonology = Phonology.from_dict(_read(base / "morphology" / "phonology.yaml"))

    suffixes: dict[str, Suffix] = {}
    for raw in _read(base / "morphology" / "suffixes.yaml"):
        suffix = Suffix(
            id=raw["id"],
            surface=raw.get("surface", ""),
            category=raw["category"],
            slot=int(raw["slot"]),
            glosses=tuple(raw.get("glosses", ())),
            triggers_pronominal_n=bool(raw.get("triggers_pronominal_n", False)),
            review=tuple(raw.get("review", ())),
        )
        if suffix.id in suffixes:
            raise ContentError(f"duplicate suffix id: {suffix.id}")
        suffixes[suffix.id] = suffix

    lexemes: dict[str, Lexeme] = {}
    for raw in _read(base / "lexicon" / "lexemes.yaml"):
        lemma = raw["lemma"]
        # A stem ending in one of the four alternating obstruents must say
        # whether it alternates. It cannot be derived, and a silent default
        # would put a wrong form in front of a learner.
        if lemma[-1] in phonology.final_voicing and "final_voicing" not in raw:
            raise ContentError(
                f"{lemma!r} ends in /{lemma[-1]}/ and must declare final_voicing "
                f"(kitap -> kitabi but sepet -> sepeti)"
            )
        harmony_class = raw.get("harmony_class")
        if harmony_class not in (None, "front", "back"):
            raise ContentError(f"{lemma!r}: harmony_class must be front or back")
        lexeme = Lexeme(
            id=raw.get("id", lemma),
            lemma=lemma,
            pos=raw["pos"],
            gloss=raw.get("gloss", ""),
            final_voicing=bool(raw.get("final_voicing", False)),
            vowel_deletion=bool(raw.get("vowel_deletion", False)),
            harmony_class=harmony_class,
            review=tuple(raw.get("review", ())),
        )
        if lexeme.lemma in lexemes:
            raise ContentError(f"duplicate lemma: {lexeme.lemma}")
        lexemes[lexeme.lemma] = lexeme

    return Language(code=code, phonology=phonology, lexemes=lexemes, suffixes=suffixes)
