/**
 * WS-C — Public conversation transcript panel (one strategy column).
 *
 * Renders the visible chat transcript for one strategy: interviewer messages
 * on one side, persona public responses on the other, in chat-bubble format.
 * Clean, neutral visual treatment — this is what a bystander would see.
 *
 * Receives the turns array and the current turn index (controlled by MindViewer).
 * Only renders turns up to and including currentTurn — later turns are hidden
 * until the user advances.
 *
 * Pure display component — no state, no data fetching. The typing animation
 * for the "current" turn is the only stateful behavior, handled locally.
 */

import type { ConversationTurn } from '../../types/simulation'

interface Props {
  turns: ConversationTurn[]
  currentTurn: number
  strategyDisplayName: string
}

export default function PublicConversation({ turns: _turns, currentTurn: _currentTurn, strategyDisplayName: _strategyDisplayName }: Props) {
  return <div>TODO: PublicConversation</div>
}
