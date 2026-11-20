<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-100 via-indigo-50/40 to-pink-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/30">
    <div class="w-full max-w-md bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl rounded-3xl shadow-xl border border-slate-200/80 dark:border-slate-800 p-7 sm:p-8">
      <!-- 顶部图标与标题 -->
      <div class="text-center">
        <div class="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-extrabold text-2xl shadow-lg shadow-indigo-500/25">
          7
        </div>
        <h1 class="mt-4 text-xl font-bold text-slate-900 dark:text-white">三月七小助手 · 云管理面板</h1>
        <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {{ store.authMode === 'oidc' ? `当前已启用 ${store.authBrand} 统一身份认证 (PKCE)` : '请输入管理员密钥或单账号专属密钥登录' }}
        </p>
      </div>

      <!-- OIDC 回调处理中加载态 -->
      <div v-if="callbackProcessing" class="mt-8 py-8 flex flex-col items-center justify-center gap-3 text-center">
        <div class="w-9 h-9 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-sm font-medium text-slate-700 dark:text-slate-300">正在验证 {{ store.authBrand }} 登录凭证...</p>
      </div>

      <!-- OIDC 模式登录界面 -->
      <div v-else-if="store.authMode === 'oidc'" class="mt-7 space-y-4">
        <div v-if="errorMsg" class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800/80 text-xs text-rose-700 dark:text-rose-300">
          {{ errorMsg }}
        </div>

        <button
          type="button"
          :disabled="loading"
          class="w-full py-3 px-4 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-60 shadow-md shadow-indigo-500/20 flex items-center justify-center gap-2 transition"
          @click="startOidcLogin"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
          </svg>
          <span>{{ loading ? '正在跳转认证中心...' : `使用 ${store.authBrand} 账号登录` }}</span>
        </button>

        <p class="text-[11px] text-center text-slate-400 dark:text-slate-500 leading-relaxed">
          登录将通过 OAuth 2.1 / OIDC PKCE (S256) 安全授权流程完成。<br />
          若登录后提示无权限，请联系管理员在后台绑定您的用户名。
        </p>
      </div>

      <!-- Token 模式登录界面 -->
      <form v-else class="mt-7 space-y-4" @submit.prevent="submitTokenLogin">
        <div v-if="errorMsg" class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800/80 text-xs text-rose-700 dark:text-rose-300">
          {{ errorMsg }}
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
            访问密钥 (WEBUI_TOKEN 或 账号专属密钥)
          </label>
          <input
            v-model="tokenInput"
            type="password"
            autocomplete="current-password"
            placeholder="请输入访问密钥..."
            class="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/90 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2.5 px-4 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-60 shadow-md shadow-indigo-500/20 transition"
        >
          {{ loading ? '验证中...' : '立即登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, loadAuthConfig, notify, setSession, store } from '../state.js'

const router = useRouter()
const tokenInput = ref('')
const loading = ref(false)
const callbackProcessing = ref(false)
const errorMsg = ref('')

function getCleanRedirectUri() {
  return `${window.location.origin}${window.location.pathname}`
}

async function startOidcLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    const redirectUri = getCleanRedirectUri()
    const res = await apiFetch(`/api/auth/oidc/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`)
    if (res.authorize_url) {
      window.location.href = res.authorize_url
    } else {
      throw new Error('未获取到有效的 OIDC 授权地址')
    }
  } catch (e) {
    errorMsg.value = e.message || '发起 OIDC 登录失败'
    loading.value = false
  }
}

async function handleOidcCallbackIfNeeded() {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const state = params.get('state')
  const err = params.get('error')
  const errDesc = params.get('error_description')

  if (err) {
    errorMsg.value = `SSO 授权拒绝: ${errDesc || err}`
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash)
    return
  }

  if (!code || !state) return

  callbackProcessing.value = true
  errorMsg.value = ''
  try {
    const redirectUri = getCleanRedirectUri()
    const authData = await apiFetch('/api/auth/oidc/callback', {
      method: 'POST',
      body: JSON.stringify({
        code,
        state,
        redirect_uri: redirectUri,
      }),
    })
    // 清理地址栏中的 ?code=&state=
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash)
    setSession(authData)

    const pendingInvite = authData.invite_code || sessionStorage.getItem('m7a_pending_invite_code') || ''
    sessionStorage.removeItem('m7a_pending_invite_code')

    if (authData.role === 'unauthorized') {
      router.replace({ name: 'unauthorized' })
    } else if (pendingInvite) {
      notify('身份绑定成功，请继续扫码登录游戏账号', 'success')
      router.replace({ name: 'invite', params: { code: pendingInvite }, query: { step: 'qr' } })
    } else {
      notify(`欢迎回来，${authData.username}`, 'success')
      router.replace({ name: 'dashboard' })
    }
  } catch (e) {
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash)
    errorMsg.value = e.message || 'OIDC 登录回调验证失败'
  } finally {
    callbackProcessing.value = false
  }
}

async function submitTokenLogin() {
  if (!tokenInput.value.trim()) {
    errorMsg.value = '请输入访问密钥'
    return
  }
  errorMsg.value = ''
  loading.value = true
  try {
    const authData = await apiFetch('/api/auth/token', {
      method: 'POST',
      body: JSON.stringify({ token: tokenInput.value.trim() }),
    })
    setSession(authData)
    notify(authData.role === 'admin' ? '管理员登录成功' : `已登录账号：${authData.username}`, 'success')
    router.replace({ name: 'dashboard' })
  } catch (e) {
    errorMsg.value = e.message || '密钥验证失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadAuthConfig()
  await handleOidcCallbackIfNeeded()
})
</script>
