"""The oracle: known Turkish surface forms the engine must reproduce.

Every row here is a form a native speaker would produce. If the engine and this
table disagree, the engine is wrong until a linguist says otherwise.

Grouped by the phenomenon each row is there to pin down, so a failure names its
own cause.
"""
import pytest

from langram import load_language

TR = load_language("tr")


def surface(lemma, *suffix_ids):
    return TR.inflect(lemma, list(suffix_ids)).surface


# ── Plain stems, no alternation ──────────────────────────────────────────────
PLAIN = [
    ("ev", ["ACC"], "evi"),
    ("ev", ["DAT"], "eve"),
    ("ev", ["LOC"], "evde"),
    ("ev", ["ABL"], "evden"),
    ("ev", ["GEN"], "evin"),
    ("ev", ["PL"], "evler"),
    ("ev", ["INS"], "evle"),
    ("kız", ["ACC"], "kızı"),
    ("kız", ["DAT"], "kıza"),
    ("kız", ["LOC"], "kızda"),
    ("kız", ["GEN"], "kızın"),
    ("göz", ["ACC"], "gözü"),
    ("göz", ["DAT"], "göze"),
    ("göz", ["PL"], "gözler"),
    ("okul", ["ACC"], "okulu"),
    ("okul", ["LOC"], "okulda"),
    ("sepet", ["ACC"], "sepeti"),      # final t, but this stem does not alternate
    ("sepet", ["LOC"], "sepette"),
    ("top", ["ACC"], "topu"),          # final p, does not alternate
]

# ── Vowel-final stems: buffer consonants ─────────────────────────────────────
BUFFERED = [
    ("araba", ["ACC"], "arabayı"),
    ("araba", ["DAT"], "arabaya"),
    ("araba", ["LOC"], "arabada"),
    ("araba", ["ABL"], "arabadan"),
    ("araba", ["GEN"], "arabanın"),
    ("araba", ["PL"], "arabalar"),
    ("araba", ["POSS1SG"], "arabam"),       # the optional vowel drops
    ("araba", ["POSS3SG"], "arabası"),      # the s buffer appears
    ("araba", ["POSS1PL"], "arabamız"),
    ("kapı", ["ACC"], "kapıyı"),
    ("kapı", ["POSS3SG"], "kapısı"),
    ("ütü", ["ACC"], "ütüyü"),
    ("ütü", ["DAT"], "ütüye"),
]

# ── Final obstruent voicing ──────────────────────────────────────────────────
VOICING = [
    ("kitap", ["ACC"], "kitabı"),
    ("kitap", ["DAT"], "kitaba"),
    ("kitap", ["GEN"], "kitabın"),
    ("kitap", ["POSS1SG"], "kitabım"),
    ("kitap", ["LOC"], "kitapta"),      # consonant-initial suffix, no voicing
    ("kitap", ["ABL"], "kitaptan"),
    ("kitap", ["PL"], "kitaplar"),
    ("kitap", ["PL", "ACC"], "kitapları"),  # plural intervenes, still no voicing
    ("ağaç", ["ACC"], "ağacı"),
    ("ağaç", ["LOC"], "ağaçta"),
    ("çocuk", ["ACC"], "çocuğu"),
    ("çocuk", ["DAT"], "çocuğa"),
    ("çocuk", ["POSS1SG"], "çocuğum"),
    ("çocuk", ["LOC"], "çocukta"),
    ("kanat", ["ACC"], "kanadı"),
    ("renk", ["ACC"], "rengi"),         # nk gives ng
    ("renk", ["LOC"], "renkte"),
]

# ── Vowel deletion (syncope) ─────────────────────────────────────────────────
# The deleted vowel is the one harmony would otherwise look at, so these also
# test that harmony runs on the post-deletion stem.
SYNCOPE = [
    ("burun", ["ACC"], "burnu"),
    ("burun", ["POSS1SG"], "burnum"),
    ("burun", ["LOC"], "burunda"),      # consonant-initial, no deletion
    ("burun", ["PL"], "burunlar"),
    ("ağız", ["ACC"], "ağzı"),
    ("ağız", ["LOC"], "ağızda"),
    ("şehir", ["ACC"], "şehri"),
    ("şehir", ["LOC"], "şehirde"),
    ("oğul", ["ACC"], "oğlu"),
    ("karın", ["ACC"], "karnı"),
    ("göğüs", ["ACC"], "göğsü"),
    ("kayıp", ["ACC"], "kaybı"),        # deletion and voicing in one derivation
]

# ── Disharmonic loans: harmony class overridden on the lexeme ────────────────
DISHARMONIC = [
    ("saat", ["ACC"], "saati"),
    ("saat", ["PL"], "saatler"),
    ("saat", ["LOC"], "saatte"),
    ("kalp", ["ACC"], "kalbi"),
    ("kalp", ["LOC"], "kalpte"),
    ("rol", ["ACC"], "rolü"),
    ("rol", ["DAT"], "role"),
]

# ── Pronominal n: a case suffix after 3rd person possessive ──────────────────
PRONOMINAL_N = [
    ("ev", ["POSS3SG"], "evi"),
    ("ev", ["POSS3SG", "LOC"], "evinde"),
    ("ev", ["POSS3SG", "ACC"], "evini"),
    ("ev", ["POSS3SG", "DAT"], "evine"),
    ("ev", ["POSS3SG", "ABL"], "evinden"),
    ("ev", ["POSS3SG", "GEN"], "evinin"),
    ("araba", ["POSS3SG", "LOC"], "arabasında"),
    ("araba", ["POSS3SG", "ACC"], "arabasını"),
    ("kitap", ["POSS3SG", "LOC"], "kitabında"),
]

# ── Suffix stacking, in slot order ───────────────────────────────────────────
STACKED = [
    ("ev", ["PL", "POSS1SG"], "evlerim"),
    ("ev", ["PL", "POSS1SG", "LOC"], "evlerimde"),
    ("ev", ["POSS3PL"], "evleri"),
    ("ev", ["POSS3PL", "LOC"], "evlerinde"),
    ("kitap", ["PL", "POSS1SG"], "kitaplarım"),
    ("araba", ["PL", "POSS2SG", "ABL"], "arabalarından"),
    ("çocuk", ["PL", "POSS1PL", "DAT"], "çocuklarımıza"),
]

# ── Predicative suffixes ─────────────────────────────────────────────────────
PREDICATIVE = [
    ("öğrenci", ["PRED1SG"], "öğrenciyim"),
    ("öğrenci", ["PRED2SG"], "öğrencisin"),
    ("öğrenci", ["PRED2PL"], "öğrencisiniz"),
    ("doktor", ["PRED1SG"], "doktorum"),
    ("doktor", ["PRED1PL"], "doktoruz"),
    ("ev", ["LOC", "PRED1SG"], "evdeyim"),
    ("ev", ["PRED3SG"], "evdir"),
    ("kitap", ["PRED3SG"], "kitaptır"),
    ("güzel", ["PRED2SG"], "güzelsin"),
]

ALL = (
    [("plain", *r) for r in PLAIN]
    + [("buffer", *r) for r in BUFFERED]
    + [("voicing", *r) for r in VOICING]
    + [("syncope", *r) for r in SYNCOPE]
    + [("disharmonic", *r) for r in DISHARMONIC]
    + [("pronominal-n", *r) for r in PRONOMINAL_N]
    + [("stacking", *r) for r in STACKED]
    + [("predicative", *r) for r in PREDICATIVE]
)


@pytest.mark.parametrize(
    "phenomenon,lemma,suffixes,expected",
    ALL,
    ids=[f"{p}:{lemma}+{'+'.join(s)}" for p, lemma, s, _ in ALL],
)
def test_known_surface_form(phenomenon, lemma, suffixes, expected):
    assert surface(lemma, *suffixes) == expected


def test_nominative_is_the_bare_stem():
    assert surface("ev", "NOM") == "ev"
    assert surface("kitap", "NOM") == "kitap"


def test_no_suffixes_returns_the_lemma():
    assert surface("kitap") == "kitap"


class TestDerivationTrace:
    """The trace is shown to learners, so its content is part of the contract."""

    def test_records_every_rule_that_fired(self):
        result = TR.inflect("kitap", ["ACC"])
        rules = [step.rule for step in result.steps]
        assert "final_voicing" in rules
        assert "harmony" in rules

    def test_trace_ends_on_the_surface_form(self):
        result = TR.inflect("kitap", ["ACC"])
        assert result.steps[-1].form == result.surface == "kitabı"

    def test_trace_renders_for_a_human(self):
        text = TR.inflect("kitap", ["ACC"]).render_trace()
        assert "kitap" in text and "kitabı" in text
        assert "harmony" in text.lower()

    def test_plain_stem_records_no_voicing(self):
        rules = [s.rule for s in TR.inflect("ev", ["ACC"]).steps]
        assert "final_voicing" not in rules


class TestKnownGaps:
    """Documented limitations. These fail loudly the day someone fixes them."""

    @pytest.mark.xfail(reason="su has an irregular genitive (suyun); not modelled in Phase 1", strict=True)
    def test_su_genitive(self):
        assert surface("su", "GEN") == "suyun"
