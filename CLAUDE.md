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
- Prefer vocabulary with genuine Turkish origin (native, or old and fully
  nativised Persian/Arabic loans like kitap, hesap, kalem) over recent
  European loanwords (avukat, sofor, patron, polis). The point is immersion
  in Turkish's own morphosyntax and phonotactics, not just correct
  translation. Centuries-old nativised loans are fine and normal; a French
  or English loan is not what this app should teach when a native word
  exists (sofor -> surucu, both meaning driver).

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

## Deployment (live: API on Fly.io, frontend on ayter.com/langram)

    fly deploy --app langram-api               # backend: migrate + reseed + release
    cd web && MSYS_NO_PATHCONV=1 VITE_BASE=/langram/ VITE_API_BASE=https://langram-api.fly.dev npm run build
                                                # frontend: FTP web/dist/* to ayter_com/langram/ after

`MSYS_NO_PATHCONV=1` is not optional in Git Bash on Windows: without it, the
leading slash in `/langram/` is silently rewritten into a Windows path, the
build succeeds, and every asset 404s on the deployed site with no warning
either way. PowerShell does not have this problem.

Postgres scales to zero after an hour idle; the first `fly deploy` or request
after that can fail once with a connection error while it wakes up. Retrying
once is the fix, not a code change.

Full steps, including the CSP `.htaccess` override every ayter.com
subdirectory needs for its own API origin, are in `docs/deploy.md`.

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
    src/langram/gamification.py
                       XP ("marks") and day streaks ("chain"). Deliberately
                       reads nothing pedagogical and is read by nothing
                       pedagogical, so a bug here cannot corrupt mastery or
                       scheduling.
    src/langram/generators/vocab_recognition.py
                       the one exercise type that is not suffix-shaped: a
                       bare word, pick its meaning. See
                       pedagogy-rationale.md for why this is a narrow,
                       deliberate exception and not a reversal of "generated,
                       not memorised."
    web/               React and Vite. VITE_BASE sets the deployment subpath.
    web/public/favicon.svg, web/src/components/Logo.tsx
                       the dotless-i mark, same SVG both places.
    tests/             known-forms oracle, property tests, unit tests.
    docs/provenance.md where every linguistic claim in content/ came from.
    docs/pedagogy-rationale.md
                       every pedagogical choice's justification, required
                       reading before adding a new one (see the working
                       agreement above).
    docs/deploy.md     exact Fly.io + ayter.com deployment steps.

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

## What Langram is

A Turkish-for-English-speakers app whose whole claim is that it teaches by
generating from a real grammar, not by drilling a fixed content list. The
morphology engine (`src/langram/engine.py`) resolves suffixes stored in
archiphoneme notation against a stem at runtime; nothing in `content/` is
ever an inflected surface form. Every exercise, every distractor, and every
"why was this wrong" explanation is a live consequence of that engine, not
hand-authored. That is the one thing to protect above all else in this repo.

## What it has, as of 2026-09-05

**Live and deployed**: API on Fly.io (`langram-api`, Postgres attached,
scales to zero when idle), frontend built and FTP'd to `ayter.com/langram`.
See the Deployment section above for the exact commands and the two gotchas
(`MSYS_NO_PATHCONV`, Postgres cold start) that have each broken a deploy
before.

**Curriculum, five units**:
1. Vowel harmony (twofold and fourfold), the plural
2. Predication without a verb (Turkish has no "to be" in the present),
   possessive-style person endings, third person unmarked
3. Possession, buffer consonants, stem alternation (syncope, devoicing)
4. Everyday vocabulary: a lexical_set concept with no prerequisites, open
   from the start rather than gated in sequence, because vocabulary is meant
   to recur alongside every other unit rather than being finished once. Not
   fully realised yet: see "Not built yet" below.
5. The first verbal unit: present tense (-(y)Iyor) and negation (-mA),
   third person only. Deliberately narrow: both are uncontested facts about
   Turkish needing no native-speaker judgement call, unlike most of what a
   fuller verb system would need (see "Not built yet").

Three exercises are deliberately not served, and say so when asked to build:
two person contrasts that need audio (readable on paper, but the whole point
is two forms differing only in who is being talked about), and one register
comparison resting on a claim still awaiting native-speaker confirmation.

**Mastery and scheduling**: Bayesian Knowledge Tracing per concept
(`src/langram/bkt.py`), guess rate taken from the item rather than fixed.
`GET /api/progress` reports per rule and per concept in sentences, not
scores. Every concept has an `intro` (VanPatten's explicit-information
stage), gated so a learner never meets two intros in a row without practice
between them.

**Gamification**: a day-streak ("chain", not "streak") and points ("marks",
not "XP") for correct answers, deliberately renamed off the Duolingo
template so it reads as this app's own. Backend in
`src/langram/gamification.py`, reads and is read by nothing pedagogical.

**A vowel chart**: front/back x rounded/unrounded, generated from
`phonology.yaml` via `GET /api/language/vowels` rather than hand-drawn, shown
on Unit 1's intro and reachable anytime from a Reference panel.

**A logo and favicon**: the dotless i, chosen because it is the single
letter that announces "this is Turkish" fastest and is literally what Unit 1
teaches.

**A vocabulary-recognition exercise** (`vocab_recognition.py`): a bare word,
pick its meaning from four options, drawn from the same reviewed lexicon
every other exercise trusts. A deliberate, narrow, cited exception to
"generated, not memorised" (see pedagogy-rationale.md); not the standalone
vocabulary track the roadmap describes, which is a much bigger feature.

**recurs_in**: a data field on `Concept` naming which later concepts
genuinely re-test an earlier one (fourfold-harmony recurs in every later
concept whose suffixes are also I-type). This is architecture, not a
linguistic claim, adopted from external material without adopting any of
that material's actual content. Not scheduler-active: `tutor.next_item`
does not yet read it to bias which item comes next. That is the real
"weak concepts resurface elsewhere" feature the roadmap wants, and it is
still unbuilt.

**The audio work is deferred.** Perception training and formant feedback are
on hold because they cannot start without recording sessions with several
native speakers. Nothing else waits on them. What is already in place and
what restarting needs is in `docs/deferred-audio.md`. Do not add an audio
feature without reading it: the hooks exist and are easy to duplicate by
accident.

## A recurring bug shape worth knowing before touching the engine again

Every one of these was caught by actually generating exercises or actually
using the app, never by reasoning about the change in the abstract, and
every one has the same shape: a rule that is correct for the common case
silently does the wrong thing for a case nobody tried yet.

- `fikir` + a nominal suffix undergoes vowel-drop syncope (fikrimiz), but the
  same stem before a predicative suffix does not (fikiriz, not fikriz) --
  confirmed with a native speaker, fixed in `engine.py` keyed off suffix
  category.
- Predicative exercises drew from the entire noun lexicon with nothing
  screening whether predicating that noun onto a person makes sense
  ("tabaksin", you are a plate). Fixed with a `predicate_natural` flag and a
  `predicative_only` lexeme filter; the resulting pool was then too small
  and visibly repeated in a short session, so it was widened, and widening
  it introduced recent European loanwords, which got swapped for native or
  old-nativised alternatives per the working agreement above. Three
  separate bugs from one root cause, each only visible after the previous
  fix shipped.
- Adding the first verbal suffix (`-(y)Iyor`) surfaced two more of the same
  shape: `candidate_lexemes()` had no `pos` filter, so a verbal suffix could
  attach to a noun ("kucuguyor"); and `_stem_after()` didn't recognise the
  new stem-vowel-deletion step, so an internal value silently pointed at the
  wrong (if coincidentally same-length) string.

Worth actually generating a batch of items after any change to a suffix,
the lexicon's `pos`/flag fields, or `candidate_lexemes()`, not just running
the type checker and the existing test suite.

## Not built yet, roughly in the order it would make sense to tackle

- **Verb person marking** (öğreniyorum, gidiyorsun). Without it, unit 5's
  verbs can only ever speak in the third person.
- **The three-axis tagging / weak-concept resurfacing scheduler.** The
  architectural idea: every exercise item is really tagged along three
  independent axes (lexeme, morphology/suffix, concept/rule), not filed
  under one lesson. Once tagged that way, "resurface this learner's weakest
  concept using vocabulary they already know" is a query the scheduler can
  run, not a curriculum-authoring problem, and it is what makes interleaving
  legible rather than confusing: the novelty in an item should be the
  grammar, not the words. `recurs_in` is a first, partial piece of this
  (which concepts re-test which); `tutor.next_item` does not yet read it,
  and per-lexeme/per-skill tagging beyond that does not exist yet either.
- **The aorist, evidential, passive, causative, reflexive/reciprocal,
  imperative/optative, question particle, word order/focus, postpositions,
  common derivational suffixes** -- all real, all still entirely absent.
  The aorist specifically needs a trustworthy per-verb high/low-vowel
  wordlist before it can be built at all; every source available described
  it as lexically listed, not a rule.
- **A standalone vocabulary track** (flashcards, content packs organised by
  a learner's actual purpose -- tourism, daily life, a relationship, cooking
  as a task-based frame). Explicitly deprioritised below everything else on
  this list, but noted so it is not forgotten: needs-analysis onboarding
  ("why are you learning?") belongs before it, since that
  changes which vocabulary a learner meets, not just the theme.
- **Phase 8 from the original brief**, register and vernacular. Almost
  every claim in it is a native-speaker judgement, so it will be slow
  regardless of effort.
- Eventually, multi-language support (English speakers learning something
  other than Turkish). Keep the item schema language-agnostic when this is
  touched, even though the concept taxonomy itself should stay
  Turkish-specific; retrofitting a language-agnostic schema after content
  assumes Turkish-specific concept names would be expensive.

Secrets: set LANGRAM_SECRET_KEY in any deployment. Without it a new signing key
is generated per process, which logs every learner out on restart.
