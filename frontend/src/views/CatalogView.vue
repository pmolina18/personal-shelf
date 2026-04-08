<template>
  <section
    class="catalog-view"
    aria-label="Media catalog"
  >
    <div class="catalog-header">
      <div>
        <h1 class="page-title">
          My Catalog
        </h1>
        <p class="page-subtitle">
          Your personal media collection
        </p>
      </div>
      <router-link
        to="/media/new"
        class="btn-add"
        aria-label="Add new media item"
        title="Add media"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
        ><path d="M12 5v14M5 12h14" /></svg>
      </router-link>
    </div>

    <FilterBar @update:filters="onFiltersChange" />

    <div
      v-if="loading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p class="state-text">
        Loading your shelf…
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
        Your shelf is empty
      </p>
      <p class="state-text">
        Start building your collection by adding your first item.
      </p>
      <router-link
        to="/media/new"
        class="btn-primary"
      >
        Get started
      </router-link>
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
      <div class="catalog-grid">
        <MediaCard
          v-for="item in items"
          :key="item.id"
          :item="item"
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
import { onMounted } from 'vue'
import { useMedia } from '../composables/useMedia.js'
import FilterBar from '../components/FilterBar.vue'
import MediaCard from '../components/MediaCard.vue'
import Pagination from '../components/Pagination.vue'

const { items, total, page, pages, loading, error, hasActiveFilters, fetchMedia, setFilters, setPage } = useMedia()

function onFiltersChange(newFilters) { setFilters(newFilters) }
function onPageChange(newPage) { setPage(newPage) }
onMounted(() => fetchMedia())
</script>

<style scoped>
.catalog-header {
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

.btn-add {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast);
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

.btn-add:hover {
  background: var(--color-primary-hover);
  color: var(--color-text-inverse);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-add:active {
  transform: translateY(0);
}

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.25rem;
}

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

@media (max-width: 500px) {
  .catalog-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.75rem;
  }
}
</style>
