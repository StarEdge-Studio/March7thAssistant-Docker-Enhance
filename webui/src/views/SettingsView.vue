<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <!-- 标题栏 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 flex items-center justify-between gap-4">
      <div>
        <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white">全局调度与运行策略</h2>
        <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          管理多账号队列的每日定时触发时间、网络连通性预检以及调试模拟模式
        </p>
      </div>

      <button
        type="button"
        :disabled="saving"
        class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-60 shadow-sm shadow-indigo-500/20 shrink-0 transition"
        @click="saveSettings"
      >
        {{ saving ? '保存中...' : '💾 保存调度设置' }}
      </button>
    </div>

    <!-- 1. 每日定时任务 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">每日自动运行队列</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400">到达指定时间后，按顺序依次执行所有「已启用」的游戏账号</p>
        </div>
        <input
          v-model="form.daily_run_enabled"
          type="checkbox"
          class="w-5 h-5 accent-indigo-600 rounded cursor-pointer"
        />
      </div>

      <div v-if="form.daily_run_enabled" class="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center gap-3">
        <label class="text-xs font-semibold text-slate-600 dark:text-slate-300">每日触发时间 (24小时制):</label>
        <input
          v-model="form.daily_run_time"
          type="time"
          class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-mono"
        />
      </div>
    </div>

    <!-- 2. 外网连通性预检 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">运行前网络连通性检查</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400">启动任务队列前检测米哈游及外网连通性，断网时自动等待重试</p>
        </div>
        <input
          v-model="form.check_internet"
          type="checkbox"
          class="w-5 h-5 accent-indigo-600 rounded cursor-pointer"
        />
      </div>

      <div v-if="form.check_internet" class="pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">失败后重试等待间隔（秒）</label>
          <input
            v-model.number="form.check_internet_Wait"
            type="number"
            min="5"
            max="3600"
            class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">最大重试次数</label>
          <input
            v-model.number="form.check_internet_MaxRetries"
            type="number"
            min="1"
            max="30"
            class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm"
          />
        </div>
      </div>
    </div>

    <!-- 3. 用户手动运行权限 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 flex items-center justify-between gap-4">
      <div>
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">允许用户手动运行自己账号</h3>
        <p class="text-xs text-slate-500 dark:text-slate-400">
          关闭后普通用户侧将隐藏「立即运行」与「单独运行」按钮，仅由每日定时队列或管理员触发执行
        </p>
      </div>
      <input
        v-model="form.allow_user_manual_run"
        type="checkbox"
        class="w-5 h-5 accent-indigo-600 rounded cursor-pointer"
      />
    </div>

    <!-- 4. 调试模拟模式 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 flex items-center justify-between gap-4">
      <div>
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">调试模拟运行模式 (Debug Mock)</h3>
        <p class="text-xs text-slate-500 dark:text-slate-400">
          开启后点击「立即运行」将输出模拟阶段日志而不真正拉起 Chrome 浏览器，方便测试多账号队列与日志展示
        </p>
      </div>
      <input
        v-model="form.debug_mode"
        type="checkbox"
        class="w-5 h-5 accent-indigo-600 rounded cursor-pointer"
      />
    </div>

    <!-- 5. 当前认证系统状态说明 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 space-y-2.5">
      <h3 class="text-sm font-bold text-slate-900 dark:text-white">身份认证系统状态</h3>
      <div class="text-xs text-slate-600 dark:text-slate-300 space-y-1.5 leading-relaxed">
        <div>
          当前激活模式:
          <span class="px-2 py-0.5 rounded font-semibold bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300">
            {{ store.authMode === 'oidc' ? `OIDC 统一身份认证 (${store.authBrand})` : 'Token 访问密钥模式' }}
          </span>
        </div>
        <p class="text-slate-400 dark:text-slate-500">
          提示：当环境变量同时配置了 <code>OIDC_ENDPOINT</code>、<code>OIDC_CLIENT_ID</code>、<code>OIDC_CLIENT_SECRET</code>（以及可选的 <code>OIDC_BRAND</code> 和 <code>OIDC_ADMIN_USERNAME</code>）时自动启用 OIDC PKCE 模式；否则使用 <code>WEBUI_TOKEN</code> 密钥模式。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { apiFetch, notify, refreshStatus, store } from '../state.js'

const saving = ref(false)
const form = reactive({
  daily_run_enabled: false,
  daily_run_time: '04:00',
  check_internet: false,
  check_internet_Wait: 60,
  check_internet_MaxRetries: 3,
  allow_user_manual_run: true,
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
