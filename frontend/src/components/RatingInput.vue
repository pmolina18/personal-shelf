<template>
  <div class="rating-input">
    <label class="rating-label">Rating</label>
    <div
      v-if="disabled"
      class="rating-disabled-msg"
    >
      Start or complete this item to rate it
    </div>
    <div
      v-else
      class="rating-stars"
      role="group"
      aria-label="Rating selection"
    >
      <button
        v-for="n in 10"
        :key="n"
        type="button"
        class="star-btn"
        :class="{ active: modelValue !== null && n <= modelValue }"
        :aria-label="`Rate ${n} out of 10`"
        @click="emit('update:modelValue', n)"
      >
        ★
      </button>
    </div>
    <span
      v-if="!disabled && modelValue"
      class="rating-value"
    >{{ modelValue }}/10</span>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: [Number, null], default: null },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.rating-input {
  margin-bottom: 1rem;
}

.rating-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.rating-disabled-msg {
  color: #888;
  font-size: 0.9rem;
  font-style: italic;
}

.rating-stars {
  display: flex;
  gap: 0.2rem;
}

.star-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #ccc;
  padding: 0.1rem;
  transition: color 0.15s;
}

.star-btn.active {
  color: #f9a825;
}

.star-btn:hover {
  color: #f9a825;
}

.rating-value {
  display: inline-block;
  margin-top: 0.3rem;
  font-size: 0.9rem;
  color: #666;
}
</style>
