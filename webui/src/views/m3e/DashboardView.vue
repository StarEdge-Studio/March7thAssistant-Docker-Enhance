<template>
  <div class="space-y-5">
    <!-- M3E Expressive Hero 状态横幅卡片 -->
    <div
      class="relative overflow-hidden rounded-[32px] p-5 sm:p-7 border transition-all"
      style="background-color: var(--m3-surface-container-low); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
    >
      <!-- 有机动态装饰背景 -->
      <div
        class="w-64 h-64 rounded-full blur-3xl opacity-35 pointer-events-none absolute -top-20 -right-12"
        :style="{ backgroundColor: store.scheduler.is_running ? 'var(--m3-tertiary-container)' : 'var(--m3-primary-container)' }"
      ></div>

      <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
        <div class="flex items-start sm:items-center gap-4">
          <div
            class="w-14 h-14 rounded-[22px] flex items-center justify-center shrink-0 shadow-xs transition-all duration-300"
            :style="store.scheduler.is_running
              ? { backgroundColor: 'var(--m3-tertiary-container)', color: 'var(--m3-on-tertiary-container)' }
              : { backgroundColor: 'var(--m3-primary-container)', color: 'var(--m3-on-primary-container)' }"
          >
            <svg v-if="store.scheduler.is_running" class="w-7 h-7 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"></path>
            </svg>
            <svg v-else class="w-7 h-7" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
            </svg>
          </div>

          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-lg sm:text-xl font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
                {{ store.scheduler.is_running ? `正在运行：${store.scheduler.current_account_name || '任务队列'}` : '运行与日志 · 空闲待命' }}
              </h2>
              <span
                v-if="store.scheduler.settings?.daily_run_enabled"
                class="px-3 py-1 rounded-full text-xs font-bold"
                style="background-color: var(--m3-secondary-container); color: var(--m3-on-secondary-container);"
              >
                ⏰ 每日 {{ store.scheduler.settings.daily_run_time }} 定时执行
              </span>
              <span
                v-if="store.scheduler.settings?.debug_mode"
                class="px-3 py-1 rounded-full text-xs font-bold"
                style="background-color: var(--m3-tertiary-container); color: var(--m3-on-tertiary-container);"
              >
                🐞 调试模拟模式
              </span>
            </div>
            <p class="mt-1 text-xs sm:text-sm" style="color: var(--m3-on-surface-variant);">
              <template v-if="store.scheduler.internet_retry_info">
                网络连通性等待重试中（第 {{ store.scheduler.internet_retry_info.retry }}/{{ store.scheduler.internet_retry_info.max_retries }} 次）...
              </template>
              <template v-else-if="store.scheduler.is_running">
                当前运行编号: <span class="font-mono font-semibold">{{ store.scheduler.current_run_id }}</span>
              </template>
              <template v-else>
                共 {{ store.accounts.length }} 个账号（已启用 {{ enabledAccountsCount }} 个）
              </template>
            </p>
          </div>
        </div>

        <!-- M3E FAB 风格操作控制区 -->
        <div class="flex flex-wrap items-center gap-3">
          <select
            v-if="store.accounts.length > 1 || store.role === 'admin'"
            v-model="selectedRunAccount"
            :disabled="store.scheduler.is_running"
            class="m3-input !rounded-full !px-4 !py-2.5 font-semibold"
          >
            <option v-if="store.role === 'admin'" value="">全部已启用账号 ({{ enabledAccountsCount }})</option>
            <option v-for="acc in store.accounts" :key="acc.id" :value="acc.id">
              仅运行：{{ acc.name }}
            </option>
          </select>

          <button
            v-if="!store.scheduler.is_running"
            type="button"
            :disabled="startingRun"
            class="m3-btn m3-btn-filled px-6 py-3 text-sm shadow-sm disabled:opacity-55"
            @click="handleStartRun"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.84A1.5 1.5 0 0 0 4 4.11v11.78a1.5 1.5 0 0 0 2.3 1.27l9.344-5.891a1.5 1.5 0 0 0 0-2.538L6.3 2.841Z" />
            </svg>
            <span>{{ selectedRunAccount ? '运行选中账号' : (store.role === 'admin' ? '立即运行队列' : '立即运行账号') }}</span>
          </button>

          <button
            v-else
            type="button"
            :disabled="stoppingRun"
            class="m3-btn m3-btn-error px-6 py-3 text-sm shadow-sm disabled:opacity-55"
            @click="handleStopRun"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <rect x="4" y="4" width="12" height="12" rx="2" />
            </svg>
            <span>{{ stoppingRun ? '正在停止...' : '停止当前任务' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 移动端 M3E Segmented Button 分栏切换 -->
    <div
      class="flex lg:hidden p-1 rounded-full border"
      style="background-color: var(--m3-surface-container); border-color: var(--m3-outline-variant);"
    >
      <button
        type="button"
        class="flex-1 py-2 rounded-full text-xs font-bold transition-all"
        :style="mobileTab === 'log'
          ? { backgroundColor: 'var(--m3-secondary-container)', color: 'var(--m3-on-secondary-container)' }
          : { color: 'var(--m3-on-surface-variant)' }"
        @click="mobileTab = 'log'"
      >
        实时终端日志
      </button>
      <button
        type="button"
        class="flex-1 py-2 rounded-full text-xs font-bold transition-all"
        :style="mobileTab === 'history'
          ? { backgroundColor: 'var(--m3-secondary-container)', color: 'var(--m3-on-secondary-container)' }
          : { color: 'var(--m3-on-surface-variant)' }"
        @click="mobileTab = 'history'"
      >
        历史记录 ({{ historyList.length }})
      </button>
    </div>

    <!-- 主体分栏：左侧历史记录 + 右侧增量日志终端 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
      <!-- 左侧：M3E 历史运行列表 -->
      <div
        class="lg:col-span-4 m3-card flex flex-col overflow-hidden h-[calc(100vh-17.5rem)] min-h-[440px]"
        :class="mobileTab === 'history' ? 'flex' : 'hidden lg:flex'"
      >
        <div
          class="px-5 py-4 border-b flex items-center justify-between"
          style="border-color: color-mix(in srgb, var(--m3-outline-variant) 45%, transparent);"
        >
          <div class="flex items-center gap-2.5">
            <span class="font-extrabold text-sm" style="color: var(--m3-on-surface);">执行历史</span>
            <span
              class="px-2.5 py-0.5 text-[11px] rounded-full font-bold"
              style="background-color: var(--m3-secondary-container); color: var(--m3-on-secondary-container);"
            >
              {{ historyList.length }}
            </span>
          </div>
          <button
            type="button"
            class="m3-btn m3-btn-tonal px-3 py-1 text-xs"
            @click="fetchHistory"
          >
            刷新
          </button>
        </div>

        <div
          v-if="historyList.length === 0"
          class="flex-1 flex flex-col items-center justify-center p-6 text-center text-xs"
          style="color: var(--m3-on-surface-variant);"
        >
          暂无历史运行记录
        </div>

        <div v-else class="flex-1 overflow-y-auto p-2.5 space-y-1.5">
          <button
            v-for="item in historyList"
            :key="item.run_id"
            type="button"
            class="w-full text-left px-4 py-3.5 rounded-[20px] transition-all flex items-start justify-between gap-2"
            :style="selectedLogFile === item.log_file
              ? { backgroundColor: 'var(--m3-secondary-container)', color: 'var(--m3-on-secondary-container)' }
              : { backgroundColor: 'transparent', color: 'var(--m3-on-surface)' }"
            @click="selectHistoryLog(item)"
          >
            <div class="min-w-0">
              <div class="font-bold text-xs sm:text-sm truncate">
                {{ item.account_name || item.account_id }}
              </div>
              <div class="mt-1 text-[11px] font-mono opacity-75">
                {{ item.start_time }}
              </div>
              <div v-if="item.end_time" class="text-[11px] opacity-75">
                耗时: {{ formatDuration(item.start_time, item.end_time) }}
              </div>
            </div>

            <span
              class="px-2.5 py-0.5 rounded-full text-[11px] font-bold shrink-0"
              :style="statusChipStyle(item.status)"
            >
              {{ statusText(item.status) }}
            </span>
          </button>
        </div>
      </div>

      <!-- 右侧：M3E 增量日志阅读器 -->
      <div
        class="lg:col-span-8 bg-[#121117] text-slate-100 rounded-[28px] border flex flex-col overflow-hidden h-[calc(100vh-17.5rem)] min-h-[440px] shadow-inner"
        style="border-color: color-mix(in srgb, var(--m3-outline-variant) 45%, transparent);"
        :class="mobileTab === 'log' ? 'flex' : 'hidden lg:flex'"
      >
        <!-- 日志工具栏 -->
        <div class="px-4 py-3 bg-[#1b1922] border-b border-white/10 flex flex-wrap items-center justify-between gap-2.5">
          <div class="flex flex-wrap items-center gap-1.5">
            <button
              v-for="lv in levelOptions"
              :key="lv.value"
              type="button"
              class="m3-btn px-3 py-1 text-[11px] font-bold"
              :class="activeLevel === lv.value ? lv.activeClass : 'bg-white/5 text-slate-400 hover:text-slate-200'"
              @click="activeLevel = lv.value"
            >
              {{ lv.label }}
            </button>
          </div>

          <div class="flex items-center gap-2 flex-1 sm:flex-initial justify-end">
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索日志关键字..."
              class="w-36 sm:w-52 px-3.5 py-1.5 rounded-full bg-white/8 border border-white/10 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-400"
            />
            <button
              v-if="selectedLogFile"
              type="button"
              class="m3-btn px-3.5 py-1.5 bg-white/10 hover:bg-white/15 text-slate-200 text-xs shrink-0"
              title="下载原始日志文件"
              @click="downloadCurrentLog"
            >
              ⬇ 下载
            </button>
          </div>
        </div>

        <!-- 当前查看的文件信息条 -->
        <div class="px-4 py-1.5 bg-black/30 border-b border-white/5 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span class="truncate">{{ selectedLogFile || '尚未选择日志文件' }}</span>
          <span v-if="logTruncated" class="text-amber-300 shrink-0 ml-2">已截取尾部最新 128KB</span>
        </div>

        <!-- 日志内容滚动区 -->
        <div
          ref="logContainerRef"
          class="flex-1 overflow-y-auto p-3.5 sm:p-4 font-mono text-xs leading-relaxed space-y-1 relative"
          @scroll="handleLogScroll"
        >
          <div v-if="!selectedLogFile" class="h-full flex items-center justify-center text-slate-500 text-xs">
            点击右上角「立即运行」或从左侧选择一条历史记录查看日志
          </div>
          <div v-else-if="filteredLogEntries.length === 0" class="h-full flex items-center justify-center text-slate-500 text-xs">
            暂无匹配的日志输出
          </div>

          <template v-else>
            <div v-for="entry in filteredLogEntries" :key="entry.id">
              <!-- 阶段分割胶囊横幅 -->
              <div
                v-if="entry.isStage"
                class="my-2.5 py-1.5 px-3.5 rounded-2xl bg-purple-500/15 border border-purple-400/25 text-purple-200 font-bold text-xs flex items-center gap-2"
              >
                <span class="w-2 h-2 rounded-full bg-purple-400"></span>
                <span>{{ entry.text }}</span>
              </div>

              <!-- 普通日志行 -->
              <div
                v-else
                class="flex items-start gap-2 px-2 py-0.5 rounded-lg hover:bg-white/5 break-all"
                :class="{
                  'bg-rose-950/40 text-rose-200': entry.level === 'ERROR',
                  'bg-amber-950/30 text-amber-200': entry.level === 'WARNING',
                  'text-slate-400': entry.level === 'DEBUG',
                }"
              >
                <span v-if="entry.time" class="text-slate-500 shrink-0 select-none">{{ entry.time }}</span>
                <span
                  v-if="entry.level"
                  class="px-1.5 py-0.2 rounded-md text-[10px] font-bold shrink-0 select-none"
                  :class="{
                    'bg-rose-500/20 text-rose-300': entry.level === 'ERROR',
                    'bg-amber-500/20 text-amber-300': entry.level === 'WARNING',
                    'bg-emerald-500/15 text-emerald-300': entry.level === 'INFO',
                    'bg-slate-700 text-slate-300': entry.level === 'DEBUG',
                  }"
                >
                  {{ entry.level }}
                </span>
                <span class="flex-1 whitespace-pre-wrap">{{ entry.text }}</span>
              </div>
            </div>
          </template>
        </div>

        <!-- 底部回到底部浮动提示 -->
        <div
          v-if="!autoScroll && selectedLogFile"
          class="px-5 py-2.5 text-xs font-bold flex items-center justify-between cursor-pointer"
          style="background-color: var(--m3-primary); color: var(--m3-on-primary);"
          @click="resumeAutoScroll"
        >
          <span>已暂停自动滚动（正在浏览历史行）</span>
          <span class="underline">↓ 回到最新底部</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { apiFetch, confirmModal, notify, refreshStatus, store } from '../../state.js'

const mobileTab = ref('log')
const selectedRunAccount = ref('')
const startingRun = ref(false)
const stoppingRun = ref(false)

const historyList = ref([])
const selectedLogFile = ref('')
const logEntries = ref([])
const logOffset = ref(0)
const logTruncated = ref(false)
const activeLevel = ref('ALL')
const searchKeyword = ref('')
const autoScroll = ref(true)
const logContainerRef = ref(null)

let lineSeq = 0
const MAX_DOM_LINES = 2500

const levelOptions = [
  { label: '全部', value: 'ALL', activeClass: 'bg-purple-600 text-white' },
  { label: 'INFO', value: 'INFO', activeClass: 'bg-emerald-600 text-white' },
  { label: 'WARN', value: 'WARNING', activeClass: 'bg-amber-600 text-white' },
  { label: 'ERROR', value: 'ERROR', activeClass: 'bg-rose-600 text-white' },
  { label: 'DEBUG', value: 'DEBUG', activeClass: 'bg-slate-600 text-white' },
]

const enabledAccountsCount = computed(() => {
  return store.accounts.filter((a) => a.enabled).length
})

const filteredLogEntries = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  return logEntries.value.filter((item) => {
    if (activeLevel.value !== 'ALL' && !item.isStage && item.level !== activeLevel.value) {
      return false
    }
    if (kw && !item.raw.toLowerCase().includes(kw)) {
      return false
    }
    return true
  })
})

function statusText(st) {
  const map = {
    running: '运行中',
    success: '成功',
    error: '失败',
    stopped: '已终止',
  }
  return map[st] || st || '未知'
}

function statusChipStyle(st) {
  if (st === 'success') {
    return { backgroundColor: 'var(--m3-success-container)', color: 'var(--m3-on-success-container)' }
  }
  if (st === 'error') {
    return { backgroundColor: 'var(--m3-error-container)', color: 'var(--m3-on-error-container)' }
  }
  if (st === 'running') {
    return { backgroundColor: 'var(--m3-tertiary-container)', color: 'var(--m3-on-tertiary-container)' }
  }
  return { backgroundColor: 'var(--m3-surface-container-highest)', color: 'var(--m3-on-surface-variant)' }
}

function formatDuration(startStr, endStr) {
  if (!startStr || !endStr) return '-'
  const s = new Date(startStr.replace(' ', 'T')).getTime()
  const e = new Date(endStr.replace(' ', 'T')).getTime()
  if (isNaN(s) || isNaN(e) || e < s) return '-'
  const sec = Math.round((e - s) / 1000)
  if (sec < 60) return `${sec}秒`
  const m = Math.floor(sec / 60)
  const rem = sec % 60
  return `${m}分${rem}秒`
}

function parseLogLine(rawLine) {
  const trimmed = rawLine.trim()
  if (!trimmed) return null

  if (
    trimmed.includes('────────') ||
    (trimmed.startsWith('==========') && trimmed.endsWith('=========='))
  ) {
    const cleanStage = trimmed.replace(/[─=]+/g, '').trim()
    return {
      id: ++lineSeq,
      raw: rawLine,
      isStage: true,
      level: 'INFO',
      time: '',
      text: cleanStage || trimmed,
    }
  }

  const pipeMatch = rawLine.match(/^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*\|\s*(INFO|WARNING|WARN|ERROR|DEBUG|CRITICAL)\s*\|\s*(.*)$/i)
  if (pipeMatch) {
    const rawLv = pipeMatch[2].toUpperCase()
    const normLv = rawLv === 'WARN' ? 'WARNING' : (rawLv === 'CRITICAL' ? 'ERROR' : rawLv)
    const msgText = pipeMatch[3]
    if (msgText.includes('────────')) {
      return {
        id: ++lineSeq,
        raw: rawLine,
        isStage: true,
        level: 'INFO',
        time: pipeMatch[1].split(/\s+/)[1] || '',
        text: msgText.replace(/[─]+/g, '').trim(),
      }
    }
    return {
      id: ++lineSeq,
      raw: rawLine,
      isStage: false,
      time: pipeMatch[1].split(/\s+/)[1] || pipeMatch[1],
      level: normLv,
      text: msgText,
    }
  }

  let guessedLevel = 'INFO'
  if (/error|exception|traceback|失败|异常/i.test(rawLine)) guessedLevel = 'ERROR'
  else if (/warn|警告/i.test(rawLine)) guessedLevel = 'WARNING'
  else if (/debug/i.test(rawLine)) guessedLevel = 'DEBUG'

  return {
    id: ++lineSeq,
    raw: rawLine,
    isStage: false,
    time: '',
    level: guessedLevel,
    text: rawLine,
  }
}

function appendRawLogContent(content, reset = false) {
  if (reset) {
    logEntries.value = []
    lineSeq = 0
  }
  if (!content) return
  const lines = content.split(/\r?\n/)
  const parsed = []
  for (const line of lines) {
    const entry = parseLogLine(line)
    if (entry) parsed.push(entry)
  }
  if (parsed.length > 0) {
    const combined = logEntries.value.concat(parsed)
    logEntries.value = combined.length > MAX_DOM_LINES
      ? combined.slice(combined.length - MAX_DOM_LINES)
      : combined
    if (autoScroll.value) {
      scrollToBottom()
    }
  }
}

function scrollToBottom() {
  nextTick(() => {
    const el = logContainerRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

function handleLogScroll() {
  const el = logContainerRef.value
  if (!el) return
  const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  autoScroll.value = distanceToBottom < 48
}

function resumeAutoScroll() {
  autoScroll.value = true
  scrollToBottom()
}

async function fetchHistory() {
  try {
    const list = await apiFetch('/api/history')
    historyList.value = Array.isArray(list) ? list : []
    if (!selectedLogFile.value) {
      if (store.scheduler.current_log_file) {
        selectLogFile(store.scheduler.current_log_file)
      } else if (historyList.value.length > 0) {
        selectLogFile(historyList.value[0].log_file)
      }
    }
  } catch {
    // ignore
  }
}

async function selectLogFile(logFile) {
  if (!logFile) return
  selectedLogFile.value = logFile
  logOffset.value = 0
  logTruncated.value = false
  autoScroll.value = true
  await pollLogChunk(true)
}

function selectHistoryLog(item) {
  selectLogFile(item.log_file)
  mobileTab.value = 'log'
}

async function pollLogChunk(isInitial = false) {
  if (!selectedLogFile.value) return
  try {
    const offsetParam = isInitial ? -1 : logOffset.value
    const res = await apiFetch(
      `/api/logs/${encodeURIComponent(selectedLogFile.value)}?offset=${offsetParam}`
    )
    if (isInitial) {
      logTruncated.value = Boolean(res.truncated)
      appendRawLogContent(res.content || '', true)
    } else if (res.content) {
      appendRawLogContent(res.content, false)
    }
    if (typeof res.next_offset === 'number') {
      logOffset.value = res.next_offset
    }
  } catch {
    // ignore
  }
}

async function handleStartRun() {
  startingRun.value = true
  try {
    const payload = selectedRunAccount.value ? { account_id: selectedRunAccount.value } : {}
    const res = await apiFetch('/api/run/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    notify(res.message || '任务已启动', 'success')
    await refreshStatus()
    await fetchHistory()
    if (store.scheduler.current_log_file) {
      selectLogFile(store.scheduler.current_log_file)
    }
  } catch (e) {
    notify(e.message || '启动失败', 'error')
  } finally {
    startingRun.value = false
  }
}

async function handleStopRun() {
  const ok = await confirmModal({
    title: '停止当前任务',
    message: '确定要立即终止正在执行的云游戏任务并清理后台浏览器进程吗？',
    confirmText: '立即停止',
    danger: true,
  })
  if (!ok) return

  stoppingRun.value = true
  try {
    const res = await apiFetch('/api/run/stop', { method: 'POST' })
    notify(res.message || '已发送停止指令', 'warning')
    await refreshStatus()
    await fetchHistory()
  } catch (e) {
    notify(e.message || '停止失败', 'error')
  } finally {
    stoppingRun.value = false
  }
}

function downloadCurrentLog() {
  if (!selectedLogFile.value) return
  const url = `/api/logs/${encodeURIComponent(selectedLogFile.value)}/download?token=${encodeURIComponent(store.token)}`
  window.open(url, '_blank')
}

watch(
  () => store.scheduler.current_log_file,
  (newFile) => {
    if (newFile && newFile !== selectedLogFile.value) {
      selectLogFile(newFile)
      fetchHistory()
    }
  }
)

let pollTimer = null
onMounted(async () => {
  await refreshStatus()
  if (store.role !== 'admin' && store.primaryAccountId) {
    selectedRunAccount.value = store.primaryAccountId
  }
  await fetchHistory()
  pollTimer = setInterval(async () => {
    await pollLogChunk(false)
    if (store.scheduler.is_running) {
      await fetchHistory()
    }
  }, 2000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>
