import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'
import { mockSimulation } from './fixtures'

// Mock framer-motion so tests don't need full animation support
vi.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement> & { variants?: unknown; initial?: unknown; animate?: unknown; exit?: unknown; transition?: unknown }) => (
      <div {...props}>{children}</div>
    ),
  },
}))

// Mock child screens so we can test routing without their implementations
vi.mock('../components/setup/SetupScreen', () => ({
  default: ({ onRunSimulation }: { onRunSimulation: (sim: typeof mockSimulation) => void }) => (
    <div data-testid="setup-screen">
      <button onClick={() => onRunSimulation(mockSimulation)}>Run</button>
    </div>
  ),
}))

vi.mock('../components/mindviewer/MindViewer', () => ({
  default: ({ onViewReport, initialStrategyId }: { onViewReport: () => void; initialStrategyId?: string }) => (
    <div data-testid="mind-viewer" data-strategy={initialStrategyId ?? ''}>
      <button onClick={onViewReport}>View Report</button>
    </div>
  ),
}))

vi.mock('../components/report/ComparisonReport', () => ({
  default: ({ onViewTranscript, onBackToSetup }: { onViewTranscript: (id: string) => void; onBackToSetup: () => void }) => (
    <div data-testid="comparison-report">
      <button onClick={() => onViewTranscript('strategy_personal_narrative')}>Watch Transcript</button>
      <button onClick={onBackToSetup}>Back to Setup</button>
    </div>
  ),
}))

describe('App', () => {
  it('renders setup screen on mount', () => {
    render(<App />)
    expect(screen.getByTestId('setup-screen')).toBeInTheDocument()
    expect(screen.queryByTestId('mind-viewer')).not.toBeInTheDocument()
    expect(screen.queryByTestId('comparison-report')).not.toBeInTheDocument()
  })

  it('has a slate-50 background', () => {
    render(<App />)
    const root = screen.getByTestId('app-root')
    expect(root.className).toContain('bg-slate-50')
  })

  it('transitions to mind viewer after run simulation', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByText('Run'))

    expect(screen.queryByTestId('setup-screen')).not.toBeInTheDocument()
    expect(screen.getByTestId('mind-viewer')).toBeInTheDocument()
  })

  it('transitions to comparison report from mind viewer', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByText('Run'))
    await user.click(screen.getByText('View Report'))

    expect(screen.queryByTestId('mind-viewer')).not.toBeInTheDocument()
    expect(screen.getByTestId('comparison-report')).toBeInTheDocument()
  })

  it('deep-links back to mind viewer with correct strategy id', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByText('Run'))
    await user.click(screen.getByText('View Report'))
    await user.click(screen.getByText('Watch Transcript'))

    const viewer = screen.getByTestId('mind-viewer')
    expect(viewer).toBeInTheDocument()
    expect(viewer.dataset.strategy).toBe('strategy_personal_narrative')
  })

  it('navigates back to setup from report', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByText('Run'))
    await user.click(screen.getByText('View Report'))
    await user.click(screen.getByText('Back to Setup'))

    expect(screen.getByTestId('setup-screen')).toBeInTheDocument()
    expect(screen.queryByTestId('comparison-report')).not.toBeInTheDocument()
  })

  it('clears deep link strategy id when starting a new run', async () => {
    const user = userEvent.setup()
    render(<App />)

    // Navigate: setup → run → view report → watch transcript (sets deep link)
    await user.click(screen.getByText('Run'))
    await user.click(screen.getByText('View Report'))
    await user.click(screen.getByText('Watch Transcript'))

    // Should be in mindviewer with strategy deep link
    expect(screen.getByTestId('mind-viewer').dataset.strategy).toBe('strategy_personal_narrative')

    // Navigate back to report then back to setup
    await user.click(screen.getByText('View Report'))
    await user.click(screen.getByText('Back to Setup'))

    // Run a fresh simulation — deep link should be cleared
    await user.click(screen.getByText('Run'))

    expect(screen.getByTestId('mind-viewer').dataset.strategy).toBe('')
  })

  it('does not show mindviewer or report when simulation is null', () => {
    render(<App />)
    // Initial state: no simulation loaded, setup screen is shown
    expect(screen.getByTestId('setup-screen')).toBeInTheDocument()
    expect(screen.queryByTestId('mind-viewer')).not.toBeInTheDocument()
    expect(screen.queryByTestId('comparison-report')).not.toBeInTheDocument()
  })
})
