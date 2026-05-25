import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts'

function formatTime(isoStr) {
  return new Date(isoStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{
      background: '#0f172a',
      border: '1px solid #334155',
      borderRadius: 6,
      padding: '6px 10px',
      fontSize: '0.75rem',
      color: '#f1f5f9',
    }}>
      <div style={{ color: d.success ? '#22c55e' : '#ef4444', fontWeight: 700 }}>
        {d.success ? '✓ OK' : '✗ Down'}
        {d.status_code ? ` · ${d.status_code}` : ''}
      </div>
      <div>{Math.round(d.latency)} ms</div>
      <div style={{ color: '#64748b' }}>{formatTime(d.time)}</div>
    </div>
  )
}

export default function LatencyChart({ checks }) {
  if (!checks || checks.length === 0) {
    return <div className="chart-empty">No data yet</div>
  }

  // Recharts expects data oldest→newest; API returns newest→oldest
  const data = [...checks].reverse().map((c) => ({
    time: c.checked_at,
    latency: c.response_time_ms,
    success: c.success,
    status_code: c.status_code,
  }))

  // Colour each dot by success/failure
  function dotColor(entry) {
    return entry.success ? '#22c55e' : '#ef4444'
  }

  return (
    <div className="chart-wrapper">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
          <XAxis dataKey="time" hide />
          <YAxis
            tick={{ fontSize: 9, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="latency"
            stroke="#38bdf8"
            strokeWidth={1.5}
            dot={(props) => {
              const { cx, cy, payload } = props
              return (
                <circle
                  key={`dot-${cx}-${cy}`}
                  cx={cx}
                  cy={cy}
                  r={3}
                  fill={dotColor(payload)}
                  stroke="none"
                />
              )
            }}
            activeDot={{ r: 4, fill: '#38bdf8' }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
