<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
    style="background-color: var(--m3-surface); color: var(--m3-on-surface);"
  >
    <!-- M3E 装饰性动态色块背景 -->
    <div
      class="w-[420px] h-[420px] rounded-full blur-3xl opacity-45 pointer-events-none absolute -top-24 -left-24"
      style="background-color: var(--m3-primary-container);"
    ></div>
    <div
      class="w-[380px] h-[380px] rounded-full blur-3xl opacity-45 pointer-events-none absolute -bottom-24 -right-24"
      style="background-color: var(--m3-tertiary-container);"
    ></div>

    <div
      class="w-full max-w-[440px] rounded-[36px] p-8 sm:p-10 shadow-xl border relative z-10 transition-all"
      style="background-color: var(--m3-surface-container-low); border-color: color-mix(in srgb, var(--m3-outline-variant) 55%, transparent);"
    >
      <!-- 顶部 M3E 徽章与标题 -->
      <div class="text-center">
        <div class="relative w-16 h-16 mx-auto">
          <div
            class="w-16 h-16 rounded-[22px] rotate-12 absolute inset-0"
            style="background-color: var(--m3-tertiary-container);"
          ></div>
          <div
            class="relative w-16 h-16 rounded-[22px] flex items-center justify-center font-black text-3xl shadow-md"
            style="background-color: var(--m3-primary); color: var(--m3-on-primary);"
          >
            7
          </div>
        </div>

        <h1 class="mt-6 text-2xl font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
          三月七小助手
        </h1>
        <p class="mt-1.5 text-xs font-medium" style="color: var(--m3-on-surface-variant);">
          {{ store.authMode === 'oidc' ? `已启用 ${store.authBrand} 统一身份认证 (PKCE)` : '请输入管理员密钥或单账号专属密钥登录' }}
        </p>
      </div>

      <!-- OIDC 回调处理中 -->
      <div v-if="callbackProcessing" class="mt-8 py-8 flex flex-col items-center justify-center gap-3 text-center">
        <div
          class="w-10 h-10 border-3 border-t-transparent rounded-full animate-spin"
          style="border-color: var(--m3-primary); border-top-color: transparent;"
        ></div>
        <p class="text-sm font-semibold" style="color: var(--m3-on-surface);">
          正在验证 {{ store.authBrand }} 授权凭证...
        </p>
      </div>

      <!-- OIDC 模式登录界面 -->
      <div v-else-if="store.authMode === 'oidc'" class="mt-8 space-y-5">
        <div
          v-if="errorMsg"
          class="p-4 rounded-[20px] text-xs font-medium"
          style="background-color: var(--m3-error-container); color: var(--m3-on-error-container);"
        >
          {{ errorMsg }}
        </div>

        <button
          type="button"
          :disabled="loading"
          class="m3-btn m3-btn-filled w-full py-3.5 px-6 text-sm shadow-sm disabled:opacity-55"
          @click="startOidcLogin"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
          </svg>
          <span>{{ loading ? '正在跳转认证中心...' : `使用 ${store.authBrand} 账号登录` }}</span>
        </button>

        <p class="text-[11px] text-center leading-relaxed" style="color: var(--m3-on-surface-variant);">
          采用 OAuth 2.1 / OIDC PKCE (S256) 安全认证标准。<br />
          若登录后显示无权限，请联系管理员在后台绑定您的用户名。
        </p>
      </div>

      <!-- Token 模式登录界面 -->
      <form v-else class="mt-8 space-y-5" @submit.prevent="submitTokenLogin">
        <div
          v-if="errorMsg"
          class="p-4 rounded-[20px] text-xs font-medium"
          style="background-color: var(--m3-error-container); color: var(--m3-on-error-container);"
        >
          {{ errorMsg }}
        </div>

        <div class="space-y-2">
          <label class="block text-xs font-bold px-1" style="color: var(--m3-on-surface-variant);">
            访问密钥（管理员 Token / 账号专属密钥）
          </label>
          <input
            v-model="tokenInput"
            type="password"
            autocomplete="current-password"
            placeholder="请输入访问密钥..."
            class="m3-input w-full !py-3 !px-4 !text-sm"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="m3-btn m3-btn-filled w-full py-3.5 px-6 text-sm shadow-sm disabled:opacity-55"
        >
          {{ loading ? '正在验证...' : '进入系统' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, loadAuthConfig, notify, setSession, store } from '../../state.js'

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
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash)
    setSession(authData)

    if (authData.role === 'unauthorized') {
      router.replace({ name: 'unauthorized' })
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
