import { ref } from 'vue'
import {
  createSuggestion,
  listSuggestions,
  listMySuggestions,
} from '../api/suggestions.js'

/**
 * Composable para el buzón de sugerencias.
 * Cada invocación devuelve refs independientes — sin estado compartido a nivel de módulo.
 */
export function useSuggestions() {
  const suggestions = ref([])
  const mySuggestions = ref([])
  const loading = ref(false)
  const error = ref(null)
  const page = ref(1)
  const totalPages = ref(0)
  const total = ref(0)
  const myPage = ref(1)
  const myTotalPages = ref(0)
  const myTotal = ref(0)
  const successMsg = ref(null)

  let successTimer = null

  async function fetchAll(p = 1) {
    loading.value = true
    error.value = null
    try {
      const data = await listSuggestions({ page: p, size: 20 })
      suggestions.value = data.items
      total.value = data.total
      page.value = data.page
      totalPages.value = Math.ceil(data.total / data.size) || 0
    } catch (err) {
      error.value = err.message || 'Error loading suggestions'
    } finally {
      loading.value = false
    }
  }

  async function fetchMine(p = 1) {
    loading.value = true
    error.value = null
    try {
      const data = await listMySuggestions({ page: p, size: 20 })
      mySuggestions.value = data.items
      myTotal.value = data.total
      myPage.value = data.page
      myTotalPages.value = Math.ceil(data.total / data.size) || 0
    } catch (err) {
      error.value = err.message || 'Error loading your suggestions'
    } finally {
      loading.value = false
    }
  }

  async function submit(data) {
    loading.value = true
    error.value = null
    successMsg.value = null
    try {
      const created = await createSuggestion(data)
      suggestions.value.unshift(created)
      total.value++
      successMsg.value = 'Suggestion submitted successfully!'
      if (successTimer) clearTimeout(successTimer)
      successTimer = setTimeout(() => { successMsg.value = null }, 2500)
    } catch (err) {
      error.value = err.message || 'Error submitting suggestion'
    } finally {
      loading.value = false
    }
  }

  return {
    suggestions,
    mySuggestions,
    loading,
    error,
    page,
    totalPages,
    total,
    myPage,
    myTotalPages,
    myTotal,
    successMsg,
    fetchAll,
    fetchMine,
    submit,
  }
}
