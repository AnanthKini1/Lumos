import type { SimulationOutput } from '../../types/simulation'

interface Props {
  simulation: SimulationOutput
  onViewTranscript: (strategyId: string) => void
  onBackToSetup: () => void
}

export default function ComparisonReport({ simulation: _simulation, onViewTranscript: _onViewTranscript, onBackToSetup: _onBackToSetup }: Props) {
  return <div data-testid="comparison-report">TODO: ComparisonReport</div>
}
