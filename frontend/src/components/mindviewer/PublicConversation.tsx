import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { ConversationTurn } from '../../types/simulation'

interface Props {
  turns: ConversationTurn[]
  currentTurn: number
  strategyDisplayName: string
  personaDisplayName: string
  onPivotalClick?: (turn: ConversationTurn) => void
}

const CATEGORY_COLOR: Record<string, string> = {
  backfire:             '#dc2626',
  genuine_persuasion:   '#16a34a',
  surface_mechanism:    '#d97706',
}

const TYPING_SPEED_MS = 18

const messageVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.25, ease: [0.22, 1, 0.36, 1] as const },
  },
}

const personaVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.25, ease: [0.22, 1, 0.36, 1] as const, delay: 0.1 },
  },
}

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
  isNew: boolean
}

function ChatBubble({ text, isTyping, label, side, annotation, turnNumber, isNew }: BubbleProps) {
  const typedText = useTypingReveal(text, turnNumber)
  const displayText = isTyping ? typedText : text
  const showCursor = isTyping && typedText.length < text.length

  const variants = side === 'left' ? messageVariants : personaVariants

  return (
    <motion.div
      variants={isNew ? variants : undefined}
      initial={isNew ? 'hidden' : false}
      animate={isNew ? 'visible' : false}
      className={`flex flex-col gap-1 ${side === 'right' ? 'items-end' : 'items-start'}`}
    >
      <span className="text-xs font-mono text-[#0f0f0f] opacity-70 font-bold uppercase tracking-widest px-1">
        {label}
      </span>
      <div
        className="max-w-[80%] border-2 border-[#0f0f0f] px-4 py-3 font-serif text-base leading-relaxed text-[#0f0f0f] bg-[#fafafa]"
      >
        {displayText}
        {showCursor && (
          <span className="inline-block w-0.5 h-4 bg-[#0f0f0f] ml-0.5 animate-pulse align-middle" />
        )}
      </div>
      {annotation && side === 'left' && (
        <p className="font-mono text-sm italic text-[#0f0f0f] opacity-70 max-w-[80%] px-1 leading-relaxed mt-1">
          {annotation}
        </p>
      )}
    </motion.div>
  )
}

export default function PublicConversation({ turns, currentTurn, strategyDisplayName, personaDisplayName, onPivotalClick }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const visibleTurns = turns.slice(0, currentTurn + 1)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentTurn])

  return (
    <div className="h-full flex flex-col bg-[#fafafa]" data-testid="public-conversation">
      {/* Panel header */}
      <div className="shrink-0 px-5 py-3 border-b-2 border-[#0f0f0f]">
        <p className="text-xs font-mono text-[#0f0f0f] opacity-50 uppercase tracking-widest mb-0.5">
          Persuasion Attempt
        </p>
        <p data-testid="strategy-name-header" className="text-base font-mono font-bold text-[#0f0f0f]">
          {strategyDisplayName}
        </p>
      </div>

      {/* Chat transcript */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
        <AnimatePresence initial={false}>
          {visibleTurns.map((turn, idx) => {
            const isCurrentTurn = idx === currentTurn
            const isInflection = turn.is_inflection_point
            const isPivotal = turn.is_pivotal === true
            const category = turn.color_category ?? ''
            const accentColor = CATEGORY_COLOR[category] ?? null

            return (
              <div
                key={turn.turn_number}
                data-testid={`turn-${turn.turn_number}`}
                onClick={isPivotal && onPivotalClick ? () => onPivotalClick(turn) : undefined}
                className={['transition-colors duration-150', isPivotal ? 'cursor-pointer' : ''].join(' ')}
              >
                {/* Turn badge + inflection / pivotal labels */}
                <div className="flex items-center justify-center gap-2 mb-3">
                  <span
                    data-testid={`turn-badge-${turn.turn_number}`}
                    className="text-xs font-mono font-bold text-[#0f0f0f] opacity-40 uppercase tracking-widest"
                  >
                    Turn {turn.turn_number}
                  </span>
                  {isInflection && (
                    <span
                      data-testid={`inflection-badge-${turn.turn_number}`}
                      className="font-mono text-xs font-bold uppercase tracking-wide text-[#0f0f0f]"
                    >
                      ★ INFLECTION
                    </span>
                  )}
                  {isPivotal && !isInflection && accentColor && (
                    <span
                      data-testid={`pivotal-badge-${turn.turn_number}`}
                      className="font-mono text-xs font-bold uppercase tracking-wide"
                      style={{ color: accentColor }}
                    >
                      ● PIVOTAL
                    </span>
                  )}
                </div>

                {/* Pivotal highlight — full border box, no side-stripe */}
                <div
                  className={isPivotal ? 'border-2 p-3' : ''}
                  style={isPivotal && accentColor
                    ? { borderColor: accentColor, backgroundColor: `${accentColor}0d` }
                    : undefined}
                >
                  {/* Persuader message */}
                  <div className="mb-3">
                    <ChatBubble
                      text={turn.persuader_message}
                      isTyping={false}
                      label="Persuader"
                      side="left"
                      annotation={turn.persuader_strategy_note}
                      turnNumber={turn.turn_number}
                      isNew={isCurrentTurn}
                    />
                  </div>

                  {/* Persona response — types in only on the current turn */}
                  <ChatBubble
                    text={turn.persona_output.public_response}
                    isTyping={isCurrentTurn}
                    label={personaDisplayName}
                    side="right"
                    turnNumber={turn.turn_number}
                    isNew={isCurrentTurn}
                  />
                </div>
              </div>
            )
          })}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
