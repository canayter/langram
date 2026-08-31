import { useEffect, useState } from 'react'
import { api, type Unit } from '../lib/api'

// Transparency about method is part of the product, so the reason for an
// exercise is one click away rather than buried in a marketing page.
export function WhyPanel({ unitId, conceptId }: { unitId: string; conceptId: string }) {
  const [open, setOpen] = useState(false)
  const [units, setUnits] = useState<Unit[] | null>(null)

  useEffect(() => {
    if (open && !units) api.units().then(setUnits).catch(() => setUnits([]))
  }, [open, units])

  const unit = units?.find((u) => u.id === unitId)
  const concept = unit?.concepts.find((c) => c.id === conceptId)

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
        <div className="mt-3 space-y-3 rounded-lg border border-slate-200 p-4 text-sm
                        text-slate-600 dark:border-slate-700 dark:text-slate-300">
          {!units && <p>Loading.</p>}
          {concept && (
            <p><span className="font-medium text-slate-900 dark:text-slate-100">
              What is hard here.</span> {concept.why_hard}</p>
          )}
          {unit && (
            <>
              <p><span className="font-medium text-slate-900 dark:text-slate-100">
                Why this unit is here.</span> {unit.rationale}</p>
              <p className="font-mono text-xs text-slate-500 dark:text-slate-400">
                {unit.research_refs.join('  ')}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}
