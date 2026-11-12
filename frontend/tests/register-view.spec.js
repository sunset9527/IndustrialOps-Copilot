import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import RegisterView from '../src/views/RegisterView.vue'

describe('RegisterView', () => {
  it('shows the safe server reason when registration is rejected', async () => {
    const register = vi.fn().mockRejectedValue({
      code: 'registration_failed',
      message: 'Password must contain at least 10 characters',
    })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/register', component: RegisterView },
        { path: '/login', component: { template: '<div />' } },
        { path: '/assets', name: 'assets', component: { template: '<div />' } },
      ],
    })
    await router.push('/register')
    await router.isReady()
    const wrapper = mount(RegisterView, {
      global: { plugins: [router], provide: { auth: { register } } },
    })

    await wrapper.get('input[name="username"]').setValue('operator-2026')
    await wrapper.get('input[name="email"]').setValue('operator-2026@example.com')
    await wrapper.get('input[name="password"]').setValue('123456789')
    await wrapper.get('form').trigger('submit')

    await vi.waitFor(() => expect(wrapper.get('[role="alert"]').text()).toContain('Password must contain at least 10 characters'))
  })
})
