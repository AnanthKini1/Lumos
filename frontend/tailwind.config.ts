import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // UI accent — rich purple used for selections, buttons, step indicators
        accent: {
          DEFAULT: '#9333ea', // purple-600
          hover:   '#7e22ce', // purple-700
          light:   '#f3e8ff', // purple-100
          shadow:  '#e9d5ff', // purple-200
        },
        // Private/internal mind panel palette
        mind: {
          bg: '#f5f3ff',       // violet-50
          border: '#ddd6fe',   // violet-200
          text: '#2e1065',     // violet-950
          muted: '#6d28d9',    // violet-700
          header: '#a78bfa',   // violet-400
        },
        // Verdict color tokens (used in JS via arbitrary values too)
        verdict: {
          genuine: { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' },
          partial: { bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' },
          surface: { bg: '#fef3c7', text: '#b45309', border: '#fde68a' },
          backfire: { bg: '#ffe4e6', text: '#be123c', border: '#fecdd3' },
          none: { bg: '#f1f5f9', text: '#475569', border: '#e2e8f0' },
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      boxShadow: {
        'emerald-subtle': '0 0 0 1px rgb(167 243 208 / 0.5), 0 1px 3px rgb(16 185 129 / 0.1)',
        'rose-subtle': '0 0 0 1px rgb(254 205 211 / 0.5), 0 1px 3px rgb(244 63 94 / 0.1)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

export default config
