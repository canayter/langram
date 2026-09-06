"""phrase.py composes more than one word without touching inflect() at all,
so it is tested the same way: known inputs, known outputs.
"""
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
