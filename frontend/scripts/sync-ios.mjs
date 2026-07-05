import { spawn } from 'node:child_process'
import { build } from 'vite'
import { normalizeAppChannel, removeServiceCardImages } from './service-build-assets.mjs'
import { createViteConfig } from './vite-config.mjs'

const normalizeBaseUrl = (value) => String(value || '').trim().replace(/\/+$/, '')

const appChannel = normalizeAppChannel(process.env.VITE_APP_CHANNEL || 'service')
const fallbackApiBaseUrl = 'https://carch-api.vercel.app'
const iosApiBaseUrl =
  normalizeBaseUrl(process.env.VITE_IOS_API_BASE_URL || process.env.VITE_API_BASE_URL)

if (appChannel === 'service') {
  if (!iosApiBaseUrl) {
    throw new Error('VITE_IOS_API_BASE_URL is required for service iOS builds.')
  }
}

process.env.VITE_API_BASE_URL = iosApiBaseUrl || fallbackApiBaseUrl
process.env.VITE_USE_MOCK_API = process.env.VITE_USE_MOCK_API || 'false'
process.env.VITE_APP_CHANNEL = appChannel

await build(createViteConfig())
await removeServiceCardImages(appChannel)

const command = process.platform === 'win32' ? 'npx.cmd' : 'npx'
const child = spawn(command, ['cap', 'sync', 'ios'], { stdio: 'inherit' })

const code = await new Promise((resolve) => {
  child.on('close', resolve)
})

if (code !== 0) {
  process.exit(code || 1)
}
