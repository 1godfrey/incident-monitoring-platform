import LatencyChart from './LatencyChart'

function StatusBadge({ checks }) {
  if (checks.length === 0) {
    return <span className="status-badge unknown"><span className="status-dot unknown" />Pending</span>
  }
  const up = checks[0].success
  return (
    <span className={`status-badge ${up ? 'up' : 'down'}`}>
      <span className={`status-dot ${up ? 'up' : 'down'}`} />
      {up ? 'Operational' : 'Down'}
    </span>
  )
}

function fmt(ms) {
  if (ms == null || ms === 0) return '—'
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`
}

function timeAgo(dateStr) {
  if (!dateStr) return null
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

export default function ServiceCard({ service, checks }) {
  const {
    service_name,
    service_url,
    uptime_percentage,
    avg_response_time_ms,
    total_checks,
    last_checked_at,
  } = service

  const uptimeColor =
    uptime_percentage >= 99 ? 'var(--success)'
    : uptime_percentage >= 90 ? 'var(--warning)'
    : 'var(--error)'

  return (
    <div className="service-card">
      {/* Header row */}
      <div className="card-header">
        <div>
          <div className="card-name">{service_name}</div>
          <div className="card-url">{service_url}</div>
        </div>
        <StatusBadge checks={checks} />
      </div>

      {/* Stats row */}
      <div className="card-stats">
        <div className="card-stat">
          <span className="card-stat-value" style={{ color: uptimeColor }}>
            {total_checks === 0 ? '—' : `${uptime_percentage.toFixed(1)}%`}
          </span>
          <span className="card-stat-label">Uptime</span>
        </div>
        <div className="card-stat">
          <span className="card-stat-value">{fmt(avg_response_time_ms)}</span>
          <span className="card-stat-label">Avg Latency</span>
        </div>
        <div className="card-stat">
          <span className="card-stat-value">{total_checks}</span>
          <span className="card-stat-label">Checks</span>
        </div>
      </div>

      {/* Latency chart */}
      <div>
        <div className="chart-label">Response time (last {Math.min(checks.length, 30)} checks)</div>
        <LatencyChart checks={checks} />
      </div>

      {/* Last checked timestamp */}
      {last_checked_at && (
        <div className="card-last-checked">Checked {timeAgo(last_checked_at)}</div>
      )}
    </div>
  )
}
