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
  'rounded-lg border px-4 py-2.5 font-mono text-lg transition-colors ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 '

function optionClass(state: 'idle' | 'correct' | 'wrong', disabled: boolean) {
  if (state === 'correct') {
    return optionBase +
      'border-emerald-500 bg-emerald-50 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-100'
  }
  if (state === 'wrong') {
    return optionBase + 'border-red-400 bg-red-50 text-red-900 dark:bg-red-900/30 dark:text-red-100'
  }
  return optionBase + 'border-slate-300 text-slate-800 dark:border-slate-600 dark:text-slate-100 ' +
    (disabled ? 'opacity-50 ' : 'hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 ')
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

function StemAndSuffix({ stem, suffix, gloss }: { stem: string; suffix?: Suffix; gloss?: string }) {
  return (
    <div className="mt-4 flex flex-wrap items-baseline gap-2">
      <span className="font-mono text-3xl text-slate-900 dark:text-slate-50">{stem}</span>
      {suffix && (
        <>
          <span className="font-mono text-2xl text-slate-400">+</span>
          <span className="font-mono text-2xl text-indigo-600 dark:text-indigo-400">
            {suffix.notation}
          </span>
        </>
      )}
      {gloss && (
        <span className="ml-2 text-sm text-slate-500 dark:text-slate-400">
          {gloss}{suffix?.glosses?.[0] ? `, ${suffix.glosses[0]}` : ''}
        </span>
      )}
    </div>
  )
}

function BigForm({ form, gloss }: { form: string; gloss?: string }) {
  return (
    <div className="mt-4 flex flex-wrap items-baseline gap-3">
      <span className="font-mono text-3xl text-slate-900 dark:text-slate-50">{form}</span>
      {gloss && <span className="text-sm text-slate-500 dark:text-slate-400">{gloss}</span>}
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
        className="rounded-lg border border-slate-300 px-3 py-2 font-mono text-lg text-slate-900 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
      />
      <button
        type="submit"
        disabled={settled || !value.trim()}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
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
            labels={(value) =>
              payload.option_prefix ? (
                <>
                  {payload.option_prefix}
                  <span className="font-semibold">{value}</span>
                </>
              ) : value
            }
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
            <span className="font-mono text-3xl text-slate-900 dark:text-slate-50">
              {payload.stem}
            </span>
            <span className="font-mono text-3xl text-slate-300 dark:text-slate-600">___</span>
            <span className="ml-2 text-sm text-slate-500 dark:text-slate-400">
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
                  <span className="font-sans text-xs text-slate-500 dark:text-slate-400">
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
          <p className="mt-4 text-xl text-slate-900 dark:text-slate-50">{payload.cue}</p>
          <TypeAnswer cue={payload.cue} settled={settled} onAnswer={onAnswer} />
        </>
      )
  }
}
