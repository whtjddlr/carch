const DEFAULT_BACKEND_URL = 'https://carch-api.vercel.app'

const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'content-encoding',
  'content-length',
  'host',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
])

const backendBaseUrl = () => (process.env.BACKEND_URL || DEFAULT_BACKEND_URL).replace(/\/+$/, '')

const readPath = (req) => {
  const rawPath = req.query?.path
  if (Array.isArray(rawPath)) return rawPath.join('/')
  if (rawPath) return rawPath

  if (req.url) {
    const incoming = new URL(req.url, 'http://localhost')
    const pathFromQuery = incoming.searchParams.get('path')
    if (pathFromQuery) return pathFromQuery
    return incoming.pathname.replace(/^\/api\/proxy\/?/, '').replace(/^\/api\/?/, '')
  }

  return ''
}

const appendQuery = (url, query) => {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query || {})) {
    if (key === 'path') continue
    if (Array.isArray(value)) {
      value.forEach((item) => params.append(key, item))
    } else if (value !== undefined) {
      params.append(key, value)
    }
  }
  const queryString = params.toString()
  return queryString ? `${url}?${queryString}` : url
}

const targetUrl = (req) => {
  const path = readPath(req).replace(/^\/+/, '')
  return appendQuery(`${backendBaseUrl()}/api/${path}`, req.query)
}

const requestHeaders = (headers = {}, hasJsonBody = false) => {
  const forwarded = new Headers()
  for (const [key, value] of Object.entries(headers)) {
    const normalizedKey = key.toLowerCase()
    if (HOP_BY_HOP_HEADERS.has(normalizedKey)) continue
    if (value === undefined) continue
    forwarded.set(key, Array.isArray(value) ? value.join(',') : value)
  }
  if (hasJsonBody && !forwarded.has('content-type')) {
    forwarded.set('content-type', 'application/json')
  }
  return forwarded
}

const requestBody = (req) => {
  if (req.method === 'GET' || req.method === 'HEAD') return undefined
  if (req.body === undefined || req.body === null) return undefined
  if (Buffer.isBuffer(req.body) || typeof req.body === 'string') return req.body
  return JSON.stringify(req.body)
}

const responseHeaders = (headers, res) => {
  headers.forEach((value, key) => {
    if (HOP_BY_HOP_HEADERS.has(key.toLowerCase())) return
    res.setHeader(key, value)
  })
}

export default async function handler(req, res) {
  const backendUrl = targetUrl(req)
  const body = requestBody(req)

  try {
    const upstream = await fetch(backendUrl, {
      method: req.method,
      headers: requestHeaders(req.headers, body && typeof req.body === 'object' && !Buffer.isBuffer(req.body)),
      body,
      redirect: 'manual',
    })

    responseHeaders(upstream.headers, res)
    res.status(upstream.status)
    res.send(Buffer.from(await upstream.arrayBuffer()))
  } catch (error) {
    res.status(502).json({
      detail: 'Backend proxy request failed.',
      backendUrl: backendBaseUrl(),
      message: error instanceof Error ? error.message : String(error),
    })
  }
}
