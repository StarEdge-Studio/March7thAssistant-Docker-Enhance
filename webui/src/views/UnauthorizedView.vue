<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-slate-950">
    <div class="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl shadow-xl border border-slate-200 dark:border-slate-800 p-7 text-center">
      <div class="mx-auto w-14 h-14 rounded-2xl bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.25-8.25-3.286Zm0 13.036h.008v.008H12v-.008Z" />
        </svg>
      </div>

      <h2 class="mt-4 text-xl font-bold text-slate-900 dark:text-white">暂无访问权限</h2>
      <p class="mt-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
        您已通过 {{ store.authBrand || 'OIDC' }} 认证登录，但当前用户名尚未绑定任何游戏账号，也未被设为管理员。
      </p>

      <div class="mt-5 p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700/80 flex items-center justify-between gap-2">
        <div class="text-left min-w-0">
          <div class="text-[11px] text-slate-400 dark:text-slate-500">当前登录用户名 (username)</div>
          <div class="text-sm font-mono font-semibold text-slate-900 dark:text-white truncate">
            {{ store.username || '未知用户' }}
          </div>
        </div>
        <button
          type="button"
          class="px-3 py-1.5 rounded-xl text-xs font-medium bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 transition shrink-0"
          @click="copyUsername"
        >
          复制用户名
        </button>
      </div>

      <p class="mt-4 text-xs text-slate-400 dark:text-slate-500">
        请将上方用户名发送给管理员，由管理员在「账号管理」中为您绑定对应账号后点击下方按钮刷新权限。
      </p>

      <div class="mt-6 flex flex-col sm:flex-row gap-2.5">
        <button
          type="button"
          :disabled="checking"
          class="flex-1 py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 transition"
          @click="recheckPermission"
        >
          {{ checking ? '正在检测...' : '重新检测权限' }}
        </button>
        <button
          type="button"
          class="flex-1 py-2.5 px-4 rounded-xl text-sm font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
          @click="logout"
        >
          退出登录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { clearSession, fetchCurrentUser, notify, store } from '../state.js'

const router = useRouter()
const checking = ref(false)

async function copyUsername() {
  if (!store.username) return
  try {
    await navigator.clipboard.writeText(store.username)
    notify('已复制用户名到剪贴板', 'success')
  } catch {
    notify('复制失败，请手动复制', 'warning')
  }
}

async function recheckPermission() {
  checking.value = true
  try {
    const me = await fetchCurrentUser()
    if (me && me.role && me.role !== 'unauthorized') {
      notify('权限已开通，正在进入系统', 'success')
      router.replace({ name: 'dashboard' })
    } else {
      notify('当前仍未分配账号权限，请稍后再试', 'warning')
    }
  } finally {
    checking.value = false
  }
}

function logout() {
  clearSession()
  router.replace({ name: 'login' })
}
</script>
