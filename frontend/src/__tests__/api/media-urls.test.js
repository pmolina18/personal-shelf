import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * Tests for dynamic URL construction in media.js.
 * Validates: Requirements 1.4, 1.5, 2.4
 *
 * We use vi.resetModules() + dynamic import() to re-evaluate the module
 * with different env vars on each test.
 */

// Helper: mock fetch so request() doesn't blow up
function installFetchMock() {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1 }),
    }),
  )
}

beforeEach(() => {
  vi.resetModules()
  vi.unstubAllEnvs()
  installFetchMock()
})

// ── Requirement 1.4: Default BASE_URL is /api ───────────────
describe('BASE_URL defaults', () => {
  it('without VITE_API_BASE_URL, request() builds URLs from /api', async () => {
    const { getMedia } = await import('../../api/media.js')

    await getMedia(42)

    const url = globalThis.fetch.mock.calls[0][0]
    expect(url).toBe('/api/media/42')
  })

  it('with VITE_API_BASE_URL set, request() uses the absolute URL', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://backend.onrender.com/api')

    const { getMedia } = await import('../../api/media.js')

    await getMedia(7)

    const url = globalThis.fetch.mock.calls[0][0]
    expect(url).toBe('https://backend.onrender.com/api/media/7')
  })
})


// ── Requirement 2.4: Default IMAGES_BASE_URL ────────────────
describe('IMAGES_BASE_URL defaults', () => {
  it('without VITE_IMAGES_BASE_URL, resolveImageUrl returns the path as-is', async () => {
    const { resolveImageUrl } = await import('../../api/media.js')

    expect(resolveImageUrl('/images/foo.jpg')).toBe('/images/foo.jpg')
  })

  it('with VITE_IMAGES_BASE_URL set, resolveImageUrl prepends the base', async () => {
    vi.stubEnv('VITE_IMAGES_BASE_URL', 'https://backend.onrender.com')

    const { resolveImageUrl } = await import('../../api/media.js')

    expect(resolveImageUrl('/images/foo.jpg')).toBe(
      'https://backend.onrender.com/images/foo.jpg',
    )
  })
})

// ── resolveImageUrl edge cases ──────────────────────────────
describe('resolveImageUrl edge cases', () => {
  it('returns null for null input', async () => {
    const { resolveImageUrl } = await import('../../api/media.js')
    expect(resolveImageUrl(null)).toBeNull()
  })

  it('returns absolute http URLs unchanged', async () => {
    const { resolveImageUrl } = await import('../../api/media.js')
    expect(resolveImageUrl('http://external.com/img.jpg')).toBe('http://external.com/img.jpg')
  })

  it('returns absolute https URLs unchanged', async () => {
    const { resolveImageUrl } = await import('../../api/media.js')
    expect(resolveImageUrl('https://cdn.example.com/pic.png')).toBe(
      'https://cdn.example.com/pic.png',
    )
  })
})

// ── Requirement 1.5: No duplicate slashes ───────────────────
describe('no duplicate slashes in URL construction', () => {
  it('BASE_URL with trailing slash does not produce double slashes', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://backend.onrender.com/api/')

    const { getMedia } = await import('../../api/media.js')

    await getMedia(1)

    const url = globalThis.fetch.mock.calls[0][0]
    expect(url).not.toMatch(/\/\/media/)
    expect(url).toBe('https://backend.onrender.com/api/media/1')
  })

  it('IMAGES_BASE_URL with trailing slash does not produce double slashes', async () => {
    vi.stubEnv('VITE_IMAGES_BASE_URL', 'https://backend.onrender.com/')

    const { resolveImageUrl } = await import('../../api/media.js')

    const result = resolveImageUrl('/images/foo.jpg')
    expect(result).not.toMatch(/\/\/images/)
    expect(result).toBe('https://backend.onrender.com/images/foo.jpg')
  })
})
