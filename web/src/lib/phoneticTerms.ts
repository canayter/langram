// A closed glossary: every symbol transcribe() in the backend's ipa.py can
// produce, and only those, so this can never claim a term for a sound the
// transcription itself does not generate. The symbol-to-description mapping
// is standard IPA nomenclature (place, manner, voicing), not a claim about
// any specific Turkish word -- that claim is exactly what ipa_caveat already
// hedges, separately, per word.
export type PhoneticTerm = { symbol: string; term: string; note?: string }

const VOWELS: PhoneticTerm[] = [
  { symbol: 'a', term: 'open back unrounded vowel', note: 'as in father, but shorter' },
  { symbol: 'e', term: 'open-mid front unrounded vowel', note: 'as in bed' },
  { symbol: 'ɯ', term: 'close back unrounded vowel', note: 'no close English equivalent -- said with the tongue back but lips unrounded' },
  { symbol: 'i', term: 'close front unrounded vowel', note: 'as in see, but shorter' },
  { symbol: 'o', term: 'close-mid back rounded vowel', note: 'as in go, but a pure vowel, not a diphthong' },
  { symbol: 'ø', term: 'close-mid front rounded vowel', note: 'like German ö or French eu' },
  { symbol: 'u', term: 'close back rounded vowel', note: 'as in boot' },
  { symbol: 'y', term: 'close front rounded vowel', note: 'like German ü or French u' },
]

const CONSONANTS: PhoneticTerm[] = [
  { symbol: 'b', term: 'voiced bilabial plosive' },
  { symbol: 'dʒ', term: 'voiced postalveolar affricate', note: 'as in jam' },
  { symbol: 'tʃ', term: 'voiceless postalveolar affricate', note: 'as in chip' },
  { symbol: 'd', term: 'voiced alveolar plosive' },
  { symbol: 'f', term: 'voiceless labiodental fricative' },
  { symbol: 'g', term: 'voiced velar plosive' },
  { symbol: 'h', term: 'voiceless glottal fricative' },
  { symbol: 'ʒ', term: 'voiced postalveolar fricative', note: 'as in measure' },
  { symbol: 'k', term: 'voiceless velar plosive' },
  { symbol: 'ɫ', term: 'velarised (dark) alveolar lateral approximant', note: 'like the l in English milk' },
  { symbol: 'l', term: 'alveolar lateral approximant', note: 'clear l, like the l in English leaf' },
  { symbol: 'm', term: 'voiced bilabial nasal' },
  { symbol: 'n', term: 'voiced alveolar nasal' },
  { symbol: 'p', term: 'voiceless bilabial plosive' },
  { symbol: 'ɾ', term: 'voiced alveolar tap', note: 'a single flick of the tongue, like Spanish pero' },
  { symbol: 's', term: 'voiceless alveolar fricative' },
  { symbol: 'ʃ', term: 'voiceless postalveolar fricative', note: 'as in she' },
  { symbol: 't', term: 'voiceless alveolar plosive' },
  { symbol: 'v', term: 'voiced labiodental fricative' },
  { symbol: 'j', term: 'voiced palatal approximant', note: 'as in yes' },
  { symbol: 'z', term: 'voiced alveolar fricative' },
]

const OTHER: PhoneticTerm[] = [
  { symbol: 'ː', term: 'length mark', note: 'lengthens the vowel before it -- how yumuşak g (ğ) is represented here' },
]

const ALL = [...VOWELS, ...CONSONANTS, ...OTHER]
const BY_SYMBOL = new Map(ALL.map((t) => [t.symbol, t]))

// Longest symbol first, so the two-character affricates (dʒ, tʃ) are read as
// one segment rather than as two consonants that happen to be adjacent.
const SYMBOLS_BY_LENGTH = [...ALL.map((t) => t.symbol)].sort((a, b) => b.length - a.length)

export function breakdown(ipa: string): PhoneticTerm[] {
  const body = ipa.replace(/^\//, '').replace(/\/$/, '')
  const out: PhoneticTerm[] = []
  let i = 0
  outer: while (i < body.length) {
    for (const symbol of SYMBOLS_BY_LENGTH) {
      if (body.startsWith(symbol, i)) {
        const term = BY_SYMBOL.get(symbol)
        if (term) out.push(term)
        i += symbol.length
        continue outer
      }
    }
    i += 1 // an unrecognised character (should not happen) is skipped, not thrown
  }
  return out
}

export function canSpeak(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

// Synthesized, not a recording of a native speaker -- a pronunciation aid,
// not the perception training docs/deferred-audio.md describes and
// deliberately has not built yet (that needs real talkers). Quality and
// even availability of a Turkish voice varies by browser and OS; there is
// no good way to detect a good voice ahead of time, so this fails silently
// rather than blocking on a check that would be wrong as often as right.
export function speak(text: string) {
  if (!canSpeak()) return
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'tr-TR'
  utterance.rate = 0.85
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(utterance)
}
