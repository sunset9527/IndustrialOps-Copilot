import { createApp, ref } from 'vue'

import App from './App.vue'
import { createApiClient } from './api/client.js'
import { createAuthSession } from './auth/session.js'
import { createIndustrialOpsRouter } from './router.js'

async function bootstrap() {
  const api = createApiClient({ baseUrl: import.meta.env.VITE_INDUSTRIALOPS_API_BASE_URL || '' })
  const session = createAuthSession({ api, storage: window.sessionStorage })
  const user = ref(await session.restore())
  const auth = {
    user,
    isAuthenticated: () => user.value !== null,
    async login(credentials) { user.value = await session.login(credentials); return user.value },
  }
  const router = createIndustrialOpsRouter({ isAuthenticated: auth.isAuthenticated })
  const app = createApp(App)
  app.provide('api', api)
  app.provide('auth', auth)
  app.use(router)
  app.mount('#app')
}

bootstrap()
