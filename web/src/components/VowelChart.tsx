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
    <div className="rounded-md border border-slate-200 bg-white px-2.5 py-2 dark:border-slate-700 dark:bg-slate-900">
      <span className="font-mono text-xl text-slate-900 dark:text-slate-50">{vowel.symbol}</span>
      <p className="mt-0.5 text-xs leading-snug text-slate-500 dark:text-slate-400">{tipFor(vowel)}</p>
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
  if (!vowels) return <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">Loading the vowel chart.</p>

  const cell = (back: boolean, rounded: boolean) =>
    vowels
      .filter((v) => v.back === back && v.rounded === rounded)
      // High before low, so the grid reads the same order left to right as
      // top to bottom: i before e, ı before a.
      .sort((a, b) => Number(b.high) - Number(a.high))

  return (
    <div className="mt-6 rounded-lg border border-slate-200 p-4 dark:border-slate-700">
      <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        A harmony suffix copies its vowel from the last vowel of the stem: twofold
        harmony copies whether that vowel is <strong>front</strong> or{' '}
        <strong>back</strong>; fourfold harmony copies that plus whether it is{' '}
        <strong>rounded</strong>. Those are exactly the two axes below.
      </p>

      <div className="mt-4 grid grid-cols-[auto_1fr_1fr] gap-2 text-sm">
        <div />
        <div className="text-center text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Front
        </div>
        <div className="text-center text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Back
        </div>

        <div className="flex items-center text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Unrounded
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {cell(false, false).map((v) => <VowelCell key={v.symbol} vowel={v} />)}
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {cell(true, false).map((v) => <VowelCell key={v.symbol} vowel={v} />)}
        </div>

        <div className="flex items-center text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
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
