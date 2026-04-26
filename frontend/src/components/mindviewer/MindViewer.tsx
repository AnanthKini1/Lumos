import { useState, useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { SimulationOutput, ConversationTurn } from '../../types/simulation'
import PublicConversation from './PublicConversation'
import InternalMind from './InternalMind'
import PivotalMomentPanel from './PivotalMomentPanel'

interface Props {
  simulation: SimulationOutput
  initialStrategyId?: string
  initialTurnNumber?: number
  onViewReport: () => void
}

export function strategyDisplayName(id: string): string {
  return id
    .replace(/^strategy_/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}


export default function MindViewer({ simulation, initialStrategyId, initialTurnNumber, onViewReport }: Props) {
  const { outcomes, metadata } = simulation
  const { persona, topic } = metadata

  const initialIdx = initialStrategyId
    ? Math.max(0, outcomes.findIndex(o => o.strategy_id === initialStrategyId))
    : 0

  const initialTurnIdx = initialTurnNumber != null
    ? Math.max(0, Math.min(initialTurnNumber - 1, outcomes[initialIdx].turns.length - 1))
    : 0

  const [activeIdx, setActiveIdx] = useState(initialIdx)
  const [currentTurn, setCurrentTurn] = useState(initialTurnIdx)
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedPivotalTurn, setSelectedPivotalTurn] = useState<ConversationTurn | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const activeOutcome = outcomes[activeIdx]
  const turns = activeOutcome.turns
  const maxTurn = turns.length - 1

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

  function handleTabSwitch(idx: number) {
    setActiveIdx(idx)
    setCurrentTurn(0)
    setIsPlaying(false)
    setSelectedPivotalTurn(null)
  }

  function handlePrev() {
    setIsPlaying(false)
    setCurrentTurn(t => Math.max(0, t - 1))
  }

  function handleNext() {
    setIsPlaying(false)
    setCurrentTurn(t => Math.min(maxTurn, t + 1))
  }

  const priorMemoryNotes = turns
    .slice(0, currentTurn)
    .map(t => t.persona_output.memory_to_carry_forward)
    .filter(Boolean)

  const previousPrivateStance =
    currentTurn > 0
      ? turns[currentTurn - 1].persona_output.private_stance
      : (topic.predicted_starting_stances[persona.id] ?? 5)

  return (
    <div className="h-screen flex flex-col bg-[#fafafa]" data-testid="mind-viewer">
      {/* Top bar */}
      <header className="shrink-0 bg-[#fafafa] border-b-2 border-[#0f0f0f] px-6 py-4 flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <span className="font-bold font-serif text-xl text-[#0f0f0f]">{persona.display_name}</span>
          <span className="text-[#0f0f0f] opacity-30 mx-2">·</span>
          <span className="font-serif text-base text-[#0f0f0f] opacity-60 truncate">{topic.display_name}</span>
        </div>
        <button
          data-testid="view-report-btn"
          onClick={onViewReport}
          className="shrink-0 px-4 py-2 border-2 border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa] font-bold font-mono text-sm hover:bg-[#333333] transition-colors"
        >
          View Report →
        </button>
      </header>

      {/* Strategy tabs */}
      <div className="shrink-0 bg-[#fafafa] border-b-2 border-[#0f0f0f] px-6">
        <div className="flex gap-0" role="tablist">
          {outcomes.map((outcome, idx) => {
            const active = idx === activeIdx
            const name = strategyDisplayName(outcome.strategy_id)
            return (
              <button
                key={outcome.strategy_id}
                role="tab"
                aria-selected={active}
                data-testid={`strategy-tab-${outcome.strategy_id}`}
                onClick={() => handleTabSwitch(idx)}
                className={[
                  'px-5 py-3.5 font-mono text-sm flex items-center gap-2 transition-all duration-150 border-b-4',
                  active
                    ? 'border-[#0f0f0f] font-bold text-[#0f0f0f]'
                    : 'border-transparent text-[#0f0f0f] opacity-50 hover:opacity-80',
                ].join(' ')}
              >
                {name}
              </button>
            )
          })}
        </div>
      </div>

      {/* Main panels */}
      <div className="flex-1 overflow-hidden relative">
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
            <div className="flex-1 overflow-hidden border-r-2 border-[#0f0f0f]">
              <PublicConversation
                turns={turns}
                currentTurn={currentTurn}
                strategyDisplayName={strategyDisplayName(activeOutcome.strategy_id)}
                personaDisplayName={persona.display_name}
                onPivotalClick={setSelectedPivotalTurn}
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

        {/* Pivotal moment detail panel — slides in from right over internal mind */}
        <PivotalMomentPanel
          turn={selectedPivotalTurn}
          onClose={() => setSelectedPivotalTurn(null)}
          personaDisplayName={persona.display_name}
        />
      </div>

      {/* Turn controls */}
      <footer
        className="shrink-0 bg-[#fafafa] border-t-2 border-[#0f0f0f] px-6 py-3 flex items-center justify-between"
        data-testid="turn-controls"
      >
        <div className="flex items-center gap-3">
          <button
            data-testid="prev-turn-btn"
            onClick={handlePrev}
            disabled={currentTurn === 0}
            aria-label="Previous turn"
            className="px-3 py-2 border-2 border-[#0f0f0f] font-mono text-sm text-[#0f0f0f] hover:bg-[#0f0f0f] hover:text-[#fafafa] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ◀
          </button>

          <span data-testid="turn-label" className="text-sm font-mono text-[#0f0f0f] w-24 text-center font-bold">
            Turn {currentTurn + 1} / {maxTurn + 1}
          </span>

          <button
            data-testid="next-turn-btn"
            onClick={handleNext}
            disabled={currentTurn === maxTurn}
            aria-label="Next turn"
            className="px-3 py-2 border-2 border-[#0f0f0f] font-mono text-sm text-[#0f0f0f] hover:bg-[#0f0f0f] hover:text-[#fafafa] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ▶
          </button>
        </div>

        <button
          data-testid="play-pause-btn"
          onClick={() => setIsPlaying(p => !p)}
          disabled={currentTurn === maxTurn && !isPlaying}
          className={[
            'flex items-center gap-2 px-5 py-2 border-2 font-mono text-sm font-bold transition-colors',
            isPlaying
              ? 'border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa] hover:bg-[#333333]'
              : 'border-[#0f0f0f] bg-transparent text-[#0f0f0f] hover:bg-[#0f0f0f] hover:text-[#fafafa]',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          ].join(' ')}
        >
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
      </footer>
    </div>
  )
}
