// Shared button styles: kept in one place so a screen new to the loop (like
// the session summary) matches the existing ones by construction rather than
// by copying a class string that then drifts.

export const primaryButton =
  'rounded-md bg-accent px-4 py-2 font-display text-sm font-medium text-accent-ink ' +
  'hover:opacity-90 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ' +
  'focus-visible:ring-offset-2'

export const secondaryButton =
  'mt-4 rounded-md border border-grid px-4 py-2 font-display text-sm font-medium ' +
  'text-ink hover:bg-surface-2'
