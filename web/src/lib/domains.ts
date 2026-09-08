// A presentational grouping only, not a linguistic claim -- unlike
// research_refs and lexicon flags, this needs no citation and no backend
// schema, so it lives here rather than in content/. It exists so UnitsScreen
// can draw the curriculum as a route map (each domain a line color) instead
// of a flat list, the way a transit map encodes which stops share a line.
//
// Nominal: units built on noun morphology and nominal predication.
// Verbal: units built on verb tense, aspect and modality.
// Particle: units built on phrase.py -- invariant particles composed with
// an inflected word, rather than a suffix chain on one stem.
export type Domain = 'nominal' | 'verbal' | 'particle'

const UNIT_DOMAIN: Record<number, Domain> = {
  1: 'nominal',
  2: 'nominal',
  3: 'nominal',
  4: 'nominal',
  5: 'verbal',
  6: 'verbal',
  7: 'particle',
  8: 'particle',
  9: 'particle',
  10: 'verbal',
  11: 'particle',
}

export const DOMAIN_LABEL: Record<Domain, string> = {
  nominal: 'Nominal',
  verbal: 'Verbal, tense',
  particle: 'Particle, phrase',
}

// A unit past the last one this file knows about reads as its nearest
// neighbor's domain rather than an undefined color, so a new unit shipping
// without a matching UI change degrades to "probably fine" instead of blank.
export function domainFor(unitOrder: number): Domain {
  return UNIT_DOMAIN[unitOrder] ?? 'particle'
}
