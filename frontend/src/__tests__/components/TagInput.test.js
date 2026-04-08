import { mount } from '@vue/test-utils'
import TagInput from '@/components/TagInput.vue'

describe('TagInput', () => {
  /** Validates: Requirement 10.1 */
  it('renderiza chips con botón de eliminar para cada tag en modelValue', () => {
    const wrapper = mount(TagInput, {
      props: { modelValue: ['action', 'sci-fi'] },
    })

    const chips = wrapper.findAll('.tag-chip')
    expect(chips).toHaveLength(2)
    expect(chips[0].text()).toContain('action')
    expect(chips[1].text()).toContain('sci-fi')

    chips.forEach((chip) => {
      expect(chip.find('.tag-remove').exists()).toBe(true)
    })
  })

  /** Validates: Requirement 10.2 */
  it('Enter con texto emite update:modelValue con array actualizado incluyendo nuevo tag', async () => {
    const wrapper = mount(TagInput, {
      props: { modelValue: ['action'] },
    })

    const input = wrapper.find('#tag-field')
    await input.setValue('comedy')
    await input.trigger('keydown.enter')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([['action', 'comedy']])
  })

  /** Validates: Requirement 10.3 */
  it('tag duplicado no emite evento y limpia campo', async () => {
    const wrapper = mount(TagInput, {
      props: { modelValue: ['action', 'sci-fi'] },
    })

    const input = wrapper.find('#tag-field')
    await input.setValue('action')
    await input.trigger('keydown.enter')

    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    expect(input.element.value).toBe('')
  })

  /** Validates: Requirement 10.4 */
  it('al alcanzar max muestra mensaje de límite y no permite agregar', async () => {
    const wrapper = mount(TagInput, {
      props: { modelValue: ['action', 'sci-fi'], max: 2 },
    })

    expect(wrapper.find('.tag-limit-msg').exists()).toBe(true)
    expect(wrapper.find('.tag-limit-msg').text()).toBe('Maximum 2 tags')

    const input = wrapper.find('#tag-field')
    await input.setValue('comedy')
    await input.trigger('keydown.enter')

    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
  })

  /** Validates: Requirement 10.5 */
  it('clic en eliminar emite array sin el tag eliminado', async () => {
    const wrapper = mount(TagInput, {
      props: { modelValue: ['action', 'sci-fi', 'comedy'] },
    })

    const removeButtons = wrapper.findAll('.tag-remove')
    await removeButtons[0].trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([['sci-fi', 'comedy']])
  })

  /** Validates: Requirement 10.6 */
  it('botón Add deshabilitado cuando campo vacío', () => {
    const wrapper = mount(TagInput, {
      props: { modelValue: [] },
    })

    const addBtn = wrapper.find('.btn-add-tag')
    expect(addBtn.attributes('disabled')).toBeDefined()
  })
})
