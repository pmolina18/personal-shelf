import { mount } from '@vue/test-utils'
import MediaForm from '@/components/MediaForm.vue'

const sampleData = {
  title: 'Test Movie',
  media_type: 'movie',
  year: 2024,
  creator: 'Test Director',
  notes: 'Some notes',
}

describe('MediaForm', () => {
  /** Validates: Requirement 7.1 */
  it('sin initialData muestra campos vacíos y botón "Create"', () => {
    const wrapper = mount(MediaForm)

    expect(wrapper.find('#mf-title').element.value).toBe('')
    expect(wrapper.find('#mf-type').element.value).toBe('')
    expect(wrapper.find('#mf-year').element.value).toBe('')
    expect(wrapper.find('#mf-creator').element.value).toBe('')
    expect(wrapper.find('#mf-notes').element.value).toBe('')
    expect(wrapper.find('button.btn-submit').text()).toBe('Create')
  })

  /** Validates: Requirement 7.2 */
  it('con initialData muestra datos populados y botón "Save Changes"', () => {
    const wrapper = mount(MediaForm, {
      props: { initialData: sampleData },
    })

    expect(wrapper.find('#mf-title').element.value).toBe('Test Movie')
    expect(wrapper.find('#mf-type').element.value).toBe('movie')
    expect(wrapper.find('#mf-year').element.value).toBe('2024')
    expect(wrapper.find('#mf-creator').element.value).toBe('Test Director')
    expect(wrapper.find('#mf-notes').element.value).toBe('Some notes')
    expect(wrapper.find('button.btn-submit').text()).toBe('Save Changes')
  })

  /** Validates: Requirement 7.3 */
  it('envío sin título muestra "Title is required" y no emite submit', async () => {
    const wrapper = mount(MediaForm)

    await wrapper.find('form').trigger('submit')

    expect(wrapper.find('.field-error').text()).toBe('Title is required')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  /** Validates: Requirement 7.4 */
  it('envío con título válido emite submit con datos formateados', async () => {
    const wrapper = mount(MediaForm, {
      props: { initialData: sampleData },
    })

    await wrapper.find('form').trigger('submit')

    const emitted = wrapper.emitted('submit')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0]).toEqual({
      title: 'Test Movie',
      media_type: 'movie',
      year: 2024,
      creator: 'Test Director',
      notes: 'Some notes',
    })
  })

  /** Validates: Requirement 7.5 */
  it('cambio de initialData después del montaje actualiza campos', async () => {
    const wrapper = mount(MediaForm, {
      props: { initialData: null },
    })

    expect(wrapper.find('#mf-title').element.value).toBe('')

    await wrapper.setProps({
      initialData: {
        title: 'Updated Title',
        media_type: 'book',
        year: 2020,
        creator: 'New Author',
        notes: 'Updated notes',
      },
    })

    expect(wrapper.find('#mf-title').element.value).toBe('Updated Title')
    expect(wrapper.find('#mf-type').element.value).toBe('book')
    expect(wrapper.find('#mf-year').element.value).toBe('2020')
    expect(wrapper.find('#mf-creator').element.value).toBe('New Author')
    expect(wrapper.find('#mf-notes').element.value).toBe('Updated notes')
    expect(wrapper.find('button.btn-submit').text()).toBe('Save Changes')
  })

  /** Validates: Requirement 7.6 */
  it('valores opcionales vacíos (year, creator, notes) se emiten como null', async () => {
    const wrapper = mount(MediaForm)

    await wrapper.find('#mf-title').setValue('Only Title')
    await wrapper.find('#mf-type').setValue('series')
    await wrapper.find('form').trigger('submit')

    const emitted = wrapper.emitted('submit')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0]).toEqual({
      title: 'Only Title',
      media_type: 'series',
      year: null,
      creator: null,
      notes: null,
    })
  })
})
