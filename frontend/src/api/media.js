/**
 * HTTP client wrapping all Media Tracker backend endpoints.
 * Uses the native fetch API with a configurable BASE_URL.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')
const IMAGES_BASE_URL = (import.meta.env.VITE_IMAGES_BASE_URL || '').replace(/\/+$/, '')

/**
 * Resolve an image URL from the backend.
 * In dev, image_url is already relative ("/images/foo.jpg") and the Vite proxy handles it.
 * In production, VITE_IMAGES_BASE_URL prefixes the path with the backend origin.
 * @param {string|null} imageUrl - The image_url from the API response.
 * @returns {string|null}
 */
export function resolveImageUrl(imageUrl) {
  if (!imageUrl) return null
  if (imageUrl.startsWith('http')) return imageUrl
  return `${IMAGES_BASE_URL}${imageUrl.startsWith('/') ? imageUrl : '/' + imageUrl}`
}

/**
 * Helper — sends a request and returns parsed JSON.
 * Throws on non-ok responses with the server's error detail.
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

  // 204 No Content — nothing to parse
  if (res.status === 204) return null

  const data = await res.json()

  if (!res.ok) {
    const message = data.detail || JSON.stringify(data)
    throw new Error(message)
  }

  return data
}

// ── Media CRUD ──────────────────────────────────────────────

/** Create a new media item. */
export function createMedia(body) {
  return request('/media', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

/**
 * List catalog with optional filters and pagination.
 * @param {Object} params - { media_type, status, search, tag, page, size }
 */
export function listMedia(params = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value)
    }
  }
  const qs = query.toString()
  return request(`/media${qs ? `?${qs}` : ''}`)
}

/** Get a single media item by ID. */
export function getMedia(id) {
  return request(`/media/${id}`)
}

/** Update a media item (partial). */
export function updateMedia(id, body) {
  return request(`/media/${id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

/** Delete a media item. Returns null (204). */
export function deleteMedia(id) {
  return request(`/media/${id}`, { method: 'DELETE' })
}

// ── Status / Rating / Tags ──────────────────────────────────

/** Update the consumption status of a media item. */
export function updateStatus(id, status) {
  return request(`/media/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

/** Assign a rating (1-10) to a media item. */
export function updateRating(id, rating) {
  return request(`/media/${id}/rating`, {
    method: 'PATCH',
    body: JSON.stringify({ rating }),
  })
}

/** Replace the tags of a media item. */
export function updateTags(id, tags) {
  return request(`/media/${id}/tags`, {
    method: 'PUT',
    body: JSON.stringify({ tags }),
  })
}

// ── Metadata ────────────────────────────────────────────────

/** Search metadata suggestions for a title and media type. */
export function searchMetadata(title, mediaType) {
  const params = new URLSearchParams({ title, media_type: mediaType })
  return request(`/media/metadata-search?${params}`)
}

// ── Image ───────────────────────────────────────────────────

/** Get the image URL for a media item. */
export function getMediaImage(id) {
  return request(`/media/${id}/image`)
}

// ── Statistics ──────────────────────────────────────────────

/** Get catalog statistics. */
export function getStats() {
  return request('/stats', { method: 'GET' })
}

// ── Export / Import ─────────────────────────────────────────

/** Export the entire catalog as JSON. */
export function exportCatalog() {
  return request('/export', { method: 'GET' })
}

/** Import catalog from a JSON payload. */
export function importCatalog(data) {
  return request('/import', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
