import { build } from 'vite'
import { createViteConfig } from './vite-config.mjs'
import { removeServiceCardImages } from './service-build-assets.mjs'

await build(createViteConfig())
await removeServiceCardImages()
