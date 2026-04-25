import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import InternalMind from '../components/mindviewer/InternalMind'
import { mockPersonaTurnOutput, mockThreatTurnOutput } from './fixtures'

afterEach(() => {
  vi.useRealTimers()
})

describe('InternalMind', () => {
  it('renders with data-testid', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByTestId('internal-mind')).toBeInTheDocument()
  })

  it('shows turn number in header', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={3} />)
    expect(screen.getByTestId('mind-header')).toHaveTextContent('Turn 3')
  })

  it('shows "INTERNAL MONOLOGUE" label in header', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByTestId('mind-header')).toHaveTextContent(/internal monologue/i)
  })

  it('shows emotion badge', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByTestId('emotion-badge')).toBeInTheDocument()
  })

  it('shows primary emotion label in badge', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByTestId('emotion-badge')).toHaveTextContent(/intrigued/i)
  })

  it('shows "defensive" emotion for threat fixture', () => {
    render(<InternalMind turnOutput={mockThreatTurnOutput} priorMemoryNotes={[]} turnNumber={2} />)
    expect(screen.getByTestId('emotion-badge')).toHaveTextContent(/defensive/i)
  })

  it('shows intensity as N/10 format', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByTestId('emotion-badge')).toHaveTextContent(/\/10/)
  })

  it('shows trigger text', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByText(/Triggered by/i)).toBeInTheDocument()
    expect(screen.getByText(/the caregiving story/i)).toBeInTheDocument()
  })

  it('does NOT show identity threat badge when not threatened', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.queryByTestId('identity-threat-badge')).not.toBeInTheDocument()
  })

  it('shows identity threat badge when threatened', () => {
    render(<InternalMind turnOutput={mockThreatTurnOutput} priorMemoryNotes={[]} turnNumber={2} />)
    expect(screen.getByTestId('identity-threat-badge')).toBeInTheDocument()
  })

  it('shows what_was_threatened text in threat badge', () => {
    render(<InternalMind turnOutput={mockThreatTurnOutput} priorMemoryNotes={[]} turnNumber={2} />)
    expect(screen.getByText(/self-reliance and common sense/i)).toBeInTheDocument()
  })

  it('applies red border when identity is threatened', () => {
    render(<InternalMind turnOutput={mockThreatTurnOutput} priorMemoryNotes={[]} turnNumber={2} />)
    const panel = screen.getByTestId('internal-mind')
    expect(panel.className).toContain('border-[#dc2626]')
    expect(panel.className).toContain('border-l-4')
  })

  it('applies dark background always (inverted panel)', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    const panel = screen.getByTestId('internal-mind')
    expect(panel.className).toContain('bg-[#0f0f0f]')
  })

  it('shows private stance section', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByTestId('private-stance')).toBeInTheDocument()
  })

  it('shows private stance value formatted to 1 decimal', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByText('6.2')).toBeInTheDocument()
  })

  it('shows private stance change reason', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByText(/The caregiving angle hadn't occurred to me/i)).toBeInTheDocument()
  })

  it('shows current memory card', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByTestId('current-memory')).toBeInTheDocument()
  })

  it('shows memory_to_carry_forward text in current memory card', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    expect(screen.getByText(/The Sarah story/i)).toBeInTheDocument()
  })

  it('shows prior memory notes', () => {
    const priorNotes = ['Prior memory from turn 1']
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={priorNotes} turnNumber={2} />)
    expect(screen.getByText('Prior memory from turn 1')).toBeInTheDocument()
  })

  it('shows multiple prior memory notes', () => {
    const priorNotes = ['Memory from turn 1', 'Memory from turn 2']
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={priorNotes} turnNumber={3} />)
    expect(screen.getByText('Memory from turn 1')).toBeInTheDocument()
    expect(screen.getByText('Memory from turn 2')).toBeInTheDocument()
  })

  it('shows stable arrow when previousPrivateStance equals current', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} previousPrivateStance={6.2} />)
    expect(screen.getByTestId('stance-arrow')).toHaveTextContent('→')
  })

  it('shows down arrow when private stance decreased', () => {
    // mockPersonaTurnOutput.private_stance = 6.2, previous = 7.0 → decrease
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={2} previousPrivateStance={7.0} />)
    expect(screen.getByTestId('stance-arrow')).toHaveTextContent('↓')
  })

  it('shows up arrow when private stance increased', () => {
    // mockThreatTurnOutput.private_stance = 7.8, previous = 7.0 → increase
    render(<InternalMind turnOutput={mockThreatTurnOutput} priorMemoryNotes={[]} turnNumber={2} previousPrivateStance={7.0} />)
    expect(screen.getByTestId('stance-arrow')).toHaveTextContent('↑')
  })

  it('defaults to stable arrow when no previousPrivateStance is provided', () => {
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)
    // With no previous stance, prevStance = private_stance → stable
    expect(screen.getByTestId('stance-arrow')).toHaveTextContent('→')
  })

  it('typing animation reveals monologue character by character', () => {
    vi.useFakeTimers()
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)

    const fullText = mockPersonaTurnOutput.internal_monologue
    act(() => { vi.advanceTimersByTime(15) })

    // Full text is NOT yet shown (typing in progress)
    expect(screen.queryByText(fullText)).not.toBeInTheDocument()
  })

  it('typing animation completes fully after enough time', () => {
    vi.useFakeTimers()
    const fullText = mockPersonaTurnOutput.internal_monologue
    render(<InternalMind turnOutput={mockPersonaTurnOutput} priorMemoryNotes={[]} turnNumber={1} />)

    act(() => { vi.advanceTimersByTime(fullText.length * 15 + 100) })
    expect(screen.getByText(fullText)).toBeInTheDocument()
  })
})
