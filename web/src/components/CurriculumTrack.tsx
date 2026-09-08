import { useMemo } from 'react'
import type { ConceptProgress } from '../lib/api'

// A single horizontal line across the whole curriculum, not the session:
// unlike the "N of 5" block badge or the 10-item session bar (both of which
// legitimately reset), this one only ever reflects real, standing mastery,
// so nothing about it resets when a topic changes or a session ends.
// Requested directly: "a line that moves with every answer... and shows
// where the units change."
//
// Segmented by unit, equal width per unit regardless of how many concepts
// it holds, so unit boundaries stay legible and predictable rather than
// some units being a sliver and others half the bar. Each segment's own
// fill is that unit's average concept mastery (BKT's ability_estimate,
// the same number ProgressScreen already shows per concept, never a raw
// answered-item count), which moves on every single answer: the mastery
// value AnswerOut already returns after each item updates exactly one
// concept, and that concept belongs to exactly one segment.

export type UnitSummary = { id: string; title: string; order: number; fill: number }

export function summarizeUnits(
  concepts: ConceptProgress[] | null,
  overrides: Record<string, number>,
): UnitSummary[] {
  if (!concepts) return []
  const order: string[] = []
  const titles = new Map<string, string>()
  const sums = new Map<string, number>()
  const counts = new Map<string, number>()
  for (const c of concepts) {
    if (!titles.has(c.unit_id)) {
      titles.set(c.unit_id, c.unit_title)
      order.push(c.unit_id)
    }
    const value = overrides[c.id] ?? c.p_known
    sums.set(c.unit_id, (sums.get(c.unit_id) ?? 0) + value)
    counts.set(c.unit_id, (counts.get(c.unit_id) ?? 0) + 1)
  }
  return order.map((id, i) => ({
    id, title: titles.get(id) ?? id, order: i + 1,
    fill: (sums.get(id) ?? 0) / (counts.get(id) || 1),
  }))
}

export function CurriculumTrack({ units, currentUnitId }: {
  units: UnitSummary[]
  currentUnitId?: string | null
}) {
  const overall = useMemo(() => {
    if (!units.length) return 0
    return units.reduce((sum, u) => sum + u.fill, 0) / units.length
  }, [units])

  if (!units.length) return null

  return (
    <div className="mb-6" aria-label="Progress across the whole curriculum, by unit">
      <div className="flex items-baseline justify-between text-xs font-medium text-ink-dim">
        <span>The curriculum</span>
        <span className="font-mono">{Math.round(overall * 100)}%</span>
      </div>
      <div className="mt-1.5 flex h-2 w-full gap-px overflow-hidden rounded-full bg-surface-2">
        {units.map((u) => {
          const isCurrent = u.id === currentUnitId
          return (
            <div
              key={u.id}
              title={`${u.order}. ${u.title} — ${Math.round(u.fill * 100)}%`}
              className={`relative h-full flex-1 overflow-hidden bg-surface-2 ${
                isCurrent ? 'ring-1 ring-inset ring-accent' : ''
              }`}
            >
              <div
                className={`h-full transition-[width] duration-700 ease-out ${
                  isCurrent ? 'bg-accent' : 'bg-mark'
                }`}
                style={{ width: `${Math.round(u.fill * 100)}%` }}
              />
            </div>
          )
        })}
      </div>
      {currentUnitId && (
        <p className="mt-1 text-[0.7rem] text-ink-dim">
          Unit {units.find((u) => u.id === currentUnitId)?.order ?? '–'} of {units.length}
          {' — '}
          {units.find((u) => u.id === currentUnitId)?.title}
        </p>
      )}
    </div>
  )
}
