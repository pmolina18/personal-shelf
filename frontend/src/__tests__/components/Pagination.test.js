import { mount } from '@vue/test-utils'
import fc from 'fast-check'
import Pagination from '@/components/Pagination.vue'

describe('Pagination', () => {
  /** Validates: Requirement 8.1 */
  it('no renderiza cuando pages es 1', () => {
    const wrapper = mount(Pagination, {
      props: { page: 1, pages: 1, total: 5 },
    })

    expect(wrapper.find('nav').exists()).toBe(false)
  })

  /** Validates: Requirement 8.1 */
  it('no renderiza cuando pages es 0', () => {
    const wrapper = mount(Pagination, {
      props: { page: 1, pages: 0, total: 0 },
    })

    expect(wrapper.find('nav').exists()).toBe(false)
  })

  /** Validates: Requirement 8.2 */
  it('muestra total de items y controles cuando pages > 1', () => {
    const wrapper = mount(Pagination, {
      props: { page: 1, pages: 5, total: 100 },
    })

    expect(wrapper.find('nav').exists()).toBe(true)
    expect(wrapper.find('.pagination-info').text()).toBe('100 items total')
    expect(wrapper.find('.pagination-controls').exists()).toBe(true)
  })

  /** Validates: Requirement 8.2 */
  it('muestra "item" singular cuando total es 1', () => {
    const wrapper = mount(Pagination, {
      props: { page: 1, pages: 2, total: 1 },
    })

    expect(wrapper.find('.pagination-info').text()).toBe('1 item total')
  })

  /** Validates: Requirement 8.3 */
  it('botón Prev deshabilitado en primera página', () => {
    const wrapper = mount(Pagination, {
      props: { page: 1, pages: 5, total: 100 },
    })

    const buttons = wrapper.findAll('button')
    const prevBtn = buttons[0]
    expect(prevBtn.text()).toBe('← Prev')
    expect(prevBtn.attributes('disabled')).toBeDefined()
  })

  /** Validates: Requirement 8.4 */
  it('botón Next deshabilitado en última página', () => {
    const wrapper = mount(Pagination, {
      props: { page: 5, pages: 5, total: 100 },
    })

    const buttons = wrapper.findAll('button')
    const nextBtn = buttons[buttons.length - 1]
    expect(nextBtn.text()).toBe('Next →')
    expect(nextBtn.attributes('disabled')).toBeDefined()
  })

  /** Validates: Requirements 8.3, 8.4 */
  it('Prev y Next habilitados en página intermedia', () => {
    const wrapper = mount(Pagination, {
      props: { page: 3, pages: 5, total: 100 },
    })

    const buttons = wrapper.findAll('button')
    const prevBtn = buttons[0]
    const nextBtn = buttons[buttons.length - 1]
    expect(prevBtn.attributes('disabled')).toBeUndefined()
    expect(nextBtn.attributes('disabled')).toBeUndefined()
  })

  /** Validates: Requirement 8.5 */
  it('emite update:page al clic en número de página', async () => {
    const wrapper = mount(Pagination, {
      props: { page: 1, pages: 5, total: 100 },
    })

    const buttons = wrapper.findAll('button')
    // buttons: [Prev, 1, 2, 3, Next] — page 1 with pages=5 → visiblePages=[1,2,3]
    // Click page 2 (index 2)
    await buttons[2].trigger('click')

    expect(wrapper.emitted('update:page')).toBeTruthy()
    expect(wrapper.emitted('update:page')[0]).toEqual([2])
  })

  /** Validates: Requirement 8.5 */
  it('emite update:page con page-1 al clic en Prev', async () => {
    const wrapper = mount(Pagination, {
      props: { page: 3, pages: 5, total: 100 },
    })

    const prevBtn = wrapper.findAll('button')[0]
    await prevBtn.trigger('click')

    expect(wrapper.emitted('update:page')[0]).toEqual([2])
  })

  /** Validates: Requirement 8.5 */
  it('emite update:page con page+1 al clic en Next', async () => {
    const wrapper = mount(Pagination, {
      props: { page: 3, pages: 5, total: 100 },
    })

    const buttons = wrapper.findAll('button')
    const nextBtn = buttons[buttons.length - 1]
    await nextBtn.trigger('click')

    expect(wrapper.emitted('update:page')[0]).toEqual([4])
  })

  /** Validates: Requirements 8.6, 8.7 */
  it('visiblePages calcula ventana ±2 en página central', () => {
    const wrapper = mount(Pagination, {
      props: { page: 5, pages: 10, total: 200 },
    })

    const buttons = wrapper.findAll('button')
    // [Prev, 3, 4, 5, 6, 7, Next]
    const pageButtons = buttons.slice(1, -1)
    const pageNumbers = pageButtons.map((b) => Number(b.text()))
    expect(pageNumbers).toEqual([3, 4, 5, 6, 7])
  })

  /** Validates: Requirement 8.7 */
  it('visiblePages no incluye páginas menores que 1 (borde inferior)', () => {
    const wrapper = mount(Pagination, {
      props: { page: 1, pages: 5, total: 100 },
    })

    const buttons = wrapper.findAll('button')
    const pageButtons = buttons.slice(1, -1)
    const pageNumbers = pageButtons.map((b) => Number(b.text()))
    expect(pageNumbers).toEqual([1, 2, 3])
    expect(pageNumbers.every((n) => n >= 1)).toBe(true)
  })

  /** Validates: Requirement 8.7 */
  it('visiblePages no incluye páginas mayores que pages (borde superior)', () => {
    const wrapper = mount(Pagination, {
      props: { page: 10, pages: 10, total: 200 },
    })

    const buttons = wrapper.findAll('button')
    const pageButtons = buttons.slice(1, -1)
    const pageNumbers = pageButtons.map((b) => Number(b.text()))
    expect(pageNumbers).toEqual([8, 9, 10])
    expect(pageNumbers.every((n) => n <= 10)).toBe(true)
  })

  /** Validates: Requirement 8.6 */
  it('página activa tiene clase active', () => {
    const wrapper = mount(Pagination, {
      props: { page: 3, pages: 5, total: 100 },
    })

    const buttons = wrapper.findAll('button')
    const pageButtons = buttons.slice(1, -1)
    const activeButtons = pageButtons.filter((b) => b.classes('active'))
    expect(activeButtons).toHaveLength(1)
    expect(activeButtons[0].text()).toBe('3')
  })
})

describe('Feature: frontend-unit-tests, Property 3: visiblePages calcula ventana correcta', () => {
  /** Validates: Requirements 8.6, 8.7 */
  it('visiblePages contiene exactamente el rango [max(1, page-2), min(pages, page+2)], ordenado y sin duplicados', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 100 }).chain((pages) =>
          fc.integer({ min: 1, max: pages }).map((page) => ({ page, pages }))
        ),
        ({ page, pages }) => {
          const total = pages * 20
          const wrapper = mount(Pagination, {
            props: { page, pages, total },
          })

          const buttons = wrapper.findAll('button')
          const pageButtons = buttons.slice(1, -1)
          const pageNumbers = pageButtons.map((b) => Number(b.text()))

          const start = Math.max(1, page - 2)
          const end = Math.min(pages, page + 2)
          const expected = Array.from({ length: end - start + 1 }, (_, i) => start + i)

          // Array matches expected range exactly
          expect(pageNumbers).toEqual(expected)

          // Sorted ascending
          for (let i = 1; i < pageNumbers.length; i++) {
            expect(pageNumbers[i]).toBeGreaterThan(pageNumbers[i - 1])
          }

          // No duplicates
          expect(new Set(pageNumbers).size).toBe(pageNumbers.length)

          wrapper.unmount()
        }
      ),
      { numRuns: 100 }
    )
  })
})
