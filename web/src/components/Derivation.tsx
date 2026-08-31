import type { DerivationStep } from '../lib/api'

// The derivation trace is a product feature, not a debugging aid. A learner who
// watches the rule fire is learning the rule; one who is handed the answer is
// memorising a word.
//
// Two of the engine's steps are bookkeeping rather than teaching. `stem` just
// restates the citation form, and `attach` says the suffix was attached, which
// the learner can see. They frame the list instead of being numbered in it.
// Intermediate forms are deliberately not shown either: a half-built string like
// "boyunla" looks like a word and is not one.
export function Derivation({ steps, result }: { steps: DerivationStep[]; result?: string | null }) {
  if (!steps.length) return null

  const start = steps.find((s) => s.rule === 'stem')?.form
  const rules = steps.filter((s) => s.rule !== 'stem' && s.rule !== 'attach')
  const answer = result ?? steps[steps.length - 1]?.form

  return (
    <div
      className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/40"
      aria-label="How this form is built"
    >
      {start && (
        <p className="font-mono text-sm text-slate-500 dark:text-slate-400">{start}</p>
      )}

      <ol className="mt-2 space-y-2.5">
        {rules.map((step, index) => (
          <li key={`${step.rule}-${index}`} className="flex gap-3 text-sm">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-200 font-mono text-xs text-slate-600 dark:bg-slate-700 dark:text-slate-300">
              {index + 1}
            </span>
            <span className="text-slate-600 dark:text-slate-300">
              {step.condition}
              <span className="mt-0.5 block text-slate-900 dark:text-slate-100">{step.result}</span>
            </span>
          </li>
        ))}
      </ol>

      {answer && (
        <p className="mt-3 flex gap-3 border-t border-slate-200 pt-3 dark:border-slate-700">
          <span className="w-5 shrink-0 text-center font-mono text-slate-400">=</span>
          <span className="font-mono text-base font-semibold text-slate-900 dark:text-slate-50">
            {answer}
          </span>
        </p>
      )}
    </div>
  )
}
