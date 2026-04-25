/**
 * WS-C — Recharts line chart showing public vs. private stance trajectory.
 *
 * One chart instance per strategy outcome (rendered in a small-multiples grid
 * or behind a strategy switcher in ComparisonReport).
 *
 * Chart spec:
 *   X-axis: turn number 1–N, plus a final "cooling-off" point
 *   Y-axis: stance 0–10
 *   Solid line: public stance per turn
 *   Dashed line: private stance per turn
 *   Shaded area between lines: the public-private gap (the key visual)
 *
 * A widening gap = surface compliance failure mode.
 * Converging lines = genuine belief shift.
 * Lines diverging opposite to intent = backfire.
 *
 * This chart should be the hero image on the Devpost submission.
 *
 * Receives a single StrategyOutcome as prop. Pure display — no state.
 */

import type { StrategyOutcome } from '../../types/simulation'

interface Props {
  outcome: StrategyOutcome
}

export default function TrajectoryChart({ outcome: _outcome }: Props) {
  return <div>TODO: TrajectoryChart</div>
}
