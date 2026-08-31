# Langram

A research-grounded Turkish course for English speakers. Two things make it
different from a flashcard app: it teaches morphophonology by rule rather than by
paradigm table, and it trains pronunciation against real formant measurements.

This repository is at **Phase 1**: the morphology engine, standing on its own,
with no web application around it yet.

## What works today

```
$ inflect kitap ACC
kitap + ACC
  1. stem ends in voiceless /p/ and the suffix is vowel-initial
     -> intervocalic voicing gives kitab- [final_voicing]: kitab
  2. stem ends in a consonant
     -> buffer y is not inserted [buffer]: kitab
  3. last vowel /a/ is back, unrounded
     -> fourfold harmony resolves I to ı [harmony]: kitabı
  = kitabı
```

The derivation is the product, not a debug aid. A learner who sees the rule fire
learns the rule; a learner who sees `kitabı` memorises a string.

Harder cases work the same way:

```
$ inflect kayıp ACC          # syncope and voicing in one derivation
$ inflect ev POSS3SG LOC     # evinde, via the pronominal n
$ inflect saat PL            # saatler, a disharmonic loan taking front suffixes
$ inflect çocuk --paradigm   # the full nominal paradigm
$ inflect --review           # every claim awaiting a native speaker
```

## How it is built

Suffixes are written once, in archiphoneme notation, and the engine generates
every allomorph:

```yaml
- id: ACC
  surface: "-(y)I"      # not -i, -ı, -u, -ü
  category: case
```

No inflected surface form appears anywhere in the project outside the engine's
output. That constraint is what lets the app generate unlimited practice items
from a grammar instead of shipping a sentence list.

The engine knows no Turkish of its own. Vowel inventories, harmony tables, the
voiceless set and the alternation maps all live in
`content/l2/tr/morphology/phonology.yaml`. A related language with the same
harmony machinery (Tatar, Azerbaijani) is a new content directory, not a fork.

## Running it

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"     # Windows
.venv/Scripts/python.exe -m pytest
```

355 tests: a known-forms oracle of real Turkish surface forms, property-based
tests asserting no generated form can violate harmony over the whole lexicon and
every legal suffix chain, and unit tests for the phonological primitives.

## Linguistic honesty

Anything a native speaker should confirm is flagged in the content files rather
than guessed, and `inflect --review` lists it. `docs/provenance.md` records where
every claim came from and what is deliberately missing. Corpus frequency bands
are absent rather than invented; they arrive in Phase 2 with a real list.

## What comes next

Phase 2 is a JSON Schema for the content files, a validator in CI, and seeding
into Postgres. The web application starts at Phase 3. See the project brief for
the full sequence.
