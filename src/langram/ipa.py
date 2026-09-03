"""A broad phonemic sketch, generated from spelling.

Turkish orthography is close to phonemic, which is what makes this defensible
as a deterministic function rather than a per-word guess: the mapping below is
a fact about the writing system, not an assertion about any specific lexeme.

What this deliberately does not claim:

- Stress. Mostly word-final, but with real exceptions (place names, the
  negative -mA, pre-stressing clitics), documented and not modelled here.
  Marking it wrong for every exception would be worse than not marking it.
- Fine allophonic detail: /k/ and /g/ palatalising before front vowels, vowel
  length in Arabic and Persian loanwords, the exact phonetic realisation of
  /r/ in different positions. This is a broad transcription, not a narrow one.
- ğ (yumuşak g) is the least settled part of this: it is not a consonant in
  most positions, so it is rendered here as length on the preceding vowel,
  which is the standard simplified description, not a claim about any
  particular speaker's realisation.

The one contextual rule this file does take a position on is clear versus dark
l, because it is called out in the project brief as a specific difficulty for
English speakers, and the engine already tracks the backness this rule needs.

Nothing here has been checked by a native speaker. `transcribe()` always
returns its result paired with that caveat; the caller decides how to show it.
"""
from __future__ import annotations

from .phonology import Phonology

# Vowels: standard Turkicist IPA (Göksel and Kerslake), not IPA-for-English.
_VOWEL_IPA = {
    "a": "a", "e": "e", "ı": "ɯ", "i": "i",
    "o": "o", "ö": "ø", "u": "u", "ü": "y",
}

# Consonants whose IPA symbol is not just the letter itself.
_CONSONANT_IPA = {
    "c": "dʒ", "ç": "tʃ", "j": "ʒ", "r": "ɾ", "ş": "ʃ", "y": "j",
}

CAVEAT = (
    "Generated from spelling using a standard letter-to-sound mapping, not "
    "checked by a native speaker. Stress is not marked."
)


def transcribe(phonology: Phonology, word: str) -> str:
    """A slash-delimited broad phonemic transcription of a Turkish word.

    `word` should be spelled correctly (lowercase, proper Turkish letters);
    this function does not correct spelling, only reads it.
    """
    word = word.lower()
    out: list[str] = []
    i = 0
    n = len(word)
    while i < n:
        ch = word[i]
        if ch == "ğ":
            # Not a consonant in most positions: lengthens what precedes it.
            # Word-initial ğ does not occur in Turkish, so there is always a
            # preceding symbol to lengthen.
            if out and not out[-1].endswith("ː"):
                out[-1] = out[-1] + "ː"
        elif phonology.is_vowel(ch):
            out.append(_VOWEL_IPA.get(ch, ch))
        elif ch == "l":
            out.append("ɫ" if _local_backness(phonology, word, i) else "l")
        else:
            out.append(_CONSONANT_IPA.get(ch, ch))
        i += 1
    return "/" + "".join(out) + "/"


def _local_backness(phonology: Phonology, word: str, index: int) -> bool:
    """Backness of the vowel nearest this position in the word.

    Clear/dark l is a syllable-level allophonic rule in Turkish, not a
    word-level harmony rule, so it needs the local vowel, not the word's
    last one: bilgisayar has a back final vowel but a front one right next
    to its only l, and should keep a clear l there regardless. Ties (a
    consonant sitting exactly between two vowels) favour the preceding
    vowel, since l is overwhelmingly a syllable coda in Turkish, following
    the vowel that governs it.
    """
    before = after = None
    for j in range(index - 1, -1, -1):
        if phonology.is_vowel(word[j]):
            before = (index - j, word[j])
            break
    for j in range(index + 1, len(word)):
        if phonology.is_vowel(word[j]):
            after = (j - index, word[j])
            break
    if before and after:
        vowel = before[1] if before[0] <= after[0] else after[1]
    else:
        picked = before or after
        vowel = picked[1] if picked else None
    return phonology.is_back(vowel) if vowel else True
