/**
 * HTTP client para endpoints de recomendaciones entre amigos.
 * Sigue el mismo patrón que social.js: helper request() con JWT de localStorage.
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

/** Enviar una recomendación a un amigo. */
export function sendRecommendation(receiverId, mediaItemId, message) {
  return request('/recommendations', {
    method: 'POST',
    body: JSON.stringify({
      receiver_id: receiverId,
      media_item_id: mediaItemId,
      message: message || null,
    }),
  })
}

/**
 * Listar recomendaciones recibidas (paginadas).
 * @param {number} page
 * @param {boolean} pendingOnly
 */
export function listRecommendations(page = 1, pendingOnly = false) {
  const params = new URLSearchParams({ page, pending_only: pendingOnly })
  return request(`/recommendations?${params}`)
}

/** Obtener conteo de recomendaciones pendientes. */
export function getUnreadCount() {
  return request('/recommendations/unread-count')
}

/** Aceptar una recomendación (añade el item al catálogo como pending). */
export function acceptRecommendation(id) {
  return request(`/recommendations/${id}/accept`, { method: 'POST' })
}

/** Descartar una recomendación. */
export function dismissRecommendation(id) {
  return request(`/recommendations/${id}/dismiss`, { method: 'POST' })
}
