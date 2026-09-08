import { useAuth } from '../lib/store'
import { Logo } from './Logo'

// Guest only, on purpose: no account step to explain or get stuck on.
// Progress is tied to this browser; nothing here asks for an email.
export function StartScreen() {
  const { startAsGuest, busy, error } = useAuth()

  return (
    <div className="flex min-h-screen items-center justify-center bg-ground px-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2.5">
          <Logo size={30} />
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">langram</h1>
        </div>
        <p className="mt-3 text-sm leading-relaxed text-ink-dim">
          Turkish for English speakers. Every exercise is generated from a
          morphological grammar, so the rules are applied rather than memorised.
        </p>

        <dl className="mt-6 space-y-4 border-t border-grid pt-6">
          <div>
            <dt className="font-display text-sm font-medium text-ink">
              You&apos;ll see a rule before you&apos;re asked to use it
            </dt>
            <dd className="mt-0.5 text-sm text-ink-dim">
              Every new pattern starts with exercises where you only have to
              recognise it. Producing it yourself comes after.
            </dd>
          </div>
          <div>
            <dt className="font-display text-sm font-medium text-ink">
              Topics are mixed, not drilled one at a time
            </dt>
            <dd className="mt-0.5 text-sm text-ink-dim">
              Exercises interleave what you&apos;ve learned so far. It feels
              harder in the moment and holds up better afterward.
            </dd>
          </div>
          <div>
            <dt className="font-display text-sm font-medium text-ink">
              Review comes back on its own schedule
            </dt>
            <dd className="mt-0.5 text-sm text-ink-dim">
              Answers you get right come back at increasing intervals; ones you
              miss come back sooner. Check your progress any time.
            </dd>
          </div>
        </dl>
        <p className="mt-3 text-xs text-ink-dim opacity-75">
          The research behind each of these is in Sources, once you&apos;re in.
        </p>

        <button
          onClick={() => void startAsGuest()}
          disabled={busy}
          className="mt-8 w-full rounded-md bg-accent px-4 py-2.5 font-display text-sm
                     font-medium text-accent-ink hover:opacity-90 disabled:opacity-60"
        >
          {busy ? 'Starting' : 'Start learning'}
        </button>

        {error && <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>}
      </div>
    </div>
  )
}
