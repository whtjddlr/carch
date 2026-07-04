const toPositiveNumber = (value, fallback) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export const normalizeBaseUrl = (value) => String(value || '').trim().replace(/\/+$/, '')

export const normalizeAppChannel = (value) => (
  String(value || 'demo').trim().toLowerCase() === 'service' ? 'service' : 'demo'
)

export const envList = (value, fallback = []) => {
  const items = String(value || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean)
  return items.length ? items : fallback
}

export const runtimeHostname = typeof window === 'undefined' ? '' : window.location.hostname.toLowerCase()
export const demoHostnames = envList(import.meta.env.VITE_DEMO_HOSTS, ['carch-demo.vercel.app'])
export const serviceHostnames = envList(import.meta.env.VITE_SERVICE_HOSTS, ['carch.vercel.app', 'carch-service.vercel.app'])

export const resolveAppChannel = (hostname = runtimeHostname) => {
  const normalizedHostname = String(hostname || '').toLowerCase()
  if (normalizedHostname && demoHostnames.includes(normalizedHostname)) return 'demo'
  if (normalizedHostname && serviceHostnames.includes(normalizedHostname)) return 'service'
  return normalizeAppChannel(import.meta.env.VITE_APP_CHANNEL)
}

export const APP_CHANNEL = resolveAppChannel()
export const IS_DEMO_CHANNEL = APP_CHANNEL === 'demo'
export const IS_SERVICE_CHANNEL = APP_CHANNEL === 'service'
export const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000'),
)
export const DEFAULT_API_TIMEOUT_MS = toPositiveNumber(import.meta.env.VITE_API_TIMEOUT_MS, 8000)
export const AI_REQUEST_TIMEOUT_MS = toPositiveNumber(import.meta.env.VITE_AI_TIMEOUT_MS, 100000)
export const USE_MOCK_API = IS_DEMO_CHANNEL
  && ['true', '1', 'yes'].includes(String(import.meta.env.VITE_USE_MOCK_API || '').toLowerCase())
export const DEV_AUTO_LOGIN_ENABLED = IS_DEMO_CHANNEL
  && import.meta.env.DEV
  && !['false', '0', 'no'].includes(String(import.meta.env.VITE_DEV_AUTO_LOGIN || 'true').toLowerCase())
