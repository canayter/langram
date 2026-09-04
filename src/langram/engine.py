"""The morphology engine.

inflect() is a pure function: a lexeme, a list of suffixes and a phonology in,
a surface form and a full derivation out. Nothing here touches the database,
the network or the clock, which is why it can be tested exhaustively.
"""
from __future__ import annotations

import re
from typing import Sequence

from .models import DerivationStep, InflectionResult, Lexeme, Suffix
from .phonology import Phonology

# "-(y)I" -> optional "y", body "I".  "-lAr" -> no optional, body "lAr".
_SURFACE = re.compile(r"^-?(?:\((?P<optional>[^)]+)\))?(?P<body>.*)$")


class MorphotacticError(ValueError):
    """A suffix sequence Turkish does not allow."""


def _parse(suffix: Suffix) -> tuple[str | None, str]:
    m = _SURFACE.match(suffix.surface)
    if not m:                                   # pragma: no cover - guarded by schema
        raise ValueError(f"unparseable suffix surface: {suffix.surface!r}")
    return m.group("optional") or None, m.group("body")


def inflect(
    lexeme: Lexeme,
    suffixes: Sequence[Suffix],
    phonology: Phonology,
) -> InflectionResult:
    """Apply suffixes to a stem, resolving harmony, buffer consonants, voicing
    assimilation and stem alternations. Returns the surface form plus a
    step-by-step derivation."""
    p = phonology
    form = lexeme.lemma
    steps = [DerivationStep("stem", f"citation form of {lexeme.lemma!r}", "stem", form)]

    # Backness is a property of the lexeme. For most words it is simply the
    # backness of the last vowel; disharmonic loans declare it instead.
    if lexeme.harmony_class:
        back = lexeme.harmony_class == "back"
    else:
        last = p.last_vowel(form)
        back = p.is_back(last) if last else True

    stem_exposed = True          # the stem's right edge is still adjacent to the suffix
    stem_form = form
    previous: Suffix | None = None
    applied: list[str] = []

    for suffix in suffixes:
        # Morphotactics before phonology: refuse sequences the language blocks
        # rather than generating a form no speaker would produce.
        clash = [s for s in suffix.cannot_follow if s in applied]
        if clash:
            raise MorphotacticError(
                f"{suffix.id} cannot follow {', '.join(clash)}: "
                f"{lexeme.lemma} + {' + '.join(applied + [suffix.id])} is not a Turkish word"
            )
        applied.append(suffix.id)

        if not suffix.is_overt:
            steps.append(DerivationStep(
                "zero_marker",
                f"{suffix.id} has no overt marker",
                "nothing is attached",
                form,
                {"suffix": suffix.id},
            ))
            previous = suffix
            continue

        optional, body = _parse(suffix)

        # A case suffix after 3rd person possessive is separated by n:
        # ev-i -> ev-i-n-de. The n takes the buffer slot, so the suffix's own
        # optional consonant does not appear.
        if previous is not None and previous.triggers_pronominal_n and suffix.category == "case":
            form += "n"
            steps.append(DerivationStep(
                "pronominal_n",
                f"{suffix.id} follows {previous.id}",
                "pronominal n is inserted",
                form,
                {"after": previous.id},
            ))

        ends_in_vowel = p.is_vowel(form[-1])
        optional_is_vowel = bool(optional) and (optional in ("A", "I") or p.is_vowel(optional))

        if optional is None:
            realise_optional = False
        elif optional_is_vowel:
            realise_optional = not ends_in_vowel      # -(I)m: ev-im, araba-m
        else:
            realise_optional = ends_in_vowel          # -(y)I: araba-yi, ev-i

        first_is_vowel = (
            optional_is_vowel if realise_optional
            else bool(body) and (body[0] in ("A", "I") or p.is_vowel(body[0]))
        )

        # ── stem alternations, only where the stem still meets the suffix ────
        if stem_exposed and first_is_vowel:
            # Confirmed with a native speaker: fikir + POSS1PL is fikrimiz
            # (syncope), but fikir + PRED1PL is fikiriz, not fikriz (no
            # syncope) -- "grammatical, but no one would say it" was the
            # exact judgement, which is a naturalness problem with the
            # example word, not a phonology problem with the form. The
            # predicative/copula suffixes do not trigger this stem's vowel
            # drop the way ordinary nominal suffixes (possessive, case) do.
            if lexeme.vowel_deletion and suffix.category != "predicative":
                form = p.delete_last_vowel(form)
                steps.append(DerivationStep(
                    "vowel_deletion",
                    f"{lexeme.lemma!r} drops its last stem vowel before a vowel-initial suffix",
                    f"syncope gives {form}-",
                    form,
                ))
            if lexeme.final_voicing and p.can_voice_final(form):
                before = form[-1]
                form = p.voice_final(form)
                steps.append(DerivationStep(
                    "final_voicing",
                    f"stem ends in voiceless /{before}/ and the suffix is vowel-initial",
                    f"intervocalic voicing gives {form}-",
                    form,
                ))

        # ── buffer segment ───────────────────────────────────────────────────
        if optional is not None:
            if realise_optional:
                inserted = optional
                if inserted in ("A", "I"):
                    inserted = p.resolve(inserted, form, back=back)
                form += inserted
                steps.append(DerivationStep(
                    "buffer",
                    f"stem ends in a {'vowel' if ends_in_vowel else 'consonant'}",
                    f"buffer {inserted} is inserted",
                    form,
                    {"segment": inserted},
                ))
            else:
                steps.append(DerivationStep(
                    "buffer",
                    f"stem ends in a {'vowel' if ends_in_vowel else 'consonant'}",
                    f"buffer {optional} is not inserted",
                    form,
                    {"segment": None},
                ))

        # ── the suffix body, segment by segment ──────────────────────────────
        for char in body:
            if char in ("A", "I"):
                resolved = p.resolve(char, form, back=back)
                trigger = p.last_vowel(form)
                harmony = "twofold" if char == "A" else "fourfold"
                shape = (
                    f"/{trigger}/ is {'back' if p.is_back(trigger) else 'front'}"
                    if char == "A" else
                    f"/{trigger}/ is {'back' if p.is_back(trigger) else 'front'}, "
                    f"{'rounded' if p.is_rounded(trigger) else 'unrounded'}"
                )
                form += resolved
                steps.append(DerivationStep(
                    "harmony",
                    f"last vowel {shape}",
                    f"{harmony} harmony resolves {char} to {resolved}",
                    form,
                    {"archiphoneme": char, "resolved": resolved},
                ))
            elif char in ("D", "C"):
                preceding = form[-1]
                resolved = p.resolve(char, form)
                form += resolved
                steps.append(DerivationStep(
                    "voicing_assimilation",
                    f"preceding /{preceding}/ is "
                    f"{'voiceless' if p.is_voiceless(preceding) else 'voiced'}",
                    f"{char} surfaces as {resolved}",
                    form,
                    {"archiphoneme": char, "resolved": resolved, "index": len(form) - 1},
                ))
            else:
                form += char

        steps.append(DerivationStep(
            "attach",
            f"{suffix.id} attached",
            f"{'-'.join(filter(None, [suffix.surface]))} realised",
            form,
            {"suffix": suffix.id},
        ))

        if stem_exposed:
            stem_form = _stem_after(steps)
        stem_exposed = False
        previous = suffix

    return InflectionResult(
        lexeme=lexeme,
        suffixes=tuple(suffixes),
        surface=form,
        stem_form=stem_form,
        steps=tuple(steps),
    )


def _stem_after(steps: list[DerivationStep]) -> str:
    """The stem as it stood after syncope and voicing, before anything was added."""
    stem = steps[0].form
    for step in steps:
        if step.rule in ("vowel_deletion", "final_voicing"):
            stem = step.form
        elif step.rule in ("buffer", "harmony", "voicing_assimilation", "attach", "pronominal_n"):
            break
    return stem
