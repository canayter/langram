"""The IPA sketch is a deterministic function of spelling, so it is testable
the same way the morphology engine is: known inputs, known outputs, and a
property that must hold no matter what word goes in.
"""
import pytest
from hypothesis import given, strategies as st

from langram.ipa import transcribe
from langram.loader import load_language


@pytest.fixture(scope="module")
def phonology():
    return load_language("tr").phonology


class TestKnownForms:
    @pytest.mark.parametrize("word, expected", [
        ("kitap", "/kitap/"),
        ("ev", "/ev/"),
        ("araba", "/aɾaba/"),
        ("çocuk", "/tʃodʒuk/"),
        ("şeker", "/ʃekeɾ/"),
        ("yol", "/joɫ/"),
        ("cam", "/dʒam/"),
    ])
    def test_straightforward_words(self, phonology, word, expected):
        assert transcribe(phonology, word) == expected

    def test_dotless_i_is_the_close_back_unrounded_vowel(self, phonology):
        assert transcribe(phonology, "ısı") == "/ɯsɯ/"

    def test_front_rounded_vowels(self, phonology):
        assert transcribe(phonology, "üzüm") == "/yzym/"
        assert transcribe(phonology, "göz") == "/gøz/"

    def test_soft_g_lengthens_the_preceding_vowel(self, phonology):
        assert transcribe(phonology, "dağ") == "/daː/"
        assert transcribe(phonology, "öğrenci") == "/øːɾendʒi/"

    def test_clear_l_next_to_a_front_vowel(self, phonology):
        assert "l" in transcribe(phonology, "el") and "ɫ" not in transcribe(phonology, "el")

    def test_l_darkness_is_local_not_whole_word(self, phonology):
        """bilgisayar's only l sits next to a front vowel even though the
        word's final vowel is back; the l stays clear, matching the vowel
        actually next to it rather than the word as a whole."""
        result = transcribe(phonology, "bilgisayar")
        assert "l" in result
        assert "ɫ" not in result

    def test_dark_l_after_a_back_word(self, phonology):
        result = transcribe(phonology, "kol")
        assert "ɫ" in result and result.count("l") == 0


class TestProperties:
    @given(st.sampled_from(["a", "e", "ı", "i", "o", "ö", "u", "ü", "b", "k", "l", "y", "c"]))
    def test_output_is_always_slash_delimited(self, phonology, letter):
        result = transcribe(phonology, letter)
        assert result.startswith("/") and result.endswith("/")

    def test_never_emits_a_raw_soft_g(self, phonology):
        """ğ is never itself a phoneme in this transcription; it always
        resolves to length on something else."""
        for word in ("dağ", "öğrenci", "bilgisayar", "yağmur"):
            assert "ğ" not in transcribe(phonology, word)

    def test_transcription_is_deterministic(self, phonology):
        assert transcribe(phonology, "arkadaş") == transcribe(phonology, "arkadaş")
