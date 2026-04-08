<template>
  <form
    class="filter-bar"
    role="search"
    aria-label="Filter catalog"
  >
    <div class="filter-group">
      <label
        for="filter-search"
        class="visually-hidden"
      >Search by title</label>
      <input
        id="filter-search"
        v-model="search"
        type="text"
        placeholder="Search by title…"
        aria-label="Search by title"
        @input="emitFilters"
      >
    </div>

    <div class="filter-group">
      <label
        for="filter-type"
        class="visually-hidden"
      >Filter by type</label>
      <select
        id="filter-type"
        v-model="mediaType"
        aria-label="Filter by media type"
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
    </div>

    <div class="filter-group">
      <label
        for="filter-status"
        class="visually-hidden"
      >Filter by status</label>
      <select
        id="filter-status"
        v-model="status"
        aria-label="Filter by status"
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
    </div>

    <div class="filter-group">
      <label
        for="filter-tag"
        class="visually-hidden"
      >Filter by tag</label>
      <input
        id="filter-tag"
        v-model="tag"
        type="text"
        placeholder="Filter by tag…"
        aria-label="Filter by tag"
        @input="emitFilters"
      >
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
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  flex: 1 1 180px;
}

.filter-group input,
.filter-group select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
}

.filter-group input:focus,
.filter-group select:focus {
  outline: 2px solid #4a90d9;
  outline-offset: 1px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
