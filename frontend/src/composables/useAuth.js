import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, refresh as apiRefresh } from '../api/auth.js'

/**
 * Singleton composable for authentication state.
 * Unlike useMedia, this shares state across all components —
 * reactive refs are defined at module level.
 */

// ── Module-level singleton state ────────────────────────────
const accessToken = ref(localStorage.getItem('access_token') || null)
const refreshToken = ref(localStorage.getItem('refresh_token') || null)

const storedUser = localStorage.getItem('user')
const user = ref(storedUser ? JSON.parse(storedUser) : null)

const isAuthenticated = computed(() => !!accessToken.value)
const isAdmin = computed(() => user.value?.is_admin ?? false)

// ── Helpers ─────────────────────────────────────────────────

function persistTokens(access, refresh, userData) {
  accessToken.value = access
  refreshToken.value = refresh
  user.value = userData

  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
  if (userData) {
    localStorage.setItem('user', JSON.stringify(userData))
  }
}

function clearAuth() {
  accessToken.value = null
  refreshToken.value = null
  user.value = null

  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

// ── Public methods ──────────────────────────────────────────

async function login(identifier, password) {
  const data = await apiLogin(identifier, password)
  persistTokens(data.access_token, data.refresh_token, data.user)
  return data
}

async function register(email, username, password) {
  const data = await apiRegister(email, username, password)
  persistTokens(data.access_token, data.refresh_token, data.user)
  return data
}

function logout() {
  clearAuth()
}

async function refreshAuth() {
  if (!refreshToken.value) {
    clearAuth()
    throw new Error('No refresh token')
  }
  try {
    const data = await apiRefresh(refreshToken.value)
    persistTokens(data.access_token, data.refresh_token, user.value)
    return data
  } catch {
    clearAuth()
    throw new Error('Refresh failed')
  }
}

// ── Composable export ───────────────────────────────────────

export function useAuth() {
  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    refreshAuth,
  }
}
