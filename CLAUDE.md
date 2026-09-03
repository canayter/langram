# Working agreement

Copied from the project brief, section 8. This file persists across sessions and
takes precedence over habit.

- The morphology engine is the foundation. Never hardcode an inflected surface
  form anywhere outside the lexicon. If you find yourself typing `kitabı` in a
  content file or a component, stop; it should be generated.
- Content lives in version-controlled files, learner state lives in the
  database. Never blur that line.
- Write tests for the engine before writing the engine. Property-based tests for
  phonological constraints, unit tests for known alternating stems.
- Every pedagogical choice in the UI must be traceable to
  `docs/pedagogy-rationale.md`. If you add a feature with no rationale, write the
  rationale or do not add it.
- Do not invent linguistic facts. If you are unsure whether a stem alternates,
  whether a suffix is pre-stressing, or what a particle means pragmatically, flag
  it as `NEEDS_REVIEW` in the content file rather than guessing. The project
  owner is a native Turkish speaker and a linguist; guessing wastes both of your
  time.
- Do not invent citations. If a claim needs a source and you do not have one,
  mark it `CITATION NEEDED`.
- Prefer boring, well-tested libraries. This project's novelty is in the
  linguistics and the pedagogy, not in the infrastructure.
- Keep the audio analysis module behind a clean interface. It has the heaviest
  dependencies and the highest chance of needing to move.
- No em dashes in any user-facing copy or documentation.

## How this repo runs

    .venv/Scripts/python.exe -m pytest        # Windows
    .venv/bin/python -m pytest                # elsewhere

    inflect kitap ACC                         # derivation for one form
    inflect cocuk --paradigm                  # full nominal paradigm
    inflect --review                          # everything awaiting a native speaker

    python -m langram.validate                # schemas plus the semantic rules
    python -m langram.validate --write-bibliography
    alembic upgrade head                      # LANGRAM_DATABASE_URL sets the target
    python -m langram.db.seed --database-url sqlite:///langram.db --create-tables

    uvicorn langram.api.main:app --reload      # API on :8000
    cd web && npm run dev                      # UI on :5173, proxies /api

Dependencies live in a project venv, not in the system or conda environment.

## Where things are

    content/l2/tr/     Turkish content. Nothing English-specific belongs here.
    content/l1/en/     English-side content, once there is any.
    content/bibliography.yaml
                       every source the curriculum may cite. A unit that cites
                       anything else fails validation.
    schemas/           JSON Schema for every content file.
    src/langram/       the engine. Knows no Turkish facts of its own; it reads
                       them from content/.
    src/langram/db/    SQLAlchemy models and the seeder. Content tables are a
                       projection of content/; learner state is not.
    alembic/           migrations. Postgres is the target, SQLite is a local
                       convenience.
    src/langram/api/   FastAPI. HTTP only; the teaching logic is outside it.
    src/langram/tutor.py
                       what to serve next: due reviews first, then the earliest
                       unfinished concept, interleaved.
    src/langram/diagnosis.py
                       why an answer was wrong, and what to say about it.
    web/               React and Vite. VITE_BASE sets the deployment subpath.
    tests/             known-forms oracle, property tests, unit tests.
    docs/provenance.md where every linguistic claim in content/ came from.

## Rules the tooling enforces for you

These are in the working agreement above and are also checked, so breaking them
fails CI rather than reaching a learner.

- A suffix may not contain a literal vowel. Use an archiphoneme, or set
  `has_fixed_vowel` if the suffix genuinely does not harmonize.
- A stem ending in p, c, t or k must declare `final_voicing`. It cannot be
  predicted from the spelling.
- A unit may only cite keys that exist in `content/bibliography.yaml`.
- A concept may not ask for production without a structured input stage first.
- No em dashes in learner-facing copy.

## Phase status

Phases 1 to 4 are complete: the morphology engine, the content pipeline, the
core web app, and all seven exercise generators.

Input before output is now real rather than only enforced in the validator. The
tutor orders by unit and then by stage, and the structured input generators
exist, so a learner meets a concept by noticing it before being asked to build
anything.

Three exercises in the curriculum are deliberately not served, and say so when
asked to build:

- two person contrasts, which are two well formed words differing only in who
  is being talked about. Readable on paper, so they need audio.
- one register comparison of bare predication against -DIr, which rests on a
  claim flagged for native speaker review.

**The audio work is deferred.** Phases 5 and 6 of the brief, perception training
and formant feedback, are on hold because they cannot start without recording
sessions with several native speakers. Nothing else waits on them. What is
already in place and what restarting needs is in `docs/deferred-audio.md`. Do
not add an audio feature without reading it: the hooks exist and are easy to
duplicate by accident.

Phase 7 is done. Mastery is Bayesian Knowledge Tracing per concept in
`src/langram/bkt.py`, with the guess rate taken from the item rather than fixed,
because a two option judgement is guessable and a typed answer is not. A concept
counts as known only with both a high probability and at least
`tutor.MIN_OPPORTUNITIES` attempts behind it.

The four BKT parameters are defaults, not fitted values. Fitting them per
concept needs learner data that does not exist yet, and everything required to
do it is logged.

`GET /api/progress` is the diagnostic report: per rule, per concept, and in
sentences rather than scores. Rates are errors over opportunities, where an
opportunity is a rule the target form actually exercised, read off the
derivation. A wrong answer whose cause cannot be pinned on a rule, such as
rejecting a well formed word, is left out of the rates rather than quietly
distorting them.

Every concept now carries `intro`, required by the curriculum schema: explicit
information about the pattern, shown once before the learner meets any exercise
for it. This is not new pedagogy; VanPatten's Processing Instruction model
(already cited for input-before-output) has explicit information as its first
stage, and the app was only implementing the third. `tutor.py` gates the very
first exercise of each concept behind its intro, and additionally forces one
real exercise of a just-introduced concept before interleaving is allowed to
introduce a different one, so a learner never meets two intros in a row with no
practice between them. `intro_seen_at` lives on `user_concept_mastery` as its
own column rather than inside the BKT `state` blob, because `bkt.update()`
replaces `state` wholesale on every real answer and would otherwise erase it
silently. On the frontend, `SessionScreen`'s mount effect needed a synchronous
re-entry guard: `/api/session/next` is not idempotent (it can mark an intro
seen), and React 18 StrictMode's deliberate double-invoke of effects in
development was firing it twice, so the intro was being fetched correctly and
then consumed by the second call before it ever rendered.

Remaining from the brief: Phase 8, the register and vernacular track. Almost
every claim in it is a native speaker judgement.

Secrets: set LANGRAM_SECRET_KEY in any deployment. Without it a new signing key
is generated per process, which logs every learner out on restart.
