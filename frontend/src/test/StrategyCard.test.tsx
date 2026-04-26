import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import StrategyCard from '../components/report/StrategyCard'
import { mockNarrativeOutcome, mockAuthorityOutcome } from './fixtures'

const user = userEvent.setup({ delay: null })
const mockOnViewTranscript = vi.fn()

beforeEach(() => {
  mockOnViewTranscript.mockClear()
})

function renderNarrative() {
  render(
    <StrategyCard
      outcome={mockNarrativeOutcome}
      strategyDisplayName="Personal Narrative"
      onViewTranscript={mockOnViewTranscript}
    />
  )
}

function renderAuthority() {
  render(
    <StrategyCard
      outcome={mockAuthorityOutcome}
      strategyDisplayName="Authority Expert"
      onViewTranscript={mockOnViewTranscript}
    />
  )
}

describe('StrategyCard — collapsed state', () => {
  it('renders with data-testid', () => {
    renderNarrative()
    expect(screen.getByTestId('strategy-card-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('shows strategy display name', () => {
    renderNarrative()
    expect(screen.getByText('Personal Narrative')).toBeInTheDocument()
  })

  it('shows verdict badge', () => {
    renderNarrative()
    expect(screen.getByTestId('card-verdict-badge-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('shows "GENUINE SHIFT" badge label for GENUINE_BELIEF_SHIFT', () => {
    renderNarrative()
    expect(screen.getByText('GENUINE SHIFT')).toBeInTheDocument()
  })

  it('shows "BACKFIRE" badge label for BACKFIRE', () => {
    renderAuthority()
    expect(screen.getByText('BACKFIRE')).toBeInTheDocument()
  })

  it('GENUINE_BELIEF_SHIFT badge has mono bold styling', () => {
    renderNarrative()
    const badge = screen.getByTestId('card-verdict-badge-strategy_personal_narrative')
    expect(badge.className).toContain('font-mono')
    expect(badge.className).toContain('font-bold')
  })

  it('BACKFIRE badge has mono bold styling', () => {
    renderAuthority()
    const badge = screen.getByTestId('card-verdict-badge-strategy_authority_expert')
    expect(badge.className).toContain('font-mono')
    expect(badge.className).toContain('font-bold')
  })

  it('card has hard border for GENUINE_BELIEF_SHIFT', () => {
    renderNarrative()
    const card = screen.getByTestId('strategy-card-strategy_personal_narrative')
    expect(card.className).toContain('border-[#0f0f0f]')
  })

  it('card has red border for BACKFIRE', () => {
    renderAuthority()
    const card = screen.getByTestId('strategy-card-strategy_authority_expert')
    expect(card.className).toContain('border-[#dc2626]')
  })

  it('shows verdict_reasoning text', () => {
    renderNarrative()
    expect(screen.getByText(/Private stance moved >2.0 with low gap/i)).toBeInTheDocument()
  })

  it('body is hidden by default', () => {
    renderNarrative()
    expect(screen.queryByTestId('strategy-card-body-strategy_personal_narrative')).not.toBeInTheDocument()
  })

  it('toggle button has aria-expanded=false by default', () => {
    renderNarrative()
    const btn = screen.getByTestId('strategy-card-toggle-strategy_personal_narrative')
    expect(btn).toHaveAttribute('aria-expanded', 'false')
  })

  it('shows identity defense badge for BACKFIRE with threats > 0', () => {
    renderAuthority()
    expect(screen.getByTestId('identity-defense-badge-strategy_authority_expert')).toBeInTheDocument()
  })

  it('does NOT show identity defense badge for GENUINE_BELIEF_SHIFT', () => {
    renderNarrative()
    expect(screen.queryByTestId('identity-defense-badge-strategy_personal_narrative')).not.toBeInTheDocument()
  })
})

describe('StrategyCard — expanded state', () => {
  it('clicking toggle reveals body', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByTestId('strategy-card-body-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('toggle button has aria-expanded=true when expanded', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative')).toHaveAttribute('aria-expanded', 'true')
  })

  it('clicking toggle again collapses the body', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.queryByTestId('strategy-card-body-strategy_personal_narrative')).not.toBeInTheDocument()
  })

  it('shows cognitive score labels when expanded', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByText('Engagement')).toBeInTheDocument()
    expect(screen.getByText('Motivated Reasoning')).toBeInTheDocument()
    expect(screen.getByText('Ambivalence')).toBeInTheDocument()
    expect(screen.getByText('Gap Score')).toBeInTheDocument()
  })

  it('shows standout quote when expanded', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByTestId('quote-0-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('quote shows turn number', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByText('Turn 1')).toBeInTheDocument()
  })

  it('quote shows type label "monologue"', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByText('monologue')).toBeInTheDocument()
  })

  it('quote shows quote text', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByText(/I hadn't considered this angle before/i)).toBeInTheDocument()
  })

  it('quote shows annotation', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByText(/Genuine cognitive openness/i)).toBeInTheDocument()
  })

  it('shows synthesis section', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByTestId('synthesis-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('shows synthesis paragraph text', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByText(/Personal narrative lowered Karen's defenses/i)).toBeInTheDocument()
  })

  it('shows Watch Full Transcript button', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    expect(screen.getByTestId('watch-transcript-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('Watch Full Transcript calls onViewTranscript with strategy_id', async () => {
    renderNarrative()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_personal_narrative'))
    await user.click(screen.getByTestId('watch-transcript-strategy_personal_narrative'))
    expect(mockOnViewTranscript).toHaveBeenCalledWith('strategy_personal_narrative')
  })

  it('Watch Transcript works for authority expert too', async () => {
    renderAuthority()
    await user.click(screen.getByTestId('strategy-card-toggle-strategy_authority_expert'))
    await user.click(screen.getByTestId('watch-transcript-strategy_authority_expert'))
    expect(mockOnViewTranscript).toHaveBeenCalledWith('strategy_authority_expert')
  })
})
