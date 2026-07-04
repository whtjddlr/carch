import { Capacitor } from '@capacitor/core'
import { KeychainAccess, SecureStorage } from '@aparajita/capacitor-secure-storage'

const KEY_PREFIX = 'carch.'

let nativeStorageSetup = null

export const isNativeRuntime = () => Capacitor.isNativePlatform()

const browserStorage = () => {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

const setupNativeStorage = async () => {
  if (!isNativeRuntime()) return
  if (!nativeStorageSetup) {
    nativeStorageSetup = Promise.all([
      SecureStorage.setKeyPrefix(KEY_PREFIX),
      SecureStorage.setSynchronize(false),
      SecureStorage.setDefaultKeychainAccess(KeychainAccess.whenUnlockedThisDeviceOnly),
    ]).then(() => undefined)
  }
  await nativeStorageSetup
}

export const getSecureItem = async (key) => {
  if (!isNativeRuntime()) {
    return browserStorage()?.getItem(key) || ''
  }
  await setupNativeStorage()
  return SecureStorage.getItem(key)
}

export const setSecureItem = async (key, value) => {
  const normalizedValue = String(value ?? '')
  if (!isNativeRuntime()) {
    browserStorage()?.setItem(key, normalizedValue)
    return
  }
  await setupNativeStorage()
  await SecureStorage.setItem(key, normalizedValue)
}

export const removeSecureItem = async (key) => {
  if (!isNativeRuntime()) {
    browserStorage()?.removeItem(key)
    return
  }
  await setupNativeStorage()
  await SecureStorage.removeItem(key)
}

export const removeBrowserOnlyItem = (key) => {
  browserStorage()?.removeItem(key)
}
