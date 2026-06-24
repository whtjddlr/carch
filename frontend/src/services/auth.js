import { API_BASE_URL, DEV_AUTO_LOGIN_ENABLED, api, loginAsDevAdmin, loginWithEmail, logoutAuth, signupWithEmail, fetchCurrentUser } from './api'

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

export const isAuthenticated = () => Boolean(getAuthToken())
export const isDevAutoLoginEnabled = () => DEV_AUTO_LOGIN_ENABLED

let devAutoLoginPromise = null

export const setAuthSession = ({ token, user }) => {
  if (token) localStorage.setItem(AUTH_TOKEN_KEY, token)
  if (user) localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
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
  if (!token) {
    clearAuthSession()
    hydrateAuthHeader()
    throw new Error('Missing auth token')
  }

  localStorage.setItem(AUTH_TOKEN_KEY, token)
  hydrateAuthHeader()
  try {
    const current = await fetchCurrentUser()
    setAuthSession({ token, user: current.user })
    return current.user
  } catch (error) {
    clearAuthSession()
    hydrateAuthHeader()
    throw error
  }
}

export const emailLogin = async (payload) => {
  const result = await loginWithEmail(payload)
  if (!result?.token) throw new Error('Missing auth token')
  setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const emailSignup = async (payload) => {
  const result = await signupWithEmail(payload)
  if (!result?.token) throw new Error('Missing auth token')
  setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const devAdminLogin = async () => {
  const result = await loginAsDevAdmin()
  if (!result?.token) throw new Error('Missing auth token')
  setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const ensureDevAutoLogin = async () => {
  if (isAuthenticated()) return true
  if (!DEV_AUTO_LOGIN_ENABLED) return false
  if (!devAutoLoginPromise) {
    devAutoLoginPromise = devAdminLogin()
      .then(() => true)
      .catch((error) => {
        console.warn('개발용 자동 로그인에 실패했습니다.', error)
        return false
      })
      .finally(() => {
        devAutoLoginPromise = null
      })
  }
  return devAutoLoginPromise
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
