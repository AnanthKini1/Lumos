import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LandingPage from '../components/landing/LandingPage'

const user = userEvent.setup({ delay: null })

describe('LandingPage', () => {
  it('renders with data-testid', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    expect(screen.getByTestId('landing-page')).toBeInTheDocument()
  })

  it('renders the Lumos icon SVG', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    expect(screen.getByTestId('lumos-icon')).toBeInTheDocument()
  })

  it('renders "Lumos" text split into characters', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    // Characters rendered individually
    const page = screen.getByTestId('landing-page')
    expect(page.textContent).toContain('Lumos')
  })

  it('renders subtitle text', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    expect(screen.getByTestId('subtitle')).toBeInTheDocument()
    expect(screen.getByTestId('subtitle')).toHaveTextContent('Internal Mind Simulator')
  })

  it('subtitle is left-aligned mono uppercase', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    const subtitle = screen.getByTestId('subtitle')
    expect(subtitle.className).toContain('font-mono')
    expect(subtitle.className).toContain('uppercase')
  })

  it('renders Begin button', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    expect(screen.getByTestId('begin-btn')).toBeInTheDocument()
    expect(screen.getByTestId('begin-btn')).toHaveTextContent('Begin')
  })

  it('calls onBegin when Begin is clicked', async () => {
    const onBegin = vi.fn()
    render(<LandingPage onBegin={onBegin} />)
    await user.click(screen.getByTestId('begin-btn'))
    expect(onBegin).toHaveBeenCalledOnce()
  })

  it('Begin button has serif font', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    const btn = screen.getByTestId('begin-btn')
    expect(btn.className).toContain('font-serif')
  })

  it('Begin button has border styling (not bg-inverted default)', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    const btn = screen.getByTestId('begin-btn')
    expect(btn.className).toContain('border-2')
    expect(btn.className).toContain('border-[#0f0f0f]')
  })

  it('background is #fafafa', () => {
    render(<LandingPage onBegin={vi.fn()} />)
    const page = screen.getByTestId('landing-page')
    expect(page.className).toContain('bg-[#fafafa]')
  })
})
