<template>
  <article class="media-card">
    <router-link
      :to="`/media/${item.id}`"
      class="card-link"
      :aria-label="`View ${item.title}`"
    >
      <div class="card-image">
        <img
          :src="imageUrl"
          :alt="`Cover for ${item.title}`"
        >
      </div>
      <div class="card-body">
        <h3 class="card-title">
          {{ item.title }}
        </h3>
        <div class="card-meta">
          <span class="badge badge-type">{{ typeLabel }}</span>
          <span :class="['badge', 'badge-status', `badge-status--${item.status}`]">
            {{ statusLabel }}
          </span>
        </div>
        <div
          v-if="item.rating"
          class="card-rating"
          aria-label="Rating"
        >
          ★ {{ item.rating }}/10
        </div>
      </div>
    </router-link>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const typeLabels = { movie: 'Movie', book: 'Book', series: 'Series' }
const statusLabels = { pending: 'Pending', in_progress: 'In Progress', completed: 'Completed' }

const typeLabel = computed(() => typeLabels[props.item.media_type] || props.item.media_type)
const statusLabel = computed(() => statusLabels[props.item.status] || props.item.status)

const placeholders = {
  movie: 'https://placehold.co/300x450?text=Movie',
  book: 'https://placehold.co/300x450?text=Book',
  series: 'https://placehold.co/300x450?text=Series',
}

const imageUrl = computed(() => {
  return props.item.image_url || placeholders[props.item.media_type] || placeholders.movie
})
</script>

<style scoped>
.media-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.media-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.card-image {
  width: 100%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: #f5f5f5;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-body {
  padding: 0.75rem;
}

.card-title {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-bottom: 0.4rem;
}

.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-type {
  background: #e8eaf6;
  color: #3949ab;
}

.badge-status--pending {
  background: #eeeeee;
  color: #616161;
}

.badge-status--in_progress {
  background: #e3f2fd;
  color: #1565c0;
}

.badge-status--completed {
  background: #e8f5e9;
  color: #2e7d32;
}

.card-rating {
  font-size: 0.85rem;
  color: #f9a825;
  font-weight: 600;
}
</style>
