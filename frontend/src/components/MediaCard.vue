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
          loading="lazy"
        >
        <span :class="['status-badge', `status-badge--${item.status}`]">{{ statusLabel }}</span>
      </div>
      <div class="card-body">
        <div class="card-type">
          {{ typeLabel }}
        </div>
        <h3 class="card-title">
          {{ item.title }}
        </h3>
        <div class="card-bottom">
          <span
            v-if="item.rating"
            class="card-rating"
            aria-label="Rating"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="currentColor"
            ><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
            {{ item.rating }}
          </span>
          <span
            v-if="item.year"
            class="card-year"
          >{{ item.year }}</span>
        </div>
        <div
          v-if="item.tags && item.tags.length"
          class="card-tags"
        >
          <span
            v-for="t in item.tags.slice(0, 2)"
            :key="t"
            class="mini-tag"
          >{{ t }}</span>
          <span
            v-if="item.tags.length > 2"
            class="mini-tag mini-tag--more"
          >+{{ item.tags.length - 2 }}</span>
        </div>
      </div>
    </router-link>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { resolveImageUrl } from '../api/media.js'

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
  movie: 'https://placehold.co/300x450/1a2e22/4ead6b?text=🎬&font=raleway',
  book: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📖&font=raleway',
  series: 'https://placehold.co/300x450/1a2e22/4ead6b?text=📺&font=raleway',
}

const imageUrl = computed(() => {
  return resolveImageUrl(props.item.image_url) || placeholders[props.item.media_type] || placeholders.movie
})
</script>

<style scoped>
.media-card {
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border-light);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.media-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
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
  background: var(--color-bg);
  position: relative;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.media-card:hover .card-image img {
  transform: scale(1.06);
}

/* Status badge */
.status-badge {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-full);
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.5;
  white-space: nowrap;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: var(--shadow-sm);
}

.status-badge--pending {
  background: rgba(241, 244, 242, 0.88);
  color: var(--color-status-pending-text);
}

.status-badge--in_progress {
  background: rgba(224, 240, 255, 0.88);
  color: var(--color-status-in-progress-text);
}

.status-badge--completed {
  background: rgba(209, 240, 221, 0.88);
  color: var(--color-status-completed-text);
}

.card-body {
  padding: 0.75rem 0.85rem 0.85rem;
}

.card-type {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin-bottom: 0.2rem;
}

.card-title {
  margin: 0 0 0.45rem;
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text);
}

.card-bottom {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.35rem;
}

.card-rating {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-rating);
}

.card-rating svg {
  flex-shrink: 0;
}

.card-year {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.mini-tag {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-weight: 500;
}

.mini-tag--more {
  background: var(--color-border-light);
  color: var(--color-text-muted);
}
</style>
