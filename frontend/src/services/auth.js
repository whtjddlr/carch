import { API_BASE_URL, DEV_AUTO_LOGIN_ENABLED, api, deleteAccountAuth, loginAsDevAdmin, loginWithEmail, logoutAuth, signupWithEmail, fetchCurrentUser } from './api'
import { isUnauthorizedError } from './runtimePolicy'
import { getSecureItem, isNativeRuntime, removeBrowserOnlyItem, removeSecureItem, setSecureItem } from './secureStorage'

const AUTH_TOKEN_KEY = 'carch-auth-token'
const AUTH_USER_KEY = 'carch-auth-user'
const LEGACY_DEV_ADMIN_EMAIL = 'admin@carch.local'

const authSession = {
  initialized: false,
  token: '',
  user: null,
}

const parseStoredUser = (value) => {
  try {
    return JSON.parse(value || 'null')
  } catch {
    return null
  }
}

export const getAuthToken = () => authSession.token || ''

export const getStoredUser = () => authSession.user

export const isAuthenticated = () => Boolean(getAuthToken())

let devAutoLoginPromise = null
let authInitializationPromise = null
let authExpiryPromise = null
let unauthorizedHandler = null

export const setUnauthorizedHandler = (handler) => {
  unauthorizedHandler = typeof handler === 'function' ? handler : null
}

const persistAuthToken = async (token) => {
  authSession.token = token || ''
  if (token) {
    await setSecureItem(AUTH_TOKEN_KEY, token)
  } else {
    await removeSecureItem(AUTH_TOKEN_KEY)
  }
}

export const setAuthSession = async ({ token, user }) => {
  if (token) await persistAuthToken(token)
  if (user) {
    authSession.user = user
    await setSecureItem(AUTH_USER_KEY, JSON.stringify(user))
  }
}

export const clearAuthSession = async () => {
  authSession.token = ''
  authSession.user = null
  await Promise.all([
    removeSecureItem(AUTH_TOKEN_KEY),
    removeSecureItem(AUTH_USER_KEY),
  ])
  removeBrowserOnlyItem('carch-auth')
  if (isNativeRuntime()) {
    removeBrowserOnlyItem(AUTH_TOKEN_KEY)
    removeBrowserOnlyItem(AUTH_USER_KEY)
  }
}

export const clearLegacyAdminSession = async () => {
  const storedUser = getStoredUser()
  if (storedUser?.email === LEGACY_DEV_ADMIN_EMAIL) {
    await clearAuthSession()
  }
}

export const hydrateAuthHeader = () => {
  const token = getAuthToken()
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common.Authorization
  }
}

const expireAuthSession = async () => {
  if (!getAuthToken()) return
  if (!authExpiryPromise) {
    authExpiryPromise = (async () => {
      await clearAuthSession()
      hydrateAuthHeader()
      if (unauthorizedHandler) {
        Promise.resolve()
          .then(() => unauthorizedHandler())
          .catch((error) => console.warn('로그인 화면으로 이동하지 못했습니다.', error))
      }
    })().finally(() => {
      authExpiryPromise = null
    })
  }
  await authExpiryPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (isUnauthorizedError(error) && getAuthToken()) {
      await expireAuthSession()
    }
    return Promise.reject(error)
  },
)

export const initAuthSession = async () => {
  if (authSession.initialized) return
  if (!authInitializationPromise) {
    authInitializationPromise = (async () => {
      const [token, user] = await Promise.all([
        getSecureItem(AUTH_TOKEN_KEY),
        getSecureItem(AUTH_USER_KEY),
      ])
      authSession.token = token || ''
      authSession.user = parseStoredUser(user)
      await clearLegacyAdminSession()
      hydrateAuthHeader()

      if (!getAuthToken()) return
      try {
        const current = await fetchCurrentUser()
        if (!current?.authenticated) {
          await expireAuthSession()
          return
        }
        if (current.user) {
          await setAuthSession({ token: getAuthToken(), user: current.user })
        }
      } catch (error) {
        if (isUnauthorizedError(error)) {
          await expireAuthSession()
        } else {
          console.warn('저장된 로그인 상태를 확인하지 못했습니다.', error)
        }
      }
    })().finally(() => {
      authSession.initialized = true
      authInitializationPromise = null
    })
  }
  await authInitializationPromise
}

export const completeOAuthLogin = async ({ token }) => {
  if (!token) {
    await clearAuthSession()
    hydrateAuthHeader()
    throw new Error('Missing auth token')
  }

  await persistAuthToken(token)
  hydrateAuthHeader()
  try {
    const current = await fetchCurrentUser()
    await setAuthSession({ token, user: current.user })
    return current.user
  } catch (error) {
    await clearAuthSession()
    hydrateAuthHeader()
    throw error
  }
}

export const emailLogin = async (payload) => {
  const result = await loginWithEmail(payload)
  if (!result?.token) throw new Error('Missing auth token')
  await setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const emailSignup = async (payload) => {
  const result = await signupWithEmail(payload)
  if (!result?.token) throw new Error('Missing auth token')
  await setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const devAdminLogin = async () => {
  const result = await loginAsDevAdmin()
  if (!result?.token) throw new Error('Missing auth token')
  await setAuthSession(result)
  hydrateAuthHeader()
  return result
}

export const ensureDevAutoLogin = async () => {
  await initAuthSession()
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
  await initAuthSession()
  try {
    await logoutAuth()
  } finally {
    await clearAuthSession()
    hydrateAuthHeader()
  }
}

export const deleteAccount = async () => {
  await initAuthSession()
  try {
    await deleteAccountAuth()
  } finally {
    await clearAuthSession()
    hydrateAuthHeader()
  }
}

export const oauthStartUrl = (provider, next = '/cards') =>
  `${API_BASE_URL}/api/auth/oauth/${provider}/start/?${new URLSearchParams({
    next,
    ...(isNativeRuntime() ? { frontend: 'capacitor://localhost' } : {}),
  }).toString()}`
