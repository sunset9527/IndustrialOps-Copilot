import { createRouter, createWebHistory } from 'vue-router'

import LoginView from './views/LoginView.vue'
import AssetOverviewView from './views/AssetOverviewView.vue'
import DiagnosisView from './views/DiagnosisView.vue'
import WorkOrdersView from './views/WorkOrdersView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/', redirect: '/assets' },
  { path: '/assets', name: 'assets', component: AssetOverviewView, meta: { requiresAuth: true } },
  { path: '/diagnosis/:assetId', name: 'diagnosis', component: DiagnosisView, meta: { requiresAuth: true } },
  { path: '/work-orders', name: 'work-orders', component: WorkOrdersView, meta: { requiresAuth: true } },
  { path: '/work-orders/:workOrderId', name: 'work-order-detail', component: WorkOrdersView, meta: { requiresAuth: true } },
]

export function createIndustrialOpsRouter({
  isAuthenticated,
  history = createWebHistory(),
} = {}) {
  const router = createRouter({ history, routes })

  router.beforeEach((to) => {
    if (to.meta.requiresAuth && !isAuthenticated?.()) {
      return { name: 'login' }
    }
    if (to.name === 'login' && isAuthenticated?.()) {
      return { name: 'assets' }
    }
    return true
  })

  return router
}
