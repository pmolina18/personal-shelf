import { describe, it, expect } from 'vitest'
import router from '../../router/index.js'

const expectedRoutes = [
  { path: '/', name: 'catalog' },
  { path: '/media/new', name: 'media-create' },
  { path: '/media/:id', name: 'media-detail' },
  { path: '/stats', name: 'stats' },
  { path: '/import-export', name: 'import-export' },
]

describe('Router', () => {
  const routes = router.options.routes

  it('define exactamente 5 rutas', () => {
    expect(routes).toHaveLength(5)
  })

  it.each(expectedRoutes)(
    'tiene la ruta $path con nombre "$name"',
    ({ path, name }) => {
      const route = routes.find((r) => r.path === path)
      expect(route).toBeDefined()
      expect(route.name).toBe(name)
    }
  )

  it('todos los componentes son funciones (lazy loading)', () => {
    for (const route of routes) {
      expect(typeof route.component).toBe('function')
    }
  })
})
