import { useEffect, useState } from 'react'
import { api, type BibliographyEntry, type Unit } from '../lib/api'

// Transparency about method is part of the product, so the reason for an
// exercise is one click away rather than buried in a marketing page. The
// citation itself used to be the bare key from research_refs
// ("vanpatten-input-processing"); now it resolves to the actual author,
// year and claim from /api/bibliography, the same file the content
// validator checks every research_ref against.
export function WhyPanel({ unitId, conceptId }: { unitId: string; conceptId: string }) {
  const [open, setOpen] = useState(false)
  const [units, setUnits] = useState<Unit[] | null>(null)
  const [bibliography, setBibliography] = useState<BibliographyEntry[] | null>(null)

  useEffect(() => {
    if (!open) return
    if (!units) api.units().then(setUnits).catch(() => setUnits([]))
    if (!bibliography) api.bibliography().then(setBibliography).catch(() => setBibliography([]))
  }, [open, units, bibliography])

  const unit = units?.find((u) => u.id === unitId)
  const concept = unit?.concepts.find((c) => c.id === conceptId)
  const refs = unit?.research_refs
    .map((key) => bibliography?.find((b) => b.key === key))
    .filter((b): b is BibliographyEntry => Boolean(b))

  return (
    <div className="mt-6">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="text-sm text-slate-500 underline underline-offset-4 hover:text-slate-800
                   dark:text-slate-400 dark:hover:text-slate-200"
      >
        Why this exercise
      </button>
      {open && (
        <div className="mt-3 space-y-4 rounded-lg border border-slate-200 p-4 text-sm
                        text-slate-600 dark:border-slate-700 dark:text-slate-300">
          {!units && <p>Loading.</p>}
          {concept && (
            <p><span className="font-medium text-slate-900 dark:text-slate-100">
              What is hard here.</span> {concept.why_hard}</p>
          )}
          {unit && (
            <p><span className="font-medium text-slate-900 dark:text-slate-100">
              Why this unit is here.</span> {unit.rationale}</p>
          )}
          {refs && refs.length > 0 && (
            <ul className="space-y-2 border-t border-slate-200 pt-3 dark:border-slate-800">
              {refs.map((ref) => (
                <li key={ref.key}>
                  <span className="font-display font-medium text-slate-800 dark:text-slate-200">
                    {ref.authors ?? ref.key}
                  </span>
                  {ref.year && (
                    <span className="ml-1 font-mono text-xs text-slate-400">{ref.year}</span>
                  )}
                  {ref.status === 'needs_citation' && (
                    <span className="ml-1.5 text-xs text-amber-600 dark:text-amber-400">
                      unverified
                    </span>
                  )}
                  <span className="block text-slate-500 dark:text-slate-400">{ref.claim}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
