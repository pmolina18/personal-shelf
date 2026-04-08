<template>
  <div class="tag-input">
    <span class="section-label">Tags</span>
    <div
      v-if="modelValue.length"
      class="tag-list"
      role="list"
      aria-label="Current tags"
    >
      <span
        v-for="tag in modelValue"
        :key="tag"
        class="tag-chip"
        role="listitem"
      >
        {{ tag }}
        <button
          type="button"
          class="tag-x"
          :aria-label="`Remove tag: ${tag}`"
          @click="removeTag(tag)"
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
          ><path d="M18 6 6 18M6 6l12 12" /></svg>
        </button>
      </span>
    </div>
    <div class="tag-add">
      <input
        id="tag-field"
        v-model.trim="newTag"
        type="text"
        placeholder="Add a tag…"
        aria-label="New tag"
        @keydown.enter.prevent="addTag"
      >
      <button
        type="button"
        class="btn-tag-add"
        :disabled="!newTag"
        @click="addTag"
      >
        Add
      </button>
    </div>
    <p
      v-if="atLimit"
      class="tag-limit"
      role="alert"
    >
      Maximum {{ max }} tags
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  max: { type: Number, default: 10 },
})

const emit = defineEmits(['update:modelValue'])

const newTag = ref('')
const atLimit = computed(() => props.modelValue.length >= props.max)

function addTag() {
  const value = newTag.value.trim()
  if (!value) return
  if (atLimit.value) return
  if (props.modelValue.includes(value)) {
    newTag.value = ''
    return
  }
  emit('update:modelValue', [...props.modelValue, value])
  newTag.value = ''
}

function removeTag(tag) {
  emit('update:modelValue', props.modelValue.filter(t => t !== tag))
}
</script>

<style scoped>
.tag-input {
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

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 0.65rem;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--color-primary-subtle);
  color: var(--color-primary);
  padding: 0.22rem 0.55rem;
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  font-weight: 500;
}

.tag-x {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-primary);
  padding: 0;
  line-height: 0;
  opacity: 0.5;
  transition: opacity var(--transition-fast);
}

.tag-x:hover {
  opacity: 1;
}

.tag-add {
  display: flex;
  gap: 0.4rem;
}

.tag-add input {
  flex: 1;
  padding: 0.45rem 0.65rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  color: var(--color-text);
  background: var(--color-bg-warm);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.tag-add input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
  background: var(--color-surface);
}

.tag-add input::placeholder {
  color: var(--color-text-muted);
}

.btn-tag-add {
  padding: 0.45rem 0.85rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: 600;
  font-size: 0.82rem;
  transition: background var(--transition-fast);
}

.btn-tag-add:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-tag-add:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.tag-limit {
  color: var(--color-error);
  font-size: 0.78rem;
  margin-top: 0.35rem;
  font-weight: 500;
}
</style>
