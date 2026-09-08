import { useEffect, useState } from 'react'
import { api, type BibliographyEntry } from '../lib/api'
import { CITATION_PENDING_LABEL, CITATION_PENDING_TITLE, citationLabel } from '../lib/citations'

// The credibility claim of an app that says it is research grounded costs
// nothing to expose and everything to hide: every citation a unit is allowed
// to draw on, read straight from the same file the content validator checks
// research_refs against, so this can never list a source the app does not
// actually rely on, and can never omit one it does.

const AREA_LABELS: Record<string, string> = {
  sla: 'Second language acquisition',
  memory: 'Memory and practice',
  'l2-speech': 'L2 speech and perception',
  turkish: 'Turkish',
  assessment: 'Assessment',
}

const AREA_ORDER = ['sla', 'memory', 'l2-speech', 'turkish', 'assessment']

export function SourcesScreen({ onBack }: { onBack: () => void }) {
  const [entries, setEntries] = useState<BibliographyEntry[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.bibliography().then(setEntries).catch((e) => setError((e as Error).message))
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

        <h1 className="font-display text-xl font-semibold">Sources</h1>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-dim">
          Every pedagogical decision here is meant to trace back to a real claim in the
          literature, not a guess dressed up as one. This is the full list a unit is allowed to
          cite. A "reference pending" tag means the idea and the claim are established, but the
          exact published reference has not been checked page by page yet &mdash; it is not a
          question about whether the research itself is legitimate.
        </p>

        {error && <p className="mt-6 text-red-600 dark:text-red-400">{error}</p>}
        {!entries && !error && <p className="mt-6 text-ink-dim">Loading.</p>}

        {entries && AREA_ORDER.map((area) => {
          const group = entries.filter((e) => e.area === area)
          if (!group.length) return null
          return (
            <section key={area} className="mt-10 border-t border-grid pt-6">
              <h2 className="font-display font-semibold text-xs uppercase tracking-wider
                             text-accent">
                {AREA_LABELS[area] ?? area}
              </h2>
              <ul className="mt-4 space-y-5">
                {group.map((entry) => (
                  <li
                    key={entry.key}
                    className="border-l-2 border-transparent pl-3 transition-colors
                               hover:border-accent"
                  >
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                      <span className="font-display font-medium text-ink">
                        {citationLabel(entry)}
                      </span>
                      {entry.year && (
                        <span className="font-mono text-xs text-ink-dim">{entry.year}</span>
                      )}
                      {entry.status === 'needs_citation' && (
                        <span
                          title={CITATION_PENDING_TITLE}
                          className="rounded-full border border-grid px-2 py-0.5
                                     text-[0.65rem] font-medium text-ink-dim"
                        >
                          {CITATION_PENDING_LABEL}
                        </span>
                      )}
                    </div>
                    {entry.title && (
                      <p className="mt-0.5 text-sm italic text-ink-dim">
                        {entry.title}
                      </p>
                    )}
                    <p className="mt-1 text-sm leading-relaxed text-ink-dim">
                      {entry.claim}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          )
        })}
      </div>
    </div>
  )
}
