import { createApp } from 'vue'
import 'bootstrap/dist/css/bootstrap.min.css'
import './styles/index.css'
import './styles/app.css'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#root')
