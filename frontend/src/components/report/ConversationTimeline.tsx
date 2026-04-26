import { useState } from 'react'
import type { StrategyOutcome, ConversationTurn } from '../../types/simulation'
import mechanisms from '../../data/cognitive_mechanisms.json'

const CATEGORY_COLOR: Record<string, string> = {
  backfire:           '#dc2626',
  genuine_persuasion: '#16a34a',
  surface_mechanism:  '#d97706',
}

const CATEGORY_LABEL: Record<string, string> = {
  backfire:           'Backfire',
  genuine_persuasion: 'Genuine Persuasion',
  surface_mechanism:  'Surface Mechanism',
}

function strategyDisplayName(id: string): string {
  return id
    .replace(/^strategy_/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function findMechanism(id: string) {
  return mechanisms.find(m => m.id === id)
}

// Converts legacy snake_case identity threat strings (e.g. "intelligence_and_identity_as_thoughtful_person")
// to readable prose. No-ops on already well-formed sentences.
function formatIdentityThreat(raw: string | null | undefined): string {
  if (!raw) return ''
  // If it looks like a variable name (no spaces, contains underscores), convert it
  if (!raw.includes(' ') && raw.includes('_')) {
    const words = raw.replace(/_/g, ' ')
    return `Their ${words} felt threatened.`
  }
  return raw
}

interface Props {
  outcomes: StrategyOutcome[]
}

export default function ConversationTimeline({ outcomes }: Props) {
  const [selectedOutcomeIdx, setSelectedOutcomeIdx] = useState(0)
  const [selectedTurnIdx, setSelectedTurnIdx]       = useState<number | null>(null)

  const activeOutcome = outcomes[selectedOutcomeIdx]
  const turns         = activeOutcome?.turns ?? []
  const selectedTurn  = selectedTurnIdx !== null ? turns[selectedTurnIdx] : null

  function handleNodeClick(idx: number) {
    setSelectedTurnIdx(prev => (prev === idx ? null : idx))
  }

  function handleStrategyChange(idx: number) {
    setSelectedOutcomeIdx(idx)
    setSelectedTurnIdx(null)
  }

  if (outcomes.length === 0) return null

  return (
    <div data-testid="conversation-timeline">
      {/* Section header */}
      <p className="font-mono font-bold text-[#0f0f0f] uppercase tracking-widest text-2xl text-center mb-8">
        Conversation Timeline
      </p>

      {/* Strategy selector pills — only shown when there are multiple outcomes */}
      {outcomes.length > 1 && (
        <div className="flex gap-3 mb-8 overflow-x-auto justify-center">
          {outcomes.map((outcome, idx) => (
            <button
              key={outcome.strategy_id}
              data-testid={`timeline-strategy-pill-${outcome.strategy_id}`}
              onClick={() => handleStrategyChange(idx)}
              className={[
                'font-mono text-xs font-bold uppercase tracking-widest px-4 py-2 border-2 transition-colors',
                idx === selectedOutcomeIdx
                  ? 'bg-[#0f0f0f] text-[#fafafa] border-[#0f0f0f]'
                  : 'bg-transparent text-[#0f0f0f] border-[#0f0f0f] hover:bg-[#0f0f0f] hover:text-[#fafafa]',
              ].join(' ')}
            >
              {strategyDisplayName(outcome.strategy_id)}
            </button>
          ))}
        </div>
      )}

      {/* Timeline row — scrollable horizontally if needed */}
      <div className="overflow-x-auto pb-2">
        <div
          className="flex items-end"
          style={{ minWidth: `${turns.length * 130}px` }}
        >
          {turns.map((turn, idx) => {
            const nodeColor  = CATEGORY_COLOR[turn.color_category ?? ''] ?? '#9ca3af'
            const isSelected = selectedTurnIdx === idx
            const isFirst    = idx === 0
            const isLast     = idx === turns.length - 1

            return (
              <div
                key={turn.turn_number}
                className="flex flex-col items-center"
                style={{ flex: 1, minWidth: '130px' }}
              >
                {/* Round label — above the node */}
                <span
                  className="font-mono text-xs font-bold uppercase tracking-widest mb-3 select-none"
                  style={{
                    color:   isSelected ? nodeColor : '#0f0f0f',
                    opacity: isSelected ? 1 : 0.5,
                    transition: 'color 0.2s ease, opacity 0.2s ease',
                  }}
                >
                  Round {turn.turn_number}
                </span>

                {/* Connector line + node */}
                <div className="relative flex items-center w-full justify-center" style={{ height: '24px' }}>
                  {/* Left half of connector */}
                  {!isFirst && (
                    <div
                      className="absolute top-1/2 -translate-y-1/2"
                      style={{ left: 0, right: '50%', height: '2px', backgroundColor: '#0f0f0f', opacity: 0.15 }}
                    />
                  )}
                  {/* Right half of connector */}
                  {!isLast && (
                    <div
                      className="absolute top-1/2 -translate-y-1/2"
                      style={{ left: '50%', right: 0, height: '2px', backgroundColor: '#0f0f0f', opacity: 0.15 }}
                    />
                  )}

                  {/* Node */}
                  <button
                    data-testid={`timeline-node-${turn.turn_number}`}
                    onClick={() => handleNodeClick(idx)}
                    aria-label={`Round ${turn.turn_number}`}
                    aria-pressed={isSelected}
                    className="relative z-10 rounded-full border-2 hover:scale-125"
                    style={{
                      width:           '20px',
                      height:          '20px',
                      backgroundColor: isSelected ? nodeColor : '#fafafa',
                      borderColor:     nodeColor,
                      transition:      'transform 0.15s ease, background-color 0.2s ease, border-color 0.2s ease',
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Synthesis panel — slides in below with smooth height + opacity transition */}
      <div
        data-testid="timeline-synthesis-panel"
        style={{
          maxHeight:  selectedTurn ? '900px' : '0px',
          opacity:    selectedTurn ? 1 : 0,
          overflow:   'hidden',
          transition: 'max-height 0.35s ease, opacity 0.25s ease',
        }}
      >
        {selectedTurn && <TurnSynthesis turn={selectedTurn} />}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Turn synthesis panel
// ---------------------------------------------------------------------------

interface TurnSynthesisProps {
  turn: ConversationTurn
}

function TurnSynthesis({ turn }: TurnSynthesisProps) {
  const mechData     = turn.mechanism_classification
    ? findMechanism(turn.mechanism_classification.primary_mechanism_id)
    : null
  const color        = CATEGORY_COLOR[turn.color_category ?? ''] ?? '#6b7280'
  const categoryLabel = CATEGORY_LABEL[turn.color_category ?? ''] ?? null

  return (
    <div className="mt-6 border-2 border-[#0f0f0f] p-6 space-y-6" data-testid="turn-synthesis">
      {/* Header row */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-mono text-xs font-bold uppercase tracking-widest text-[#0f0f0f]">
          Round {turn.turn_number}
        </span>

        {turn.stance_delta === 0 ? (
          <span className="font-mono text-xs font-bold px-2 py-0.5 border border-[#0f0f0f] text-[#0f0f0f] opacity-40">
            No shift
          </span>
        ) : (
          <span
            className="font-mono text-xs font-bold px-2 py-0.5 border"
            style={{ color, borderColor: color }}
          >
            {turn.stance_delta > 0 ? '+' : ''}{turn.stance_delta.toFixed(1)} stance shift
          </span>
        )}

        {categoryLabel && (
          <span
            className="font-mono text-xs font-bold px-2 py-0.5 text-[#fafafa]"
            style={{ backgroundColor: color }}
          >
            {categoryLabel}
          </span>
        )}
      </div>

      {/* Internal monologue — what the persona was actually thinking */}
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-2">
          Internal Monologue
        </p>
        <p className="font-serif text-sm text-[#0f0f0f] leading-relaxed italic opacity-80">
          "{turn.persona_output.internal_monologue}"
        </p>
      </div>

      {/* Identity threat — only shown on significant shifts */}
      {turn.is_pivotal && turn.persona_output.identity_threat.threatened && (
        <div
          className="px-4 py-3 space-y-1"
          style={{ borderLeft: `3px solid ${CATEGORY_COLOR.backfire}` }}
        >
          <p className="font-mono text-xs uppercase tracking-widest opacity-50 text-[#0f0f0f]">
            Identity Threatened
          </p>
          <p className="font-serif text-sm text-[#0f0f0f] leading-relaxed">
            {formatIdentityThreat(turn.persona_output.identity_threat.what_was_threatened)}
          </p>
        </div>
      )}

      {/* Cognitive mechanism — explains WHY this happened psychologically */}
      {mechData && turn.mechanism_classification ? (
        <div
          className="space-y-3 pl-4"
          style={{ borderLeft: `3px solid ${color}` }}
        >
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-1">
              Cognitive Mechanism Triggered
            </p>
            <p className="font-serif font-bold text-lg text-[#0f0f0f]">{mechData.display_name}</p>
            <p className="font-mono text-xs text-[#0f0f0f] opacity-50 mt-0.5">{mechData.framework}</p>
          </div>

          <p className="font-serif text-sm text-[#0f0f0f] opacity-70 leading-relaxed">
            {mechData.operational_definition}
          </p>

          {turn.mechanism_classification.explanation && (
            <p className="font-serif text-sm text-[#0f0f0f] leading-relaxed">
              {turn.mechanism_classification.explanation}
            </p>
          )}

          {turn.mechanism_classification.evidence_quotes.length > 0 && (
            <div className="space-y-2">
              <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50">
                From the Persona's Response
              </p>
              {turn.mechanism_classification.evidence_quotes.slice(0, 2).map((q, i) => (
                <p key={i} className="font-serif text-xs italic text-[#0f0f0f] opacity-60 leading-relaxed">
                  "{q}"
                </p>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-40 mb-1">
            No Mechanism Classified
          </p>
        </div>
      )}

      {/* Emotional snapshot */}
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-2">
          Emotional Reaction
        </p>
        <div className="flex items-center gap-4 flex-wrap">
          <span className="font-mono text-xs font-bold text-[#0f0f0f] uppercase tracking-widest">
            {turn.persona_output.emotional_reaction.primary_emotion}
          </span>
          <div className="flex gap-1">
            {Array.from({ length: 10 }, (_, i) => (
              <div
                key={i}
                className="rounded-sm"
                style={{
                  width:           '8px',
                  height:          '8px',
                  backgroundColor: i < turn.persona_output.emotional_reaction.intensity
                    ? color
                    : '#e5e7eb',
                  transition: 'background-color 0.2s ease',
                }}
              />
            ))}
          </div>
          <span className="font-mono text-xs text-[#0f0f0f] opacity-40">
            {turn.persona_output.emotional_reaction.intensity}/10
          </span>
        </div>
      </div>

      {/* Cognitive scores — only rendered when present */}
      {turn.per_turn_cognitive_scores &&
        Object.keys(turn.per_turn_cognitive_scores).length > 0 && (
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-3">
              Cognitive Scores
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {Object.entries(turn.per_turn_cognitive_scores).map(([key, val]) => (
                <div key={key} className="border border-[#0f0f0f] border-opacity-20 px-3 py-2">
                  <p className="font-mono text-xs text-[#0f0f0f] opacity-40 mb-0.5 capitalize">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p className="font-mono text-sm font-bold text-[#0f0f0f]">
                    {typeof val === 'number' ? val.toFixed(1) : String(val)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
    </div>
  )
}
