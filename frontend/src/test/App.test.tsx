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
  default: ({ onViewReport, initialStrategyId, initialTurnNumber }: { onViewReport: () => void; initialStrategyId?: string; initialTurnNumber?: number }) => (
    <div data-testid="mind-viewer" data-strategy={initialStrategyId ?? ''} data-turn={initialTurnNumber ?? ''}>
      <button onClick={onViewReport}>View Report</button>
    </div>
  ),
}))

vi.mock('../components/report/ComparisonReport', () => ({
  default: ({ onViewTranscript, onBackToSetup }: { onViewTranscript: (id: string, turnNumber?: number) => void; onBackToSetup: () => void }) => (
    <div data-testid="comparison-report">
      <button onClick={() => onViewTranscript('strategy_personal_narrative')}>Watch Transcript</button>
      <button onClick={() => onViewTranscript('strategy_personal_narrative', 2)}>Watch Transcript Turn 2</button>
      <button onClick={onBackToSetup}>Back to Setup</button>
    </div>
  ),
}))

vi.mock('../components/shared/SourcesPanel', () => ({
  default: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
    <div data-testid="sources-panel" data-open={isOpen}>
      <button onClick={onClose}>Close Sources</button>
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

  it('has a fafafa background', () => {
    render(<App />)
    const root = screen.getByTestId('app-root')
    expect(root.className).toContain('bg-[#fafafa]')
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

  it('deep-links to mind viewer with correct turn number from quote click', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByText('Run'))
    await user.click(screen.getByText('View Report'))
    await user.click(screen.getByText('Watch Transcript Turn 2'))

    const viewer = screen.getByTestId('mind-viewer')
    expect(viewer).toBeInTheDocument()
    expect(viewer.dataset.strategy).toBe('strategy_personal_narrative')
    expect(viewer.dataset.turn).toBe('2')
  })

  it('does not show mindviewer or report when simulation is null', () => {
    render(<App />)
    // Initial state: no simulation loaded, setup screen is shown
    expect(screen.getByTestId('setup-screen')).toBeInTheDocument()
    expect(screen.queryByTestId('mind-viewer')).not.toBeInTheDocument()
    expect(screen.queryByTestId('comparison-report')).not.toBeInTheDocument()
  })

  it('shows breadcrumb navigation', () => {
    render(<App />)
    expect(screen.getByTestId('breadcrumb')).toBeInTheDocument()
  })

  it('breadcrumb highlights Setup on initial render', () => {
    render(<App />)
    const setupStep = screen.getByTestId('breadcrumb-step-setup')
    expect(setupStep.className).toContain('font-bold')
    expect(setupStep.className).toContain('underline')
  })

  it('breadcrumb highlights Mind Viewer after running simulation', async () => {
    const user = userEvent.setup({ delay: null })
    render(<App />)
    await user.click(screen.getByText('Run'))
    const mindviewerStep = screen.getByTestId('breadcrumb-step-mindviewer')
    expect(mindviewerStep.className).toContain('font-bold')
    expect(mindviewerStep.className).toContain('underline')
  })

  it('breadcrumb highlights Report after viewing report', async () => {
    const user = userEvent.setup({ delay: null })
    render(<App />)
    await user.click(screen.getByText('Run'))
    await user.click(screen.getByText('View Report'))
    const reportStep = screen.getByTestId('breadcrumb-step-report')
    expect(reportStep.className).toContain('font-bold')
    expect(reportStep.className).toContain('underline')
  })

  it('shows Sources & Methodology trigger button', () => {
    render(<App />)
    expect(screen.getByTestId('sources-trigger')).toBeInTheDocument()
  })

  it('sources panel starts closed', () => {
    render(<App />)
    expect(screen.getByTestId('sources-panel')).toHaveAttribute('data-open', 'false')
  })

  it('clicking sources trigger opens the panel', async () => {
    const user = userEvent.setup({ delay: null })
    render(<App />)
    await user.click(screen.getByTestId('sources-trigger'))
    expect(screen.getByTestId('sources-panel')).toHaveAttribute('data-open', 'true')
  })

  it('closing sources panel sets it back to closed', async () => {
    const user = userEvent.setup({ delay: null })
    render(<App />)
    await user.click(screen.getByTestId('sources-trigger'))
    await user.click(screen.getByText('Close Sources'))
    expect(screen.getByTestId('sources-panel')).toHaveAttribute('data-open', 'false')
  })
})
