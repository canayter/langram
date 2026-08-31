import { SessionScreen } from './components/SessionScreen'
import { StartScreen } from './components/StartScreen'
import { useAuth } from './lib/store'

export default function App() {
  const { token, signOut } = useAuth()
  return token ? <SessionScreen onSignOut={signOut} /> : <StartScreen />
}
