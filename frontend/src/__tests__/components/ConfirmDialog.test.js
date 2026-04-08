import { mount } from '@vue/test-utils'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

describe('ConfirmDialog', () => {
  let wrapper

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
      wrapper = null
    }
  })

  const defaultProps = {
    open: true,
    title: 'Delete Item',
    message: 'Are you sure you want to delete this item?',
  }

  /** Validates: Requirement 4.1 */
  it('no renderiza el diálogo cuando open es false', () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: { ...defaultProps, open: false },
    })

    expect(document.querySelector('.dialog-overlay')).toBeNull()
    expect(document.querySelector('.dialog-box')).toBeNull()
  })

  /** Validates: Requirement 4.2 */
  it('renderiza título y mensaje cuando open es true', () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: defaultProps,
    })

    const dialogBox = document.querySelector('.dialog-box')
    expect(dialogBox).not.toBeNull()
    expect(dialogBox.querySelector('.dialog-title').textContent).toBe('Delete Item')
    expect(dialogBox.querySelector('.dialog-message').textContent).toBe(
      'Are you sure you want to delete this item?'
    )
  })

  /** Validates: Requirement 4.3 */
  it('emite confirm al hacer clic en el botón Confirm', async () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: defaultProps,
    })

    const confirmBtn = document.querySelector('.btn-confirm')
    await confirmBtn.click()

    expect(wrapper.emitted('confirm')).toHaveLength(1)
  })

  /** Validates: Requirement 4.4 */
  it('emite cancel al hacer clic en el botón Cancel', async () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: defaultProps,
    })

    const cancelBtn = document.querySelector('.btn-cancel')
    await cancelBtn.click()

    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  /** Validates: Requirement 4.5 */
  it('emite cancel al hacer clic en el overlay', async () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: defaultProps,
    })

    const overlay = document.querySelector('.dialog-overlay')
    await overlay.click()

    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  /** Validates: Requirement 4.6 */
  it('tiene los atributos ARIA correctos', () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: defaultProps,
    })

    const dialogBox = document.querySelector('.dialog-box')
    expect(dialogBox.getAttribute('role')).toBe('dialog')
    expect(dialogBox.getAttribute('aria-modal')).toBe('true')
    expect(dialogBox.getAttribute('aria-label')).toBe('Delete Item')
  })
})
