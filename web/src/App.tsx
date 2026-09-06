import { useState } from 'react'
import { NetworkNav } from './components/NetworkNav'
import { ProgressScreen } from './components/ProgressScreen'
import { ReferenceScreen } from './components/ReferenceScreen'
import { SessionScreen } from './components/SessionScreen'
import { SourcesScreen } from './components/SourcesScreen'
import { StartScreen } from './components/StartScreen'
import { UnitsScreen } from './components/UnitsScreen'
import { api } from './lib/api'
import { useAuth } from './lib/store'

// A full reload rather than resetting each piece of client state by hand:
// mastery, review cards and responses are all gone server-side after this,
// and a reload is the one guaranteed way every component (the stats store,
// SessionScreen's own block/summary state, whatever screen is open) starts
// clean from it, rather than trusting each one to notice on its own.
async function resetProgress() {
  await api.resetProgress()
  window.location.reload()
}

function Screen() {
  const { token } = useAuth()
  const [showProgress, setShowProgress] = useState(false)
  const [showReference, setShowReference] = useState(false)
  const [showUnits, setShowUnits] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const [focusConcept, setFocusConcept] = useState<string | null>(null)

  if (!token) return <StartScreen />
  if (showProgress) return <ProgressScreen onBack={() => setShowProgress(false)} />
  if (showReference) return <ReferenceScreen onBack={() => setShowReference(false)} />
  if (showSources) return <SourcesScreen onBack={() => setShowSources(false)} />
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
      onHome={() => setFocusConcept(null)}
      onShowProgress={() => setShowProgress(true)}
      onShowReference={() => setShowReference(true)}
      onShowUnits={() => setShowUnits(true)}
      onShowSources={() => setShowSources(true)}
      onResetProgress={resetProgress}
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
