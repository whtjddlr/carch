import { createServer } from 'vite'
import { createViteConfig } from './vite-config.mjs'

function readArg(name, fallback) {
  const index = process.argv.indexOf(name)
  if (index >= 0 && process.argv[index + 1]) return process.argv[index + 1]
  const inline = process.argv.find((arg) => arg.startsWith(`${name}=`))
  return inline ? inline.split('=').slice(1).join('=') : fallback
}

const host = readArg('--host', '127.0.0.1')
const port = Number(readArg('--port', '5174'))
const mode = readArg('--mode', 'development')

if (mode === 'mock') {
  process.env.VITE_USE_MOCK_API = process.env.VITE_USE_MOCK_API || 'true'
}

const server = await createServer({
  ...createViteConfig(),
  mode,
  server: {
    host,
    port,
    strictPort: false,
  },
})

await server.listen()
server.printUrls()
