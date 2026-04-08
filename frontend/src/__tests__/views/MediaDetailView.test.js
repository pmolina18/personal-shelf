import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { ref, computed } from 'vue'
import MediaDetailView from '../../views/MediaDetailView.vue'

// ── Router mocks ──────────────────────────────────────────
const mockPush = vi.fn()
let mockRoute = { name: 'media-create', params: {} }

vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => mockRoute),
  useRouter: vi.fn(() => ({ push: mockPush })),
}))

// ── useMedia mock ─────────────────────────────────────────
const mockFetchItem = vi.fn()
const mockCreate = vi.fn()
const mockUpdate = vi.fn()
const mockRemove = vi.fn()
const mockChangeStatus = vi.fn()
const mockChangeRating = vi.fn()
const mockChangeTags = vi.fn()
const mockFetchMedia = vi.fn()

let mockState = {}

function createMockState(overrides = {}) {
  return {
    currentItem: ref(overrides.currentItem ?? null),
    itemLoading: ref(overrides.itemLoading ?? false),
    itemError: ref(overrides.itemError ?? null),
    successMsg: ref(overrides.successMsg ?? ''),
    fetchItem: mockFetchItem,
    create: mockCreate,
    update: mockUpdate,
    remove: mockRemove,
    changeStatus: mockChangeStatus,
    changeRating: mockChangeRating,
    changeTags: mockChangeTags,
    items: ref([]),
    total: ref(0),
    page: ref(1),
    size: ref(20),
    pages: ref(0),
    filters: ref({}),
    loading: ref(false),
    error: ref(null),
    hasActiveFilters: computed(() => false),
    fetchMedia: mockFetchMedia,
    setFilters: vi.fn(),
    setPage: vi.fn(),
  }
}

vi.mock('../../composables/useMedia.js', () => ({
  useMedia: vi.fn(() => mockState),
}))

function mountView(routeOverride = {}, stateOverrides = {}) {
  mockRoute = { name: 'media-create', params: {}, ...routeOverride }
  mockState = createMockState(stateOverrides)

  return shallowMount(MediaDetailView, {
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Requirement 12.1: create mode shows "Add Media" ──────
describe('MediaDetailView — modo creación', () => {
  it('muestra "Add Media" cuando la ruta es media-create', () => {
    const wrapper = mountView({ name: 'media-create', params: {} })

    expect(wrapper.find('h1').text()).toBe('Add Media')
  })

  it('no invoca fetchItem en modo creación', () => {
    mountView({ name: 'media-create', params: {} })

    expect(mockFetchItem).not.toHaveBeenCalled()
  })

  it('renderiza MediaForm en modo creación', () => {
    const wrapper = mountView({ name: 'media-create', params: {} })

    expect(wrapper.find('media-form-stub').exists()).toBe(true)
  })
})

// ── Requirement 12.2: edit mode invokes fetchItem ─────────
describe('MediaDetailView — modo edición', () => {
  it('invoca fetchItem con el ID de la ruta al montar', () => {
    mountView({ name: 'media-detail', params: { id: '42' } })

    expect(mockFetchItem).toHaveBeenCalledWith('42')
  })
})

// ── Requirement 12.3: create submit invokes create + navigates ──
describe('MediaDetailView — envío en modo creación', () => {
  it('invoca create y navega al detalle del item creado', async () => {
    mockCreate.mockResolvedValueOnce({ id: 99 })
    const wrapper = mountView({ name: 'media-create', params: {} })

    // Find the MediaForm stub and trigger its submit event
    const formStub = wrapper.findComponent('media-form-stub')
    await formStub.vm.$emit('submit', { title: 'New Item', media_type: 'movie' })
    await flushPromises()

    expect(mockCreate).toHaveBeenCalledWith({ title: 'New Item', media_type: 'movie' })
    expect(mockPush).toHaveBeenCalledWith('/media/99')
  })
})

// ── Requirement 12.4: delete + confirm invokes remove + navigates ──
describe('MediaDetailView — eliminación', () => {
  it('clic en Delete + confirmar invoca remove y navega al catálogo', async () => {
    mockRemove.mockResolvedValueOnce(null)
    const item = { id: 42, title: 'Test', media_type: 'movie', status: 'pending', tags: [], rating: null }
    const wrapper = mountView(
      { name: 'media-detail', params: { id: '42' } },
      { currentItem: item },
    )

    // Click the delete button
    const deleteBtn = wrapper.find('.btn-delete')
    await deleteBtn.trigger('click')

    // Confirm via ConfirmDialog stub
    const dialog = wrapper.findComponent('confirm-dialog-stub')
    await dialog.vm.$emit('confirm')
    await flushPromises()

    expect(mockRemove).toHaveBeenCalledWith('42')
    expect(mockPush).toHaveBeenCalledWith('/')
  })
})

// ── Requirement 12.5: loading indicator ───────────────────
describe('MediaDetailView — estados de carga y error', () => {
  it('muestra indicador de carga cuando itemLoading es true', () => {
    const wrapper = mountView(
      { name: 'media-detail', params: { id: '42' } },
      { itemLoading: true },
    )

    const loading = wrapper.find('.detail-loading')
    expect(loading.exists()).toBe(true)
    expect(loading.text()).toContain('Loading')
  })

  // ── Requirement 12.6: error message ───────────────────────
  it('muestra mensaje de error cuando itemError tiene valor', () => {
    const wrapper = mountView(
      { name: 'media-detail', params: { id: '42' } },
      { itemError: 'Item not found' },
    )

    const error = wrapper.find('.detail-error')
    expect(error.exists()).toBe(true)
    expect(error.text()).toBe('Item not found')
  })
})
