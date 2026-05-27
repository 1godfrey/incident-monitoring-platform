import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import ServiceCard from './components/ServiceCard'
import AlertsFeed from './components/AlertsFeed'
import AddServiceModal from './components/AddServiceModal'
import { fetchSummary, fetchHealthChecks, fetchIncidents } from './api/client'

export default function App() {
  const [summary, setSummary] = useState([])
  const [healthData, setHealthData] = useState({})
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)

  const loadAll = useCallback(async () => {
    try {
      // Fetch summary, incidents, and health history in parallel
      const [{ services }, alertData] = await Promise.all([
        fetchSummary(),
        fetchIncidents(50),
      ])
      setSummary(services)
      setIncidents(alertData)

      const results = await Promise.allSettled(
        services.map((s) => fetchHealthChecks(s.service_id, 30))
      )
      const map = {}
      services.forEach((s, i) => {
        map[s.service_id] = results[i].status === 'fulfilled' ? results[i].value : []
      })
      setHealthData(map)
      setLastRefresh(new Date())
      setError(null)
    } catch {
      setError('Unable to reach the monitoring API. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAll()
    const id = setInterval(loadAll, 30_000)
    return () => clearInterval(id)
  }, [loadAll])

  // Derived global stats
  const servicesDown = summary.filter((s) => {
    const checks = healthData[s.service_id] ?? []
    return checks.length > 0 && !checks[0].success
  }).length

  const avgUptime =
    summary.length > 0
      ? (summary.reduce((acc, s) => acc + s.uptime_percentage, 0) / summary.length).toFixed(1)
      : '—'

  return (
    <div className="app">
      <Header
        onAddService={() => setShowAddModal(true)}
        lastRefresh={lastRefresh}
        onRefresh={loadAll}
      />

      <div className="stats-bar">
        <div className="stat">
          <span className="stat-value">{summary.length}</span>
          <span className="stat-label">Services</span>
        </div>
        <div className="stat">
          <span
            className="stat-value"
            style={{ color: servicesDown > 0 ? 'var(--error)' : 'var(--success)' }}
          >
            {summary.length === 0 ? '—' : servicesDown === 0 ? 'All Clear' : `${servicesDown} Down`}
          </span>
          <span className="stat-label">Current Status</span>
        </div>
        <div className="stat">
          <span className="stat-value">{avgUptime}{avgUptime !== '—' ? '%' : ''}</span>
          <span className="stat-label">Avg Uptime 24h</span>
        </div>
      </div>

      <main className="main-content">
        {loading && <div className="loading-state">Loading monitoring data…</div>}

        {!loading && error && <div className="error-state">{error}</div>}

        {!loading && !error && (
          <AlertsFeed incidents={incidents} />
        )}

        {!loading && !error && summary.length === 0 && (
          <div className="empty-state">
            <p>No services are being monitored yet.</p>
            <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
              Add your first service
            </button>
          </div>
        )}

        <div className="services-grid">
          {summary.map((service) => (
            <ServiceCard
              key={service.service_id}
              service={service}
              checks={healthData[service.service_id] ?? []}
            />
          ))}
        </div>
      </main>

      {showAddModal && (
        <AddServiceModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false)
            loadAll()
          }}
        />
      )}
    </div>
  )
}
