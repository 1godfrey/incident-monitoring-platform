import { useState } from 'react'
import { addService } from '../api/client'

export default function AddServiceModal({ onClose, onSuccess }) {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [jsonPath, setJsonPath] = useState('')
  const [expectedValue, setExpectedValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await addService(
        name.trim(),
        url.trim(),
        jsonPath.trim() || null,
        expectedValue.trim() || null,
      )
      onSuccess()
    } catch (err) {
      setError(err.message ?? 'Failed to add service')
    } finally {
      setSubmitting(false)
    }
  }

  // Close on backdrop click
  function handleBackdropClick(e) {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <h2 className="modal-title" id="modal-title">Add Service</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="svc-name">Service name</label>
            <input
              id="svc-name"
              className="form-input"
              type="text"
              placeholder="e.g. GitHub"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="svc-url">URL to monitor (Include https)</label>
            <input
              id="svc-url"
              className="form-input"
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>

          {/* Optional content check — leave both blank to use HTTP-only checking */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '.25rem' }}>
            <p style={{ fontSize: '.75rem', color: 'var(--text-muted)', marginBottom: '.75rem' }}>
              Optional: alert when a JSON field has an unexpected value (e.g. GitHub status API)
            </p>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-json-path">JSON path</label>
              <input
                id="svc-json-path"
                className="form-input"
                type="text"
                placeholder="status.indicator"
                value={jsonPath}
                onChange={(e) => setJsonPath(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-expected">Expected value (healthy)</label>
              <input
                id="svc-expected"
                className="form-input"
                type="text"
                placeholder="none"
                value={expectedValue}
                onChange={(e) => setExpectedValue(e.target.value)}
              />
            </div>
          </div>

          {error && <p className="form-error">{error}</p>}

          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting || !name || !url}>
              {submitting ? 'Adding…' : 'Add Service'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
