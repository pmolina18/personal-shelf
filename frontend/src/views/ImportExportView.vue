<template>
  <section
    class="import-export-view"
    aria-label="Import and export catalog"
  >
    <h1>Import / Export</h1>

    <section
      class="ie-section"
      aria-label="Export catalog"
    >
      <h2>Export</h2>
      <p>Download your entire catalog as a JSON file.</p>
      <button
        class="btn-export"
        :disabled="exporting"
        aria-label="Export catalog to JSON file"
        @click="handleExport"
      >
        {{ exporting ? 'Exporting…' : 'Export Catalog' }}
      </button>
      <p
        v-if="exportError"
        class="ie-error"
        role="alert"
      >
        {{ exportError }}
      </p>
    </section>

    <section
      class="ie-section"
      aria-label="Import catalog"
    >
      <h2>Import</h2>
      <p>Upload a JSON file to import media items into your catalog.</p>
      <div class="import-controls">
        <input
          ref="fileInput"
          type="file"
          accept=".json"
          aria-label="Select JSON file to import"
          @change="onFileSelected"
        >
        <button
          class="btn-import"
          :disabled="!selectedFile || importing"
          aria-label="Import selected JSON file"
          @click="handleImport"
        >
          {{ importing ? 'Importing…' : 'Import' }}
        </button>
      </div>
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
          Created {{ importResult.created }} items
        </p>
        <ul
          v-if="importResult.errors.length > 0"
          class="ie-errors-list"
        >
          <li
            v-for="(err, i) in importResult.errors"
            :key="i"
          >
            {{ err }}
          </li>
        </ul>
      </div>
    </section>
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

async function handleImport() {
  if (!selectedFile.value) return
  importing.value = true
  importError.value = null
  importResult.value = null
  try {
    const text = await readFileAsText(selectedFile.value)
    let parsed
    try {
      parsed = JSON.parse(text)
    } catch {
      throw new Error('Invalid JSON file')
    }
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
.import-export-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem;
}

.import-export-view h1 {
  margin-bottom: 1rem;
}

.ie-section {
  margin-bottom: 2rem;
}

.ie-section h2 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.3rem;
}

.ie-section p {
  margin-bottom: 0.75rem;
  color: #555;
}

.import-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn-export,
.btn-import {
  padding: 0.5rem 1rem;
  background: #4a90d9;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-export:hover:not(:disabled),
.btn-import:hover:not(:disabled) {
  background: #3a7bc8;
}

.btn-export:disabled,
.btn-import:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-export:focus-visible,
.btn-import:focus-visible {
  outline: 2px solid #4a90d9;
  outline-offset: 2px;
}

.ie-error {
  color: #c62828;
  background: #ffebee;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  margin-top: 0.5rem;
}

.ie-result {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: #e8f5e9;
  border-radius: 6px;
}

.ie-success {
  color: #2e7d32;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.ie-errors-list {
  margin: 0.5rem 0 0 1.25rem;
  padding: 0;
  color: #c62828;
}

.ie-errors-list li {
  margin-bottom: 0.25rem;
}
</style>
