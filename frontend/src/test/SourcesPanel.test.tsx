import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SourcesPanel from '../components/shared/SourcesPanel'
import { mockSimulation } from './fixtures'

// Mock the JSON data import to avoid loading the full file in tests
vi.mock('../data/persuasion_strategies.json', () => ({
  default: {
    metadata: { version: '1.0' },
    strategies: [
      {
        id: 'authority',
        name: 'Authority / Expertise Appeal',
        citation: {
          author: 'Robert B. Cialdini',
          work: 'Influence: The Psychology of Persuasion',
          year: 2007,
          url: 'https://example.com/authority',
          key_empirical_anchor: 'Patient compliance jumped 34% after staff posted credentials on walls.',
        },
      },
      {
        id: 'narrative',
        name: 'Personal Narrative',
        citation: {
          author: 'Walter Fisher',
          work: 'Human Communication as Narration',
          year: 1987,
          key_empirical_anchor: 'Narrative logic governs most human reasoning about values.',
        },
      },
    ],
  },
}))

const user = userEvent.setup({ delay: null })
const noop = vi.fn()

describe('SourcesPanel', () => {
  it('renders the panel element', () => {
    render(<SourcesPanel simulation={null} isOpen={false} onClose={noop} />)
    expect(screen.getByTestId('sources-panel')).toBeInTheDocument()
  })

  it('is hidden (translated off-screen) when isOpen=false', () => {
    render(<SourcesPanel simulation={null} isOpen={false} onClose={noop} />)
    expect(screen.getByTestId('sources-panel').className).toContain('translate-x-full')
  })

  it('is visible when isOpen=true', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('sources-panel').className).toContain('translate-x-0')
  })

  it('shows the panel title', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByText('Sources & Methodology')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', async () => {
    const onClose = vi.fn()
    render(<SourcesPanel simulation={null} isOpen={true} onClose={onClose} />)
    await user.click(screen.getByTestId('sources-close-btn'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('shows backdrop when open', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('sources-backdrop')).toBeInTheDocument()
  })

  it('does NOT show backdrop when closed', () => {
    render(<SourcesPanel simulation={null} isOpen={false} onClose={noop} />)
    expect(screen.queryByTestId('sources-backdrop')).not.toBeInTheDocument()
  })

  it('calls onClose when backdrop is clicked', async () => {
    const onClose = vi.fn()
    render(<SourcesPanel simulation={null} isOpen={true} onClose={onClose} />)
    await user.click(screen.getByTestId('sources-backdrop'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('shows strategies section', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('sources-strategies-section')).toBeInTheDocument()
  })

  it('shows strategy names from the data file', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByText('Authority / Expertise Appeal')).toBeInTheDocument()
    expect(screen.getByText('Personal Narrative')).toBeInTheDocument()
  })

  it('shows strategy citation author', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByText(/Robert B. Cialdini/i)).toBeInTheDocument()
  })

  it('shows strategy empirical anchor', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByText(/Patient compliance jumped 34%/i)).toBeInTheDocument()
  })

  it('shows strategy source link when URL is present', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    const links = screen.getAllByText('View source →')
    expect(links.length).toBeGreaterThan(0)
  })

  it('renders a card for each strategy in the data', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('sources-strategy-authority')).toBeInTheDocument()
    expect(screen.getByTestId('sources-strategy-narrative')).toBeInTheDocument()
  })

  it('shows methodology section', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('sources-methodology-section')).toBeInTheDocument()
  })

  it('shows methodology content', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.getByText(/Public vs. Private Stance Gap/i)).toBeInTheDocument()
    expect(screen.getByText(/Identity Threat Detection/i)).toBeInTheDocument()
  })

  it('does NOT show personas section when simulation is null', () => {
    render(<SourcesPanel simulation={null} isOpen={true} onClose={noop} />)
    expect(screen.queryByTestId('sources-personas-section')).not.toBeInTheDocument()
  })

  it('shows personas section when simulation is provided', () => {
    render(<SourcesPanel simulation={mockSimulation} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('sources-personas-section')).toBeInTheDocument()
  })

  it('shows persona display name', () => {
    render(<SourcesPanel simulation={mockSimulation} isOpen={true} onClose={noop} />)
    expect(screen.getByText('Karen M.')).toBeInTheDocument()
  })

  it('shows persona primary source citation', () => {
    render(<SourcesPanel simulation={mockSimulation} isOpen={true} onClose={noop} />)
    expect(screen.getByText(/Pew Research 2021 Political Typology/i)).toBeInTheDocument()
  })

  it('shows persona citation link when URL is present', () => {
    render(<SourcesPanel simulation={mockSimulation} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('persona-citation-link')).toBeInTheDocument()
  })

  it('shows validation section when simulation has validation_note', () => {
    render(<SourcesPanel simulation={mockSimulation} isOpen={true} onClose={noop} />)
    expect(screen.getByTestId('sources-validation-section')).toBeInTheDocument()
    expect(screen.getByText(/Matches published persuasion research/i)).toBeInTheDocument()
  })

  it('does NOT show validation section when validation_note is absent', () => {
    const simWithoutNote = { ...mockSimulation, validation_note: undefined }
    render(<SourcesPanel simulation={simWithoutNote} isOpen={true} onClose={noop} />)
    expect(screen.queryByTestId('sources-validation-section')).not.toBeInTheDocument()
  })
})
