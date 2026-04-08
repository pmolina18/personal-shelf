<template>
  <section
    class="media-detail-view"
    aria-label="Media detail"
  >
    <router-link
      to="/"
      class="back-link"
      aria-label="Back to catalog"
    >
      ← Back to catalog
    </router-link>

    <h1>{{ isCreate ? 'Add Media' : 'Media Detail' }}</h1>

    <!-- Loading -->
    <div
      v-if="!isCreate && itemLoading"
      class="detail-loading"
      role="status"
    >
      Loading…
    </div>

    <!-- Error on initial load -->
    <div
      v-else-if="!isCreate && itemError"
      class="detail-error"
      role="alert"
    >
      {{ itemError }}
    </div>

    <!-- Create mode -->
    <template v-else-if="isCreate">
      <MediaForm @submit="onCreate" />
      <p
        v-if="itemError"
        class="op-error"
        role="alert"
      >
        {{ itemError }}
      </p>
    </template>

    <!-- Edit / View mode -->
    <template v-else-if="currentItem">
      <!-- Image -->
      <div
        v-if="currentItem.image_url"
        class="detail-image"
      >
        <img
          :src="currentItem.image_url"
          :alt="`Cover for ${currentItem.title}`"
        >
      </div>

      <!-- Success toast -->
      <p
        v-if="successMsg"
        class="op-success"
        role="status"
      >
        {{ successMsg }}
      </p>
      <p
        v-if="itemError"
        class="op-error"
        role="alert"
      >
        {{ itemError }}
      </p>

      <!-- Form -->
      <MediaForm
        :initial-data="currentItem"
        @submit="onUpdate"
      />

      <!-- Status controls -->
      <fieldset class="status-controls">
        <legend>Status</legend>
        <div
          class="status-buttons"
          role="group"
          aria-label="Change status"
        >
          <button
            v-for="s in statuses"
            :key="s.value"
            type="button"
            class="btn-status"
            :class="{ active: currentItem.status === s.value }"
            :aria-pressed="currentItem.status === s.value"
            @click="onStatusChange(s.value)"
          >
            {{ s.label }}
          </button>
        </div>
      </fieldset>

      <!-- Rating -->
      <RatingInput
        :model-value="currentItem.rating"
        :disabled="currentItem.status === 'pending'"
        @update:model-value="onRatingChange"
      />

      <!-- Tags -->
      <TagInput
        :model-value="currentItem.tags"
        @update:model-value="onTagsChange"
      />

      <!-- Delete -->
      <button
        type="button"
        class="btn-delete"
        @click="showConfirm = true"
      >
        Delete item
      </button>

      <ConfirmDialog
        :open="showConfirm"
        title="Delete Media Item"
        message="Are you sure you want to delete this item? This action cannot be undone."
        @confirm="onDelete"
        @cancel="showConfirm = false"
      />
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMedia } from '../composables/useMedia.js'
import MediaForm from '../components/MediaForm.vue'
import TagInput from '../components/TagInput.vue'
import RatingInput from '../components/RatingInput.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const route = useRoute()
const router = useRouter()

const {
  currentItem,
  itemLoading,
  itemError,
  successMsg,
  fetchItem,
  create,
  update,
  remove,
  changeStatus,
  changeRating,
  changeTags,
} = useMedia()

const isCreate = computed(() => route.name === 'media-create')
const showConfirm = ref(false)

const statuses = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
]

async function onCreate(data) {
  try {
    const created = await create(data)
    router.push(`/media/${created.id}`)
  } catch (err) {
    itemError.value = err.message || 'Failed to create item'
  }
}

async function onUpdate(data) {
  await update(route.params.id, data)
}

async function onStatusChange(status) {
  if (currentItem.value && currentItem.value.status === status) return
  await changeStatus(route.params.id, status)
}

async function onRatingChange(rating) {
  await changeRating(route.params.id, rating)
}

async function onTagsChange(tags) {
  await changeTags(route.params.id, tags)
}

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
  if (!isCreate.value) {
    fetchItem(route.params.id)
  }
})
</script>

<style scoped>
.media-detail-view {
  max-width: 700px;
  margin: 0 auto;
  padding: 1rem;
}

.back-link {
  display: inline-block;
  margin-bottom: 1rem;
  color: #4a90d9;
  text-decoration: none;
  font-weight: 600;
}

.back-link:hover {
  text-decoration: underline;
}

.detail-loading {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
}

.detail-error {
  text-align: center;
  padding: 2rem 1rem;
  color: #c62828;
  background: #ffebee;
  border-radius: 8px;
}

.detail-image {
  margin-bottom: 1rem;
  text-align: center;
}

.detail-image img {
  max-width: 250px;
  border-radius: 8px;
}

.op-success {
  color: #2e7d32;
  background: #e8f5e9;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.75rem;
}

.op-error {
  color: #c62828;
  background: #ffebee;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.75rem;
}

.status-controls {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}

.status-controls legend {
  font-weight: 600;
}

.status-buttons {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-status {
  padding: 0.4rem 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-weight: 600;
}

.btn-status.active {
  background: #4a90d9;
  color: #fff;
  border-color: #4a90d9;
}

.btn-status:hover:not(.active) {
  background: #f5f5f5;
}

.btn-delete {
  margin-top: 1.5rem;
  padding: 0.5rem 1.2rem;
  background: #c62828;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-delete:hover {
  background: #b71c1c;
}
</style>
