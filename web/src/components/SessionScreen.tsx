import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type AnswerResult, type Item } from '../lib/api'
import { Derivation } from './Derivation'
import { WhyPanel } from './WhyPanel'

const TAG_LABELS: Record<string, string> = {
  harmony_backness: 'backness harmony',
  harmony_rounding: 'rounding harmony',
  stem_alternation: 'stem alternation',
  vowel_deletion: 'vowel deletion',
  buffer_missing: 'buffer consonant',
  unclassified: 'form',
}

const primaryButton =
  'rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2'

const secondaryButton =
  'mt-4 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 ' +
  'hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800'

function optionClass(state: 'idle' | 'correct' | 'wrong', disabled: boolean) {
  const base =
    'rounded-lg border px-4 py-2.5 font-mono text-lg transition-colors ' +
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 '
  if (state === 'correct') {
    return base + 'border-emerald-500 bg-emerald-50 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-100'
  }
  if (state === 'wrong') {
    return base + 'border-red-400 bg-red-50 text-red-900 dark:bg-red-900/30 dark:text-red-100'
  }
  return base + 'border-slate-300 text-slate-800 dark:border-slate-600 dark:text-slate-100 ' +
    (disabled ? 'opacity-50 ' : 'hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 ')
}

function Shell({ children, onSignOut }: { children: React.ReactNode; onSignOut: () => void }) {
  return (
    <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between">
          <span className="font-mono text-sm tracking-tight text-slate-400">langram</span>
          <button
            onClick={onSignOut}
            className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
          >
            Sign out
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function SessionScreen({ onSignOut }: { onSignOut: () => void }) {
  const [item, setItem] = useState<Item | null>(null)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [attempt, setAttempt] = useState(1)
  const [chosen, setChosen] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const lastConcept = useRef<string | undefined>(undefined)
  const shownAt = useRef<number>(Date.now())

  const load = useCallback(async () => {
    setResult(null)
    setChosen(null)
    setAttempt(1)
    setError(null)
    try {
      const next = await api.next(lastConcept.current)
      setItem(next)
      shownAt.current = Date.now()
    } catch (e) {
      setError((e as Error).message)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  // Settled means the item is finished with: solved, or given up on after the
  // ladder has run out of prompts.
  const settled = Boolean(result?.correct || result?.kind === 'explicit')

  async function choose(option: string) {
    if (!item || settled) return
    setChosen(option)
    try {
      const answered = await api.answer({
        item_token: item.item_token,
        answer: option,
        attempt,
        latency_ms: Date.now() - shownAt.current,
      })
      setResult(answered)
      if (answered.correct || answered.kind === 'explicit') {
        lastConcept.current = item.concept_id
      } else {
        setAttempt((n) => n + 1)
      }
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (error) {
    return (
      <Shell onSignOut={onSignOut}>
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button onClick={() => void load()} className={secondaryButton}>
          Try again
        </button>
      </Shell>
    )
  }

  if (!item) {
    return (
      <Shell onSignOut={onSignOut}>
        <p className="text-slate-500">Loading.</p>
      </Shell>
    )
  }

  return (
    <Shell onSignOut={onSignOut}>
      <div className="flex items-baseline justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {item.unit_title}
          </p>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
            {item.concept_name}
          </h1>
        </div>
        {item.source === 'review' && (
          <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
            review
          </span>
        )}
      </div>

      <p className="mt-6 text-slate-700 dark:text-slate-300">{item.prompt}</p>

      <div className="mt-4 flex flex-wrap items-baseline gap-2">
        <span className="font-mono text-3xl text-slate-900 dark:text-slate-50">{item.payload.stem}</span>
        <span className="font-mono text-2xl text-slate-400">+</span>
        <span className="font-mono text-2xl text-indigo-600 dark:text-indigo-400">
          {item.payload.suffix.notation}
        </span>
        {item.payload.gloss && (
          <span className="ml-2 text-sm text-slate-500 dark:text-slate-400">
            ({item.payload.gloss}, {item.payload.suffix.glosses[0]})
          </span>
        )}
      </div>

      <div className="mt-6 flex flex-wrap gap-2" role="group" aria-label="Suffix shapes">
        {item.payload.options.map((option) => {
          const isChosen = chosen === option
          let state: 'idle' | 'correct' | 'wrong' = 'idle'
          if (isChosen && result) state = result.correct ? 'correct' : 'wrong'
          return (
            <button
              key={option}
              onClick={() => void choose(option)}
              disabled={settled}
              aria-pressed={isChosen}
              className={optionClass(state, settled)}
            >
              {item.payload.stem}
              <span className="font-semibold">{option}</span>
            </button>
          )
        })}
      </div>

      {result && (
        <div className="mt-6" aria-live="polite">
          <p
            className={
              result.correct
                ? 'font-medium text-emerald-700 dark:text-emerald-400'
                : 'font-medium text-slate-800 dark:text-slate-200'
            }
          >
            {result.message}
          </p>

          {result.elicitation && (
            <p className="mt-2 font-mono text-lg text-slate-700 dark:text-slate-300">
              {result.elicitation} = ?
            </p>
          )}

          {!result.correct && result.tags.length > 0 && (
            <p className="mt-2 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
              {result.tags.map((t) => TAG_LABELS[t] ?? t).join(', ')}
            </p>
          )}

          {result.derivation && <Derivation steps={result.derivation} result={result.answer} />}

          {settled && (
            <button onClick={() => void load()} className={`${primaryButton} mt-6`} autoFocus>
              Continue
            </button>
          )}
        </div>
      )}

      <WhyPanel unitId={item.unit_id} conceptId={item.concept_id} />
    </Shell>
  )
}
