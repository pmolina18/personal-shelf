<template>
  <section
    class="recommendations-view"
    aria-label="Recomendaciones recibidas"
  >
    <div class="recommendations-header">
      <h1 class="page-title">
        Recommendations
      </h1>
      <p class="page-subtitle">
        Media recommended by your friends
      </p>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p class="state-text">
        Loading recommendations…
      </p>
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="state-box state-box--error"
      role="alert"
    >
      <p class="state-text">
        {{ error }}
      </p>
    </div>

    <!-- Empty -->
    <div
      v-else-if="recommendations.length === 0"
      class="state-box"
    >
      <span class="state-emoji">🎁</span>
      <p class="state-heading">
        Aún no tienes recomendaciones
      </p>
      <p class="state-text">
        ¡Tus amigos pueden recomendarte películas, libros y series!
      </p>
    </div>

    <!-- List -->
    <template v-else>
      <div
        v-if="hasPending"
        class="recommendations-toolbar"
      >
        <button
          type="button"
          class="btn-mark-all"
          aria-label="Filtrar solo recomendaciones pendientes"
          @click="fetchRecommendations(1, true)"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" /></svg>
          Solo pendientes
        </button>
      </div>

      <ul class="recommendations-list">
        <li
          v-for="rec in recommendations"
          :key="rec.id"
          :class="['recommendation-item', { 'recommendation-item--unread': rec.status === 'pending' }]"
        >
          <router-link
            :to="`/media/${rec.media_item.id}`"
            class="recommendation-item__image-link"
            :aria-label="`Ver ${rec.media_item.title}`"
          >
            <img
              :src="resolveImageUrl(rec.media_item.image_url) || placeholderFor(rec.media_item.media_type)"
              :alt="`Portada de ${rec.media_item.title}`"
              class="recommendation-item__image"
            >
          </router-link>
          <div class="recommendation-item__body">
            <div class="recommendation-item__top">
              <router-link
                :to="`/media/${rec.media_item.id}`"
                class="recommendation-item__title"
              >
                {{ rec.media_item.title }}
              </router-link>
              <span class="recommendation-item__type">{{ typeLabel(rec.media_item.media_type) }}</span>
            </div>
            <p class="recommendation-item__sender">
              Recomendado por <span class="recommendation-item__username">{{ rec.sender.username }}</span>
            </p>
            <p
              v-if="rec.message"
              class="recommendation-item__message"
            >
              "{{ rec.message }}"
            </p>
            <div class="recommendation-item__footer">
              <span class="recommendation-item__date">{{ formatDate(rec.created_at) }}</span>
              <button
                v-if="rec.status === 'pending'"
                type="button"
                class="btn-accept"
                :aria-label="`Aceptar recomendación de ${rec.sender.username}`"
                @click="onAccept(rec.id)"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                ><polyline points="20 6 9 17 4 12" /></svg>
                Añadir a mi catálogo
              </button>
              <button
                v-if="rec.status === 'pending'"
                type="button"
                class="btn-dismiss"
                :aria-label="`Descartar recomendación de ${rec.sender.username}`"
                @click="onDismiss(rec.id)"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                ><line
                  x1="18"
                  y1="6"
                  x2="6"
                  y2="18"
                /><line
                  x1="6"
                  y1="6"
                  x2="18"
                  y2="18"
                /></svg>
                Descartar
              </button>
              <span
                v-else-if="rec.status === 'accepted'"
                class="recommendation-item__status-badge recommendation-item__status-badge--accepted"
              >✓ Añadida</span>
              <span
                v-else-if="rec.status === 'dismissed'"
                class="recommendation-item__status-badge recommendation-item__status-badge--dismissed"
              >Descartada</span>
            </div>
          </div>
        </li>
      </ul>

      <!-- Pagination -->
      <nav
        v-if="pages > 1"
        class="recommendations-pagination"
        aria-label="Paginación de recomendaciones"
      >
        <button
          class="pg-btn"
          :disabled="page <= 1"
          aria-label="Página anterior"
          @click="goToPage(page - 1)"
        >
          ← Anterior
        </button>
        <span class="pg-info">Página {{ page }} de {{ pages }}</span>
        <button
          class="pg-btn"
          :disabled="page >= pages"
          aria-label="Página siguiente"
          @click="goToPage(page + 1)"
        >
          Siguiente →
        </button>
      </nav>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRecommendations } from '../composables/useRecommendations.js'
import { resolveImageUrl } from '../api/media.js'

const {
  recommendations,
  pages,
  page,
  loading,
  error,
  fetchRecommendations,
  accept,
  dismiss,
} = useRecommendations()

const hasPending = computed(() => recommendations.value.some(r => r.status === 'pending'))

const typeLabels = { movie: 'Movie', book: 'Book', series: 'Series' }
function typeLabel(t) { return typeLabels[t] || t }

const placeholders = {
  movie: 'https://placehold.co/300x450/1a2e22/4ead6b?text=🎬&font=raleway',
  book: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📖&font=raleway',
  series: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📺&font=raleway',
}
function placeholderFor(type) { return placeholders[type] || placeholders.movie }

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function onAccept(id) { accept(id) }
function onDismiss(id) { dismiss(id) }

function goToPage(p) {
  fetchRecommendations(p)
}

onMounted(() => fetchRecommendations())
</script>

<style scoped>
.recommendations-view {
  max-width: 700px;
}

.recommendations-header {
  margin-bottom: 1.75rem;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.page-subtitle {
  font-size: 0.87rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
}

.recommendations-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.75rem;
}

.btn-mark-all {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  border: 1px solid var(--color-primary-light);
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-mark-all:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn-mark-all:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.recommendations-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.recommendation-item {
  display: flex;
  gap: 0.85rem;
  padding: 0.85rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  transition: box-shadow var(--transition-fast);
}

.recommendation-item:hover {
  box-shadow: var(--shadow-sm);
}

.recommendation-item--unread {
  border-left: 3px solid var(--color-primary);
  background: var(--color-primary-subtle);
}

.recommendation-item__image-link {
  flex-shrink: 0;
}

.recommendation-item__image {
  width: 3.5rem;
  height: 5.25rem;
  object-fit: cover;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.recommendation-item__body {
  flex: 1;
  min-width: 0;
}

.recommendation-item__top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.15rem;
}

.recommendation-item__title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--color-text);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color var(--transition-fast);
}

.recommendation-item__title:hover {
  color: var(--color-primary);
}

.recommendation-item__type {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.08rem 0.35rem;
  border-radius: var(--radius-full);
  background: var(--color-type-bg);
  color: var(--color-type-text);
  white-space: nowrap;
  flex-shrink: 0;
}

.recommendation-item__sender {
  font-size: 0.82rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.2rem;
}

.recommendation-item__username {
  font-weight: 600;
  color: var(--color-primary);
}

.recommendation-item__message {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-style: italic;
  margin-bottom: 0.3rem;
  line-height: 1.4;
}

.recommendation-item__footer {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.recommendation-item__date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.btn-accept {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
  background: var(--color-primary-subtle);
  border: 1px solid var(--color-primary-light);
  border-radius: var(--radius-sm);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-accept:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-color: var(--color-primary);
}

.btn-accept:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.btn-dismiss {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-dismiss:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
  border-color: var(--color-error);
}

.btn-dismiss:focus-visible {
  outline: 2px solid var(--color-error);
  outline-offset: 1px;
}

.recommendation-item__status-badge {
  font-size: 0.72rem;
  font-weight: 500;
}

.recommendation-item__status-badge--accepted {
  color: var(--color-success);
}

.recommendation-item__status-badge--dismissed {
  color: var(--color-text-muted);
}

/* Pagination */
.recommendations-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
}

.pg-btn {
  padding: 0.45rem 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.pg-btn:hover:not(:disabled) {
  background: var(--color-surface-hover);
  border-color: var(--color-text-muted);
}

.pg-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pg-info {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-weight: 500;
}

/* States */
.state-box {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}

.state-box--error {
  background: var(--color-error-bg);
  border-color: transparent;
}

.state-box--error .state-text {
  color: var(--color-error);
}

.state-emoji {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.75rem;
}

.state-heading {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.3rem;
}

.state-text {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.loader {
  width: 2rem;
  height: 2rem;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
