import { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { SimulationOutput } from './types/simulation'
import { loadScenario } from './data/loader'
import SetupScreen from './components/setup/SetupScreen'
import MindViewer from './components/mindviewer/MindViewer'
import ComparisonReport from './components/report/ComparisonReport'
import SourcesPanel from './components/shared/SourcesPanel'
import MechanismLegend from './components/shared/MechanismLegend'

type Screen = 'setup' | 'mindviewer' | 'report'

const STEPS: { key: Screen; label: string }[] = [
  { key: 'setup',      label: 'Setup' },
  { key: 'mindviewer', label: 'Mind Viewer' },
  { key: 'report',     label: 'Report' },
]

const STEP_IDX: Record<Screen, number> = { setup: 0, mindviewer: 1, report: 2 }

const fadeVariants = {
  hidden:  { opacity: 0 },
  visible: { opacity: 1 },
  exit:    { opacity: 0 },
}

function Breadcrumb({ screen }: { screen: Screen }) {
  const current = STEP_IDX[screen]
  return (
    <nav data-testid="breadcrumb" aria-label="Steps" className="flex items-center gap-2 px-6 py-3 bg-[#fafafa] border-b-2 border-[#0f0f0f]">
      {STEPS.map((step, i) => (
        <span key={step.key} className="flex items-center gap-2">
          {i > 0 && <span className="text-[#0f0f0f] text-sm select-none">›</span>}
          <span
            data-testid={`breadcrumb-step-${step.key}`}
            className={[
              'text-sm font-mono transition-all',
              i === current
                ? 'font-bold underline text-[#0f0f0f]'
                : i < current
                  ? 'text-[#0f0f0f]'
                  : 'text-[#0f0f0f] opacity-40',
            ].join(' ')}
          >
            {step.label}
          </span>
        </span>
      ))}
    </nav>
  )
}

export default function App() {
  const [screen, setScreen]                     = useState<Screen>('setup')
  const [simulation, setSimulation]             = useState<SimulationOutput | null>(null)
  const [deepLinkStrategyId, setDeepLinkStrategyId] = useState<string | null>(null)
  const [sourcesOpen, setSourcesOpen]           = useState(false)
  const [pitchLoading, setPitchLoading]         = useState(false)

  // Pitch mode: ?pitch=1 skips setup and auto-loads demo
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('pitch') === '1') {
      setPitchLoading(true)
      loadScenario('demo_v1')
        .then(sim => {
          setSimulation(sim)
          setDeepLinkStrategyId(null)
          setScreen('mindviewer')
        })
        .finally(() => setPitchLoading(false))
    }
  }, [])

  function handleRunSimulation(sim: SimulationOutput) {
    setSimulation(sim)
    setDeepLinkStrategyId(null)
    setScreen('mindviewer')
  }

  function handleViewReport() {
    setScreen('report')
  }

  function handleViewTranscript(strategyId: string) {
    setDeepLinkStrategyId(strategyId)
    setScreen('mindviewer')
  }

  function handleBackToSetup() {
    setScreen('setup')
  }

  if (pitchLoading) {
    return (
      <div className="min-h-screen bg-[#fafafa] flex items-center justify-center" data-testid="pitch-loading">
        <div className="space-y-4 w-64">
          <div className="h-4 bg-[#0f0f0f] animate-pulse" />
          <div className="h-4 bg-[#0f0f0f] animate-pulse w-3/4" />
          <div className="h-4 bg-[#0f0f0f] animate-pulse w-1/2" />
          <p className="text-sm text-[#0f0f0f] opacity-50 text-center font-mono">Loading simulation…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#fafafa]" data-testid="app-root">
      {/* Breadcrumb nav */}
      <Breadcrumb screen={screen} />

      {/* Persistent Sources trigger */}
      <button
        data-testid="sources-trigger"
        onClick={() => setSourcesOpen(true)}
        className="fixed bottom-4 left-4 z-30 text-xs text-[#0f0f0f] underline font-mono transition-colors hover:opacity-60"
      >
        Sources &amp; Methodology
      </button>

      {/* Sources drawer */}
      <SourcesPanel
        simulation={simulation}
        isOpen={sourcesOpen}
        onClose={() => setSourcesOpen(false)}
      />

      {/* Mechanism legend overlay */}
      <MechanismLegend />

      {/* Screen transitions */}
      <AnimatePresence mode="wait">
        {screen === 'setup' && (
          <motion.div
            key="setup"
            variants={fadeVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ duration: 0.2 }}
          >
            <SetupScreen onRunSimulation={handleRunSimulation} />
          </motion.div>
        )}

        {screen === 'mindviewer' && simulation && (
          <motion.div
            key="mindviewer"
            variants={fadeVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ duration: 0.2 }}
          >
            <MindViewer
              simulation={simulation}
              initialStrategyId={deepLinkStrategyId ?? undefined}
              onViewReport={handleViewReport}
            />
          </motion.div>
        )}

        {screen === 'report' && simulation && (
          <motion.div
            key="report"
            variants={fadeVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ duration: 0.2 }}
          >
            <ComparisonReport
              simulation={simulation}
              onViewTranscript={handleViewTranscript}
              onBackToSetup={handleBackToSetup}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
