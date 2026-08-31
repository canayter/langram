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

Dependencies live in a project venv, not in the system or conda environment.

## Where things are

    content/l2/tr/     Turkish content. Nothing English-specific belongs here.
    content/l1/en/     English-side content, once there is any.
    src/langram/       the engine. Knows no Turkish facts of its own; it reads
                       them from content/.
    tests/             known-forms oracle, property tests, unit tests.
    docs/provenance.md where every linguistic claim in content/ came from.

## Phase status

Phase 1 (morphology engine) is complete. Do not start Phase 3 work before
Phase 2 (content schema, validator in CI, seeding) exists.
