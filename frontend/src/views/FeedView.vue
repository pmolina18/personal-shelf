<template>
  <section
    class="feed-view"
    aria-label="Social feed"
  >
    <div class="feed-header">
      <h1 class="page-title">
        Feed
      </h1>
      <p class="page-subtitle">
        Recent activity from your friends
      </p>
    </div>

    <div
      v-if="loading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p class="state-text">
        Loading feed…
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
      v-else-if="items.length === 0"
      class="state-box"
    >
      <span class="state-emoji">📡</span>
      <p class="state-heading">
        Your feed is empty
      </p>
      <p class="state-text">
        Add some friends to see what they're watching, reading, and completing.
      </p>
      <router-link
        to="/friends"
        class="btn-primary"
      >
        Find friends
      </router-link>
    </div>

    <template v-else>
      <ul class="feed-list">
        <li
          v-for="(entry, idx) in items"
          :key="idx"
          class="feed-entry"
        >
          <div class="entry-icon">
            {{ actionIcon(entry.action) }}
          </div>
          <div class="entry-body">
            <p class="entry-text">
              <span class="entry-user">{{ entry.username }}</span>
              {{ actionLabel(entry.action) }}
              <span class="entry-title">{{ entry.title }}</span>
            </p>
            <div class="entry-meta">
              <span :class="['entry-type', `entry-type--${entry.media_type}`]">{{ typeLabel(entry.media_type) }}</span>
              <span class="entry-date">{{ formatDate(entry.date) }}</span>
            </div>
          </div>
        </li>
      </ul>

      <nav
        v-if="pages > 1"
        class="feed-pagination"
        aria-label="Feed pagination"
      >
        <button
          class="pg-btn"
          :disabled="page <= 1"
          aria-label="Previous page"
          @click="goToPage(page - 1)"
        >
          ← Previous
        </button>
        <span class="pg-info">Page {{ page }} of {{ pages }}</span>
        <button
          class="pg-btn"
          :disabled="page >= pages"
          aria-label="Next page"
          @click="goToPage(page + 1)"
        >
          Next →
        </button>
      </nav>
    </template>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFeed } from '../api/social.js'

const items = ref([])
const page = ref(1)
const pages = ref(1)
const loading = ref(false)
const error = ref('')

const typeLabels = { movie: 'Movie', book: 'Book', series: 'Series' }
function typeLabel(t) { return typeLabels[t] || t }

function actionIcon(action) {
  const icons = { added: '➕', completed: '✅', rated: '⭐' }
  return icons[action] || '📌'
}

function actionLabel(action) {
  const labels = { added: 'added', completed: 'completed', rated: 'rated' }
  return labels[action] || action
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

async function fetchFeed() {
  loading.value = true
  error.value = ''
  try {
    const data = await getFeed(page.value)
    items.value = data.items
    pages.value = data.pages
  } catch (err) {
    error.value = err.message || 'Failed to load feed'
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  page.value = p
  fetchFeed()
}

onMounted(() => fetchFeed())
</script>

<style scoped>
.feed-view {
  max-width: 700px;
}

.feed-header {
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

.feed-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.feed-entry {
  display: flex;
  gap: 0.85rem;
  padding: 0.85rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  transition: box-shadow var(--transition-fast);
}

.feed-entry:hover {
  box-shadow: var(--shadow-sm);
}

.entry-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.entry-body {
  flex: 1;
  min-width: 0;
}

.entry-text {
  font-size: 0.9rem;
  color: var(--color-text);
  line-height: 1.4;
}

.entry-user {
  font-weight: 600;
  color: var(--color-primary);
}

.entry-title {
  font-weight: 600;
}

.entry-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.3rem;
}

.entry-type {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.1rem 0.4rem;
  border-radius: var(--radius-full);
}

.entry-type--movie,
.entry-type--book,
.entry-type--series {
  background: var(--color-type-bg);
  color: var(--color-type-text);
}

.entry-date {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

/* Pagination */
.feed-pagination {
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

.btn-primary {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.55rem 1.25rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  text-decoration: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.87rem;
  transition: background var(--transition-fast);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
  color: var(--color-text-inverse);
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
</style>
