/**
 * WS-C — Screen 3: Strategy comparison report. Top-level container.
 *
 * The screen judges spend 30-60 seconds on to decide whether to be impressed.
 * Information hierarchy (top to bottom):
 *   1. Insight Synthesis paragraph — the one-sentence punchline at the top
 *   2. Comparison grid — verdict badges + key metrics per strategy at a glance
 *   3. TrajectoryChart — public vs. private stance lines, one per strategy
 *   4. Expandable StrategyCards — drill-in quotes, synthesis, transcript link
 *
 * Receives the full SimulationOutput as a prop. Passes individual StrategyOutcome
 * records down to TrajectoryChart and StrategyCard — no direct data access in
 * child components.
 *
 * The "watch full transcript" links navigate back to MindViewer filtered to
 * that strategy.
 */

import type { SimulationOutput } from '../../types/simulation'

interface Props {
  simulation: SimulationOutput
  onViewTranscript: (strategyId: string) => void
}

export default function ComparisonReport({ simulation: _simulation, onViewTranscript: _onViewTranscript }: Props) {
  return <div>TODO: ComparisonReport</div>
}
