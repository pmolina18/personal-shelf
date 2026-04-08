import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { ref, computed } from 'vue'
import CatalogView from '../../views/CatalogView.vue'

const mockFetchMedia = vi.fn()
const mockSetFilters = vi.fn()
const mockSetPage = vi.fn()

let mockState = {}

function createMockState(overrides = {}) {
  return {
    items: ref(overrides.items ?? []),
    total: ref(overrides.total ?? 0),
    page: ref(overrides.page ?? 1),
    pages: ref(overrides.pages ?? 0),
    loading: ref(overrides.loading ?? false),
    error: ref(overrides.error ?? null),
    hasActiveFilters: computed(() => overrides.hasActiveFilters ?? false),
    fetchMedia: mockFetchMedia,
    setFilters: mockSetFilters,
    setPage: mockSetPage,
  }
}

vi.mock('../../composables/useMedia.js', () => ({
  useMedia: vi.fn(() => mockState),
}))

function mountView(stateOverrides = {}) {
  mockState = createMockState(stateOverrides)

  return shallowMount(CatalogView, {
    global: {
      stubs: {
        FilterBar: true,
        MediaCard: true,
        Pagination: true,
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Requirement 11.1: fetchMedia invoked on mount ───────────
describe('CatalogView', () => {
  it('invoca fetchMedia al montar', () => {
    mountView()
    expect(mockFetchMedia).toHaveBeenCalledOnce()
  })

  // ── Requirement 11.2: loading indicator ─────────────────────
  it('muestra indicador de carga cuando loading es true', () => {
    const wrapper = mountView({ loading: true })

    expect(wrapper.find('.catalog-loading').exists()).toBe(true)
    expect(wrapper.find('.catalog-loading').text()).toContain('Loading')
  })

  // ── Requirement 11.3: error message ─────────────────────────
  it('muestra mensaje de error cuando error tiene valor', () => {
    const wrapper = mountView({ error: 'Failed to load catalog' })

    expect(wrapper.find('.catalog-error').exists()).toBe(true)
    expect(wrapper.find('.catalog-error').text()).toBe('Failed to load catalog')
  })

  // ── Requirement 11.4: empty state without filters ───────────
  it('muestra estado vacío con enlace cuando items vacío sin filtros', () => {
    const wrapper = mountView({ items: [], hasActiveFilters: false })

    const empty = wrapper.find('.catalog-empty')
    expect(empty.exists()).toBe(true)
    expect(empty.text()).toContain('No items in your catalog yet')

    const link = wrapper.find('a')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('Add your first item')
  })

  // ── Requirement 11.5: empty state with active filters ───────
  it('muestra "No items match your filters" cuando items vacío con filtros activos', () => {
    const wrapper = mountView({ items: [], hasActiveFilters: true })

    const empty = wrapper.find('.catalog-empty')
    expect(empty.exists()).toBe(true)
    expect(empty.text()).toContain('No items match your filters')
  })

  // ── Requirement 11.6: renders MediaCard and Pagination ──────
  it('renderiza MediaCard por cada item y Pagination cuando hay items', () => {
    const items = [
      { id: 1, title: 'Movie A' },
      { id: 2, title: 'Book B' },
      { id: 3, title: 'Series C' },
    ]
    const wrapper = mountView({ items, total: 30, pages: 2, page: 1 })

    const cards = wrapper.findAllComponents({ name: 'MediaCard' })
    expect(cards).toHaveLength(3)

    const pagination = wrapper.findComponent({ name: 'Pagination' })
    expect(pagination.exists()).toBe(true)
  })
})
