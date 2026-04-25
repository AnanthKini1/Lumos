import type { SimulationOutput } from '../../types/simulation'
import strategiesData from '../../data/persuasion_strategies.json'

interface StrategyEntry {
  id: string
  name: string
  citation: {
    author: string
    work: string
    year: number
    url?: string
    key_empirical_anchor: string
  }
}

const STRATEGIES = strategiesData.strategies as StrategyEntry[]

interface Props {
  simulation: SimulationOutput | null
  isOpen: boolean
  onClose: () => void
}

export default function SourcesPanel({ simulation, isOpen, onClose }: Props) {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          data-testid="sources-backdrop"
          className="fixed inset-0 bg-black/20 z-40"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        data-testid="sources-panel"
        role="dialog"
        aria-label="Sources & Methodology"
        className={[
          'fixed top-0 right-0 h-full w-full max-w-[480px] bg-[#fafafa] border-l-2 border-[#0f0f0f] z-50',
          'flex flex-col transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
      >
        {/* Drawer header */}
        <div className="shrink-0 flex items-center justify-between px-6 py-4 border-b-2 border-[#0f0f0f]">
          <h2 className="font-bold font-serif text-xl text-[#0f0f0f]">Sources &amp; Methodology</h2>
          <button
            data-testid="sources-close-btn"
            onClick={onClose}
            aria-label="Close sources panel"
            className="border-2 border-[#0f0f0f] px-3 py-1 font-mono text-sm text-[#0f0f0f] hover:bg-[#0f0f0f] hover:text-[#fafafa] transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">

          {/* Personas section */}
          {simulation && (
            <section data-testid="sources-personas-section">
              <h3 className="text-xs font-mono text-[#0f0f0f] opacity-40 uppercase tracking-widest border-b-2 border-[#0f0f0f] pb-1 mb-4">Personas</h3>
              <div className="space-y-3">
                <div className="border-2 border-[#0f0f0f] p-4">
                  <p className="font-bold font-serif text-base text-[#0f0f0f] mb-0.5">{simulation.metadata.persona.display_name}</p>
                  <p className="font-mono text-xs text-[#0f0f0f] opacity-50 mb-2">{simulation.metadata.persona.demographic_shorthand}</p>
                  <p className="font-serif text-sm text-[#0f0f0f] mb-2">{simulation.metadata.persona.source_citation.primary_source}</p>
                  {simulation.metadata.persona.source_citation.url && (
                    <a
                      href={simulation.metadata.persona.source_citation.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid="persona-citation-link"
                      className="font-mono text-xs text-[#0f0f0f] underline font-bold hover:opacity-60 transition-opacity"
                    >
                      View source →
                    </a>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* Persuasion strategies section */}
          <section data-testid="sources-strategies-section">
            <h3 className="text-xs font-mono text-[#0f0f0f] opacity-40 uppercase tracking-widest border-b-2 border-[#0f0f0f] pb-1 mb-4">Persuasion Strategies</h3>
            <div className="space-y-3">
              {STRATEGIES.map(strategy => (
                <div
                  key={strategy.id}
                  data-testid={`sources-strategy-${strategy.id}`}
                  className="border-2 border-[#0f0f0f] p-4"
                >
                  <p className="font-bold font-serif text-base text-[#0f0f0f] mb-0.5">{strategy.name}</p>
                  <p className="font-mono text-xs text-[#0f0f0f] opacity-50 mb-1">
                    {strategy.citation.author} — <em>{strategy.citation.work}</em> ({strategy.citation.year})
                  </p>
                  <p className="font-serif text-sm text-[#0f0f0f] opacity-70 leading-relaxed mb-2">{strategy.citation.key_empirical_anchor}</p>
                  {strategy.citation.url && (
                    <a
                      href={strategy.citation.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-xs text-[#0f0f0f] underline font-bold hover:opacity-60 transition-opacity"
                    >
                      View source →
                    </a>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Measurement methodology section */}
          <section data-testid="sources-methodology-section">
            <h3 className="text-xs font-mono text-[#0f0f0f] opacity-40 uppercase tracking-widest border-b-2 border-[#0f0f0f] pb-1 mb-4">Measurement Methodology</h3>
            <div className="space-y-4 font-serif text-base text-[#0f0f0f] leading-relaxed">
              <div>
                <p className="font-bold mb-1">Public vs. Private Stance Gap</p>
                <p className="opacity-70">Each turn, the persona agent produces both a public response and a private stance score (0–10). The gap between them is the primary signal — a widening gap indicates surface compliance, where the persona says one thing and thinks another.</p>
              </div>
              <div>
                <p className="font-bold mb-1">Identity Threat Detection</p>
                <p className="opacity-70">The persona agent flags when a persuasive move threatens a core identity value. Identity-protective cognition causes the persona to harden their position rather than move — a key mechanism behind backfire effects.</p>
              </div>
              <div>
                <p className="font-bold mb-1">Motivated Reasoning Intensity</p>
                <p className="opacity-70">Scores (0–10) how actively the persona is generating counter-arguments and rejecting incoming information, rather than evaluating it neutrally.</p>
              </div>
              <div>
                <p className="font-bold mb-1">Engagement Depth</p>
                <p className="opacity-70">Scores how substantively the persona is engaging with the argument's content — as opposed to deflecting, changing the subject, or responding performatively.</p>
              </div>
              <div>
                <p className="font-bold mb-1">Ambivalence</p>
                <p className="opacity-70">Scores internal conflict — the degree to which the persona holds simultaneously positive and negative associations with the topic. High ambivalence is a prerequisite for genuine belief shift.</p>
              </div>
              <div>
                <p className="font-bold mb-1">Memory Residue</p>
                <p className="opacity-70">Each turn, the persona agent produces a memory note — the single most salient thing to carry forward. These accumulate and influence subsequent responses, modeling how conversations compound.</p>
              </div>
              <div>
                <p className="font-bold mb-1">Persistence (Cooling-Off)</p>
                <p className="opacity-70">After the conversation ends, the persona reflects independently. If their private stance after cooling-off is within 1.0 of their end-of-conversation stance, the change is classified as "held." Larger regressions indicate surface compliance or motivated reasoning.</p>
              </div>
            </div>
          </section>

          {/* Validation note */}
          {simulation?.validation_note && (
            <section data-testid="sources-validation-section">
              <h3 className="text-xs font-mono text-[#0f0f0f] opacity-40 uppercase tracking-widest border-b-2 border-[#0f0f0f] pb-1 mb-3">Validation</h3>
              <p className="font-serif text-base text-[#0f0f0f] italic opacity-70 leading-relaxed">{simulation.validation_note}</p>
            </section>
          )}
        </div>
      </div>
    </>
  )
}
