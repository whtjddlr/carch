import { createApp } from 'vue'
import 'bootstrap/dist/css/bootstrap.min.css'
import './styles/index.css'
import './styles/app.css'
import App from './App.vue'
import router from './router'
import { initAuthSession } from './services/auth'
import { prepareNativeShell } from './services/nativeShell'

async function bootstrap() {
  await initAuthSession()
  createApp(App).use(router).mount('#root')
  await prepareNativeShell()
}

bootstrap().catch((error) => {
  console.error('CARCH 앱 시작에 실패했습니다.', error)
  createApp(App).use(router).mount('#root')
})
