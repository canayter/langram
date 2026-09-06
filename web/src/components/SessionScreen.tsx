import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type AnswerResult, type Item } from '../lib/api'
import { TAG_LABELS } from '../lib/labels'
import { useStats } from '../lib/store'
import { primaryButton, secondaryButton } from '../lib/ui'
import { Derivation } from './Derivation'
import { ItemBody } from './ItemBody'
import { Logo } from './Logo'
import { SessionSummary, type SessionStats } from './SessionSummary'
import { VowelChart } from './VowelChart'
import { WhyPanel } from './WhyPanel'
import { WordInfo } from './WordInfo'

const STAGE_LABELS: Record<string, string> = {
  structured_input: 'Notice',
  guided_output: 'Build',
  free_output: 'Produce',
  review: 'Review',
}

// How many exercises make up one block before the summary interrupts the
// loop. Not a server-side concept: /api/session/next has no notion of a
// bounded session, it always has another item, so where a block ends is
// entirely a client-side pacing decision.
const SESSION_LENGTH = 10

function FocusBanner({ conceptName, onExit }: { conceptName: string; onExit: () => void }) {
  return (
    <div className="mb-6 flex items-center justify-between gap-4 rounded-lg border
                     border-indigo-200 bg-indigo-50 px-3 py-2 text-sm dark:border-indigo-900
                     dark:bg-indigo-950/40">
      <span className="text-indigo-900 dark:text-indigo-200">
        Practicing <span className="font-medium">{conceptName}</span> on purpose &mdash;
        skipping the usual order.
      </span>
      <button
        onClick={onExit}
        className="shrink-0 font-medium text-indigo-700 hover:text-indigo-900
                   dark:text-indigo-300 dark:hover:text-indigo-100"
      >
        Back to normal practice
      </button>
    </div>
  )
}

const EMPTY_STATS: SessionStats = {
  answered: 0,
  correct: 0,
  marks: 0,
  concepts: new Map(),
  mistakes: {},
}

function Shell({ children, onSignOut, onShowProgress, onShowReference, onShowUnits }: {
  children: React.ReactNode
  onSignOut: () => void
  onShowProgress: () => void
  onShowReference: () => void
  onShowUnits: () => void
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
              <span title="Day chain: consecutive days practiced">⛓️ {streak}</span>
              <span title="Marks earned for correct answers" className="text-amber-600 dark:text-amber-400">{xp} Marks</span>
            </span>
            <button
              onClick={onShowUnits}
              className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            >
              Units
            </button>
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

export function SessionScreen({ onSignOut, onShowProgress, onShowReference, onShowUnits,
                                focusConcept, onExitFocus }: {
  onSignOut: () => void
  onShowProgress: () => void
  onShowReference: () => void
  onShowUnits: () => void
  focusConcept: string | null
  onExitFocus: () => void
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
  const [stats, setStats] = useState<SessionStats>(EMPTY_STATS)
  const [showSummary, setShowSummary] = useState(false)
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
      const next = await api.next(lastConcept.current, focusConcept ?? undefined)
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
  }, [focusConcept])

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
      // Every wrong attempt is its own mistake worth tallying, whether or
      // not the item is eventually solved through the ladder.
      if (!answered.correct && answered.tags.length > 0) {
        setStats((s) => {
          const mistakes = { ...s.mistakes }
          for (const tag of answered.tags) mistakes[tag] = (mistakes[tag] ?? 0) + 1
          return { ...s, mistakes }
        })
      }
      if (answered.correct || answered.kind === 'explicit') {
        lastConcept.current = item.concept_id
        setStats((s) => {
          const concepts = new Map(s.concepts)
          concepts.set(item.concept_id, item.concept_name)
          return {
            ...s,
            answered: s.answered + 1,
            correct: s.correct + (answered.correct ? 1 : 0),
            marks: s.marks + answered.xp_awarded,
            concepts,
          }
        })
      } else {
        setAttempt((n) => n + 1)
      }
    } catch (e) {
      setError((e as Error).message)
    }
  }

  function continueOrSummarize() {
    if (stats.answered >= SESSION_LENGTH) {
      setShowSummary(true)
    } else {
      void load()
    }
  }

  function keepPracticing() {
    setStats(EMPTY_STATS)
    setShowSummary(false)
    void load()
  }

  if (error) {
    return (
      <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference} onShowUnits={onShowUnits}>
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button onClick={() => void load()} className={secondaryButton}>
          Try again
        </button>
      </Shell>
    )
  }

  if (!item) {
    return (
      <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference} onShowUnits={onShowUnits}>
        <p className="text-slate-500">Loading.</p>
      </Shell>
    )
  }

  if (showSummary) {
    return (
      <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference} onShowUnits={onShowUnits}>
        <SessionSummary stats={stats} onContinue={keepPracticing} />
      </Shell>
    )
  }

  // Explicit information about the concept, shown once before its first
  // exercise. Not answered, so it never touches submit() or api.answer.
  if (item.payload.kind === 'intro') {
    return (
      <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference} onShowUnits={onShowUnits}>
        {focusConcept && <FocusBanner conceptName={item.concept_name} onExit={onExitFocus} />}
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
    <Shell onSignOut={onSignOut} onShowProgress={onShowProgress} onShowReference={onShowReference} onShowUnits={onShowUnits}>
      {focusConcept && <FocusBanner conceptName={item.concept_name} onExit={onExitFocus} />}
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
                  +{result.xp_awarded} Marks
                </span>
              )}
              {result.streak_extended && (
                <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-1 text-xs font-semibold text-orange-800 dark:bg-orange-900/40 dark:text-orange-200">
                  ⛓️ {result.streak} day chain
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
            <button onClick={continueOrSummarize} className={`${primaryButton} mt-6`} autoFocus>
              Continue
            </button>
          )}
        </div>
      )}

      <WhyPanel unitId={item.unit_id} conceptId={item.concept_id} />
    </Shell>
  )
}
