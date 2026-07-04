import { Capacitor } from '@capacitor/core'
import { SplashScreen } from '@capacitor/splash-screen'
import { StatusBar, Style } from '@capacitor/status-bar'

export const prepareNativeShell = async () => {
  if (!Capacitor.isNativePlatform()) return

  await Promise.allSettled([
    StatusBar.setStyle({ style: Style.Light }),
    StatusBar.setBackgroundColor({ color: '#F3F6F8' }),
    StatusBar.setOverlaysWebView({ overlay: false }),
  ])

  await SplashScreen.hide().catch(() => {})
}
