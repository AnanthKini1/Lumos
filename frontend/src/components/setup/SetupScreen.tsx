import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { SimulationOutput, PersonaProfile, TopicProfile } from '../../types/simulation'
import { loadScenario } from '../../data/loader'
import mockData from '../../data/mock_simulation.json'

interface Props {
  onRunSimulation: (simulation: SimulationOutput) => void
}

const sim = mockData as SimulationOutput
const availablePersonas: PersonaProfile[] = [sim.metadata.persona]
const availableTopics: TopicProfile[] = [sim.metadata.topic]

function CitationBadge({ text }: { text: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono bg-violet-50 text-violet-600 border border-violet-200">
      <span className="opacity-60">src:</span> {text.split('—')[0].trim()}
    </span>
  )
}

function ValuePill({ value }: { value: string }) {
  return (
    <span className="inline-block px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-600 border border-slate-200">
      {value}
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
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.99 }}
      onClick={onSelect}
      data-testid={`persona-card-${persona.id}`}
      className={[
        'w-full text-left p-4 rounded-xl border-2 transition-colors duration-150 bg-white',
        selected
          ? 'border-amber-400 shadow-md shadow-amber-100'
          : 'border-slate-200 hover:border-slate-300',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <p className="font-semibold text-slate-900">{persona.display_name}</p>
          <p className="text-sm text-slate-500">{persona.demographic_shorthand}</p>
        </div>
        {selected && (
          <span className="shrink-0 w-5 h-5 rounded-full bg-amber-400 flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-1 mb-3">
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
      initial={{ x: '100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '100%', opacity: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="fixed top-0 right-0 h-full w-[420px] bg-white border-l border-slate-200 shadow-xl overflow-y-auto z-50"
    >
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="font-semibold text-xl text-slate-900">{persona.display_name}</h2>
            <p className="text-sm text-slate-500">{persona.demographic_shorthand}</p>
          </div>
          <button
            data-testid="close-profile-panel"
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p className="text-sm italic text-slate-700 leading-relaxed mb-6 border-l-2 border-violet-200 pl-3">
          "{persona.first_person_description}"
        </p>

        <section className="mb-5">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-2">Core Values</h3>
          <div className="flex flex-wrap gap-1.5">
            {persona.core_values.map(v => <ValuePill key={v} value={v} />)}
          </div>
        </section>

        <section className="mb-5">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-2">Trust Orientation</h3>
          <div className="flex flex-wrap gap-1.5">
            {persona.trust_orientation.map(t => (
              <span key={t} className="px-2 py-0.5 rounded-full text-xs bg-sky-50 text-sky-700 border border-sky-200">{t.replace(/_/g, ' ')}</span>
            ))}
          </div>
        </section>

        <section className="mb-5">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-2">Opens Up When</h3>
          <ul className="space-y-1">
            {persona.emotional_triggers.open_when.map(t => (
              <li key={t} className="text-sm text-emerald-700 flex gap-2">
                <span className="text-emerald-400 shrink-0">↑</span>
                {t.replace(/_/g, ' ')}
              </li>
            ))}
          </ul>
        </section>

        <section className="mb-5">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-2">Gets Defensive When</h3>
          <ul className="space-y-1">
            {persona.emotional_triggers.defensive_when.map(t => (
              <li key={t} className="text-sm text-rose-600 flex gap-2">
                <span className="text-rose-400 shrink-0">↓</span>
                {t.replace(/_/g, ' ')}
              </li>
            ))}
          </ul>
        </section>

        {Object.keys(persona.predicted_behavior_under_strategies).length > 0 && (
          <section className="mb-6">
            <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-2">Predicted Responses</h3>
            <div className="space-y-2">
              {Object.entries(persona.predicted_behavior_under_strategies).map(([strategy, prediction]) => (
                <div key={strategy} className="text-sm p-2 rounded bg-slate-50 border border-slate-200">
                  <span className="font-mono text-xs text-violet-600">{strategy.replace('strategy_', '').replace(/_/g, ' ')}</span>
                  <p className="text-slate-600 mt-0.5">{prediction}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="pt-4 border-t border-slate-100">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-2">Source</h3>
          <p className="text-sm text-slate-700 mb-1">{persona.source_citation.primary_source}</p>
          {persona.source_citation.url && (
            <a
              href={persona.source_citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-violet-600 hover:text-violet-800 underline underline-offset-2"
            >
              View original research →
            </a>
          )}
          {persona.source_citation.supplementary.length > 0 && (
            <p className="text-xs text-slate-400 mt-1">Also: {persona.source_citation.supplementary.join(', ')}</p>
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
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onClick={onSelect}
      data-testid={`topic-card-${topic.id}`}
      className={[
        'w-full text-left p-4 rounded-xl border-2 transition-colors duration-150 bg-white',
        selected
          ? 'border-amber-400 shadow-md shadow-amber-100'
          : 'border-slate-200 hover:border-slate-300',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-slate-900 mb-1">{topic.display_name}</p>
          <p className="text-sm text-slate-500 line-clamp-2">{topic.context_briefing.slice(0, 130)}…</p>
        </div>
        {startingStance !== null && (
          <div className="shrink-0 text-right">
            <p className="text-xs text-slate-400 mb-0.5">Starting stance</p>
            <p className="font-mono text-lg font-semibold text-slate-800">{startingStance.toFixed(1)}<span className="text-slate-400 text-sm">/10</span></p>
          </div>
        )}
      </div>
    </motion.button>
  )
}

export default function SetupScreen({ onRunSimulation }: Props) {
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null)
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)
  const [panelPersona, setPanelPersona] = useState<PersonaProfile | null>(null)
  const [loading, setLoading] = useState(false)

  const canRun = selectedPersonaId !== null && selectedTopicId !== null

  async function handleRun() {
    if (!canRun) return
    setLoading(true)
    try {
      const sim = await loadScenario('demo_v1')
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
      <header className="border-b border-slate-200 bg-white px-8 py-5">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Lumos</h1>
          <p className="text-sm text-slate-500 mt-0.5">Internal Mind Simulator — configure your simulation</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-8 py-10 space-y-12">
        {/* Step 1: Persona */}
        <section>
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-6 h-6 rounded-full bg-amber-400 text-white text-xs font-semibold flex items-center justify-center">1</span>
              <h2 className="font-semibold text-slate-900">Select a persona</h2>
            </div>
            <p className="text-sm text-slate-500 pl-8">Each persona is grounded in published psychographic research. Click to read their full profile.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
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
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-6 h-6 rounded-full bg-amber-400 text-white text-xs font-semibold flex items-center justify-center">2</span>
              <h2 className="font-semibold text-slate-900">Select a topic</h2>
            </div>
            <p className="text-sm text-slate-500 pl-8">All persuasion strategies run automatically in parallel against the selected persona.</p>
          </div>
          <div className="space-y-3">
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

        {/* Run button */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-200">
          <p className="text-sm text-slate-400">
            {!canRun ? 'Select a persona and topic to continue' : 'Ready — all 7 strategies will run in parallel'}
          </p>
          <motion.button
            whileHover={canRun ? { scale: 1.02 } : {}}
            whileTap={canRun ? { scale: 0.98 } : {}}
            onClick={handleRun}
            disabled={!canRun || loading}
            data-testid="run-button"
            className={[
              'px-6 py-2.5 rounded-lg font-semibold text-sm transition-colors duration-150',
              canRun && !loading
                ? 'bg-amber-400 text-slate-900 hover:bg-amber-500 cursor-pointer'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed',
            ].join(' ')}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Loading…
              </span>
            ) : 'Run Simulation →'}
          </motion.button>
        </div>
      </main>

      {/* Profile side panel */}
      <AnimatePresence>
        {panelPersona && (
          <>
            <motion.div
              data-testid="panel-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setPanelPersona(null)}
              className="fixed inset-0 bg-black/10 z-40"
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
