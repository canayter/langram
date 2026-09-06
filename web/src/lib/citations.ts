import type { BibliographyEntry } from './api'

// A citation with no authors on file yet (interleaving-over-blocking, at
// writing) falls back to its key, which is a fine identifier and a bad
// sentence: this turns "interleaving-over-blocking" into "Interleaving over
// blocking" rather than showing the raw slug. Not a citation for a name
// nobody knows -- a readable label for a topic that does not have one yet.
export function citationLabel(entry: BibliographyEntry): string {
  if (entry.authors) return entry.authors
  const words = entry.key.split('-')
  return words[0].charAt(0).toUpperCase() + words[0].slice(1) + ' ' + words.slice(1).join(' ')
}

// "needs_citation" is a content-authoring state -- the tradition and the
// claim are real, but nobody has checked the exact reference against the
// literature yet -- not a comment on whether the underlying research is
// legitimate. Labelling it "unverified" right next to VanPatten's or
// Pienemann's name reads as questioning the theory itself, which is
// exactly backwards, so the wording here is about the reference, not the
// person.
export const CITATION_PENDING_LABEL = 'reference pending'
export const CITATION_PENDING_TITLE =
  'The idea and the claim are established; the exact published reference has not been checked yet.'
