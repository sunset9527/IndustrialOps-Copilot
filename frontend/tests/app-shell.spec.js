import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import App from '../src/App.vue'

describe('App shell', () => {
  it('shows the current role and returns to login after logout', async () => {
    const logout = vi.fn()
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/login', name: 'login', component: { template: '<p>login</p>' }, meta: { public: true } },
        { path: '/assets', name: 'assets', component: { template: '<p>assets</p>' } },
        { path: '/work-orders', name: 'work-orders', component: { template: '<p>work orders</p>' } },
      ],
    })
    await router.push('/assets')
    await router.isReady()
    const wrapper = mount(App, {
      global: {
        plugins: [router],
        provide: { auth: { user: ref({ username: 'operator', role: 'user' }), logout } },
      },
    })

    expect(wrapper.text()).toContain('operator · user')
    await wrapper.get('button[aria-label="退出登录"]').trigger('click')

    expect(logout).toHaveBeenCalledOnce()
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('login'))
  })
})
