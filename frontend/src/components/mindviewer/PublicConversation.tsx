import { useEffect, useRef, useState } from 'react'
import type { ConversationTurn } from '../../types/simulation'

interface Props {
  turns: ConversationTurn[]
  currentTurn: number
  strategyDisplayName: string
  personaDisplayName: string
}

const TYPING_SPEED_MS = 18

function useTypingReveal(text: string, trigger: number): string {
  const [revealed, setRevealed] = useState('')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    setRevealed('')
    let idx = 0
    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = setInterval(() => {
      idx += 1
      setRevealed(text.slice(0, idx))
      if (idx >= text.length) {
        clearInterval(intervalRef.current!)
      }
    }, TYPING_SPEED_MS)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger])

  return revealed
}

interface BubbleProps {
  text: string
  isTyping: boolean
  label: string
  side: 'left' | 'right'
  annotation?: string
  turnNumber: number
}

function ChatBubble({ text, isTyping, label, side, annotation, turnNumber }: BubbleProps) {
  const typedText = useTypingReveal(text, turnNumber)
  const displayText = isTyping ? typedText : text
  const showCursor = isTyping && typedText.length < text.length

  return (
    <div className={`flex flex-col gap-1 ${side === 'right' ? 'items-end' : 'items-start'}`}>
      <span className="text-xs font-mono text-slate-400 px-1">{label}</span>
      <div
        className={[
          'max-w-[80%] rounded-2xl px-4 py-3 text-base leading-relaxed',
          side === 'left'
            ? 'bg-slate-100 text-slate-800 rounded-tl-sm'
            : 'bg-white border border-slate-200 text-slate-900 rounded-tr-sm shadow-sm',
        ].join(' ')}
      >
        {displayText}
        {showCursor && (
          <span className="inline-block w-0.5 h-4 bg-slate-400 ml-0.5 animate-pulse align-middle" />
        )}
      </div>
      {annotation && side === 'left' && (
        <p className="text-xs italic text-slate-400 max-w-[80%] px-1 leading-relaxed">
          {annotation}
        </p>
      )}
    </div>
  )
}

export default function PublicConversation({ turns, currentTurn, strategyDisplayName, personaDisplayName }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const visibleTurns = turns.slice(0, currentTurn + 1)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentTurn])

  return (
    <div className="h-full flex flex-col bg-white" data-testid="public-conversation">
      {/* Panel header */}
      <div className="shrink-0 px-5 py-3 border-b border-slate-100">
        <p className="text-xs font-mono text-slate-400 uppercase tracking-widest">
          Public Conversation — {strategyDisplayName}
        </p>
      </div>

      {/* Chat transcript */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
        {visibleTurns.map((turn, idx) => {
          const isCurrentTurn = idx === currentTurn
          return (
            <div key={turn.turn_number} data-testid={`turn-${turn.turn_number}`}>
              {/* Turn badge */}
              <div className="flex justify-center mb-3">
                <span className="text-xs font-mono text-slate-300 bg-slate-50 border border-slate-100 px-2.5 py-0.5 rounded-full">
                  Turn {turn.turn_number}
                </span>
              </div>

              {/* Interviewer message */}
              <div className="mb-3">
                <ChatBubble
                  text={turn.interviewer_message}
                  isTyping={false}
                  label="Interviewer"
                  side="left"
                  annotation={turn.interviewer_strategy_note}
                  turnNumber={turn.turn_number}
                />
              </div>

              {/* Persona response — types in only on the current turn */}
              <ChatBubble
                text={turn.persona_output.public_response}
                isTyping={isCurrentTurn}
                label={personaDisplayName}
                side="right"
                turnNumber={turn.turn_number}
              />
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
