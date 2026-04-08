<template>
  <form
    class="media-form"
    @submit.prevent="onSubmit"
  >
    <!-- Title -->
    <div class="field">
      <label
        for="mf-title"
        class="field-label"
      >Title <span class="req">*</span></label>
      <div class="field-input-wrap">
        <svg
          class="field-icon"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><path d="M4 7V4h16v3" /><path d="M9 20h6" /><path d="M12 4v16" /></svg>
        <input
          id="mf-title"
          v-model="form.title"
          type="text"
          maxlength="255"
          required
          aria-required="true"
          placeholder="e.g. The Shawshank Redemption"
        >
      </div>
      <p
        v-if="errors.title"
        class="field-error"
        role="alert"
      >
        {{ errors.title }}
      </p>
    </div>

    <!-- Type + Year row -->
    <div class="field-row">
      <div class="field">
        <label
          for="mf-type"
          class="field-label"
        >Type <span class="req">*</span></label>
        <div class="field-input-wrap field-input-wrap--select">
          <svg
            class="field-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><rect
            x="2"
            y="7"
            width="20"
            height="14"
            rx="2"
          /><path d="M16 7V5a4 4 0 0 0-8 0v2" /></svg>
          <select
            id="mf-type"
            v-model="form.media_type"
            required
            aria-required="true"
          >
            <option
              value=""
              disabled
            >
              Select type
            </option>
            <option value="movie">
              Movie
            </option>
            <option value="book">
              Book
            </option>
            <option value="series">
              Series
            </option>
          </select>
          <svg
            class="field-chevron"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
          ><path d="m6 9 6 6 6-6" /></svg>
        </div>
      </div>
      <div class="field">
        <label
          for="mf-year"
          class="field-label"
        >Year</label>
        <div class="field-input-wrap">
          <svg
            class="field-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><rect
            x="3"
            y="4"
            width="18"
            height="18"
            rx="2"
          /><path d="M16 2v4M8 2v4M3 10h18" /></svg>
          <input
            id="mf-year"
            v-model.number="form.year"
            type="number"
            placeholder="2024"
          >
        </div>
      </div>
    </div>

    <!-- Creator -->
    <div class="field">
      <label
        for="mf-creator"
        class="field-label"
      >Director / Author</label>
      <div class="field-input-wrap">
        <svg
          class="field-icon"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle
          cx="12"
          cy="7"
          r="4"
        /></svg>
        <input
          id="mf-creator"
          v-model="form.creator"
          type="text"
          maxlength="255"
          placeholder="Who made it?"
        >
      </div>
    </div>

    <!-- Notes -->
    <div class="field">
      <label
        for="mf-notes"
        class="field-label"
      >Notes</label>
      <textarea
        id="mf-notes"
        v-model="form.notes"
        rows="3"
        placeholder="Your thoughts, reviews, or notes…"
      />
    </div>

    <button
      type="submit"
      class="btn-submit"
    >
      <svg
        v-if="!initialData"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
      ><path d="M12 5v14M5 12h14" /></svg>
      <svg
        v-else
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      ><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" /><polyline points="17 21 17 13 7 13 7 21" /><polyline points="7 3 7 8 15 8" /></svg>
      {{ initialData ? 'Save Changes' : 'Create Item' }}
    </button>
  </form>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  initialData: { type: Object, default: null },
})

const emit = defineEmits(['submit'])

const form = reactive({
  title: '',
  media_type: '',
  year: null,
  creator: '',
  notes: '',
})

const errors = reactive({ title: '' })

function populate(data) {
  if (!data) return
  form.title = data.title || ''
  form.media_type = data.media_type || ''
  form.year = data.year ?? null
  form.creator = data.creator || ''
  form.notes = data.notes || ''
}

watch(() => props.initialData, (val) => populate(val), { immediate: true })

function onSubmit() {
  errors.title = ''
  if (!form.title.trim()) {
    errors.title = 'Title is required'
    return
  }
  emit('submit', {
    title: form.title.trim(),
    media_type: form.media_type,
    year: form.year || null,
    creator: form.creator.trim() || null,
    notes: form.notes.trim() || null,
  })
}
</script>

<style scoped>
.media-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-row {
  display: flex;
  gap: 0.75rem;
}

.field-row .field {
  flex: 1;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field-label {
  font-weight: 600;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.req { color: var(--color-error); }

/* Input wrapper with icon */
.field-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.field-icon {
  position: absolute;
  left: 0.7rem;
  color: var(--color-text-muted);
  pointer-events: none;
  z-index: 1;
}

.field-input-wrap input,
.field-input-wrap select {
  width: 100%;
  padding: 0.6rem 0.75rem 0.6rem 2.25rem;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.87rem;
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
  appearance: none;
  -webkit-appearance: none;
}

.field-input-wrap input:hover,
.field-input-wrap select:hover {
  border-color: var(--color-text-muted);
  background: var(--color-bg-warm);
}

.field-input-wrap input:focus,
.field-input-wrap select:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
  background: var(--color-surface);
}

.field-input-wrap input::placeholder {
  color: var(--color-text-muted);
}

/* Select chevron */
.field-input-wrap--select { position: relative; }

.field-chevron {
  position: absolute;
  right: 0.65rem;
  color: var(--color-text-muted);
  pointer-events: none;
}

.field-input-wrap--select select {
  padding-right: 2rem;
}

/* Textarea */
.field textarea {
  padding: 0.6rem 0.75rem;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.87rem;
  color: var(--color-text);
  background: var(--color-surface);
  resize: vertical;
  min-height: 5rem;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}

.field textarea:hover {
  border-color: var(--color-text-muted);
  background: var(--color-bg-warm);
}

.field textarea:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
  background: var(--color-surface);
}

.field textarea::placeholder {
  color: var(--color-text-muted);
}

.field-error {
  color: var(--color-error);
  font-size: 0.78rem;
  margin: 0;
  font-weight: 500;
}

/* Submit */
.btn-submit {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1.4rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.87rem;
  cursor: pointer;
  transition: background var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast);
  box-shadow: var(--shadow-xs);
}

.btn-submit:hover {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.btn-submit:active {
  transform: translateY(0);
}

@media (max-width: 500px) {
  .field-row {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
