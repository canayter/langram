"""phrase.py composes more than one word without touching inflect() at all,
so it is tested the same way: known inputs, known outputs.
"""
import pytest

from langram import phrase
from langram.loader import load_language

TR = load_language("tr")


def test_a_bare_word_and_an_invariant_particle():
    result = phrase.render(TR, [phrase.Word("kedi", ["POSS1SG"]), phrase.Literal("var")])
    assert result.surface == "kedim var"
    assert result.words == ("kedim", "var")


def test_final_devoicing_still_applies_inside_a_phrase():
    result = phrase.render(TR, [phrase.Word("çocuk", ["POSS2PL"]), phrase.Literal("var")])
    assert result.surface == "çocuğunuz var"


def test_negation_of_existence_is_yok_not_a_suffix():
    result = phrase.render(TR, [phrase.Word("para", ["POSS1SG"]), phrase.Literal("yok")])
    assert result.surface == "param yok"


def test_plain_existence_with_no_suffix_at_all():
    result = phrase.render(TR, [phrase.Word("araba"), phrase.Literal("var")])
    assert result.surface == "araba var"


def test_derivation_includes_a_step_for_the_literal():
    result = phrase.render(TR, [phrase.Word("ev", ["POSS1SG"]), phrase.Literal("var")])
    assert any(step.rule == "literal" for step in result.derivation)
    # The word's own steps (buffer, harmony, attach...) are still there,
    # not replaced by the literal step.
    assert any(step.rule != "literal" for step in result.derivation)


def test_a_literal_never_inflects_regardless_of_the_preceding_word():
    front = phrase.render(TR, [phrase.Word("ev", ["POSS1SG"]), phrase.Literal("var")])
    back = phrase.render(TR, [phrase.Word("araba", ["POSS1SG"]), phrase.Literal("var")])
    assert front.words[-1] == back.words[-1] == "var"


class TestQuestionParticle:
    """mI: fourfold harmony against whatever precedes it, and -- unlike a
    Literal -- it can itself take a further suffix chain, since a person
    ending moves onto mI rather than staying on the predicate for a
    present-tense/aorist-shaped verb or an ordinary nominal predicate."""

    def test_harmonizes_all_four_ways(self):
        assert phrase.render(TR, [phrase.Word("doktor"), phrase.QuestionParticle()]).words[-1] == "mu"
        assert phrase.render(TR, [phrase.Word("öğrenci"), phrase.QuestionParticle()]).words[-1] == "mi"
        assert phrase.render(TR, [phrase.Word("büyük"), phrase.QuestionParticle()]).words[-1] == "mü"
        assert phrase.render(TR, [phrase.Word("araba"), phrase.QuestionParticle()]).words[-1] == "mı"

    def test_var_yok_take_no_suffix_and_mi_just_follows(self):
        result = phrase.render(TR, [
            phrase.Word("araba", ["POSS1SG"]), phrase.Literal("var"), phrase.QuestionParticle(),
        ])
        assert result.surface == "arabam var mı"
        result = phrase.render(TR, [
            phrase.Word("para", ["POSS1SG"]), phrase.Literal("yok"), phrase.QuestionParticle(),
        ])
        assert result.surface == "param yok mu"

    def test_person_moves_onto_mi_for_a_nominal_predicate(self):
        """öğrenci misin, never öğrencisin mi: the person ending is on the
        particle, not on the noun."""
        result = phrase.render(TR, [phrase.Word("öğrenci"), phrase.QuestionParticle(["PRED2SG"])])
        assert result.surface == "öğrenci misin"

    def test_person_moves_onto_mi_after_present_progressive(self):
        """geliyor musun, never geliyorsun mu -- the canonical textbook
        example for this rule."""
        result = phrase.render(TR, [phrase.Word("gel", ["PROG"]), phrase.QuestionParticle(["PRED2SG"])])
        assert result.surface == "geliyor musun"

    def test_person_moves_onto_mi_after_ability(self):
        result = phrase.render(TR, [
            phrase.Word("gel", ["ABIL", "ABILTENSE"]), phrase.QuestionParticle(["PRED1SG"]),
        ])
        assert result.surface == "gelebilir miyim"

    def test_bare_third_person_needs_no_suffix_on_mi_either(self):
        result = phrase.render(TR, [phrase.Word("gel", ["PROG"]), phrase.QuestionParticle()])
        assert result.surface == "geliyor mu"

    def test_mi_without_a_preceding_part_is_an_error(self):
        with pytest.raises(ValueError):
            phrase.render(TR, [phrase.QuestionParticle()])
