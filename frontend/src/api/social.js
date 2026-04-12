/**
 * HTTP client wrapping all Social (friends + feed) backend endpoints.
 * Uses the native fetch API with a configurable BASE_URL.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

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

// ── Friend Requests ─────────────────────────────────────────

/** Send a friend request to a user by username. */
export function sendFriendRequest(username) {
  return request('/friends/requests', {
    method: 'POST',
    body: JSON.stringify({ username }),
  })
}

/** Get pending friend requests received by the current user. */
export function getPendingRequests() {
  return request('/friends/requests/pending')
}

/** Get pending friend requests sent by the current user. */
export function getSentRequests() {
  return request('/friends/requests/sent')
}

/** Accept a pending friend request. */
export function acceptRequest(id) {
  return request(`/friends/requests/${id}/accept`, { method: 'POST' })
}

/** Reject a pending friend request. */
export function rejectRequest(id) {
  return request(`/friends/requests/${id}/reject`, { method: 'POST' })
}

// ── Friends ─────────────────────────────────────────────────

/** List all confirmed friends. */
export function listFriends() {
  return request('/friends')
}

/** Remove a friend. Returns null (204). */
export function removeFriend(id) {
  return request(`/friends/${id}`, { method: 'DELETE' })
}

/** Search users by username substring. */
export function searchUsers(query = '') {
  const qs = encodeURIComponent(query)
  return request(`/friends/search?q=${qs}`)
}

// ── Feed ────────────────────────────────────────────────────

/**
 * Get the social feed (paginated).
 * @param {number} [page=1]
 */
export function getFeed(page = 1) {
  return request(`/feed?page=${page}&size=20`)
}

/**
 * Get a friend's media collection with optional filters.
 * @param {number} friendId
 * @param {Object} params - { media_type, status, search, tag, page, size }
 */
export function getFriendCollection(friendId, params = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value)
    }
  }
  const qs = query.toString()
  return request(`/feed/friends/${friendId}/collection${qs ? `?${qs}` : ''}`)
}
