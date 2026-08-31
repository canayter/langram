"""The validator is only worth having if it fails on bad content.

Each test copies the real content into a temporary tree, breaks one thing, and
asserts the validator catches exactly that. A validator that has only ever seen
valid content proves nothing.
"""
import shutil

import pytest
import yaml

from langram.loader import CONTENT_ROOT
from langram.validate import render_bibliography, validate


@pytest.fixture
def content(tmp_path):
    """A writable copy of the real content tree."""
    dest = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, dest)
    return dest


def _write(path, data):
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


def _read(path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _errors(content):
    return "\n".join(validate(content).errors)


class TestTheRealContent:
    def test_ships_valid(self):
        report = validate()
        assert report.ok, "\n".join(report.errors)

    def test_reports_what_is_still_pending(self):
        notes = " ".join(validate().notes)
        assert "citation" in notes
        assert "native speaker" in notes


class TestSchemaFailures:
    def test_unknown_field_in_lexeme(self, content):
        path = content / "l2" / "tr" / "lexicon" / "lexemes.yaml"
        data = _read(path)
        data[0]["colour"] = "blue"
        _write(path, data)
        assert "colour" in _errors(content)

    def test_bad_suffix_notation(self, content):
        path = content / "l2" / "tr" / "morphology" / "suffixes.yaml"
        data = _read(path)
        # A surface allomorph rather than an archiphoneme: exactly what the
        # working agreement forbids anywhere outside engine output.
        next(s for s in data if s["id"] == "ACC")["surface"] = "-yi"
        _write(path, data)
        errors = _errors(content)
        assert "literal vowel" in errors
        assert "archiphoneme" in errors

    def test_a_genuinely_fixed_vowel_can_opt_out(self, content):
        """Turkish does have non-harmonizing suffix vowels (-Iyor, -ki). The
        check must be escapable, but only by saying so explicitly."""
        path = content / "l2" / "tr" / "morphology" / "suffixes.yaml"
        data = _read(path)
        data.append({
            "id": "PROG", "surface": "-Iyor", "category": "tense", "slot": 5,
            "glosses": ["progressive"], "has_fixed_vowel": True,
        })
        _write(path, data)
        assert "literal vowel" not in _errors(content)

    def test_unit_missing_rationale(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        del data["rationale"]
        _write(path, data)
        assert "rationale" in _errors(content)


class TestSemanticFailures:
    def test_lexeme_ending_in_an_alternating_stop_must_declare_voicing(self, content):
        path = content / "l2" / "tr" / "lexicon" / "lexemes.yaml"
        data = _read(path)
        del next(x for x in data if x["lemma"] == "kitap")["final_voicing"]
        _write(path, data)
        assert "final_voicing" in _errors(content)

    def test_duplicate_lemma(self, content):
        path = content / "l2" / "tr" / "lexicon" / "lexemes.yaml"
        data = _read(path)
        data.append(dict(data[0]))
        _write(path, data)
        assert "duplicate lemmas" in _errors(content)

    def test_citation_that_is_not_in_the_bibliography(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        data["research_refs"].append("krashen-monitor-model")
        _write(path, data)
        assert "krashen-monitor-model" in _errors(content)
        assert "bibliography" in _errors(content)

    def test_concept_teaching_an_unknown_suffix(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        data["concepts"][0]["teaches_suffixes"] = ["ABESSIVE"]
        _write(path, data)
        assert "ABESSIVE" in _errors(content)

    def test_unregistered_generator(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        data["concepts"][0]["exercises"][0]["generator"] = "vibes_based_drill"
        _write(path, data)
        assert "vibes_based_drill" in _errors(content)

    def test_generator_used_at_the_wrong_stage(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        data["concepts"][0]["exercises"][0]["generator"] = "suffix_builder"
        _write(path, data)
        assert "produces guided_output items" in _errors(content)

    def test_production_without_comprehension_first(self, content):
        """The input-before-output commitment, enforced rather than trusted."""
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        concept = data["concepts"][0]
        concept["exercises"] = [e for e in concept["exercises"] if e["stage"] != "structured_input"]
        _write(path, data)
        errors = _errors(content)
        assert "structured input" in errors
        assert "vanpatten" in errors

    def test_prerequisite_that_comes_later(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        data["prerequisites"] = ["unit-03-possession"]
        _write(path, data)
        assert "does not come earlier" in _errors(content) or "at or after" in _errors(content)

    def test_duplicate_concept_id_across_units(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-02-predication.yaml"
        data = _read(path)
        data["concepts"][0]["id"] = "twofold-harmony"      # already in unit 1
        _write(path, data)
        assert "already defined" in _errors(content)


class TestWorkingAgreement:
    def test_em_dash_in_learner_facing_copy_is_an_error(self, content):
        path = content / "l2" / "tr" / "curriculum" / "unit-01-vowel-harmony.yaml"
        data = _read(path)
        data["concepts"][0]["exercises"][0]["prompt"] = "Which word did you hear — the first?"
        _write(path, data)
        errors = _errors(content)
        assert "em dash" in errors

    def test_em_dash_in_a_gloss_is_an_error(self, content):
        path = content / "l2" / "tr" / "lexicon" / "lexemes.yaml"
        data = _read(path)
        data[0]["gloss"] = "man — adult male"
        _write(path, data)
        assert "em dash" in _errors(content)


class TestBibliographyDoc:
    def test_generated_doc_lists_every_key(self):
        text = render_bibliography()
        for key in ("vanpatten-input-processing", "logan-lively-pisoni-hvpt", "lobanov-normalization"):
            assert key in text

    def test_unverified_sources_are_marked(self):
        assert "NEEDS CITATION" in render_bibliography()
