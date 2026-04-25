import { useEffect, useRef, useState } from 'react'
import type { PersonaTurnOutput, PrimaryEmotion } from '../../types/simulation'

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

const EMOTION_CONFIG: Record<PrimaryEmotion, { dot: string; bg: string; text: string }> = {
  defensive:  { dot: 'bg-rose-500',    bg: 'bg-rose-100',    text: 'text-rose-700' },
  frustrated: { dot: 'bg-orange-500',  bg: 'bg-orange-100',  text: 'text-orange-700' },
  threatened: { dot: 'bg-red-500',     bg: 'bg-red-100',     text: 'text-red-700' },
  dismissed:  { dot: 'bg-slate-400',   bg: 'bg-slate-100',   text: 'text-slate-600' },
  curious:    { dot: 'bg-sky-500',     bg: 'bg-sky-100',     text: 'text-sky-700' },
  bored:      { dot: 'bg-slate-400',   bg: 'bg-slate-100',   text: 'text-slate-600' },
  engaged:    { dot: 'bg-emerald-500', bg: 'bg-emerald-100', text: 'text-emerald-700' },
  intrigued:  { dot: 'bg-violet-500',  bg: 'bg-violet-100',  text: 'text-violet-700' },
  warm:       { dot: 'bg-amber-500',   bg: 'bg-amber-100',   text: 'text-amber-700' },
}

export default function InternalMind({ turnOutput, priorMemoryNotes, turnNumber, previousPrivateStance }: Props) {
  const { internal_monologue, emotional_reaction, identity_threat, private_stance, private_stance_change_reason, memory_to_carry_forward } = turnOutput

  const monologue = useTypingReveal(internal_monologue, turnNumber)
  const showCursor = monologue.length < internal_monologue.length

  const emotion = emotional_reaction.primary_emotion
  const emotionConfig = EMOTION_CONFIG[emotion]

  const prevStance = previousPrivateStance ?? private_stance
  const stanceDirection = private_stance < prevStance ? '↓' : private_stance > prevStance ? '↑' : '→'
  const stanceArrowColor = private_stance < prevStance ? 'text-emerald-600' : private_stance > prevStance ? 'text-rose-500' : 'text-slate-400'

  const threatened = identity_threat.threatened

  return (
    <div
      data-testid="internal-mind"
      className={[
        'h-full flex flex-col transition-colors duration-300',
        threatened
          ? 'bg-rose-50 border-l-4 border-rose-400'
          : 'bg-violet-50 border-l-2 border-violet-200',
      ].join(' ')}
    >
      {/* Panel header */}
      <div className="shrink-0 px-5 py-3 border-b border-violet-100">
        <p data-testid="mind-header" className="text-xs font-mono text-violet-400 uppercase tracking-widest">
          Internal Monologue — Turn {turnNumber}
        </p>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">

        {/* Emotion badge */}
        <div>
          <div
            data-testid="emotion-badge"
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full transition-colors duration-300 ${emotionConfig.bg}`}
          >
            <span className={`w-2 h-2 rounded-full shrink-0 ${emotionConfig.dot}`} />
            <span className={`text-sm font-semibold ${emotionConfig.text}`}>{emotion}</span>
            <div data-testid="intensity-dots" className="flex gap-0.5 ml-1">
              {Array.from({ length: 10 }, (_, i) => (
                <span
                  key={i}
                  className={`w-1.5 h-1.5 rounded-full ${i < emotional_reaction.intensity ? emotionConfig.dot : 'bg-slate-200'}`}
                />
              ))}
            </div>
          </div>
          <p className="text-xs italic text-slate-500 mt-1.5 px-1">
            Triggered by: &ldquo;{emotional_reaction.trigger}&rdquo;
          </p>
        </div>

        {/* Identity threat alert */}
        {threatened && (
          <div
            data-testid="identity-threat-badge"
            className="flex flex-wrap items-center gap-1.5 px-3 py-2 bg-rose-100 border border-rose-200 rounded-lg"
          >
            <span className="text-xs font-semibold text-rose-600">Identity threatened:</span>
            <span className="text-xs text-rose-700">{identity_threat.what_was_threatened}</span>
          </div>
        )}

        {/* Internal monologue */}
        <div className="space-y-1.5">
          <p className="text-xs font-mono text-violet-400 uppercase tracking-wider">Thinking</p>
          <div className="text-base italic text-violet-900 leading-relaxed min-h-[4rem]">
            {monologue}
            {showCursor && (
              <span className="inline-block w-0.5 h-4 bg-violet-400 ml-0.5 animate-pulse align-middle" />
            )}
          </div>
        </div>

        {/* Private stance */}
        <div data-testid="private-stance" className="space-y-1">
          <p className="text-xs font-mono text-violet-400 uppercase tracking-wider">Private Stance</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-violet-900">{private_stance.toFixed(1)}</span>
            <span className="text-slate-400 text-sm">/ 10</span>
            <span data-testid="stance-arrow" className={`text-lg font-bold ${stanceArrowColor}`}>
              {stanceDirection}
            </span>
          </div>
          <p className="text-xs italic text-violet-600">{private_stance_change_reason}</p>
        </div>

        {/* Memory residue */}
        <div className="space-y-2">
          <p className="text-xs font-mono text-violet-400 uppercase tracking-wider">Memory</p>

          {priorMemoryNotes.map((note, i) => (
            <div
              key={i}
              className="px-3 py-2 bg-white border border-slate-200 rounded-lg"
            >
              <span className="font-mono text-xs text-slate-400 mr-2">Turn {i + 1}</span>
              <span className="text-xs text-slate-500">{note}</span>
            </div>
          ))}

          <div
            data-testid="current-memory"
            className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg shadow-sm"
          >
            <span className="font-mono text-xs text-amber-600 mr-2">Turn {turnNumber}</span>
            <span className="text-xs text-amber-900">{memory_to_carry_forward}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
