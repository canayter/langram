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
      className="bp-grid mt-4 rounded-md border border-grid p-4"
      aria-label="How this form is built"
    >
      {start && (
        <p className="font-mono text-xs uppercase tracking-wider text-ink-dim">{start}</p>
      )}

      <ol className="mt-2 space-y-2.5">
        {rules.map((step, index) => (
          <li key={`${step.rule}-${index}`} className="flex gap-3 text-sm">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-accent font-mono text-xs text-accent">
              {index + 1}
            </span>
            <span className="text-ink-dim">
              {step.condition}
              <span className="mt-0.5 block font-turkish text-lg text-ink">{step.result}</span>
            </span>
          </li>
        ))}
      </ol>

      {answer && (
        <p className="mt-3 flex items-baseline gap-3 border-t border-dashed border-grid pt-3">
          <span className="w-5 shrink-0 text-center font-mono text-ink-dim">=</span>
          <span className="font-turkish text-xl font-semibold text-accent">
            {answer}
          </span>
        </p>
      )}
    </div>
  )
}
