import type { PersonaTurnOutput } from '../../types/simulation'

interface Props {
  turnOutput: PersonaTurnOutput
  priorMemoryNotes: string[]
  turnNumber: number
  previousPrivateStance?: number
}

export default function InternalMind({ turnOutput: _turnOutput, priorMemoryNotes: _priorMemoryNotes, turnNumber: _turnNumber, previousPrivateStance: _previousPrivateStance }: Props) {
  return (
    <div data-testid="internal-mind" className="h-full flex items-center justify-center text-slate-400 text-sm bg-violet-50">
      Internal Mind — coming in Step 5
    </div>
  )
}
