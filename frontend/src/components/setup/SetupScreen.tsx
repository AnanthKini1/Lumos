import type { SimulationOutput } from '../../types/simulation'

interface Props {
  onRunSimulation: (simulation: SimulationOutput) => void
}

export default function SetupScreen({ onRunSimulation: _onRunSimulation }: Props) {
  return <div data-testid="setup-screen">TODO: SetupScreen</div>
}
