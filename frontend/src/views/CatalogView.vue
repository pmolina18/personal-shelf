<template>
  <section
    class="catalog-view"
    aria-label="Media catalog"
  >
    <h1>My Catalog</h1>

    <FilterBar @update:filters="onFiltersChange" />

    <div
      v-if="loading"
      class="catalog-loading"
      role="status"
    >
      Loading…
    </div>

    <div
      v-else-if="error"
      class="catalog-error"
      role="alert"
    >
      {{ error }}
    </div>

    <div
      v-else-if="items.length === 0 && !hasActiveFilters"
      class="catalog-empty"
    >
      <p>No items in your catalog yet</p>
      <router-link
        to="/media/new"
        class="btn-add"
        aria-label="Add your first media item"
      >
        Add your first item
      </router-link>
    </div>

    <div
      v-else-if="items.length === 0 && hasActiveFilters"
      class="catalog-empty"
    >
      <p>No items match your filters.</p>
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

function onFiltersChange(newFilters) {
  setFilters(newFilters)
}

function onPageChange(newPage) {
  setPage(newPage)
}

onMounted(() => {
  fetchMedia()
})
</script>

<style scoped>
.catalog-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.catalog-view h1 {
  margin-bottom: 1rem;
}

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.catalog-loading {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
}

.catalog-error {
  text-align: center;
  padding: 2rem 1rem;
  color: #c62828;
  background: #ffebee;
  border-radius: 8px;
}

.catalog-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
}

.btn-add {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.6rem 1.2rem;
  background: #4a90d9;
  color: #fff;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 600;
}

.btn-add:hover {
  background: #3a7bc8;
}

.btn-add:focus-visible {
  outline: 2px solid #4a90d9;
  outline-offset: 2px;
}
</style>
