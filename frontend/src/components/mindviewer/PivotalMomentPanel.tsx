import { motion, AnimatePresence } from 'framer-motion'
import type { ConversationTurn } from '../../types/simulation'
import mechanisms from '../../data/cognitive_mechanisms.json'

const CATEGORY_COLOR: Record<string, string> = {
  backfire:           '#dc2626',
  genuine_persuasion: '#16a34a',
  surface_mechanism:  '#d97706',
}

interface Props {
  turn: ConversationTurn | null
  onClose: () => void
  personaDisplayName: string
}

function findMechanism(id: string) {
  return mechanisms.find(m => m.id === id) ?? null
}

export default function PivotalMomentPanel({ turn, onClose, personaDisplayName }: Props) {
  return (
    <AnimatePresence>
      {turn && (
        <motion.div
          key={turn.turn_number}
          data-testid="pivotal-moment-panel"
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          className="absolute top-0 right-0 h-full w-full max-w-[480px] bg-[#fafafa] border-l-2 border-[#0f0f0f] z-30 flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="shrink-0 flex items-center justify-between px-5 py-3 border-b-2 border-[#0f0f0f]">
            <span className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 font-bold">
              Turn {turn.turn_number} — Pivotal Moment
            </span>
            <button
              data-testid="pivotal-panel-close"
              onClick={onClose}
              className="border-2 border-[#0f0f0f] px-3 py-1 font-mono text-sm hover:bg-[#0f0f0f] hover:text-[#fafafa] transition-colors"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-6 space-y-7">
            <StanceDelta turn={turn} />
            <PersuaderPhrase turn={turn} />
            <InternalMonologue turn={turn} personaDisplayName={personaDisplayName} />
            <MechanismSection turn={turn} />
            <CognitiveScores turn={turn} />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function StanceDelta({ turn }: { turn: ConversationTurn }) {
  const delta = turn.stance_delta ?? 0
  const category = turn.color_category ?? ''
  const color = CATEGORY_COLOR[category] ?? '#0f0f0f'
  const sign = delta > 0 ? '+' : ''
  const direction = delta < 0 ? '↓' : delta > 0 ? '↑' : '→'

  return (
    <div data-testid="pivotal-stance-delta">
      <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-1">Private Stance Shift</p>
      <p className="font-mono font-bold text-3xl" style={{ color }}>
        {direction} {sign}{delta.toFixed(1)} points
      </p>
    </div>
  )
}

function PersuaderPhrase({ turn }: { turn: ConversationTurn }) {
  return (
    <div data-testid="pivotal-persuader-phrase">
      <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-2">Persuader Said</p>
      <blockquote className="border-l-4 border-[#0f0f0f] pl-4 font-serif text-base italic leading-relaxed text-[#0f0f0f]">
        {turn.persuader_message}
      </blockquote>
    </div>
  )
}

function InternalMonologue({ turn, personaDisplayName }: { turn: ConversationTurn; personaDisplayName: string }) {
  return (
    <div data-testid="pivotal-internal-monologue">
      <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-2">
        {personaDisplayName}'s Internal Monologue
      </p>
      <div className="bg-[#0f0f0f] text-[#fafafa] p-4 font-serif text-base italic leading-relaxed">
        {turn.persona_output.internal_monologue}
      </div>
    </div>
  )
}

function MechanismSection({ turn }: { turn: ConversationTurn }) {
  const mc = turn.mechanism_classification
  if (!mc) return null

  const mechanism = findMechanism(mc.primary_mechanism_id)
  const category = mc.color_category
  const color = CATEGORY_COLOR[category] ?? '#0f0f0f'
  const categoryLabel = category.replace(/_/g, ' ').toUpperCase()

  return (
    <div data-testid="pivotal-mechanism">
      <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-2">Cognitive Mechanism</p>

      {mechanism ? (
        <div className="border-2 border-[#0f0f0f] p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <p className="font-serif font-bold text-xl text-[#0f0f0f] leading-tight">{mechanism.display_name}</p>
            <span className="shrink-0 font-mono text-xs font-bold uppercase" style={{ color }}>
              {categoryLabel}
            </span>
          </div>
          <p className="font-mono text-xs text-[#0f0f0f] opacity-60">{mechanism.framework}</p>
          <a
            href={mechanism.citation_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs underline text-[#0f0f0f] opacity-50 hover:opacity-100 block"
          >
            {mechanism.citation}
          </a>
        </div>
      ) : (
        <p className="font-mono text-xs text-[#0f0f0f] opacity-50">
          {mc.primary_mechanism_id.replace(/^mechanism_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
        </p>
      )}

      <p className="font-serif text-sm leading-relaxed text-[#0f0f0f] mt-3">{mc.explanation}</p>

      {mc.evidence_quotes.length > 0 && (
        <div className="mt-3 space-y-2">
          {mc.evidence_quotes.map((q, i) => (
            <blockquote
              key={i}
              className="border-l-2 pl-2 font-serif text-sm italic text-[#0f0f0f] opacity-70"
              style={{ borderColor: color }}
            >
              "{q}"
            </blockquote>
          ))}
        </div>
      )}
    </div>
  )
}

function CognitiveScores({ turn }: { turn: ConversationTurn }) {
  const scores = turn.per_turn_cognitive_scores
  if (!scores || Object.keys(scores).length === 0) return null

  return (
    <div data-testid="pivotal-cognitive-scores">
      <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 mb-2">Per-Turn Scores</p>
      <div className="border-2 border-[#0f0f0f] divide-y-2 divide-[#0f0f0f]">
        {Object.entries(scores).map(([dim, score]) => (
          <div key={dim} className="flex items-center justify-between px-4 py-2">
            <span className="font-mono text-xs text-[#0f0f0f] capitalize">{dim.replace(/_/g, ' ')}</span>
            <span className="font-mono text-xs font-bold text-[#0f0f0f]">{score}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
