import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MindViewer, { strategyDisplayName } from '../components/mindviewer/MindViewer'
import { mockSimulation } from './fixtures'

vi.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, className, 'data-testid': testId, ...rest }: React.HTMLAttributes<HTMLDivElement> & { 'data-testid'?: string; initial?: unknown; animate?: unknown; exit?: unknown; transition?: unknown }) => (
      <div className={className} data-testid={testId} {...rest}>{children}</div>
    ),
    span: ({ children, className, layoutId: _l, ...rest }: React.HTMLAttributes<HTMLSpanElement> & { layoutId?: string }) => (
      <span className={className} {...rest}>{children}</span>
    ),
  },
}))

vi.mock('../components/mindviewer/PublicConversation', () => ({
  default: ({ currentTurn, personaDisplayName }: { turns: unknown[]; currentTurn: number; strategyDisplayName: string; personaDisplayName: string }) => (
    <div data-testid="public-conversation" data-turn={currentTurn} data-persona={personaDisplayName} />
  ),
}))

vi.mock('../components/mindviewer/InternalMind', () => ({
  default: ({ turnNumber, priorMemoryNotes }: { turnOutput: unknown; priorMemoryNotes: string[]; turnNumber: number; previousPrivateStance?: number }) => (
    <div data-testid="internal-mind" data-turn={turnNumber} data-memories={priorMemoryNotes.length} />
  ),
}))

const mockOnViewReport = vi.fn()
// userEvent with no delays — safe to use regardless of fake/real timer state
const user = userEvent.setup({ delay: null })

beforeEach(() => {
  mockOnViewReport.mockClear()
})

describe('strategyDisplayName helper', () => {
  it('strips strategy_ prefix and title-cases', () => {
    expect(strategyDisplayName('strategy_personal_narrative')).toBe('Personal Narrative')
    expect(strategyDisplayName('strategy_authority_expert')).toBe('Authority Expert')
  })

  it('handles ids without the prefix', () => {
    expect(strategyDisplayName('social_proof')).toBe('Social Proof')
  })
})

describe('MindViewer', () => {
  it('renders the mind viewer container', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('mind-viewer')).toBeInTheDocument()
  })

  it('shows persona name and topic in header', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByText('Karen M.')).toBeInTheDocument()
    expect(screen.getByText('Should companies require return-to-office?')).toBeInTheDocument()
  })

  it('renders one tab per strategy outcome', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('strategy-tab-strategy_personal_narrative')).toBeInTheDocument()
    expect(screen.getByTestId('strategy-tab-strategy_authority_expert')).toBeInTheDocument()
  })

  it('shows strategy display names in tabs', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByText('Personal Narrative')).toBeInTheDocument()
    expect(screen.getByText('Authority Expert')).toBeInTheDocument()
  })

  it('tabs do not show verdict abbreviations (verdict is revealed only in the report)', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.queryByText('[GEN]')).not.toBeInTheDocument()
    expect(screen.queryByText('[BCK]')).not.toBeInTheDocument()
  })

  it('first tab is active by default', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('strategy-tab-strategy_personal_narrative')).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByTestId('strategy-tab-strategy_authority_expert')).toHaveAttribute('aria-selected', 'false')
  })

  it('activates the correct tab from initialStrategyId', () => {
    render(
      <MindViewer
        simulation={mockSimulation}
        initialStrategyId="strategy_authority_expert"
        onViewReport={mockOnViewReport}
      />
    )
    expect(screen.getByTestId('strategy-tab-strategy_authority_expert')).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByTestId('strategy-tab-strategy_personal_narrative')).toHaveAttribute('aria-selected', 'false')
  })

  it('renders both PublicConversation and InternalMind panels', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('public-conversation')).toBeInTheDocument()
    expect(screen.getByTestId('internal-mind')).toBeInTheDocument()
  })

  it('shows Turn 1 / 2 on initial render (fixture has 2 turns)', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('turn-label')).toHaveTextContent('Turn 1 / 2')
  })

  it('prev button is disabled on first turn', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('prev-turn-btn')).toBeDisabled()
  })

  it('next button is enabled on first turn', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('next-turn-btn')).not.toBeDisabled()
  })

  it('next button advances the turn', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('next-turn-btn'))
    expect(screen.getByTestId('turn-label')).toHaveTextContent('Turn 2 / 2')
  })

  it('next button is disabled on last turn', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('next-turn-btn'))
    expect(screen.getByTestId('next-turn-btn')).toBeDisabled()
  })

  it('prev button is enabled after advancing', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('next-turn-btn'))
    expect(screen.getByTestId('prev-turn-btn')).not.toBeDisabled()
  })

  it('prev button goes back a turn', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('next-turn-btn'))
    await user.click(screen.getByTestId('prev-turn-btn'))
    expect(screen.getByTestId('turn-label')).toHaveTextContent('Turn 1 / 2')
  })

  it('play button shows Pause label while playing', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('play-pause-btn'))
    expect(screen.getByTestId('play-pause-btn')).toHaveTextContent('Pause')
  })

  it('clicking pause restores Play label', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('play-pause-btn'))
    await user.click(screen.getByTestId('play-pause-btn'))
    expect(screen.getByTestId('play-pause-btn')).toHaveTextContent('Play')
  })

  it('play auto-advances turn via fake timer', () => {
    vi.useFakeTimers()
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)

    act(() => { fireEvent.click(screen.getByTestId('play-pause-btn')) })
    act(() => { vi.advanceTimersByTime(2500) })

    expect(screen.getByTestId('turn-label')).toHaveTextContent('Turn 2 / 2')
    vi.useRealTimers()
  })

  it('play stops automatically at last turn', () => {
    vi.useFakeTimers()
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)

    act(() => { fireEvent.click(screen.getByTestId('play-pause-btn')) })
    act(() => { vi.advanceTimersByTime(10000) })

    expect(screen.getByTestId('turn-label')).toHaveTextContent('Turn 2 / 2')
    expect(screen.getByTestId('play-pause-btn')).toHaveTextContent('Play')
    vi.useRealTimers()
  })

  it('switching strategy tab resets turn to 1', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('next-turn-btn'))
    expect(screen.getByTestId('turn-label')).toHaveTextContent('Turn 2 / 2')

    await user.click(screen.getByTestId('strategy-tab-strategy_authority_expert'))
    expect(screen.getByTestId('turn-label')).toHaveTextContent('Turn 1 / 2')
  })

  it('InternalMind receives turn number 1 on first turn', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('internal-mind')).toHaveAttribute('data-turn', '1')
  })

  it('InternalMind receives 0 prior memories on first turn', () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    expect(screen.getByTestId('internal-mind')).toHaveAttribute('data-memories', '0')
  })

  it('InternalMind receives 1 prior memory after advancing to turn 2', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('next-turn-btn'))
    expect(screen.getByTestId('internal-mind')).toHaveAttribute('data-memories', '1')
  })

  it('View Report button calls onViewReport', async () => {
    render(<MindViewer simulation={mockSimulation} onViewReport={mockOnViewReport} />)
    await user.click(screen.getByTestId('view-report-btn'))
    expect(mockOnViewReport).toHaveBeenCalledOnce()
  })
})

// Ensure real timers are restored after module even if a test crashes
afterEach(() => {
  vi.useRealTimers()
})
