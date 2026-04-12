<template>
  <section
    class="suggestions-view"
    aria-label="Suggestion box"
  >
    <div class="suggestions-header">
      <h1 class="page-title">
        Suggestions
      </h1>
      <p class="page-subtitle">
        Share ideas for new features or report bugs
      </p>
    </div>

    <!-- Tabs -->
    <nav
      class="suggestions-tabs"
      aria-label="Suggestion tabs"
    >
      <button
        type="button"
        :class="['tab-btn', { 'tab-btn--active': activeTab === 'all' }]"
        :aria-pressed="activeTab === 'all'"
        @click="switchTab('all')"
      >
        All suggestions
      </button>
      <button
        type="button"
        :class="['tab-btn', { 'tab-btn--active': activeTab === 'mine' }]"
        :aria-pressed="activeTab === 'mine'"
        @click="switchTab('mine')"
      >
        My suggestions
      </button>
    </nav>

    <!-- New suggestion toggle -->
    <button
      type="button"
      class="btn-new-suggestion"
      :aria-pressed="showForm"
      @click="showForm = !showForm"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <line
          x1="12"
          y1="5"
          x2="12"
          y2="19"
        />
        <line
          x1="5"
          y1="12"
          x2="19"
          y2="12"
        />
      </svg>
      {{ showForm ? 'Cancel' : 'New suggestion' }}
    </button>

    <!-- Success message -->
    <div
      v-if="successMsg"
      class="alert alert--success"
      role="status"
    >
      {{ successMsg }}
    </div>

    <!-- Error message -->
    <div
      v-if="error && !loading"
      class="alert alert--error"
      role="alert"
    >
      {{ error }}
    </div>

    <!-- Inline form -->
    <form
      v-if="showForm"
      class="suggestion-form"
      @submit.prevent="onSubmit"
    >
      <div class="form-field">
        <label
          for="suggestion-title"
          class="form-label"
        >Title</label>
        <input
          id="suggestion-title"
          v-model="formTitle"
          type="text"
          class="form-input"
          placeholder="Brief summary of your suggestion"
          maxlength="255"
          required
        >
      </div>
      <div class="form-field">
        <label
          for="suggestion-description"
          class="form-label"
        >Description</label>
        <textarea
          id="suggestion-description"
          v-model="formDescription"
          class="form-input form-textarea"
          placeholder="Describe your idea or the bug in detail…"
          maxlength="2000"
          rows="4"
          required
        />
      </div>
      <div class="form-field">
        <label
          for="suggestion-type"
          class="form-label"
        >Type</label>
        <select
          id="suggestion-type"
          v-model="formType"
          class="form-input"
          required
        >
          <option value="feature">
            Feature
          </option>
          <option value="bug">
            Bug
          </option>
        </select>
      </div>
      <button
        type="submit"
        class="btn-submit"
        :disabled="loading"
      >
        {{ loading ? 'Submitting…' : 'Submit suggestion' }}
      </button>
    </form>

    <!-- Loading -->
    <div
      v-if="loading && !showForm"
      class="state-box"
      role="status"
    >
      <div class="loader" />
      <p class="state-text">
        Loading suggestions…
      </p>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="currentList.length === 0 && !error"
      class="state-box"
    >
      <span class="state-emoji">💡</span>
      <p class="state-heading">
        No suggestions yet
      </p>
      <p class="state-text">
        {{ activeTab === 'mine' ? 'You haven\'t submitted any suggestions yet.' : 'Be the first to share an idea!' }}
      </p>
    </div>

    <!-- Suggestion cards -->
    <template v-else-if="!loading">
      <ul class="suggestions-list">
        <li
          v-for="item in currentList"
          :key="item.id"
          class="suggestion-card"
        >
          <article class="suggestion-card__body">
            <div class="suggestion-card__top">
              <span :class="['type-badge', `type-badge--${item.type}`]">
                {{ item.type }}
              </span>
              <span class="suggestion-card__date">{{ formatDate(item.created_at) }}</span>
            </div>
            <h2 class="suggestion-card__title">
              {{ item.title }}
            </h2>
            <p class="suggestion-card__description">
              {{ item.description }}
            </p>
            <div class="suggestion-card__footer">
              <span class="suggestion-card__author">by {{ item.username }}</span>
            </div>
          </article>
        </li>
      </ul>

      <Pagination
        :page="currentPage"
        :pages="currentTotalPages"
        :total="currentTotal"
        @update:page="onPageChange"
      />
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSuggestions } from '../composables/useSuggestions.js'
import Pagination from '../components/Pagination.vue'

const {
  suggestions,
  mySuggestions,
  loading,
  error,
  page,
  totalPages,
  total,
  myPage,
  myTotalPages,
  myTotal,
  successMsg,
  fetchAll,
  fetchMine,
  submit,
} = useSuggestions()

const activeTab = ref('all')
const showForm = ref(false)
const formTitle = ref('')
const formDescription = ref('')
const formType = ref('feature')

const currentList = computed(() =>
  activeTab.value === 'all' ? suggestions.value : mySuggestions.value,
)
const currentPage = computed(() =>
  activeTab.value === 'all' ? page.value : myPage.value,
)
const currentTotalPages = computed(() =>
  activeTab.value === 'all' ? totalPages.value : myTotalPages.value,
)
const currentTotal = computed(() =>
  activeTab.value === 'all' ? total.value : myTotal.value,
)

function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'all') {
    fetchAll(page.value)
  } else {
    fetchMine(myPage.value)
  }
}

function onPageChange(p) {
  if (activeTab.value === 'all') {
    fetchAll(p)
  } else {
    fetchMine(p)
  }
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

async function onSubmit() {
  await submit({
    title: formTitle.value.trim(),
    description: formDescription.value.trim(),
    type: formType.value,
  })
  if (!error.value) {
    formTitle.value = ''
    formDescription.value = ''
    formType.value = 'feature'
    showForm.value = false
  }
}

onMounted(() => fetchAll())
</script>

<style scoped>
.suggestions-view {
  max-width: 800px;
}

.suggestions-header {
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.page-subtitle {
  font-size: 0.87rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
}

/* Tabs */
.suggestions-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 1rem;
}

.tab-btn {
  padding: 0.6rem 1.1rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.87rem;
  font-weight: 600;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text);
}

.tab-btn--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.tab-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

/* New suggestion button */
.btn-new-suggestion {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 1rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-bottom: 1rem;
}

.btn-new-suggestion:hover {
  background: var(--color-primary-hover);
}

.btn-new-suggestion:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Alerts */
.alert {
  padding: 0.65rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.alert--success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.alert--error {
  background: var(--color-error-bg);
  color: var(--color-error);
}

/* Form */
.suggestion-form {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.form-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 0.9rem;
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color var(--transition-fast);
}

.form-input:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
  border-color: var(--color-primary);
}

.form-textarea {
  resize: vertical;
  min-height: 5rem;
  line-height: 1.5;
}

.btn-submit {
  align-self: flex-start;
  padding: 0.5rem 1.25rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-submit:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* States */
.state-box {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}

.state-emoji {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.75rem;
}

.state-heading {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.3rem;
}

.state-text {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.loader {
  width: 2rem;
  height: 2rem;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Suggestion list */
.suggestions-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.suggestion-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  transition: box-shadow var(--transition-fast);
}

.suggestion-card:hover {
  box-shadow: var(--shadow-sm);
}

.suggestion-card__body {
  padding: 1rem 1.15rem;
}

.suggestion-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.type-badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.12rem 0.5rem;
  border-radius: 4px;
}

.type-badge--feature {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.type-badge--bug {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.suggestion-card__date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.suggestion-card__title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.3rem;
  line-height: 1.3;
}

.suggestion-card__description {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.suggestion-card__footer {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.suggestion-card__author {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}


</style>
