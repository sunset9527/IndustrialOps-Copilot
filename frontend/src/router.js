import { createRouter, createWebHistory } from 'vue-router'

import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import AssetOverviewView from './views/AssetOverviewView.vue'
import DiagnosisView from './views/DiagnosisView.vue'
import WorkOrdersView from './views/WorkOrdersView.vue'
import WorkOrderDetailView from './views/WorkOrderDetailView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { public: true } },
  { path: '/', redirect: '/assets' },
  { path: '/assets', name: 'assets', component: AssetOverviewView, meta: { requiresAuth: true } },
  { path: '/diagnosis/:assetId', name: 'diagnosis', component: DiagnosisView, meta: { requiresAuth: true } },
  { path: '/work-orders', name: 'work-orders', component: WorkOrdersView, meta: { requiresAuth: true } },
  { path: '/work-orders/:workOrderId', name: 'work-order-detail', component: WorkOrderDetailView, meta: { requiresAuth: true } },
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
