import { describe, it, expect, vi, beforeEach } from 'vitest'
import fc from 'fast-check'
import { useMedia } from '../../composables/useMedia.js'
import {
  listMedia,
  createMedia,
  getMedia,
  updateMedia,
  deleteMedia,
  updateStatus,
  updateRating,
  updateTags,
} from '../../api/media.js'

vi.mock('../../api/media.js', () => ({
  listMedia: vi.fn(),
  createMedia: vi.fn(),
  getMedia: vi.fn(),
  updateMedia: vi.fn(),
  deleteMedia: vi.fn(),
  updateStatus: vi.fn(),
  updateRating: vi.fn(),
  updateTags: vi.fn(),
}))

const listResponse = {
  items: [{ id: 1, title: 'Test Movie' }],
  total: 42,
  pages: 3,
}

const singleItem = { id: 1, title: 'Test Movie', status: 'pending', rating: 7, tags: ['action'] }

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Requirement 3.1: Independent instances ──────────────────
describe('independent instances', () => {
  it('two invocations return distinct refs', () => {
    const a = useMedia()
    const b = useMedia()
    expect(a.items).not.toBe(b.items)
    expect(a.page).not.toBe(b.page)
    expect(a.loading).not.toBe(b.loading)
    expect(a.currentItem).not.toBe(b.currentItem)
  })
})

// ── Requirements 3.2, 3.3, 3.4: fetchMedia ─────────────────
describe('fetchMedia', () => {
  it('loading changes during request', async () => {
    let resolvePromise
    listMedia.mockImplementation(() => new Promise(r => { resolvePromise = r }))

    const { fetchMedia, loading } = useMedia()
    expect(loading.value).toBe(false)

    const promise = fetchMedia()
    expect(loading.value).toBe(true)

    resolvePromise(listResponse)
    await promise

    expect(loading.value).toBe(false)
  })

  it('items, total and pages update on success', async () => {
    listMedia.mockResolvedValueOnce(listResponse)

    const { fetchMedia, items, total, pages } = useMedia()
    await fetchMedia()

    expect(items.value).toEqual(listResponse.items)
    expect(total.value).toBe(42)
    expect(pages.value).toBe(3)
  })

  it('error is captured on failure', async () => {
    listMedia.mockRejectedValueOnce(new Error('Network error'))

    const { fetchMedia, error, loading } = useMedia()
    await fetchMedia()

    expect(error.value).toBe('Network error')
    expect(loading.value).toBe(false)
  })
})

// ── Requirement 3.5: setFilters ─────────────────────────────
describe('setFilters', () => {
  it('page resets to 1 and fetchMedia invoked with updated filters', async () => {
    listMedia.mockResolvedValue(listResponse)

    const { setFilters, page, filters } = useMedia()
    page.value = 5

    await setFilters({ media_type: 'movie', status: null, search: null, tag: null })

    expect(page.value).toBe(1)
    expect(filters.value.media_type).toBe('movie')
    expect(listMedia).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, media_type: 'movie' })
    )
  })
})

// ── Requirement 3.6: setPage ────────────────────────────────
describe('setPage', () => {
  it('page updates and fetchMedia invoked', async () => {
    listMedia.mockResolvedValue(listResponse)

    const { setPage, page } = useMedia()
    await setPage(3)

    expect(page.value).toBe(3)
    expect(listMedia).toHaveBeenCalledWith(
      expect.objectContaining({ page: 3 })
    )
  })
})

// ── Requirement 3.7: hasActiveFilters ───────────────────────
describe('hasActiveFilters', () => {
  it('returns false when all filters are null', () => {
    const { hasActiveFilters } = useMedia()
    expect(hasActiveFilters.value).toBe(false)
  })

  it('returns true when at least one filter is set', async () => {
    listMedia.mockResolvedValue(listResponse)

    const { hasActiveFilters, setFilters } = useMedia()
    await setFilters({ media_type: 'book', status: null, search: null, tag: null })

    expect(hasActiveFilters.value).toBe(true)
  })
})

// ── Requirement 3.8: fetchItem ──────────────────────────────
describe('fetchItem', () => {
  it('currentItem updates and itemLoading reflects loading state', async () => {
    let resolvePromise
    getMedia.mockImplementation(() => new Promise(r => { resolvePromise = r }))

    const { fetchItem, currentItem, itemLoading } = useMedia()
    expect(itemLoading.value).toBe(false)

    const promise = fetchItem(1)
    expect(itemLoading.value).toBe(true)

    resolvePromise(singleItem)
    await promise

    expect(itemLoading.value).toBe(false)
    expect(currentItem.value).toEqual(singleItem)
  })
})

// ── Requirement 3.12: create ────────────────────────────────
describe('create', () => {
  it('calls createMedia and returns the created object', async () => {
    const created = { id: 99, title: 'New Item' }
    createMedia.mockResolvedValueOnce(created)

    const { create } = useMedia()
    const result = await create({ title: 'New Item' })

    expect(createMedia).toHaveBeenCalledWith({ title: 'New Item' })
    expect(result).toEqual(created)
  })
})

// ── Requirement 3.9: update ─────────────────────────────────
describe('update', () => {
  it('updates currentItem and shows successMsg', async () => {
    vi.useFakeTimers()
    const updated = { ...singleItem, title: 'Updated' }
    updateMedia.mockResolvedValueOnce(updated)

    const { update, currentItem, successMsg } = useMedia()
    await update(1, { title: 'Updated' })

    expect(updateMedia).toHaveBeenCalledWith(1, { title: 'Updated' })
    expect(currentItem.value).toEqual(updated)
    expect(successMsg.value).toBe('Changes saved')

    vi.advanceTimersByTime(2500)
    expect(successMsg.value).toBe('')

    vi.useRealTimers()
  })
})

// ── Requirement 3.13: remove ────────────────────────────────
describe('remove', () => {
  it('calls deleteMedia with the correct id', async () => {
    deleteMedia.mockResolvedValueOnce(null)

    const { remove } = useMedia()
    await remove(5)

    expect(deleteMedia).toHaveBeenCalledWith(5)
  })
})

// ── Requirement 3.10: changeStatus, changeRating, changeTags
describe('changeStatus', () => {
  it('updates currentItem and shows temporary successMsg', async () => {
    vi.useFakeTimers()
    const updated = { ...singleItem, status: 'completed' }
    updateStatus.mockResolvedValueOnce(updated)

    const { changeStatus, currentItem, successMsg } = useMedia()
    await changeStatus(1, 'completed')

    expect(updateStatus).toHaveBeenCalledWith(1, 'completed')
    expect(currentItem.value).toEqual(updated)
    expect(successMsg.value).toBe('Status updated')

    vi.advanceTimersByTime(2500)
    expect(successMsg.value).toBe('')

    vi.useRealTimers()
  })
})

describe('changeRating', () => {
  it('updates currentItem and shows temporary successMsg', async () => {
    vi.useFakeTimers()
    const updated = { ...singleItem, rating: 9 }
    updateRating.mockResolvedValueOnce(updated)

    const { changeRating, currentItem, successMsg } = useMedia()
    await changeRating(1, 9)

    expect(updateRating).toHaveBeenCalledWith(1, 9)
    expect(currentItem.value).toEqual(updated)
    expect(successMsg.value).toBe('Rating saved')

    vi.advanceTimersByTime(2500)
    expect(successMsg.value).toBe('')

    vi.useRealTimers()
  })
})

describe('changeTags', () => {
  it('updates currentItem and shows temporary successMsg', async () => {
    vi.useFakeTimers()
    const updated = { ...singleItem, tags: ['drama', 'comedy'] }
    updateTags.mockResolvedValueOnce(updated)

    const { changeTags, currentItem, successMsg } = useMedia()
    await changeTags(1, ['drama', 'comedy'])

    expect(updateTags).toHaveBeenCalledWith(1, ['drama', 'comedy'])
    expect(currentItem.value).toEqual(updated)
    expect(successMsg.value).toBe('Tags updated')

    vi.advanceTimersByTime(2500)
    expect(successMsg.value).toBe('')

    vi.useRealTimers()
  })
})

// ── Requirement 3.11: error handling ────────────────────────
describe('error handling', () => {
  it('fetchItem sets itemError on failure', async () => {
    getMedia.mockRejectedValueOnce(new Error('Not found'))

    const { fetchItem, itemError } = useMedia()
    await fetchItem(999)

    expect(itemError.value).toBe('Not found')
  })

  it('update sets itemError on failure', async () => {
    updateMedia.mockRejectedValueOnce(new Error('Update failed'))

    const { update, itemError } = useMedia()
    await update(1, { title: 'x' })

    expect(itemError.value).toBe('Update failed')
  })

  it('changeStatus sets itemError on failure', async () => {
    updateStatus.mockRejectedValueOnce(new Error('Status error'))

    const { changeStatus, itemError } = useMedia()
    await changeStatus(1, 'completed')

    expect(itemError.value).toBe('Status error')
  })

  it('changeRating sets itemError on failure', async () => {
    updateRating.mockRejectedValueOnce(new Error('Rating error'))

    const { changeRating, itemError } = useMedia()
    await changeRating(1, 5)

    expect(itemError.value).toBe('Rating error')
  })

  it('changeTags sets itemError on failure', async () => {
    updateTags.mockRejectedValueOnce(new Error('Tags error'))

    const { changeTags, itemError } = useMedia()
    await changeTags(1, ['x'])

    expect(itemError.value).toBe('Tags error')
  })
})

// ── Property: hasActiveFilters reflects filter presence ──────
// **Validates: Requirements 3.7**
describe('Property: hasActiveFilters reflects filter presence', () => {
  const filterArb = fc.record({
    media_type: fc.oneof(fc.constant(null), fc.string({ minLength: 1 })),
    status: fc.oneof(fc.constant(null), fc.string({ minLength: 1 })),
    search: fc.oneof(fc.constant(null), fc.string({ minLength: 1 })),
    tag: fc.oneof(fc.constant(null), fc.string({ minLength: 1 })),
  })

  it('hasActiveFilters is true iff at least one filter value is truthy', () => {
    fc.assert(
      fc.property(filterArb, (filterObj) => {
        const { hasActiveFilters, filters } = useMedia()
        filters.value = filterObj

        const expected = !!(filterObj.media_type || filterObj.status || filterObj.search || filterObj.tag)
        expect(hasActiveFilters.value).toBe(expected)
      }),
      { numRuns: 100 }
    )
  })
})
