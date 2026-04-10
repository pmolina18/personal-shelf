import { createRouter, createWebHistory } from 'vue-router'

const CatalogView = () => import('../views/CatalogView.vue')
const MediaDetailView = () => import('../views/MediaDetailView.vue')
const StatsView = () => import('../views/StatsView.vue')
const ImportExportView = () => import('../views/ImportExportView.vue')
const LoginView = () => import('../views/LoginView.vue')
const RegisterView = () => import('../views/RegisterView.vue')
const FeedView = () => import('../views/FeedView.vue')
const FriendsView = () => import('../views/FriendsView.vue')
const FriendCollectionView = () => import('../views/FriendCollectionView.vue')
const RecommendationsView = () => import('../views/RecommendationsView.vue')

const routes = [
  // Auth routes (public)
  { path: '/login', name: 'login', component: LoginView, meta: { isAuth: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { isAuth: true } },

  // Protected routes
  { path: '/', name: 'catalog', component: CatalogView },
  { path: '/media/new', name: 'media-create', component: MediaDetailView },
  { path: '/media/:id', name: 'media-detail', component: MediaDetailView },
  { path: '/stats', name: 'stats', component: StatsView },
  { path: '/import-export', name: 'import-export', component: ImportExportView },
  { path: '/feed', name: 'feed', component: FeedView },
  { path: '/friends', name: 'friends', component: FriendsView },
  { path: '/friends/:id/collection', name: 'friend-collection', component: FriendCollectionView },
  { path: '/recommendations', name: 'recommendations', component: RecommendationsView },
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
})

export default router
