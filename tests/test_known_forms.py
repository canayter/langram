"""The oracle: known Turkish surface forms the engine must reproduce.

Every row here is a form a native speaker would produce. If the engine and this
table disagree, the engine is wrong until a linguist says otherwise.

Grouped by the phenomenon each row is there to pin down, so a failure names its
own cause.
"""
import pytest

from langram import MorphotacticError, load_language

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
    ("araba", ["INS"], "arabayla"),         # ile, contracted: buffer y, back
    ("kalem", ["INS"], "kalemle"),          # consonant-final: no buffer, front
    ("arkadaş", ["POSS1SG", "INS"], "arkadaşımla"),
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
    # Confirmed with a native speaker: the deletion these stems undergo before
    # an ordinary vowel-initial suffix does not happen before the predicative
    # suffixes. fikiriz "we are an idea" is grammatical but not something
    # anyone would say; fikriz is not a word at all.
    ("fikir", ["POSS1PL"], "fikrimiz"),  # deletes: an ordinary nominal suffix
    ("fikir", ["PRED1PL"], "fikiriz"),   # does not: the predicative suffix
    ("isim", ["POSS1PL"], "ismimiz"),
    ("isim", ["PRED1PL"], "isimiz"),
    ("resim", ["POSS1PL"], "resmimiz"),
    ("resim", ["PRED1PL"], "resimiz"),
]

# ── Disharmonic loans: harmony class overridden on the lexeme ────────────────
DISHARMONIC = [
    ("saat", ["ACC"], "saati"),
    ("saat", ["PL"], "saatler"),
    ("saat", ["LOC"], "saatte"),
    # A chain, not just one suffix: PL's own front vowel has to take over
    # harmony for LOC once it attaches, rather than saat's declared front
    # override reaching past PL to govern LOC too (engine.py's harmony_back).
    ("saat", ["PL", "LOC"], "saatlerde"),
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

# ── Verbal: negation and the present progressive ─────────────────────────────
# -(Ø)Iyor deletes the stem's own final vowel and replaces it with the
# harmonised I, rather than inserting a buffer (see engine.py's
# stem_vowel_deletion step). Consonant-final stems have nothing to delete, so
# the ordinary vowel-initial-suffix path handles final_voicing exactly as it
# would for any other suffix (git -> gid- before -Iyor same as before -(y)I).
VERBAL = [
    ("gel", ["PROG"], "geliyor"),          # consonant-final, no alternation
    ("git", ["PROG"], "gidiyor"),          # consonant-final, final_voicing
    ("yap", ["PROG"], "yapıyor"),          # consonant-final, does not voice
    ("oku", ["PROG"], "okuyor"),           # vowel-final, back rounded
    ("bekle", ["PROG"], "bekliyor"),       # vowel-final, front unrounded
    ("iç", ["PROG"], "içiyor"),
    ("çalış", ["PROG"], "çalışıyor"),
    ("otur", ["PROG"], "oturuyor"),
    ("iste", ["PROG"], "istiyor"),
    ("konuş", ["PROG"], "konuşuyor"),
    ("gel", ["NEG"], "gelme"),
    ("yap", ["NEG"], "yapma"),
    ("git", ["NEG"], "gitme"),             # NEG is consonant-initial: no
                                            # final_voicing trigger from it
    ("gel", ["NEG", "PROG"], "gelmiyor"),
    ("git", ["NEG", "PROG"], "gitmiyor"),
    ("yap", ["NEG", "PROG"], "yapmıyor"),
    # The negative progressive's one genuine irregularity: -Iyor's rounding
    # here tracks the verb root, not NEG's own unrounded -mA, so a rounded
    # stem needs okumuyor, not the "regular" okumıyor the ordinary rule
    # (unrounded after a low vowel, as in evler+PRED3SG -> evlerdir) would
    # otherwise predict. gel/git/yap above never exposed this because none
    # of their own stem vowels are rounded.
    ("oku", ["NEG", "PROG"], "okumuyor"),
    ("konuş", ["NEG", "PROG"], "konuşmuyor"),

    # Person marking: the same PRED suffixes already taught for nominal
    # predication, reused on a verb. -(y)Iyor's own invariant back-rounded o
    # governs harmony for whatever follows it, so the person ending's shape
    # no longer varies with the verb's own harmony class the way it does on
    # a noun (see engine.py's harmony_back).
    ("gel", ["PROG", "PRED1SG"], "geliyorum"),
    ("bekle", ["PROG", "PRED1SG"], "bekliyorum"),   # front stem: still -um, not -üm
    ("git", ["PROG", "PRED2SG"], "gidiyorsun"),
    ("oku", ["PROG", "PRED1PL"], "okuyoruz"),
    ("konuş", ["PROG", "PRED2PL"], "konuşuyorsunuz"),
    ("yap", ["PROG", "PL"], "yapıyorlar"),
    ("iste", ["PROG", "PRED3SG"], "istiyordur"),

    # Negation and person together: both fixes composed.
    ("gel", ["NEG", "PROG", "PRED1SG"], "gelmiyorum"),
    ("oku", ["NEG", "PROG", "PRED1PL"], "okumuyoruz"),
    ("konuş", ["NEG", "PROG", "PRED2SG"], "konuşmuyorsun"),
]

# ── Ability: -(y)Abil, split into ABIL + the fixed tense that follows it ─────
# bil (the frozen root of bilmek) never harmonises, and neither does the
# vowel immediately after it: it always resolves to i, reading bil's own
# vowel rather than the original verb's class, so back-vowel verbs
# (yap, oku, çalış...) still end in -ir, never -ar. Confirmed against
# multiple independent descriptions of Turkish before writing these.
ABILITY = [
    ("gel", ["ABIL", "ABILTENSE"], "gelebilir"),         # consonant-final, front
    ("yap", ["ABIL", "ABILTENSE"], "yapabilir"),          # consonant-final, back -- still -ir
    ("git", ["ABIL", "ABILTENSE"], "gidebilir"),          # final_voicing before ABIL's vowel-initial A
    ("oku", ["ABIL", "ABILTENSE"], "okuyabilir"),         # vowel-final: buffer y, still -ir
    ("bekle", ["ABIL", "ABILTENSE"], "bekleyebilir"),
    ("çalış", ["ABIL", "ABILTENSE"], "çalışabilir"),
    ("konuş", ["ABIL", "ABILTENSE"], "konuşabilir"),
    ("gel", ["ABIL", "ABILTENSE", "PRED1SG"], "gelebilirim"),
    ("yap", ["ABIL", "ABILTENSE", "PRED2SG"], "yapabilirsin"),
    ("oku", ["ABIL", "ABILTENSE", "PRED1PL"], "okuyabiliriz"),
    ("konuş", ["ABIL", "ABILTENSE", "PRED2PL"], "konuşabilirsiniz"),
    ("gel", ["ABIL", "ABILTENSE", "PL"], "gelebilirler"),
    ("yap", ["ABIL", "ABILTENSE", "PRED3SG"], "yapabilirdir"),
]

# ── Simple past: -DI, and a third, non-reused person paradigm ───────────────
# No buffer and no vowel-deletion at all, unlike every other tense suffix
# taught so far (compare -(y)Iyor's Ø-deletion and -(y)Abil's buffer y):
# DI attaches directly to a vowel-final stem with nothing inserted. D
# devoices exactly like final_voicing would, but for a different reason --
# the suffix's own consonant reading the stem's voicing, not the stem
# itself alternating -- confirmed by git giving gitti, not gidti (D reads
# git's own final t as voiceless; final_voicing never triggers here at
# all, since that rule only ever fires before a vowel-initial suffix, and D
# is not one). The person endings here (PAST1SG -m, PAST2SG -n, PAST1PL -k,
# PAST2PL -nIz) are their own paradigm, not a reuse of the predicative
# endings (unit 2, reused again in units 5 and 6) or the possessive ones
# (unit 3); -k for "we" in particular matches neither.
PAST_TENSE = [
    ("gel", ["DI"], "geldi"),               # consonant-final, voiced: d
    ("git", ["DI"], "gitti"),               # own final t is voiceless: t, not gidti
    ("yap", ["DI"], "yaptı"),               # voiceless p: t
    ("oku", ["DI"], "okudu"),               # vowel-final: no buffer at all
    ("bekle", ["DI"], "bekledi"),
    ("iç", ["DI"], "içti"),                 # voiceless ç: t
    ("çalış", ["DI"], "çalıştı"),           # voiceless ş: t
    ("otur", ["DI"], "oturdu"),
    ("iste", ["DI"], "istedi"),
    ("konuş", ["DI"], "konuştu"),           # voiceless ş: t
    ("gel", ["DI", "PAST1SG"], "geldim"),
    ("gel", ["DI", "PAST2SG"], "geldin"),
    ("gel", ["DI", "PAST1PL"], "geldik"),   # -k, unlike any other paradigm
    ("gel", ["DI", "PAST2PL"], "geldiniz"),
    ("gel", ["DI", "PL"], "geldiler"),      # 3pl reuses PL directly
    ("yap", ["DI", "PAST1SG"], "yaptım"),
    ("yap", ["DI", "PAST1PL"], "yaptık"),
    ("oku", ["DI", "PAST1SG"], "okudum"),
    ("oku", ["DI", "PAST2PL"], "okudunuz"),
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
    + [("verbal", *r) for r in VERBAL]
    + [("ability", *r) for r in ABILITY]
    + [("past-tense", *r) for r in PAST_TENSE]
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


class TestMorphotactics:
    """Sequences Turkish does not allow are refused, not invented."""

    def test_plural_then_third_person_plural_possessive_is_refused(self):
        # The plural already sits inside -lArI. There is no *kitaplarları;
        # "kitapları" is simply ambiguous between his books and their books.
        with pytest.raises(MorphotacticError, match="POSS3PL cannot follow PL"):
            TR.inflect("kitap", ["PL", "POSS3PL"])

    def test_third_person_plural_possessive_alone_is_fine(self):
        assert surface("kitap", "POSS3PL") == "kitapları"

    def test_other_possessives_stack_on_the_plural(self):
        assert surface("kitap", "PL", "POSS1SG") == "kitaplarım"
        assert surface("kitap", "PL", "POSS2PL") == "kitaplarınız"


class TestKnownGaps:
    """Documented limitations. These fail loudly the day someone fixes them."""

    @pytest.mark.xfail(reason="su has an irregular genitive (suyun); not modelled in Phase 1", strict=True)
    def test_su_genitive(self):
        assert surface("su", "GEN") == "suyun"
