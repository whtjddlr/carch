import { createServer } from 'vite'
import { createViteConfig } from './vite-config.mjs'

const args = process.argv.slice(2)
const argValue = (name, fallback = '') => {
  const index = args.indexOf(name)
  return index >= 0 ? args[index + 1] || fallback : fallback
}

const mode = argValue('--mode')
if (mode === 'mock') {
  process.env.VITE_USE_MOCK_API = 'true'
}

const host = argValue('--host', '127.0.0.1')
const port = Number(argValue('--port', mode === 'mock' ? '5175' : '5173'))

const server = await createServer(createViteConfig({
  server: {
    host,
    port,
  },
}))

await server.listen()
server.printUrls()
