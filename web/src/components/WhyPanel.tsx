import { useEffect, useState } from 'react'
import { api, type BibliographyEntry, type Unit } from '../lib/api'
import { CITATION_PENDING_LABEL, CITATION_PENDING_TITLE, citationLabel } from '../lib/citations'

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
        className="text-sm text-ink-dim underline underline-offset-4 hover:text-ink"
      >
        Why this exercise
      </button>
      {open && (
        <div className="mt-3 space-y-4 rounded-md border border-grid p-4 text-sm
                        text-ink-dim">
          {!units && <p>Loading.</p>}
          {concept && (
            <p><span className="font-medium text-ink">
              What is hard here.</span> {concept.why_hard}</p>
          )}
          {unit && (
            <p><span className="font-medium text-ink">
              Why this unit is here.</span> {unit.rationale}</p>
          )}
          {refs && refs.length > 0 && (
            <ul className="space-y-2 border-t border-grid pt-3">
              {refs.map((ref) => (
                <li key={ref.key}>
                  <p>
                    <span className="font-display font-medium text-ink">
                      {citationLabel(ref)}
                    </span>
                    {ref.year && <span className="font-mono text-xs text-ink-dim"> &middot; {ref.year}</span>}
                    {ref.status === 'needs_citation' && (
                      <span
                        title={CITATION_PENDING_TITLE}
                        className="ml-1 text-xs text-ink-dim opacity-75"
                      >
                        &middot; {CITATION_PENDING_LABEL}
                      </span>
                    )}
                  </p>
                  <span className="block text-ink-dim">{ref.claim}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
