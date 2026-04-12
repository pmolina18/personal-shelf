/**
 * HTTP client for authentication endpoints.
 * Uses the native fetch API — same pattern as media.js.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

/**
 * Helper — sends a request and returns parsed JSON.
 * Throws on non-ok responses with the server's error detail.
 */
async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (res.status === 204) return null

  const data = await res.json()

  if (!res.ok) {
    const message = data.detail || JSON.stringify(data)
    throw new Error(message)
  }

  return data
}

// ── Auth ────────────────────────────────────────────────────

/**
 * Register a new user.
 * @param {string} email
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{ access_token: string, refresh_token: string, user: { id: number, email: string, username: string } }>}
 */
export function register(email, username, password) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  })
}

/**
 * Log in with existing credentials.
 * @param {string} identifier - Email address or username.
 * @param {string} password
 * @returns {Promise<{ access_token: string, refresh_token: string, user: { id: number, email: string, username: string } }>}
 */
export function login(identifier, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ identifier, password }),
  })
}

/**
 * Refresh an expired access token.
 * @param {string} refreshToken
 * @returns {Promise<{ access_token: string, refresh_token: string }>}
 */
export function refresh(refreshToken) {
  return request('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}

/**
 * Request access when registration is denied.
 * Creates a GitHub PR to add the email to the allowed users list.
 * @param {string} email
 * @returns {Promise<{ message: string, pr_url: string | null }>}
 */
export function requestAccess(email) {
  return request('/auth/request-access', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}
