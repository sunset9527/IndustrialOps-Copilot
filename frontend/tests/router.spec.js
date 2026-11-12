import { describe, expect, it } from 'vitest'

import { createIndustrialOpsRouter } from '../src/router.js'

describe('IndustrialOps route access', () => {
  it('redirects an anonymous user away from the protected asset overview', async () => {
    const router = createIndustrialOpsRouter({ isAuthenticated: () => false })

    await router.push('/assets')
    await router.isReady()

    expect(router.currentRoute.value.fullPath).toBe('/login')
  })

  it('redirects an authenticated user away from login to the asset overview', async () => {
    const router = createIndustrialOpsRouter({ isAuthenticated: () => true })

    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.fullPath).toBe('/assets')
  })
})
