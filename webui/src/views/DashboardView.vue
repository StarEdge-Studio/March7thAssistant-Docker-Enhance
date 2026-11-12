<template>
  <div class="space-y-4">
    <!-- 顶部状态与任务控制卡片 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 shadow-xs">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div class="flex items-start sm:items-center gap-3.5">
          <div
            class="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0"
            :class="store.scheduler.is_running
              ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
              : 'bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-400'"
          >
            <svg v-if="store.scheduler.is_running" class="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"></path>
            </svg>
            <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
            </svg>
          </div>

          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
                {{ store.scheduler.is_running ? `正在运行：${store.scheduler.current_account_name || '任务队列'}` : '自动化调度中心 · 空闲待命' }}
              </h2>
              <span
                v-if="store.scheduler.settings?.daily_run_enabled"
                class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300"
              >
                ⏰ 每日 {{ store.scheduler.settings.daily_run_time }} 定时执行
              </span>
              <span
                v-if="store.scheduler.settings?.debug_mode"
                class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-300"
              >
                🐞 调试模拟模式
              </span>
            </div>
            <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              <template v-if="store.scheduler.internet_retry_info">
                网络连通性等待重试中（第 {{ store.scheduler.internet_retry_info.retry }}/{{ store.scheduler.internet_retry_info.max_retries }} 次）...
              </template>
              <template v-else-if="store.scheduler.is_running">
                当前运行编号: <span class="font-mono">{{ store.scheduler.current_run_id }}</span>
              </template>
              <template v-else>
                共 {{ store.accounts.length }} 个账号（已启用 {{ enabledAccountsCount }} 个）
              </template>
            </p>
          </div>
        </div>

        <!-- 操作控制区 -->
        <div v-if="canManualRun() || store.scheduler.is_running" class="flex flex-wrap items-center gap-2.5">
          <select
            v-if="canManualRun() && (store.accounts.length > 1 || store.role === 'admin')"
            v-model="selectedRunAccount"
            :disabled="store.scheduler.is_running"
            class="px-3 py-2 rounded-xl text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">
              {{ store.role === 'admin' ? `全部已启用账号 (${enabledAccountsCount})` : `我的全部已启用账号 (${enabledAccountsCount})` }}
            </option>
            <option v-for="acc in store.accounts" :key="acc.id" :value="acc.id">
              仅运行：{{ acc.name }}
            </option>
          </select>

          <button
            v-if="!store.scheduler.is_running && canManualRun()"
            type="button"
            :disabled="startingRun"
            class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-60 shadow-sm shadow-indigo-500/20 flex items-center gap-1.5 transition"
            @click="handleStartRun"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.84A1.5 1.5 0 0 0 4 4.11v11.78a1.5 1.5 0 0 0 2.3 1.27l9.344-5.891a1.5 1.5 0 0 0 0-2.538L6.3 2.841Z" />
            </svg>
            <span>{{ selectedRunAccount ? '运行选中账号' : (store.role === 'admin' ? '立即运行队列' : '立即运行账号') }}</span>
          </button>

          <button
            v-else-if="store.scheduler.is_running && (store.role === 'admin' || (canManualRun() && store.accountIds.includes(store.scheduler.current_account_id)))"
            type="button"
            :disabled="stoppingRun"
            class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-white bg-rose-600 hover:bg-rose-500 disabled:opacity-60 shadow-sm flex items-center gap-1.5 transition"
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

    <!-- 移动端分栏切换按钮 -->
    <div class="flex lg:hidden bg-slate-200/70 dark:bg-slate-800/80 p-1 rounded-xl">
      <button
        type="button"
        class="flex-1 py-1.5 rounded-lg text-xs font-semibold transition"
        :class="mobileTab === 'log'
          ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-xs'
          : 'text-slate-600 dark:text-slate-400'"
        @click="mobileTab = 'log'"
      >
        实时终端日志
      </button>
      <button
        type="button"
        class="flex-1 py-1.5 rounded-lg text-xs font-semibold transition"
        :class="mobileTab === 'history'
          ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-xs'
          : 'text-slate-600 dark:text-slate-400'"
        @click="mobileTab = 'history'"
      >
        历史记录 ({{ historyList.length }})
      </button>
    </div>

    <!-- 主体分栏：左侧历史记录 + 右侧增量日志终端 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <!-- 左侧：历史运行列表 -->
      <div
        class="lg:col-span-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 flex flex-col overflow-hidden h-[calc(100vh-16rem)] min-h-[420px]"
        :class="mobileTab === 'history' ? 'flex' : 'hidden lg:flex'"
      >
        <div class="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="font-bold text-sm text-slate-900 dark:text-white">执行历史</span>
            <span class="px-2 py-0.5 text-[11px] rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {{ historyList.length }}
            </span>
          </div>
          <button
            type="button"
            class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
            @click="fetchHistory"
          >
            刷新
          </button>
        </div>

        <div v-if="historyList.length === 0" class="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-400 dark:text-slate-500 text-xs">
          暂无历史运行记录
        </div>

        <div v-else class="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/70">
          <button
            v-for="item in historyList"
            :key="item.run_id"
            type="button"
            class="w-full text-left px-4 py-3 transition hover:bg-slate-50 dark:hover:bg-slate-800/50 flex items-start justify-between gap-2"
            :class="selectedLogFile === item.log_file ? 'bg-indigo-50/70 dark:bg-indigo-500/10 border-l-4 border-indigo-500' : ''"
            @click="selectHistoryLog(item)"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-semibold text-xs sm:text-sm text-slate-800 dark:text-slate-200 truncate">
                  {{ item.account_name || item.account_id }}
                </span>
              </div>
              <div class="mt-1 text-[11px] text-slate-400 dark:text-slate-500 font-mono">
                {{ item.start_time }}
              </div>
              <div v-if="item.end_time" class="text-[11px] text-slate-400 dark:text-slate-500">
                耗时: {{ formatDuration(item.start_time, item.end_time) }}
              </div>
            </div>

            <span
              class="px-2 py-0.5 rounded-full text-[11px] font-semibold shrink-0"
              :class="{
                'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300': item.status === 'success',
                'bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300': item.status === 'error',
                'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300': item.status === 'stopped',
                'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300 animate-pulse': item.status === 'running',
              }"
            >
              {{ statusText(item.status) }}
            </span>
          </button>
        </div>
      </div>

      <!-- 右侧：高性能增量日志阅读器 -->
      <div
        class="lg:col-span-8 bg-slate-950 text-slate-100 rounded-2xl border border-slate-800 flex flex-col overflow-hidden h-[calc(100vh-16rem)] min-h-[420px] shadow-inner"
        :class="mobileTab === 'log' ? 'flex' : 'hidden lg:flex'"
      >
        <!-- 日志工具栏 -->
        <div class="px-3.5 py-2.5 bg-slate-900 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-1.5">
            <button
              v-for="lv in levelOptions"
              :key="lv.value"
              type="button"
              class="px-2.5 py-1 rounded-lg text-[11px] font-semibold transition"
              :class="activeLevel === lv.value
                ? lv.activeClass
                : 'bg-slate-800 text-slate-400 hover:text-slate-200'"
              @click="activeLevel = lv.value"
            >
              {{ lv.label }}
            </button>

            <!-- 分割线 -->
            <div class="h-4 w-px bg-slate-700 mx-0.5"></div>

            <!-- DEBUG 独立切换开关（作显著视觉区分） -->
            <button
              type="button"
              class="px-2 py-1 rounded-lg text-[11px] font-semibold flex items-center gap-1.5 transition border"
              :class="showDebug
                ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40 shadow-xs'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200 border-transparent'"
              :title="showDebug ? 'DEBUG 调试日志已开启（全部视图中可见）' : '点击开启 DEBUG 调试日志（默认隐藏）'"
              @click="showDebug = !showDebug"
            >
              <span
                class="w-1.5 h-1.5 rounded-full transition-all duration-200"
                :class="showDebug ? 'bg-cyan-400' : 'bg-slate-500'"
              ></span>
              <span>DEBUG</span>
              <span
                class="text-[9px] px-1 py-0.2 rounded font-mono font-bold"
                :class="showDebug ? 'bg-cyan-500/25 text-cyan-200' : 'bg-slate-700 text-slate-400'"
              >
                {{ showDebug ? 'ON' : 'OFF' }}
              </span>
            </button>
          </div>

          <div class="flex items-center gap-2 flex-1 sm:flex-initial justify-end">
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索日志关键字..."
              class="w-36 sm:w-48 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              v-if="selectedLogFile"
              type="button"
              class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition shrink-0"
              title="下载原始日志文件"
              @click="downloadCurrentLog"
            >
              ⬇ 下载
            </button>
          </div>
        </div>

        <!-- 当前查看的文件信息条 -->
        <div class="px-4 py-1.5 bg-slate-900/60 border-b border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span class="truncate">{{ selectedLogFile || '尚未选择日志文件' }}</span>
          <span v-if="logTruncated" class="text-amber-400 shrink-0 ml-2">已截取尾部最新 128KB</span>
        </div>

        <!-- 日志内容滚动区 -->
        <div
          ref="logContainerRef"
          class="flex-1 overflow-y-auto p-3 sm:p-4 font-mono text-xs leading-relaxed space-y-1 relative"
          @scroll="handleLogScroll"
        >
          <div v-if="!selectedLogFile" class="h-full flex items-center justify-center text-slate-500 text-xs">
            点击左上角「立即运行」或从左侧选择一条历史记录查看日志
          </div>
          <div v-else-if="filteredLogEntries.length === 0" class="h-full flex items-center justify-center text-slate-500 text-xs">
            暂无匹配的日志输出
          </div>

          <template v-else>
            <div
              v-for="entry in filteredLogEntries"
              :key="entry.id"
            >
              <!-- 阶段分割横幅 -->
              <div
                v-if="entry.isStage"
                class="my-2.5 py-1.5 px-3 rounded-lg bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 font-bold text-xs flex items-center gap-2"
              >
                <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
                <span>{{ entry.text }}</span>
              </div>

              <!-- 普通日志行 -->
              <div
                v-else
                class="flex items-start gap-2 px-1.5 py-0.5 rounded hover:bg-slate-900/80 break-all"
                :class="{
                  'bg-rose-950/35 text-rose-200': entry.level === 'ERROR',
                  'bg-amber-950/25 text-amber-200': entry.level === 'WARNING',
                  'text-slate-400': entry.level === 'DEBUG',
                }"
              >
                <span v-if="entry.time" class="text-slate-500 shrink-0 select-none">{{ entry.time }}</span>
                <span
                  v-if="entry.level"
                  class="px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 select-none"
                  :class="{
                    'bg-rose-500/20 text-rose-400': entry.level === 'ERROR',
                    'bg-amber-500/20 text-amber-400': entry.level === 'WARNING',
                    'bg-emerald-500/15 text-emerald-400': entry.level === 'INFO',
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
          class="px-4 py-2 bg-indigo-600/95 text-white text-xs font-semibold flex items-center justify-between cursor-pointer"
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
import { apiFetch, canManualRun, confirmModal, fetchHistory as globalFetchHistory, notify, refreshStatus, store } from '../state.js'

const mobileTab = ref('log')
const selectedRunAccount = ref('')
const startingRun = ref(false)
const stoppingRun = ref(false)

const historyList = ref([...(store.history || [])])
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
  { label: '全部', value: 'ALL', activeClass: 'bg-indigo-600 text-white' },
  { label: 'INFO', value: 'INFO', activeClass: 'bg-emerald-600 text-white' },
  { label: 'WARN', value: 'WARNING', activeClass: 'bg-amber-600 text-white' },
  { label: 'ERROR', value: 'ERROR', activeClass: 'bg-rose-600 text-white' },
]

// DEBUG 级别独立开关，默认关闭；开启状态下全部 (ALL) 里才会显示 debug
const showDebug = ref(localStorage.getItem('m7a_show_debug') === 'true')
watch(showDebug, (val) => {
  localStorage.setItem('m7a_show_debug', String(val))
})

const enabledAccountsCount = computed(() => {
  return store.accounts.filter((a) => a.enabled).length
})

const filteredLogEntries = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  return logEntries.value.filter((item) => {
    // 阶段分割横幅保留
    if (item.isStage) return true

    // 全部模式下，仅在开启 DEBUG 开关时才显示 DEBUG 日志，默认隐藏
    if (activeLevel.value === 'ALL') {
      if (!showDebug.value && item.level === 'DEBUG') {
        return false
      }
    } else if (item.level !== activeLevel.value) {
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

  // 匹配标准格式: 2026-11-11 04:00:01 | INFO | ... 或 [time] ERROR ...
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
    const list = await globalFetchHistory()
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
    // ignore transient poll errors
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
  // 1. 若已有缓存历史且尚未选定日志，立即自动选定最近的日志文件，提前渲染，避免界面等待
  if (!selectedLogFile.value) {
    if (store.scheduler.current_log_file) {
      selectLogFile(store.scheduler.current_log_file)
    } else if (historyList.value.length > 0) {
      selectLogFile(historyList.value[0].log_file)
    }
  }

  // 2. 并发拉取状态与最新历史记录（不串行阻塞）
  await Promise.allSettled([
    refreshStatus(),
    fetchHistory(),
  ])

  if (store.role !== 'admin' && store.accounts.length === 1 && store.primaryAccountId) {
    selectedRunAccount.value = store.primaryAccountId
  }

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
