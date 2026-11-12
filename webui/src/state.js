import { reactive } from 'vue'

export const store = reactive({
  // 前端设计语言主题: 'm3e' (Material 3 Expressive) | 'simple' (经典轻量简洁版)
  uiTheme: (typeof window !== 'undefined' && window.__M7A_UI_THEME__ === 'simple') ? 'simple' : 'm3e',

  // 认证配置与当前会话
  authConfigLoaded: false,
  authMode: 'token', // 'token' | 'oidc'
  authBrand: 'SSO',
  token: localStorage.getItem('m7a_session_token') || '',
  role: '', // 'admin' | 'user' | 'unauthorized' | ''
  username: '',
  displayName: '',
  avatar: '',
  accountIds: [],
  primaryAccountId: null,

  // 主题模式
  darkMode: localStorage.getItem('m7a_theme') === 'dark' ||
    (!localStorage.getItem('m7a_theme') && window.matchMedia('(prefers-color-scheme: dark)').matches),

  // 调度器与账号全局数据
  scheduler: {
    is_running: false,
    current_account_id: null,
    current_account_name: null,
    current_run_id: null,
    current_log_file: null,
    stop_requested: false,
    internet_retry_info: null,
    settings: {
      daily_run_enabled: false,
      daily_run_time: '04:00',
      check_internet: false,
      check_internet_Wait: 60,
      check_internet_MaxRetries: 3,
      allow_user_manual_run: true,
      debug_mode: false,
    },
  },
  accounts: [],
  history: [],
  historyLoaded: false,

  // 轻量全局 Toast 通知
  toasts: [],

  // 全局确认弹窗
  confirmDialog: {
    visible: false,
    title: '',
    message: '',
    confirmText: '确定',
    cancelText: '取消',
    danger: false,
    resolve: null,
  },
})

export function applyTheme() {
  if (store.darkMode) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('m7a_theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('m7a_theme', 'light')
  }
}

export function toggleTheme() {
  store.darkMode = !store.darkMode
  applyTheme()
}

export function canManualRun() {
  return store.role === 'admin' || store.scheduler.settings?.allow_user_manual_run !== false
}

/**
 * 复制文本到剪贴板。
 * 优先使用 Clipboard API；在非 HTTPS（如通过局域网 IP 直接访问）环境下回退到 execCommand。
 */
export async function copyText(text) {
  if (!text) return false
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    // fall through to legacy fallback
  }
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.top = '-9999px'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch {
    return false
  }
}

export function buildInviteUrl(code) {
  return `${window.location.origin}${window.location.pathname}#/invite/${code}`
}

let toastSeq = 0
export function notify(message, type = 'info', duration = 3200) {
  const id = ++toastSeq
  store.toasts.push({ id, message, type })
  if (duration > 0) {
    setTimeout(() => {
      const idx = store.toasts.findIndex((t) => t.id === id)
      if (idx !== -1) store.toasts.splice(idx, 1)
    }, duration)
  }
}

export function confirmModal({
  title = '确认操作',
  message = '',
  confirmText = '确定',
  cancelText = '取消',
  danger = false,
}) {
  return new Promise((resolve) => {
    store.confirmDialog = {
      visible: true,
      title,
      message,
      confirmText,
      cancelText,
      danger,
      resolve,
    }
  })
}

export function resolveConfirmModal(accepted) {
  const fn = store.confirmDialog.resolve
  store.confirmDialog.visible = false
  store.confirmDialog.resolve = null
  if (fn) fn(accepted)
}

export function setSession(authData) {
  if (authData.token) {
    store.token = authData.token
    localStorage.setItem('m7a_session_token', authData.token)
  }
  if (authData.mode) store.authMode = authData.mode
  if (authData.brand !== undefined) store.authBrand = authData.brand || 'SSO'
  store.role = authData.role || ''
  store.username = authData.username || ''
  store.displayName = authData.display_name || ''
  store.avatar = authData.avatar || ''
  store.accountIds = authData.account_ids || []
  store.primaryAccountId = authData.account_id || (store.accountIds[0] || null)
}

export function clearSession() {
  store.token = ''
  store.role = ''
  store.username = ''
  store.displayName = ''
  store.avatar = ''
  store.accountIds = []
  store.primaryAccountId = null
  store.history = []
  store.historyLoaded = false
  localStorage.removeItem('m7a_session_token')
}

export async function apiFetch(url, options = {}) {
  const headers = {
    ...(options.headers || {}),
  }
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  if (store.token) {
    headers['Authorization'] = `Bearer ${store.token}`
  }

  const resp = await fetch(url, {
    ...options,
    headers,
  })

  if (resp.status === 401 && !url.startsWith('/api/auth/')) {
    clearSession()
    window.location.hash = '#/login'
    throw new Error('登录已过期，请重新登录')
  }

  let data = null
  const contentType = resp.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    data = await resp.json()
  } else {
    const text = await resp.text()
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }

  if (!resp.ok) {
    const err = new Error(data?.detail || data?.message || `请求失败 (${resp.status})`)
    err.status = resp.status
    err.data = data
    throw err
  }

  return data
}

export async function loadAuthConfig() {
  try {
    const cfg = await apiFetch('/api/auth/config')
    store.authMode = cfg.mode || 'token'
    store.authBrand = cfg.brand || 'SSO'
    if (cfg.ui_theme) {
      store.uiTheme = cfg.ui_theme === 'simple' ? 'simple' : 'm3e'
    }
    store.authConfigLoaded = true
    return cfg
  } catch (e) {
    store.authConfigLoaded = true
    return { mode: 'token', brand: '', ui_theme: store.uiTheme }
  }
}

export async function fetchCurrentUser() {
  if (!store.token) return null
  try {
    const me = await apiFetch('/api/auth/me')
    setSession(me)
    return me
  } catch (e) {
    clearSession()
    return null
  }
}

export async function refreshStatus() {
  if (!store.token || !store.role || store.role === 'unauthorized') return null
  try {
    const data = await apiFetch('/api/status')
    if (data.ui_theme) {
      store.uiTheme = data.ui_theme === 'simple' ? 'simple' : 'm3e'
    }
    if (data.auth) {
      setSession(data.auth)
    }
    if (data.scheduler) {
      store.scheduler = data.scheduler
    }
    if (Array.isArray(data.accounts)) {
      store.accounts = data.accounts
    }
    // 状态拉取成功后，若历史尚未加载过，静默在后台预热运行历史，避免路由切换时出现等待延迟
    if (!store.historyLoaded) {
      fetchHistory().catch(() => {})
    }
    return data
  } catch (e) {
    if (e.status === 403 && store.authMode === 'oidc') {
      store.role = 'unauthorized'
    }
    return null
  }
}

export async function fetchHistory() {
  if (!store.token || !store.role || store.role === 'unauthorized') return store.history
  try {
    const list = await apiFetch('/api/history')
    store.history = Array.isArray(list) ? list : []
    store.historyLoaded = true
    return store.history
  } catch {
    return store.history
  }
}
