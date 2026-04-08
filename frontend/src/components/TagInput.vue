<template>
  <div class="tag-input">
    <label
      class="tag-label"
      for="tag-field"
    >Tags</label>
    <div
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
          class="tag-remove"
          :aria-label="`Remove tag: ${tag}`"
          @click="removeTag(tag)"
        >
          ×
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
        class="btn-add-tag"
        :disabled="!newTag"
        @click="addTag"
      >
        Add
      </button>
    </div>
    <p
      v-if="atLimit"
      class="tag-limit-msg"
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
  margin-bottom: 1rem;
}

.tag-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: #e8eaf6;
  color: #3949ab;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.85rem;
}

.tag-remove {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  color: #3949ab;
  padding: 0;
  line-height: 1;
}

.tag-add {
  display: flex;
  gap: 0.5rem;
}

.tag-add input {
  flex: 1;
  padding: 0.4rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
}

.btn-add-tag {
  padding: 0.4rem 0.8rem;
  background: #4a90d9;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.btn-add-tag:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tag-limit-msg {
  color: #c62828;
  font-size: 0.85rem;
  margin-top: 0.3rem;
}
</style>
