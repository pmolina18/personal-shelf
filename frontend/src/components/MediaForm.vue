<template>
  <form
    class="media-form"
    @submit.prevent="onSubmit"
  >
    <div class="form-group">
      <label for="mf-title">Title <span class="required">*</span></label>
      <input
        id="mf-title"
        v-model="form.title"
        type="text"
        maxlength="255"
        required
        aria-required="true"
        aria-label="Title"
      >
      <p
        v-if="errors.title"
        class="field-error"
        role="alert"
      >
        {{ errors.title }}
      </p>
    </div>

    <div class="form-group">
      <label for="mf-type">Type <span class="required">*</span></label>
      <select
        id="mf-type"
        v-model="form.media_type"
        required
        aria-required="true"
        aria-label="Media type"
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
    </div>

    <div class="form-group">
      <label for="mf-year">Year</label>
      <input
        id="mf-year"
        v-model.number="form.year"
        type="number"
        aria-label="Year"
      >
    </div>

    <div class="form-group">
      <label for="mf-creator">Director / Author</label>
      <input
        id="mf-creator"
        v-model="form.creator"
        type="text"
        maxlength="255"
        aria-label="Director or Author"
      >
    </div>

    <div class="form-group">
      <label for="mf-notes">Notes</label>
      <textarea
        id="mf-notes"
        v-model="form.notes"
        rows="3"
        aria-label="Notes"
      />
    </div>

    <button
      type="submit"
      class="btn-submit"
    >
      {{ initialData ? 'Save Changes' : 'Create' }}
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.form-group label {
  font-weight: 600;
  font-size: 0.9rem;
}

.required {
  color: #c62828;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.5rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.95rem;
}

.field-error {
  color: #c62828;
  font-size: 0.85rem;
  margin: 0;
}

.btn-submit {
  align-self: flex-start;
  padding: 0.6rem 1.4rem;
  background: #4a90d9;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-submit:hover {
  background: #3a7bc8;
}
</style>
