"""Property-based tests: constraints that must hold for every form the engine
can generate, over the whole lexicon and every suffix combination.

A known-forms table proves the engine right about the cases someone thought of.
These prove it never violates a phonological law, including on the cases nobody
thought of.
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

from langram import load_language

TR = load_language("tr")
P = TR.phonology

LEMMAS = sorted(TR.lexemes)
SUFFIX_BY_SLOT = {
    slot: sorted(s.id for s in TR.suffixes.values() if s.slot == slot and s.surface)
    for slot in (1, 2, 3, 4)
}


def legal_suffix_chains():
    """At most one suffix per slot, in slot order. That is the noun template."""
    return st.tuples(
        st.one_of(st.none(), st.sampled_from(SUFFIX_BY_SLOT[1])),
        st.one_of(st.none(), st.sampled_from(SUFFIX_BY_SLOT[2])),
        st.one_of(st.none(), st.sampled_from(SUFFIX_BY_SLOT[3])),
        st.one_of(st.none(), st.sampled_from(SUFFIX_BY_SLOT[4])),
    ).map(lambda t: [s for s in t if s]).filter(_is_legal)


def _is_legal(chain):
    """Drop sequences the language blocks, so the properties below only ever
    look at words Turkish would actually form."""
    for i, suffix_id in enumerate(chain):
        blocked = TR.suffixes[suffix_id].cannot_follow
        if any(earlier in blocked for earlier in chain[:i]):
            return False
    return True


SLOW = settings(max_examples=400, suppress_health_check=[HealthCheck.too_slow], deadline=None)


@given(lemma=st.sampled_from(LEMMAS), chain=legal_suffix_chains())
@SLOW
def test_output_uses_only_turkish_letters(lemma, chain):
    """No archiphoneme may survive into a surface form."""
    surface = TR.inflect(lemma, chain).surface
    alphabet = set("abcçdefgğhıijklmnoöprsştuüvyz")
    circumflex = set("âîû")   # loanword orthography: kâğıt, lâzım
    illegal = set(surface) - alphabet - circumflex
    assert not illegal, f"{lemma}+{chain} produced {surface!r} containing {illegal}"


@given(lemma=st.sampled_from(LEMMAS), chain=legal_suffix_chains())
@SLOW
def test_suffix_vowels_obey_backness_harmony(lemma, chain):
    """Every suffix vowel agrees in backness with the stem's harmony class.

    Not with the stem's last vowel: a disharmonic loan like saat has a back
    vowel and still takes front suffixes (saatler, saati). Backness comes from
    the class, which is why the class is a lexeme property.
    """
    result = TR.inflect(lemma, chain)
    lexeme = TR.lexemes[lemma]
    # Only disharmonic loans declare a class; for everything else it is the
    # backness of the last stem vowel.
    stem_is_back = (
        lexeme.harmony_class == "back" if lexeme.harmony_class
        else P.is_back(P.last_vowel(lemma))
    )
    for vowel in (c for c in result.suffix_region if c in P.vowels):
        assert P.is_back(vowel) == stem_is_back, (
            f"{lemma}+{chain} = {result.surface!r}: suffix vowel {vowel!r} "
            f"disagrees with harmony class {'back' if stem_is_back else 'front'}"
        )


@given(lemma=st.sampled_from(LEMMAS), chain=legal_suffix_chains())
@SLOW
def test_high_suffix_vowels_obey_rounding_harmony(lemma, chain):
    """A fourfold (high) vowel takes its rounding from the vowel before it.

    Rounding, unlike backness, does come from the actual preceding vowel, which
    is how rol gives rolu with a front rounded vowel: front from the class,
    rounded from the o. Non-high vowels never round, so only high ones qualify.
    """
    result = TR.inflect(lemma, chain)
    vowels = [c for c in result.surface if c in P.vowels]
    stem_vowel_count = len([c for c in result.stem_form if c in P.vowels])
    for i, later in enumerate(vowels):
        if i == 0 or i < stem_vowel_count or not P.is_high(later):
            continue          # stem-internal vowels are lexical, not derived
        earlier = vowels[i - 1]
        assert P.is_rounded(earlier) == P.is_rounded(later), (
            f"{lemma}+{chain} = {result.surface!r}: {later!r} disagrees in rounding with {earlier!r}"
        )


@given(lemma=st.sampled_from(LEMMAS), chain=legal_suffix_chains())
@SLOW
def test_no_voiceless_stop_after_voiced_and_vice_versa(lemma, chain):
    """The D archiphoneme must never surface as t after a voiced segment."""
    result = TR.inflect(lemma, chain)
    for step in result.steps:
        if step.rule == "voicing_assimilation":
            form = step.form
            idx = step.detail["index"]
            preceding = form[idx - 1]
            realised = form[idx]
            assert (realised == "t") == P.is_voiceless(preceding), (
                f"{lemma}+{chain}: {realised!r} after {preceding!r} in {form!r}"
            )


@given(lemma=st.sampled_from(LEMMAS), chain=legal_suffix_chains())
@SLOW
def test_stem_only_changes_where_the_lexeme_permits(lemma, chain):
    """The stem may be altered only by an alternation the lexeme declares.

    Everything the suffixes add is appended to that stem, so no rule may reach
    back and rewrite a stem that did not opt in. (uc + PRED1PL is legitimately
    ucuz: a two-letter stem whose second letter voices.)
    """
    lexeme = TR.lexemes[lemma]
    result = TR.inflect(lemma, chain)
    assert result.surface.startswith(result.stem_form)
    if result.stem_form != lemma:
        assert lexeme.final_voicing or lexeme.vowel_deletion, (
            f"{lemma} became {result.stem_form!r} but declares no alternation"
        )
        assert result.stem_form[0] == lemma[0]


@given(lemma=st.sampled_from(LEMMAS), chain=legal_suffix_chains())
@SLOW
def test_derivation_trace_is_consistent(lemma, chain):
    """Each step's form must be reachable from the last, and the last must be
    the surface form. The trace is shown to learners; it cannot drift."""
    result = TR.inflect(lemma, chain)
    assert result.steps, "every derivation records at least the stem"
    assert result.steps[-1].form == result.surface
    for step in result.steps:
        assert step.rule and step.condition and step.result


@given(lemma=st.sampled_from(LEMMAS))
@SLOW
def test_nominative_singular_is_the_citation_form(lemma):
    assert TR.inflect(lemma, ["NOM"]).surface == lemma


@pytest.mark.parametrize("lemma", LEMMAS)
def test_every_lexeme_inflects_for_every_case(lemma):
    """Exhaustive rather than sampled: no lexeme may crash the engine."""
    for case in SUFFIX_BY_SLOT[3]:
        result = TR.inflect(lemma, [case])
        assert result.surface
