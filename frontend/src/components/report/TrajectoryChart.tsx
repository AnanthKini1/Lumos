import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { StrategyOutcome, VerdictCategory } from '../../types/simulation'

interface Props {
  outcome: StrategyOutcome
  strategyDisplayName: string
}

const VERDICT_TOP_BORDER: Record<VerdictCategory, string> = {
  GENUINE_BELIEF_SHIFT: 'border-t-emerald-400',
  PARTIAL_SHIFT:        'border-t-sky-400',
  SURFACE_COMPLIANCE:   'border-t-amber-400',
  BACKFIRE:             'border-t-rose-400',
  NO_MOVEMENT:          'border-t-slate-300',
}

const VERDICT_DOT: Record<VerdictCategory, string> = {
  GENUINE_BELIEF_SHIFT: 'bg-emerald-500',
  PARTIAL_SHIFT:        'bg-sky-500',
  SURFACE_COMPLIANCE:   'bg-amber-500',
  BACKFIRE:             'bg-rose-500',
  NO_MOVEMENT:          'bg-slate-400',
}

export function buildChartData(outcome: StrategyOutcome) {
  const { trajectory, cooling_off } = outcome
  const data = trajectory.public_stance_per_turn.map((pub, i) => ({
    turn: i + 1,
    public: pub,
    private: trajectory.private_stance_per_turn[i],
  }))
  data.push({
    turn: 'Cool' as unknown as number,
    public: cooling_off.post_reflection_stance,
    private: cooling_off.post_reflection_stance,
  })
  return data
}

interface TooltipPayload {
  name: string
  value: number
  color: string
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayload[]; label?: string | number }) {
  if (!active || !payload?.length) return null
  const pub  = payload.find(p => p.name === 'Public')
  const priv = payload.find(p => p.name === 'Private')
  const gap  = pub && priv ? Math.abs(pub.value - priv.value).toFixed(1) : null

  return (
    <div className="bg-white border border-slate-200 shadow-md rounded-lg px-3 py-2 text-xs text-slate-900">
      <p className="font-semibold mb-1">{label === 'Cool' ? 'Cool-off' : `Turn ${label}`}</p>
      {pub  && <p>Public: <span className="font-mono">{pub.value.toFixed(1)}</span></p>}
      {priv && <p>Private: <span className="font-mono">{priv.value.toFixed(1)}</span></p>}
      {gap  && <p className="text-slate-500">Gap: <span className="font-mono">{gap}</span></p>}
    </div>
  )
}

export default function TrajectoryChart({ outcome, strategyDisplayName }: Props) {
  const data = buildChartData(outcome)
  const topBorder = VERDICT_TOP_BORDER[outcome.verdict]
  const dot = VERDICT_DOT[outcome.verdict]

  return (
    <div
      data-testid={`trajectory-chart-${outcome.strategy_id}`}
      className={`bg-white border border-slate-200 rounded-xl p-4 shadow-sm border-t-2 ${topBorder}`}
    >
      {/* Card header */}
      <div className="flex items-center gap-2 mb-4">
        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${dot}`} data-testid={`chart-dot-${outcome.strategy_id}`} />
        <span className="text-sm font-semibold text-slate-800">{strategyDisplayName}</span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
          {/* Subtle fill under public line to visually suggest the gap */}
          <Area
            type="monotone"
            dataKey="public"
            stroke="none"
            fill="rgba(139,92,246,0.08)"
            isAnimationActive={false}
          />
          <XAxis
            dataKey="turn"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 10]}
            ticks={[0, 2.5, 5, 7.5, 10]}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <ReferenceLine y={5} stroke="#cbd5e1" strokeDasharray="2 4" />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '11px', color: '#64748b', paddingTop: '8px' }}
          />
          {/* Public stance — solid sky */}
          <Line
            type="monotone"
            dataKey="public"
            name="Public"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={{ r: 3, fill: '#38bdf8', strokeWidth: 0 }}
            isAnimationActive={false}
          />
          {/* Private stance — dashed violet */}
          <Line
            type="monotone"
            dataKey="private"
            name="Private"
            stroke="#a78bfa"
            strokeWidth={2}
            strokeDasharray="5 3"
            dot={{ r: 3, fill: '#a78bfa', strokeWidth: 0 }}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
