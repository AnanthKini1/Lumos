import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import TrajectoryChart, { buildChartData } from '../components/report/TrajectoryChart'
import { mockNarrativeOutcome, mockAuthorityOutcome } from './fixtures'

// Recharts uses browser SVG/ResizeObserver APIs not available in jsdom.
// Mock to stub internals while keeping the card wrapper testable.
vi.mock('recharts', () => ({
  ComposedChart:       ({ children }: { children: unknown }) => children,
  Line:                () => null,
  Area:                () => null,
  XAxis:               () => null,
  YAxis:               () => null,
  Tooltip:             () => null,
  Legend:              () => null,
  ReferenceLine:       () => null,
  ResponsiveContainer: ({ children }: { children: unknown }) => children,
}))

// ------- buildChartData unit tests (no render needed) -------

describe('buildChartData', () => {
  it('returns N + 1 points (turns + cooling-off)', () => {
    const data = buildChartData(mockNarrativeOutcome)
    // 2 turns + 1 cooling-off = 3
    expect(data).toHaveLength(3)
  })

  it('first point uses turn 1 public/private stance values', () => {
    const data = buildChartData(mockNarrativeOutcome)
    expect(data[0]).toMatchObject({ turn: 1, public: 7.0, private: 7.0 })
  })

  it('second point uses turn 2 values', () => {
    const data = buildChartData(mockNarrativeOutcome)
    expect(data[1]).toMatchObject({ turn: 2, public: 6.5, private: 6.2 })
  })

  it('last point is the cooling-off point with post_reflection_stance for both lines', () => {
    const data = buildChartData(mockNarrativeOutcome)
    const last = data[data.length - 1]
    expect(last.turn).toBe('Cool')
    expect(last.public).toBe(mockNarrativeOutcome.cooling_off.post_reflection_stance)
    expect(last.private).toBe(mockNarrativeOutcome.cooling_off.post_reflection_stance)
  })

  it('builds correct data for authority expert outcome', () => {
    const data = buildChartData(mockAuthorityOutcome)
    expect(data).toHaveLength(3)
    expect(data[1]).toMatchObject({ turn: 2, public: 6.0, private: 7.5 })
  })
})

// ------- Rendered card tests -------

describe('TrajectoryChart', () => {
  it('renders with data-testid for the outcome', () => {
    render(<TrajectoryChart outcome={mockNarrativeOutcome} strategyDisplayName="Personal Narrative" />)
    expect(screen.getByTestId('trajectory-chart-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('renders for authority expert outcome', () => {
    render(<TrajectoryChart outcome={mockAuthorityOutcome} strategyDisplayName="Authority Expert" />)
    expect(screen.getByTestId('trajectory-chart-strategy_authority_expert')).toBeInTheDocument()
  })

  it('shows strategy display name in card header', () => {
    render(<TrajectoryChart outcome={mockNarrativeOutcome} strategyDisplayName="Personal Narrative" />)
    expect(screen.getByText('Personal Narrative')).toBeInTheDocument()
  })

  it('shows verdict dot', () => {
    render(<TrajectoryChart outcome={mockNarrativeOutcome} strategyDisplayName="Personal Narrative" />)
    expect(screen.getByTestId('chart-dot-strategy_personal_narrative')).toBeInTheDocument()
  })

  it('verdict dot has sr-only text for accessibility', () => {
    render(<TrajectoryChart outcome={mockNarrativeOutcome} strategyDisplayName="Personal Narrative" />)
    const dot = screen.getByTestId('chart-dot-strategy_personal_narrative')
    expect(dot.className).toContain('sr-only')
  })

  it('verdict dot shows verdict text for BACKFIRE', () => {
    render(<TrajectoryChart outcome={mockAuthorityOutcome} strategyDisplayName="Authority Expert" />)
    const dot = screen.getByTestId('chart-dot-strategy_authority_expert')
    expect(dot.textContent).toBe('BACKFIRE')
  })

  it('card has hard black border (monochrome design)', () => {
    render(<TrajectoryChart outcome={mockNarrativeOutcome} strategyDisplayName="Personal Narrative" />)
    const card = screen.getByTestId('trajectory-chart-strategy_personal_narrative')
    expect(card.className).toContain('border-[#0f0f0f]')
  })

  it('card has hard black border for BACKFIRE too', () => {
    render(<TrajectoryChart outcome={mockAuthorityOutcome} strategyDisplayName="Authority Expert" />)
    const card = screen.getByTestId('trajectory-chart-strategy_authority_expert')
    expect(card.className).toContain('border-[#0f0f0f]')
  })
})
