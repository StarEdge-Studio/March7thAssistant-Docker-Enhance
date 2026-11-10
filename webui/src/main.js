import { createApp, defineComponent, h } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import './style.css'
import { applyTheme, fetchCurrentUser, loadAuthConfig, store } from './state.js'

// Simple (经典轻量简洁版) 视图
import SimpleLoginView from './views/LoginView.vue'
import SimpleUnauthorizedView from './views/UnauthorizedView.vue'
import SimpleDashboardView from './views/DashboardView.vue'
import SimpleAccountsView from './views/AccountsView.vue'
import SimpleTasksView from './views/TasksView.vue'
import SimpleSettingsView from './views/SettingsView.vue'

// M3E (Material 3 Expressive) 视图
import M3ELoginView from './views/m3e/LoginView.vue'
import M3EUnauthorizedView from './views/m3e/UnauthorizedView.vue'
import M3EDashboardView from './views/m3e/DashboardView.vue'
import M3EAccountsView from './views/m3e/AccountsView.vue'
import M3ETasksView from './views/m3e/TasksView.vue'
import M3ESettingsView from './views/m3e/SettingsView.vue'

applyTheme()

function createThemedRouteComponent(M3EComp, SimpleComp) {
  return defineComponent({
    setup() {
      return () => h(store.uiTheme === 'simple' ? SimpleComp : M3EComp)
    },
  })
}

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    name: 'login',
    component: createThemedRouteComponent(M3ELoginView, SimpleLoginView),
    meta: { public: true },
  },
  {
    path: '/unauthorized',
    name: 'unauthorized',
    component: createThemedRouteComponent(M3EUnauthorizedView, SimpleUnauthorizedView),
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: createThemedRouteComponent(M3EDashboardView, SimpleDashboardView),
  },
  {
    path: '/accounts',
    name: 'accounts',
    component: createThemedRouteComponent(M3EAccountsView, SimpleAccountsView),
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: createThemedRouteComponent(M3ETasksView, SimpleTasksView),
  },
  {
    path: '/settings',
    name: 'settings',
    component: createThemedRouteComponent(M3ESettingsView, SimpleSettingsView),
    meta: { adminOnly: true },
  },
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
