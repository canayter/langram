import { create } from 'zustand'
import { api, getToken, setToken } from './api'

type AuthState = {
  token: string | null
  isGuest: boolean
  busy: boolean
  error: string | null
  startAsGuest: () => Promise<void>
  signIn: (email: string, password: string, register: boolean) => Promise<void>
  signOut: () => void
}

export const useAuth = create<AuthState>((set) => ({
  token: getToken(),
  isGuest: false,
  busy: false,
  error: null,

  startAsGuest: async () => {
    set({ busy: true, error: null })
    try {
      const result = await api.guest()
      setToken(result.access_token)
      set({ token: result.access_token, isGuest: true, busy: false })
    } catch (error) {
      set({ busy: false, error: (error as Error).message })
    }
  },

  signIn: async (email, password, register) => {
    set({ busy: true, error: null })
    try {
      const result = register ? await api.register(email, password) : await api.login(email, password)
      setToken(result.access_token)
      set({ token: result.access_token, isGuest: result.is_guest, busy: false })
    } catch (error) {
      set({ busy: false, error: (error as Error).message })
    }
  },

  signOut: () => {
    setToken(null)
    set({ token: null, isGuest: false })
  },
}))

// XP and streak: read from whatever the server last reported (session/next
// and session/answer both carry the running totals), never computed here.
// Kept as its own store, not folded into useAuth, since Shell reads it
// without needing to know anything else about identity.
type StatsState = {
  xp: number
  streak: number
  sync: (xp: number, streak: number) => void
}

export const useStats = create<StatsState>((set) => ({
  xp: 0,
  streak: 0,
  sync: (xp, streak) => set({ xp, streak }),
}))
