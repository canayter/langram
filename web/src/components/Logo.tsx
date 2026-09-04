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
          <stop offset="0" stopColor="#fb7185" />
          <stop offset="0.5" stopColor="#f43f5e" />
          <stop offset="1" stopColor="#be123c" />
        </linearGradient>
      </defs>
      <rect x="1.6" y="1.6" width="28.8" height="28.8" rx="8" fill="#1a0e12" stroke={`url(#${gradientId})`} strokeWidth="2.2" />
      <text
        x="16" y="23" textAnchor="middle"
        fontFamily="Verdana, Geneva, sans-serif" fontSize="21" fontWeight="700"
        fill={`url(#${gradientId})`}
      >
        ı
      </text>
    </svg>
  )
}
