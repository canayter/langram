# Provenance of the linguistic content

Where every claim in `content/` came from, and what still needs a native
speaker's eye. The working agreement forbids inventing linguistic facts, so
anything uncertain is flagged rather than guessed.

Run `inflect --review` for the current list.

## Phonology

`content/l2/tr/morphology/phonology.yaml` encodes the standard description of
Turkish vowel harmony and voicing assimilation: eight vowels crossed by backness,
rounding and height; twofold harmony on the A archiphoneme and fourfold on I; the
eight voiceless consonants conventionally remembered as "fistikci sahap"; and
stem-final p, c, t, k voicing to b, c, d, g before a vowel.

These are uncontroversial and appear in every reference grammar. Full citations
belong in `docs/bibliography.md`, which is `CITATION NEEDED` until the reference
grammars are to hand.

The one non-obvious rule encoded here is that stem-final k after n surfaces as g
rather than the soft g: renk gives rengi, not "renği".

## Suffixes

`content/l2/tr/morphology/suffixes.yaml` covers the Phase 1 scope named in the
brief: number, possessive, case and predicative. Every suffix is written once in
archiphoneme notation; no surface allomorph appears anywhere in the project.

Slot order on the noun is number, then possessive, then case, then predicative.

Known gaps:

- Stress is not modelled at all. Turkish stress is predominantly word-final, with
  exceptional classes (place names, the negative, the pre-stressing clitics).
  INS `-(y)lA` is flagged because it is pre-stressing and the engine is silent
  about that.
- The C archiphoneme is implemented but unused, since the suffixes that carry it
  are derivational and arrive later.

## Lexicon

`content/l2/tr/lexicon/lexemes.yaml` holds roughly 165 stems chosen to exercise
every alternation the engine implements, plus enough ordinary vocabulary to be
useful for early units.

### What is asserted, and how confident it is

**final_voicing** is required on every stem ending in p, c, t or k. The loader
refuses to load a lexicon where one is missing, because a silent default would
put a wrong form in front of a learner. Most values here are textbook pairs
(kitap/kitabi, agac/agaci, sepet/sepeti, cocuk/cocugu). Where a stem is
genuinely lexically split and memory is not enough, it carries a `review` flag.

Polysyllabic stems in -k almost always alternate; monosyllabic ones are split
(ok gives oku, but gok gives gogu). Every monosyllable in the file is flagged.

**vowel_deletion** is a closed class and is listed explicitly rather than
derived. The entries here are the standard syncope stems (burun, agiz, karin,
alin, boyun, gogus, ogul, sehir, fikir, isim, resim, akil, vakit, kayip).

Note that `koyun` is deliberately absent. It is two words: "sheep", which does
not syncopate, and "bosom", which does. Adding it needs a decision about how the
lexicon represents homographs, which Phase 1 does not have.

**harmony_class** appears only on disharmonic loans, where suffix backness does
not follow the last stem vowel: saat takes front suffixes (saatler, saati)
despite its back vowels. Every one of these is flagged, because the class of
disharmonic loans is exactly where a non-native intuition is least reliable.

**frequency_band is absent.** The brief calls for corpus frequency bands from the
Turkish National Corpus or TS Corpus. Those numbers do not exist in this repo
yet, and writing plausible-looking bands would be inventing data that later
drives the scheduler. Bands arrive in Phase 2 with the real list.

## Morphotactics

Only one constraint is declared so far: POSS3PL cannot follow PL. The plural is
already inside `-lArI`, so there is no *kitaplarlari, and "kitaplari" is
genuinely ambiguous between "his books" and "their books". The engine raises
MorphotacticError rather than generating a form no speaker would produce.

**Confirm this.** It is a structural claim, not a lexical one, and it is the
kind of thing that is easy to be confidently wrong about. Other possessives
stack on the plural normally (kitaplarim, kitaplariniz).

This was found by inflecting forms that were not in the test table. Before the
constraint existed the engine produced "kitaplarlarindan" without complaint,
which is a reminder that a green suite proves only what it asked.

## Known modelling gaps

- `su` has an irregular genitive (suyun, not the regular form the engine
  produces). There is a strict xfail test for it in
  `tests/test_known_forms.py::TestKnownGaps`, so it fails loudly the day someone
  implements irregular stems.
- Homographs are not representable. See `koyun` above.
- Compound nouns and the compound possessive are out of scope.
