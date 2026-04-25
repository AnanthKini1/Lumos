import { useState } from 'react'
import type { StrategyOutcome, VerdictCategory } from '../../types/simulation'

const CARD_STYLE: Record<VerdictCategory, { border: string; leftBorder: string }> = {
  GENUINE_BELIEF_SHIFT: { border: 'border-emerald-200', leftBorder: 'border-l-emerald-400' },
  PARTIAL_SHIFT:        { border: 'border-sky-200',     leftBorder: 'border-l-sky-400' },
  SURFACE_COMPLIANCE:   { border: 'border-amber-200',   leftBorder: 'border-l-amber-400' },
  BACKFIRE:             { border: 'border-rose-200',     leftBorder: 'border-l-rose-400' },
  NO_MOVEMENT:          { border: 'border-slate-200',   leftBorder: 'border-l-slate-300' },
}

const BADGE: Record<VerdictCategory, { bg: string; text: string; border: string; label: string }> = {
  GENUINE_BELIEF_SHIFT: { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-200', label: 'Genuine Shift' },
  PARTIAL_SHIFT:        { bg: 'bg-sky-100',     text: 'text-sky-700',     border: 'border-sky-200',     label: 'Partial Shift' },
  SURFACE_COMPLIANCE:   { bg: 'bg-amber-100',   text: 'text-amber-700',   border: 'border-amber-200',   label: 'Surface Compliance' },
  BACKFIRE:             { bg: 'bg-rose-100',     text: 'text-rose-700',    border: 'border-rose-200',    label: 'Backfire' },
  NO_MOVEMENT:          { bg: 'bg-slate-100',   text: 'text-slate-600',   border: 'border-slate-200',   label: 'No Movement' },
}

interface Props {
  outcome: StrategyOutcome
  strategyDisplayName: string
  onViewTranscript: (strategyId: string) => void
}

function ScoreBar({ value }: { value: number }) {
  const pct = Math.min(100, (value / 10) * 100)
  return (
    <div className="h-1.5 bg-slate-100 rounded-full w-full">
      <div className="h-full rounded-full bg-violet-400 transition-all" style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function StrategyCard({ outcome, strategyDisplayName, onViewTranscript }: Props) {
  const [expanded, setExpanded] = useState(false)
  const { verdict, verdict_reasoning, cognitive_scores, standout_quotes, synthesis_paragraph } = outcome

  const cardStyle = CARD_STYLE[verdict]
  const badge = BADGE[verdict]
  const hasIdentityThreats = cognitive_scores.identity_threats_triggered > 0

  return (
    <div
      data-testid={`strategy-card-${outcome.strategy_id}`}
      className={`bg-white border ${cardStyle.border} border-l-4 ${cardStyle.leftBorder} rounded-xl shadow-sm overflow-hidden`}
    >
      {/* Collapsed header — always visible */}
      <button
        data-testid={`strategy-card-toggle-${outcome.strategy_id}`}
        onClick={() => setExpanded(e => !e)}
        aria-expanded={expanded}
        className="w-full px-5 py-4 flex items-start gap-3 text-left hover:bg-slate-50 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span className="font-semibold text-slate-800 text-base">{strategyDisplayName}</span>
            <span
              data-testid={`card-verdict-badge-${outcome.strategy_id}`}
              className={`font-mono text-xs px-2.5 py-0.5 rounded-full border ${badge.bg} ${badge.text} ${badge.border}`}
            >
              {badge.label}
            </span>
            {verdict === 'BACKFIRE' && hasIdentityThreats && (
              <span
                data-testid={`identity-defense-badge-${outcome.strategy_id}`}
                className="text-xs px-2 py-0.5 rounded-full bg-rose-100 text-rose-600 font-medium"
              >
                ⚠ Identity defense triggered
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 leading-snug">{verdict_reasoning}</p>
        </div>
        <span
          className={`text-slate-400 text-xl font-light shrink-0 mt-0.5 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
          aria-hidden="true"
        >
          ›
        </span>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div
          data-testid={`strategy-card-body-${outcome.strategy_id}`}
          className="px-5 pb-5 space-y-5 border-t border-slate-100"
        >
          {/* Cognitive score mini-badges */}
          <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {([
              { label: 'Engagement',          value: cognitive_scores.average_engagement_depth },
              { label: 'Motivated Reasoning', value: cognitive_scores.motivated_reasoning_intensity },
              { label: 'Ambivalence',         value: cognitive_scores.ambivalence_presence },
              { label: 'Gap Score',           value: cognitive_scores.public_private_gap_score },
            ] as const).map(({ label, value }) => (
              <div key={label} className="bg-slate-50 border border-slate-100 rounded-lg px-3 py-2.5 space-y-1.5">
                <p className="text-xs text-slate-500 font-medium leading-tight">{label}</p>
                <ScoreBar value={value} />
                <p className="font-mono text-xs text-slate-700">{value.toFixed(1)}</p>
              </div>
            ))}
          </div>

          {/* Standout quotes */}
          {standout_quotes.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Standout Moments</p>
              {standout_quotes.slice(0, 3).map((quote, i) => (
                <blockquote
                  key={i}
                  data-testid={`quote-${i}-${outcome.strategy_id}`}
                  className="border-l-2 border-violet-300 pl-3 bg-violet-50 rounded-r-lg py-2 pr-3"
                >
                  <div className="flex gap-2 mb-1.5">
                    <span className="text-xs font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                      Turn {quote.turn}
                    </span>
                    <span
                      className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                        quote.type === 'monologue'
                          ? 'bg-violet-100 text-violet-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {quote.type}
                    </span>
                  </div>
                  <p className="text-sm italic text-slate-800 leading-relaxed">&ldquo;{quote.text}&rdquo;</p>
                  <p className="text-xs text-slate-500 mt-1">{quote.annotation}</p>
                </blockquote>
              ))}
            </div>
          )}

          {/* Synthesis paragraph */}
          <div data-testid={`synthesis-${outcome.strategy_id}`} className="border-l-2 border-amber-300 pl-3">
            <p className="text-xs font-mono text-amber-600 uppercase tracking-wider mb-1.5">Synthesis</p>
            <p className="text-sm text-slate-800 leading-relaxed">{synthesis_paragraph}</p>
          </div>

          {/* Watch transcript CTA */}
          <div className="flex justify-end pt-1">
            <button
              data-testid={`watch-transcript-${outcome.strategy_id}`}
              onClick={() => onViewTranscript(outcome.strategy_id)}
              className="text-sm text-violet-600 hover:text-violet-800 font-medium transition-colors"
            >
              Watch Full Transcript →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
