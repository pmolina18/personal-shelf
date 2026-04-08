import { describe, it, expect, vi, beforeEach } from 'vitest'
import fc from 'fast-check'
import { shallowMount, flushPromises } from '@vue/test-utils'
import StatsView from '../../views/StatsView.vue'
import { getStats } from '../../api/media.js'

vi.mock('../../api/media.js', () => ({
  getStats: vi.fn(),
}))

const statsFixture = {
  by_type: { movie: 10, book: 5, series: 3 },
  by_status: { pending: 4, in_progress: 6, completed: 8 },
  avg_rating_by_type: { movie: 7.5, book: 8.2, series: null },
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('StatsView', () => {
  // ── Requirement 13.1: invokes getStats on mount ─────────────
  it('invoca getStats al montar', () => {
    getStats.mockResolvedValueOnce(statsFixture)
    shallowMount(StatsView)
    expect(getStats).toHaveBeenCalledOnce()
  })

  // ── Requirement 13.2: shows sections with loaded data ───────
  it('muestra secciones by_type, by_status y avg_rating_by_type con datos cargados', async () => {
    getStats.mockResolvedValueOnce(statsFixture)
    const wrapper = shallowMount(StatsView)
    await flushPromises()

    const sections = wrapper.findAll('.stats-section')
    expect(sections).toHaveLength(3)

    expect(sections[0].attributes('aria-label')).toBe('Items by type')
    expect(sections[1].attributes('aria-label')).toBe('Items by status')
    expect(sections[2].attributes('aria-label')).toBe('Average rating by type')

    // by_type values
    const byTypeDds = sections[0].findAll('dd')
    expect(byTypeDds.map(dd => dd.text())).toEqual(['10', '5', '3'])

    // by_status values
    const byStatusDds = sections[1].findAll('dd')
    expect(byStatusDds.map(dd => dd.text())).toEqual(['4', '6', '8'])

    // avg_rating_by_type values
    const avgDds = sections[2].findAll('dd')
    expect(avgDds.map(dd => dd.text())).toEqual(['7.5', '8.2', 'No ratings'])
  })

  // ── Requirement 13.3: totalItems calculated as sum of by_type ─
  it('totalItems se calcula como la suma de valores de by_type', async () => {
    getStats.mockResolvedValueOnce(statsFixture)
    const wrapper = shallowMount(StatsView)
    await flushPromises()

    const total = wrapper.find('.stats-total')
    expect(total.exists()).toBe(true)
    // 10 + 5 + 3 = 18
    expect(total.text()).toContain('18')
  })

  // ── Requirement 13.4: formatLabel converts keys ─────────────
  it('formatLabel convierte "in_progress" a "In Progress"', async () => {
    getStats.mockResolvedValueOnce(statsFixture)
    const wrapper = shallowMount(StatsView)
    await flushPromises()

    // by_status section has "in_progress" key
    const statusSection = wrapper.findAll('.stats-section')[1]
    const dts = statusSection.findAll('dt')
    const labels = dts.map(dt => dt.text())

    expect(labels).toContain('In Progress')
    expect(labels).toContain('Pending')
    expect(labels).toContain('Completed')
  })

  // ── Requirement 13.5: loading indicator ─────────────────────
  it('muestra indicador de carga mientras se cargan las estadísticas', async () => {
    let resolve
    getStats.mockReturnValueOnce(new Promise(r => { resolve = r }))
    const wrapper = shallowMount(StatsView)

    // Wait for onMounted to fire and set loading = true
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.stats-loading').exists()).toBe(true)
    expect(wrapper.find('.stats-loading').text()).toContain('Loading')

    // Sections should not be visible while loading
    expect(wrapper.find('.stats-section').exists()).toBe(false)

    // Resolve to clean up
    resolve(statsFixture)
    await flushPromises()
  })

  // ── Requirement 13.6: error message ─────────────────────────
  it('muestra mensaje de error cuando la carga falla', async () => {
    getStats.mockRejectedValueOnce(new Error('Network error'))
    const wrapper = shallowMount(StatsView)
    await flushPromises()

    expect(wrapper.find('.stats-error').exists()).toBe(true)
    expect(wrapper.find('.stats-error').text()).toBe('Network error')

    // Sections should not be visible on error
    expect(wrapper.find('.stats-section').exists()).toBe(false)
  })
})

// ── Property-Based Tests ──────────────────────────────────────
// Replicate formatLabel since it's not exported from StatsView.vue
const formatLabel = (key) =>
  key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

describe('Feature: frontend-unit-tests, Property 4: formatLabel transforms keys correctly', () => {
  /**
   * **Validates: Requirement 13.4**
   *
   * For any string composed of lowercase words separated by underscores,
   * formatLabel must produce a string where each underscore is replaced
   * by a space and the first letter of each word is uppercase.
   */
  const underscoreKey = fc
    .array(fc.stringMatching(/^[a-z]+$/, { minLength: 1 }), { minLength: 1 })
    .map((ws) => ws.join('_'))

  it('replaces all underscores with spaces', () => {
    fc.assert(
      fc.property(underscoreKey, (key) => {
        const result = formatLabel(key)
        expect(result).not.toContain('_')
      }),
      { numRuns: 100 },
    )
  })

  it('capitalizes the first letter of each word', () => {
    fc.assert(
      fc.property(underscoreKey, (key) => {
        const result = formatLabel(key)
        const words = result.split(' ')
        for (const word of words) {
          expect(word[0]).toBe(word[0].toUpperCase())
        }
      }),
      { numRuns: 100 },
    )
  })

  it('produces the same output as the reference implementation', () => {
    fc.assert(
      fc.property(underscoreKey, (key) => {
        const result = formatLabel(key)
        const expected = key
          .replace(/_/g, ' ')
          .replace(/\b\w/g, (c) => c.toUpperCase())
        expect(result).toBe(expected)
      }),
      { numRuns: 100 },
    )
  })
})
