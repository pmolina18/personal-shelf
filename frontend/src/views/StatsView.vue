<template>
  <section
    class="stats-view"
    aria-label="Catalog statistics"
  >
    <h1>Statistics</h1>

    <div
      v-if="loading"
      class="stats-loading"
      role="status"
    >
      Loading…
    </div>

    <div
      v-else-if="error"
      class="stats-error"
      role="alert"
    >
      {{ error }}
    </div>

    <template v-else>
      <p class="stats-total">
        Total items: <strong>{{ totalItems }}</strong>
      </p>

      <section
        class="stats-section"
        aria-label="Items by type"
      >
        <h2>Items by Type</h2>
        <dl class="stats-list">
          <div
            v-for="(count, type) in stats.by_type"
            :key="type"
            class="stats-row"
          >
            <dt>{{ formatLabel(type) }}</dt>
            <dd>{{ count }}</dd>
          </div>
        </dl>
      </section>

      <section
        class="stats-section"
        aria-label="Items by status"
      >
        <h2>Items by Status</h2>
        <dl class="stats-list">
          <div
            v-for="(count, status) in stats.by_status"
            :key="status"
            class="stats-row"
          >
            <dt>{{ formatLabel(status) }}</dt>
            <dd>{{ count }}</dd>
          </div>
        </dl>
      </section>

      <section
        class="stats-section"
        aria-label="Average rating by type"
      >
        <h2>Average Rating by Type</h2>
        <dl class="stats-list">
          <div
            v-for="(avg, type) in stats.avg_rating_by_type"
            :key="type"
            class="stats-row"
          >
            <dt>{{ formatLabel(type) }}</dt>
            <dd>{{ avg !== null ? avg.toFixed(1) : 'No ratings' }}</dd>
          </div>
        </dl>
      </section>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStats } from '../api/media.js'

const stats = ref(null)
const loading = ref(false)
const error = ref(null)

const totalItems = computed(() => {
  if (!stats.value) return 0
  return Object.values(stats.value.by_type).reduce((sum, n) => sum + n, 0)
})

function formatLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function fetchStats() {
  loading.value = true
  error.value = null
  try {
    stats.value = await getStats()
  } catch (err) {
    error.value = err.message || 'Failed to load statistics'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.stats-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem;
}

.stats-view h1 {
  margin-bottom: 1rem;
}

.stats-total {
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
}

.stats-section {
  margin-bottom: 2rem;
}

.stats-section h2 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.3rem;
}

.stats-list {
  margin: 0;
  padding: 0;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 0;
  border-bottom: 1px solid #eee;
}

.stats-row dt {
  font-weight: 500;
}

.stats-row dd {
  margin: 0;
  color: #555;
}

.stats-loading {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
}

.stats-error {
  text-align: center;
  padding: 2rem 1rem;
  color: #c62828;
  background: #ffebee;
  border-radius: 8px;
}
</style>
