import { useEffect, useState } from 'react'
import { api, type Vowel } from '../lib/api'

// Every fact here comes straight off /api/language/vowels, which reads
// content/l2/tr/morphology/phonology.yaml -- the same table the engine
// resolves archiphonemes against. Nothing about a vowel is written into this
// component; a pronunciation tip is generated from its back/rounded/high
// flags rather than a separate hand-written description, so it cannot drift
// from what the grammar actually treats as true about that vowel.

function tipFor(v: Vowel): string {
  const tongue = v.back ? 'pulled back' : 'pushed forward'
  const height = v.high ? 'raised close to the roof of the mouth' : 'held low, mouth more open'
  const lips = v.rounded ? 'rounded, like starting a whistle' : 'relaxed and spread, unrounded'
  return `Tongue ${tongue} and ${height}. Lips ${lips}.`
}

function VowelCell({ vowel }: { vowel: Vowel }) {
  return (
    <div className="rounded-md border border-grid bg-surface px-2.5 py-2">
      <span className="font-turkish text-2xl text-ink">{vowel.symbol}</span>
      <p className="mt-0.5 text-xs leading-snug text-ink-dim">{tipFor(vowel)}</p>
    </div>
  )
}

export function VowelChart() {
  const [vowels, setVowels] = useState<Vowel[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    api.vowels()
      .then((v) => { if (!cancelled) setVowels(v) })
      .catch(() => { if (!cancelled) setError(true) })
    return () => { cancelled = true }
  }, [])

  if (error) return null
  if (!vowels) return <p className="mt-4 text-sm text-ink-dim">Loading the vowel chart.</p>

  const cell = (back: boolean, rounded: boolean) =>
    vowels
      .filter((v) => v.back === back && v.rounded === rounded)
      // High before low, so the grid reads the same order left to right as
      // top to bottom: i before e, ı before a.
      .sort((a, b) => Number(b.high) - Number(a.high))

  return (
    <div className="bp-grid mt-6 rounded-md border border-grid p-4">
      <p className="text-sm leading-relaxed text-ink-dim">
        A harmony suffix copies its vowel from the last vowel of the stem: twofold
        harmony copies whether that vowel is <strong className="text-ink">front</strong> or{' '}
        <strong className="text-ink">back</strong>; fourfold harmony copies that plus whether it is{' '}
        <strong className="text-ink">rounded</strong>. Those are exactly the two axes below.
      </p>

      <div className="mt-4 grid grid-cols-[auto_1fr_1fr] gap-2 text-sm">
        <div />
        <div className="text-center font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
          Front
        </div>
        <div className="text-center font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
          Back
        </div>

        <div className="flex items-center font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
          Unrounded
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {cell(false, false).map((v) => <VowelCell key={v.symbol} vowel={v} />)}
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {cell(true, false).map((v) => <VowelCell key={v.symbol} vowel={v} />)}
        </div>

        <div className="flex items-center font-display font-semibold text-xs uppercase tracking-wider text-ink-dim">
          Rounded
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {cell(false, true).map((v) => <VowelCell key={v.symbol} vowel={v} />)}
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {cell(true, true).map((v) => <VowelCell key={v.symbol} vowel={v} />)}
        </div>
      </div>
    </div>
  )
}
