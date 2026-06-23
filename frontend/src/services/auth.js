import { API_BASE_URL, api, loginWithEmail, logoutAuth, signupWithEmail, fetchCurrentUser } from './api'

const AUTH_TOKEN_KEY = 'carch-auth-token'
const AUTH_USER_KEY = 'carch-auth-user'

export const getAuthToken = () => localStorage.getItem(AUTH_TOKEN_KEY) || ''

export const getStoredUser = () => {
  try {
    return JSON.parse(localStorage.getItem(AUTH_USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const isAuthenticated = () => Boolean(getAuthToken() || localStorage.getItem('carch-auth') === '1')

export const setAuthSession = ({ token, user }) => {
  if (token) localStorage.setItem(AUTH_TOKEN_KEY, token)
  if (user) localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
  localStorage.setItem('carch-auth', '1')
}

export const clearAuthSession = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
  localStorage.removeItem('carch-auth')
}

export const hydrateAuthHeader = () => {
  const token = getAuthToken()
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common.Authorization
  }
}

export const completeOAuthLogin = async ({ token }) => {
  setAuthSession({ token })
  hydrateAuthHeader()
  try {
    const current = await fetchCurrentUser()
    setAuthSession({ token, user: current.user })
    return current.user
  } catch {
    return getStoredUser()
  }
}

export const emailLogin = async (payload) => {
  const result = await loginWithEmail(payload)
  setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const emailSignup = async (payload) => {
  const result = await signupWithEmail(payload)
  setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const logout = async () => {
  try {
    await logoutAuth()
  } finally {
    clearAuthSession()
    hydrateAuthHeader()
  }
}

export const oauthStartUrl = (provider, next = '/cards') =>
  `${API_BASE_URL}/api/auth/oauth/${provider}/start/?next=${encodeURIComponent(next)}`

hydrateAuthHeader()
