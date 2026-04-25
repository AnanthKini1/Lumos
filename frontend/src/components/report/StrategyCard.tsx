/**
 * WS-C — Expandable card for one strategy outcome in the comparison report.
 *
 * Collapsed state shows:
 *   - Strategy display name
 *   - Verdict badge (color-coded: GENUINE_BELIEF_SHIFT = green, BACKFIRE = red, etc.)
 *   - One-line verdict reasoning
 *
 * Expanded state adds:
 *   - 2-3 standout monologue quotes with turn number and annotation
 *   - Synthesis paragraph explaining what worked/failed and why
 *   - "Watch full transcript" button (calls onViewTranscript)
 *
 * Strategies with GENUINE_BELIEF_SHIFT should be visually celebrated;
 * BACKFIRE should be visually flagged (border accent, distinct badge color).
 *
 * Receives a single StrategyOutcome + the strategy's display name as props.
 */

import type { StrategyOutcome } from '../../types/simulation'

interface Props {
  outcome: StrategyOutcome
  strategyDisplayName: string
  onViewTranscript: (strategyId: string) => void
}

export default function StrategyCard({ outcome: _outcome, strategyDisplayName: _strategyDisplayName, onViewTranscript: _onViewTranscript }: Props) {
  return <div>TODO: StrategyCard</div>
}
