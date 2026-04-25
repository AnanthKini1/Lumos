import { useState } from 'react'
import type { StrategyOutcome, VerdictCategory } from '../../types/simulation'

const VERDICT_LABEL: Record<VerdictCategory, string> = {
  GENUINE_BELIEF_SHIFT: 'GENUINE SHIFT',
  PARTIAL_SHIFT:        'PARTIAL SHIFT',
  SURFACE_COMPLIANCE:   'SURFACE COMPLIANCE',
  BACKFIRE:             'BACKFIRE',
  NO_MOVEMENT:          'NO MOVEMENT',
}

interface Props {
  outcome: StrategyOutcome
  strategyDisplayName: string
  onViewTranscript: (strategyId: string) => void
}

function ScoreBar({ value }: { value: number }) {
  const pct = Math.min(100, (value / 10) * 100)
  return (
    <div className="h-1.5 bg-[#0f0f0f] bg-opacity-10 w-full">
      <div className="h-full bg-[#0f0f0f] transition-all" style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function StrategyCard({ outcome, strategyDisplayName, onViewTranscript }: Props) {
  const [expanded, setExpanded] = useState(false)
  const { verdict, verdict_reasoning, cognitive_scores, standout_quotes, synthesis_paragraph } = outcome

  const isBackfire = verdict === 'BACKFIRE'
  const hasIdentityThreats = cognitive_scores.identity_threats_triggered > 0

  return (
    <div
      data-testid={`strategy-card-${outcome.strategy_id}`}
      className={[
        'bg-[#fafafa] overflow-hidden',
        isBackfire ? 'border-2 border-[#dc2626]' : 'border-2 border-[#0f0f0f]',
      ].join(' ')}
    >
      {/* Collapsed header */}
      <button
        data-testid={`strategy-card-toggle-${outcome.strategy_id}`}
        onClick={() => setExpanded(e => !e)}
        aria-expanded={expanded}
        className="group w-full px-5 py-5 flex items-start gap-3 text-left hover:bg-[#0f0f0f] transition-colors"
      >
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <span className="font-bold font-serif text-xl text-[#0f0f0f] group-hover:text-[#fafafa]">{strategyDisplayName}</span>
            <span
              data-testid={`card-verdict-badge-${outcome.strategy_id}`}
              className="font-mono text-xs font-bold text-[#0f0f0f] group-hover:text-[#fafafa] uppercase"
            >
              {VERDICT_LABEL[verdict]}
            </span>
            {isBackfire && hasIdentityThreats && (
              <span
                data-testid={`identity-defense-badge-${outcome.strategy_id}`}
                className="font-mono text-xs font-bold text-[#dc2626] uppercase"
              >
                ⚠ Identity defense triggered
              </span>
            )}
          </div>
          <p className="font-serif text-base text-[#0f0f0f] group-hover:text-[#fafafa] opacity-60 leading-snug">{verdict_reasoning}</p>
        </div>
        <span
          className="font-mono text-xl font-bold text-[#0f0f0f] group-hover:text-[#fafafa] shrink-0 mt-0.5"
          aria-hidden="true"
        >
          {expanded ? '−' : '+'}
        </span>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div
          data-testid={`strategy-card-body-${outcome.strategy_id}`}
          className="px-5 pb-5 space-y-6 border-t-2 border-[#0f0f0f]"
        >
          {/* Cognitive score mini-badges */}
          <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {([
              { label: 'Engagement',          value: cognitive_scores.average_engagement_depth },
              { label: 'Motivated Reasoning', value: cognitive_scores.motivated_reasoning_intensity },
              { label: 'Ambivalence',         value: cognitive_scores.ambivalence_presence },
              { label: 'Gap Score',           value: cognitive_scores.public_private_gap_score },
            ] as const).map(({ label, value }) => (
              <div key={label} className="border border-[#0f0f0f] px-3 py-2.5 space-y-1.5">
                <p className="font-mono text-xs text-[#0f0f0f] opacity-60 uppercase tracking-wide leading-tight">{label}</p>
                <ScoreBar value={value} />
                <p className="font-mono text-xs font-bold text-[#0f0f0f]">{value.toFixed(1)}</p>
              </div>
            ))}
          </div>

          {/* Standout quotes */}
          {standout_quotes.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-mono font-bold text-[#0f0f0f] uppercase tracking-wider">Standout Moments</p>
              {standout_quotes.slice(0, 3).map((quote, i) => (
                <blockquote
                  key={i}
                  data-testid={`quote-${i}-${outcome.strategy_id}`}
                  className="pt-4 border-t-2 border-[#0f0f0f]"
                >
                  <div className="flex gap-3 mb-2">
                    <span className="font-mono text-xs font-bold text-[#0f0f0f] opacity-30 leading-none tabular-nums">{String(i + 1).padStart(2, '0')}</span>
                    <div className="flex gap-2">
                      <span className="text-xs font-mono border border-[#0f0f0f] px-1.5 py-0.5 text-[#0f0f0f]">
                        Turn {quote.turn}
                      </span>
                      <span className="text-xs font-mono border border-[#0f0f0f] px-1.5 py-0.5 text-[#0f0f0f] uppercase">
                        {quote.type}
                      </span>
                    </div>
                  </div>
                  <p className="font-serif text-base italic text-[#0f0f0f] leading-relaxed">&ldquo;{quote.text}&rdquo;</p>
                  <p className="font-mono text-xs text-[#0f0f0f] opacity-50 mt-1">{quote.annotation}</p>
                </blockquote>
              ))}
            </div>
          )}

          {/* Synthesis paragraph */}
          <div data-testid={`synthesis-${outcome.strategy_id}`} className="pt-4 border-t-2 border-[#0f0f0f]">
            <p className="text-xs font-mono font-bold text-[#0f0f0f] uppercase tracking-wider mb-2">Synthesis</p>
            <p className="font-serif text-base text-[#0f0f0f] leading-relaxed">{synthesis_paragraph}</p>
          </div>

          {/* Watch transcript CTA */}
          <div className="flex justify-end pt-1">
            <button
              data-testid={`watch-transcript-${outcome.strategy_id}`}
              onClick={() => onViewTranscript(outcome.strategy_id)}
              className="font-mono text-sm font-bold text-[#0f0f0f] underline hover:opacity-60 transition-opacity"
            >
              Watch Full Transcript →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
