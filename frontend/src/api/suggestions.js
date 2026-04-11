/**
 * HTTP client para endpoints del buzón de sugerencias.
 * Sigue el mismo patrón que media.js / recommendations.js.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

/**
 * Helper — envía una petición y devuelve JSON parseado.
 * Lanza error en respuestas no-ok con el detalle del servidor.
 */
async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`
  const token = localStorage.getItem('access_token')
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }
  const res = await fetch(url, { ...options, headers })

  if (res.status === 204) return null

  const data = await res.json()

  if (!res.ok) {
    const message = data.detail || JSON.stringify(data)
    const err = new Error(message)
    err.status = res.status
    throw err
  }

  return data
}

/** Crear una nueva sugerencia. */
export function createSuggestion(body) {
  return request('/suggestions', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

/**
 * Listar todas las sugerencias (paginadas).
 * @param {Object} params - { page, size }
 */
export function listSuggestions(params = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value)
    }
  }
  const qs = query.toString()
  return request(`/suggestions${qs ? `?${qs}` : ''}`)
}

/**
 * Listar las sugerencias del usuario autenticado (paginadas).
 * @param {Object} params - { page, size }
 */
export function listMySuggestions(params = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value)
    }
  }
  const qs = query.toString()
  return request(`/suggestions/mine${qs ? `?${qs}` : ''}`)
}
