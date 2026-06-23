import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'

const root = fileURLToPath(new URL('..', import.meta.url))

function figmaAssetResolver() {
  return {
    name: 'figma-asset-resolver',
    resolveId(id) {
      if (id.startsWith('figma:asset/')) {
        const filename = id.replace('figma:asset/', '')
        return fileURLToPath(new URL(`../src/assets/${filename}`, import.meta.url))
      }
      return null
    },
  }
}

export function createViteConfig() {
  return {
    root,
    configFile: false,
    plugins: [figmaAssetResolver(), vue(), tailwindcss()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('../src', import.meta.url)),
      },
    },
    assetsInclude: ['**/*.svg', '**/*.csv'],
    optimizeDeps: {
      noDiscovery: true,
      include: [],
    },
  }
}
