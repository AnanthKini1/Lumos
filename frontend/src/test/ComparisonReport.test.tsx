import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ComparisonReport from '../components/report/ComparisonReport'
import { mockSimulation } from './fixtures'

// Avoid pulling in recharts (requires browser SVG/ResizeObserver APIs)
vi.mock('../components/report/TrajectoryChart', () => ({
  default: ({ outcome }: { outcome: { strategy_id: string } }) => (
    <div data-testid={`trajectory-chart-${outcome.strategy_id}`} />
  ),
}))

vi.mock('../components/report/StrategyCard', () => ({
  default: ({ outcome }: { outcome: { strategy_id: string } }) => (
    <div data-testid={`strategy-card-${outcome.strategy_id}`} />
  ),
}))

const user = userEvent.setup({ delay: null })

const mockOnViewTranscript = vi.fn()
const mockOnBackToSetup = vi.fn()

beforeEach(() => {
  mockOnViewTranscript.mockClear()
  mockOnBackToSetup.mockClear()
})

function renderReport() {
  render(
    <ComparisonReport
      simulation={mockSimulation}
      onViewTranscript={mockOnViewTranscript}
      onBackToSetup={mockOnBackToSetup}
    />
  )
}

describe('ComparisonReport', () => {
  it('renders with data-testid', () => {
    renderReport()
    expect(screen.getByTestId('comparison-report')).toBeInTheDocument()
  })

  it('calls onBackToSetup when back button is clicked', async () => {
    renderReport()
    await user.click(screen.getByTestId('back-btn'))
    expect(mockOnBackToSetup).toHaveBeenCalledOnce()
  })

  it('shows synthesis card', () => {
    renderReport()
    expect(screen.getByTestId('synthesis-card')).toBeInTheDocument()
  })

  it('shows overall_synthesis text', () => {
    renderReport()
    expect(screen.getByText(/For Karen, Personal Narrative produced genuine belief shift/i)).toBeInTheDocument()
  })

  it('shows validation_note when present', () => {
    renderReport()
    expect(screen.getByTestId('validation-note')).toBeInTheDocument()
    expect(screen.getByText(/Matches published persuasion research/i)).toBeInTheDocument()
  })

  it('does not show validation_note when absent', () => {
    const simWithoutNote = { ...mockSimulation, validation_note: undefined }
    render(
      <ComparisonReport
        simulation={simWithoutNote}
        onViewTranscript={mockOnViewTranscript}
        onBackToSetup={mockOnBackToSetup}
      />
    )
    expect(screen.queryByTestId('validation-note')).not.toBeInTheDocument()
  })

  it('shows comparison table', () => {
    renderReport()
    expect(screen.getByTestId('comparison-table')).toBeInTheDocument()
  })

  it('renders a row for each outcome', () => {
    renderReport()
    expect(screen.getByTestId('report-row-strategy_personal_narrative')).toBeInTheDocument()
    expect(screen.getByTestId('report-row-strategy_authority_expert')).toBeInTheDocument()
  })

  it('rows are sorted: GENUINE_BELIEF_SHIFT before BACKFIRE', () => {
    renderReport()
    const rows = screen.getAllByRole('row').slice(1) // skip header row
    const firstRowId = rows[0].getAttribute('data-testid')
    const secondRowId = rows[1].getAttribute('data-testid')
    expect(firstRowId).toBe('report-row-strategy_personal_narrative')
    expect(secondRowId).toBe('report-row-strategy_authority_expert')
  })

  it('shows GENUINE_BELIEF_SHIFT verdict badge as uppercase mono text', () => {
    renderReport()
    const badge = screen.getByTestId('verdict-badge-strategy_personal_narrative')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('font-mono')
    expect(badge.className).toContain('font-bold')
  })

  it('shows BACKFIRE verdict badge as uppercase mono text', () => {
    renderReport()
    const badge = screen.getByTestId('verdict-badge-strategy_authority_expert')
    expect(badge.className).toContain('font-mono')
    expect(badge.className).toContain('font-bold')
  })

  it('shows "GENUINE SHIFT" label for GENUINE_BELIEF_SHIFT', () => {
    renderReport()
    expect(screen.getByText('GENUINE SHIFT')).toBeInTheDocument()
  })

  it('shows "BACKFIRE" label for BACKFIRE', () => {
    renderReport()
    expect(screen.getByText('BACKFIRE')).toBeInTheDocument()
  })

  it('computes correct public delta for Personal Narrative', () => {
    // public_stance_per_turn: [7.0, 6.5] → delta = -0.5
    renderReport()
    expect(screen.getByTestId('public-delta-strategy_personal_narrative')).toHaveTextContent('-0.5')
  })

  it('computes correct public delta for Authority Expert', () => {
    // public_stance_per_turn: [7.0, 6.0] → delta = -1.0
    renderReport()
    expect(screen.getByTestId('public-delta-strategy_authority_expert')).toHaveTextContent('-1.0')
  })

  it('computes correct private delta for Personal Narrative', () => {
    // private_stance_per_turn: [7.0, 6.2] → delta = -0.8
    renderReport()
    expect(screen.getByTestId('private-delta-strategy_personal_narrative')).toHaveTextContent('-0.8')
  })

  it('computes correct private delta for Authority Expert', () => {
    // private_stance_per_turn: [7.0, 7.5] → delta = +0.5
    renderReport()
    expect(screen.getByTestId('private-delta-strategy_authority_expert')).toHaveTextContent('+0.5')
  })

  it('computes correct max gap for Personal Narrative', () => {
    // gap_per_turn: [0.0, 0.3] → max = 0.3
    renderReport()
    expect(screen.getByTestId('max-gap-strategy_personal_narrative')).toHaveTextContent('0.3')
  })

  it('computes correct max gap for Authority Expert', () => {
    // gap_per_turn: [0.0, 1.5] → max = 1.5
    renderReport()
    expect(screen.getByTestId('max-gap-strategy_authority_expert')).toHaveTextContent('1.5')
  })

  it('shows correct threats count for Personal Narrative', () => {
    renderReport()
    expect(screen.getByTestId('threats-strategy_personal_narrative')).toHaveTextContent('0')
  })

  it('shows correct threats count for Authority Expert', () => {
    renderReport()
    expect(screen.getByTestId('threats-strategy_authority_expert')).toHaveTextContent('2')
  })

  it('shows persistence badge for Personal Narrative as uppercase mono', () => {
    renderReport()
    const badge = screen.getByTestId('persistence-strategy_personal_narrative')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('font-mono')
    expect(badge.className).toContain('font-bold')
  })

  it('shows persistence badge for Authority Expert as uppercase mono', () => {
    renderReport()
    const badge = screen.getByTestId('persistence-strategy_authority_expert')
    expect(badge.className).toContain('font-mono')
    expect(badge.className).toContain('font-bold')
  })

  it('calls onViewTranscript with correct strategy_id when Watch button clicked', async () => {
    renderReport()
    await user.click(screen.getByTestId('view-transcript-strategy_personal_narrative'))
    expect(mockOnViewTranscript).toHaveBeenCalledWith('strategy_personal_narrative')
  })

  it('calls onViewTranscript with authority_expert strategy_id', async () => {
    renderReport()
    await user.click(screen.getByTestId('view-transcript-strategy_authority_expert'))
    expect(mockOnViewTranscript).toHaveBeenCalledWith('strategy_authority_expert')
  })

  it('shows trajectory section', () => {
    renderReport()
    expect(screen.getByTestId('trajectory-section')).toBeInTheDocument()
  })

  it('shows trajectory chart for each outcome', () => {
    renderReport()
    expect(screen.getByTestId('trajectory-chart-strategy_personal_narrative')).toBeInTheDocument()
    expect(screen.getByTestId('trajectory-chart-strategy_authority_expert')).toBeInTheDocument()
  })

  it('shows strategy cards section', () => {
    renderReport()
    expect(screen.getByTestId('strategy-cards-section')).toBeInTheDocument()
  })

  it('shows strategy card for each outcome', () => {
    renderReport()
    expect(screen.getByTestId('strategy-card-strategy_personal_narrative')).toBeInTheDocument()
    expect(screen.getByTestId('strategy-card-strategy_authority_expert')).toBeInTheDocument()
  })

  it('table rows use warm tint hover, not black inversion', () => {
    renderReport()
    const row = screen.getByTestId('report-row-strategy_personal_narrative')
    expect(row.className).not.toContain('hover:bg-[#0f0f0f]')
    expect(row.className).toContain('hover:bg-[#f0ede8]')
  })

  it('table rows do not use group class (no child group-hover inversions)', () => {
    renderReport()
    const row = screen.getByTestId('report-row-strategy_personal_narrative')
    expect(row.className).not.toContain('group')
  })
})
