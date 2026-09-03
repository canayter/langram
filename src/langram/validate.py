"""Validate every content file: shape first, then meaning.

JSON Schema catches malformed content. The semantic checks below catch content
that is well formed and still wrong: a unit citing a source that is not in the
bibliography, a concept that asks for production before comprehension, an em
dash in learner-facing copy. Run in CI, so none of it reaches a learner.

    python -m langram.validate
    python -m langram.validate --write-bibliography
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .generators import REGISTRY, unimplemented
from .loader import CONTENT_ROOT

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
BIBLIOGRAPHY_DOC = ROOT / "docs" / "bibliography.md"

# The working agreement forbids em dashes in user-facing copy. These are the
# fields a learner actually reads.
LEARNER_FACING = ("title", "rationale", "why_hard", "intro", "prompt", "name", "gloss", "claim")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def _rel(path: Path) -> str:
    """Repo-relative where possible. Content under test lives outside the repo,
    and an error message must never be the thing that crashes."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def _load_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _schema(name: str) -> Draft202012Validator:
    with (SCHEMAS / name).open(encoding="utf-8") as fh:
        return Draft202012Validator(json.load(fh))


def _check_schema(report: Report, path: Path, schema_name: str, data) -> bool:
    validator = _schema(schema_name)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    for err in errors:
        where = "/".join(str(p) for p in err.path) or "(root)"
        report.error(f"{_rel(path)}: {where}: {err.message}")
    return not errors


def _check_em_dashes(report: Report, path: Path, node, trail: str = "") -> None:
    """The one style rule that is a project rule, enforced rather than trusted."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in LEARNER_FACING and isinstance(value, str) and "—" in value:
                report.error(
                    f"{_rel(path)}: {trail}{key}: contains an em dash, "
                    f"which the working agreement forbids in user-facing copy"
                )
            _check_em_dashes(report, path, value, f"{trail}{key}.")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _check_em_dashes(report, path, item, f"{trail}{i}.")


def validate(content_root: Path | None = None) -> Report:
    report = Report()
    content = content_root or CONTENT_ROOT
    tr = content / "l2" / "tr"

    # ── bibliography ─────────────────────────────────────────────────────────
    bib_path = content / "bibliography.yaml"
    bibliography = _load_yaml(bib_path)
    _check_schema(report, bib_path, "bibliography.schema.json", bibliography)
    _check_em_dashes(report, bib_path, bibliography)
    bib_keys = {entry["key"] for entry in bibliography}
    if len(bib_keys) != len(bibliography):
        report.error("bibliography.yaml: duplicate keys")
    unverified = [e["key"] for e in bibliography if e["status"] == "needs_citation"]
    if unverified:
        report.note(f"{len(unverified)} of {len(bibliography)} sources still need a real citation")

    # ── phonology ────────────────────────────────────────────────────────────
    ph_path = tr / "morphology" / "phonology.yaml"
    phonology = _load_yaml(ph_path)
    _check_schema(report, ph_path, "phonology.schema.json", phonology)

    # ── suffixes ─────────────────────────────────────────────────────────────
    sfx_path = tr / "morphology" / "suffixes.yaml"
    suffixes = _load_yaml(sfx_path)
    _check_schema(report, sfx_path, "suffixes.schema.json", suffixes)
    _check_em_dashes(report, sfx_path, suffixes)
    suffix_ids = {s["id"] for s in suffixes}
    if len(suffix_ids) != len(suffixes):
        report.error("suffixes.yaml: duplicate suffix ids")
    # A literal vowel in a suffix is an allomorph, and allomorphs belong in
    # engine output rather than in content. Turkish does have suffixes with
    # fixed vowels (-Iyor, -ki), so there is an opt-out, but it must be said
    # out loud.
    turkish_vowels = set("aeıioöuü")
    for s in suffixes:
        literal = sorted(set(s["surface"]) & turkish_vowels)
        if literal and not s.get("has_fixed_vowel"):
            report.error(
                f"suffixes.yaml: {s['id']} writes literal vowel(s) {''.join(literal)!r} in "
                f"{s['surface']!r}. Use an archiphoneme (A, I), or declare has_fixed_vowel "
                f"if this suffix genuinely does not harmonize"
            )

    for s in suffixes:
        for blocked in s.get("cannot_follow", []):
            if blocked not in suffix_ids:
                report.error(f"suffixes.yaml: {s['id']}.cannot_follow references unknown suffix {blocked}")

    # ── lexicon ──────────────────────────────────────────────────────────────
    lex_path = tr / "lexicon" / "lexemes.yaml"
    lexemes = _load_yaml(lex_path)
    _check_schema(report, lex_path, "lexemes.schema.json", lexemes)
    _check_em_dashes(report, lex_path, lexemes)
    lemmas = [x["lemma"] for x in lexemes]
    if len(set(lemmas)) != len(lemmas):
        dupes = sorted({l for l in lemmas if lemmas.count(l) > 1})
        report.error(f"lexemes.yaml: duplicate lemmas: {', '.join(dupes)}")
    alternating = set(phonology["final_voicing"])
    for entry in lexemes:
        lemma = entry["lemma"]
        if lemma[-1] in alternating and "final_voicing" not in entry:
            report.error(
                f"lexemes.yaml: {lemma} ends in /{lemma[-1]}/ and must declare "
                f"final_voicing; it cannot be predicted from the spelling"
            )
    flagged = [e["lemma"] for e in lexemes if e.get("review")]
    if flagged:
        report.note(f"{len(flagged)} lexemes await a native speaker: run inflect --review")

    # ── curriculum ───────────────────────────────────────────────────────────
    unit_paths = sorted((tr / "curriculum").glob("unit-*.yaml"))
    if not unit_paths:
        report.warn("no curriculum units found")
    units, seen_concepts, orders = [], {}, {}
    for path in unit_paths:
        unit = _load_yaml(path)
        if not _check_schema(report, path, "curriculum-unit.schema.json", unit):
            continue
        _check_em_dashes(report, path, unit)
        units.append((path, unit))

        if unit["id"] != path.stem:
            report.error(f"{path.name}: id {unit['id']} does not match the file name")
        if unit["order"] in orders:
            report.error(f"{path.name}: order {unit['order']} already used by {orders[unit['order']]}")
        orders[unit["order"]] = unit["id"]

        for ref in unit["research_refs"]:
            if ref not in bib_keys:
                report.error(f"{path.name}: research_ref {ref!r} is not in bibliography.yaml")

        for concept in unit["concepts"]:
            if concept["id"] in seen_concepts:
                report.error(
                    f"{path.name}: concept id {concept['id']!r} already defined in "
                    f"{seen_concepts[concept['id']]}"
                )
            seen_concepts[concept["id"]] = unit["id"]

            for suffix_id in concept.get("teaches_suffixes", []):
                if suffix_id not in suffix_ids:
                    report.error(f"{path.name}: {concept['id']} teaches unknown suffix {suffix_id}")

            stages = set()
            exercise_ids = set()
            for ex in concept["exercises"]:
                if ex["id"] in exercise_ids:
                    report.error(f"{path.name}: duplicate exercise id {ex['id']} in {concept['id']}")
                exercise_ids.add(ex["id"])
                stages.add(ex["stage"])
                generator = REGISTRY.get(ex["generator"])
                if generator is None:
                    report.error(
                        f"{path.name}: {ex['id']} uses unregistered generator "
                        f"{ex['generator']!r}; add it to langram.generators"
                    )
                elif generator.stage != ex["stage"]:
                    report.error(
                        f"{path.name}: {ex['id']} is stage {ex['stage']} but generator "
                        f"{generator.name} produces {generator.stage} items"
                    )

            # Input before output is a design commitment, not a preference.
            if stages & {"guided_output", "free_output"} and "structured_input" not in stages:
                report.error(
                    f"{path.name}: concept {concept['id']!r} asks for production with no "
                    f"structured input stage first (see bibliography: vanpatten-input-processing)"
                )

    order_values = sorted(orders)
    if order_values and order_values != list(range(1, len(order_values) + 1)):
        report.warn(f"unit order has gaps: {order_values}")

    order_of = {u["id"]: u["order"] for _, u in units}
    for path, unit in units:
        for prereq in unit.get("prerequisites", []):
            if prereq not in order_of:
                report.error(f"{path.name}: prerequisite {prereq!r} does not exist")
            elif order_of[prereq] >= unit["order"]:
                report.error(
                    f"{path.name}: prerequisite {prereq!r} is taught at or after this unit"
                )

    pending = unimplemented()
    if pending:
        report.note(f"{len(pending)} generators are declared but not implemented yet (Phase 4)")

    return report


def render_bibliography(content_root: Path | None = None) -> str:
    content = content_root or CONTENT_ROOT
    entries = _load_yaml(content / "bibliography.yaml")
    areas = {
        "sla": "Second language acquisition",
        "memory": "Memory and practice",
        "l2-speech": "L2 speech and perception",
        "turkish": "Turkish",
        "assessment": "Assessment",
    }
    lines = [
        "# Bibliography",
        "",
        "Generated from `content/bibliography.yaml`. Do not edit this file by hand;",
        "edit the YAML and run `python -m langram.validate --write-bibliography`.",
        "",
        "Entries marked NEEDS CITATION name a real tradition and a real claim, but the",
        "reference itself has not been checked. Inventing one to fill the gap is",
        "forbidden by the working agreement.",
        "",
    ]
    for area, heading in areas.items():
        group = [e for e in entries if e.get("area") == area]
        if not group:
            continue
        lines += [f"## {heading}", ""]
        for entry in sorted(group, key=lambda e: e["key"]):
            bits = [b for b in (entry.get("authors"), str(entry.get("year", "")) or None) if b]
            byline = ", ".join(bits)
            status = "" if entry["status"] == "verified" else "  **NEEDS CITATION**"
            lines.append(f"- `{entry['key']}`{(' ' + byline) if byline else ''}{status}")
            lines.append(f"  {' '.join(entry['claim'].split())}")
        lines.append("")
    ungrouped = [e for e in entries if e.get("area") not in areas]
    if ungrouped:
        lines += ["## Uncategorised", ""]
        for entry in ungrouped:
            lines.append(f"- `{entry['key']}`")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="langram-validate", description=__doc__)
    parser.add_argument("--write-bibliography", action="store_true",
                        help="regenerate docs/bibliography.md from content/bibliography.yaml")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):    # pragma: no cover
            pass

    if args.write_bibliography:
        BIBLIOGRAPHY_DOC.write_text(render_bibliography(), encoding="utf-8", newline="\n")
        print(f"wrote {BIBLIOGRAPHY_DOC.relative_to(ROOT)}")

    report = validate()

    current = BIBLIOGRAPHY_DOC.read_text(encoding="utf-8") if BIBLIOGRAPHY_DOC.exists() else ""
    if current.replace("\r\n", "\n") != render_bibliography():
        report.error("docs/bibliography.md is out of date; run --write-bibliography")

    for note in report.notes:
        print(f"  note: {note}")
    for warning in report.warnings:
        print(f"  warning: {warning}")
    for error in report.errors:
        print(f"  ERROR: {error}")

    if report.ok:
        print("content is valid")
        return 0
    print(f"\n{len(report.errors)} error(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
