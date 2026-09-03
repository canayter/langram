// Every call goes through here, so the token is attached in exactly one place.

export type Suffix = { id: string; notation: string; glosses: string[] }

// The payload is generator specific and discriminated by `kind`, which is what
// lets a new exercise type reach the UI without changing the envelope.
export type SuffixOption = { id: string; notation: string; gloss: string }

export type Payload =
  | { kind: 'choose_form'; options: string[]; stem?: string; gloss?: string
      suffix?: Suffix; option_prefix?: string; modality?: string }
  | { kind: 'choose_meaning'; form: string; gloss: string; options: string[] }
  | { kind: 'choose_letter'; form: string; stem: string; gloss: string; options: string[] }
  | { kind: 'judge'; form: string; gloss: string; suffix: Suffix; options: string[] }
  | { kind: 'choose_suffix'; stem: string; gloss: string; meaning: string
      options: SuffixOption[] }
  | { kind: 'type'; cue: string; stem: string; gloss: string; suffix: Suffix }
  | { kind: 'intro'; title: string; text: string }

export type WordInfo = {
  lemma: string
  gloss: string
  ipa: string
  ipa_caveat: string
  etymology: string | null
}

export type Item = {
  item_token: string
  exercise_id: string
  concept_id: string
  concept_name: string
  unit_id: string
  unit_title: string
  stage: string
  generator: string
  prompt: string
  source: 'new' | 'review' | 'intro'
  payload: Payload
  word_info: WordInfo | null
}

export type DerivationStep = { rule: string; condition: string; result: string; form: string }

export type AnswerResult = {
  correct: boolean
  kind: 'correct' | 'clarification' | 'metalinguistic' | 'elicitation' | 'explicit'
  message: string
  tags: string[]
  elicitation?: string | null
  answer?: string | null
  derivation?: DerivationStep[] | null
  mastery?: number | null
  due_at?: string | null
}

export type Concept = {
  id: string; name: string; type: string; why_hard: string; teaches_suffixes: string[]
}
export type Unit = {
  id: string; order: number; title: string; rationale: string
  research_refs: string[]; prerequisites: string[]; concepts: Concept[]
}

export type SkillReport = {
  skill: string; label: string; opportunities: number; errors: number
  accuracy: number | null; summary: string; confident: boolean
}

export type ConceptProgress = {
  id: string; name: string; unit_id: string; unit_title: string; why_hard: string
  p_known: number; opportunities: number; correct: number; status: string
}

export type Progress = {
  answered: number; correct: number; accuracy: number | null; headline: string
  skills: SkillReport[]; concepts: ConceptProgress[]; note: string
}

export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message)
  }
}

let token: string | null = localStorage.getItem('langram.token')

export function setToken(value: string | null) {
  token = value
  if (value) localStorage.setItem('langram.token', value)
  else localStorage.removeItem('langram.token')
}

export function getToken() {
  return token
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    let detail = response.statusText
    try {
      detail = (await response.json()).detail ?? detail
    } catch { /* a non-JSON error body is still an error */ }
    throw new ApiError(response.status, detail)
  }
  return response.status === 204 ? (undefined as T) : await response.json()
}

export const api = {
  guest: () => call<{ access_token: string; user_id: number; is_guest: boolean }>(
    '/api/auth/guest', { method: 'POST' }),
  login: (email: string, password: string) =>
    call<{ access_token: string; user_id: number; is_guest: boolean }>(
      '/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string) =>
    call<{ access_token: string; user_id: number; is_guest: boolean }>(
      '/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),
  next: (after?: string) =>
    call<Item>(`/api/session/next${after ? `?after=${encodeURIComponent(after)}` : ''}`),
  answer: (body: { item_token: string; answer: string; attempt: number; latency_ms?: number }) =>
    call<AnswerResult>('/api/session/answer', { method: 'POST', body: JSON.stringify(body) }),
  units: () => call<Unit[]>('/api/units'),
  progress: () => call<Progress>('/api/progress'),
}
