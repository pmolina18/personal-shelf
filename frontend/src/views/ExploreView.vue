<template>
  <section
    class="explore-view"
    aria-label="Explore catalog"
  >
    <div class="explore-header">
      <div>
        <h1 class="page-title">
          Explore
        </h1>
        <p class="page-subtitle">
          Discover what others are watching and reading
        </p>
      </div>
    </div>

    <form
      class="explore-controls"
      role="search"
      aria-label="Explore filters"
      @submit.prevent
    >
      <div class="control-field control-field--wide">
        <label
          for="explore-search"
          class="visually-hidden"
        >Search by title</label>
        <div class="field-inner">
          <svg
            class="field-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><circle
            cx="11"
            cy="11"
            r="8"
          /><path d="m21 21-4.3-4.3" /></svg>
          <input
            id="explore-search"
            v-model="searchInput"
            type="text"
            placeholder="Search titles…"
            @input="onSearchInput"
          >
          <button
            v-if="searchInput"
            type="button"
            class="field-clear"
            aria-label="Clear search"
            @click="clearSearch"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
            ><path d="M18 6 6 18M6 6l12 12" /></svg>
          </button>
        </div>
      </div>

      <div class="control-field">
        <label
          for="explore-type"
          class="visually-hidden"
        >Filter by type</label>
        <div class="field-inner field-inner--select">
          <svg
            class="field-icon"
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><rect
            x="2"
            y="7"
            width="20"
            height="14"
            rx="2"
          /><path d="M16 7V5a4 4 0 0 0-8 0v2" /></svg>
          <select
            id="explore-type"
            v-model="typeInput"
            @change="onTypeChange"
          >
            <option value="">
              All Types
            </option>
            <option value="movie">
              Movie
            </option>
            <option value="book">
              Book
            </option>
            <option value="series">
              Series
            </option>
          </select>
          <svg
            class="field-chevron"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="m6 9 6 6 6-6" /></svg>
        </div>
      </div>

      <div class="control-field">
        <label
          for="explore-sort"
          class="visually-hidden"
        >Sort order</label>
        <div class="field-inner field-inner--select">
          <svg
            class="field-icon"
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="m3 16 4 4 4-4" /><path d="M7 20V4" /><path d="m21 8-4-4-4 4" /><path d="M17 4v16" /></svg>
          <select
            id="explore-sort"
            v-model="sortInput"
            @change="onSortChange"
          >
            <option value="title_asc">
              A → Z
            </option>
            <option value="title_desc">
              Z → A
            </option>
            <option value="friends">
              By Friends
            </option>
          </select>
          <svg
            class="field-chevron"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="m6 9 6 6 6-6" /></svg>
        </div>
      </div>
    </form>

    <div
      v-if="loading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p class="state-text">
        Loading explore catalog…
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
      <span class="state-emoji">🔍</span>
      <p class="state-heading">
        No results
      </p>
      <p class="state-text">
        Try adjusting your filters or search terms.
      </p>
    </div>

    <template v-else>
      <div class="explore-grid">
        <ExploreCard
          v-for="(item, index) in items"
          :key="`${item.title}-${item.media_type}-${index}`"
          :item="item"
          @add="onAdd"
        />
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
import { ref, onMounted } from 'vue'
import { useExplore } from '../composables/useExplore.js'
import ExploreCard from '../components/ExploreCard.vue'
import Pagination from '../components/Pagination.vue'

const {
  items, total, page, pages, loading, error,
  fetchExplore, setFilters, setPage, setSort, addItem,
} = useExplore()

const searchInput = ref('')
const typeInput = ref('')
const sortInput = ref('title_asc')

function onSearchInput() {
  setFilters({ search: searchInput.value || null, media_type: typeInput.value || null })
}

function clearSearch() {
  searchInput.value = ''
  setFilters({ search: null, media_type: typeInput.value || null })
}

function onTypeChange() {
  setFilters({ media_type: typeInput.value || null, search: searchInput.value || null })
}

function onSortChange() {
  setSort(sortInput.value)
}

function onPageChange(newPage) {
  setPage(newPage)
}

async function onAdd(item) {
  try {
    await addItem(item)
  } catch (err) {
    console.error('Failed to add item:', err.message)
  }
}

onMounted(() => fetchExplore())
</script>

<style scoped>
.explore-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.75rem;
  gap: 1rem;
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

/* ── Controls bar ──────────────────────────────────────── */
.explore-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.75rem;
}

.control-field {
  flex: 1 1 160px;
}

.control-field--wide {
  flex: 2 1 240px;
}

.field-inner {
  position: relative;
  display: flex;
  align-items: center;
}

.field-icon {
  position: absolute;
  left: 0.7rem;
  color: var(--color-text-muted);
  pointer-events: none;
  z-index: 1;
}

.field-inner input,
.field-inner select {
  width: 100%;
  padding: 0.55rem 0.7rem 0.55rem 2.2rem;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
  appearance: none;
  -webkit-appearance: none;
}

.field-inner input:hover,
.field-inner select:hover {
  border-color: var(--color-text-muted);
  background: var(--color-bg-warm);
}

.field-inner input:focus,
.field-inner select:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
  background: var(--color-surface);
}

.field-inner input::placeholder {
  color: var(--color-text-muted);
}

.field-inner--select {
  position: relative;
}

.field-chevron {
  position: absolute;
  right: 0.65rem;
  color: var(--color-text-muted);
  pointer-events: none;
}

.field-inner--select select {
  padding-right: 2rem;
}

.field-clear {
  position: absolute;
  right: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 0.2rem;
  display: flex;
  align-items: center;
  border-radius: var(--radius-xs);
  transition: color var(--transition-fast), background var(--transition-fast);
}

.field-clear:hover {
  color: var(--color-text);
  background: var(--color-border-light);
}

/* ── Grid ──────────────────────────────────────────────── */
.explore-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.25rem;
}

/* ── State boxes ───────────────────────────────────────── */
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
  .explore-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.75rem;
  }
}
</style>
