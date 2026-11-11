<template>
  <div class="max-w-3xl mx-auto space-y-5">
    <!-- M3E 标题栏 -->
    <div
      class="rounded-[28px] p-5 sm:p-6 border flex items-center justify-between gap-4"
      style="background-color: var(--m3-surface-container-low); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
    >
      <div>
        <h2 class="text-lg sm:text-xl font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
          全局设置
        </h2>
        <p class="mt-1 text-xs sm:text-sm" style="color: var(--m3-on-surface-variant);">
          管理多账号队列的每日定时触发时间、网络连通性预检以及调试模拟模式
        </p>
      </div>

      <button
        type="button"
        :disabled="saving"
        class="m3-btn m3-btn-filled px-6 py-3 text-xs sm:text-sm shrink-0 shadow-xs disabled:opacity-55"
        @click="saveSettings"
      >
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
    </div>

    <!-- 1. 每日定时任务 -->
    <div class="m3-card m3-card-interactive m3-stagger-item p-5 sm:p-6 space-y-4" style="--stagger-index: 0;">
      <div class="flex items-center justify-between gap-4">
        <div>
          <h3 class="text-sm sm:text-base font-extrabold" style="color: var(--m3-on-surface);">每日自动运行队列</h3>
          <p class="text-xs mt-0.5" style="color: var(--m3-on-surface-variant);">
            到达指定时间后，按顺序依次执行所有「已启用」的游戏账号
          </p>
        </div>
        <M3Switch v-model="form.daily_run_enabled" />
      </div>

      <Transition name="m3-expand">
        <div
          v-if="form.daily_run_enabled"
          class="pt-4 border-t flex items-center gap-3"
          style="border-color: color-mix(in srgb, var(--m3-outline-variant) 40%, transparent);"
        >
          <label class="text-xs font-bold" style="color: var(--m3-on-surface);">每日触发时间 (24小时制):</label>
          <input
            v-model="form.daily_run_time"
            type="time"
            class="m3-input font-mono !text-sm"
          />
        </div>
      </Transition>
    </div>

    <!-- 2. 外网连通性预检 -->
    <div class="m3-card m3-card-interactive m3-stagger-item p-5 sm:p-6 space-y-4" style="--stagger-index: 1;">
      <div class="flex items-center justify-between gap-4">
        <div>
          <h3 class="text-sm sm:text-base font-extrabold" style="color: var(--m3-on-surface);">运行前网络连通性检查</h3>
          <p class="text-xs mt-0.5" style="color: var(--m3-on-surface-variant);">
            启动任务队列前检测米哈游及外网连通性，断网时自动等待重试
          </p>
        </div>
        <M3Switch v-model="form.check_internet" />
      </div>

      <Transition name="m3-expand">
        <div
          v-if="form.check_internet"
          class="pt-4 border-t grid grid-cols-1 sm:grid-cols-2 gap-4"
          style="border-color: color-mix(in srgb, var(--m3-outline-variant) 40%, transparent);"
        >
          <div class="space-y-1.5">
            <label class="block text-xs font-bold" style="color: var(--m3-on-surface-variant);">
              失败后重试等待间隔（秒）
            </label>
            <input
              v-model.number="form.check_internet_Wait"
              type="number"
              min="5"
              max="3600"
              class="m3-input w-full"
            />
          </div>
          <div class="space-y-1.5">
            <label class="block text-xs font-bold" style="color: var(--m3-on-surface-variant);">
              最大重试次数
            </label>
            <input
              v-model.number="form.check_internet_MaxRetries"
              type="number"
              min="1"
              max="30"
              class="m3-input w-full"
            />
          </div>
        </div>
      </Transition>
    </div>

    <!-- 3. 调试模拟模式 -->
    <div class="m3-card m3-card-interactive m3-stagger-item p-5 sm:p-6 flex items-center justify-between gap-4" style="--stagger-index: 2;">
      <div>
        <h3 class="text-sm sm:text-base font-extrabold" style="color: var(--m3-on-surface);">
          调试模拟运行模式 (Debug Mock)
        </h3>
        <p class="text-xs mt-0.5" style="color: var(--m3-on-surface-variant);">
          开启后点击「立即运行」将输出模拟阶段日志而不真正拉起 Chrome 浏览器，方便测试多账号队列与日志展示
        </p>
      </div>
      <M3Switch v-model="form.debug_mode" />
    </div>

    <!-- 4. 当前认证与前端主题状态说明 -->
    <div class="m3-card m3-stagger-item p-5 sm:p-6 space-y-3" style="--stagger-index: 3;">
      <h3 class="text-sm sm:text-base font-extrabold" style="color: var(--m3-on-surface);">
        系统运行环境与认证模式
      </h3>
      <div class="text-xs space-y-2 leading-relaxed" style="color: var(--m3-on-surface-variant);">
        <div class="flex flex-wrap items-center gap-2">
          <span>当前身份认证模式:</span>
          <span
            class="px-2.5 py-0.5 rounded-full font-bold"
            style="background-color: var(--m3-primary-container); color: var(--m3-on-primary-container);"
          >
            {{ store.authMode === 'oidc' ? `OIDC 统一身份认证 (${store.authBrand})` : 'Token 访问密钥模式' }}
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span>当前前端界面风格:</span>
          <span
            class="px-2.5 py-0.5 rounded-full font-bold"
            style="background-color: var(--m3-tertiary-container); color: var(--m3-on-tertiary-container);"
          >
            {{ store.uiTheme === 'simple' ? 'Simple 轻量简洁版' : 'M3E (Material 3 Expressive)' }}
          </span>
          <span class="opacity-80">（可通过环境变量 <code>WEBUI_THEME=m3e</code> 或 <code>WEBUI_THEME=simple</code> 切换）</span>
        </div>
        <p>
          提示：当环境变量同时配置了 <code>OIDC_ENDPOINT</code>、<code>OIDC_CLIENT_ID</code>、<code>OIDC_CLIENT_SECRET</code>（以及可选的 <code>OIDC_BRAND</code> 和 <code>OIDC_ADMIN_USERNAME</code>）时自动启用 OIDC PKCE 模式；否则使用 <code>WEBUI_TOKEN</code> 密钥模式。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import M3Switch from '../../components/m3e/M3Switch.vue'
import { apiFetch, notify, refreshStatus, store } from '../../state.js'

const saving = ref(false)
const form = reactive({
  daily_run_enabled: false,
  daily_run_time: '04:00',
  check_internet: false,
  check_internet_Wait: 60,
  check_internet_MaxRetries: 3,
  debug_mode: false,
})

async function loadSettings() {
  try {
    const res = await apiFetch('/api/settings')
    Object.assign(form, res)
  } catch (e) {
    notify(e.message || '加载调度设置失败', 'error')
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await apiFetch('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(form),
    })
    notify('调度设置已保存生效', 'success')
    await refreshStatus()
  } catch (e) {
    notify(e.message || '保存设置失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>
