<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
    <div class="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-xl space-y-5">
      <!-- 顶部标识 -->
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white font-black text-xl flex items-center justify-center mx-auto shadow-sm">
          7
        </div>
        <h1 class="mt-3 text-lg font-bold">三月七小助手 · 账号受邀绑定</h1>
      </div>

      <!-- 步骤进度条 -->
      <div v-if="!loadError && (step !== 'welcome' || invite.status === 'active')" class="grid grid-cols-3 gap-2">
        <div v-for="(s, idx) in stepItems" :key="s.key" class="flex flex-col items-center gap-1 text-center">
          <div
            class="w-full h-1.5 rounded-full transition-colors"
            :class="currentStepIndex >= idx ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
          ></div>
          <span
            class="text-[11px] font-semibold"
            :class="currentStepIndex >= idx ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'"
          >
            {{ idx + 1 }}. {{ s.label }}
          </span>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loadingInvite" class="py-8 flex flex-col items-center justify-center gap-2">
        <div class="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-xs text-slate-500">正在验证邀请链接...</span>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="loadError" class="space-y-4 text-center py-2">
        <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-300 text-xs font-medium">
          {{ loadError }}
        </div>
        <button
          type="button"
          class="w-full py-2.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 transition"
          @click="goToLogin"
        >
          返回登录页
        </button>
      </div>

      <!-- 阶段 1：欢迎与登录绑定 -->
      <div v-else-if="step === 'welcome'" class="space-y-4">
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/70 border border-slate-100 dark:border-slate-800 text-center space-y-1.5">
          <div class="text-xs text-slate-500 dark:text-slate-400">管理员邀请您认领并托管游戏账号</div>
          <div class="text-base font-bold">{{ invite.account_name }}</div>
          <div class="text-[11px] font-mono text-slate-400">有效期至：{{ invite.expires_at_str || '7 天内有效' }}</div>
        </div>

        <template v-if="invite.status !== 'active'">
          <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-300 text-xs font-semibold text-center">
            {{ inviteUnavailableReason }}
          </div>
          <button
            type="button"
            class="w-full py-2.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 transition"
            @click="goToLogin"
          >
            前往登录页
          </button>
        </template>

        <template v-else>
          <div v-if="actionError" class="p-3 rounded-xl bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-300 text-xs">
            {{ actionError }}
          </div>

          <button
            type="button"
            :disabled="submittingClaim"
            class="w-full py-3 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-55 transition shadow-sm"
            @click="handleLoginAndBind"
          >
            {{ submittingClaim ? '正在处理...' : (invite.auth_mode === 'oidc' ? `使用 ${invite.auth_brand || 'OIDC'} 登录并绑定` : '登录并绑定') }}
          </button>
        </template>
      </div>

      <!-- 阶段 1.5：Token 模式下提示保存密钥 -->
      <div v-else-if="step === 'save_token'" class="space-y-4">
        <div class="p-3.5 rounded-xl bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 text-xs font-medium leading-relaxed">
          账号「{{ invite.account_name }}」已绑定！请复制并妥善保存下方您的专属登录密钥（Token），后续凭此密钥即可直接登录管理。
        </div>

        <div class="p-3.5 rounded-xl bg-slate-100 dark:bg-slate-800 space-y-2">
          <div class="text-[11px] font-semibold text-slate-500">您的账号专属登录密钥 (Token)</div>
          <div class="font-mono text-xs font-bold break-all select-all p-2 rounded-lg bg-white dark:bg-slate-900">
            {{ claimedSecretKey }}
          </div>
          <button
            type="button"
            class="w-full py-2 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition"
            @click="copyToken"
          >
            {{ tokenCopied ? '已复制专属密钥' : '复制专属密钥' }}
          </button>
        </div>

        <button
          type="button"
          class="w-full py-3 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 transition"
          @click="proceedToQrStep"
        >
          我已保存密钥，下一步：扫码登录游戏
        </button>
      </div>

      <!-- 阶段 2：扫码登录游戏账号 -->
      <div v-else-if="step === 'qr'" class="space-y-4 text-center">
        <div class="text-xs font-bold">请扫码登录游戏账号：{{ invite.account_name }}</div>

        <div class="p-3 rounded-xl text-xs font-semibold bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300">
          {{ qrState.message }}
        </div>

        <div class="mx-auto w-52 h-52 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-center overflow-hidden">
          <!-- 扫码成功或登录成功：隐藏二维码并显示绿色对号与提示 -->
          <div v-if="qrState.status === 'scanned' || qrState.status === 'success'" class="text-emerald-500 flex flex-col items-center gap-2.5 px-4 text-center">
            <div class="w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            </div>
            <div class="space-y-0.5">
              <span class="text-sm font-bold text-slate-800 dark:text-slate-100 block">
                {{ qrState.status === 'success' ? '登录成功' : '扫码成功' }}
              </span>
              <span class="text-xs text-slate-500 dark:text-slate-400">
                {{ qrState.status === 'success' ? '登录凭证已保存，正在跳转...' : '请在手机端点击「确认登录」' }}
              </span>
            </div>
          </div>

          <div v-else-if="qrState.status === 'failed'" class="text-xs text-rose-600 px-4 text-center">
            加载失败，可点击下方重试
          </div>

          <img
            v-else-if="qrState.hasQr && qrState.imageUrl"
            :src="qrState.imageUrl"
            alt="登录二维码"
            class="w-full h-full object-contain p-2"
          />

          <div v-else class="flex flex-col items-center gap-2 text-slate-500">
            <div class="w-7 h-7 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-xs">正在准备二维码...</span>
          </div>
        </div>

        <p class="text-[11px] text-slate-500">
          {{ qrState.status === 'scanned' ? '已成功识别二维码，请在手机米游社上点击「确认登录」。' : '请使用手机「米游社 App」扫描上方二维码并在手机端点击确认登录。' }}
        </p>

        <button
          v-if="qrState.status === 'failed'"
          type="button"
          class="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500"
          @click="startQrLogin"
        >
          重新获取二维码
        </button>
      </div>

      <!-- 阶段 3：恭喜完成页 -->
      <div v-else-if="step === 'congrats'" class="py-3 text-center space-y-4">
        <div class="mx-auto w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        </div>

        <div class="space-y-1">
          <h2 class="text-lg font-bold">恭喜！账号绑定与登录已完成</h2>
          <p class="text-xs text-slate-500">
            游戏账号「{{ invite.account_name }}」已就绪，将在 <span class="font-bold text-indigo-600">{{ countdown }}</span> 秒后自动跳转至任务配置页面...
          </p>
        </div>

        <button
          type="button"
          class="w-full py-3 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500"
          @click="goToTasksNow"
        >
          立即前往任务配置
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch, copyText, notify, refreshStatus, setSession } from '../state.js'

const route = useRoute()
const router = useRouter()

const loadingInvite = ref(true)
const loadError = ref('')
const actionError = ref('')
const submittingClaim = ref(false)
const step = ref('welcome')
const claimedSecretKey = ref('')
const tokenCopied = ref(false)
const countdown = ref(3)

const invite = reactive({
  code: '',
  account_id: '',
  account_name: '',
  status: 'active',
  expires_at_str: '',
  auth_mode: 'token',
  auth_brand: 'SSO',
})

const qrState = reactive({
  status: 'starting',
  message: '正在启动无头浏览器并加载云·星穹铁道登录页...',
  hasQr: false,
  imageUrl: '',
})

let qrPollTimer = null
let countdownTimer = null

const stepItems = [
  { key: 'bind', label: '绑定身份' },
  { key: 'qr', label: '扫码登录' },
  { key: 'done', label: '完成配置' },
]

const currentStepIndex = computed(() => {
  if (step.value === 'welcome' || step.value === 'save_token') return 0
  if (step.value === 'qr') return 1
  return 2
})

const inviteUnavailableReason = computed(() => {
  if (invite.status === 'used') return '该邀请链接已被认领使用'
  if (invite.status === 'expired') return '该邀请链接已超过 7 天有效期，请联系管理员刷新链接'
  if (invite.status === 'invalid') return '该邀请链接关联的游戏账号已被删除'
  return '该邀请链接当前不可用'
})

function getCleanRedirectUri() {
  return `${window.location.origin}${window.location.pathname}`
}

async function loadInviteDetails() {
  loadingInvite.value = true
  loadError.value = ''
  const code = String(route.params.code || '').trim()
  if (!code) {
    loadError.value = '无效的邀请链接参数'
    loadingInvite.value = false
    return
  }
  try {
    const res = await apiFetch(`/api/invites/${encodeURIComponent(code)}`)
    Object.assign(invite, res)
    if (route.query.step === 'qr') {
      step.value = 'qr'
      await startQrLogin()
    }
  } catch (e) {
    loadError.value = e.message || '加载邀请链接信息失败'
  } finally {
    loadingInvite.value = false
  }
}

async function handleLoginAndBind() {
  actionError.value = ''
  submittingClaim.value = true
  try {
    if (invite.auth_mode === 'oidc') {
      sessionStorage.setItem('m7a_pending_invite_code', invite.code)
      const redirectUri = getCleanRedirectUri()
      const res = await apiFetch(
        `/api/auth/oidc/authorize?redirect_uri=${encodeURIComponent(redirectUri)}&invite_code=${encodeURIComponent(invite.code)}`
      )
      if (res.authorize_url) {
        window.location.href = res.authorize_url
        return
      }
      throw new Error('未获取到有效的 OIDC 授权跳转地址')
    } else {
      const res = await apiFetch(`/api/invites/${encodeURIComponent(invite.code)}/claim`, {
        method: 'POST',
      })
      setSession(res)
      claimedSecretKey.value = res.secret_key || ''
      step.value = 'save_token'
      await copyToken()
    }
  } catch (e) {
    actionError.value = e.message || '绑定失败，请稍后重试'
  } finally {
    submittingClaim.value = false
  }
}

async function copyToken() {
  if (!claimedSecretKey.value) return
  try {
    if (!(await copyText(claimedSecretKey.value))) throw new Error('copy failed')
    tokenCopied.value = true
    notify('专属密钥已复制到剪贴板', 'success')
  } catch {
    notify('自动复制失败，请手动选中复制', 'warning')
  }
}

async function proceedToQrStep() {
  step.value = 'qr'
  await startQrLogin()
}

function stopQrPoll() {
  if (qrPollTimer) {
    clearInterval(qrPollTimer)
    qrPollTimer = null
  }
}

async function startQrLogin() {
  stopQrPoll()
  qrState.status = 'starting'
  qrState.message = '正在启动无头浏览器并加载云·星穹铁道登录页...'
  qrState.hasQr = false
  qrState.imageUrl = ''

  try {
    await apiFetch(`/api/accounts/${invite.account_id}/qr_login/start`, {
      method: 'POST',
    })
    qrPollTimer = setInterval(() => {
      pollQrStatus()
    }, 1500)
  } catch (e) {
    qrState.status = 'failed'
    qrState.message = e.message || '启动扫码会话失败'
  }
}

async function pollQrStatus() {
  if (step.value !== 'qr' || !invite.account_id) return
  try {
    const res = await apiFetch(`/api/accounts/${invite.account_id}/qr_login/status`)
    qrState.status = res.status
    qrState.message = res.message || ''
    qrState.hasQr = Boolean(res.has_qr)
    if (res.has_qr) {
      qrState.imageUrl = `/api/accounts/${invite.account_id}/qr_login/image?token=${encodeURIComponent(localStorage.getItem('m7a_session_token') || '')}&t=${Date.now()}`
    }
    if (res.status === 'success') {
      stopQrPoll()
      await refreshStatus()
      enterCongratsStep()
    } else if (res.status === 'failed') {
      stopQrPoll()
    }
  } catch {
    // ignore
  }
}

function enterCongratsStep() {
  step.value = 'congrats'
  countdown.value = 3
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      goToTasksNow()
    }
  }, 1000)
}

function goToTasksNow() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  router.replace({ path: '/tasks', query: { account_id: invite.account_id } })
}

function goToLogin() {
  router.replace({ name: 'login' })
}

onMounted(() => {
  loadInviteDetails()
})

onUnmounted(() => {
  stopQrPoll()
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>
