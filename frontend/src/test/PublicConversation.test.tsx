import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import PublicConversation from '../components/mindviewer/PublicConversation'
import { mockTurn1, mockTurn2 } from './fixtures'

const turns = [mockTurn1, mockTurn2]

afterEach(() => {
  vi.useRealTimers()
})

describe('PublicConversation', () => {
  it('renders the public conversation panel', () => {
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByTestId('public-conversation')).toBeInTheDocument()
  })

  it('shows panel header with strategy display name', () => {
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByText(/Personal Narrative/i)).toBeInTheDocument()
  })

  it('renders only turns up to currentTurn (turn 0 → 1 visible turn)', () => {
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByTestId('turn-1')).toBeInTheDocument()
    expect(screen.queryByTestId('turn-2')).not.toBeInTheDocument()
  })

  it('renders turn 2 when currentTurn is 1', () => {
    render(<PublicConversation turns={turns} currentTurn={1} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByTestId('turn-1')).toBeInTheDocument()
    expect(screen.getByTestId('turn-2')).toBeInTheDocument()
  })

  it('shows turn number badges', () => {
    render(<PublicConversation turns={turns} currentTurn={1} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByText('Turn 1')).toBeInTheDocument()
    expect(screen.getByText('Turn 2')).toBeInTheDocument()
  })

  it('shows "Interviewer" label for interviewer messages', () => {
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByText('Interviewer')).toBeInTheDocument()
  })

  it('shows persona display name label for persona responses', () => {
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByText('Karen M.')).toBeInTheDocument()
  })

  it('renders interviewer message text for previous turns immediately', () => {
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByText(/Let me tell you about my neighbor Sarah/i)).toBeInTheDocument()
  })

  it('shows strategy annotation below interviewer bubble', () => {
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    expect(screen.getByText(/Opening with a personal story/i)).toBeInTheDocument()
  })

  it('previous turns show full persona response without typing', () => {
    render(<PublicConversation turns={turns} currentTurn={1} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)
    // Turn 1 persona response should be fully visible (it's a previous turn)
    expect(screen.getByText(/I have a sister who went through something similar/i)).toBeInTheDocument()
  })

  it('typing animation reveals persona response character by character on current turn', () => {
    vi.useFakeTimers()
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)

    // At t=0, only first character should be shown
    const fullText = mockTurn1.persona_output.public_response
    // Advance 1 character worth of time
    act(() => { vi.advanceTimersByTime(18) })

    // After 1 tick, at least the first character is shown but not the full text
    const bubbles = screen.getByTestId('public-conversation')
    expect(bubbles).toBeInTheDocument()
    // Full text is NOT yet in the document (typing is in progress)
    expect(screen.queryByText(fullText)).not.toBeInTheDocument()
  })

  it('typing animation completes fully after enough time', () => {
    vi.useFakeTimers()
    const fullText = mockTurn1.persona_output.public_response
    render(<PublicConversation turns={turns} currentTurn={0} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)

    act(() => { vi.advanceTimersByTime(fullText.length * 18 + 100) })
    expect(screen.getByText(fullText)).toBeInTheDocument()
  })

  it('renders all turn data after all turns are revealed', () => {
    vi.useFakeTimers()
    const text2 = mockTurn2.persona_output.public_response
    render(<PublicConversation turns={turns} currentTurn={1} strategyDisplayName="Personal Narrative" personaDisplayName="Karen M." />)

    act(() => { vi.advanceTimersByTime(text2.length * 18 + 100) })
    expect(screen.getByText(text2)).toBeInTheDocument()
  })
})
