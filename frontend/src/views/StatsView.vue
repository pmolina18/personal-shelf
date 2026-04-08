<template>
  <section
    class="stats-view"
    aria-label="Catalog statistics"
  >
    <h1 class="page-title">
      Statistics
    </h1>
    <p class="page-subtitle">
      Overview of your collection
    </p>

    <div
      v-if="loading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p>Loading statistics…</p>
    </div>

    <div
      v-else-if="error"
      class="state-box state-box--error"
      role="alert"
    >
      <p>{{ error }}</p>
    </div>

    <template v-else>
      <!-- KPI row -->
      <div class="kpi-row">
        <div class="kpi-card">
          <span class="kpi-number">{{ totalItems }}</span>
          <span class="kpi-label">Total Items</span>
        </div>
        <div
          v-for="(count, type) in stats.by_type"
          :key="'kpi-'+type"
          class="kpi-card"
        >
          <span class="kpi-number">{{ count }}</span>
          <span class="kpi-label">{{ formatLabel(type) }}{{ count !== 1 ? 's' : '' }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <!-- By Status -->
        <div class="stats-card">
          <h2 class="card-title">
            By Status
          </h2>
          <div class="bar-chart">
            <div
              v-for="(count, status) in stats.by_status"
              :key="status"
              class="bar-row"
            >
              <span class="bar-label">{{ formatLabel(status) }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :class="`bar-fill--${status}`"
                  :style="{ width: barPct(count) }"
                />
              </div>
              <span class="bar-value">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- Avg Rating -->
        <div class="stats-card">
          <h2 class="card-title">
            Avg. Rating by Type
          </h2>
          <div class="rating-list">
            <div
              v-for="(avg, type) in stats.avg_rating_by_type"
              :key="type"
              class="rating-row"
            >
              <span class="rating-type">{{ formatLabel(type) }}</span>
              <div
                v-if="avg !== null"
                class="rating-visual"
              >
                <div class="rating-bar-track">
                  <div
                    class="rating-bar-fill"
                    :style="{ width: `${(avg / 10) * 100}%` }"
                  />
                </div>
                <span class="rating-num">{{ avg.toFixed(1) }}</span>
              </div>
              <span
                v-else
                class="no-data"
              >No ratings</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStats } from '../api/media.js'

const stats = ref(null)
const loading = ref(true)
const error = ref(null)

const totalItems = computed(() => {
  if (!stats.value) return 0
  return Object.values(stats.value.by_type).reduce((sum, n) => sum + n, 0)
})

const maxCount = computed(() => {
  if (!stats.value) return 1
  const all = [...Object.values(stats.value.by_type), ...Object.values(stats.value.by_status)]
  return Math.max(...all, 1)
})

function barPct(count) {
  return `${(count / maxCount.value) * 100}%`
}

function formatLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function fetchStats() {
  loading.value = true
  error.value = null
  try { stats.value = await getStats() }
  catch (err) { error.value = err.message || 'Failed to load statistics' }
  finally { loading.value = false }
}

onMounted(() => fetchStats())
</script>

<style scoped>
.stats-view {
  max-width: 860px;
  margin: 0 auto;
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
  margin-bottom: 1.75rem;
}

/* KPI */
.kpi-row {
  display: flex;
  gap: 0.85rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.kpi-card {
  flex: 1 1 120px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 1.15rem 1rem;
  text-align: center;
}

.kpi-number {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
  margin-bottom: 0.25rem;
}

.kpi-label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1rem;
}

.stats-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
}

.card-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 1rem;
}

/* Bar chart */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.bar-label {
  width: 85px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.bar-track {
  flex: 1;
  height: 8px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--color-primary);
}

.bar-fill--pending { background: var(--color-status-pending-text); }
.bar-fill--in_progress { background: var(--color-status-in-progress-text); }
.bar-fill--completed { background: var(--color-status-completed-text); }

.bar-value {
  width: 2rem;
  text-align: right;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text);
}

/* Rating list */
.rating-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.rating-type {
  width: 65px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.rating-visual {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rating-bar-track {
  flex: 1;
  height: 8px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.rating-bar-fill {
  height: 100%;
  background: var(--color-rating);
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.rating-num {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-rating);
  min-width: 1.8rem;
  text-align: right;
}

.no-data {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-style: italic;
}

/* State */
.state-box {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  color: var(--color-text-muted);
}

.state-box--error {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.loader {
  width: 2rem;
  height: 2rem;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 500px) {
  .stats-grid { grid-template-columns: 1fr; }
  .kpi-row { gap: 0.5rem; }
  .kpi-card { padding: 0.85rem 0.65rem; }
  .kpi-number { font-size: 1.4rem; }
}
</style>
