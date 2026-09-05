import { useEffect, useRef, useState } from 'react'

// The same nine projects ForgeNav lists across the sibling React apps
// (iron, reverie, nous, vault, semaphore, cadence, timbre, cipher, rosetta),
// plus forage and prudence, which shipped after ForgeNav's own list was last
// updated there. Names, one-line descriptions and accent colours are copied
// from the root site's own project list (ayter_com/index.html) rather than
// ForgeNav's copy, since that root list is the more current of the two.
// Langram itself is deliberately absent: this is "the other projects".
type Project = { name: string; path: string; desc: string; accent: string }

const NETWORK: Project[] = [
  { name: 'Rosetta', path: '/rosetta/', accent: '#00d4ff',
    desc: 'Interactive map of 7,000+ languages' },
  { name: 'Semaphore', path: '/semaphore/', accent: '#ff6fff',
    desc: 'Real-time AI sign language interpreter' },
  { name: 'Timbre', path: '/timbre/', accent: '#facc15',
    desc: 'Acoustic phonetics lab' },
  { name: 'Cipher', path: '/cipher/', accent: '#22d3ee',
    desc: 'Instant EN ↔ TR translation' },
  { name: 'Iron', path: '/iron/', accent: '#f97316',
    desc: 'Full-stack training platform' },
  { name: 'Reverie', path: '/reverie/', accent: '#4ade80',
    desc: 'Science-backed meditation suite' },
  { name: 'Nous', path: '/nous/', accent: '#bf5af2',
    desc: 'Cognitive training battery' },
  { name: 'Forage', path: '/forage/', accent: '#84cc16',
    desc: 'AI pantry companion' },
  { name: 'Prudence', path: '/prudence/', accent: '#c6a15b',
    desc: 'Conversational budgeting guide' },
  { name: 'Vault', path: '/vault/', accent: '#39ff14',
    desc: 'Neo-retro arcade' },
  { name: 'Cadence', path: '/cadence/', accent: '#fb923c',
    desc: 'Last.fm scrobble storyteller' },
]

// Discreet on purpose: a small corner handle rather than a permanent bar, so
// it never competes with an exercise for attention. Hover opens it for a
// pointer; a click (or Enter/Space on the button, since it is a real button)
// covers touch and keyboard, and Escape or a click outside closes it either
// way.
export function NetworkNav() {
  const [open, setOpen] = useState(false)
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

  return (
    <div
      ref={rootRef}
      className="fixed bottom-4 right-4 z-50"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="true"
        aria-label="Other projects in the network"
        className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200
                   bg-white/80 text-slate-400 shadow-sm backdrop-blur transition
                   hover:text-slate-700 hover:shadow-md focus:outline-none
                   focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2
                   dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-500 dark:hover:text-slate-200"
      >
        <span aria-hidden className="text-[0.6rem] tracking-widest">&bull;&bull;&bull;</span>
      </button>

      <div
        role="menu"
        aria-hidden={!open}
        className={`absolute bottom-11 right-0 w-72 origin-bottom-right rounded-xl border
                    border-slate-200 bg-white/95 p-3 shadow-xl backdrop-blur transition
                    duration-150 dark:border-slate-700 dark:bg-slate-900/95
                    ${open ? 'scale-100 opacity-100' : 'pointer-events-none scale-95 opacity-0'}`}
      >
        <p className="px-1 pb-2 text-[0.65rem] font-semibold uppercase tracking-widest
                       text-slate-400 dark:text-slate-500">
          The Network
        </p>
        <ul className="max-h-80 space-y-0.5 overflow-y-auto">
          {NETWORK.map((p) => (
            <li key={p.name}>
              <a
                href={p.path}
                target="_blank"
                rel="noopener noreferrer"
                role="menuitem"
                tabIndex={open ? 0 : -1}
                className="flex items-start gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-100
                           dark:hover:bg-slate-800"
              >
                <span
                  aria-hidden
                  className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{ backgroundColor: p.accent }}
                />
                <span>
                  <span className="block text-sm font-medium text-slate-800 dark:text-slate-100">
                    {p.name}
                  </span>
                  <span className="block text-xs text-slate-500 dark:text-slate-400">{p.desc}</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
