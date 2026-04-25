import type { SimulationOutput, StrategyOutcome, VerdictCategory } from '../../types/simulation'
import TrajectoryChart from './TrajectoryChart'
import StrategyCard from './StrategyCard'

const VERDICT_ORDER: Record<VerdictCategory, number> = {
  GENUINE_BELIEF_SHIFT: 0,
  PARTIAL_SHIFT:        1,
  SURFACE_COMPLIANCE:   2,
  NO_MOVEMENT:          3,
  BACKFIRE:             4,
}

const VERDICT_STYLE: Record<VerdictCategory, { bg: string; text: string; border: string }> = {
  GENUINE_BELIEF_SHIFT: { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-200' },
  PARTIAL_SHIFT:        { bg: 'bg-sky-100',     text: 'text-sky-700',     border: 'border-sky-200' },
  SURFACE_COMPLIANCE:   { bg: 'bg-amber-100',   text: 'text-amber-700',   border: 'border-amber-200' },
  BACKFIRE:             { bg: 'bg-rose-100',     text: 'text-rose-700',    border: 'border-rose-200' },
  NO_MOVEMENT:          { bg: 'bg-slate-100',   text: 'text-slate-600',   border: 'border-slate-200' },
}

const VERDICT_LABEL: Record<VerdictCategory, string> = {
  GENUINE_BELIEF_SHIFT: 'Genuine Shift',
  PARTIAL_SHIFT:        'Partial Shift',
  SURFACE_COMPLIANCE:   'Surface Compliance',
  BACKFIRE:             'Backfire',
  NO_MOVEMENT:          'No Movement',
}

const PERSISTENCE_STYLE: Record<string, { bg: string; text: string }> = {
  held:               { bg: 'bg-emerald-100', text: 'text-emerald-700' },
  partially_reverted: { bg: 'bg-amber-100',   text: 'text-amber-700' },
  fully_reverted:     { bg: 'bg-rose-100',     text: 'text-rose-700' },
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
  onViewTranscript: (strategyId: string) => void
  onBackToSetup: () => void
}

export default function ComparisonReport({ simulation, onViewTranscript, onBackToSetup }: Props) {
  const { outcomes, overall_synthesis, validation_note } = simulation

  const sortedOutcomes = [...outcomes].sort(
    (a, b) => VERDICT_ORDER[a.verdict] - VERDICT_ORDER[b.verdict]
  )

  return (
    <div className="min-h-screen bg-slate-50" data-testid="comparison-report">
      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4">
        <button
          data-testid="back-btn"
          onClick={onBackToSetup}
          className="text-sm text-slate-500 hover:text-slate-800 transition-colors"
        >
          ← Back to Setup
        </button>
        <span className="text-slate-300 select-none">|</span>
        <h1 className="font-bold text-slate-900 text-base">Strategy Comparison Report</h1>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* Insight synthesis */}
        <div
          data-testid="synthesis-card"
          className="bg-white border border-slate-200 border-l-4 border-l-amber-400 rounded-xl p-6 shadow-sm"
        >
          <p className="text-xs font-mono text-amber-600 uppercase tracking-widest mb-3">Overall Synthesis</p>
          <p className="text-lg text-slate-900 leading-relaxed">{overall_synthesis}</p>
          {validation_note && (
            <p data-testid="validation-note" className="text-sm italic text-slate-500 mt-3">
              {validation_note}
            </p>
          )}
        </div>

        {/* Strategy comparison table */}
        <section>
          <h2 className="text-lg font-semibold text-slate-800 tracking-tight mb-1">Strategy Comparison</h2>
          <p className="text-sm text-slate-500 mb-4">How each approach landed on this persona.</p>

          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-sm" data-testid="comparison-table">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-4 py-3 font-semibold text-slate-600 text-sm">Strategy</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600 text-sm">Verdict</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600 text-sm">Public Δ</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600 text-sm">Private Δ</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600 text-sm">Max Gap</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600 text-sm">Threats</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600 text-sm">Persistence</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {sortedOutcomes.map(outcome => {
                  const row = computeRow(outcome)
                  const vs = VERDICT_STYLE[outcome.verdict]
                  const ps = PERSISTENCE_STYLE[row.persistence] ?? PERSISTENCE_STYLE.held
                  return (
                    <tr
                      key={outcome.strategy_id}
                      data-testid={`report-row-${outcome.strategy_id}`}
                      className="border-b border-slate-50 hover:bg-slate-50 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium text-slate-800">
                        {strategyDisplayName(outcome.strategy_id)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          data-testid={`verdict-badge-${outcome.strategy_id}`}
                          className={`inline-block font-mono text-xs px-2.5 py-1 rounded-full border ${vs.bg} ${vs.text} ${vs.border}`}
                        >
                          {VERDICT_LABEL[outcome.verdict]}
                        </span>
                      </td>
                      <td
                        data-testid={`public-delta-${outcome.strategy_id}`}
                        className="px-4 py-3 text-right font-mono text-slate-700"
                      >
                        {row.publicDelta}
                      </td>
                      <td
                        data-testid={`private-delta-${outcome.strategy_id}`}
                        className="px-4 py-3 text-right font-mono text-slate-700"
                      >
                        {row.privateDelta}
                      </td>
                      <td
                        data-testid={`max-gap-${outcome.strategy_id}`}
                        className="px-4 py-3 text-right font-mono text-slate-700"
                      >
                        {row.maxGap}
                      </td>
                      <td
                        data-testid={`threats-${outcome.strategy_id}`}
                        className="px-4 py-3 text-right font-mono text-slate-700"
                      >
                        {row.threats}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          data-testid={`persistence-${outcome.strategy_id}`}
                          className={`inline-block font-mono text-xs px-2.5 py-1 rounded-full ${ps.bg} ${ps.text}`}
                        >
                          {row.persistence.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          data-testid={`view-transcript-${outcome.strategy_id}`}
                          onClick={() => onViewTranscript(outcome.strategy_id)}
                          className="text-xs text-violet-600 hover:text-violet-800 font-medium transition-colors"
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

        {/* Stance trajectories — placeholder for Step 7 */}
        <section>
          <h2 className="text-lg font-semibold text-slate-800 tracking-tight mb-4">Stance Trajectories</h2>
          <div data-testid="trajectory-section" className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {sortedOutcomes.map(outcome => (
              <TrajectoryChart
                key={outcome.strategy_id}
                outcome={outcome}
                strategyDisplayName={strategyDisplayName(outcome.strategy_id)}
              />
            ))}
          </div>
        </section>

        {/* Strategy breakdown — placeholder for Step 8 */}
        <section>
          <h2 className="text-lg font-semibold text-slate-800 tracking-tight mb-4">Strategy Breakdown</h2>
          <div data-testid="strategy-cards-section" className="space-y-4">
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
