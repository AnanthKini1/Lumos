import { useState } from 'react'

const CATEGORIES = [
  {
    id: 'backfire',
    label: 'Backfire',
    color: '#dc2626',
    mechanisms: ['Identity-Protective Cognition', 'Reactance', 'Source Credibility Discounting'],
  },
  {
    id: 'genuine_persuasion',
    label: 'Genuine Persuasion',
    color: '#16a34a',
    mechanisms: ['Narrative Transportation', 'Central Route Elaboration'],
  },
  {
    id: 'surface_mechanism',
    label: 'Surface Mechanism',
    color: '#d97706',
    mechanisms: ['Peripheral Route Compliance'],
  },
]

export default function MechanismLegend() {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      data-testid="mechanism-legend"
      className="fixed bottom-16 right-4 z-20 flex flex-col items-end gap-1"
    >
      {expanded && (
        <div className="border-2 border-[#0f0f0f] bg-[#fafafa] p-4 w-64 space-y-3">
          <p className="font-mono text-xs uppercase tracking-widest text-[#0f0f0f] opacity-50 font-bold border-b border-[#0f0f0f] pb-1">
            Mechanism Categories
          </p>
          {CATEGORIES.map(cat => (
            <div key={cat.id}>
              <div className="flex items-center gap-1.5 mb-0.5">
                <span
                  className="w-2.5 h-2.5 shrink-0 inline-block border border-current"
                  style={{ backgroundColor: cat.color, borderColor: cat.color }}
                />
                <span className="font-mono text-xs font-bold uppercase" style={{ color: cat.color }}>
                  {cat.label}
                </span>
              </div>
              <ul className="pl-4 space-y-0.5">
                {cat.mechanisms.map(m => (
                  <li key={m} className="font-serif text-xs text-[#0f0f0f] opacity-70">{m}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <button
        data-testid="mechanism-legend-toggle"
        onClick={() => setExpanded(e => !e)}
        className="border-2 border-[#0f0f0f] bg-[#fafafa] px-3 py-1.5 font-mono text-xs font-bold uppercase tracking-wide text-[#0f0f0f] hover:bg-[#0f0f0f] hover:text-[#fafafa] transition-colors"
      >
        {expanded ? '✕ Legend' : '◎ Legend'}
      </button>
    </div>
  )
}
