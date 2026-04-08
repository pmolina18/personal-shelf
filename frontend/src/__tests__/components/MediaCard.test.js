import { mount } from '@vue/test-utils'
import MediaCard from '@/components/MediaCard.vue'

const RouterLinkStub = {
  template: '<a :href="to"><slot/></a>',
  props: ['to'],
}

const baseItem = {
  id: 42,
  title: 'Inception',
  media_type: 'movie',
  status: 'in_progress',
  rating: 8,
  image_url: 'https://example.com/poster.jpg',
  tags: ['sci-fi', 'thriller'],
}

function mountCard(itemOverrides = {}) {
  return mount(MediaCard, {
    props: { item: { ...baseItem, ...itemOverrides } },
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

describe('MediaCard', () => {
  /** Validates: Requirement 6.1 */
  it('renderiza título, badges de tipo y estado', () => {
    const wrapper = mountCard()

    expect(wrapper.find('.card-title').text()).toBe('Inception')
    expect(wrapper.find('.badge-type').text()).toBe('Movie')
    expect(wrapper.find('.badge-status').text()).toBe('In Progress')
  })

  /** Validates: Requirement 6.5 */
  it('router-link apunta a /media/{id}', () => {
    const wrapper = mountCard()

    expect(wrapper.find('a').attributes('href')).toBe('/media/42')
  })

  /** Validates: Requirement 6.2 */
  it('muestra rating "★ N/10" cuando existe', () => {
    const wrapper = mountCard({ rating: 8 })

    const rating = wrapper.find('.card-rating')
    expect(rating.exists()).toBe(true)
    expect(rating.text()).toBe('★ 8/10')
  })

  /** Validates: Requirement 6.3 */
  it('no renderiza rating cuando es null', () => {
    const wrapper = mountCard({ rating: null })

    expect(wrapper.find('.card-rating').exists()).toBe(false)
  })

  /** Validates: Requirement 6.4 */
  it('usa placeholder cuando no hay image_url', () => {
    const wrapper = mountCard({ image_url: null, media_type: 'book' })

    expect(wrapper.find('img').attributes('src')).toBe(
      'https://placehold.co/300x450?text=Book'
    )
  })

  /** Validates: Requirement 6.4 */
  it('usa imagen proporcionada cuando image_url existe', () => {
    const wrapper = mountCard()

    expect(wrapper.find('img').attributes('src')).toBe('https://example.com/poster.jpg')
  })

  /** Validates: Requirement 6.6 */
  describe('labels computados mapean valores correctamente', () => {
    it.each([
      ['movie', 'Movie'],
      ['book', 'Book'],
      ['series', 'Series'],
    ])('typeLabel: %s → %s', (type, expected) => {
      const wrapper = mountCard({ media_type: type })
      expect(wrapper.find('.badge-type').text()).toBe(expected)
    })

    it.each([
      ['pending', 'Pending'],
      ['in_progress', 'In Progress'],
      ['completed', 'Completed'],
    ])('statusLabel: %s → %s', (status, expected) => {
      const wrapper = mountCard({ status })
      expect(wrapper.find('.badge-status').text()).toBe(expected)
    })
  })
})
