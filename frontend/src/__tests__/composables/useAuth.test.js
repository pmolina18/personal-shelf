import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'

// Mock the auth API module before importing useAuth
vi.mock('../../api/auth.js', () => ({
  login: vi.fn(),
  register: vi.fn(),
  refresh: vi.fn(),
}))

// Dynamic import so we can reset the singleton module between tests
let useAuth, login, register, refresh

async function loadModules() {
  const authApi = await import('../../api/auth.js')
  login = authApi.login
  register = authApi.register
  refresh = authApi.refresh

  // Reset the module registry so useAuth re-initialises from clean localStorage
  vi.resetModules()

  // Re-apply mock after resetModules
  vi.doMock('../../api/auth.js', () => ({
    login: login,
    register: register,
    refresh: refresh,
  }))

  const mod = await import('../../composables/useAuth.js')
  useAuth = mod.useAuth
}

beforeEach(async () => {
  localStorage.clear()
  vi.clearAllMocks()
  await loadModules()
})

// ── Login guarda tokens en localStorage ─────────────────────
describe('login', () => {
  it('guarda tokens y usuario en localStorage', async () => {
    const apiResponse = {
      access_token: 'access-abc',
      refresh_token: 'refresh-xyz',
      user: { id: 1, email: 'a@b.com', username: 'alice' },
    }
    login.mockResolvedValueOnce(apiResponse)

    const auth = useAuth()
    await auth.login('a@b.com', 'password123')

    expect(localStorage.getItem('access_token')).toBe('access-abc')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-xyz')
    expect(JSON.parse(localStorage.getItem('user'))).toEqual(apiResponse.user)
  })

  it('actualiza el estado reactivo tras login', async () => {
    const apiResponse = {
      access_token: 'tok-1',
      refresh_token: 'ref-1',
      user: { id: 2, email: 'b@c.com', username: 'bob' },
    }
    login.mockResolvedValueOnce(apiResponse)

    const auth = useAuth()
    expect(auth.isAuthenticated.value).toBe(false)

    await auth.login('b@c.com', 'pass1234')

    expect(auth.accessToken.value).toBe('tok-1')
    expect(auth.refreshToken.value).toBe('ref-1')
    expect(auth.user.value).toEqual(apiResponse.user)
    expect(auth.isAuthenticated.value).toBe(true)
  })

  it('llama a la API con email y password', async () => {
    login.mockResolvedValueOnce({
      access_token: 'a',
      refresh_token: 'r',
      user: { id: 1, email: 'x@y.com', username: 'x' },
    })

    const auth = useAuth()
    await auth.login('x@y.com', 'secret99')

    expect(login).toHaveBeenCalledWith('x@y.com', 'secret99')
  })
})

// ── Register guarda tokens en localStorage ──────────────────
describe('register', () => {
  it('guarda tokens y usuario tras registro', async () => {
    const apiResponse = {
      access_token: 'reg-access',
      refresh_token: 'reg-refresh',
      user: { id: 3, email: 'c@d.com', username: 'carol' },
    }
    register.mockResolvedValueOnce(apiResponse)

    const auth = useAuth()
    await auth.register('c@d.com', 'carol', 'password8')

    expect(auth.accessToken.value).toBe('reg-access')
    expect(auth.isAuthenticated.value).toBe(true)
    expect(localStorage.getItem('access_token')).toBe('reg-access')
  })

  it('llama a la API con email, username y password', async () => {
    register.mockResolvedValueOnce({
      access_token: 'a',
      refresh_token: 'r',
      user: { id: 1, email: 'e@f.com', username: 'eve' },
    })

    const auth = useAuth()
    await auth.register('e@f.com', 'eve', 'longpass1')

    expect(register).toHaveBeenCalledWith('e@f.com', 'eve', 'longpass1')
  })
})

// ── Logout limpia estado ────────────────────────────────────
describe('logout', () => {
  it('limpia tokens, usuario y localStorage', async () => {
    // Pre-populate state via login
    login.mockResolvedValueOnce({
      access_token: 'to-clear',
      refresh_token: 'ref-clear',
      user: { id: 1, email: 'a@b.com', username: 'alice' },
    })

    const auth = useAuth()
    await auth.login('a@b.com', 'password1')
    expect(auth.isAuthenticated.value).toBe(true)

    auth.logout()

    expect(auth.accessToken.value).toBeNull()
    expect(auth.refreshToken.value).toBeNull()
    expect(auth.user.value).toBeNull()
    expect(auth.isAuthenticated.value).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })
})

// ── isAuthenticated es reactivo ─────────────────────────────
describe('isAuthenticated reactivity', () => {
  it('cambia de false a true tras login y de vuelta a false tras logout', async () => {
    login.mockResolvedValueOnce({
      access_token: 'tok',
      refresh_token: 'ref',
      user: { id: 1, email: 'a@b.com', username: 'a' },
    })

    const auth = useAuth()
    expect(auth.isAuthenticated.value).toBe(false)

    await auth.login('a@b.com', 'pass1234')
    expect(auth.isAuthenticated.value).toBe(true)

    auth.logout()
    expect(auth.isAuthenticated.value).toBe(false)
  })

  it('es un computed derivado de accessToken', async () => {
    const auth = useAuth()

    // Singleton — all calls share the same refs
    const auth2 = useAuth()
    expect(auth.isAuthenticated).toBe(auth2.isAuthenticated)

    login.mockResolvedValueOnce({
      access_token: 'shared',
      refresh_token: 'r',
      user: { id: 1, email: 'a@b.com', username: 'a' },
    })

    await auth.login('a@b.com', 'pass1234')

    // Both references see the same value
    expect(auth2.isAuthenticated.value).toBe(true)
  })
})

// ── Refresh automático ──────────────────────────────────────
describe('refreshAuth', () => {
  it('renueva tokens con el refresh token actual', async () => {
    // First login to have a refresh token
    login.mockResolvedValueOnce({
      access_token: 'old-access',
      refresh_token: 'old-refresh',
      user: { id: 1, email: 'a@b.com', username: 'a' },
    })

    const auth = useAuth()
    await auth.login('a@b.com', 'pass1234')

    // Now refresh
    refresh.mockResolvedValueOnce({
      access_token: 'new-access',
      refresh_token: 'new-refresh',
    })

    await auth.refreshAuth()

    expect(refresh).toHaveBeenCalledWith('old-refresh')
    expect(auth.accessToken.value).toBe('new-access')
    expect(auth.refreshToken.value).toBe('new-refresh')
    expect(localStorage.getItem('access_token')).toBe('new-access')
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh')
  })

  it('limpia estado si no hay refresh token', async () => {
    const auth = useAuth()

    await expect(auth.refreshAuth()).rejects.toThrow('No refresh token')
    expect(auth.isAuthenticated.value).toBe(false)
  })

  it('limpia estado si el refresh falla', async () => {
    login.mockResolvedValueOnce({
      access_token: 'acc',
      refresh_token: 'ref',
      user: { id: 1, email: 'a@b.com', username: 'a' },
    })

    const auth = useAuth()
    await auth.login('a@b.com', 'pass1234')

    refresh.mockRejectedValueOnce(new Error('Token expired'))

    await expect(auth.refreshAuth()).rejects.toThrow('Refresh failed')
    expect(auth.isAuthenticated.value).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('conserva el usuario actual tras refresh exitoso', async () => {
    const userData = { id: 5, email: 'keep@me.com', username: 'keeper' }
    login.mockResolvedValueOnce({
      access_token: 'a1',
      refresh_token: 'r1',
      user: userData,
    })

    const auth = useAuth()
    await auth.login('keep@me.com', 'pass1234')

    refresh.mockResolvedValueOnce({
      access_token: 'a2',
      refresh_token: 'r2',
    })

    await auth.refreshAuth()

    // User data should be preserved
    expect(auth.user.value).toEqual(userData)
  })
})

// ── Inicialización desde localStorage ───────────────────────
describe('inicialización desde localStorage', () => {
  it('restaura tokens de localStorage al crear el composable', async () => {
    // Pre-populate localStorage before module loads
    localStorage.setItem('access_token', 'persisted-access')
    localStorage.setItem('refresh_token', 'persisted-refresh')
    localStorage.setItem('user', JSON.stringify({ id: 9, email: 'p@q.com', username: 'persisted' }))

    // Re-load module to pick up localStorage values
    await loadModules()

    const auth = useAuth()
    expect(auth.accessToken.value).toBe('persisted-access')
    expect(auth.refreshToken.value).toBe('persisted-refresh')
    expect(auth.user.value).toEqual({ id: 9, email: 'p@q.com', username: 'persisted' })
    expect(auth.isAuthenticated.value).toBe(true)
  })
})
