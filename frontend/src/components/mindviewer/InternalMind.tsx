/**
 * WS-C — Internal mind panel for one turn (one strategy column).
 *
 * Renders the private layer of the current turn:
 *   - Internal monologue text with a typing/streaming reveal animation
 *   - Emotion badge (primary_emotion + intensity color)
 *   - Identity threat indicator — subtle glow/border when threatened: true
 *   - Private stance reading (numeric, with smooth tick between turns)
 *   - Memory note card — what the persona says they'll carry forward
 *
 * Visual treatment signals "behind the curtain": different background tint,
 * distinct typography, set apart from the public panel.
 *
 * Receives the PersonaTurnOutput for the current turn as a prop.
 * Pure display — no state except the typing animation for monologue text.
 *
 * Memory cards from ALL prior turns should stack up visibly above the current
 * one, so the judge can see residue accumulating across the conversation.
 */

import type { PersonaTurnOutput } from '../../types/simulation'

interface Props {
  turnOutput: PersonaTurnOutput
  priorMemoryNotes: string[]
  turnNumber: number
}

export default function InternalMind({ turnOutput: _turnOutput, priorMemoryNotes: _priorMemoryNotes, turnNumber: _turnNumber }: Props) {
  return <div>TODO: InternalMind</div>
}
