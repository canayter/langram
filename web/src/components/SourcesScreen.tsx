import { useEffect, useState } from 'react'
import { api, type BibliographyEntry } from '../lib/api'

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
    <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between">
          <span className="font-mono text-sm tracking-tight text-slate-400">langram</span>
          <button
            onClick={onBack}
            className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
          >
            Back to practice
          </button>
        </div>

        <h1 className="font-display text-xl font-semibold">Sources</h1>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          Every pedagogical decision here is meant to trace back to a real claim in the
          literature, not a guess dressed up as one. This is the full list a unit is allowed to
          cite &mdash; nothing on it is invented, and a source not yet checked against the actual
          text says so, rather than pretending otherwise.
        </p>

        {error && <p className="mt-6 text-rose-600 dark:text-rose-400">{error}</p>}
        {!entries && !error && <p className="mt-6 text-slate-500">Loading.</p>}

        {entries && AREA_ORDER.map((area) => {
          const group = entries.filter((e) => e.area === area)
          if (!group.length) return null
          return (
            <section key={area} className="mt-10 border-t border-slate-200 pt-6 dark:border-slate-800">
              <h2 className="font-display font-semibold text-xs uppercase tracking-wider
                             text-rose-600 dark:text-rose-400">
                {AREA_LABELS[area] ?? area}
              </h2>
              <ul className="mt-4 space-y-5">
                {group.map((entry) => (
                  <li
                    key={entry.key}
                    className="border-l-2 border-transparent pl-3 transition-colors
                               hover:border-rose-400"
                  >
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                      <span className="font-display font-medium text-slate-900 dark:text-slate-50">
                        {entry.authors ?? entry.key}
                      </span>
                      {entry.year && (
                        <span className="font-mono text-xs text-slate-400">{entry.year}</span>
                      )}
                      {entry.status === 'needs_citation' && (
                        <span className="rounded-full border border-amber-300 px-2 py-0.5
                                         text-[0.65rem] font-medium uppercase tracking-wide
                                         text-amber-700 dark:border-amber-800 dark:text-amber-400">
                          unverified
                        </span>
                      )}
                    </div>
                    {entry.title && (
                      <p className="mt-0.5 text-sm italic text-slate-600 dark:text-slate-300">
                        {entry.title}
                      </p>
                    )}
                    <p className="mt-1 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
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
