import { useId } from 'react'

// The dotless i: the single letter that gives away "this is Turkish" faster
// than anything else in the alphabet, and exactly what Unit 1 teaches (front
// vowels take one suffix shape, back vowels including i without its dot take
// another). Same mark as web/public/favicon.svg; this is the in-app version
// so it can sit inline next to the wordmark without an extra image request.
export function Logo({ size = 28 }: { size?: number }) {
  const gradientId = useId()
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      role="img"
      aria-label="Langram"
      className="shrink-0"
    >
      <defs>
        <linearGradient id={gradientId} x1="3" y1="3" x2="29" y2="29" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#f2b84b" />
          <stop offset="0.55" stopColor="#e0a72e" />
          <stop offset="1" stopColor="#6fd7c0" />
        </linearGradient>
      </defs>
      <rect x="1.6" y="1.6" width="28.8" height="28.8" rx="6" fill="#0f1d2e" stroke={`url(#${gradientId})`} strokeWidth="2.2" />
      <text
        x="16" y="23" textAnchor="middle"
        fontFamily="Newsreader, Georgia, serif" fontSize="21" fontWeight="600"
        fill={`url(#${gradientId})`}
      >
        ı
      </text>
    </svg>
  )
}
