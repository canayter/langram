"""Command line front end for the morphology engine.

    inflect kitap ACC
    inflect ev PL POSS1SG LOC
    inflect --paradigm cocuk
    inflect --review
"""
from __future__ import annotations

import argparse
import sys

from .loader import load_language

CASES = ["NOM", "ACC", "DAT", "LOC", "ABL", "GEN"]


def _derive(lang, stem: str, suffix_ids: list[str], plain: bool) -> int:
    try:
        result = lang.inflect(stem, suffix_ids)
    except KeyError as err:
        print(str(err).strip("'"), file=sys.stderr)
        return 1
    if plain:
        print(result.surface)
    else:
        print(result.render_trace())
    return 0


def _paradigm(lang, stem: str) -> int:
    try:
        lexeme = lang.lexeme(stem)
    except KeyError as err:
        print(str(err).strip("'"), file=sys.stderr)
        return 1
    notes = []
    if lexeme.final_voicing:
        notes.append("final voicing")
    if lexeme.vowel_deletion:
        notes.append("vowel deletion")
    if lexeme.harmony_class:
        notes.append(f"{lexeme.harmony_class} harmony class")
    header = f"{lexeme.lemma}  ({lexeme.gloss})"
    if notes:
        header += "  [" + ", ".join(notes) + "]"
    print(header)
    print()
    print(f"  {'':10} {'singular':<16} plural")
    for case in CASES:
        singular = lang.inflect(lexeme, [case]).surface
        plural = lang.inflect(lexeme, ["PL", case]).surface
        print(f"  {case:<10} {singular:<16} {plural}")
    print()
    print("  possessive")
    for poss in ["POSS1SG", "POSS2SG", "POSS3SG", "POSS1PL", "POSS2PL", "POSS3PL"]:
        print(f"  {poss:<10} {lang.inflect(lexeme, [poss]).surface}")
    if lexeme.review:
        print()
        print("  NEEDS REVIEW: " + ", ".join(lexeme.review))
    return 0


def _review(lang) -> int:
    items = lang.needs_review
    if not items:
        print("Nothing flagged.")
        return 0
    print(f"{len(items)} item(s) a native speaker should confirm.")
    print()
    for item in items:
        name = getattr(item, "lemma", None) or item.id
        gloss = getattr(item, "gloss", "") or ", ".join(getattr(item, "glosses", ()))
        print(f"  {name:<12} {gloss:<28} {', '.join(item.review)}")
    print()
    print("Each flag names the field to check. See docs/provenance.md.")
    return 0


def _force_utf8() -> None:
    """Windows consoles default to cp1252, which cannot encode i, s, g or o with
    their diacritics. A Turkish CLI that cannot print Turkish is not a CLI."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):    # pragma: no cover
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    parser = argparse.ArgumentParser(
        prog="inflect",
        description="Apply Turkish suffixes to a stem and show the derivation.",
    )
    parser.add_argument("stem", nargs="?", help="a lemma from the lexicon, for example kitap")
    parser.add_argument("suffixes", nargs="*", help="suffix ids in slot order, for example PL POSS1SG LOC")
    parser.add_argument("--lang", default="tr", help="language code (default tr)")
    parser.add_argument("--plain", action="store_true", help="print only the surface form")
    parser.add_argument("--paradigm", action="store_true", help="print the full nominal paradigm")
    parser.add_argument("--review", action="store_true", help="list everything flagged for review")
    parser.add_argument("--list-suffixes", action="store_true", help="list available suffix ids")
    args = parser.parse_args(argv)

    lang = load_language(args.lang)

    if args.review:
        return _review(lang)
    if args.list_suffixes:
        for slot in sorted({s.slot for s in lang.suffixes.values()}):
            ids = [s.id for s in lang.suffixes.values() if s.slot == slot]
            print(f"  slot {slot}: {' '.join(ids)}")
        return 0
    if not args.stem:
        parser.print_help()
        return 2
    if args.paradigm:
        return _paradigm(lang, args.stem)
    return _derive(lang, args.stem, args.suffixes, args.plain)


if __name__ == "__main__":
    raise SystemExit(main())
