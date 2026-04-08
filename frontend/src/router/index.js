import { createRouter, createWebHistory } from 'vue-router'

const CatalogView = () => import('../views/CatalogView.vue')
const MediaDetailView = () => import('../views/MediaDetailView.vue')
const StatsView = () => import('../views/StatsView.vue')
const ImportExportView = () => import('../views/ImportExportView.vue')

const routes = [
  { path: '/', name: 'catalog', component: CatalogView },
  { path: '/media/new', name: 'media-create', component: MediaDetailView },
  { path: '/media/:id', name: 'media-detail', component: MediaDetailView },
  { path: '/stats', name: 'stats', component: StatsView },
  { path: '/import-export', name: 'import-export', component: ImportExportView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
