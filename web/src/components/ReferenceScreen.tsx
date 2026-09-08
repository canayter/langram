import { VowelChart } from './VowelChart'

// A pull-up-anytime version of the chart shown once in Unit 1's intro. Same
// component, same data, so there is exactly one place this content can go
// stale.

export function ReferenceScreen({ onBack }: { onBack: () => void }) {
  return (
    <div className="min-h-screen bg-ground text-ink">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between">
          <button
            onClick={onBack}
            className="rounded-md font-display text-sm font-medium tracking-tight text-ink-dim
                       hover:text-ink focus:outline-none focus-visible:ring-2
                       focus-visible:ring-accent focus-visible:ring-offset-2"
          >
            langram
          </button>
          <button
            onClick={onBack}
            className="text-sm text-ink-dim hover:text-ink"
          >
            Back to practice
          </button>
        </div>

        <h1 className="font-display text-lg font-semibold text-ink">Vowels</h1>
        <VowelChart />
      </div>
    </div>
  )
}
