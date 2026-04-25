import type { SimulationOutput } from '../../types/simulation'

interface Props {
  simulation: SimulationOutput
  initialStrategyId?: string
  onViewReport: () => void
}

export default function MindViewer({ simulation: _simulation, initialStrategyId: _initialStrategyId, onViewReport: _onViewReport }: Props) {
  return <div data-testid="mind-viewer">TODO: MindViewer</div>
}
