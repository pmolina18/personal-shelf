<template>
  <section
    class="admin-view"
    aria-label="Admin dashboard"
  >
    <h1 class="page-title">
      Admin Dashboard
    </h1>
    <p class="page-subtitle">
      Global platform statistics
    </p>

    <!-- Loading -->
    <div
      v-if="loading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p>Loading statistics…</p>
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="state-box state-box--error"
      role="alert"
    >
      <p>{{ error }}</p>
    </div>

    <!-- Data -->
    <template v-else-if="stats">
      <!-- KPI row -->
      <div class="admin-kpi-row">
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.users.total }}</span>
          <span class="admin-kpi__label">Total Users</span>
        </div>
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.users.new_this_week }}</span>
          <span class="admin-kpi__label">New Users This Week</span>
        </div>
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.content.total }}</span>
          <span class="admin-kpi__label">Total Items</span>
        </div>
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.content.new_this_week }}</span>
          <span class="admin-kpi__label">New Items This Week</span>
        </div>
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.users.active_this_week }}</span>
          <span class="admin-kpi__label">Active Users This Week</span>
        </div>
      </div>

      <!-- Content distribution -->
      <div class="admin-grid">
        <div class="admin-card">
          <h2 class="admin-card__title">
            By Type
          </h2>
          <div class="admin-bar-chart">
            <div
              v-for="(count, type) in stats.content.by_type"
              :key="'type-' + type"
              class="admin-bar-row"
            >
              <span class="admin-bar__label">{{ formatLabel(type) }}</span>
              <div class="admin-bar__track">
                <div
                  class="admin-bar__fill admin-bar__fill--type"
                  :style="{ width: barPct(count, contentMax) }"
                />
              </div>
              <span class="admin-bar__value">{{ count }}</span>
            </div>
          </div>
        </div>

        <div class="admin-card">
          <h2 class="admin-card__title">
            By Status
          </h2>
          <div class="admin-bar-chart">
            <div
              v-for="(count, status) in stats.content.by_status"
              :key="'status-' + status"
              class="admin-bar-row"
            >
              <span class="admin-bar__label">{{ formatLabel(status) }}</span>
              <div class="admin-bar__track">
                <div
                  :class="['admin-bar__fill', `admin-bar__fill--${status}`]"
                  :style="{ width: barPct(count, statusMax) }"
                />
              </div>
              <span class="admin-bar__value">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Avg Rating -->
      <div class="admin-card admin-card--rating">
        <h2 class="admin-card__title">
          Global Avg. Rating
        </h2>
        <div
          v-if="stats.content.avg_rating !== null"
          class="admin-rating"
        >
          <div class="admin-rating__bar-track">
            <div
              class="admin-rating__bar-fill"
              :style="{ width: `${(stats.content.avg_rating / 10) * 100}%` }"
            />
          </div>
          <span class="admin-rating__num">{{ stats.content.avg_rating.toFixed(1) }} / 10</span>
        </div>
        <span
          v-else
          class="admin-no-data"
        >No ratings yet</span>
      </div>

      <!-- Social metrics row -->
      <div class="admin-kpi-row admin-kpi-row--social">
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.social.total_friendships }}</span>
          <span class="admin-kpi__label">Total Friendships</span>
        </div>
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.social.pending_requests }}</span>
          <span class="admin-kpi__label">Pending Requests</span>
        </div>
        <div class="admin-kpi-card">
          <span class="admin-kpi__number">{{ stats.social.unique_tags }}</span>
          <span class="admin-kpi__label">Unique Tags</span>
        </div>
      </div>

      <!-- Rankings -->
      <div class="admin-grid">
        <!-- Top 5 Users -->
        <div class="admin-card">
          <h2 class="admin-card__title">
            Top 5 Users
          </h2>
          <table
            v-if="stats.top_users.length"
            class="admin-table"
          >
            <thead>
              <tr>
                <th class="admin-table__th">
                  Username
                </th>
                <th class="admin-table__th admin-table__th--right">
                  Items
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(u, i) in stats.top_users"
                :key="'user-' + i"
                class="admin-table__row"
              >
                <td class="admin-table__td">
                  {{ u.username }}
                </td>
                <td class="admin-table__td admin-table__td--right">
                  {{ u.count }}
                </td>
              </tr>
            </tbody>
          </table>
          <p
            v-else
            class="admin-no-data"
          >
            No user activity yet
          </p>
        </div>

        <!-- Top 5 Tags -->
        <div class="admin-card">
          <h2 class="admin-card__title">
            Top 5 Tags
          </h2>
          <table
            v-if="stats.top_tags.length"
            class="admin-table"
          >
            <thead>
              <tr>
                <th class="admin-table__th">
                  Tag
                </th>
                <th class="admin-table__th admin-table__th--right">
                  Count
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(t, i) in stats.top_tags"
                :key="'tag-' + i"
                class="admin-table__row"
              >
                <td class="admin-table__td">
                  {{ t.name }}
                </td>
                <td class="admin-table__td admin-table__td--right">
                  {{ t.count }}
                </td>
              </tr>
            </tbody>
          </table>
          <p
            v-else
            class="admin-no-data"
          >
            No tags yet
          </p>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="admin-card">
        <h2 class="admin-card__title">
          Recent Activity
        </h2>
        <ul
          v-if="stats.recent_activity.length"
          class="admin-activity"
        >
          <li
            v-for="(item, i) in stats.recent_activity"
            :key="'activity-' + i"
            class="admin-activity__item"
          >
            <span class="admin-activity__title">{{ item.title }}</span>
            <span :class="['admin-badge-type', `admin-badge-type--${item.media_type}`]">{{ formatLabel(item.media_type) }}</span>
            <span class="admin-activity__user">{{ item.username }}</span>
            <time
              class="admin-activity__time"
              :datetime="item.timestamp"
            >{{ relativeTime(item.timestamp) }}</time>
          </li>
        </ul>
        <p
          v-else
          class="admin-no-data"
        >
          No recent activity
        </p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getAdminStats } from '../api/admin.js'

const stats = ref(null)
const loading = ref(true)
const error = ref(null)

const contentMax = computed(() => {
  if (!stats.value) return 1
  const vals = Object.values(stats.value.content.by_type)
  return Math.max(...vals, 1)
})

const statusMax = computed(() => {
  if (!stats.value) return 1
  const vals = Object.values(stats.value.content.by_status)
  return Math.max(...vals, 1)
})

function barPct(count, max) {
  return `${(count / max) * 100}%`
}

function formatLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function relativeTime(timestamp) {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diff = now - then

  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return 'just now'

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`

  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`

  const weeks = Math.floor(days / 7)
  return `${weeks}w ago`
}

async function fetchStats() {
  loading.value = true
  error.value = null
  try {
    stats.value = await getAdminStats()
  } catch (err) {
    error.value = err.message || 'Failed to load admin statistics'
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchStats())
</script>

<style scoped>
.admin-view {
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

/* KPI row */
.admin-kpi-row {
  display: flex;
  gap: 0.85rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.admin-kpi-card {
  flex: 1 1 120px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 1.15rem 1rem;
  text-align: center;
}

.admin-kpi__number {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
  margin-bottom: 0.25rem;
}

.admin-kpi__label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Grid */
.admin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

/* Card */
.admin-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.admin-grid > .admin-card {
  margin-bottom: 0;
}

.admin-card__title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 1rem;
}

.admin-card--rating {
  margin-bottom: 1.5rem;
}

/* Bar chart */
.admin-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.admin-bar-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.admin-bar__label {
  width: 85px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.admin-bar__track {
  flex: 1;
  height: 8px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.admin-bar__fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--color-primary);
}

.admin-bar__fill--type {
  background: var(--color-type-text, #5b3fb5);
}

.admin-bar__fill--pending {
  background: var(--color-status-pending-text);
}

.admin-bar__fill--in_progress {
  background: var(--color-status-in-progress-text);
}

.admin-bar__fill--completed {
  background: var(--color-status-completed-text);
}

.admin-bar__value {
  width: 2rem;
  text-align: right;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text);
}

/* Rating */
.admin-rating {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.admin-rating__bar-track {
  flex: 1;
  height: 8px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.admin-rating__bar-fill {
  height: 100%;
  background: var(--color-rating);
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.admin-rating__num {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-rating);
  white-space: nowrap;
}

.admin-no-data {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-style: italic;
}

/* Table */
.admin-table {
  width: 100%;
  border-collapse: collapse;
}

.admin-table__th {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-align: left;
  padding: 0.5rem 0.65rem;
  border-bottom: 1px solid var(--color-border-light);
}

.admin-table__th--right {
  text-align: right;
}

.admin-table__row:not(:last-child) .admin-table__td {
  border-bottom: 1px solid var(--color-border-light);
}

.admin-table__td {
  font-size: 0.85rem;
  color: var(--color-text);
  padding: 0.55rem 0.65rem;
}

.admin-table__td--right {
  text-align: right;
  font-weight: 600;
  color: var(--color-primary);
}

/* Activity feed */
.admin-activity {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.admin-activity__item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--color-border-light);
  flex-wrap: wrap;
}

.admin-activity__item:last-child {
  border-bottom: none;
}

.admin-activity__title {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.admin-badge-type {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-xs);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  background: var(--color-type-bg, #ede8f5);
  color: var(--color-type-text, #5b3fb5);
}

.admin-badge-type--movie {
  background: var(--color-type-movie-bg, #edf2fb);
  color: var(--color-status-in-progress-text, #1565c0);
}

.admin-badge-type--series {
  background: var(--color-type-series-bg, #edf7f0);
  color: var(--color-status-completed-text, #2e7d32);
}

.admin-badge-type--book {
  background: var(--color-type-book-bg, #faf5eb);
  color: #8d6e2e;
}

.admin-activity__user {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin-left: auto;
}

.admin-activity__time {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* State boxes */
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 500px) {
  .admin-grid { grid-template-columns: 1fr; }
  .admin-kpi-row { gap: 0.5rem; }
  .admin-kpi-card { padding: 0.85rem 0.65rem; }
  .admin-kpi__number { font-size: 1.4rem; }
  .admin-activity__title { max-width: 140px; }
}
</style>
