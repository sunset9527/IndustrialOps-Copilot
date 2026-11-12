import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import LoginView from '../src/views/LoginView.vue'

describe('LoginView', () => {
  it('submits credentials and navigates to the asset overview after a successful login', async () => {
    const login = vi.fn().mockResolvedValue({ username: 'operator', role: 'user' })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: LoginView },
        { path: '/register', component: { template: '<div />' } },
        { path: '/assets', name: 'assets', component: { template: '<div>assets</div>' } },
      ],
    })
    await router.push('/')
    await router.isReady()

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router],
        provide: { auth: { login } },
      },
    })

    await wrapper.get('input[name="username"]').setValue('operator')
    await wrapper.get('input[name="password"]').setValue('a long enough password')
    await wrapper.get('form').trigger('submit')

    expect(login).toHaveBeenCalledWith({ username: 'operator', password: 'a long enough password' })
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('assets'))
  })

  it('keeps entered credentials and shows a recoverable message when login is rejected', async () => {
    const login = vi.fn().mockRejectedValue({ code: 'invalid_credentials', status: 401 })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: LoginView }, { path: '/register', component: { template: '<div />' } }],
    })
    await router.push('/')
    await router.isReady()
    const wrapper = mount(LoginView, {
      global: { plugins: [router], provide: { auth: { login } } },
    })

    await wrapper.get('input[name="username"]').setValue('operator')
    await wrapper.get('input[name="password"]').setValue('wrong password')
    await wrapper.get('form').trigger('submit')

    await vi.waitFor(() => expect(wrapper.get('[role="alert"]').text()).toContain('用户名或密码不正确'))
    expect(wrapper.get('input[name="username"]').element.value).toBe('operator')
    expect(wrapper.get('input[name="password"]').element.value).toBe('wrong password')
  })
})
