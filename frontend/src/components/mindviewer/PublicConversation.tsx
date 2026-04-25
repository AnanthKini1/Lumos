import type { ConversationTurn } from '../../types/simulation'

interface Props {
  turns: ConversationTurn[]
  currentTurn: number
  strategyDisplayName: string
  personaDisplayName: string
}

export default function PublicConversation({ turns: _turns, currentTurn: _currentTurn, strategyDisplayName: _strategyDisplayName, personaDisplayName: _personaDisplayName }: Props) {
  return (
    <div data-testid="public-conversation" className="h-full flex items-center justify-center text-slate-400 text-sm">
      Public Conversation — coming in Step 4
    </div>
  )
}
