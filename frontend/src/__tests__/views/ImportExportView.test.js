import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ImportExportView from '../../views/ImportExportView.vue'
import { exportCatalog, importCatalog } from '../../api/media.js'

vi.mock('../../api/media.js', () => ({
  exportCatalog: vi.fn(),
  importCatalog: vi.fn(),
}))

// ── Global mocks ──────────────────────────────────────────────
const originalCreateObjectURL = globalThis.URL.createObjectURL
const originalRevokeObjectURL = globalThis.URL.revokeObjectURL
const OriginalFileReader = globalThis.FileReader

beforeEach(() => {
  vi.clearAllMocks()
  globalThis.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
  globalThis.URL.revokeObjectURL = vi.fn()
})

afterEach(() => {
  globalThis.URL.createObjectURL = originalCreateObjectURL
  globalThis.URL.revokeObjectURL = originalRevokeObjectURL
  globalThis.FileReader = OriginalFileReader
})

// Helper: mock FileReader that resolves with given text
function mockFileReader(text) {
  globalThis.FileReader = class {
    readAsText() {
      setTimeout(() => {
        this.result = text
        this.onload()
      }, 0)
    }
  }
}

// Helper: mock document.createElement to spy on anchor click
function spyOnAnchorClick() {
  const clickSpy = vi.fn()
  const originalCreateElement = document.createElement.bind(document)
  vi.spyOn(document, 'createElement').mockImplementation((tag) => {
    const el = originalCreateElement(tag)
    if (tag === 'a') {
      el.click = clickSpy
    }
    return el
  })
  return clickSpy
}

describe('ImportExportView', () => {
  // ── Requirement 14.1: Export invokes exportCatalog and creates download link ──
  it('clic en Export invoca exportCatalog y crea enlace de descarga con blob JSON', async () => {
    const catalogData = { items: [{ id: 1, title: 'Test' }] }
    exportCatalog.mockResolvedValueOnce(catalogData)
    const clickSpy = spyOnAnchorClick()

    const wrapper = mount(ImportExportView)
    await wrapper.find('.btn-export').trigger('click')
    await flushPromises()

    expect(exportCatalog).toHaveBeenCalledOnce()
    expect(globalThis.URL.createObjectURL).toHaveBeenCalledOnce()

    // Verify the blob passed to createObjectURL is a Blob with JSON content
    const blob = globalThis.URL.createObjectURL.mock.calls[0][0]
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toBe('application/json')

    // Anchor was clicked to trigger download
    expect(clickSpy).toHaveBeenCalledOnce()

    // URL was revoked after download
    expect(globalThis.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  // ── Requirement 14.2: Export error shows error message ────────
  it('error de exportación muestra mensaje de error', async () => {
    exportCatalog.mockRejectedValueOnce(new Error('Server down'))

    const wrapper = mount(ImportExportView)
    await wrapper.find('.btn-export').trigger('click')
    await flushPromises()

    const errorEl = wrapper.find('[aria-label="Export catalog"] .ie-error')
    expect(errorEl.exists()).toBe(true)
    expect(errorEl.text()).toBe('Server down')
  })

  // ── Requirement 14.3: Select file + Import reads with FileReader ──
  it('seleccionar archivo + Import lee con FileReader, parsea JSON e invoca importCatalog', async () => {
    const importData = { items: [{ title: 'Imported' }] }
    const importResponse = { created: 1, errors: [] }
    mockFileReader(JSON.stringify(importData))
    importCatalog.mockResolvedValueOnce(importResponse)

    const wrapper = mount(ImportExportView)

    // Simulate file selection
    const fileInput = wrapper.find('input[type="file"]')
    const mockFile = new File(['{}'], 'catalog.json', { type: 'application/json' })
    Object.defineProperty(fileInput.element, 'files', {
      value: [mockFile],
      writable: false,
    })
    await fileInput.trigger('change')

    // Click import
    await wrapper.find('.btn-import').trigger('click')

    // Wait for FileReader setTimeout + promise resolution
    await vi.waitFor(async () => {
      await flushPromises()
      expect(importCatalog).toHaveBeenCalledOnce()
    })

    expect(importCatalog).toHaveBeenCalledWith(importData)
  })

  // ── Requirement 14.4: Successful import shows number of created items ──
  it('importación exitosa muestra número de items creados', async () => {
    const importResponse = { created: 5, errors: [] }
    mockFileReader(JSON.stringify({ items: [] }))
    importCatalog.mockResolvedValueOnce(importResponse)

    const wrapper = mount(ImportExportView)

    // Select file
    const fileInput = wrapper.find('input[type="file"]')
    const mockFile = new File(['{}'], 'catalog.json', { type: 'application/json' })
    Object.defineProperty(fileInput.element, 'files', {
      value: [mockFile],
      writable: false,
    })
    await fileInput.trigger('change')

    // Import
    await wrapper.find('.btn-import').trigger('click')

    await vi.waitFor(async () => {
      await flushPromises()
      const result = wrapper.find('.ie-result')
      expect(result.exists()).toBe(true)
    })

    const success = wrapper.find('.ie-success')
    expect(success.text()).toBe('Created 5 items')
  })

  // ── Requirement 14.5: Invalid JSON file shows error ───────────
  it('archivo JSON inválido muestra error "Invalid JSON file"', async () => {
    mockFileReader('this is not valid json {{{')

    const wrapper = mount(ImportExportView)

    // Select file
    const fileInput = wrapper.find('input[type="file"]')
    const mockFile = new File(['bad'], 'bad.json', { type: 'application/json' })
    Object.defineProperty(fileInput.element, 'files', {
      value: [mockFile],
      writable: false,
    })
    await fileInput.trigger('change')

    // Import
    await wrapper.find('.btn-import').trigger('click')

    await vi.waitFor(async () => {
      await flushPromises()
      const errorEl = wrapper.find('[aria-label="Import catalog"] .ie-error')
      expect(errorEl.exists()).toBe(true)
    })

    const errorEl = wrapper.find('[aria-label="Import catalog"] .ie-error')
    expect(errorEl.text()).toBe('Invalid JSON file')
  })

  // ── Requirement 14.6: Import button disabled without file selected ──
  it('botón Import deshabilitado sin archivo seleccionado', () => {
    const wrapper = mount(ImportExportView)
    const importBtn = wrapper.find('.btn-import')
    expect(importBtn.attributes('disabled')).toBeDefined()
  })

  // ── Requirement 14.7: Export button disabled and shows "Exporting…" during export ──
  it('botón Export deshabilitado y muestra "Exporting…" durante exportación', async () => {
    let resolveExport
    exportCatalog.mockReturnValueOnce(new Promise((r) => { resolveExport = r }))

    const wrapper = mount(ImportExportView)
    const exportBtn = wrapper.find('.btn-export')

    // Before click
    expect(exportBtn.text()).toBe('Export Catalog')
    expect(exportBtn.attributes('disabled')).toBeUndefined()

    // Click export — don't await, check intermediate state
    wrapper.find('.btn-export').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.btn-export').text()).toBe('Exporting…')
    expect(wrapper.find('.btn-export').attributes('disabled')).toBeDefined()

    // Resolve to clean up
    resolveExport({ items: [] })
    await flushPromises()

    // After export completes, button returns to normal
    expect(wrapper.find('.btn-export').text()).toBe('Export Catalog')
    expect(wrapper.find('.btn-export').attributes('disabled')).toBeUndefined()
  })
})
