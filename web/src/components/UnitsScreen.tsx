import { useEffect, useState } from 'react'
import { api, type ConceptProgress, type Unit } from '../lib/api'

// Free-roam navigation: every concept is clickable regardless of unit
// prerequisites or mastery, deliberately -- picking one on purpose is a
// stronger signal of what deserves the next turn than anything the
// scheduler could infer, so nothing here is locked.

function statusFor(progress: ConceptProgress[] | null, conceptId: string) {
  return progress?.find((c) => c.id === conceptId)
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

        <h1 className="text-xl font-semibold">Units</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Jump straight to any concept. Nothing here is locked &mdash; picking one skips ahead
          of whatever the usual order would serve next, and normal practice picks up again
          once you leave.
        </p>

        {error && <p className="mt-6 text-red-600 dark:text-red-400">{error}</p>}
        {!units && !error && <p className="mt-6 text-slate-500">Loading.</p>}

        {units && (
          <div className="mt-8 space-y-8">
            {units.map((unit) => (
              <section key={unit.id}>
                <h2 className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Unit {unit.order} &middot; {unit.title}
                </h2>
                <ul className="mt-3 space-y-1">
                  {unit.concepts.map((concept) => {
                    const status = statusFor(progress, concept.id)
                    return (
                      <li key={concept.id}>
                        <button
                          onClick={() => onSelectConcept(concept.id)}
                          className="flex w-full items-center justify-between gap-4 rounded-lg
                                     px-3 py-2 text-left hover:bg-slate-100
                                     focus:outline-none focus-visible:ring-2
                                     focus-visible:ring-indigo-400 focus-visible:ring-offset-2
                                     dark:hover:bg-slate-800"
                        >
                          <span className="font-medium">{concept.name}</span>
                          {status && (
                            <span className="shrink-0 text-xs text-slate-500 dark:text-slate-400">
                              {status.status}
                            </span>
                          )}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
