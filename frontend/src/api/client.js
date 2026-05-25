// All requests go through /api so the Vite dev proxy and the nginx
// production proxy both route them to the FastAPI backend correctly.
const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const fetchSummary = (windowHours = 24) =>
  request(`/summary?window_hours=${windowHours}`)

export const fetchServices = () => request('/services/')

export const fetchHealthChecks = (serviceId, limit = 30) =>
  request(`/health/${serviceId}?limit=${limit}`)

export const addService = (name, url, jsonPath = null, expectedValue = null) =>
  request('/services/', {
    method: 'POST',
    body: JSON.stringify({ name, url, json_path: jsonPath, expected_value: expectedValue }),
  })
