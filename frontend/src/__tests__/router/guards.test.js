import { describe, it, expect, beforeEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'

/**
 * Crea un router fresco con las mismas rutas y guards que el de producción.
 * No importamos el router real porque es un singleton y su estado
 * persiste entre tests. En su lugar replicamos la configuración.
 */
function createTestRouter() {
  // Componentes stub — solo necesitamos la navegación, no el render
  const Stub = { template: '<div />' }

  const routes = [
    { path: '/login', name: 'login', component: Stub, meta: { isAuth: true } },
    { path: '/register', name: 'register', component: Stub, meta: { isAuth: true } },
    { path: '/', name: 'catalog', component: Stub },
    { path: '/media/new', name: 'media-create', component: Stub },
    { path: '/media/:id', name: 'media-detail', component: Stub },
    { path: '/stats', name: 'stats', component: Stub },
    { path: '/import-export', name: 'import-export', component: Stub },
    { path: '/feed', name: 'feed', component: Stub },
    { path: '/friends', name: 'friends', component: Stub },
    { path: '/friends/:id/collection', name: 'friend-collection', component: Stub },
  ]

  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  // Misma lógica del guard de producción (router/index.js)
  router.beforeEach((to) => {
    const isAuthenticated = !!localStorage.getItem('access_token')

    if (to.meta.isAuth && isAuthenticated) {
      return { name: 'catalog' }
    }

    if (!to.meta.isAuth && !isAuthenticated) {
      return { name: 'login' }
    }
  })

  return router
}

describe('Navigation guards', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  // ── Sin auth: redirige a login ──────────────────────────────
  describe('sin autenticación', () => {
    it('redirige a /login al intentar acceder a /', async () => {
      const router = createTestRouter()
      await router.push('/')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('login')
    })

    it('redirige a /login al intentar acceder a /stats', async () => {
      const router = createTestRouter()
      await router.push('/stats')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('login')
    })

    it('redirige a /login al intentar acceder a /feed', async () => {
      const router = createTestRouter()
      await router.push('/feed')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('login')
    })

    it('redirige a /login al intentar acceder a /friends', async () => {
      const router = createTestRouter()
      await router.push('/friends')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('login')
    })

    it('redirige a /login al intentar acceder a /media/new', async () => {
      const router = createTestRouter()
      await router.push('/media/new')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('login')
    })

    it('redirige a /login al intentar acceder a /import-export', async () => {
      const router = createTestRouter()
      await router.push('/import-export')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('login')
    })

    it('permite acceder a /login sin auth', async () => {
      const router = createTestRouter()
      await router.push('/login')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('login')
    })

    it('permite acceder a /register sin auth', async () => {
      const router = createTestRouter()
      await router.push('/register')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('register')
    })
  })

  // ── Con auth: redirige a catálogo desde rutas de auth ───────
  describe('con autenticación', () => {
    beforeEach(() => {
      localStorage.setItem('access_token', 'valid-token')
    })

    it('redirige a catálogo al intentar acceder a /login', async () => {
      const router = createTestRouter()
      await router.push('/login')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('catalog')
    })

    it('redirige a catálogo al intentar acceder a /register', async () => {
      const router = createTestRouter()
      await router.push('/register')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('catalog')
    })
  })

  // ── Con auth: permite acceso a rutas protegidas ─────────────
  describe('acceso a rutas protegidas con auth', () => {
    beforeEach(() => {
      localStorage.setItem('access_token', 'valid-token')
    })

    it('permite acceder a / (catálogo)', async () => {
      const router = createTestRouter()
      await router.push('/')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('catalog')
    })

    it('permite acceder a /stats', async () => {
      const router = createTestRouter()
      await router.push('/stats')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('stats')
    })

    it('permite acceder a /feed', async () => {
      const router = createTestRouter()
      await router.push('/feed')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('feed')
    })

    it('permite acceder a /friends', async () => {
      const router = createTestRouter()
      await router.push('/friends')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('friends')
    })

    it('permite acceder a /media/new', async () => {
      const router = createTestRouter()
      await router.push('/media/new')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('media-create')
    })

    it('permite acceder a /media/42', async () => {
      const router = createTestRouter()
      await router.push('/media/42')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('media-detail')
    })

    it('permite acceder a /import-export', async () => {
      const router = createTestRouter()
      await router.push('/import-export')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('import-export')
    })

    it('permite acceder a /friends/7/collection', async () => {
      const router = createTestRouter()
      await router.push('/friends/7/collection')
      await router.isReady()

      expect(router.currentRoute.value.name).toBe('friend-collection')
    })
  })
})
