import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import type { PersonaTurnOutput } from '../../types/simulation'

interface Props {
  turnOutput: PersonaTurnOutput
  priorMemoryNotes: string[]
  turnNumber: number
  previousPrivateStance?: number
}

const TYPING_SPEED_MS = 15

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
      if (idx >= text.length) clearInterval(intervalRef.current!)
    }, TYPING_SPEED_MS)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger])

  return revealed
}

export default function InternalMind({ turnOutput, priorMemoryNotes, turnNumber, previousPrivateStance }: Props) {
  const { internal_monologue, emotional_reaction, identity_threat, private_stance, private_stance_change_reason, memory_to_carry_forward } = turnOutput

  const monologue = useTypingReveal(internal_monologue, turnNumber)
  const showCursor = monologue.length < internal_monologue.length

  const prevStance = previousPrivateStance ?? private_stance
  const stanceDirection = private_stance < prevStance ? '↓' : private_stance > prevStance ? '↑' : '→'

  const threatened = identity_threat.threatened

  return (
    <div
      data-testid="internal-mind"
      className={[
        'h-full flex flex-col bg-[#f2ede4] text-[#0f0f0f] transition-colors duration-300 border-l-4',
        threatened ? 'border-[#dc2626]' : 'border-[#0f0f0f]',
      ].join(' ')}
    >
      {/* Panel header */}
      <div className="shrink-0 px-5 py-3 border-b border-[#0f0f0f] border-opacity-10">
        <p data-testid="mind-header" className="text-xs font-mono text-[#0f0f0f] opacity-60 font-bold uppercase tracking-[0.3em]">
          Internal Monologue — Turn {turnNumber}
        </p>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">

        {/* Emotion display */}
        <div>
          <motion.div
            data-testid="emotion-badge"
            key={emotional_reaction.primary_emotion}
            animate={{ opacity: [0.4, 1] }}
            transition={{ duration: 0.3 }}
          >
            <p className="font-mono font-bold text-4xl text-[#0f0f0f] uppercase tracking-wide leading-none">
              {emotional_reaction.primary_emotion} — {emotional_reaction.intensity}/10
            </p>
          </motion.div>
          <p className="font-mono text-sm text-[#0f0f0f] opacity-70 mt-1.5">
            Triggered by: &ldquo;{emotional_reaction.trigger}&rdquo;
          </p>
        </div>

        {/* Identity threat */}
        {threatened && (
          <div
            data-testid="identity-threat-badge"
            className="px-3 py-2 border border-[#dc2626]"
          >
            <span className="font-mono text-xs font-bold text-[#dc2626] uppercase">
              ⚠ Identity Threat: {identity_threat.what_was_threatened}
            </span>
          </div>
        )}

        {/* Internal monologue */}
        <div className="space-y-2">
          <p className="text-sm font-mono font-bold text-[#0f0f0f] opacity-70 uppercase tracking-wider">Thinking</p>

          {/* Prior turns faded */}
          {priorMemoryNotes.length > 0 && (
            <div className="space-y-1 opacity-40">
              {turnOutput.internal_monologue && priorMemoryNotes.map((_, i) => (
                <div key={i} className="text-sm font-serif italic text-[#0f0f0f] line-clamp-2">
                  {/* prior monologue is not stored, show memory note as proxy */}
                </div>
              ))}
            </div>
          )}

          {/* Current monologue */}
          <div className="text-lg italic font-serif text-[#0f0f0f] leading-relaxed min-h-[5rem]">
            {monologue}
            {showCursor && (
              <span className="typing-cursor" />
            )}
          </div>
        </div>

        {/* Private stance — hero number */}
        <div data-testid="private-stance" className="space-y-1 border-t border-[#0f0f0f] border-opacity-10 pt-4">
          <p className="text-sm font-mono font-bold text-[#0f0f0f] opacity-70 uppercase tracking-wider">Private Stance</p>
          <div className="flex items-baseline gap-3">
            <span className="text-6xl font-mono font-bold text-[#0f0f0f] leading-none">
              {private_stance.toFixed(1)}
            </span>
            <span className="text-[#0f0f0f] opacity-40 font-mono text-xl">/ 10</span>
            <span data-testid="stance-arrow" className="text-2xl text-[#0f0f0f] font-mono">
              {stanceDirection}
            </span>
          </div>
          <p className="text-sm font-serif italic text-[#0f0f0f] opacity-80 mt-1">{private_stance_change_reason}</p>
        </div>

        {/* Memory residue */}
        <div className="space-y-2 border-t border-[#0f0f0f] border-opacity-10 pt-4">
          <p className="text-sm font-mono font-bold text-[#0f0f0f] opacity-70 uppercase tracking-wider">Memory</p>

          {priorMemoryNotes.map((note, i) => (
            <div
              key={i}
              className="px-3 py-2 border border-[#0f0f0f] border-opacity-20 opacity-60"
            >
              <span className="font-mono text-xs text-[#0f0f0f] mr-2 font-bold">Turn {i + 1}</span>
              <span className="font-serif text-xs text-[#0f0f0f] opacity-70">{note}</span>
            </div>
          ))}

          <div
            data-testid="current-memory"
            className="px-3 py-2 border-2 border-[#0f0f0f]"
          >
            <span className="font-mono text-xs text-[#0f0f0f] mr-2 font-bold">Turn {turnNumber}</span>
            <span className="font-serif text-xs text-[#0f0f0f]">{memory_to_carry_forward}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
