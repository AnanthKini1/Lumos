import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { SimulationOutput, PersonaProfile, TopicProfile } from '../../types/simulation'
import { loadScenario, loadCatalog } from '../../data/loader'

interface Props {
  onRunSimulation: (simulation: SimulationOutput) => void
}

function toTitleCase(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

interface PersonaCardProps {
  persona: PersonaProfile
  selected: boolean
  onSelect: () => void
}

function PersonaCard({ persona, selected, onSelect }: PersonaCardProps) {
  return (
    <button
      onClick={onSelect}
      data-testid={`persona-card-${persona.id}`}
      className={[
        'w-full text-left p-6 border-2 transition-colors duration-150',
        selected
          ? 'border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]'
          : 'border-[#0f0f0f] bg-white text-[#0f0f0f] hover:bg-[#f0f0f0]',
      ].join(' ')}
    >
      <p className="font-bold text-xl font-serif leading-tight mb-1">{persona.display_name}</p>
      <p className="text-sm font-mono mb-3 opacity-70">{persona.demographic_shorthand}</p>
      <p className="text-sm font-serif mb-3">
        {persona.core_values.slice(0, 3).map((v, i) => (
          <span key={v}>{i > 0 && <span className="mx-1 opacity-40">·</span>}<span>{toTitleCase(v)}</span></span>
        ))}
      </p>
      <span className={[
        'inline-block font-mono text-xs border px-1.5 py-0.5',
        selected ? 'border-[#fafafa] text-[#fafafa]' : 'border-[#0f0f0f] text-[#0f0f0f]',
      ].join(' ')}>
        {persona.source_citation.primary_source.split('—')[0].trim()}
      </span>
    </button>
  )
}

interface ProfilePanelProps {
  persona: PersonaProfile
  onClose: () => void
}

function ProfilePanel({ persona, onClose }: ProfilePanelProps) {
  return (
    <motion.div
      data-testid="profile-panel"
      initial={{ x: '-100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '-100%', opacity: 0 }}
      transition={{ type: 'spring', stiffness: 320, damping: 32 }}
      className="fixed top-0 left-0 h-full w-[520px] bg-[#fafafa] border-r-2 border-[#0f0f0f] overflow-y-auto z-50"
    >
      <div className="p-8">
        <div className="flex items-start justify-between mb-8">
          <div>
            <h2 className="font-bold text-3xl font-serif text-[#0f0f0f] leading-tight">{persona.display_name}</h2>
            <p className="text-sm font-mono text-[#0f0f0f] opacity-60 mt-1">{persona.demographic_shorthand}</p>
          </div>
          <button
            data-testid="close-profile-panel"
            onClick={onClose}
            className="border-2 border-[#0f0f0f] px-3 py-1 font-mono text-sm text-[#0f0f0f] hover:bg-[#0f0f0f] hover:text-[#fafafa] transition-colors"
          >
            ✕
          </button>
        </div>

        <blockquote className="text-lg italic font-serif text-[#0f0f0f] leading-relaxed mb-8 border-l-4 border-[#0f0f0f] pl-4">
          "{persona.first_person_description}"
        </blockquote>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-[#0f0f0f] opacity-50 uppercase tracking-widest mb-2 border-b border-[#0f0f0f] border-opacity-20 pb-1">Core Values</h3>
          <p className="font-serif text-base text-[#0f0f0f]">
            {persona.core_values.map(toTitleCase).join(' · ')}
          </p>
        </section>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-[#0f0f0f] opacity-50 uppercase tracking-widest mb-2 border-b border-[#0f0f0f] border-opacity-20 pb-1">Trust Orientation</h3>
          <p className="font-serif text-base text-[#0f0f0f]">
            {persona.trust_orientation.map(toTitleCase).join(', ')}
          </p>
        </section>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-[#0f0f0f] opacity-50 uppercase tracking-widest mb-2 border-b border-[#0f0f0f] border-opacity-20 pb-1">Opens Up When</h3>
          <ul className="space-y-1">
            {persona.emotional_triggers.open_when.map(t => (
              <li key={t} className="font-serif text-base text-[#0f0f0f] flex gap-2 items-start">
                <span className="font-mono shrink-0">↑</span>
                {toTitleCase(t)}
              </li>
            ))}
          </ul>
        </section>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-[#0f0f0f] opacity-50 uppercase tracking-widest mb-2 border-b border-[#0f0f0f] border-opacity-20 pb-1">Gets Defensive When</h3>
          <ul className="space-y-1">
            {persona.emotional_triggers.defensive_when.map(t => (
              <li key={t} className="font-serif text-base text-[#0f0f0f] flex gap-2 items-start">
                <span className="font-mono shrink-0">↓</span>
                {toTitleCase(t)}
              </li>
            ))}
          </ul>
        </section>

        {Object.keys(persona.predicted_behavior_under_strategies).length > 0 && (
          <section className="mb-8">
            <h3 className="text-xs font-mono text-[#0f0f0f] opacity-50 uppercase tracking-widest mb-2 border-b border-[#0f0f0f] border-opacity-20 pb-1">Predicted Responses by Strategy</h3>
            <div className="space-y-3">
              {Object.entries(persona.predicted_behavior_under_strategies).map(([strategy, prediction]) => (
                <div key={strategy} className="p-4 border-2 border-[#0f0f0f]">
                  <span className="font-mono text-sm font-bold text-[#0f0f0f] uppercase">
                    {toTitleCase(strategy.replace('strategy_', ''))}
                  </span>
                  <p className="font-serif text-base text-[#0f0f0f] mt-1.5 leading-snug">{prediction}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="pt-6 border-t-2 border-[#0f0f0f]">
          <h3 className="text-xs font-mono text-[#0f0f0f] opacity-50 uppercase tracking-widest mb-2">Research Source</h3>
          <p className="font-serif text-base text-[#0f0f0f] mb-2 font-bold">{persona.source_citation.primary_source}</p>
          {persona.source_citation.url && (
            <a
              href={persona.source_citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-sm text-[#0f0f0f] underline font-bold"
            >
              View original research →
            </a>
          )}
          {persona.source_citation.supplementary.length > 0 && (
            <p className="font-mono text-xs text-[#0f0f0f] opacity-50 mt-2">
              Also informed by: {persona.source_citation.supplementary.join(', ')}
            </p>
          )}
        </section>
      </div>
    </motion.div>
  )
}

interface TopicCardProps {
  topic: TopicProfile
  selectedPersonaId: string | null
  selected: boolean
  onSelect: () => void
}

function TopicCard({ topic, selectedPersonaId, selected, onSelect }: TopicCardProps) {
  const startingStance = selectedPersonaId ? topic.predicted_starting_stances[selectedPersonaId] : null

  return (
    <button
      onClick={onSelect}
      data-testid={`topic-card-${topic.id}`}
      className={[
        'w-full text-left p-6 border-2 transition-colors duration-150',
        selected
          ? 'border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa]'
          : 'border-[#0f0f0f] bg-white text-[#0f0f0f] hover:bg-[#f0f0f0]',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1 min-w-0">
          <p className="font-bold text-xl font-serif mb-2">{topic.display_name}</p>
          <p className="font-serif text-base leading-relaxed opacity-70 line-clamp-2">
            {topic.context_briefing.slice(0, 160)}…
          </p>
        </div>
        {startingStance !== null && (
          <div className={[
            'shrink-0 text-right border-2 p-3',
            selected ? 'border-[#fafafa]' : 'border-[#0f0f0f]',
          ].join(' ')}>
            <p className="text-xs font-mono uppercase tracking-wide opacity-60 mb-1">Starting Stance</p>
            <p className="font-mono text-2xl font-bold">
              {startingStance.toFixed(1)}
              <span className="text-base font-normal opacity-50">/10</span>
            </p>
          </div>
        )}
      </div>
    </button>
  )
}

export default function SetupScreen({ onRunSimulation }: Props) {
  const [availablePersonas, setAvailablePersonas] = useState<PersonaProfile[]>([])
  const [availableTopics, setAvailableTopics] = useState<TopicProfile[]>([])
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null)
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)
  const [panelPersona, setPanelPersona] = useState<PersonaProfile | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadCatalog().then(catalog => {
      setAvailablePersonas(catalog.personas)
      setAvailableTopics(catalog.topics)
    })
  }, [])

  const canRun = selectedPersonaId !== null && selectedTopicId !== null

  async function handleRun() {
    if (!selectedPersonaId || !selectedTopicId) return
    setLoading(true)
    try {
      const scenarioId = `${selectedPersonaId}__${selectedTopicId}`
      const sim = await loadScenario(scenarioId)
      onRunSimulation(sim)
    } finally {
      setLoading(false)
    }
  }

  function handlePersonaClick(persona: PersonaProfile) {
    setSelectedPersonaId(persona.id)
    setPanelPersona(persona)
  }

  return (
    <div className="min-h-screen bg-[#fafafa]" data-testid="setup-screen">
      {/* Header */}
      <header className="border-b-2 border-[#0f0f0f] bg-[#fafafa] px-10 py-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-4xl font-bold font-serif tracking-tight text-[#0f0f0f]">Lumos</h1>
          <p className="font-mono text-sm text-[#0f0f0f] opacity-60 mt-1">Internal Mind Simulator — Configure Your Simulation</p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-10 py-14 space-y-16">
        {/* Step 1: Persona */}
        <section>
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <span className="w-8 h-8 border-2 border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa] text-sm font-bold font-mono flex items-center justify-center">
                1
              </span>
              <h2 className="text-2xl font-bold font-serif text-[#0f0f0f]">Select a Persona</h2>
            </div>
            <p className="font-serif text-base text-[#0f0f0f] opacity-60 pl-11">
              Each persona is grounded in published psychographic research. Click any card to read their full profile.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {availablePersonas.map(persona => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                selected={selectedPersonaId === persona.id}
                onSelect={() => handlePersonaClick(persona)}
              />
            ))}
          </div>
        </section>

        {/* Step 2: Topic */}
        <section>
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <span className="w-8 h-8 border-2 border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa] text-sm font-bold font-mono flex items-center justify-center">
                2
              </span>
              <h2 className="text-2xl font-bold font-serif text-[#0f0f0f]">Select a Topic</h2>
            </div>
            <p className="font-serif text-base text-[#0f0f0f] opacity-60 pl-11">
              All persuasion strategies run automatically in parallel against the selected persona.
            </p>
          </div>
          <div className="space-y-4">
            {availableTopics.map(topic => (
              <TopicCard
                key={topic.id}
                topic={topic}
                selectedPersonaId={selectedPersonaId}
                selected={selectedTopicId === topic.id}
                onSelect={() => setSelectedTopicId(topic.id)}
              />
            ))}
          </div>
        </section>

        {/* Run */}
        <div className="flex items-center justify-between pt-4 border-t-2 border-[#0f0f0f]">
          <p className="font-mono text-sm text-[#0f0f0f] opacity-50">
            {!canRun
              ? 'Select a persona and topic to continue'
              : 'Ready — All 7 strategies will run in parallel'}
          </p>
          <button
            onClick={handleRun}
            disabled={!canRun || loading}
            data-testid="run-button"
            className={[
              'px-8 py-3.5 font-bold font-serif text-lg transition-colors duration-150 border-2',
              canRun && !loading
                ? 'border-[#0f0f0f] bg-[#0f0f0f] text-[#fafafa] hover:bg-[#333333] cursor-pointer'
                : 'border-[#0f0f0f] bg-transparent text-[#0f0f0f] opacity-30 cursor-not-allowed',
            ].join(' ')}
          >
            {loading ? (
              <span className="flex items-center gap-2.5 font-mono">
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Loading…
              </span>
            ) : 'Run Simulation →'}
          </button>
        </div>
      </main>

      {/* Profile side panel — slides from LEFT */}
      <AnimatePresence>
        {panelPersona && (
          <>
            <motion.div
              data-testid="panel-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setPanelPersona(null)}
              className="fixed inset-0 bg-black/20 z-40"
            />
            <ProfilePanel
              persona={panelPersona}
              onClose={() => setPanelPersona(null)}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
