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
import type { StrategyOutcome } from '../../types/simulation'

interface Props {
  outcome: StrategyOutcome
  strategyDisplayName: string
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
    <div className="bg-[#fafafa] border-2 border-[#0f0f0f] px-3 py-2 font-mono text-xs text-[#0f0f0f]">
      <p className="font-bold mb-1">{label === 'Cool' ? 'Cool-off' : `Turn ${label}`}</p>
      {pub  && <p>Public: {pub.value.toFixed(1)}</p>}
      {priv && <p>Private: {priv.value.toFixed(1)}</p>}
      {gap  && <p className="opacity-50">Gap: {gap}</p>}
    </div>
  )
}

export default function TrajectoryChart({ outcome, strategyDisplayName }: Props) {
  const data = buildChartData(outcome)

  return (
    <div
      data-testid={`trajectory-chart-${outcome.strategy_id}`}
      className="bg-white border-2 border-[#0f0f0f] p-4"
    >
      {/* Card header */}
      <div className="mb-4">
        <span className="font-mono text-sm font-bold text-[#0f0f0f] uppercase tracking-wide">{strategyDisplayName}</span>
        <span data-testid={`chart-dot-${outcome.strategy_id}`} className="sr-only">{outcome.verdict}</span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
          <Area
            type="monotone"
            dataKey="public"
            stroke="none"
            fill="rgba(15,15,15,0.06)"
            isAnimationActive={false}
          />
          <XAxis
            dataKey="turn"
            tick={{ fill: '#0f0f0f', fontSize: 11, fontFamily: 'Courier New' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 10]}
            ticks={[0, 2.5, 5, 7.5, 10]}
            tick={{ fill: '#0f0f0f', fontSize: 11, fontFamily: 'Courier New' }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <ReferenceLine y={5} stroke="#0f0f0f" strokeDasharray="2 4" opacity={0.3} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '11px', color: '#0f0f0f', paddingTop: '8px', fontFamily: 'Courier New' }}
          />
          {/* Public stance — solid black */}
          <Line
            type="monotone"
            dataKey="public"
            name="Public"
            stroke="#0f0f0f"
            strokeWidth={2}
            dot={{ r: 3, fill: '#0f0f0f', strokeWidth: 0 }}
            isAnimationActive={false}
          />
          {/* Private stance — dashed black */}
          <Line
            type="monotone"
            dataKey="private"
            name="Private"
            stroke="#0f0f0f"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ r: 3, fill: '#0f0f0f', strokeWidth: 0 }}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
