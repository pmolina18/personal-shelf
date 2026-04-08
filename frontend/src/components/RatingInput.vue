<template>
  <div class="rating-input">
    <span class="section-label">Rating</span>
    <div
      v-if="disabled"
      class="rating-disabled"
    >
      Complete or start this item to rate it
    </div>
    <div
      v-else
      class="rating-row"
    >
      <div
        class="rating-stars"
        role="group"
        aria-label="Rating selection"
      >
        <button
          v-for="n in 10"
          :key="n"
          type="button"
          class="star-btn"
          :class="{ active: modelValue !== null && n <= modelValue, hovered: n <= hoverVal }"
          :aria-label="`Rate ${n} out of 10`"
          @click="emit('update:modelValue', n)"
          @mouseenter="hoverVal = n"
          @mouseleave="hoverVal = 0"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="currentColor"
          ><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
        </button>
      </div>
      <span
        v-if="modelValue"
        class="rating-badge"
      >{{ modelValue }}/10</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: [Number, null], default: null },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const hoverVal = ref(0)
</script>

<style scoped>
.rating-input {
  padding: 1rem 1.15rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  margin-bottom: 0.75rem;
}

.section-label {
  display: block;
  font-weight: 600;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.rating-disabled {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  font-style: italic;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.rating-stars {
  display: flex;
  gap: 0.1rem;
}

.star-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-border);
  padding: 0.1rem;
  transition: color var(--transition-fast), transform var(--transition-fast);
  line-height: 0;
}

.star-btn.active {
  color: var(--color-rating);
}

.star-btn.hovered {
  color: var(--color-rating);
  transform: scale(1.15);
}

.rating-badge {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-bg);
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-full);
}
</style>
