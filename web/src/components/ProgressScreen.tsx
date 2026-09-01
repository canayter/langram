import { useEffect, useState } from 'react'
import { api, type Progress } from '../lib/api'

// The report is per rule and per concept rather than a score, because a
// percentage tells a learner nothing they can act on.

function Bar({ value, tone }: { value: number; tone: 'good' | 'weak' | 'neutral' }) {
  const colour =
    tone === 'good' ? 'bg-emerald-500' : tone === 'weak' ? 'bg-amber-500' : 'bg-slate-400'
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
      <div className={`h-full ${colour}`} style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  )
}

export function ProgressScreen({ onBack }: { onBack: () => void }) {
  const [report, setReport] = useState<Progress | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.progress().then(setReport).catch((e) => setError((e as Error).message))
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

        {error && <p className="text-red-600 dark:text-red-400">{error}</p>}
        {!report && !error && <p className="text-slate-500">Loading.</p>}

        {report && (
          <>
            <h1 className="text-xl font-semibold">{report.headline}</h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {report.answered} answered
              {report.accuracy !== null && `, ${Math.round(report.accuracy * 100)} percent right`}
            </p>

            {report.skills.length > 0 && (
              <section className="mt-8">
                <h2 className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  By rule
                </h2>
                <ul className="mt-3 space-y-4">
                  {report.skills.map((skill) => (
                    <li key={skill.skill}>
                      <div className="flex items-baseline justify-between gap-4">
                        <span className="font-medium">{skill.label}</span>
                        <span className="font-mono text-xs text-slate-500 dark:text-slate-400">
                          {skill.opportunities - skill.errors}/{skill.opportunities}
                        </span>
                      </div>
                      {/* No bar until the rate means something: a full bar
                          beside "too few attempts" says the opposite. */}
                      {skill.confident && (
                        <div className="mt-1.5">
                          <Bar
                            value={skill.accuracy ?? 0}
                            tone={(skill.accuracy ?? 0) >= 0.9 ? 'good' : 'weak'}
                          />
                        </div>
                      )}
                      <p className="mt-1.5 text-sm text-slate-600 dark:text-slate-300">
                        {skill.summary}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section className="mt-10">
              <h2 className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                By concept
              </h2>
              <ul className="mt-3 space-y-5">
                {report.concepts.map((concept) => (
                  <li key={concept.id}>
                    <div className="flex items-baseline justify-between gap-4">
                      <span className="font-medium">{concept.name}</span>
                      <span className="shrink-0 text-xs text-slate-500 dark:text-slate-400">
                        {concept.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 dark:text-slate-500">
                      {concept.unit_title}
                    </p>
                    {concept.opportunities > 0 && (
                      <div className="mt-1.5">
                        <Bar
                          value={concept.p_known}
                          tone={concept.status === 'known' ? 'good' : 'weak'}
                        />
                      </div>
                    )}
                    {/* Why it is hard, not just how far along. The point is that
                        a learner should understand the difficulty, not rate it. */}
                    <p className="mt-1.5 text-sm text-slate-600 dark:text-slate-300">
                      {concept.why_hard}
                    </p>
                  </li>
                ))}
              </ul>
            </section>

            <p className="mt-10 border-t border-slate-200 pt-4 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
              {report.note}
            </p>
          </>
        )}
      </div>
    </div>
  )
}
