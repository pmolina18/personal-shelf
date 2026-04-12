import { createRouter, createWebHistory } from 'vue-router'

const CatalogView = () => import('../views/CatalogView.vue')
const MediaDetailView = () => import('../views/MediaDetailView.vue')
const StatsView = () => import('../views/StatsView.vue')
const LoginView = () => import('../views/LoginView.vue')
const RegisterView = () => import('../views/RegisterView.vue')
const FriendsView = () => import('../views/FriendsView.vue')
const FriendCollectionView = () => import('../views/FriendCollectionView.vue')
const RecommendationsView = () => import('../views/RecommendationsView.vue')
const ExploreView = () => import('../views/ExploreView.vue')
const SuggestionsView = () => import('../views/SuggestionsView.vue')
const AdminView = () => import('../views/AdminView.vue')

const routes = [
  // Auth routes (public)
  { path: '/login', name: 'login', component: LoginView, meta: { isAuth: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { isAuth: true } },

  // Protected routes
  { path: '/', name: 'catalog', component: CatalogView },
  { path: '/media/new', name: 'media-create', component: MediaDetailView },
  { path: '/media/:id', name: 'media-detail', component: MediaDetailView },
  { path: '/stats', name: 'stats', component: StatsView },
  { path: '/feed', redirect: '/explore' },
  { path: '/explore', name: 'explore', component: ExploreView },
  { path: '/friends', name: 'friends', component: FriendsView },
  { path: '/friends/:id/collection', name: 'friend-collection', component: FriendCollectionView },
  { path: '/recommendations', name: 'recommendations', component: RecommendationsView },
  { path: '/suggestions', name: 'suggestions', component: SuggestionsView },
  { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const isAuthenticated = !!localStorage.getItem('access_token')

  // Authenticated user hitting auth pages → redirect to catalog
  if (to.meta.isAuth && isAuthenticated) {
    return { name: 'catalog' }
  }

  // Unauthenticated user hitting protected pages → redirect to login
  if (!to.meta.isAuth && !isAuthenticated) {
    return { name: 'login' }
  }

  // Admin-only route: check is_admin from stored user object
  if (to.meta.requiresAdmin) {
    try {
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
      if (!storedUser.is_admin) {
        return { name: 'catalog' }
      }
    } catch {
      return { name: 'catalog' }
    }
  }
})

export default router
