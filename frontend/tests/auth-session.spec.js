import { describe, expect, it } from 'vitest'

import { createApiClient } from '../src/api/client.js'
import { createAuthSession } from '../src/auth/session.js'

describe('browser authentication session', () => {
  it('serializes login credentials as JSON and persists only the issued token in session storage', async () => {
    const recorded = []
    const storage = new Map()
    const api = createApiClient({
      fetchImpl: async (url, options) => {
        recorded.push({ url, options })
        return Response.json({
          access_token: 'opaque-issued-token',
          token_type: 'bearer',
          expires_at: '2026-11-12T10:00:00Z',
          user: { username: 'operator', role: 'user' },
        })
      },
    })
    const session = createAuthSession({
      api,
      storage: {
        getItem: (key) => storage.get(key) ?? null,
        setItem: (key, value) => storage.set(key, value),
        removeItem: (key) => storage.delete(key),
      },
    })

    const user = await session.login({ username: 'operator', password: 'a long enough password' })

    expect(recorded).toHaveLength(1)
    expect(recorded[0].url).toBe('http://localhost:8100/api/auth/login')
    expect(recorded[0].options).toMatchObject({
      method: 'POST',
      body: JSON.stringify({ username: 'operator', password: 'a long enough password' }),
    })
    expect(new Headers(recorded[0].options.headers).get('Content-Type')).toBe('application/json')
    expect(user).toEqual({ username: 'operator', role: 'user' })
    expect(storage.get('industrialops.accessToken')).toBe('opaque-issued-token')
    expect(storage.has('industrialops.user')).toBe(false)
  })

  it('clears a persisted token when session restoration is rejected with 401', async () => {
    const authorization = []
    const storage = new Map([['industrialops.accessToken', 'expired-token']])
    const api = createApiClient({
      fetchImpl: async (_, { headers }) => {
        authorization.push(headers.get('Authorization'))
        return authorization.length === 1
          ? Response.json({ error: { code: 'unauthorized', message: 'Session expired' } }, { status: 401 })
          : Response.json({ status: 'ok' })
      },
    })
    const session = createAuthSession({
      api,
      storage: {
        getItem: (key) => storage.get(key) ?? null,
        setItem: (key, value) => storage.set(key, value),
        removeItem: (key) => storage.delete(key),
      },
    })

    await expect(session.restore()).resolves.toBeNull()
    await api.request('/health')

    expect(storage.has('industrialops.accessToken')).toBe(false)
    expect(authorization).toEqual(['Bearer expired-token', null])
  })
})
