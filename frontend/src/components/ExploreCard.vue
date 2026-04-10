<template>
  <article :class="['explore-card', `type-${item.media_type}`]">
    <div class="explore-card__image">
      <img
        :src="imageUrl"
        :alt="`Cover for ${item.title}`"
        loading="lazy"
      >
      <button
        type="button"
        :class="['explore-card__add-btn', { 'explore-card__add-btn--added': added }]"
        :aria-label="added ? 'Added to shelf' : 'Add to shelf'"
        :disabled="adding || added"
        @click.stop="onAdd"
      >
        <svg
          v-if="added"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><polyline points="20 6 9 17 4 12" /></svg>
        <svg
          v-else
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><line
          x1="12"
          y1="5"
          x2="12"
          y2="19"
        /><line
          x1="5"
          y1="12"
          x2="19"
          y2="12"
        /></svg>
      </button>
    </div>
    <div class="explore-card__body">
      <div class="explore-card__type">
        {{ typeLabel }}
      </div>
      <h3 class="explore-card__title">
        {{ item.title }}
      </h3>
      <div class="explore-card__meta">
        <span
          v-if="item.year"
          class="explore-card__year"
        >{{ item.year }}</span>
        <span
          v-if="item.creator"
          class="explore-card__creator"
        >{{ item.creator }}</span>
      </div>
      <div
        v-if="item.tags && item.tags.length"
        class="explore-card__tags"
      >
        <span
          v-for="t in item.tags.slice(0, 3)"
          :key="t"
          class="explore-card__tag"
        >{{ t }}</span>
        <span
          v-if="item.tags.length > 3"
          class="explore-card__tag explore-card__tag--more"
        >+{{ item.tags.length - 3 }}</span>
      </div>
      <div
        v-if="item.friends_have > 0 || item.friends_recommended > 0"
        class="explore-card__social"
      >
        <span
          v-if="item.friends_have > 0"
          class="explore-card__signal"
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle
            cx="9"
            cy="7"
            r="4"
          /></svg>
          {{ item.friends_have }} amigos lo tienen
        </span>
        <span
          v-if="item.friends_recommended > 0"
          class="explore-card__signal explore-card__signal--recommended"
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M20 12v10H4V12" /><path d="M2 7h20v5H2z" /><path d="M12 22V7" /><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z" /><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z" /></svg>
          {{ item.friends_recommended }} amigos te lo recomendaron
        </span>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, ref } from 'vue'
import { resolveImageUrl } from '../api/media.js'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['add'])

const adding = ref(false)
const added = ref(false)

async function onAdd() {
  if (adding.value || added.value) return
  adding.value = true
  try {
    emit('add', props.item)
    added.value = true
  } finally {
    adding.value = false
  }
}

const typeLabels = { movie: 'Movie', book: 'Book', series: 'Series' }
const typeLabel = computed(() => typeLabels[props.item.media_type] || props.item.media_type)

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
.explore-card {
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border-light);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.explore-card.type-movie { border-color: var(--color-type-movie-border); }
.explore-card.type-series { border-color: var(--color-type-series-border); }
.explore-card.type-book { border-color: var(--color-type-book-border); }

.explore-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
}

.explore-card__image {
  position: relative;
  width: 100%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--color-bg);
}

.explore-card__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.explore-card:hover .explore-card__image img {
  transform: scale(1.06);
}

.explore-card__body {
  padding: 0.75rem 0.85rem 0.85rem;
}

.type-movie .explore-card__body { background: var(--color-type-movie-bg); }
.type-series .explore-card__body { background: var(--color-type-series-bg); }
.type-book .explore-card__body { background: var(--color-type-book-bg); }

.explore-card__type {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin-bottom: 0.2rem;
}

.explore-card__title {
  margin: 0 0 0.35rem;
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text);
}

.explore-card__meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
}

.explore-card__year {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.explore-card__creator {
  font-size: 0.78rem;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.explore-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.35rem;
}

.explore-card__tag {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-weight: 500;
}

.explore-card__tag--more {
  background: var(--color-border-light);
  color: var(--color-text-muted);
}

.explore-card__social {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-top: 0.35rem;
  padding-top: 0.4rem;
  border-top: 1px solid var(--color-border-light);
}

.explore-card__signal {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--color-primary);
}

.explore-card__signal svg {
  flex-shrink: 0;
}

.explore-card__signal--recommended {
  color: var(--color-rating);
}

.explore-card__add-btn {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border: none;
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--transition-fast), background var(--transition-fast), color var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.explore-card:hover .explore-card__add-btn {
  opacity: 1;
}

.explore-card__add-btn:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.explore-card__add-btn--added {
  background: var(--color-success);
  color: var(--color-text-inverse);
  opacity: 1;
  cursor: default;
}

.explore-card__add-btn:disabled {
  cursor: not-allowed;
}

.explore-card__add-btn:focus-visible {
  opacity: 1;
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}
</style>
