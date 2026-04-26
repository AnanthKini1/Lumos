import type { SimulationOutput, StrategyOutcome, VerdictCategory, ConversationTurn } from '../../types/simulation'
import TrajectoryChart from './TrajectoryChart'
import StrategyCard from './StrategyCard'
import ConversationTimeline from './ConversationTimeline'
import mechanisms from '../../data/cognitive_mechanisms.json'

const CATEGORY_COLOR: Record<string, string> = {
  backfire:           '#dc2626',
  genuine_persuasion: '#16a34a',
  surface_mechanism:  '#d97706',
}

function findMechanismName(id: string): string {
  return mechanisms.find(m => m.id === id)?.display_name
    ?? id.replace(/^mechanism_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function findMechanismCitation(id: string): string {
  const m = mechanisms.find(m => m.id === id)
  if (!m) return ''
  return m.framework ? `${m.framework}` : ''
}

function inflectionPointTurn(outcome: StrategyOutcome): ConversationTurn | undefined {
  return outcome.turns.find(t => t.is_inflection_point)
}

const VERDICT_ORDER: Record<VerdictCategory, number> = {
  GENUINE_BELIEF_SHIFT: 0,
  PARTIAL_SHIFT:        1,
  SURFACE_COMPLIANCE:   2,
  NO_MOVEMENT:          3,
  BACKFIRE:             4,
}

const VERDICT_LABEL: Record<VerdictCategory, string> = {
  GENUINE_BELIEF_SHIFT: 'GENUINE SHIFT',
  PARTIAL_SHIFT:        'PARTIAL SHIFT',
  SURFACE_COMPLIANCE:   'SURFACE COMPLIANCE',
  BACKFIRE:             'BACKFIRE',
  NO_MOVEMENT:          'NO MOVEMENT',
}

const PERSISTENCE_LABEL: Record<string, string> = {
  held:               'HELD',
  partially_reverted: 'PARTIAL REVERT',
  fully_reverted:     'FULL REVERT',
}

function strategyDisplayName(id: string): string {
  return id
    .replace(/^strategy_/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function formatDelta(start: number, end: number): string {
  const d = end - start
  return (d >= 0 ? '+' : '') + d.toFixed(1)
}

function computeRow(outcome: StrategyOutcome) {
  const { trajectory, cognitive_scores } = outcome
  const pubStart  = trajectory.public_stance_per_turn[0]
  const pubEnd    = trajectory.public_stance_per_turn.at(-1) ?? pubStart
  const privStart = trajectory.private_stance_per_turn[0]
  const privEnd   = trajectory.private_stance_per_turn.at(-1) ?? privStart
  return {
    publicDelta:  formatDelta(pubStart, pubEnd),
    privateDelta: formatDelta(privStart, privEnd),
    maxGap:       Math.max(...trajectory.gap_per_turn).toFixed(1),
    threats:      cognitive_scores.identity_threats_triggered,
    persistence:  cognitive_scores.persistence,
  }
}

interface Props {
  simulation: SimulationOutput
  onViewTranscript: (strategyId: string, turnNumber?: number) => void
  onBackToSetup: () => void
}

export default function ComparisonReport({ simulation, onViewTranscript, onBackToSetup }: Props) {
  const { outcomes, overall_synthesis, validation_note } = simulation

  const sortedOutcomes = [...outcomes].sort(
    (a, b) => VERDICT_ORDER[a.verdict] - VERDICT_ORDER[b.verdict]
  )

  return (
    <div className="min-h-screen bg-[#fafafa]" data-testid="comparison-report">
      {/* Thin nav strip */}
      <div className="bg-[#fafafa] border-b border-[#0f0f0f] border-opacity-20 px-8 py-2">
        <button
          data-testid="back-btn"
          onClick={onBackToSetup}
          className="font-mono text-xs text-[#0f0f0f] underline font-bold hover:opacity-60 transition-opacity"
        >
          ← Back to Setup
        </button>
      </div>

      {/* Masthead */}
      <header className="border-b-4 border-[#0f0f0f] px-8 pt-10 pb-8">
        <p className="font-mono text-xs text-[#0f0f0f] opacity-40 uppercase tracking-widest mb-3">Lumos / Analysis</p>
        <h1 className="font-black font-serif text-6xl leading-none text-[#0f0f0f]">
          Strategy Comparison Report
        </h1>
      </header>

      <div className="max-w-4xl mx-auto px-8 py-12 space-y-16">

        {/* Conversation timeline — first visual on the report */}
        <ConversationTimeline outcomes={outcomes} />

        {/* Insight synthesis */}
        <div data-testid="synthesis-card">
          <p className="text-xs font-mono font-bold text-[#0f0f0f] uppercase tracking-widest mb-4">Overall Synthesis</p>
          <div className="border-2 border-[#0f0f0f] p-8">
            <p className="text-3xl font-serif leading-snug text-[#0f0f0f]">{overall_synthesis}</p>
            {validation_note && (
              <p data-testid="validation-note" className="font-serif text-base italic text-[#0f0f0f] opacity-50 mt-6 pt-6 border-t border-[#0f0f0f] border-opacity-20">
                {validation_note}
              </p>
            )}
          </div>
        </div>

        {/* Strategy comparison table */}
        <section>
          <div className="bg-[#0f0f0f] -mx-8 px-8 py-3 mb-8">
            <p className="text-sm font-mono font-bold text-[#fafafa] uppercase tracking-widest">
              Strategy Comparison
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse border-2 border-[#0f0f0f]" data-testid="comparison-table">
              <thead>
                <tr>
                  <th className="text-left px-4 py-3 font-mono text-xs uppercase tracking-widest border border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]">Strategy</th>
                  <th className="text-left px-4 py-3 font-mono text-xs uppercase tracking-widest border border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]">Verdict</th>
                  <th className="text-center px-4 py-3 font-mono text-xs uppercase tracking-widest border border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]">Public Δ</th>
                  <th className="text-center px-4 py-3 font-mono text-xs uppercase tracking-widest border border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]">Private Δ</th>
                  <th className="text-center px-4 py-3 font-mono text-xs uppercase tracking-widest border border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]">Max Gap</th>
                  <th className="text-center px-4 py-3 font-mono text-xs uppercase tracking-widest border border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]">Threats</th>
                  <th className="text-left px-4 py-3 font-mono text-xs uppercase tracking-widest border border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]">Persistence</th>
                  <th className="px-4 py-3 border border-[#0f0f0f] bg-[#0f0f0f]" />
                </tr>
              </thead>
              <tbody>
                {sortedOutcomes.map(outcome => {
                  const row = computeRow(outcome)
                  const inflection = inflectionPointTurn(outcome)
                  return (
                    <tr
                      key={outcome.strategy_id}
                      data-testid={`report-row-${outcome.strategy_id}`}
                      className="border-b border-[#0f0f0f] hover:bg-[#f0ede8] transition-colors cursor-default"
                    >
                      <td className="px-4 py-3 font-serif font-bold text-[#0f0f0f] border border-[#0f0f0f]">
                        {strategyDisplayName(outcome.strategy_id)}
                      </td>
                      <td className="px-4 py-3 border border-[#0f0f0f]">
                        <span
                          data-testid={`verdict-badge-${outcome.strategy_id}`}
                          className="font-mono text-xs font-bold text-[#0f0f0f] uppercase"
                        >
                          {VERDICT_LABEL[outcome.verdict]}
                        </span>
                        {inflection && inflection.mechanism_classification && (
                          <div
                            data-testid={`inflection-callout-${outcome.strategy_id}`}
                            className="mt-2 px-3 py-2 font-mono text-xs text-[#0f0f0f] opacity-70 leading-snug border"
                            style={{ borderColor: CATEGORY_COLOR[inflection.color_category ?? ''] ?? '#0f0f0f' }}
                          >
                            <span className="font-bold">Turn {inflection.turn_number}</span>
                            {' — '}
                            {inflection.persuader_message.slice(0, 80)}{inflection.persuader_message.length > 80 ? '…' : ''}
                            <br />
                            <span className="opacity-75">
                              {(() => {
                                const name     = findMechanismName(inflection.mechanism_classification.primary_mechanism_id)
                                const citation = findMechanismCitation(inflection.mechanism_classification.primary_mechanism_id)
                                const shift    = inflection.stance_delta != null
                                  ? ` · Shift: ${inflection.stance_delta > 0 ? '+' : ''}${inflection.stance_delta.toFixed(1)}`
                                  : ''
                                return `${name}${citation ? ` · ${citation}` : ''}${shift}`
                              })()}
                            </span>
                          </div>
                        )}
                      </td>
                      <td
                        data-testid={`public-delta-${outcome.strategy_id}`}
                        className="px-4 py-3 text-center font-mono text-sm text-[#0f0f0f] border border-[#0f0f0f]"
                      >
                        {row.publicDelta}
                      </td>
                      <td
                        data-testid={`private-delta-${outcome.strategy_id}`}
                        className="px-4 py-3 text-center font-mono text-sm text-[#0f0f0f] border border-[#0f0f0f]"
                      >
                        {row.privateDelta}
                      </td>
                      <td
                        data-testid={`max-gap-${outcome.strategy_id}`}
                        className="px-4 py-3 text-center font-mono text-sm text-[#0f0f0f] border border-[#0f0f0f]"
                      >
                        {row.maxGap}
                      </td>
                      <td
                        data-testid={`threats-${outcome.strategy_id}`}
                        className="px-4 py-3 text-center font-mono text-sm text-[#0f0f0f] border border-[#0f0f0f]"
                      >
                        {row.threats}
                      </td>
                      <td className="px-4 py-3 border border-[#0f0f0f]">
                        <span
                          data-testid={`persistence-${outcome.strategy_id}`}
                          className="font-mono text-xs font-bold text-[#0f0f0f] uppercase"
                        >
                          {PERSISTENCE_LABEL[row.persistence] ?? row.persistence.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 border border-[#0f0f0f]">
                        <button
                          data-testid={`view-transcript-${outcome.strategy_id}`}
                          onClick={() => onViewTranscript(outcome.strategy_id)}
                          className="font-mono text-xs font-bold text-[#0f0f0f] underline hover:opacity-60 transition-opacity"
                        >
                          Watch →
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* Stance trajectories */}
        <section>
          <div className="bg-[#0f0f0f] -mx-8 px-8 py-3 mb-8">
            <p className="text-sm font-mono font-bold text-[#fafafa] uppercase tracking-widest">
              Stance Trajectories
            </p>
          </div>
          <div data-testid="trajectory-section" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {sortedOutcomes.map(outcome => (
              <TrajectoryChart
                key={outcome.strategy_id}
                outcome={outcome}
                strategyDisplayName={strategyDisplayName(outcome.strategy_id)}
              />
            ))}
          </div>
        </section>

        {/* Strategy breakdown */}
        <section>
          <div className="bg-[#0f0f0f] -mx-8 px-8 py-3 mb-8">
            <p className="text-sm font-mono font-bold text-[#fafafa] uppercase tracking-widest">
              Strategy Breakdown
            </p>
          </div>
          <div data-testid="strategy-cards-section" className="space-y-6">
            {sortedOutcomes.map(outcome => (
              <StrategyCard
                key={outcome.strategy_id}
                outcome={outcome}
                strategyDisplayName={strategyDisplayName(outcome.strategy_id)}
                onViewTranscript={onViewTranscript}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
