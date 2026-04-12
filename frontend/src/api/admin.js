/**
 * HTTP client for admin dashboard endpoints.
 * Uses the native fetch API — same pattern as media.js.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

/**
 * Build Authorization header with the stored JWT token.
 * @returns {Object} Headers object with Bearer token if available.
 */
function authHeaders() {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Helper — sends a request and returns parsed JSON.
 * Throws on non-ok responses with the server's error detail.
 */
async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`
  const headers = {
    'Content-Type': 'application/json',
    ...authHeaders(),
    ...options.headers,
  }
  const res = await fetch(url, { ...options, headers })

  if (res.status === 204) return null

  const data = await res.json()

  if (!res.ok) {
    const message = data.detail || JSON.stringify(data)
    throw new Error(message)
  }

  return data
}

// ── Admin ───────────────────────────────────────────────────

/**
 * Fetch global admin statistics.
 * Requires admin privileges (Bearer token from an admin user).
 * @returns {Promise<Object>} AdminStatsResponse
 */
export function getAdminStats() {
  return request('/admin/stats')
}
