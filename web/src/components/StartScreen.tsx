import { useState } from 'react'
import { useAuth } from '../lib/store'

// Guest first. Asking for an email before someone has seen a single exercise
// loses them, and the account can be claimed later without losing history.
export function StartScreen() {
  const { startAsGuest, signIn, busy, error } = useAuth()
  const [showForm, setShowForm] = useState(false)
  const [register, setRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  return (
    <div className="flex min-h-screen items-center justify-center bg-white px-6 dark:bg-slate-950">
      <div className="w-full max-w-sm">
        <h1 className="font-mono text-2xl tracking-tight text-slate-900 dark:text-slate-50">langram</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          Turkish for English speakers. Every exercise is generated from a
          morphological grammar, so the rules are applied rather than memorised.
        </p>

        <dl className="mt-6 space-y-3 border-t border-slate-200 pt-6 dark:border-slate-800">
          <div>
            <dt className="text-sm font-medium text-slate-900 dark:text-slate-100">
              You&apos;ll see a rule before you&apos;re asked to use it
            </dt>
            <dd className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
              Every new pattern starts with exercises where you only have to
              recognise it. Producing it yourself comes after.
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-900 dark:text-slate-100">
              Topics are mixed, not drilled one at a time
            </dt>
            <dd className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
              Exercises interleave what you&apos;ve learned so far. It feels
              harder in the moment and holds up better afterward.
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-900 dark:text-slate-100">
              Review comes back on its own schedule
            </dt>
            <dd className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
              Answers you get right come back at increasing intervals; ones you
              miss come back sooner. Check your progress any time.
            </dd>
          </div>
        </dl>

        {!showForm ? (
          <div className="mt-8 space-y-3">
            <button
              onClick={() => void startAsGuest()}
              disabled={busy}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
            >
              {busy ? 'Starting' : 'Start learning'}
            </button>
            <button
              onClick={() => setShowForm(true)}
              className="w-full text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            >
              I already have an account
            </button>
          </div>
        ) : (
          <form
            className="mt-8 space-y-3"
            onSubmit={(e) => {
              e.preventDefault()
              void signIn(email, password, register)
            }}
          >
            <label className="block text-sm text-slate-600 dark:text-slate-300">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              />
            </label>
            <label className="block text-sm text-slate-600 dark:text-slate-300">
              Password
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={register ? 'new-password' : 'current-password'}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              />
            </label>
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
            >
              {register ? 'Create account' : 'Sign in'}
            </button>
            <button
              type="button"
              onClick={() => setRegister(!register)}
              className="w-full text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            >
              {register ? 'I already have an account' : 'Create an account instead'}
            </button>
          </form>
        )}

        {error && <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>}
      </div>
    </div>
  )
}
