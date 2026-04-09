import { describe, it, expect, beforeEach } from 'vitest'
import router from '../../router/index.js'

const expectedRoutes = [
  // Auth routes (public)
  { path: '/login', name: 'login', isAuth: true },
  { path: '/register', name: 'register', isAuth: true },
  // Protected routes
  { path: '/', name: 'catalog' },
  { path: '/media/new', name: 'media-create' },
  { path: '/media/:id', name: 'media-detail' },
  { path: '/stats', name: 'stats' },
  { path: '/import-export', name: 'import-export' },
  { path: '/feed', name: 'feed' },
  { path: '/friends', name: 'friends' },
  { path: '/friends/:id/collection', name: 'friend-collection' },
]

describe('Router', () => {
  const routes = router.options.routes

  beforeEach(() => {
    localStorage.clear()
  })

  it('define exactamente 10 rutas', () => {
    expect(routes).toHaveLength(10)
  })

  it.each(expectedRoutes)(
    'tiene la ruta $path con nombre "$name"',
    ({ path, name }) => {
      const route = routes.find((r) => r.path === path)
      expect(route).toBeDefined()
      expect(route.name).toBe(name)
    },
  )

  it('todos los componentes son funciones (lazy loading)', () => {
    for (const route of routes) {
      expect(typeof route.component).toBe('function')
    }
  })

  it('rutas de auth tienen meta.isAuth = true', () => {
    const authRoutes = routes.filter((r) => r.meta?.isAuth)
    expect(authRoutes).toHaveLength(2)
    expect(authRoutes.map((r) => r.name).sort()).toEqual(['login', 'register'])
  })
})
