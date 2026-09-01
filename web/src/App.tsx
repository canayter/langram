import { useState } from 'react'
import { ProgressScreen } from './components/ProgressScreen'
import { SessionScreen } from './components/SessionScreen'
import { StartScreen } from './components/StartScreen'
import { useAuth } from './lib/store'

export default function App() {
  const { token, signOut } = useAuth()
  const [showProgress, setShowProgress] = useState(false)

  if (!token) return <StartScreen />
  if (showProgress) return <ProgressScreen onBack={() => setShowProgress(false)} />
  return <SessionScreen onSignOut={signOut} onShowProgress={() => setShowProgress(true)} />
}
