<template>
  <div
    class="min-h-screen flex flex-col md:flex-row transition-colors duration-300"
    style="background-color: var(--m3-surface-container); color: var(--m3-on-surface);"
  >
    <!-- M3E 全局 Snackbar / Toast 通知层 -->
    <TransitionGroup
      tag="div"
      name="m3-toast"
      class="fixed top-4 right-4 z-[100] flex flex-col gap-2.5 max-w-sm w-[calc(100vw-2rem)] pointer-events-none"
    >
      <div
        v-for="t in store.toasts"
        :key="t.id"
        class="pointer-events-auto flex items-center gap-3 px-5 py-3.5 rounded-[20px] shadow-xl border text-sm font-medium"
        :style="toastStyle(t.type)"
      >
        <span
          class="w-2.5 h-2.5 rounded-full shrink-0"
          :style="{ backgroundColor: toastDotColor(t.type) }"
        ></span>
        <span class="flex-1 break-words">{{ t.message }}</span>
      </div>
    </TransitionGroup>

    <!-- M3E 全局确认对话框 (28px Extra-Large Corner Radius + Spring Entrance) -->
    <Transition name="m3-dialog">
      <div
        v-if="store.confirmDialog.visible"
        class="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
        @click.self="resolveConfirmModal(false)"
      >
        <div
          class="m3-dialog-panel max-w-md w-full p-7 rounded-[28px] shadow-2xl border"
          style="background-color: var(--m3-surface-container-high); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
        >
          <h3 class="text-xl font-bold tracking-tight" style="color: var(--m3-on-surface);">
            {{ store.confirmDialog.title }}
          </h3>
          <p class="mt-3 text-sm leading-relaxed whitespace-pre-line" style="color: var(--m3-on-surface-variant);">
            {{ store.confirmDialog.message }}
          </p>
          <div class="mt-7 flex justify-end gap-2.5">
            <button
              type="button"
              class="m3-btn m3-btn-tonal px-5 py-2.5 text-sm"
              @click="resolveConfirmModal(false)"
            >
              {{ store.confirmDialog.cancelText }}
            </button>
            <button
              type="button"
              class="m3-btn px-6 py-2.5 text-sm"
              :class="store.confirmDialog.danger ? 'm3-btn-error' : 'm3-btn-filled'"
              @click="resolveConfirmModal(true)"
            >
              {{ store.confirmDialog.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 登录页或无权限页独立全屏渲染 -->
    <template v-if="isStandaloneRoute">
      <router-view v-slot="{ Component, route: curRoute }">
        <Transition name="m3-page" mode="out-in">
          <component :is="Component" :key="curRoute.path" class="flex-1" />
        </Transition>
      </router-view>
    </template>

    <!-- M3E 自适应主框架 (Navigation Drawer + Framed Surface Viewport) -->
    <template v-else>
      <!-- 桌面端 M3E Navigation Drawer -->
      <aside class="hidden md:flex md:w-[268px] md:flex-col md:fixed md:inset-y-0 px-3 py-4 z-30 select-none">
        <!-- 品牌标识头 -->
        <div class="group/brand px-4 py-3 flex items-center gap-3.5">
          <div class="relative shrink-0">
            <div
              class="w-11 h-11 rounded-[16px] rotate-6 group-hover/brand:rotate-12 group-hover/brand:scale-105 transition-transform duration-300 absolute inset-0 opacity-60"
              style="background-color: var(--m3-tertiary-container); transition-timing-function: var(--m3-spring);"
            ></div>
            <div
              class="relative w-11 h-11 rounded-[16px] group-hover/brand:rounded-[13px] group-hover/brand:-rotate-3 transition-all duration-300 flex items-center justify-center font-black text-xl shadow-xs"
              style="background-color: var(--m3-primary); color: var(--m3-on-primary); transition-timing-function: var(--m3-spring);"
            >
              7
            </div>
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-1.5">
              <h1 class="font-extrabold text-base tracking-tight truncate" style="color: var(--m3-on-surface);">
                三月七小助手
              </h1>
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide"
                style="background-color: var(--m3-tertiary-container); color: var(--m3-on-tertiary-container);"
              >
                M3E
              </span>
            </div>
            <p class="text-xs truncate mt-0.5" style="color: var(--m3-on-surface-variant);">
              多账号容器云控制台
            </p>
          </div>
        </div>

        <!-- M3E 胶囊导航列表 -->
        <nav class="flex-1 mt-5 space-y-1.5 overflow-y-auto px-1">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="group flex items-center justify-between h-14 px-4 rounded-[28px] active:rounded-[16px] active:scale-[0.98] text-sm transition-all duration-300"
            :style="isActiveRoute(item.to)
              ? {
                  backgroundColor: 'var(--m3-secondary-container)',
                  color: 'var(--m3-on-secondary-container)',
                  fontWeight: '700',
                  transitionTimingFunction: 'var(--m3-spring-soft)',
                }
              : {
                  color: 'var(--m3-on-surface-variant)',
                  fontWeight: '500',
                  transitionTimingFunction: 'var(--m3-spring-soft)',
                }"
          >
            <div class="flex items-center gap-3.5">
              <span
                class="w-6 h-6 flex items-center justify-center transition-transform duration-300 group-hover:scale-115 group-hover:-rotate-6"
                :class="isActiveRoute(item.to) ? 'scale-110' : ''"
                style="transition-timing-function: var(--m3-spring);"
                v-html="item.icon"
              ></span>
              <span class="tracking-wide transition-transform duration-300 group-hover:translate-x-0.5">{{ item.label }}</span>
            </div>
            <span
              v-if="item.badge"
              class="px-2.5 py-0.5 text-[11px] rounded-full font-bold transition-transform duration-300 group-hover:scale-105"
              :style="item.isRunningBadge
                ? { backgroundColor: 'var(--m3-tertiary-container)', color: 'var(--m3-on-tertiary-container)' }
                : { backgroundColor: 'var(--m3-primary-container)', color: 'var(--m3-on-primary-container)' }"
            >
              {{ item.badge }}
            </span>
          </router-link>
        </nav>

        <!-- 底部 M3E 用户信息与快捷控制卡片 -->
        <div
          class="p-4 rounded-[26px] space-y-3"
          style="background-color: var(--m3-surface-container-high);"
        >
          <div class="flex items-center gap-3">
            <img
              v-if="store.avatar && !avatarLoadError"
              :src="store.avatar"
              :alt="userDisplayName"
              class="w-10 h-10 rounded-full object-cover shrink-0 border"
              style="border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
              referrerpolicy="no-referrer"
              @error="avatarLoadError = true"
            />
            <div
              v-else
              class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0"
              style="background-color: var(--m3-primary-container); color: var(--m3-on-primary-container);"
            >
              {{ userAvatarText }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-bold truncate" style="color: var(--m3-on-surface);" :title="userDisplayName">
                  {{ userDisplayName }}
                </span>
                <span
                  class="px-2 py-0.5 text-[10px] rounded-full font-bold shrink-0"
                  :style="store.role === 'admin'
                    ? { backgroundColor: 'var(--m3-primary)', color: 'var(--m3-on-primary)' }
                    : { backgroundColor: 'var(--m3-tertiary-container)', color: 'var(--m3-on-tertiary-container)' }"
                >
                  {{ store.role === 'admin' ? '管理员' : '用户' }}
                </span>
              </div>
              <p class="text-[11px] truncate mt-0.5" style="color: var(--m3-on-surface-variant);">
                {{ store.authMode === 'oidc' ? `OIDC · ${store.authBrand}` : 'Token 密钥认证' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              type="button"
              class="m3-btn m3-btn-tonal flex-1 py-2 px-3 text-xs"
              @click="toggleTheme"
            >
              <svg v-if="store.darkMode" class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
              </svg>
              <svg v-else class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
              </svg>
              <span>{{ store.darkMode ? '浅色' : '深色' }}</span>
            </button>
            <button
              type="button"
              class="m3-btn m3-btn-error flex-1 py-2 px-3 text-xs"
              @click="handleLogout"
            >
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </aside>

      <!-- 移动端 M3E Top App Bar -->
      <header
        class="md:hidden sticky top-0 z-30 h-16 px-4 flex items-center justify-between backdrop-blur-md border-b"
        style="background-color: color-mix(in srgb, var(--m3-surface-container) 88%, transparent); border-color: color-mix(in srgb, var(--m3-outline-variant) 45%, transparent);"
      >
        <div class="flex items-center gap-3 min-w-0">
          <div
            class="w-9 h-9 rounded-[14px] flex items-center justify-center font-black text-base shrink-0"
            style="background-color: var(--m3-primary); color: var(--m3-on-primary);"
          >
            7
          </div>
          <div class="truncate">
            <div class="flex items-center gap-2">
              <span class="font-extrabold text-base truncate" style="color: var(--m3-on-surface);">三月七小助手</span>
              <span
                v-if="store.scheduler.is_running"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold"
                style="background-color: var(--m3-tertiary-container); color: var(--m3-on-tertiary-container);"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-current animate-ping"></span>
                运行中
              </span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            type="button"
            class="m3-btn m3-btn-tonal w-9 h-9 text-sm"
            title="切换深浅色"
            @click="toggleTheme"
          >
            <svg v-if="store.darkMode" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
            </svg>
          </button>
          <button
            type="button"
            class="m3-btn m3-btn-error px-3.5 h-9 text-xs"
            @click="handleLogout"
          >
            退出
          </button>
        </div>
      </header>

      <!-- 主内容视口 (Desktop 圆角 32px 悬浮画布层) -->
      <main class="flex-1 md:pl-[268px] md:pr-3 md:py-3 pb-24 md:pb-3 min-w-0 flex flex-col">
        <div
          class="flex-1 md:rounded-[32px] p-4 sm:p-6 md:p-7 border transition-colors duration-300"
          style="background-color: var(--m3-surface); border-color: color-mix(in srgb, var(--m3-outline-variant) 40%, transparent);"
        >
          <div class="max-w-7xl mx-auto">
            <router-view v-slot="{ Component, route: curRoute }">
              <Transition name="m3-page" mode="out-in">
                <component :is="Component" :key="curRoute.path" />
              </Transition>
            </router-view>
          </div>
        </div>
      </main>

      <!-- 移动端 M3E Expressive Bottom Navigation Bar (带胶囊指示器) -->
      <nav
        class="md:hidden fixed bottom-0 inset-x-0 z-30 h-20 border-t grid px-2 select-none"
        :class="navItems.length === 4 ? 'grid-cols-4' : 'grid-cols-3'"
        style="background-color: var(--m3-surface-container); border-color: color-mix(in srgb, var(--m3-outline-variant) 45%, transparent);"
      >
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="group flex flex-col items-center justify-center gap-1 py-1 active:scale-95 transition-transform duration-200"
        >
          <div
            class="h-8 flex items-center justify-center rounded-[16px] group-active:rounded-[10px] transition-all duration-300"
            :style="isActiveRoute(item.to)
              ? {
                  width: '64px',
                  backgroundColor: 'var(--m3-secondary-container)',
                  color: 'var(--m3-on-secondary-container)',
                  transitionTimingFunction: 'var(--m3-spring)',
                }
              : {
                  width: '36px',
                  backgroundColor: 'transparent',
                  color: 'var(--m3-on-surface-variant)',
                  transitionTimingFunction: 'var(--m3-spring)',
                }"
          >
            <span
              class="w-5 h-5 flex items-center justify-center transition-transform duration-300"
              :class="isActiveRoute(item.to) ? 'scale-110 -translate-y-0.5' : 'group-hover:scale-105'"
              style="transition-timing-function: var(--m3-spring);"
              v-html="item.icon"
            ></span>
          </div>
          <span
            class="text-[11px] tracking-tight transition-all duration-200"
            :style="isActiveRoute(item.to)
              ? { color: 'var(--m3-on-surface)', fontWeight: '700' }
              : { color: 'var(--m3-on-surface-variant)', fontWeight: '500' }"
          >
            {{ item.shortLabel || item.label }}
          </span>
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
  return store.displayName || store.username || (store.role === 'admin' ? '管理员' : '账号用户')
})

const userAvatarText = computed(() => {
  const base = store.displayName || store.username || (store.role === 'admin' ? '管' : '用')
  return base.slice(0, 1).toUpperCase()
})

const isStandaloneRoute = computed(() => {
  return route.name === 'login' || route.name === 'unauthorized'
})

function isActiveRoute(prefix) {
  return route.path.startsWith(prefix)
}

function toastStyle(type) {
  if (type === 'error') {
    return {
      backgroundColor: 'var(--m3-error-container)',
      color: 'var(--m3-on-error-container)',
      borderColor: 'color-mix(in srgb, var(--m3-error) 35%, transparent)',
    }
  }
  if (type === 'warning') {
    return {
      backgroundColor: 'var(--m3-tertiary-container)',
      color: 'var(--m3-on-tertiary-container)',
      borderColor: 'color-mix(in srgb, var(--m3-tertiary) 35%, transparent)',
    }
  }
  if (type === 'success') {
    return {
      backgroundColor: 'var(--m3-primary-container)',
      color: 'var(--m3-on-primary-container)',
      borderColor: 'color-mix(in srgb, var(--m3-primary) 35%, transparent)',
    }
  }
  return {
    backgroundColor: 'var(--m3-surface-container-highest)',
    color: 'var(--m3-on-surface)',
    borderColor: 'var(--m3-outline-variant)',
  }
}

function toastDotColor(type) {
  if (type === 'error') return 'var(--m3-error)'
  if (type === 'warning') return 'var(--m3-tertiary)'
  return 'var(--m3-primary)'
}

const navItems = computed(() => {
  const items = [
    {
      to: '/dashboard',
      label: '运行与日志',
      shortLabel: '运行与日志',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"/></svg>`,
      badge: store.scheduler.is_running ? '运行中' : '',
      isRunningBadge: true,
    },
    {
      to: '/accounts',
      label: '账号配置',
      shortLabel: '账号配置',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z"/></svg>`,
      badge: store.accounts.length ? String(store.accounts.length) : '',
      isRunningBadge: false,
    },
    {
      to: '/tasks',
      label: '任务配置',
      shortLabel: '任务配置',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75"/></svg>`,
    },
  ]

  if (store.role === 'admin') {
    items.push({
      to: '/settings',
      label: '全局设置',
      shortLabel: '全局设置',
      icon: `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>`,
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
