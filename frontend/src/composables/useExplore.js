import { ref } from 'vue'
import { listExplore, addToShelf } from '../api/media.js'

/**
 * Composable for the Explore catalog — global discovery with social signals.
 * Each invocation returns fresh (independent) state — no module-level sharing.
 */
export function useExplore() {
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(20)
  const pages = ref(0)
  const loading = ref(false)
  const error = ref(null)

  const mediaType = ref(null)
  const search = ref(null)
  const sort = ref('title_asc')

  async function fetchExplore() {
    loading.value = true
    error.value = null
    try {
      const params = {
        page: page.value,
        size: size.value,
        media_type: mediaType.value,
        search: search.value,
        sort: sort.value,
      }
      const result = await listExplore(params)
      items.value = result.items
      total.value = result.total
      pages.value = result.pages
    } catch (err) {
      error.value = err.message || 'Failed to load explore catalog'
    } finally {
      loading.value = false
    }
  }

  function setFilters(newFilters) {
    if (newFilters.media_type !== undefined) mediaType.value = newFilters.media_type
    if (newFilters.search !== undefined) search.value = newFilters.search
    page.value = 1
    return fetchExplore()
  }

  function setPage(newPage) {
    page.value = newPage
    return fetchExplore()
  }

  function setSort(newSort) {
    sort.value = newSort
    page.value = 1
    return fetchExplore()
  }

  async function addItem(item) {
    const result = await addToShelf({
      title: item.title,
      media_type: item.media_type,
      year: item.year,
      creator: item.creator,
    })
    // Remove from local list since user now owns it
    items.value = items.value.filter(
      i => !(i.title === item.title && i.media_type === item.media_type)
    )
    total.value = Math.max(0, total.value - 1)
    return result
  }

  return {
    items,
    total,
    page,
    size,
    pages,
    loading,
    error,
    mediaType,
    search,
    sort,
    fetchExplore,
    setFilters,
    setPage,
    setSort,
    addItem,
  }
}
