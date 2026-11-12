const accessTokenKey = 'industrialops.accessToken'

export function createAuthSession({ api, storage }) {
  return {
    async login({ username, password }) {
      const response = await api.request('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      api.setToken(response.access_token)
      storage.setItem(accessTokenKey, response.access_token)
      return response.user
    },

    async restore() {
      const token = storage.getItem(accessTokenKey)
      if (!token) {
        return null
      }

      api.setToken(token)
      try {
        return await api.request('/api/auth/me')
      } catch (error) {
        if (error.status === 401) {
          api.setToken(null)
          storage.removeItem(accessTokenKey)
          return null
        }
        throw error
      }
    },
  }
}
