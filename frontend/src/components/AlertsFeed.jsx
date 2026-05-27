function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000)
  if (diff < 60)    return `${diff}s ago`
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function AlertCard({ incident }) {
  const isDown = incident.status === 'DOWN'
  return (
    <div className={`alert-card ${isDown ? 'alert-down' : 'alert-recovered'}`}>
      <div className="alert-header">
        <span className="alert-emoji" aria-hidden="true">{isDown ? '🔴' : '✅'}</span>
        <span className="alert-service-name">{incident.service_name}</span>
        <span className={`alert-status-badge ${isDown ? 'down' : 'recovered'}`}>
          {incident.status}
        </span>
        <span className="alert-time">{timeAgo(incident.triggered_at)}</span>
      </div>

      <div className="alert-url">{incident.service_url}</div>

      <div className="alert-meta">
        <span>HTTP {incident.http_status_code ?? 'No response'}</span>
        <span className="alert-meta-dot">·</span>
        <span>{incident.response_time_ms} ms latency</span>
      </div>

      {incident.content_detail && (
        <div className="alert-content-detail">
          Content check: {incident.content_detail}
        </div>
      )}
    </div>
  )
}

export default function AlertsFeed({ incidents }) {
  return (
    <section className="alerts-feed">
      <div className="alerts-feed-header">
        <h2 className="alerts-title">Recent Alerts</h2>
        <span className="alerts-subtitle">State-change events · same as Discord</span>
      </div>

      {!incidents || incidents.length === 0 ? (
        <div className="alerts-empty">
          No alerts yet — all services have been stable since monitoring started.
        </div>
      ) : (
        <div className="alerts-list">
          {incidents.map((incident) => (
            <AlertCard key={incident.id} incident={incident} />
          ))}
        </div>
      )}
    </section>
  )
}
