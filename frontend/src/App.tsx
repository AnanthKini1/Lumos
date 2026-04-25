/**
 * WS-C — Root application component.
 *
 * Owns top-level screen routing (Setup → MindViewer → ComparisonReport)
 * and the scenario data loading state. Passes loaded SimulationOutput down
 * to child screens as props — no child fetches data directly.
 *
 * Screen flow:
 *   1. SetupScreen    — persona / topic / strategy selection
 *   2. MindViewer     — live turn-by-turn conversation + internal mind panels
 *   3. ComparisonReport — post-run verdict grid, trajectory charts, synthesis
 */

import SetupScreen from './components/setup/SetupScreen'

type Screen = 'setup' | 'mindviewer' | 'report'

export default function App() {
  const screen: Screen = 'setup'

  if (screen === 'setup') return <SetupScreen />

  return <div>TODO: App routing</div>
}
