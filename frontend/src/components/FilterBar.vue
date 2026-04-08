<template>
  <form
    class="filter-bar"
    role="search"
    aria-label="Filter catalog"
    @submit.prevent
  >
    <div class="filter-field filter-field--wide">
      <label
        for="filter-search"
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
          id="filter-search"
          v-model="search"
          type="text"
          placeholder="Search titles…"
          @input="emitFilters"
        >
        <button
          v-if="search"
          type="button"
          class="field-clear"
          aria-label="Clear search"
          @click="search = ''; emitFilters()"
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

    <div class="filter-field">
      <label
        for="filter-type"
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
          id="filter-type"
          v-model="mediaType"
          @change="emitFilters"
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

    <div class="filter-field">
      <label
        for="filter-status"
        class="visually-hidden"
      >Filter by status</label>
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
        ><circle
          cx="12"
          cy="12"
          r="10"
        /><path d="m9 12 2 2 4-4" /></svg>
        <select
          id="filter-status"
          v-model="status"
          @change="emitFilters"
        >
          <option value="">
            All Statuses
          </option>
          <option value="pending">
            Pending
          </option>
          <option value="in_progress">
            In Progress
          </option>
          <option value="completed">
            Completed
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

    <div class="filter-field">
      <label
        for="filter-tag"
        class="visually-hidden"
      >Filter by tag</label>
      <div class="field-inner">
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
        ><path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z" /><path d="M7 7h.01" /></svg>
        <input
          id="filter-tag"
          v-model="tag"
          type="text"
          placeholder="Filter by tag…"
          @input="emitFilters"
        >
        <button
          v-if="tag"
          type="button"
          class="field-clear"
          aria-label="Clear tag filter"
          @click="tag = ''; emitFilters()"
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
  </form>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['update:filters'])

const search = ref('')
const mediaType = ref('')
const status = ref('')
const tag = ref('')

function emitFilters() {
  emit('update:filters', {
    search: search.value || null,
    media_type: mediaType.value || null,
    status: status.value || null,
    tag: tag.value || null,
  })
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.75rem;
}

.filter-field {
  flex: 1 1 160px;
}

.filter-field--wide {
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

/* Select chevron */
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

/* Clear button */
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
</style>
