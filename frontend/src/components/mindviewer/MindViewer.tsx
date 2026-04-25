/**
 * WS-C — Screen 2: The hero split-screen mind viewer. Top-level container.
 *
 * Manages turn-by-turn navigation state (current turn index, play/pause/speed)
 * and lays out one column per strategy. Each column has two stacked panels:
 *   - PublicConversation (top): the visible transcript
 *   - InternalMind (bottom): monologue, emotion, identity threat, stance
 *
 * Coordinates the "streaming illusion" — even when loading from cache,
 * turns are revealed one at a time with a brief delay to convey live thinking.
 *
 * The user can pause on any turn across any strategy column and read the
 * internal mind panel carefully. Auto-advance should never outpace the user.
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
