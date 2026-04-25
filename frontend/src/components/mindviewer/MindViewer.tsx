import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { SimulationOutput, VerdictCategory } from '../../types/simulation'
import PublicConversation from './PublicConversation'
import InternalMind from './InternalMind'

interface Props {
  simulation: SimulationOutput
  initialStrategyId?: string
  onViewReport: () => void
}

// Strips "strategy_" prefix and converts snake_case to Title Case
export function strategyDisplayName(id: string): string {
  return id
    .replace(/^strategy_/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

const VERDICT_DOT: Record<VerdictCategory, string> = {
  GENUINE_BELIEF_SHIFT: 'bg-emerald-500',
  PARTIAL_SHIFT:        'bg-sky-500',
  SURFACE_COMPLIANCE:   'bg-amber-500',
  BACKFIRE:             'bg-rose-500',
  NO_MOVEMENT:          'bg-slate-400',
}

const VERDICT_LABEL: Record<VerdictCategory, string> = {
  GENUINE_BELIEF_SHIFT: 'Genuine Shift',
  PARTIAL_SHIFT:        'Partial Shift',
  SURFACE_COMPLIANCE:   'Surface Compliance',
  BACKFIRE:             'Backfire',
  NO_MOVEMENT:          'No Movement',
}

export default function MindViewer({ simulation, initialStrategyId, onViewReport }: Props) {
  const { outcomes, metadata } = simulation
  const { persona, topic } = metadata

  const initialIdx = initialStrategyId
    ? Math.max(0, outcomes.findIndex(o => o.strategy_id === initialStrategyId))
    : 0

  const [activeIdx, setActiveIdx] = useState(initialIdx)
  const [currentTurn, setCurrentTurn] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const activeOutcome = outcomes[activeIdx]
  const turns = activeOutcome.turns
  const maxTurn = turns.length - 1

  // Auto-advance when playing
  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(() => {
        setCurrentTurn(prev => {
          if (prev >= maxTurn) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, 2200)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isPlaying, maxTurn])

  // Reset turn when switching strategy
  function handleTabSwitch(idx: number) {
    setActiveIdx(idx)
    setCurrentTurn(0)
    setIsPlaying(false)
  }

  function handlePrev() {
    setIsPlaying(false)
    setCurrentTurn(t => Math.max(0, t - 1))
  }

  function handleNext() {
    setIsPlaying(false)
    setCurrentTurn(t => Math.min(maxTurn, t + 1))
  }

  // Build prior memory notes for InternalMind
  const priorMemoryNotes = turns
    .slice(0, currentTurn)
    .map(t => t.persona_output.memory_to_carry_forward)
    .filter(Boolean)

  const previousPrivateStance =
    currentTurn > 0
      ? turns[currentTurn - 1].persona_output.private_stance
      : (topic.predicted_starting_stances[persona.id] ?? 5)

  return (
    <div className="h-screen flex flex-col bg-slate-50" data-testid="mind-viewer">
      {/* Top bar */}
      <header className="shrink-0 bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <span className="font-bold text-slate-900 text-base">{persona.display_name}</span>
          <span className="text-slate-300 mx-2">·</span>
          <span className="text-slate-500 text-base truncate">{topic.display_name}</span>
        </div>
        <button
          data-testid="view-report-btn"
          onClick={onViewReport}
          className="shrink-0 px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-semibold hover:bg-purple-700 transition-colors"
        >
          View Report →
        </button>
      </header>

      {/* Strategy tabs */}
      <div className="shrink-0 bg-white border-b border-slate-200 px-6">
        <div className="flex gap-1 relative" role="tablist">
          {outcomes.map((outcome, idx) => {
            const active = idx === activeIdx
            const name = strategyDisplayName(outcome.strategy_id)
            const dotClass = VERDICT_DOT[outcome.verdict]
            return (
              <button
                key={outcome.strategy_id}
                role="tab"
                aria-selected={active}
                data-testid={`strategy-tab-${outcome.strategy_id}`}
                onClick={() => handleTabSwitch(idx)}
                className={[
                  'relative px-4 py-3.5 text-sm font-medium flex items-center gap-2 transition-colors duration-150 border-b-2',
                  active
                    ? 'text-purple-700 border-purple-600'
                    : 'text-slate-500 border-transparent hover:text-slate-700 hover:border-slate-300',
                ].join(' ')}
              >
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${dotClass}`}
                  title={VERDICT_LABEL[outcome.verdict]}
                  data-testid={`verdict-dot-${outcome.strategy_id}`}
                />
                {name}
                {active && (
                  <motion.span
                    layoutId="tab-underline"
                    className="absolute bottom-[-2px] left-0 right-0 h-0.5 bg-purple-600 rounded-full"
                  />
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Main panels */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeIdx}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="h-full flex flex-col lg:flex-row gap-0"
            data-testid="strategy-panel"
          >
            {/* Public conversation — left / top */}
            <div className="flex-1 overflow-hidden border-r border-slate-200">
              <PublicConversation
                turns={turns}
                currentTurn={currentTurn}
                strategyDisplayName={strategyDisplayName(activeOutcome.strategy_id)}
                personaDisplayName={persona.display_name}
              />
            </div>

            {/* Internal mind — right / bottom */}
            <div className="flex-1 overflow-hidden">
              <InternalMind
                turnOutput={turns[currentTurn].persona_output}
                priorMemoryNotes={priorMemoryNotes}
                turnNumber={currentTurn + 1}
                previousPrivateStance={previousPrivateStance}
              />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Turn controls */}
      <footer
        className="shrink-0 bg-white border-t border-slate-200 px-6 py-3 flex items-center justify-between"
        data-testid="turn-controls"
      >
        <div className="flex items-center gap-3">
          <button
            data-testid="prev-turn-btn"
            onClick={handlePrev}
            disabled={currentTurn === 0}
            aria-label="Previous turn"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </button>

          <span data-testid="turn-label" className="text-sm font-mono text-slate-600 w-24 text-center">
            Turn {currentTurn + 1} / {maxTurn + 1}
          </span>

          <button
            data-testid="next-turn-btn"
            onClick={handleNext}
            disabled={currentTurn === maxTurn}
            aria-label="Next turn"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        <button
          data-testid="play-pause-btn"
          onClick={() => setIsPlaying(p => !p)}
          disabled={currentTurn === maxTurn && !isPlaying}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {isPlaying ? (
            <>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Pause
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
              Play
            </>
          )}
        </button>
      </footer>
    </div>
  )
}
