// Shared button styles: kept in one place so a screen new to the loop (like
// the session summary) matches the existing ones by construction rather than
// by copying a class string that then drifts.

export const primaryButton =
  'rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2'

export const secondaryButton =
  'mt-4 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 ' +
  'hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800'
