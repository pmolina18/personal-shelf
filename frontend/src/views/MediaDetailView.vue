<template>
  <section
    class="detail-view"
    aria-label="Media detail"
  >
    <router-link
      to="/"
      class="back-link"
      aria-label="Back to catalog"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      ><path d="m15 18-6-6 6-6" /></svg>
      Back to catalog
    </router-link>

    <!-- Loading -->
    <div
      v-if="!isCreate && itemLoading"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p>Loading…</p>
    </div>

    <!-- Error -->
    <div
      v-else-if="!isCreate && itemError"
      class="state-box state-box--error"
      role="alert"
    >
      <p>{{ itemError }}</p>
    </div>

    <!-- Create -->
    <template v-else-if="isCreate">
      <h1 class="page-title">
        Add Media
      </h1>
      <div class="card">
        <MediaForm @submit="onCreate" />
      </div>
      <p
        v-if="itemError"
        class="toast toast--error"
        role="alert"
      >
        {{ itemError }}
      </p>
    </template>

    <!-- Detail / Edit -->
    <template v-else-if="currentItem">
      <Transition name="toast">
        <p
          v-if="successMsg"
          class="toast toast--success"
          role="status"
        >
          ✓ {{ successMsg }}
        </p>
      </Transition>
      <p
        v-if="itemError"
        class="toast toast--error"
        role="alert"
      >
        {{ itemError }}
      </p>

      <div class="detail-grid">
        <!-- Sidebar -->
        <aside class="detail-aside">
          <div class="cover-wrapper">
            <img
              :src="resolveImageUrl(currentItem.image_url) || placeholderUrl"
              :alt="`Cover for ${currentItem.title}`"
            >
          </div>
          <div class="aside-info">
            <div class="info-item">
              <span class="info-key">Status</span>
              <span :class="['status-badge', `status-badge--${currentItem.status}`]">{{ statusLabel }}</span>
            </div>
            <div
              v-if="currentItem.rating"
              class="info-item"
            >
              <span class="info-key">Rating</span>
              <span class="info-val info-val--rating">
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                ><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
                {{ currentItem.rating }}/10
              </span>
            </div>
            <div
              v-if="currentItem.creator"
              class="info-item"
            >
              <span class="info-key">Creator</span>
              <span class="info-val">{{ currentItem.creator }}</span>
            </div>
            <div
              v-if="currentItem.year"
              class="info-item"
            >
              <span class="info-key">Year</span>
              <span class="info-val">{{ currentItem.year }}</span>
            </div>
            <div
              v-if="currentItem.tags && currentItem.tags.length"
              class="info-item info-item--col"
            >
              <span class="info-key">Tags</span>
              <div class="info-tags">
                <span
                  v-for="t in currentItem.tags"
                  :key="t"
                  class="tag-pill"
                >{{ t }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- Main -->
        <div class="detail-main">
          <div class="detail-title-row">
            <h1 class="page-title">
              {{ currentItem.title }}
            </h1>
            <button
              type="button"
              class="btn-recommend"
              aria-label="Recomendar este item a un amigo"
              @click="showRecommendModal = true"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              ><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" /><polyline points="16 6 12 2 8 6" /><line
                x1="12"
                y1="2"
                x2="12"
                y2="15"
              /></svg>
              Recomendar
            </button>
          </div>

          <div class="card">
            <MediaForm
              :initial-data="currentItem"
              @submit="onUpdate"
            />
          </div>

          <div class="card">
            <span class="section-label">Status</span>
            <div
              class="status-group"
              role="group"
              aria-label="Change status"
            >
              <button
                v-for="s in statuses"
                :key="s.value"
                type="button"
                class="status-btn"
                :class="{ active: currentItem.status === s.value }"
                :aria-pressed="currentItem.status === s.value"
                @click="onStatusChange(s.value)"
              >
                <span class="status-btn-icon">{{ s.icon }}</span>
                {{ s.label }}
              </button>
            </div>
          </div>

          <!-- Mini-Timeline -->
          <div
            v-if="hasTimeline"
            class="card"
          >
            <span class="section-label">Timeline</span>
            <div
              class="mini-timeline"
              role="list"
              aria-label="Status timeline"
            >
              <div
                class="timeline-step"
                :class="{ 'timeline-step--active': currentItem.pending_at }"
                role="listitem"
                :aria-label="currentItem.pending_at
                  ? `Pending since ${formatDate(currentItem.pending_at)}`
                  : 'Pending — no date'"
              >
                <span class="timeline-dot timeline-dot--pending" />
                <span class="timeline-label">Pending</span>
                <span
                  v-if="currentItem.pending_at"
                  class="timeline-date"
                >
                  {{ formatDate(currentItem.pending_at) }}
                </span>
              </div>

              <span class="timeline-line" />

              <div
                class="timeline-step"
                :class="{ 'timeline-step--active': currentItem.started_at }"
                role="listitem"
                :aria-label="currentItem.started_at
                  ? `In Progress since ${formatDate(currentItem.started_at)}`
                  : 'In Progress — no date'"
              >
                <span class="timeline-dot timeline-dot--in-progress" />
                <span class="timeline-label">In Progress</span>
                <span
                  v-if="currentItem.started_at"
                  class="timeline-date"
                >
                  {{ formatDate(currentItem.started_at) }}
                </span>
              </div>

              <span class="timeline-line" />

              <div
                class="timeline-step"
                :class="{ 'timeline-step--active': currentItem.completed_at }"
                role="listitem"
                :aria-label="currentItem.completed_at
                  ? `Completed since ${formatDate(currentItem.completed_at)}`
                  : 'Completed — no date'"
              >
                <span class="timeline-dot timeline-dot--completed" />
                <span class="timeline-label">Completed</span>
                <span
                  v-if="currentItem.completed_at"
                  class="timeline-date"
                >
                  {{ formatDate(currentItem.completed_at) }}
                </span>
              </div>
            </div>
          </div>

          <RatingInput
            :model-value="currentItem.rating"
            :disabled="currentItem.status === 'pending'"
            @update:model-value="onRatingChange"
          />

          <TagInput
            :model-value="currentItem.tags"
            @update:model-value="onTagsChange"
          />

          <div class="danger-card">
            <span class="section-label section-label--danger">Danger Zone</span>
            <button
              type="button"
              class="btn-delete"
              @click="showConfirm = true"
            >
              Delete this item
            </button>
          </div>

          <ConfirmDialog
            :open="showConfirm"
            title="Delete Media Item"
            message="Are you sure you want to delete this item? This action cannot be undone."
            @confirm="onDelete"
            @cancel="showConfirm = false"
          />

          <RecommendModal
            :media-item-id="currentItem.id"
            :media-title="currentItem.title"
            :show="showRecommendModal"
            @close="showRecommendModal = false"
            @sent="showRecommendModal = false"
          />
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMedia } from '../composables/useMedia.js'
import { resolveImageUrl } from '../api/media.js'
import MediaForm from '../components/MediaForm.vue'
import TagInput from '../components/TagInput.vue'
import RatingInput from '../components/RatingInput.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import RecommendModal from '../components/RecommendModal.vue'

const route = useRoute()
const router = useRouter()

const {
  currentItem, itemLoading, itemError, successMsg,
  fetchItem, create, update, remove, changeStatus, changeRating, changeTags,
} = useMedia()

const isCreate = computed(() => route.name === 'media-create')
const showConfirm = ref(false)
const showRecommendModal = ref(false)

const statusLabels = { pending: 'Pending', in_progress: 'In Progress', completed: 'Completed' }
const statusLabel = computed(() => statusLabels[currentItem.value?.status] || '')

const placeholders = {
  movie: 'https://placehold.co/300x450/1a2e22/4ead6b?text=🎬&font=raleway',
  book: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📖&font=raleway',
  series: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📺&font=raleway',
}

const placeholderUrl = computed(() => placeholders[currentItem.value?.media_type] || placeholders.movie)

const statuses = [
  { value: 'pending', label: 'Pending', icon: '⏳' },
  { value: 'in_progress', label: 'In Progress', icon: '▶️' },
  { value: 'completed', label: 'Completed', icon: '✅' },
]

// Mini-timeline: visible si hay al menos un timestamp de estado
const hasTimeline = computed(() =>
  !!(currentItem.value?.pending_at || currentItem.value?.started_at || currentItem.value?.completed_at)
)

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

async function onCreate(data) {
  try {
    const created = await create(data)
    router.push('/')
  } catch (err) {
    itemError.value = err.message || 'Failed to create item'
  }
}

async function onUpdate(data) { await update(route.params.id, data) }
async function onStatusChange(status) {
  if (currentItem.value?.status === status) return
  await changeStatus(route.params.id, status)
}
async function onRatingChange(rating) { await changeRating(route.params.id, rating) }
async function onTagsChange(tags) { await changeTags(route.params.id, tags) }

async function onDelete() {
  showConfirm.value = false
  try {
    await remove(route.params.id)
    router.push('/')
  } catch (err) {
    itemError.value = err.message || 'Failed to delete item'
  }
}

onMounted(() => {
  if (!isCreate.value) fetchItem(route.params.id)
})
</script>

<style scoped>
.detail-view {
  max-width: 960px;
  margin: 0 auto;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 1.25rem;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  transition: color var(--transition-fast);
}

.back-link:hover {
  color: var(--color-primary);
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 1.25rem;
  line-height: 1.25;
}

.detail-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.detail-title-row .page-title {
  margin-bottom: 0;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-recommend {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.85rem;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  border: 1px solid var(--color-primary-light);
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.82rem;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.btn-recommend:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn-recommend:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Grid */
.detail-grid {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 2rem;
  align-items: start;
}

/* Aside */
.detail-aside {
  position: sticky;
  top: 1.5rem;
}

.cover-wrapper {
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  margin-bottom: 1rem;
}

.cover-wrapper img {
  width: 100%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
}

.aside-info {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.85rem;
  border-bottom: 1px solid var(--color-border-light);
}

.info-item:last-child {
  border-bottom: none;
}

.info-item--col {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
}

.info-key {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.info-val {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text);
}

.info-val--rating {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  color: var(--color-rating);
  font-weight: 600;
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.tag-pill {
  font-size: 0.7rem;
  padding: 0.12rem 0.45rem;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-weight: 500;
}

.status-badge {
  font-size: 0.72rem;
  padding: 0.15rem 0.55rem;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.status-badge--pending {
  background: var(--color-status-pending-bg);
  color: var(--color-status-pending-text);
}

.status-badge--in_progress {
  background: var(--color-status-in-progress-bg);
  color: var(--color-status-in-progress-text);
}

.status-badge--completed {
  background: var(--color-status-completed-bg);
  color: var(--color-status-completed-text);
}

/* Cards */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  margin-bottom: 0.75rem;
}

.section-label {
  display: block;
  font-weight: 600;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.6rem;
}

.section-label--danger {
  color: var(--color-error);
}

/* Status buttons */
.status-group {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.status-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  cursor: pointer;
  font-weight: 500;
  font-size: 0.82rem;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.status-btn:hover:not(.active) {
  background: var(--color-surface-hover);
}

.status-btn.active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-color: var(--color-primary);
}

.status-btn-icon {
  font-size: 0.85rem;
}

/* Danger */
.danger-card {
  background: var(--color-surface);
  border: 1px dashed var(--color-error);
  border-radius: var(--radius-md);
  padding: 1rem 1.15rem;
}

.btn-delete {
  padding: 0.45rem 1rem;
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-delete:hover {
  background: var(--color-error);
  color: var(--color-text-inverse);
}

/* Toasts */
.toast {
  padding: 0.6rem 0.85rem;
  border-radius: var(--radius-sm);
  margin-bottom: 0.75rem;
  font-weight: 500;
  font-size: 0.85rem;
}

.toast--success {
  color: var(--color-success);
  background: var(--color-success-bg);
}

.toast--error {
  color: var(--color-error);
  background: var(--color-error-bg);
}

.toast-enter-active, .toast-leave-active {
  transition: opacity 200ms, transform 200ms;
}
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
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

/* Responsive */
@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-aside {
    position: static;
    display: grid;
    grid-template-columns: 160px 1fr;
    gap: 1rem;
  }

  .cover-wrapper { margin-bottom: 0; }
}

@media (max-width: 500px) {
  .detail-aside {
    grid-template-columns: 1fr;
  }
}

/* ── Mini-Timeline ─────────────────────────────────────── */
.mini-timeline {
  display: flex;
  align-items: flex-start;
  gap: 0;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  flex: 1;
  text-align: center;
  opacity: 0.4;
  transition: opacity var(--transition-fast);
}

.timeline-step--active {
  opacity: 1;
}

.timeline-dot {
  width: 1rem;
  height: 1rem;
  border-radius: var(--radius-full);
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  transition: all var(--transition-fast);
}

.timeline-step--active .timeline-dot--pending {
  background: var(--color-status-pending-bg);
  border-color: var(--color-status-pending-text);
}

.timeline-step--active .timeline-dot--in-progress {
  background: var(--color-status-in-progress-bg);
  border-color: var(--color-status-in-progress-text);
}

.timeline-step--active .timeline-dot--completed {
  background: var(--color-status-completed-bg);
  border-color: var(--color-status-completed-text);
}

.timeline-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
}

.timeline-step--active .timeline-label {
  color: var(--color-text-secondary);
}

.timeline-date {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  font-weight: 500;
}

.timeline-line {
  flex: 0 0 auto;
  width: 2rem;
  height: 2px;
  background: var(--color-border);
  margin-top: 0.45rem;
  align-self: flex-start;
}

/* ── Timeline responsive: vertical en móvil ────────────── */
@media (max-width: 500px) {
  .mini-timeline {
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
  }

  .timeline-step {
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    text-align: left;
  }

  .timeline-line {
    width: 2px;
    height: 1.5rem;
    margin-top: 0;
    margin-left: 0.45rem;
  }
}
</style>
