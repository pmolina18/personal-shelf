<template>
  <nav
    v-if="pages > 1"
    class="pagination"
    aria-label="Pagination"
  >
    <span class="pagination-info">{{ total }} item{{ total === 1 ? '' : 's' }} total</span>

    <div class="pagination-controls">
      <button
        :disabled="page <= 1"
        aria-label="Previous page"
        @click="$emit('update:page', page - 1)"
      >
        ← Prev
      </button>

      <button
        v-for="p in visiblePages"
        :key="p"
        :class="{ active: p === page }"
        :aria-label="`Go to page ${p}`"
        :aria-current="p === page ? 'page' : undefined"
        @click="$emit('update:page', p)"
      >
        {{ p }}
      </button>

      <button
        :disabled="page >= pages"
        aria-label="Next page"
        @click="$emit('update:page', page + 1)"
      >
        Next →
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
  margin-top: 1.5rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.pagination-info {
  font-size: 0.85rem;
  color: #666;
}

.pagination-controls {
  display: flex;
  gap: 0.25rem;
}

.pagination-controls button {
  padding: 0.4rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 0.85rem;
}

.pagination-controls button:hover:not(:disabled) {
  background: #f0f0f0;
}

.pagination-controls button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination-controls button.active {
  background: #4a90d9;
  color: #fff;
  border-color: #4a90d9;
}

.pagination-controls button:focus-visible {
  outline: 2px solid #4a90d9;
  outline-offset: 1px;
}
</style>
