import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import './style.css'
import { applyTheme, fetchCurrentUser, loadAuthConfig, store } from './state.js'

import LoginView from './views/LoginView.vue'
import UnauthorizedView from './views/UnauthorizedView.vue'
import DashboardView from './views/DashboardView.vue'
import AccountsView from './views/AccountsView.vue'
import TasksView from './views/TasksView.vue'
import SettingsView from './views/SettingsView.vue'

applyTheme()

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/unauthorized', name: 'unauthorized', component: UnauthorizedView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
  { path: '/accounts', name: 'accounts', component: AccountsView },
  { path: '/tasks', name: 'tasks', component: TasksView },
  { path: '/settings', name: 'settings', component: SettingsView, meta: { adminOnly: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (!store.authConfigLoaded) {
    await loadAuthConfig()
  }

  // 检查 URL Search 参数中是否有 OIDC 回调的 code & state
  const urlParams = new URLSearchParams(window.location.search)
  const hasOidcCallback = urlParams.has('code') && urlParams.has('state')
  if (hasOidcCallback && to.name !== 'login') {
    return next({ name: 'login' })
  }

  if (store.token && !store.role) {
    await fetchCurrentUser()
  }

  if (to.meta.public) {
    if (store.token && store.role && !hasOidcCallback) {
      if (store.role === 'unauthorized') return next({ name: 'unauthorized' })
      return next({ name: 'dashboard' })
    }
    return next()
  }

  if (!store.token || !store.role) {
    return next({ name: 'login' })
  }

  if (store.role === 'unauthorized' && to.name !== 'unauthorized') {
    return next({ name: 'unauthorized' })
  }

  if (store.role !== 'unauthorized' && to.name === 'unauthorized') {
    return next({ name: 'dashboard' })
  }

  if (to.meta.adminOnly && store.role !== 'admin') {
    return next({ name: 'dashboard' })
  }

  next()
})

const app = createApp(App)
app.use(router)
app.mount('#app')
