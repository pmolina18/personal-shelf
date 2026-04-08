import { ref, computed } from 'vue'
import {
  createMedia,
  listMedia,
  getMedia,
  updateMedia,
  deleteMedia,
  updateStatus,
  updateRating,
  updateTags,
} from '../api/media.js'

/**
 * Composable encapsulating media CRUD, filters, pagination state, and API calls.
 * Each invocation returns fresh (independent) state — no module-level sharing.
 */
export function useMedia() {
  // ── Catalog listing state ───────────────────────────────
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(20)
  const pages = ref(0)
  const filters = ref({
    media_type: null,
    status: null,
    search: null,
    tag: null,
  })
  const loading = ref(false)
  const error = ref(null)

  const hasActiveFilters = computed(() => {
    return !!(filters.value.media_type || filters.value.status || filters.value.search || filters.value.tag)
  })

  async function fetchMedia() {
    loading.value = true
    error.value = null
    try {
      const params = {
        page: page.value,
        size: size.value,
        ...filters.value,
      }
      const result = await listMedia(params)
      items.value = result.items
      total.value = result.total
      pages.value = result.pages
    } catch (err) {
      error.value = err.message || 'Failed to load catalog'
    } finally {
      loading.value = false
    }
  }

  function setFilters(newFilters) {
    filters.value = { ...newFilters }
    page.value = 1
    return fetchMedia()
  }

  function setPage(newPage) {
    page.value = newPage
    return fetchMedia()
  }

  // ── Single item state ───────────────────────────────────
  const currentItem = ref(null)
  const itemLoading = ref(false)
  const itemError = ref(null)
  const successMsg = ref('')

  let successTimer = null

  function flashSuccess(msg) {
    successMsg.value = msg
    clearTimeout(successTimer)
    successTimer = setTimeout(() => { successMsg.value = '' }, 2500)
  }

  async function fetchItem(id) {
    itemLoading.value = true
    itemError.value = null
    try {
      currentItem.value = await getMedia(id)
    } catch (err) {
      itemError.value = err.message || 'Failed to load item'
    } finally {
      itemLoading.value = false
    }
  }

  async function create(data) {
    itemError.value = null
    const created = await createMedia(data)
    return created
  }

  async function update(id, data) {
    itemError.value = null
    try {
      currentItem.value = await updateMedia(id, data)
      flashSuccess('Changes saved')
    } catch (err) {
      itemError.value = err.message || 'Failed to update item'
    }
  }

  async function remove(id) {
    itemError.value = null
    await deleteMedia(id)
  }

  async function changeStatus(id, status) {
    itemError.value = null
    try {
      currentItem.value = await updateStatus(id, status)
      flashSuccess('Status updated')
    } catch (err) {
      itemError.value = err.message || 'Failed to update status'
    }
  }

  async function changeRating(id, rating) {
    itemError.value = null
    try {
      currentItem.value = await updateRating(id, rating)
      flashSuccess('Rating saved')
    } catch (err) {
      itemError.value = err.message || 'Failed to update rating'
    }
  }

  async function changeTags(id, tags) {
    itemError.value = null
    try {
      currentItem.value = await updateTags(id, tags)
      flashSuccess('Tags updated')
    } catch (err) {
      itemError.value = err.message || 'Failed to update tags'
    }
  }

  return {
    // Catalog listing
    items,
    total,
    page,
    size,
    pages,
    filters,
    loading,
    error,
    hasActiveFilters,
    fetchMedia,
    setFilters,
    setPage,
    // Single item operations
    currentItem,
    itemLoading,
    itemError,
    successMsg,
    fetchItem,
    create,
    update,
    remove,
    changeStatus,
    changeRating,
    changeTags,
  }
}
