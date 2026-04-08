import { describe, it, expect, beforeEach, vi } from 'vitest'
import fc from 'fast-check'
import {
  createMedia,
  listMedia,
  getMedia,
  updateMedia,
  deleteMedia,
  updateStatus,
  updateRating,
  updateTags,
  exportCatalog,
  importCatalog,
} from '../../api/media.js'

// ── Helpers ─────────────────────────────────────────────────

function mockFetch(status, body = null, ok = true) {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({
      ok,
      status,
      json: () => Promise.resolve(body),
    }),
  )
}

// ── Tests ───────────────────────────────────────────────────

describe('API media layer', () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn()
  })

  // ── request() behaviour (tested indirectly via getMedia) ──

  describe('request() internal helper', () => {
    it('parses JSON on successful response', async () => {
      const payload = { id: 1, title: 'Test' }
      mockFetch(200, payload)

      const result = await getMedia(1)

      expect(result).toEqual(payload)
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media/1',
        expect.objectContaining({
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        }),
      )
    })

    it('returns null for status 204', async () => {
      mockFetch(204)

      const result = await deleteMedia(99)

      expect(result).toBeNull()
    })

    it('throws Error with detail message on non-ok response', async () => {
      mockFetch(400, { detail: 'Bad request' }, false)

      await expect(getMedia(1)).rejects.toThrow('Bad request')
    })

    it('throws Error with stringified body when detail is missing', async () => {
      mockFetch(422, { errors: ['invalid'] }, false)

      await expect(getMedia(1)).rejects.toThrow(JSON.stringify({ errors: ['invalid'] }))
    })
  })

  // ── listMedia ─────────────────────────────────────────────

  describe('listMedia', () => {
    it('includes non-empty params in query string', async () => {
      mockFetch(200, { items: [], total: 0, pages: 0 })

      await listMedia({ media_type: 'movie', status: 'completed', page: 1 })

      const url = globalThis.fetch.mock.calls[0][0]
      expect(url).toContain('media_type=movie')
      expect(url).toContain('status=completed')
      expect(url).toContain('page=1')
    })

    it('omits null, undefined and empty string params', async () => {
      mockFetch(200, { items: [], total: 0, pages: 0 })

      await listMedia({ media_type: null, status: undefined, search: '', tag: 'sci-fi' })

      const url = globalThis.fetch.mock.calls[0][0]
      expect(url).not.toContain('media_type')
      expect(url).not.toContain('status')
      expect(url).not.toContain('search')
      expect(url).toContain('tag=sci-fi')
    })

    it('calls /api/media without query string when params are empty', async () => {
      mockFetch(200, { items: [], total: 0, pages: 0 })

      await listMedia({})

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media',
        expect.any(Object),
      )
    })
  })

  // ── createMedia ───────────────────────────────────────────

  describe('createMedia', () => {
    it('sends POST with JSON body to /api/media', async () => {
      const body = { title: 'New Movie', media_type: 'movie' }
      mockFetch(201, { id: 1, ...body })

      await createMedia(body)

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(body),
        }),
      )
    })
  })

  // ── updateMedia ───────────────────────────────────────────

  describe('updateMedia', () => {
    it('sends PUT with ID and body to /api/media/:id', async () => {
      const body = { title: 'Updated' }
      mockFetch(200, { id: 5, ...body })

      await updateMedia(5, body)

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media/5',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(body),
        }),
      )
    })
  })

  // ── deleteMedia ───────────────────────────────────────────

  describe('deleteMedia', () => {
    it('sends DELETE to /api/media/:id and returns null', async () => {
      mockFetch(204)

      const result = await deleteMedia(7)

      expect(result).toBeNull()
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media/7',
        expect.objectContaining({ method: 'DELETE' }),
      )
    })
  })

  // ── updateStatus ──────────────────────────────────────────

  describe('updateStatus', () => {
    it('sends PATCH to /api/media/:id/status with status payload', async () => {
      mockFetch(200, { id: 3, status: 'completed' })

      await updateStatus(3, 'completed')

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media/3/status',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ status: 'completed' }),
        }),
      )
    })
  })

  // ── updateRating ──────────────────────────────────────────

  describe('updateRating', () => {
    it('sends PATCH to /api/media/:id/rating with rating payload', async () => {
      mockFetch(200, { id: 3, rating: 8 })

      await updateRating(3, 8)

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media/3/rating',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ rating: 8 }),
        }),
      )
    })
  })

  // ── updateTags ────────────────────────────────────────────

  describe('updateTags', () => {
    it('sends PUT to /api/media/:id/tags with tags payload', async () => {
      mockFetch(200, { id: 3, tags: ['action', 'sci-fi'] })

      await updateTags(3, ['action', 'sci-fi'])

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/media/3/tags',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ tags: ['action', 'sci-fi'] }),
        }),
      )
    })
  })

  // ── exportCatalog ─────────────────────────────────────────

  describe('exportCatalog', () => {
    it('sends GET to /api/export', async () => {
      mockFetch(200, [{ id: 1 }])

      await exportCatalog()

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/export',
        expect.objectContaining({ method: 'GET' }),
      )
    })
  })

  // ── importCatalog ─────────────────────────────────────────

  describe('importCatalog', () => {
    it('sends POST with JSON body to /api/import', async () => {
      const data = [{ title: 'Imported' }]
      mockFetch(200, { created: 1, errors: [] })

      await importCatalog(data)

      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/import',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data),
        }),
      )
    })
  })
})


// ── Property-Based Tests ────────────────────────────────────

describe('Property: Correct query string construction in listMedia', () => {
  /**
   * Feature: frontend-unit-tests, Property 1: Correct query string construction in listMedia
   * Validates: Requirements 2.4, 2.5
   *
   * For any params object with an arbitrary mix of null, undefined, empty-string,
   * and non-empty values, the URL built by listMedia must include exactly those
   * parameters whose value is non-null, non-undefined, and non-empty-string,
   * and must omit all others.
   */

  const paramValue = fc.oneof(
    fc.constant(null),
    fc.constant(undefined),
    fc.constant(''),
    fc.string({ minLength: 1, maxLength: 20 }).filter(s => s.trim().length > 0),
  )

  const pageValue = fc.oneof(
    fc.constant(null),
    fc.constant(undefined),
    fc.constant(''),
    fc.integer({ min: 1, max: 100 }),
  )

  const paramsArb = fc.record({
    media_type: paramValue,
    status: paramValue,
    search: paramValue,
    tag: paramValue,
    page: pageValue,
    size: pageValue,
  })

  it('URL contains exactly the non-null/non-empty params and omits the rest', async () => {
    await fc.assert(
      fc.asyncProperty(paramsArb, async (params) => {
        globalThis.fetch = vi.fn(() =>
          Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [], total: 0, pages: 0 }),
          }),
        )

        await listMedia(params)

        const url = globalThis.fetch.mock.calls[0][0]
        const qsIndex = url.indexOf('?')
        const searchParams = qsIndex >= 0
          ? new URLSearchParams(url.slice(qsIndex + 1))
          : new URLSearchParams()

        for (const [key, value] of Object.entries(params)) {
          if (value !== null && value !== undefined && value !== '') {
            // Non-empty value must appear in the query string
            expect(searchParams.has(key)).toBe(true)
            expect(searchParams.get(key)).toBe(String(value))
          } else {
            // Null, undefined, or empty string must be absent
            expect(searchParams.has(key)).toBe(false)
          }
        }
      }),
      { numRuns: 100 },
    )
  })
})
