import { useEffect, useState } from 'react'
import { api, type ConceptProgress, type Unit } from '../lib/api'
import { DOMAIN_LABEL, domainFor, type Domain } from '../lib/domains'

// Free-roam navigation: every concept is clickable regardless of unit
// prerequisites or mastery, deliberately -- picking one on purpose is a
// stronger signal of what deserves the next turn than anything the
// scheduler could infer, so nothing here is locked.
//
// Drawn as a route map rather than a flat list: eleven units with real
// prerequisites between them and three recurring grammatical domains is
// closer to a transit line than a table of contents, so each domain gets
// its own line color the way a metro map codes lines, and a learner can
// see at a glance which grammar family a unit belongs to before reading
// a word of it.

function statusFor(progress: ConceptProgress[] | null, conceptId: string) {
  return progress?.find((c) => c.id === conceptId)
}

const DOMAIN_DOT: Record<Domain, string> = {
  nominal: 'border-domain-nominal',
  verbal: 'border-domain-verbal',
  particle: 'border-domain-particle',
}

const DOMAIN_TEXT: Record<Domain, string> = {
  nominal: 'text-domain-nominal',
  verbal: 'text-domain-verbal',
  particle: 'text-domain-particle',
}

function Legend() {
  const domains: Domain[] = ['nominal', 'verbal', 'particle']
  return (
    <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1.5 font-mono text-xs text-ink-dim">
      {domains.map((d) => (
        <span key={d} className="flex items-center gap-1.5">
          <span aria-hidden className={`h-2.5 w-2.5 shrink-0 rounded-full border-2 ${DOMAIN_DOT[d]}`} />
          {DOMAIN_LABEL[d]}
        </span>
      ))}
    </div>
  )
}

export function UnitsScreen({ onBack, onSelectConcept }: {
  onBack: () => void
  onSelectConcept: (conceptId: string) => void
}) {
  const [units, setUnits] = useState<Unit[] | null>(null)
  const [progress, setProgress] = useState<ConceptProgress[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.units(), api.progress()])
      .then(([u, p]) => {
        setUnits(u)
        setProgress(p.concepts)
      })
      .catch((e) => setError((e as Error).message))
  }, [])

  return (
    <div className="min-h-screen bg-ground text-ink">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between">
          <button
            onClick={onBack}
            className="rounded-md font-display text-sm font-medium tracking-tight text-ink-dim
                       hover:text-ink focus:outline-none focus-visible:ring-2
                       focus-visible:ring-accent focus-visible:ring-offset-2"
          >
            langram
          </button>
          <button
            onClick={onBack}
            className="text-sm text-ink-dim hover:text-ink"
          >
            Back to practice
          </button>
        </div>

        <h1 className="font-display text-xl font-semibold">Units</h1>
        <p className="mt-2 text-sm text-ink-dim">
          Jump straight to any concept. Nothing here is locked &mdash; picking one skips ahead
          of whatever the usual order would serve next, and normal practice picks up again
          once you leave.
        </p>
        <Legend />

        {error && <p className="mt-6 text-red-600 dark:text-red-400">{error}</p>}
        {!units && !error && <p className="mt-6 text-ink-dim">Loading.</p>}

        {units && (
          <ol className="relative mt-8 space-y-8 border-l-2 border-grid pl-6">
            {units.map((unit) => {
              const domain = domainFor(unit.order)
              return (
                <li key={unit.id} className="relative">
                  <span
                    aria-hidden
                    className={`absolute -left-[27px] top-1 h-3 w-3 rounded-full border-[3px] bg-ground ${DOMAIN_DOT[domain]}`}
                  />
                  <h2 className="flex items-baseline gap-2 font-display text-xs font-semibold uppercase tracking-wider">
                    <span className="font-mono text-ink-dim">{String(unit.order).padStart(2, '0')}</span>
                    <span className={DOMAIN_TEXT[domain]}>{unit.title}</span>
                  </h2>
                  <ul className="mt-3 space-y-1">
                    {unit.concepts.map((concept) => {
                      const status = statusFor(progress, concept.id)
                      return (
                        <li key={concept.id}>
                          <button
                            onClick={() => onSelectConcept(concept.id)}
                            className="flex w-full items-center justify-between gap-4 rounded-md
                                       px-3 py-2 text-left hover:bg-surface-2
                                       focus:outline-none focus-visible:ring-2
                                       focus-visible:ring-accent focus-visible:ring-offset-2"
                          >
                            <span className="font-medium">{concept.name}</span>
                            {status && (
                              <span className="shrink-0 text-xs text-ink-dim">
                                {status.status}
                              </span>
                            )}
                          </button>
                        </li>
                      )
                    })}
                  </ul>
                </li>
              )
            })}
          </ol>
        )}
      </div>
    </div>
  )
}
