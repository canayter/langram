"""Unit tests for the phonological primitives.

These are the rules everything else stands on, so they are tested in isolation
before any suffix is applied.
"""
import pytest

from langram import load_language

TR = load_language("tr")
P = TR.phonology


class TestVowelInventory:
    def test_eight_vowels(self):
        assert set(P.vowels) == set("aeiıoöuü")

    @pytest.mark.parametrize("vowel,back", [
        ("a", True), ("ı", True), ("o", True), ("u", True),
        ("e", False), ("i", False), ("ö", False), ("ü", False),
    ])
    def test_backness(self, vowel, back):
        assert P.is_back(vowel) is back

    @pytest.mark.parametrize("vowel,rounded", [
        ("o", True), ("ö", True), ("u", True), ("ü", True),
        ("a", False), ("e", False), ("ı", False), ("i", False),
    ])
    def test_rounding(self, vowel, rounded):
        assert P.is_rounded(vowel) is rounded

    @pytest.mark.parametrize("word,vowel", [
        ("kitap", "a"), ("ev", "e"), ("araba", "a"),
        ("çocuk", "u"), ("gözlük", "ü"), ("kız", "ı"),
    ])
    def test_last_vowel(self, word, vowel):
        assert P.last_vowel(word) == vowel

    def test_last_vowel_of_vowelless_string_is_none(self):
        assert P.last_vowel("str") is None


class TestTwofoldHarmony:
    """The A archiphoneme: backness only."""

    @pytest.mark.parametrize("stem,expected", [
        ("kitap", "a"), ("araba", "a"), ("kız", "a"), ("okul", "a"),
        ("ev", "e"), ("göz", "e"), ("gün", "e"), ("şehir", "e"),
    ])
    def test_resolves_on_backness(self, stem, expected):
        assert P.resolve("A", stem) == expected


class TestFourfoldHarmony:
    """The I archiphoneme: backness and rounding."""

    @pytest.mark.parametrize("stem,expected", [
        ("kitap", "ı"),   # back unrounded
        ("kız", "ı"),
        ("çocuk", "u"),   # back rounded
        ("okul", "u"),
        ("ev", "i"),      # front unrounded
        ("şehir", "i"),
        ("göz", "ü"),     # front rounded
        ("gün", "ü"),
    ])
    def test_resolves_on_backness_and_rounding(self, stem, expected):
        assert P.resolve("I", stem) == expected


class TestVoicingAssimilation:
    """The D archiphoneme, and the voiceless set."""

    @pytest.mark.parametrize("char", list("fstkçşhp"))
    def test_voiceless_set(self, char):
        assert P.is_voiceless(char)

    @pytest.mark.parametrize("char", list("bcdgğjlmnrvyz") + list("aeiıoöuü"))
    def test_everything_else_is_voiced(self, char):
        assert not P.is_voiceless(char)

    @pytest.mark.parametrize("stem,expected", [
        ("kitap", "t"), ("ağaç", "t"), ("sepet", "t"), ("çocuk", "t"),
        ("ev", "d"), ("araba", "d"), ("göz", "d"), ("okul", "d"),
    ])
    def test_D_assimilates(self, stem, expected):
        assert P.resolve("D", stem) == expected


class TestFinalVoicing:
    """Stem-final obstruent voicing, for lexemes that alternate."""

    @pytest.mark.parametrize("stem,expected", [
        ("kitap", "kitab"),
        ("ağaç", "ağac"),
        ("kanat", "kanad"),
        ("çocuk", "çocuğ"),
        ("renk", "reng"),      # k after n gives g, not the soft g
        ("ahenk", "aheng"),
    ])
    def test_voices_final_obstruent(self, stem, expected):
        assert P.voice_final(stem) == expected

    def test_leaves_non_obstruent_finals_alone(self):
        assert P.voice_final("ev") == "ev"
