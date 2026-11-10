<template>
  <div
    class="min-h-screen flex items-center justify-center p-4"
    style="background-color: var(--m3-surface); color: var(--m3-on-surface);"
  >
    <div
      class="w-full max-w-md rounded-[32px] p-8 text-center border shadow-xl"
      style="background-color: var(--m3-surface-container-low); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
    >
      <div
        class="mx-auto w-16 h-16 rounded-[22px] flex items-center justify-center"
        style="background-color: var(--m3-tertiary-container); color: var(--m3-on-tertiary-container);"
      >
        <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.25-8.25-3.286Zm0 13.036h.008v.008H12v-.008Z" />
        </svg>
      </div>

      <h2 class="mt-5 text-xl font-extrabold tracking-tight">暂无访问权限</h2>
      <p class="mt-2 text-xs sm:text-sm leading-relaxed" style="color: var(--m3-on-surface-variant);">
        您已通过 {{ store.authBrand || 'OIDC' }} 认证登录，但当前用户名尚未绑定任何游戏账号，也未被设为管理员。
      </p>

      <div
        class="mt-6 p-4 rounded-[22px] flex items-center justify-between gap-2"
        style="background-color: var(--m3-surface-container-highest);"
      >
        <div class="text-left min-w-0">
          <div class="text-[11px] font-medium" style="color: var(--m3-on-surface-variant);">当前登录用户名</div>
          <div class="text-sm font-mono font-bold truncate" style="color: var(--m3-on-surface);">
            {{ store.username || '未知用户' }}
          </div>
        </div>
        <button
          type="button"
          class="m3-btn m3-btn-tonal px-4 py-2 text-xs shrink-0"
          @click="copyUsername"
        >
          复制用户名
        </button>
      </div>

      <p class="mt-4 text-xs" style="color: var(--m3-on-surface-variant);">
        请将上方用户名发送给管理员，由管理员在「账号配置」中为您绑定对应账号后点击下方按钮刷新权限。
      </p>

      <div class="mt-7 flex flex-col sm:flex-row gap-3">
        <button
          type="button"
          :disabled="checking"
          class="m3-btn m3-btn-filled flex-1 py-3 px-4 text-sm disabled:opacity-55"
          @click="recheckPermission"
        >
          {{ checking ? '正在检测...' : '重新检测权限' }}
        </button>
        <button
          type="button"
          class="m3-btn m3-btn-tonal flex-1 py-3 px-4 text-sm"
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
import { clearSession, fetchCurrentUser, notify, store } from '../../state.js'

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
