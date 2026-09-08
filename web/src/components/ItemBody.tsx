import { useEffect, useRef, useState } from 'react'
import type { Payload, Suffix } from '../lib/api'

// One component per payload kind. The envelope around them does not change, so
// a new exercise type is a new branch here and nothing else in the UI.

type Props = {
  payload: Payload
  chosen: string | null
  correct: boolean | null
  settled: boolean
  onAnswer: (value: string) => void
}

const optionBase =
  'rounded-md border px-4 py-2.5 font-mono text-lg transition-colors ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 '

function optionClass(state: 'idle' | 'correct' | 'wrong', disabled: boolean) {
  if (state === 'correct') {
    return optionBase +
      'border-emerald-500 bg-emerald-50 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-100'
  }
  if (state === 'wrong') {
    return optionBase + 'border-red-400 bg-red-50 text-red-900 dark:bg-red-900/30 dark:text-red-100'
  }
  return optionBase + 'border-grid text-ink ' +
    (disabled ? 'opacity-50 ' : 'hover:border-accent hover:bg-surface-2 ')
}

function Options({ values, labels, chosen, correct, settled, onAnswer, label }: {
  values: string[]
  labels?: (value: string) => React.ReactNode
  chosen: string | null
  correct: boolean | null
  settled: boolean
  onAnswer: (value: string) => void
  label: string
}) {
  return (
    <div className="mt-6 flex flex-wrap gap-2" role="group" aria-label={label}>
      {values.map((value) => {
        const isChosen = chosen === value
        let state: 'idle' | 'correct' | 'wrong' = 'idle'
        if (isChosen && correct !== null) state = correct ? 'correct' : 'wrong'
        return (
          <button
            key={value}
            onClick={() => onAnswer(value)}
            disabled={settled}
            aria-pressed={isChosen}
            className={optionClass(state, settled)}
          >
            {labels ? labels(value) : value}
          </button>
        )
      })}
    </div>
  )
}

// The stem is set in font-turkish: this is the form an exercise is actually
// about, and giving it its own typographic voice (a serif among an
// otherwise all-grotesk-and-mono interface) is what makes it the one thing
// on screen that reads as language rather than chrome. The suffix notation
// stays in font-mono deliberately -- it is the rule, not the word, the
// same distinction the derivation trace draws between a form and a step.
function StemAndSuffix({ stem, suffix, gloss }: { stem: string; suffix?: Suffix; gloss?: string }) {
  return (
    <div className="mt-4 flex flex-wrap items-baseline gap-2">
      <span className="font-turkish text-4xl text-ink">{stem}</span>
      {suffix && (
        <>
          <span className="font-mono text-2xl text-ink-dim">+</span>
          <span className="font-mono text-2xl text-accent">
            {suffix.notation}
          </span>
        </>
      )}
      {gloss && (
        <span className="ml-2 text-sm text-ink-dim">
          {gloss}{suffix?.glosses?.[0] ? `, ${suffix.glosses[0]}` : ''}
        </span>
      )}
    </div>
  )
}

function BigForm({ form, gloss }: { form: string; gloss?: string }) {
  return (
    <div className="mt-4 flex flex-wrap items-baseline gap-3">
      <span className="font-turkish text-4xl text-ink">{form}</span>
      {gloss && <span className="text-sm text-ink-dim">{gloss}</span>}
    </div>
  )
}

function TypeAnswer({ cue, settled, onAnswer }: {
  cue: string; settled: boolean; onAnswer: (value: string) => void
}) {
  const [value, setValue] = useState('')
  const input = useRef<HTMLInputElement>(null)
  useEffect(() => { input.current?.focus() }, [])

  return (
    <form
      className="mt-6 flex flex-wrap items-center gap-2"
      onSubmit={(e) => {
        e.preventDefault()
        if (value.trim()) onAnswer(value.trim())
      }}
    >
      <label className="sr-only" htmlFor="answer">Your answer</label>
      <input
        id="answer"
        ref={input}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={settled}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        aria-label={`Turkish for ${cue}`}
        className="rounded-md border border-grid bg-surface px-3 py-2 font-turkish text-lg text-ink disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={settled || !value.trim()}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-ink hover:opacity-90 disabled:opacity-50"
      >
        Check
      </button>
    </form>
  )
}

export function ItemBody({ payload, chosen, correct, settled, onAnswer }: Props) {
  const shared = { chosen, correct, settled, onAnswer }

  switch (payload.kind) {
    case 'choose_form':
      return (
        <>
          {payload.stem && (
            <StemAndSuffix stem={payload.stem} suffix={payload.suffix} gloss={payload.gloss} />
          )}
          <Options
            {...shared}
            label="Possible forms"
            values={payload.options}
            labels={(value) => {
              const info = payload.word_info?.[value]
              const form = payload.option_prefix ? (
                <span className="font-turkish">
                  {payload.option_prefix}
                  <span className="font-semibold">{value}</span>
                </span>
              ) : <span className="font-turkish">{value}</span>
              if (!info) return form
              return (
                <span className="flex flex-col items-start">
                  {form}
                  <span className="mt-0.5 flex gap-1.5 font-sans text-xs font-normal text-ink-dim">
                    <span title={payload.word_info_caveat}>{info.ipa}</span>
                    <span>{info.gloss}</span>
                  </span>
                </span>
              )
            }}
          />
        </>
      )

    case 'choose_meaning':
      return (
        <>
          <BigForm form={payload.form} />
          <Options {...shared} label="Meanings" values={payload.options} />
        </>
      )

    case 'choose_letter':
      return (
        <>
          <BigForm form={payload.form} gloss={payload.gloss} />
          <Options {...shared} label="Vowels" values={payload.options} />
        </>
      )

    case 'judge':
      return (
        <>
          <BigForm form={payload.form} gloss={payload.gloss} />
          <Options
            {...shared}
            label="Your judgement"
            values={payload.options}
            labels={(value) => (value === 'yes' ? 'Possible' : 'Not possible')}
          />
        </>
      )

    case 'choose_suffix':
      return (
        <>
          <div className="mt-4 flex flex-wrap items-baseline gap-2">
            <span className="font-turkish text-4xl text-ink">
              {payload.stem}
            </span>
            <span className="font-mono text-3xl text-ink-dim opacity-50">___</span>
            <span className="ml-2 text-sm text-ink-dim">
              {payload.gloss}, {payload.meaning}
            </span>
          </div>
          <Options
            {...shared}
            label="Suffixes"
            values={payload.options.map((o) => o.id)}
            labels={(value) => {
              const option = payload.options.find((o) => o.id === value)
              return (
                <span className="flex flex-col items-start">
                  <span>{option?.notation}</span>
                  <span className="font-sans text-xs text-ink-dim">
                    {option?.gloss}
                  </span>
                </span>
              )
            }}
          />
        </>
      )

    case 'type':
      return (
        <>
          <p className="mt-4 text-xl text-ink">{payload.cue}</p>
          <TypeAnswer cue={payload.cue} settled={settled} onAnswer={onAnswer} />
        </>
      )
  }
}
