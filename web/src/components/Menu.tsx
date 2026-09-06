import { useEffect, useRef, useState } from 'react'

// A single disclosed menu rather than four competing text links in the
// header: once navigation passes about four items, grouping them behind one
// clearly-labelled trigger is the standard recommendation (Nielsen Norman
// Group's guidance on navigation menus; Baymard Institute's e-commerce
// usability research finds the same for account/utility menus specifically)
// over spreading them flat, which forces a reader to scan and choose among
// several equally-weighted options every time. The destructive item (reset)
// is separated by a rule and coloured differently, per the same
// recognition-over-recall and error-prevention reasoning: it should never
// be mistaken for an ordinary navigation choice or clicked by momentum.

type MenuItemProps = { onClick: () => void; danger?: boolean; children: React.ReactNode }

function MenuItem({ onClick, danger, children }: MenuItemProps) {
  return (
    <button
      role="menuitem"
      onClick={onClick}
      className={`block w-full rounded-lg px-3 py-2 text-left text-sm font-medium
                  hover:bg-slate-100 focus:outline-none focus-visible:ring-2
                  focus-visible:ring-rose-400 focus-visible:ring-inset dark:hover:bg-slate-800
                  ${danger
                    ? 'text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40'
                    : 'text-slate-700 dark:text-slate-200'}`}
    >
      {children}
    </button>
  )
}

function ConfirmResetDialog({ busy, onCancel, onConfirm }: {
  busy: boolean; onCancel: () => void; onConfirm: () => void
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !busy) onCancel()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [busy, onCancel])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-6">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="reset-progress-title"
        className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl dark:bg-slate-900"
      >
        <h2
          id="reset-progress-title"
          className="font-display text-base font-semibold text-slate-900 dark:text-slate-50"
        >
          Reset all progress?
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          Every answer, review and mastery estimate is gone, along with your marks and day
          chain. There is no account to recover this from &mdash; this cannot be undone.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            disabled={busy}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium
                       text-slate-700 hover:bg-slate-50 disabled:opacity-50
                       dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            autoFocus
            className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white
                       hover:bg-red-500 disabled:opacity-50"
          >
            {busy ? 'Resetting' : 'Reset progress'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Menu({ onShowUnits, onShowProgress, onShowReference, onShowSources,
                       onResetProgress }: {
  onShowUnits: () => void
  onShowProgress: () => void
  onShowReference: () => void
  onShowSources: () => void
  onResetProgress: () => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [resetting, setResetting] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    function onPointerDown(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointerDown)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointerDown)
    }
  }, [open])

  function pick(action: () => void) {
    setOpen(false)
    action()
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Menu"
        className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500
                   hover:bg-slate-100 hover:text-slate-800 focus:outline-none
                   focus-visible:ring-2 focus-visible:ring-rose-400 focus-visible:ring-offset-2
                   dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <line x1="4" y1="7" x2="20" y2="7" />
          <line x1="4" y1="12" x2="20" y2="12" />
          <line x1="4" y1="17" x2="20" y2="17" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Langram"
          className="absolute right-0 top-10 z-40 w-52 rounded-xl border border-slate-200
                     bg-white p-1.5 shadow-lg dark:border-slate-700 dark:bg-slate-900"
        >
          <MenuItem onClick={() => pick(onShowUnits)}>Units</MenuItem>
          <MenuItem onClick={() => pick(onShowProgress)}>Progress</MenuItem>
          <MenuItem onClick={() => pick(onShowReference)}>Reference</MenuItem>
          <MenuItem onClick={() => pick(onShowSources)}>Sources</MenuItem>
          <div className="my-1.5 border-t border-slate-200 dark:border-slate-800" />
          <MenuItem danger onClick={() => { setOpen(false); setConfirming(true) }}>
            Reset progress
          </MenuItem>
        </div>
      )}

      {confirming && (
        <ConfirmResetDialog
          busy={resetting}
          onCancel={() => setConfirming(false)}
          onConfirm={async () => {
            setResetting(true)
            try {
              await onResetProgress()
            } finally {
              setResetting(false)
              setConfirming(false)
            }
          }}
        />
      )}
    </div>
  )
}
