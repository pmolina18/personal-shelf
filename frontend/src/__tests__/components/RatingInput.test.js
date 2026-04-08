import { mount } from '@vue/test-utils'
import RatingInput from '@/components/RatingInput.vue'

describe('RatingInput', () => {
  /** Validates: Requirement 9.1 */
  it('renderiza 10 botones de estrella cuando no está deshabilitado', () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: null, disabled: false },
    })

    const stars = wrapper.findAll('.star-btn')
    expect(stars).toHaveLength(10)
    expect(wrapper.find('.rating-stars').exists()).toBe(true)
    expect(wrapper.find('.rating-disabled-msg').exists()).toBe(false)
  })

  /** Validates: Requirement 9.2 */
  it('muestra mensaje de estado deshabilitado cuando disabled es true', () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: null, disabled: true },
    })

    expect(wrapper.find('.rating-disabled-msg').exists()).toBe(true)
    expect(wrapper.find('.rating-disabled-msg').text()).toBe(
      'Start or complete this item to rate it'
    )
    expect(wrapper.find('.rating-stars').exists()).toBe(false)
  })

  /** Validates: Requirement 9.3 */
  it('emite update:modelValue con número correcto al clic en estrella', async () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: null, disabled: false },
    })

    const stars = wrapper.findAll('.star-btn')
    await stars[4].trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([5])
  })

  /** Validates: Requirement 9.3 */
  it('emite update:modelValue con 1 al clic en primera estrella', async () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: null, disabled: false },
    })

    const stars = wrapper.findAll('.star-btn')
    await stars[0].trigger('click')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual([1])
  })

  /** Validates: Requirement 9.3 */
  it('emite update:modelValue con 10 al clic en última estrella', async () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: null, disabled: false },
    })

    const stars = wrapper.findAll('.star-btn')
    await stars[9].trigger('click')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual([10])
  })

  /** Validates: Requirement 9.4 */
  it('estrellas hasta modelValue tienen clase active y muestra texto N/10', () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: 7, disabled: false },
    })

    const stars = wrapper.findAll('.star-btn')
    for (let i = 0; i < 7; i++) {
      expect(stars[i].classes()).toContain('active')
    }
    for (let i = 7; i < 10; i++) {
      expect(stars[i].classes()).not.toContain('active')
    }

    expect(wrapper.find('.rating-value').exists()).toBe(true)
    expect(wrapper.find('.rating-value').text()).toBe('7/10')
  })

  /** Validates: Requirement 9.4 */
  it('no muestra texto N/10 cuando modelValue es null', () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: null, disabled: false },
    })

    expect(wrapper.find('.rating-value').exists()).toBe(false)
  })

  /** Validates: Requirement 9.4 */
  it('ninguna estrella tiene clase active cuando modelValue es null', () => {
    const wrapper = mount(RatingInput, {
      props: { modelValue: null, disabled: false },
    })

    const stars = wrapper.findAll('.star-btn')
    stars.forEach((star) => {
      expect(star.classes()).not.toContain('active')
    })
  })
})
