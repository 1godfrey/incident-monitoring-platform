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

export default function ServiceCard({ service, checks, onEdit, onDelete }) {
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
        <div className="card-header-right">
          <StatusBadge checks={checks} />
          <div className="card-actions">
            <button className="icon-btn" onClick={onEdit} title="Edit service" aria-label="Edit service">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </button>
            <button className="icon-btn icon-btn-danger" onClick={onDelete} title="Delete service" aria-label="Delete service">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        </div>
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
