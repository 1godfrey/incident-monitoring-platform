// In dev the Vite proxy rewrites /api/* → backend (no prefix).
// On Vercel VITE_API_URL is the full backend origin, so we call it directly.
const BASE = import.meta.env.VITE_API_URL ?? '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
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

export const updateService = (serviceId, name, url, jsonPath = null, expectedValue = null) =>
  request(`/services/${serviceId}`, {
    method: 'PUT',
    body: JSON.stringify({ name, url, json_path: jsonPath, expected_value: expectedValue }),
  })

export const deleteService = (serviceId) =>
  request(`/services/${serviceId}`, { method: 'DELETE' })

export const fetchIncidents = (limit = 50) =>
  request(`/incidents?limit=${limit}`)
