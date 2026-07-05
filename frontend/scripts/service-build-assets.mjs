import { copyFile, mkdir, readdir, rm } from 'node:fs/promises'
import { join } from 'node:path'
import { fileURLToPath, URL } from 'node:url'

const frontendRoot = fileURLToPath(new URL('..', import.meta.url))
const keepCardImageFiles = new Set(['magpie-face.png', 'magpie-face2.png'])

export const normalizeAppChannel = (value) => (
  String(value || 'demo').trim().toLowerCase() === 'service' ? 'service' : 'demo'
)

export async function removeServiceCardImages(appChannel = process.env.VITE_APP_CHANNEL) {
  if (normalizeAppChannel(appChannel) !== 'service') return

  const publicCardImageDir = join(frontendRoot, 'public', 'card-images')
  const distCardImageDir = join(frontendRoot, 'dist', 'card-images')
  const entries = await readdir(distCardImageDir).catch(() => [])

  await Promise.all(entries.map(async (entry) => {
    if (keepCardImageFiles.has(entry)) return
    await rm(join(distCardImageDir, entry), { force: true, recursive: true })
  }))

  await mkdir(distCardImageDir, { recursive: true })
  await Promise.all([...keepCardImageFiles].map((filename) => (
    copyFile(join(publicCardImageDir, filename), join(distCardImageDir, filename))
  )))
}
