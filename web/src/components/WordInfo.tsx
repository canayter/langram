import { useState } from 'react'
import type { WordInfo as WordInfoType } from '../lib/api'

// Meaning and pronunciation for the stem an item is about, shown every time,
// not just on request: a learner who has never seen bilgisayar benefits from
// knowing it means computer and how it is said whether or not they think to
// ask. The origin is longer and not always available, so it stays a click
// away rather than pushing the exercise down the page on every item.
export function WordInfo({ info }: { info: WordInfoType | null | undefined }) {
  const [showOrigin, setShowOrigin] = useState(false)
  if (!info) return null

  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1">
      <span
        className="font-mono text-sm text-slate-500 dark:text-slate-400"
        title={info.ipa_caveat}
      >
        {info.ipa}
      </span>
      <span className="text-sm text-slate-500 dark:text-slate-400">{info.gloss}</span>
      {info.etymology && (
        <button
          onClick={() => setShowOrigin(!showOrigin)}
          aria-expanded={showOrigin}
          className="text-xs text-slate-400 underline underline-offset-4 hover:text-slate-700
                     dark:text-slate-500 dark:hover:text-slate-300"
        >
          {showOrigin ? 'Hide word origin' : 'Word origin'}
        </button>
      )}
      {showOrigin && info.etymology && (
        <p className="mt-1 w-full text-xs leading-relaxed text-slate-500 dark:text-slate-400">
          {info.etymology}
        </p>
      )}
    </div>
  )
}
