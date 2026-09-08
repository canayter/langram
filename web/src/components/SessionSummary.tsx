import { TAG_LABELS } from '../lib/labels'
import { useStats } from '../lib/store'
import { primaryButton } from '../lib/ui'

// A stopping point, not a score. The block runs until SessionScreen decides
// enough items have been answered, then this stands between the learner and
// an endless loop, the same way a real lesson has an end rather than just
// trailing off.

export type SessionStats = {
  answered: number
  correct: number
  marks: number
  concepts: Map<string, string>
  mistakes: Record<string, number>
}

export function SessionSummary({ stats, onContinue }: { stats: SessionStats; onContinue: () => void }) {
  const { streak } = useStats()
  const accuracy = stats.answered > 0 ? Math.round((stats.correct / stats.answered) * 100) : null
  const mistakes = Object.entries(stats.mistakes).sort((a, b) => b[1] - a[1])

  return (
    <div>
      <p className="font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
        Session complete
      </p>
      <h1 className="font-display mt-1 text-lg font-semibold text-ink">
        {stats.answered} exercises{accuracy !== null && `, ${accuracy} percent right`}
      </h1>

      <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div>
          <dt className="font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
            Marks earned
          </dt>
          <dd className="mt-1 text-lg font-semibold text-accent">
            +{stats.marks}
          </dd>
        </div>
        <div>
          <dt className="font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
            Day chain
          </dt>
          <dd className="mt-1 text-lg font-semibold text-mark">
            {streak}
          </dd>
        </div>
        <div>
          <dt className="font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
            Concepts practiced
          </dt>
          <dd className="mt-1 text-lg font-semibold text-ink">
            {stats.concepts.size}
          </dd>
        </div>
      </dl>

      {stats.concepts.size > 0 && (
        <p className="mt-4 text-sm text-ink-dim">
          {Array.from(stats.concepts.values()).join(', ')}
        </p>
      )}

      {mistakes.length > 0 && (
        <section className="mt-8">
          <h2 className="font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
            Worth a second look
          </h2>
          <ul className="mt-3 space-y-1 text-sm text-ink-dim">
            {mistakes.map(([tag, count]) => (
              <li key={tag}>
                {TAG_LABELS[tag] ?? tag} &times; {count}
              </li>
            ))}
          </ul>
        </section>
      )}

      <button onClick={onContinue} className={`${primaryButton} mt-8`} autoFocus>
        Keep practicing
      </button>
      <p className="mt-3 text-sm text-ink-dim">
        Or come back tomorrow to keep the chain going &mdash; Progress and Reference are still
        up above.
      </p>
    </div>
  )
}
