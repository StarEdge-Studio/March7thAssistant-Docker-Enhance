<template>
  <div class="min-h-screen flex flex-col md:flex-row bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100">
    <!-- 全局 Toast 消息层 -->
    <div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-[calc(100vw-2rem)] pointer-events-none">
      <div
        v-for="t in store.toasts"
        :key="t.id"
        class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-md text-sm font-medium transition-all duration-200"
        :class="{
          'bg-emerald-50/95 dark:bg-emerald-950/90 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200': t.type === 'success',
          'bg-rose-50/95 dark:bg-rose-950/90 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200': t.type === 'error',
          'bg-amber-50/95 dark:bg-amber-950/90 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200': t.type === 'warning',
          'bg-white/95 dark:bg-slate-900/95 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100': t.type === 'info',
        }"
      >
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :class="{
            'bg-emerald-500': t.type === 'success',
            'bg-rose-500': t.type === 'error',
            'bg-amber-500': t.type === 'warning',
            'bg-indigo-500': t.type === 'info',
          }"
        ></span>
        <span class="flex-1 break-words">{{ t.message }}</span>
      </div>
    </div>

    <!-- 全局确认对话框 -->
    <div
      v-if="store.confirmDialog.visible"
      class="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs"
      @click.self="resolveConfirmModal(false)"
    >
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <h3 class="text-lg font-bold text-slate-900 dark:text-white">{{ store.confirmDialog.title }}</h3>
        <p class="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed whitespace-pre-line">
          {{ store.confirmDialog.message }}
        </p>
        <div class="mt-6 flex justify-end gap-3">
          <button
            type="button"
            class="px-4 py-2 rounded-xl text-sm font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
            @click="resolveConfirmModal(false)"
          >
            {{ store.confirmDialog.cancelText }}
          </button>
          <button
            type="button"
            class="px-4 py-2 rounded-xl text-sm font-medium text-white transition shadow-sm"
            :class="store.confirmDialog.danger ? 'bg-rose-600 hover:bg-rose-500' : 'bg-indigo-600 hover:bg-indigo-500'"
            @click="resolveConfirmModal(true)"
          >
            {{ store.confirmDialog.confirmText }}
          </button>
        </div>
      </div>
    </div>

    <!-- 登录页或无权限页独立全屏渲染 -->
    <template v-if="isStandaloneRoute">
      <router-view class="flex-1" />
    </template>

    <!-- 已授权主框架 -->
    <template v-else>
      <!-- 桌面端侧边导航栏 -->
      <aside class="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800/80 z-30">
        <!-- 品牌区 -->
        <div class="h-16 px-5 flex items-center gap-3 border-b border-slate-100 dark:border-slate-800/80">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-indigo-500/20">
            7
          </div>
          <div class="min-w-0">
            <h1 class="font-bold text-sm tracking-tight text-slate-900 dark:text-white truncate">三月七小助手</h1>
            <p class="text-[11px] text-slate-400 dark:text-slate-500 truncate">Docker 多账号增强中心</p>
          </div>
        </div>

        <!-- 导航菜单 -->
        <nav class="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all"
            :class="$route.path.startsWith(item.to)
              ? 'bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 font-semibold'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'"
          >
            <div class="flex items-center gap-3">
              <span class="w-5 h-5 flex items-center justify-center" v-html="item.icon"></span>
              <span>{{ item.label }}</span>
            </div>
            <span
              v-if="item.badge"
              class="px-2 py-0.5 text-[11px] rounded-full font-semibold"
              :class="item.badgeClass"
            >
              {{ item.badge }}
            </span>
          </router-link>
        </nav>

        <!-- 底部当前登录信息与操作 -->
        <div class="p-3 border-t border-slate-100 dark:border-slate-800/80 space-y-2">
          <div class="px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 flex items-center gap-2.5">
            <img
              v-if="store.avatar && !avatarLoadError"
              :src="store.avatar"
              :alt="userDisplayName"
              class="w-9 h-9 rounded-full object-cover shrink-0 border border-slate-200 dark:border-slate-700"
              referrerpolicy="no-referrer"
              @error="avatarLoadError = true"
            />
            <div
              v-else
              class="w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shrink-0 bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300"
            >
              {{ userAvatarText }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate" :title="userDisplayName">
                  {{ userDisplayName }}
                </span>
                <span
                  class="px-1.5 py-0.2 text-[10px] rounded font-medium shrink-0"
                  :class="store.role === 'admin'
                    ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300'
                    : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300'"
                >
                  {{ store.role === 'admin' ? '管理员' : '用户' }}
                </span>
              </div>
              <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5 truncate">
                认证模式: {{ store.authMode === 'oidc' ? `OIDC (${store.authBrand})` : 'Token 密钥' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              type="button"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
              @click="toggleTheme"
            >
              <span>{{ store.darkMode ? '☀️ 浅色' : '🌙 深色' }}</span>
            </button>
            <button
              type="button"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-500/20 transition"
              @click="handleLogout"
            >
              退出登录
            </button>
          </div>
        </div>
      </aside>

      <!-- 移动端顶部栏 -->
      <header class="md:hidden sticky top-0 z-30 h-14 px-4 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-base shrink-0">
            7
          </div>
          <div class="truncate">
            <div class="flex items-center gap-1.5">
              <span class="font-bold text-sm text-slate-900 dark:text-white truncate">三月七小助手</span>
              <span
                v-if="store.scheduler.is_running"
                class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                运行中
              </span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-1.5">
          <button
            type="button"
            class="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
            @click="toggleTheme"
            title="切换主题"
          >
            {{ store.darkMode ? '☀️' : '🌙' }}
          </button>
          <button
            type="button"
            class="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-400"
            @click="handleLogout"
          >
            退出
          </button>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="flex-1 md:pl-64 pb-20 md:pb-6 min-w-0">
        <div class="max-w-7xl mx-auto p-3.5 sm:p-5 md:p-6">
          <router-view />
        </div>
      </main>

      <!-- 移动端底部固定导航栏 -->
      <nav
        class="md:hidden fixed bottom-0 inset-x-0 z-30 h-16 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 grid"
        :class="navItems.length === 4 ? 'grid-cols-4' : 'grid-cols-3'"
      >
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex flex-col items-center justify-center gap-1 text-[11px] font-medium transition"
          :class="$route.path.startsWith(item.to)
            ? 'text-indigo-600 dark:text-indigo-400 font-semibold'
            : 'text-slate-500 dark:text-slate-400'"
        >
          <span class="w-5 h-5 flex items-center justify-center" v-html="item.icon"></span>
          <span>{{ item.shortLabel || item.label }}</span>
        </router-link>
      </nav>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  clearSession,
  notify,
  resolveConfirmModal,
  store,
  toggleTheme,
} from './state.js'

const route = useRoute()
const router = useRouter()
const avatarLoadError = ref(false)

watch(
  () => store.avatar,
  () => {
    avatarLoadError.value = false
  }
)

const userDisplayName = computed(() => {
  return store.displayName || store.username || (store.role === 'admin' ? '管理员' : '用户')
})

const userAvatarText = computed(() => {
  const base = store.displayName || store.username || (store.role === 'admin' ? '管' : '用')
  return base.slice(0, 1).toUpperCase()
})

const isStandaloneRoute = computed(() => {
  return route.name === 'login' || route.name === 'unauthorized' || route.name === 'invite'
})

const navItems = computed(() => {
  const items = [
    {
      to: '/dashboard',
      label: '运行与日志',
      shortLabel: '运行日志',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"/></svg>`,
      badge: store.scheduler.is_running ? '运行中' : '',
      badgeClass: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300',
    },
    {
      to: '/accounts',
      label: '账号配置',
      shortLabel: '账号配置',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z"/></svg>`,
      badge: store.accounts.length ? String(store.accounts.length) : '',
      badgeClass: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
    },
    {
      to: '/tasks',
      label: '任务配置',
      shortLabel: '任务配置',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75"/></svg>`,
    },
  ]

  if (store.role === 'admin') {
    items.push({
      to: '/settings',
      label: '全局设置',
      shortLabel: '全局设置',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>`,
    })
  }
  return items
})

function handleLogout() {
  clearSession()
  notify('已退出登录', 'info')
  router.replace({ name: 'login' })
}
</script>
