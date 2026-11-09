const defaultBaseUrl = import.meta.env?.VITE_INDUSTRIALOPS_API_BASE_URL || 'http://localhost:8100'

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export function createApiClient({ baseUrl = defaultBaseUrl, fetchImpl = fetch } = {}) {
  const normalizedBase = baseUrl.replace(/\/+$/, '')
  let session = null

  return {
    baseUrl: normalizedBase,

    setToken(token) {
      session = token ? { token } : null
    },

    async request(path, options = {}) {
      const requestSession = session
      const headers = new Headers(options.headers)
      if (requestSession) {
        headers.set('Authorization', `Bearer ${requestSession.token}`)
      }

      const url = `${normalizedBase}/${path.replace(/^\/+/, '')}`
      const response = await fetchImpl(url, { ...options, headers })
      if (response.ok) {
        return response.json()
      }

      const unauthorized = response.status === 401
      if (unauthorized && requestSession === session) {
        session = null
      }

      const body = await response.json().catch(() => null)
      const error = body?.error
      if (typeof error?.code === 'string' && typeof error?.message === 'string') {
        throw new ApiError(response.status, error.code, error.message)
      }

      throw new ApiError(
        response.status,
        unauthorized ? 'unauthorized' : 'http_error',
        unauthorized ? 'Authentication required' : 'Request could not be completed',
      )
    },
  }
}
