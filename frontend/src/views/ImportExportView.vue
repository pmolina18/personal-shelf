<template>
  <section
    class="ie-view"
    aria-label="Import and export catalog"
  >
    <h1 class="page-title">
      Import / Export
    </h1>
    <p class="page-subtitle">
      Backup or restore your collection
    </p>

    <div class="ie-grid">
      <!-- Export -->
      <div class="ie-card">
        <div class="ie-card-header">
          <span class="ie-icon">📤</span>
          <h2 class="ie-card-title">
            Export
          </h2>
        </div>
        <p class="ie-desc">
          Download your entire catalog as a JSON file.
        </p>
        <button
          class="btn-action"
          :disabled="exporting"
          aria-label="Export catalog to JSON file"
          @click="handleExport"
        >
          {{ exporting ? 'Exporting…' : 'Download JSON' }}
        </button>
        <p
          v-if="exportError"
          class="ie-error"
          role="alert"
        >
          {{ exportError }}
        </p>
      </div>

      <!-- Import -->
      <div class="ie-card">
        <div class="ie-card-header">
          <span class="ie-icon">📥</span>
          <h2 class="ie-card-title">
            Import
          </h2>
        </div>
        <p class="ie-desc">
          Upload a JSON file to add items to your catalog.
        </p>

        <div
          class="drop-zone"
          :class="{ 'drop-zone--hover': dragging }"
          @dragover.prevent="dragging = true"
          @dragleave="dragging = false"
          @drop.prevent="onDrop"
          @click="fileInput?.click()"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line
            x1="12"
            y1="3"
            x2="12"
            y2="15"
          /></svg>
          <span class="drop-text">{{ selectedFile ? selectedFile.name : 'Drop file or click to browse' }}</span>
          <input
            ref="fileInput"
            type="file"
            accept=".json"
            class="visually-hidden"
            aria-label="Select JSON file to import"
            @change="onFileSelected"
          >
        </div>

        <button
          class="btn-action"
          :disabled="!selectedFile || importing"
          aria-label="Import selected JSON file"
          @click="handleImport"
        >
          {{ importing ? 'Importing…' : 'Import' }}
        </button>

        <p
          v-if="importError"
          class="ie-error"
          role="alert"
        >
          {{ importError }}
        </p>

        <div
          v-if="importResult"
          class="ie-result"
          role="status"
        >
          <p class="ie-success">
            ✓ Created {{ importResult.created }} items
          </p>
          <ul
            v-if="importResult.errors.length > 0"
            class="ie-err-list"
          >
            <li
              v-for="(err, i) in importResult.errors"
              :key="i"
            >
              {{ err }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { exportCatalog, importCatalog } from '../api/media.js'

const exporting = ref(false)
const exportError = ref(null)
const selectedFile = ref(null)
const importing = ref(false)
const importError = ref(null)
const importResult = ref(null)
const fileInput = ref(null)
const dragging = ref(false)

async function handleExport() {
  exporting.value = true
  exportError.value = null
  try {
    const data = await exportCatalog()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'media-catalog-export.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    exportError.value = err.message || 'Failed to export catalog'
  } finally {
    exporting.value = false
  }
}

function onFileSelected(event) {
  selectedFile.value = event.target.files[0] || null
  importError.value = null
  importResult.value = null
}

function onDrop(event) {
  dragging.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.name.endsWith('.json')) {
    selectedFile.value = file
    importError.value = null
    importResult.value = null
  }
}

async function handleImport() {
  if (!selectedFile.value) return
  importing.value = true
  importError.value = null
  importResult.value = null
  try {
    const text = await readFileAsText(selectedFile.value)
    let parsed
    try { parsed = JSON.parse(text) }
    catch { throw new Error('Invalid JSON file') }
    importResult.value = await importCatalog(parsed)
  } catch (err) {
    importError.value = err.message || 'Failed to import catalog'
  } finally {
    importing.value = false
  }
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsText(file)
  })
}
</script>

<style scoped>
.ie-view {
  max-width: 860px;
  margin: 0 auto;
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
  margin-bottom: 1.75rem;
}

.ie-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1.25rem;
}

.ie-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
}

.ie-card-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.5rem;
}

.ie-icon {
  font-size: 1.5rem;
}

.ie-card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
}

.ie-desc {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  margin-bottom: 1.25rem;
  line-height: 1.5;
}

.btn-action {
  width: 100%;
  padding: 0.55rem 1rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.87rem;
  cursor: pointer;
  transition: background var(--transition-fast), transform var(--transition-fast);
}

.btn-action:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
}

.btn-action:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Drop zone */
.drop-zone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  padding: 1.75rem 1rem;
  margin-bottom: 0.85rem;
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-muted);
}

.drop-zone:hover,
.drop-zone--hover {
  border-color: var(--color-primary);
  background: var(--color-primary-ghost);
  color: var(--color-primary);
}

.drop-text {
  font-size: 0.82rem;
  font-weight: 500;
}

/* Feedback */
.ie-error {
  color: var(--color-error);
  background: var(--color-error-bg);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  margin-top: 0.65rem;
  font-size: 0.82rem;
  font-weight: 500;
}

.ie-result {
  margin-top: 0.65rem;
  padding: 0.75rem;
  background: var(--color-success-bg);
  border-radius: var(--radius-sm);
}

.ie-success {
  color: var(--color-success);
  font-weight: 600;
  font-size: 0.85rem;
}

.ie-err-list {
  margin: 0.4rem 0 0 1.15rem;
  padding: 0;
  color: var(--color-error);
  font-size: 0.82rem;
}

@media (max-width: 500px) {
  .ie-grid { grid-template-columns: 1fr; }
}
</style>
