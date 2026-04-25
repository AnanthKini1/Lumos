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
          const isInflection = turn.is_inflection_point
          const isPivotal = turn.is_pivotal
          const cat = turn.color_category

          const turnBadgeClass = isInflection
            ? 'text-violet-700 bg-violet-100 border-violet-300 font-semibold'
            : isPivotal && cat === 'backfire'
              ? 'text-rose-600 bg-rose-50 border-rose-200'
              : isPivotal && cat === 'genuine_persuasion'
                ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                : isPivotal && cat === 'surface_mechanism'
                  ? 'text-amber-600 bg-amber-50 border-amber-200'
                  : 'text-slate-300 bg-slate-50 border-slate-100'

          return (
            <div key={turn.turn_number} data-testid={`turn-${turn.turn_number}`}>
              {/* Turn badge */}
              <div className="flex justify-center mb-3 gap-2 items-center">
                <span
                  data-testid={`turn-badge-${turn.turn_number}`}
                  className={`text-xs font-mono border px-2.5 py-0.5 rounded-full transition-colors ${turnBadgeClass}`}
                >
                  Turn {turn.turn_number}
                </span>
                {isInflection && (
                  <span
                    data-testid={`inflection-badge-${turn.turn_number}`}
                    className="text-xs font-semibold text-violet-600 tracking-wide"
                  >
                    ★ Inflection Point
                  </span>
                )}
                {isPivotal && !isInflection && (
                  <span
                    data-testid={`pivotal-badge-${turn.turn_number}`}
                    className={`text-xs font-medium ${
                      cat === 'backfire' ? 'text-rose-500' :
                      cat === 'genuine_persuasion' ? 'text-emerald-600' : 'text-amber-500'
                    }`}
                  >
                    Pivotal
                  </span>
                )}
              </div>

              {/* Persuader message */}
              <div className="mb-3">
                <ChatBubble
                  text={turn.persuader_message}
                  isTyping={false}
                  label="Persuader"
                  side="left"
                  annotation={turn.persuader_strategy_note}
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
