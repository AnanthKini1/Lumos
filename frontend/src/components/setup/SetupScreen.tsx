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

function CitationBadge({ text }: { text: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-mono bg-violet-50 text-violet-700 border border-violet-200">
      <span className="opacity-50 text-xs">src</span>
      <span className="opacity-30 text-xs">·</span>
      {text.split('—')[0].trim()}
    </span>
  )
}

function ValuePill({ value }: { value: string }) {
  return (
    <span className="inline-block px-3 py-1 rounded-full text-sm bg-slate-100 text-slate-700 border border-slate-200 font-medium">
      {toTitleCase(value)}
    </span>
  )
}

interface PersonaCardProps {
  persona: PersonaProfile
  selected: boolean
  onSelect: () => void
}

function PersonaCard({ persona, selected, onSelect }: PersonaCardProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.99 }}
      onClick={onSelect}
      data-testid={`persona-card-${persona.id}`}
      className={[
        'w-full text-left p-6 rounded-2xl border-2 transition-all duration-150 bg-white',
        selected
          ? 'border-purple-500 shadow-lg shadow-purple-100'
          : 'border-slate-200 hover:border-slate-300 hover:shadow-md',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <p className="font-bold text-lg text-slate-900 leading-tight">{persona.display_name}</p>
          <p className="text-base text-slate-500 mt-0.5">{persona.demographic_shorthand}</p>
        </div>
        {selected && (
          <span className="shrink-0 w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center shadow-sm">
            <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-2 mb-4">
        {persona.core_values.slice(0, 3).map(v => (
          <ValuePill key={v} value={v} />
        ))}
      </div>
      <CitationBadge text={persona.source_citation.primary_source} />
    </motion.button>
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
      className="fixed top-0 left-0 h-full w-[520px] bg-white border-r border-slate-200 shadow-2xl overflow-y-auto z-50"
    >
      <div className="p-8">
        <div className="flex items-start justify-between mb-8">
          <div>
            <h2 className="font-bold text-2xl text-slate-900 leading-tight">{persona.display_name}</h2>
            <p className="text-base text-slate-500 mt-1">{persona.demographic_shorthand}</p>
          </div>
          <button
            data-testid="close-profile-panel"
            onClick={onClose}
            className="p-2.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <blockquote className="text-base italic text-slate-700 leading-relaxed mb-8 border-l-4 border-violet-300 pl-4 bg-violet-50 py-3 pr-3 rounded-r-lg">
          "{persona.first_person_description}"
        </blockquote>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-3">Core Values</h3>
          <div className="flex flex-wrap gap-2">
            {persona.core_values.map(v => <ValuePill key={v} value={v} />)}
          </div>
        </section>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-3">Trust Orientation</h3>
          <div className="flex flex-wrap gap-2">
            {persona.trust_orientation.map(t => (
              <span key={t} className="px-3 py-1 rounded-full text-sm bg-sky-50 text-sky-700 border border-sky-200 font-medium">
                {toTitleCase(t)}
              </span>
            ))}
          </div>
        </section>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-3">Opens Up When</h3>
          <ul className="space-y-2">
            {persona.emotional_triggers.open_when.map(t => (
              <li key={t} className="text-base text-emerald-800 flex gap-2.5 items-start">
                <span className="text-emerald-500 shrink-0 mt-0.5 font-bold">↑</span>
                {toTitleCase(t)}
              </li>
            ))}
          </ul>
        </section>

        <section className="mb-6">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-3">Gets Defensive When</h3>
          <ul className="space-y-2">
            {persona.emotional_triggers.defensive_when.map(t => (
              <li key={t} className="text-base text-rose-700 flex gap-2.5 items-start">
                <span className="text-rose-400 shrink-0 mt-0.5 font-bold">↓</span>
                {toTitleCase(t)}
              </li>
            ))}
          </ul>
        </section>

        {Object.keys(persona.predicted_behavior_under_strategies).length > 0 && (
          <section className="mb-8">
            <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-3">Predicted Responses by Strategy</h3>
            <div className="space-y-3">
              {Object.entries(persona.predicted_behavior_under_strategies).map(([strategy, prediction]) => (
                <div key={strategy} className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="font-mono text-sm text-purple-700 font-semibold">
                    {toTitleCase(strategy.replace('strategy_', ''))}
                  </span>
                  <p className="text-base text-slate-600 mt-1.5 leading-snug">{prediction}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="pt-6 border-t border-slate-100">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-3">Research Source</h3>
          <p className="text-base text-slate-700 mb-2 font-medium">{persona.source_citation.primary_source}</p>
          {persona.source_citation.url && (
            <a
              href={persona.source_citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-purple-600 hover:text-purple-800 underline underline-offset-2"
            >
              View original research →
            </a>
          )}
          {persona.source_citation.supplementary.length > 0 && (
            <p className="text-sm text-slate-400 mt-2">
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
    <motion.button
      whileHover={{ scale: 1.01, y: -1 }}
      whileTap={{ scale: 0.99 }}
      onClick={onSelect}
      data-testid={`topic-card-${topic.id}`}
      className={[
        'w-full text-left p-6 rounded-2xl border-2 transition-all duration-150 bg-white',
        selected
          ? 'border-purple-500 shadow-lg shadow-purple-100'
          : 'border-slate-200 hover:border-slate-300 hover:shadow-md',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1 min-w-0">
          <p className="font-bold text-lg text-slate-900 mb-2">{topic.display_name}</p>
          <p className="text-base text-slate-500 leading-relaxed line-clamp-2">
            {topic.context_briefing.slice(0, 160)}…
          </p>
        </div>
        {startingStance !== null && (
          <div className="shrink-0 text-right bg-slate-50 rounded-xl p-3 border border-slate-100">
            <p className="text-xs text-slate-400 mb-1 font-medium uppercase tracking-wide">Starting Stance</p>
            <p className="font-mono text-2xl font-bold text-slate-800">
              {startingStance.toFixed(1)}
              <span className="text-slate-400 text-base font-normal">/10</span>
            </p>
          </div>
        )}
      </div>
    </motion.button>
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
    <div className="min-h-screen bg-slate-50" data-testid="setup-screen">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white px-10 py-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Lumos</h1>
          <p className="text-base text-slate-500 mt-1">Internal Mind Simulator — Configure Your Simulation</p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-10 py-14 space-y-16">
        {/* Step 1: Persona */}
        <section>
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <span className="w-8 h-8 rounded-full bg-purple-600 text-white text-sm font-bold flex items-center justify-center shadow-sm shadow-purple-200">
                1
              </span>
              <h2 className="text-xl font-bold text-slate-900">Select a Persona</h2>
            </div>
            <p className="text-base text-slate-500 pl-11">
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
              <span className="w-8 h-8 rounded-full bg-purple-600 text-white text-sm font-bold flex items-center justify-center shadow-sm shadow-purple-200">
                2
              </span>
              <h2 className="text-xl font-bold text-slate-900">Select a Topic</h2>
            </div>
            <p className="text-base text-slate-500 pl-11">
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
        <div className="flex items-center justify-between pt-4 border-t border-slate-200">
          <p className="text-base text-slate-400">
            {!canRun
              ? 'Select a persona and topic to continue'
              : 'Ready — All 7 strategies will run in parallel'}
          </p>
          <motion.button
            whileHover={canRun ? { scale: 1.03 } : {}}
            whileTap={canRun ? { scale: 0.97 } : {}}
            onClick={handleRun}
            disabled={!canRun || loading}
            data-testid="run-button"
            className={[
              'px-8 py-3.5 rounded-xl font-bold text-base transition-colors duration-150',
              canRun && !loading
                ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-md shadow-purple-200 cursor-pointer'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed',
            ].join(' ')}
          >
            {loading ? (
              <span className="flex items-center gap-2.5">
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Loading…
              </span>
            ) : 'Run Simulation →'}
          </motion.button>
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
              className="fixed inset-0 bg-black/15 backdrop-blur-[1px] z-40"
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
