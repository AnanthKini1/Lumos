import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { SimulationOutput } from './types/simulation'
import SetupScreen from './components/setup/SetupScreen'
import MindViewer from './components/mindviewer/MindViewer'
import ComparisonReport from './components/report/ComparisonReport'

type Screen = 'setup' | 'mindviewer' | 'report'

const fadeVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
  exit: { opacity: 0 },
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('setup')
  const [simulation, setSimulation] = useState<SimulationOutput | null>(null)
  const [deepLinkStrategyId, setDeepLinkStrategyId] = useState<string | null>(null)

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

  return (
    <div className="min-h-screen bg-slate-50" data-testid="app-root">
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
