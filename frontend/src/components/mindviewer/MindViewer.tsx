/**
 * WS-C — Screen 2: The hero split-screen mind viewer. Top-level container.
 *
 * Layout: strategy-switcher tabs at the top (one tab per strategy, ~7 total),
 * with a single full-width conversation panel below showing the selected strategy.
 * Each strategy panel has two stacked sections:
 *   - PublicConversation (top): the visible transcript
 *   - InternalMind (bottom): monologue, emotion, identity threat, stance
 *
 * State owned here:
 *   - activeStrategyIndex: which strategy tab is selected
 *   - currentTurn: turn being shown (shared across all strategies for sync'd playback,
 *     or per-strategy if the user wants to compare specific turns)
 *   - isPlaying: auto-advance on/off
 *
 * Coordinates the "streaming illusion" — even when loading from cache,
 * turns are revealed one at a time to convey live thinking. The user can
 * pause on any turn of any strategy and read the internal mind panel carefully.
 *
 * Receives the full SimulationOutput as a prop. Delegates all rendering to
 * PublicConversation and InternalMind — no display logic lives here.
 */

import type { SimulationOutput } from '../../types/simulation'

interface Props {
  simulation: SimulationOutput
}

export default function MindViewer({ simulation: _simulation }: Props) {
  return <div>TODO: MindViewer</div>
}
