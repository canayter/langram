import { useState } from 'react'
import { NetworkNav } from './components/NetworkNav'
import { ProgressScreen } from './components/ProgressScreen'
import { ReferenceScreen } from './components/ReferenceScreen'
import { SessionScreen } from './components/SessionScreen'
import { StartScreen } from './components/StartScreen'
import { UnitsScreen } from './components/UnitsScreen'
import { useAuth } from './lib/store'

function Screen() {
  const { token, signOut } = useAuth()
  const [showProgress, setShowProgress] = useState(false)
  const [showReference, setShowReference] = useState(false)
  const [showUnits, setShowUnits] = useState(false)
  const [focusConcept, setFocusConcept] = useState<string | null>(null)

  if (!token) return <StartScreen />
  if (showProgress) return <ProgressScreen onBack={() => setShowProgress(false)} />
  if (showReference) return <ReferenceScreen onBack={() => setShowReference(false)} />
  if (showUnits) {
    return (
      <UnitsScreen
        onBack={() => setShowUnits(false)}
        onSelectConcept={(conceptId) => {
          setFocusConcept(conceptId)
          setShowUnits(false)
        }}
      />
    )
  }
  return (
    <SessionScreen
      onSignOut={signOut}
      onShowProgress={() => setShowProgress(true)}
      onShowReference={() => setShowReference(true)}
      onShowUnits={() => setShowUnits(true)}
      focusConcept={focusConcept}
      onExitFocus={() => setFocusConcept(null)}
    />
  )
}

export default function App() {
  return (
    <>
      <Screen />
      <NetworkNav />
    </>
  )
}
