"""The form is the only cue to the meaning.

Three shapes, chosen by the exercise parameters:

  gloss    a form is shown and the learner says what it means, where only the
           suffix distinguishes the options
  trigger  which vowel decided the shape of the suffix
  buffer   which of these words needed an extra sound

All three are comprehension. Nothing is produced, which is the point: a learner
should process a form before being asked to make one.
"""
from __future__ import annotations

import random

from . import COMPREHENSION, GeneratedItem, GenerationError
from ._common import (
    candidate_lexemes, chain, ends_in_vowel, pick_lexeme, realisation, suffix_choices,
    syllable_count,
)
from ..ipa import CAVEAT as IPA_CAVEAT
from ..ipa import transcribe


def _mode(params: dict) -> str:
    highlight = str(params.get("highlight") or "")
    if highlight == "last_stem_vowel":
        return "trigger"
    if highlight == "buffer_segment":
        return "buffer"
    return "gloss"


def _gloss_suffixes(language, params: dict) -> list[str]:
    chosen = suffix_choices(params)
    if chosen:
        return chosen
    cue = str(params.get("cue") or "")
    category = "possessive" if "possessive" in cue else "predicative" if "person" in cue else ""
    if not category:
        raise GenerationError("form_meaning_match needs persons, or a cue naming a category")
    return [s.id for s in language.suffixes.values() if s.category == category]


def build(exercise, language, rng: random.Random) -> GeneratedItem:
    params = dict(exercise.params or {})
    mode = _mode(params)

    if mode == "gloss":
        options = _gloss_suffixes(language, params)
        if len(options) < 2:
            raise GenerationError(f"{exercise.id}: a meaning choice needs at least two suffixes")
        suffix_id = rng.choice(options)
        lexeme = pick_lexeme(language, params, rng)
        spec = {"mode": mode, "lemma": lexeme.lemma, "suffixes": chain(params, suffix_id),
                "options": sorted(options)}

    elif mode == "trigger":
        params.setdefault("min_syllables", 2)
        suffixes = suffix_choices(params) or ["PL"]
        # Not every word with two or more vowels has two or more DIFFERENT
        # vowels: anahtar has three, all of them a, which leaves nothing to
        # actually choose between. Retried rather than checked once, the way
        # the other generators handle a draw that will not work out, since
        # min_syllables alone cannot rule this out ahead of time.
        for _ in range(12):
            lexeme = pick_lexeme(language, params, rng)
            if len({ch for ch in lexeme.lemma if language.phonology.is_vowel(ch)}) >= 2:
                break
        else:
            raise GenerationError(f"{exercise.id}: no candidate word has two different vowels")
        spec = {"mode": mode, "lemma": lexeme.lemma, "suffixes": [rng.choice(suffixes)]}

    else:
        suffixes = suffix_choices(params) or ["POSS3SG"]
        suffix_id = rng.choice(suffixes)
        pool = candidate_lexemes(language, params)
        vowel_final = [lx for lx in pool if ends_in_vowel(language, lx.lemma)]
        consonant_final = [lx for lx in pool if not ends_in_vowel(language, lx.lemma)]
        if not vowel_final or len(consonant_final) < 2:
            raise GenerationError(f"{exercise.id}: not enough stems of both shapes")
        chosen = [rng.choice(vowel_final)] + rng.sample(consonant_final, 2)
        spec = {"mode": mode, "lemma": chosen[0].lemma, "suffixes": [suffix_id],
                "others": [lx.lemma for lx in chosen[1:]]}

    return assemble(exercise, language, spec)


def assemble(exercise, language, spec: dict) -> GeneratedItem:
    mode = spec.get("mode", "gloss")
    lemma, suffix_ids = spec["lemma"], list(spec["suffixes"])
    lexeme = language.lexeme(lemma)
    result = language.inflect(lexeme, suffix_ids)
    seed = f"{mode}|{lemma}|{'+'.join(suffix_ids)}"

    if mode == "gloss":
        option_ids = list(spec["options"])
        labels = {sid: _label(language, sid) for sid in option_ids}
        options = sorted(labels[sid] for sid in option_ids)
        answer = labels[suffix_ids[-1]]
        question = result.surface
        payload = {"kind": "choose_meaning", "form": question, "gloss": lexeme.gloss,
                   "options": options}

    elif mode == "trigger":
        vowels = [ch for ch in lexeme.lemma if language.phonology.is_vowel(ch)]
        options = sorted(set(vowels))
        if len(options) < 2:
            # Reachable directly through assemble(), e.g. replaying a stale
            # review card for a word content has since changed, so this
            # stays a real check rather than trusting build()'s retry alone.
            raise GenerationError(f"{lemma} has no two different vowels, so there is nothing to choose")
        answer = vowels[-1]
        payload = {"kind": "choose_letter", "form": result.surface, "stem": lexeme.lemma,
                   "gloss": lexeme.gloss, "options": options}

    else:
        others = [language.lexeme(l) for l in spec["others"]]
        lexemes = [lexeme, *others]
        forms = [language.inflect(lx, suffix_ids).surface for lx in lexemes]
        answer = forms[0]                       # the vowel-final stem, which needed the buffer
        options = list(forms)
        random.Random(seed).shuffle(options)
        # Three different words share one item here, not three shapes of one
        # word, so one gloss and one transcription is not enough: every
        # option needs its own, keyed by the surface form shown for it.
        word_info = {
            form: {"gloss": lx.gloss, "ipa": transcribe(language.phonology, form)}
            for lx, form in zip(lexemes, forms)
        }
        payload = {"kind": "choose_form", "options": options, "word_info": word_info,
                   "word_info_caveat": IPA_CAVEAT,
                   "suffix": {"id": language.suffix(suffix_ids[0]).id,
                              "notation": language.suffix(suffix_ids[0]).surface,
                              "glosses": list(language.suffix(suffix_ids[0]).glosses)}}

    return GeneratedItem(
        exercise_id=exercise.id,
        concept_id=exercise.concept_id,
        generator="form_meaning_match",
        stage=exercise.stage,
        prompt=exercise.prompt or "What does this mean?",
        spec=spec,
        payload=payload,
        answer=answer,
        accepted=(answer,),
        derivation=tuple(
            {"rule": s.rule, "condition": s.condition, "result": s.result, "form": s.form}
            for s in result.steps
        ),
        diagnosis=COMPREHENSION,
        lemma=lemma,
        suffixes=tuple(suffix_ids),
        extra={"mode": mode},
    )


def _label(language, suffix_id: str) -> str:
    suffix = language.suffix(suffix_id)
    return suffix.glosses[0] if suffix.glosses else suffix.id
