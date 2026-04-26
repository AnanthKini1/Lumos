import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConversationTimeline from '../components/report/ConversationTimeline'
import { mockNarrativeOutcome, mockAuthorityOutcome } from './fixtures'

describe('ConversationTimeline', () => {
  it('renders a node for every turn in the active outcome', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome]} />)
    const turns = mockNarrativeOutcome.turns
    turns.forEach(turn => {
      expect(screen.getByTestId(`timeline-node-${turn.turn_number}`)).toBeDefined()
    })
  })

  it('renders "Round N" labels above each node', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome]} />)
    mockNarrativeOutcome.turns.forEach(turn => {
      expect(screen.getByText(`Round ${turn.turn_number}`)).toBeDefined()
    })
  })

  it('synthesis panel is hidden before any node is clicked', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome]} />)
    const panel = screen.getByTestId('timeline-synthesis-panel')
    expect(panel.style.maxHeight).toBe('0px')
    expect(panel.style.opacity).toBe('0')
  })

  it('synthesis panel expands when a node is clicked', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome]} />)
    fireEvent.click(screen.getByTestId('timeline-node-1'))
    const panel = screen.getByTestId('timeline-synthesis-panel')
    expect(panel.style.maxHeight).not.toBe('0px')
    expect(panel.style.opacity).toBe('1')
  })

  it('synthesis panel collapses when the same node is clicked again', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome]} />)
    const node = screen.getByTestId('timeline-node-1')
    fireEvent.click(node)
    fireEvent.click(node)
    const panel = screen.getByTestId('timeline-synthesis-panel')
    expect(panel.style.maxHeight).toBe('0px')
    expect(panel.style.opacity).toBe('0')
  })

  it('shows turn synthesis content after clicking a node', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome]} />)
    fireEvent.click(screen.getByTestId('timeline-node-1'))
    expect(screen.getByTestId('turn-synthesis')).toBeDefined()
  })

  it('displays strategy selector pills when multiple outcomes provided', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome, mockAuthorityOutcome]} />)
    expect(screen.getByTestId(`timeline-strategy-pill-${mockNarrativeOutcome.strategy_id}`)).toBeDefined()
    expect(screen.getByTestId(`timeline-strategy-pill-${mockAuthorityOutcome.strategy_id}`)).toBeDefined()
  })

  it('does not render strategy pills when only one outcome', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome]} />)
    expect(screen.queryByTestId(`timeline-strategy-pill-${mockNarrativeOutcome.strategy_id}`)).toBeNull()
  })

  it('resets selected turn when switching strategies', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome, mockAuthorityOutcome]} />)
    fireEvent.click(screen.getByTestId('timeline-node-1'))
    expect(screen.getByTestId('timeline-synthesis-panel').style.opacity).toBe('1')

    fireEvent.click(screen.getByTestId(`timeline-strategy-pill-${mockAuthorityOutcome.strategy_id}`))
    const panel = screen.getByTestId('timeline-synthesis-panel')
    expect(panel.style.maxHeight).toBe('0px')
    expect(panel.style.opacity).toBe('0')
  })

  it('renders nodes for the newly selected strategy after switching', () => {
    render(<ConversationTimeline outcomes={[mockNarrativeOutcome, mockAuthorityOutcome]} />)
    fireEvent.click(screen.getByTestId(`timeline-strategy-pill-${mockAuthorityOutcome.strategy_id}`))
    // mockAuthorityOutcome also has 2 turns — both node labels should be present
    mockAuthorityOutcome.turns.forEach(turn => {
      expect(screen.getByTestId(`timeline-node-${turn.turn_number}`)).toBeDefined()
    })
  })

  it('renders nothing when outcomes array is empty', () => {
    const { container } = render(<ConversationTimeline outcomes={[]} />)
    expect(container.firstChild).toBeNull()
  })
})
