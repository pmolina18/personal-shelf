<template>
  <nav
    v-if="pages > 1"
    class="pagination"
    aria-label="Pagination"
  >
    <span class="pagination-info">{{ total }} item{{ total === 1 ? '' : 's' }}</span>
    <div class="pagination-controls">
      <button
        class="pg-btn pg-btn--nav"
        :disabled="page <= 1"
        aria-label="Previous page"
        @click="$emit('update:page', page - 1)"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><path d="m15 18-6-6 6-6" /></svg>
      </button>
      <button
        v-for="p in visiblePages"
        :key="p"
        class="pg-btn"
        :class="{ 'pg-btn--active': p === page }"
        :aria-label="`Go to page ${p}`"
        :aria-current="p === page ? 'page' : undefined"
        @click="$emit('update:page', p)"
      >
        {{ p }}
      </button>
      <button
        class="pg-btn pg-btn--nav"
        :disabled="page >= pages"
        aria-label="Next page"
        @click="$emit('update:page', page + 1)"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><path d="m9 18 6-6-6-6" /></svg>
      </button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  pages: { type: Number, required: true },
  total: { type: Number, required: true },
})

defineEmits(['update:page'])

const visiblePages = computed(() => {
  const result = []
  const start = Math.max(1, props.page - 2)
  const end = Math.min(props.pages, props.page + 2)
  for (let i = start; i <= end; i++) {
    result.push(i)
  }
  return result
})
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.pagination-info {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-weight: 500;
}

.pagination-controls {
  display: flex;
  gap: 0.25rem;
}

.pg-btn {
  min-width: 2.1rem;
  height: 2.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.pg-btn:hover:not(:disabled):not(.pg-btn--active) {
  background: var(--color-surface-hover);
  border-color: var(--color-text-muted);
}

.pg-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pg-btn--active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-color: var(--color-primary);
}

.pg-btn--nav {
  color: var(--color-text-muted);
}

.pg-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
</style>
