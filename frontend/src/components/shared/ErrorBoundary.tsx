import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' }

  static getDerivedStateFromError(error: unknown): State {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return { hasError: true, message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          data-testid="error-boundary-fallback"
          className="min-h-screen bg-slate-50 flex items-center justify-center"
        >
          <div className="max-w-md text-center px-6">
            <p className="text-lg font-semibold text-slate-800 mb-2">Demo data unavailable</p>
            <p className="text-sm text-slate-500">{this.state.message}</p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
