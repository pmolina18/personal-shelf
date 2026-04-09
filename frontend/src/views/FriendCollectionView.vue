<template>
  <section
    class="friend-collection-view"
    aria-label="Friend's collection"
  >
    <router-link
      to="/friends"
      class="back-link"
      aria-label="Back to friends"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      ><path d="m15 18-6-6 6-6" /></svg>
      Back to friends
    </router-link>

    <div class="collection-header">
      <div>
        <h1 class="page-title">
          {{ friendName ? `${friendName}'s Collection` : 'Friend\'s Collection' }}
        </h1>
        <p class="page-subtitle">
          Browsing in read-only mode
        </p>
      </div>
    </div>

    <FilterBar @update:filters="onFiltersChange" />

    <div
      v-if="loading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p class="state-text">
        Loading collection…
      </p>
    </div>

    <div
      v-else-if="error"
      class="state-box state-box--error"
      role="alert"
    >
      <p class="state-text">
        {{ error }}
      </p>
    </div>

    <div
      v-else-if="items.length === 0 && !hasActiveFilters"
      class="state-box"
    >
      <span class="state-emoji">📚</span>
      <p class="state-heading">
        Empty collection
      </p>
      <p class="state-text">
        This friend hasn't added any items yet.
      </p>
    </div>

    <div
      v-else-if="items.length === 0 && hasActiveFilters"
      class="state-box"
    >
      <span class="state-emoji">🔍</span>
      <p class="state-heading">
        No results
      </p>
      <p class="state-text">
        Try adjusting your filters.
      </p>
    </div>

    <template v-else>
      <div class="collection-grid">
        <article
          v-for="item in items"
          :key="item.id"
          class="media-card"
        >
          <div class="card-image">
            <img
              :src="item.image_url || placeholderUrl(item.media_type)"
              :alt="`Cover for ${item.title}`"
              loading="lazy"
            >
            <span :class="['status-badge', `status-badge--${item.status}`]">{{ statusLabel(item.status) }}</span>
          </div>
          <div class="card-body">
            <div class="card-type">
              {{ typeLabel(item.media_type) }}
            </div>
            <h3 class="card-title">
              {{ item.title }}
            </h3>
            <div class="card-bottom">
              <span
                v-if="item.rating"
                class="card-rating"
              >
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                ><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
                {{ item.rating }}
              </span>
              <span
                v-if="item.year"
                class="card-year"
              >{{ item.year }}</span>
            </div>
          </div>
        </article>
      </div>
      <Pagination
        :page="page"
        :pages="pages"
        :total="total"
        @update:page="onPageChange"
      />
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getFriendCollection } from '../api/social.js'
import FilterBar from '../components/FilterBar.vue'
import Pagination from '../components/Pagination.vue'

const route = useRoute()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const loading = ref(false)
const error = ref('')
const friendName = ref('')

const filters = ref({
  media_type: null,
  status: null,
  search: null,
  tag: null,
})

const hasActiveFilters = computed(() =>
  Object.values(filters.value).some(v => v !== null && v !== ''),
)

const typeLabels = { movie: 'Movie', book: 'Book', series: 'Series' }
const statusLabels = { pending: 'Pending', in_progress: 'In Progress', completed: 'Completed' }
function typeLabel(t) { return typeLabels[t] || t }
function statusLabel(s) { return statusLabels[s] || s }

const placeholders = {
  movie: 'https://placehold.co/300x450/1a2e22/4ead6b?text=🎬&font=raleway',
  book: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📖&font=raleway',
  series: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📺&font=raleway',
}
function placeholderUrl(type) { return placeholders[type] || placeholders.movie }

async function fetchCollection() {
  loading.value = true
  error.value = ''
  try {
    const params = { ...filters.value, page: page.value, size: 20 }
    const data = await getFriendCollection(route.params.id, params)
    items.value = data.items
    total.value = data.total
    pages.value = data.pages
  } catch (err) {
    error.value = err.message || 'Failed to load collection'
  } finally {
    loading.value = false
  }
}

function onFiltersChange(newFilters) {
  filters.value = newFilters
  page.value = 1
  fetchCollection()
}

function onPageChange(newPage) {
  page.value = newPage
  fetchCollection()
}

onMounted(() => {
  friendName.value = route.query.name || ''
  fetchCollection()
})
</script>

<style scoped>
.friend-collection-view {
  max-width: 1200px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 1.25rem;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  transition: color var(--transition-fast);
}

.back-link:hover {
  color: var(--color-primary);
}

.collection-header {
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

.collection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.25rem;
}

/* Inline media card (read-only, no link) */
.media-card {
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border-light);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.media-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.card-image {
  width: 100%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--color-bg);
  position: relative;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-badge {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-full);
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.5;
  backdrop-filter: blur(6px);
  box-shadow: var(--shadow-sm);
}

.status-badge--pending {
  background: rgba(241, 244, 242, 0.88);
  color: var(--color-status-pending-text);
}

.status-badge--in_progress {
  background: rgba(224, 240, 255, 0.88);
  color: var(--color-status-in-progress-text);
}

.status-badge--completed {
  background: rgba(209, 240, 221, 0.88);
  color: var(--color-status-completed-text);
}

.card-body {
  padding: 0.75rem 0.85rem 0.85rem;
}

.card-type {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin-bottom: 0.2rem;
}

.card-title {
  margin: 0 0 0.45rem;
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text);
}

.card-bottom {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.card-rating {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-rating);
}

.card-year {
  font-size: 0.78rem;
  color: var(--color-text-muted);
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

.state-box--error .state-text { color: var(--color-error); }

.state-emoji { font-size: 3rem; display: block; margin-bottom: 0.75rem; }

.state-heading {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.3rem;
}

.state-text {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.loader {
  width: 2rem; height: 2rem;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 500px) {
  .collection-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.75rem;
  }
}
</style>
