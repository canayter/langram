import { VowelChart } from './VowelChart'

// A pull-up-anytime version of the chart shown once in Unit 1's intro. Same
// component, same data, so there is exactly one place this content can go
// stale.

export function ReferenceScreen({ onBack }: { onBack: () => void }) {
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

        <h1 className="font-display text-lg font-semibold text-slate-900 dark:text-slate-50">Vowels</h1>
        <VowelChart />
      </div>
    </div>
  )
}
