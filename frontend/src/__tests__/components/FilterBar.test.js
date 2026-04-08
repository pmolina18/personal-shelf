import { mount } from '@vue/test-utils'
import FilterBar from '@/components/FilterBar.vue'

describe('FilterBar', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(FilterBar)
  })

  /** Validates: Requirement 5.1 */
  it('renderiza los 4 campos de filtro', () => {
    expect(wrapper.find('#filter-search').exists()).toBe(true)
    expect(wrapper.find('#filter-type').exists()).toBe(true)
    expect(wrapper.find('#filter-status').exists()).toBe(true)
    expect(wrapper.find('#filter-tag').exists()).toBe(true)
  })

  /** Validates: Requirement 5.2 */
  it('emite update:filters con search al escribir en búsqueda', async () => {
    await wrapper.find('#filter-search').setValue('matrix')

    const emitted = wrapper.emitted('update:filters')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0]).toMatchObject({ search: 'matrix' })
  })

  /** Validates: Requirement 5.3 */
  it('emite update:filters con media_type al seleccionar tipo', async () => {
    await wrapper.find('#filter-type').setValue('movie')

    const emitted = wrapper.emitted('update:filters')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0]).toMatchObject({ media_type: 'movie' })
  })

  /** Validates: Requirement 5.4 */
  it('emite update:filters con status al seleccionar estado', async () => {
    await wrapper.find('#filter-status').setValue('completed')

    const emitted = wrapper.emitted('update:filters')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0]).toMatchObject({ status: 'completed' })
  })

  /** Validates: Requirement 5.5 */
  it('campos vacíos emiten null en la propiedad correspondiente', async () => {
    await wrapper.find('#filter-search').setValue('')

    const emitted = wrapper.emitted('update:filters')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0]).toEqual({
      search: null,
      media_type: null,
      status: null,
      tag: null,
    })
  })

  /** Validates: Requirements 5.2, 5.5 */
  it('emite null para campos no modificados al interactuar con uno', async () => {
    await wrapper.find('#filter-type').setValue('book')

    const emitted = wrapper.emitted('update:filters')
    expect(emitted[0][0]).toEqual({
      search: null,
      media_type: 'book',
      status: null,
      tag: null,
    })
  })
})
