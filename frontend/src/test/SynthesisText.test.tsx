import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SynthesisText from '../components/report/SynthesisText'

describe('SynthesisText', () => {
  it('renders plain text as a paragraph', () => {
    render(<SynthesisText text="This is a plain sentence." />)
    expect(screen.getByText(/plain sentence/)).toBeTruthy()
  })

  it('returns null for empty string', () => {
    const { container } = render(<SynthesisText text="" />)
    expect(container.firstChild).toBeNull()
  })

  it('replaces " / " with " and "', () => {
    render(<SynthesisText text="Strategy A / Strategy B worked well." />)
    expect(screen.getByText(/Strategy A and Strategy B worked well/)).toBeTruthy()
  })

  it('collapses double punctuation artifacts', () => {
    render(<SynthesisText text="The result was clear,. Period." />)
    expect(screen.queryByText(/,\./)).toBeNull()
  })

  it('splits on double newlines into multiple paragraphs', () => {
    const { container } = render(
      <SynthesisText text={"First paragraph.\n\nSecond paragraph."} />
    )
    const paras = container.querySelectorAll('p')
    expect(paras.length).toBe(2)
  })

  it('detects a mechanism name and injects a citation superscript', () => {
    render(
      <SynthesisText text="The persona displayed Reactance when pushed." />
    )
    // The mechanism name itself should still be visible
    expect(screen.getByText(/Reactance/)).toBeTruthy()
    // A citation superscript for Brehm should appear
    expect(screen.getByText(/Brehm/)).toBeTruthy()
  })

  it('renders citation as a link when citation_url is present', () => {
    render(
      <SynthesisText text="Identity-Protective Cognition was observed." />
    )
    const link = screen.getByRole('link')
    expect(link).toBeTruthy()
    expect((link as HTMLAnchorElement).href).toContain('doi.org')
  })

  it('does not add spurious citations for text without mechanism names', () => {
    render(<SynthesisText text="The strategy failed due to poor framing." />)
    expect(screen.queryByRole('link')).toBeNull()
    expect(screen.queryByRole('superscript')).toBeNull()
  })

  it('applies the className prop to each paragraph', () => {
    const { container } = render(
      <SynthesisText text="One sentence." className="font-serif" />
    )
    const p = container.querySelector('p')
    expect(p?.className).toContain('font-serif')
  })
})
