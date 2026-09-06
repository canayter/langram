import { useState } from 'react'
import type { WordInfo as WordInfoType } from '../lib/api'
import { breakdown, canSpeak, speak } from '../lib/phoneticTerms'

// Meaning and pronunciation for the stem an item is about, shown every time,
// not just on request: a learner who has never seen bilgisayar benefits from
// knowing it means computer and how it is said whether or not they think to
// ask. The origin is longer and not always available, so it stays a click
// away rather than pushing the exercise down the page on every item.
export function WordInfo({ info }: { info: WordInfoType | null | undefined }) {
  const [showOrigin, setShowOrigin] = useState(false)
  const [showSounds, setShowSounds] = useState(false)
  if (!info) return null

  const sounds = breakdown(info.ipa)

  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1">
      <span
        className="font-mono text-sm text-slate-500 dark:text-slate-400"
        title={info.ipa_caveat}
      >
        {info.ipa}
      </span>
      {canSpeak() && (
        <button
          onClick={() => speak(info.lemma)}
          aria-label={`Hear "${info.lemma}" pronounced`}
          title="Synthesised pronunciation, not a native speaker recording"
          className="rounded-full border border-slate-300 p-1 text-slate-500 hover:border-rose-400
                     hover:text-rose-600 focus:outline-none focus-visible:ring-2
                     focus-visible:ring-rose-400 focus-visible:ring-offset-2 dark:border-slate-600
                     dark:text-slate-400 dark:hover:border-rose-400 dark:hover:text-rose-400"
        >
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true">
            <path d="M4 9v6h4l5 5V4L8 9H4z" />
            <path
              d="M16.5 8.5a5 5 0 0 1 0 7"
              fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
            />
          </svg>
        </button>
      )}
      <span className="text-sm text-slate-500 dark:text-slate-400">{info.gloss}</span>
      {sounds.length > 0 && (
        <button
          onClick={() => setShowSounds(!showSounds)}
          aria-expanded={showSounds}
          className="text-xs text-slate-400 underline underline-offset-4 hover:text-slate-700
                     dark:text-slate-500 dark:hover:text-slate-300"
        >
          {showSounds ? 'Hide sounds' : 'How to say this'}
        </button>
      )}
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
      {showSounds && (
        <ul className="mt-1 w-full space-y-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
          {sounds.map((s, i) => (
            <li key={i}>
              <span className="font-mono text-slate-700 dark:text-slate-300">[{s.symbol}]</span>
              {' '}&mdash; {s.term}
              {s.note && <span className="text-slate-400 dark:text-slate-500">, {s.note}</span>}
            </li>
          ))}
        </ul>
      )}
      {showOrigin && info.etymology && (
        <p className="mt-1 w-full text-xs leading-relaxed text-slate-500 dark:text-slate-400">
          {info.etymology}
        </p>
      )}
    </div>
  )
}
