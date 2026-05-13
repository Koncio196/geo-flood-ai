import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Vue3Lottie from 'vue3-lottie' // <-- DODANE
import App from './App.vue'

const app = createApp(App)

app.use(createPinia())
app.use(Vue3Lottie) // <-- DODANE

app.mount('#app')
