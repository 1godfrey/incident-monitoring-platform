export default function Header({ onAddService, lastRefresh, onRefresh }) {
  const formattedTime = lastRefresh
    ? lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : null

  return (
    <header className="header">
      <div className="header-brand">
        {/* Radar / signal icon */}
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 12m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />
          <path d="M4.929 4.929a10 10 0 1 1 14.142 14.142a10 10 0 0 1 -14.142 -14.142z" />
          <path d="M7.757 7.757a6 6 0 1 1 8.486 8.486a6 6 0 0 1 -8.486 -8.486z" />
        </svg>
        <span className="header-title">Incident Monitor</span>
      </div>

      <div className="header-right">
        {formattedTime && (
          <span className="header-refresh">Last updated {formattedTime}</span>
        )}
        <button className="btn btn-ghost" onClick={onRefresh} title="Refresh now">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5" />
            <path d="M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5" />
          </svg>
          Refresh
        </button>
        <button className="btn btn-primary" onClick={onAddService}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Service
        </button>
      </div>
    </header>
  )
}
