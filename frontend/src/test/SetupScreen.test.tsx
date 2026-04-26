import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SetupScreen from '../components/setup/SetupScreen'
import { mockSimulation } from './fixtures'
import * as loader from '../data/loader'

vi.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    button: ({ children, whileHover: _wh, whileTap: _wt, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { whileHover?: unknown; whileTap?: unknown }) => (
      <button {...props}>{children}</button>
    ),
    div: ({ children, whileHover: _wh, whileTap: _wt, initial: _i, animate: _a, exit: _e, transition: _t, ...props }: React.HTMLAttributes<HTMLDivElement> & { whileHover?: unknown; whileTap?: unknown; initial?: unknown; animate?: unknown; exit?: unknown; transition?: unknown }) => (
      <div {...props}>{children}</div>
    ),
  },
}))

vi.mock('../data/loader')

const mockCatalog = {
  personas: [mockSimulation.metadata.persona],
  topics: [mockSimulation.metadata.topic],
  strategies: [],
}

beforeEach(() => {
  vi.mocked(loader.loadScenario).mockResolvedValue(mockSimulation)
  vi.mocked(loader.loadCatalog).mockResolvedValue(mockCatalog)
})

const mockOnRunSimulation = vi.fn()

beforeEach(() => {
  mockOnRunSimulation.mockClear()
})

describe('SetupScreen', () => {
  it('renders the setup screen header', () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(screen.getByText('Lumos')).toBeInTheDocument()
    expect(screen.getByText(/configure your simulation/i)).toBeInTheDocument()
  })

  it('renders step labels for persona and topic selection', () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(screen.getByRole('heading', { name: /select a persona/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /select a topic/i })).toBeInTheDocument()
  })

  it('renders persona card with display name and demographic shorthand', async () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(await screen.findByText('Karen M.')).toBeInTheDocument()
    expect(await screen.findByText('62, suburban Pennsylvania, retired schoolteacher')).toBeInTheDocument()
  })

  it('renders core value pills on persona card with title case', async () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(await screen.findByText('Family')).toBeInTheDocument()
    expect(await screen.findByText('Tradition')).toBeInTheDocument()
    expect(await screen.findByText('Self-Reliance')).toBeInTheDocument()
  })

  it('renders citation badge on persona card', async () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(await screen.findByText(/Pew Research 2021/i)).toBeInTheDocument()
  })

  it('renders topic card with display name', async () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(await screen.findByText('Should companies require return-to-office?')).toBeInTheDocument()
  })

  it('run button is disabled initially', () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(screen.getByTestId('run-button')).toBeDisabled()
  })

  it('run button remains disabled when only persona is selected', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    expect(screen.getByTestId('run-button')).toBeDisabled()
  })

  it('run button remains disabled when only topic is selected', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('topic-card-topic_return_to_office'))
    expect(screen.getByTestId('run-button')).toBeDisabled()
  })

  it('run button enables when both persona and topic are selected', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    await user.click(await screen.findByTestId('topic-card-topic_return_to_office'))

    expect(screen.getByTestId('run-button')).not.toBeDisabled()
  })

  it('clicking persona card opens profile panel', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    expect(screen.queryByTestId('profile-panel')).not.toBeInTheDocument()
    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    expect(screen.getByTestId('profile-panel')).toBeInTheDocument()
  })

  it('profile panel shows first-person description', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    expect(screen.getByText(/thirty years in a classroom/i)).toBeInTheDocument()
  })

  it('profile panel shows emotional triggers', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    expect(screen.getByText(/lectured to/i)).toBeInTheDocument()
    expect(screen.getByText(/asked about their experience/i)).toBeInTheDocument()
  })

  it('profile panel shows source citation with external link', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    const link = screen.getByText(/view original research/i)
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', expect.stringContaining('pewresearch.org'))
  })

  it('close button dismisses profile panel', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    expect(screen.getByTestId('profile-panel')).toBeInTheDocument()

    await user.click(screen.getByTestId('close-profile-panel'))
    expect(screen.queryByTestId('profile-panel')).not.toBeInTheDocument()
  })

  it('overlay click dismisses profile panel', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    await user.click(screen.getByTestId('panel-overlay'))
    expect(screen.queryByTestId('profile-panel')).not.toBeInTheDocument()
  })

  it('topic card shows predicted starting stance when persona is selected', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    expect(screen.getByText(/7\.0/)).toBeInTheDocument()
  })

  it('calls onRunSimulation with simulation data after run', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    await user.click(await screen.findByTestId('topic-card-topic_return_to_office'))
    await user.click(screen.getByTestId('run-button'))

    await waitFor(() => {
      expect(mockOnRunSimulation).toHaveBeenCalledOnce()
      expect(mockOnRunSimulation).toHaveBeenCalledWith(mockSimulation)
    })
  })

  it('shows ready message when both selections are made', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)

    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    await user.click(await screen.findByTestId('topic-card-topic_return_to_office'))

    expect(screen.getByText(/all 7 strategies will run in parallel/i)).toBeInTheDocument()
  })

  it('shows instruction message when selections are incomplete', () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    expect(screen.getByText(/select a persona and topic to continue/i)).toBeInTheDocument()
  })

  it('selected persona card uses border-4 instead of bg inversion', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    await user.click(await screen.findByTestId('persona-card-persona_skeptical_traditionalist'))
    const card = screen.getByTestId('persona-card-persona_skeptical_traditionalist')
    expect(card.className).toContain('border-4')
    expect(card.className).not.toContain('bg-[#0f0f0f]')
  })

  it('unselected persona card uses border-2', async () => {
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    const card = await screen.findByTestId('persona-card-persona_skeptical_traditionalist')
    expect(card.className).toContain('border-2')
  })

  it('selected topic card uses border-4 instead of bg inversion', async () => {
    const user = userEvent.setup()
    render(<SetupScreen onRunSimulation={mockOnRunSimulation} />)
    await user.click(await screen.findByTestId('topic-card-topic_return_to_office'))
    const card = screen.getByTestId('topic-card-topic_return_to_office')
    expect(card.className).toContain('border-4')
    expect(card.className).not.toContain('bg-[#0f0f0f]')
  })
})
