const accessTokenKey = 'industrialops.accessToken'

export function createAuthSession({ api, storage }) {
  function adopt(response) {
    api.setToken(response.access_token)
    storage.setItem(accessTokenKey, response.access_token)
    return response.user
  }

  return {
    async login({ username, password }) {
      const response = await api.request('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      return adopt(response)
    },

    async register({ username, email, password }) {
      const response = await api.request('/api/auth/register', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, email, password }),
      })
      return adopt(response)
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
