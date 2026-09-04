import { useState } from 'react'
import { ProgressScreen } from './components/ProgressScreen'
import { ReferenceScreen } from './components/ReferenceScreen'
import { SessionScreen } from './components/SessionScreen'
import { StartScreen } from './components/StartScreen'
import { useAuth } from './lib/store'

export default function App() {
  const { token, signOut } = useAuth()
  const [showProgress, setShowProgress] = useState(false)
  const [showReference, setShowReference] = useState(false)

  if (!token) return <StartScreen />
  if (showProgress) return <ProgressScreen onBack={() => setShowProgress(false)} />
  if (showReference) return <ReferenceScreen onBack={() => setShowReference(false)} />
  return (
    <SessionScreen
      onSignOut={signOut}
      onShowProgress={() => setShowProgress(true)}
      onShowReference={() => setShowReference(true)}
    />
  )
}
