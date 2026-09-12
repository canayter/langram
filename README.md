# Langram

*[Türkçe](README.tr.md)*

A research-grounded Turkish course for English speakers. Two things make it
different from a flashcard app: it teaches morphophonology by rule rather than by
paradigm table, and it trains pronunciation against real formant measurements.

**Current status.** The morphology engine, the content pipeline, a FastAPI
backend and a React frontend are built and working end to end: a learner signs
in as a guest, is shown explicit information about a grammatical concept once
before its first exercise, answers items generated live from the grammar
rather than drawn from a fixed list, gets feedback that escalates from a
clarification prompt to the full derivation, and sees a diagnostic report
broken down by which specific rule they are missing. 459 tests. What is left
from the project brief: perception training and production feedback are
deferred until native-speaker recording sessions are possible (see
`docs/deferred-audio.md`), and the register and vernacular track (Phase 8) is
mostly native-speaker judgement calls rather than engineering.

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

**The engine and its tests:**

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"     # Windows
.venv/Scripts/python.exe -m pytest
```

A known-forms oracle of real Turkish surface forms, property-based tests
asserting no generated form can violate harmony over the whole lexicon and
every legal suffix chain, unit tests for the phonological primitives, and
integration tests for the API and the tutor's scheduling logic.

**The full app**, backend and frontend, against a local SQLite database:

```
python -m langram.validate                                   # content is checked in CI too
alembic upgrade head                                          # LANGRAM_DATABASE_URL sets the target
python -m langram.db.seed --database-url sqlite:///langram.db --create-tables

uvicorn langram.api.main:app --reload                          # API on :8000
cd web && npm install && npm run dev                            # UI on :5173, proxies /api
```

`LANGRAM_SECRET_KEY` should be set in any real deployment; without it a new
signing key is generated per process, which logs every learner out on restart.

## Linguistic honesty

Anything a native speaker should confirm is flagged in the content files rather
than guessed, and `inflect --review` lists it. `docs/provenance.md` records where
every claim came from and what is deliberately missing. Corpus frequency bands
are absent rather than invented; they arrive with a real corpus list, not
before.

## What comes next

The register and vernacular track (Phase 8): discourse particles, register
pairs, spoken reductions, address terms, formulaic expressions with no English
equivalent. Almost every claim in it needs a native speaker to confirm before
it can ship, which is what makes it the slow phase rather than the hard one.

Perception training and production feedback (Phases 5 and 6 of the brief) are
deferred, not abandoned. They cannot start without recording sessions with
several native speakers. `docs/deferred-audio.md` has what is already in place
and what restarting needs.
