import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type AnswerResult, type Item } from '../lib/api'
import { useStats } from '../lib/store'
import { Derivation } from './Derivation'
import { ItemBody } from './ItemBody'
import { Logo } from './Logo'
import { VowelChart } from './VowelChart'
import { WhyPanel } from './WhyPanel'
import { WordInfo } from './WordInfo'

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

function Shell({ children, onSignOut, onShowProgress, onShowReference }: {
  children: React.ReactNode
  onSignOut: () => void
  onShowProgress: () => void
  onShowReference: () => void
}) {
  const { xp, streak } = useStats()
  return (
    <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-mono text-sm tracking-tight text-slate-400">
            <Logo size={18} />
            langram
          </span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-3 text-sm font-medium text-slate-500 dark:text-slate-400">
              <span title="Day streak">🔥 {streak}</span>
              <span title="Total XP" className="text-amber-600 dark:text-amber-400">{xp} XP</span>
            </span>
            <button
              onClick={onShowReference}
              className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            >
              Reference
            </button>
            <button
              onClick={onShowProgress}
              className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            >
              Progress
            </button>
            <button
              onClick={onSignOut}
              className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            >
              Sign out
            </button>
          </div>
        </div>
        {children}
      </div>
    </div>
  )
}

export function SessionScreen({ onSignOut, onShowProgress, onShowReference }: {
  onSignOut: () => void
  onShowProgress: () => void
  onShowReference: () => void
}) {
  const [item, setItem] = useState<Item | null>(null)
  // Which numbered question this is within the current concept's block of
  // five. Purely a display concern: the cap itself is enforced server side,
  // this only tracks what to show, and resets whenever the concept changes
  // or an intro is shown, since an intro is not a numbered question.
  const [block, setBlock] = useState<{ concept: string; count: number } | null>(null)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [attempt, setAttempt] = useState(1)
  const [chosen, setChosen] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const lastConcept = useRef<string | undefined>(undefined)
  const shownAt = useRef<number>(Date.now())
  // /api/session/next is not idempotent: serving a concept's intro also
  // marks it seen server-side. React 18 StrictMode deliberately double-fires
  // a mount effect in development, and without this guard the second call
  // would land after the intro was already consumed by the first, so the
  // intro would fetch correctly and then never render. The ref persists
  // across StrictMode's synthetic remount (only state and effects reset), so
  // setting it synchronously, before the first await, blocks the second call
  // from ever reaching the network.
  const loading = useRef(false)

  const load = useCallback(async () => {
    if (loading.current) return
    loading.current = true
    setResult(null)
    setChosen(null)
    setAttempt(1)
    setError(null)
    try {
      const next = await api.next(lastConcept.current)
      setItem(next)
      useStats.getState().sync(next.xp_total, next.streak)
      shownAt.current = Date.now()
      setBlock((prev) => {
        if (next.payload.kind === 'intro') return null
        if (prev && prev.concept === next.concept_id) {
          return { concept: next.concept_id, count: Math.min(prev.count + 1, 5) }
        }
        return { concept: next.concept_id, count: 1 }
      })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      loading.current = false
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
      useStats.getState().sync(answered.xp_total, answered.streak)
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
      <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference}>
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button onClick={() => void load()} className={secondaryButton}>
          Try again
        </button>
      </Shell>
    )
  }

  if (!item) {
    return (
      <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference}>
        <p className="text-slate-500">Loading.</p>
      </Shell>
    )
  }

  // Explicit information about the concept, shown once before its first
  // exercise. Not answered, so it never touches submit() or api.answer.
  if (item.payload.kind === 'intro') {
    return (
      <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference}>
        <p className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {item.unit_title}
        </p>
        <h1 className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">
          {item.concept_name}
        </h1>
        <p className="mt-6 max-w-prose leading-relaxed text-slate-700 dark:text-slate-300">
          {item.payload.text}
        </p>
        {item.payload.visual_aid === 'vowel_chart' && <VowelChart />}
        <button onClick={() => void load()} className={`${primaryButton} mt-8`} autoFocus>
          Start practicing
        </button>
      </Shell>
    )
  }

  return (
    <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference}>
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
          {block && (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {block.count} of 5
            </span>
          )}
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

      <WordInfo key={item.item_token} info={item.word_info} />

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

          {(result.xp_awarded > 0 || result.streak_extended) && (
            <div key={item.item_token} className="mt-2 flex flex-wrap gap-2 animate-pop-in">
              {result.xp_awarded > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
                  +{result.xp_awarded} XP
                </span>
              )}
              {result.streak_extended && (
                <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-1 text-xs font-semibold text-orange-800 dark:bg-orange-900/40 dark:text-orange-200">
                  🔥 {result.streak} day streak
                </span>
              )}
            </div>
          )}

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
