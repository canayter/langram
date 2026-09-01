import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type AnswerResult, type Item } from '../lib/api'
import { Derivation } from './Derivation'
import { ItemBody } from './ItemBody'
import { WhyPanel } from './WhyPanel'

const TAG_LABELS: Record<string, string> = {
  harmony_backness: 'backness harmony',
  harmony_rounding: 'rounding harmony',
  stem_alternation: 'stem alternation',
  vowel_deletion: 'vowel deletion',
  buffer_missing: 'buffer consonant',
  form_not_processed: 'the ending was skipped',
  rejected_a_good_form: 'rejected a well formed word',
  missed_the_error: 'accepted a broken form',
  unclassified: 'form',
}

const STAGE_LABELS: Record<string, string> = {
  structured_input: 'Notice',
  guided_output: 'Build',
  free_output: 'Produce',
  review: 'Review',
}

const primaryButton =
  'rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2'

const secondaryButton =
  'mt-4 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 ' +
  'hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800'

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

  async function submit(value: string) {
    if (!item || settled) return
    setChosen(value)
    try {
      const answered = await api.answer({
        item_token: item.item_token,
        answer: value,
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
        <div className="flex shrink-0 gap-2">
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {STAGE_LABELS[item.stage] ?? item.stage}
          </span>
          {item.source === 'review' && (
            <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
              due
            </span>
          )}
        </div>
      </div>

      <p className="mt-6 text-slate-700 dark:text-slate-300">{item.prompt}</p>

      <ItemBody
        payload={item.payload}
        chosen={chosen}
        correct={result ? result.correct : null}
        settled={settled}
        onAnswer={(value) => void submit(value)}
      />

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

          {/* The trace always ends in the Turkish form. Passing result.answer
              here would print "a" or "yes" for items whose answer is a letter
              or a verdict rather than a word. */}
          {result.derivation && <Derivation steps={result.derivation} />}

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
