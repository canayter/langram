# Deferred: perception training and production feedback

Phases 5 and 6 of the brief are the audio half of the project: High Variability
Phonetic Training, and production feedback from formant measurements. Both are
deferred. Nothing in the codebase is waiting on them to work, and this file is
what is needed to pick them up cold.

They are deferred because they are the only part of the project that cannot
start without recording sessions with several native speakers. Everything else
can be built and shipped meanwhile.

## What is already in place

The hooks exist, so restarting is not a rewrite.

- `recordings` and `perception_trials` tables are in the schema and in the
  migrations. They are empty and unused, deliberately.
- `lexemes.yaml` accepts an `audio` list per lexeme, validated by the schema.
  Nothing populates it yet.
- Exercises carry a `modality` parameter. `text` is the default; `audio` marks
  an item that cannot be served yet.
- `minimal_pair_identification` refuses to build an audio item and says why,
  rather than quietly rendering it as a reading task.
- The exercise stage `perception` is in the curriculum schema and in the tutor's
  ordering, with no generator behind it.

## What deferring actually costs

Less than it looks, for now.

Two exercises are unserved: the person contrasts in units 2 and 3. Both put two
well formed words side by side that differ only in who is being talked about,
which is trivially readable on paper. The same contrast is already covered in
reading by `form_meaning_match`, which asks what a form means and offers the
same set of persons. So no concept currently loses coverage.

What is genuinely lost is the perception training claim itself. Training
perception with many talkers is a distinct intervention, not a harder version of
a reading exercise, and the app should not claim it until it does it.

## What Phase 5 needs before any code

1. **Talkers.** At least six native speakers, balanced for sex, ideally spread
   across regional accents. This is the real blocker.
2. **A wordlist** covering the contrast inventory in section 3.5 of the brief:
   the front rounded vowels, the close back unrounded vowel, clear against dark
   l, the palatalised consonants in loanwords, and soft g. Each target in
   several phonetic environments.
3. **A recording protocol** worth writing down: same prompt order, same
   distance, quiet room, uncompressed at 44.1 kHz. It is the same protocol as a
   phonetics study because it is one.
4. **Consent and licensing** recorded in `data/reference/provenance` before any
   file is committed. Nothing ships whose licence has not been checked.

## Then the code

- A `perception_forced_choice` generator, registered like any other, drawing a
  talker at random and never the same one twice in a row.
- Per contrast d-prime rather than accuracy, so sensitivity is separated from
  response bias, tracked in `perception_trials`.
- A threshold gate: no learner is moved to production of a contrast until their
  perception of it clears it.
- A held out talker for the generalisation test, which is the only measure that
  says whether training transferred.

## Phase 6, after that

Recording through `MediaRecorder`, analysis with Parselmouth behind its own
module boundary and its own dependencies, Lobanov normalisation before any
comparison across speakers, and the vowel space plot in D3.

The one thing to get right on the first day: never compare raw Hz across
speakers. Normalise first. The brief calls this the single most common mistake
in this kind of feature, and it is.
