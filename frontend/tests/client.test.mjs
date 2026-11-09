import assert from 'node:assert/strict'
import test from 'node:test'

import { ApiError, createApiClient } from '../src/api/client.js'

test('uses the local IndustrialOps API by default', async () => {
  const client = createApiClient({
    fetchImpl: async (url) => {
      assert.equal(url, 'http://localhost:8100/health')
      return Response.json({ status: 'ok' })
    },
  })

  assert.deepEqual(await client.request('/health'), { status: 'ok' })
})

test('preserves the path prefix of a configured API base', async () => {
  const client = createApiClient({
    baseUrl: 'https://industrialops.example/api/',
    fetchImpl: async (url) => Response.json({ url }),
  })

  assert.deepEqual(await client.request('/health'), {
    url: 'https://industrialops.example/api/health',
  })
})

test('preserves the API error code, message and HTTP status', async () => {
  const client = createApiClient({
    fetchImpl: async () => Response.json({
      error: { code: 'not_found', message: 'Resource not found' },
    }, { status: 404 }),
  })

  await assert.rejects(client.request('/missing'), {
    name: 'ApiError',
    code: 'not_found',
    message: 'Resource not found',
    status: 404,
  })
})

test('sends bearer authentication and clears the rejected session on 401', async () => {
  const authorization = []
  const client = createApiClient({
    fetchImpl: async (_, { headers }) => {
      authorization.push(headers.get('Authorization'))
      return authorization.length === 1
        ? Response.json({ error: { code: 'expired', message: 'Session expired' } }, { status: 401 })
        : Response.json({ status: 'ok' })
    },
  })

  client.setToken('temporary-token')
  await assert.rejects(client.request('/protected'), { code: 'expired', status: 401 })
  await client.request('/health')

  assert.deepEqual(authorization, ['Bearer temporary-token', null])
})

test('keeps a replacement session if an earlier request later returns 401', async () => {
  let rejectEarlierSession
  const client = createApiClient({
    fetchImpl: async (url, { headers }) => {
      if (url.endsWith('/protected')) {
        return new Promise((resolve) => { rejectEarlierSession = resolve })
      }
      return Response.json({ authorization: headers.get('Authorization') })
    },
  })

  client.setToken('old-token')
  const pending = client.request('/protected')
  client.setToken('new-token')
  rejectEarlierSession(new Response(null, { status: 401 }))

  await assert.rejects(pending, { code: 'unauthorized', status: 401 })
  assert.deepEqual(await client.request('/health'), { authorization: 'Bearer new-token' })
})

test('uses a safe fallback for non-JSON server errors', async () => {
  const client = createApiClient({
    fetchImpl: async () => new Response('<html>Server exception</html>', { status: 502 }),
  })

  await assert.rejects(client.request('/health'), (error) => {
    assert.ok(error instanceof ApiError)
    assert.equal(error.code, 'http_error')
    assert.equal(error.status, 502)
    assert.equal(error.message, 'Request could not be completed')
    return true
  })
})
