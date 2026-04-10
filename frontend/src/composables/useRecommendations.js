import { ref } from 'vue'
import {
  sendRecommendation,
  listRecommendations,
  getUnreadCount as apiGetUnreadCount,
  acceptRecommendation as apiAccept,
  dismissRecommendation as apiDismiss,
} from '../api/recommendations.js'

/**
 * Composable para recomendaciones entre amigos.
 * Cada invocación devuelve refs independientes — sin estado compartido a nivel de módulo.
 */
export function useRecommendations() {
  const recommendations = ref([])
  const unreadCount = ref(0)
  const total = ref(0)
  const pages = ref(0)
  const page = ref(1)
  const loading = ref(false)
  const error = ref(null)

  async function fetchRecommendations(p = 1, pendingOnly = false) {
    loading.value = true
    error.value = null
    try {
      const data = await listRecommendations(p, pendingOnly)
      recommendations.value = data.items
      total.value = data.total
      pages.value = data.pages
      page.value = data.page
    } catch (err) {
      error.value = err.message || 'Error al cargar recomendaciones'
    } finally {
      loading.value = false
    }
  }

  async function fetchUnreadCount() {
    try {
      const data = await apiGetUnreadCount()
      unreadCount.value = data.count
    } catch {
      // Silenciar errores de polling
    }
  }

  async function send(receiverId, mediaItemId, message) {
    return await sendRecommendation(receiverId, mediaItemId, message)
  }

  async function accept(id) {
    // Optimistic update
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    const idx = recommendations.value.findIndex(r => r.id === id)
    if (idx !== -1) recommendations.value[idx] = { ...recommendations.value[idx], status: 'accepted' }
    try {
      await apiAccept(id)
    } catch (err) {
      // Revertir
      unreadCount.value++
      if (idx !== -1) recommendations.value[idx] = { ...recommendations.value[idx], status: 'pending' }
      error.value = err.message || 'Error al aceptar recomendación'
    }
  }

  async function dismiss(id) {
    // Optimistic update
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    const idx = recommendations.value.findIndex(r => r.id === id)
    if (idx !== -1) recommendations.value[idx] = { ...recommendations.value[idx], status: 'dismissed' }
    try {
      await apiDismiss(id)
    } catch (err) {
      // Revertir
      unreadCount.value++
      if (idx !== -1) recommendations.value[idx] = { ...recommendations.value[idx], status: 'pending' }
      error.value = err.message || 'Error al descartar recomendación'
    }
  }

  return {
    recommendations,
    unreadCount,
    total,
    pages,
    page,
    loading,
    error,
    fetchRecommendations,
    fetchUnreadCount,
    send,
    accept,
    dismiss,
  }
}
