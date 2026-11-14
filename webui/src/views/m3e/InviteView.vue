<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
    style="background-color: var(--m3-surface); color: var(--m3-on-surface);"
  >
    <!-- M3E 装饰性动态色块背景 -->
    <div
      class="m3-ambient-blob w-[420px] h-[420px] rounded-full blur-3xl opacity-45 pointer-events-none absolute -top-24 -left-24"
      style="background-color: var(--m3-primary-container);"
    ></div>
    <div
      class="m3-ambient-blob w-[380px] h-[380px] rounded-full blur-3xl opacity-45 pointer-events-none absolute -bottom-24 -right-24"
      style="background-color: var(--m3-tertiary-container); animation-delay: -4.5s;"
    ></div>

    <div
      class="m3-stagger-item w-full max-w-[460px] rounded-[36px] p-7 sm:p-9 shadow-xl border relative z-10 transition-all space-y-6"
      style="background-color: var(--m3-surface-container-low); border-color: color-mix(in srgb, var(--m3-outline-variant) 55%, transparent);"
    >
      <!-- 顶部品牌徽章 -->
      <div class="text-center">
        <div class="group/badge relative w-14 h-14 mx-auto cursor-default">
          <div
            class="w-14 h-14 rounded-[20px] rotate-12 group-hover/badge:rotate-18 group-hover/badge:scale-105 transition-transform duration-300 absolute inset-0"
            style="background-color: var(--m3-tertiary-container); transition-timing-function: var(--m3-spring);"
          ></div>
          <div
            class="relative w-14 h-14 rounded-[20px] group-hover/badge:rounded-[15px] group-hover/badge:-rotate-3 transition-all duration-300 flex items-center justify-center font-black text-2xl shadow-md"
            style="background-color: var(--m3-primary); color: var(--m3-on-primary); transition-timing-function: var(--m3-spring);"
          >
            7
          </div>
        </div>
        <h1 class="mt-4 text-xl font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
          三月七小助手 · 账号受邀绑定
        </h1>
      </div>

      <!-- 步骤指示条 -->
      <div
        v-if="!loadError && (step !== 'welcome' || invite.status === 'active')"
        class="grid grid-cols-3 gap-2 pt-1"
      >
        <div
          v-for="(s, idx) in stepItems"
          :key="s.key"
          class="flex flex-col items-center gap-1.5 text-center"
        >
          <div
            class="w-full h-1.5 rounded-full transition-colors duration-300"
            :style="{
              backgroundColor: currentStepIndex >= idx
                ? 'var(--m3-primary)'
                : 'var(--m3-surface-container-highest)',
            }"
          ></div>
          <span
            class="text-[11px] font-bold"
            :style="{
              color: currentStepIndex >= idx
                ? 'var(--m3-primary)'
                : 'var(--m3-on-surface-variant)',
            }"
          >
            {{ idx + 1 }}. {{ s.label }}
          </span>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loadingInvite" class="py-10 flex flex-col items-center justify-center gap-3">
        <div
          class="w-9 h-9 border-3 border-t-transparent rounded-full animate-spin"
          style="border-color: var(--m3-primary); border-top-color: transparent;"
        ></div>
        <span class="text-xs font-medium" style="color: var(--m3-on-surface-variant);">
          正在验证邀请链接...
        </span>
      </div>

      <!-- 邀请链接不存在或报错 -->
      <div v-else-if="loadError" class="space-y-5 text-center py-4">
        <div
          class="p-4 rounded-[22px] text-xs font-semibold"
          style="background-color: var(--m3-error-container); color: var(--m3-on-error-container);"
        >
          {{ loadError }}
        </div>
        <button
          type="button"
          class="m3-btn m3-btn-tonal w-full py-3 text-sm"
          @click="goToLogin"
        >
          返回登录页
        </button>
      </div>

      <!-- 阶段 1：欢迎与点击「登录并绑定」 -->
      <div v-else-if="step === 'welcome'" class="space-y-5">
        <div
          class="p-5 rounded-[24px] space-y-2.5 text-center"
          style="background-color: var(--m3-surface-container-high);"
        >
          <div class="text-xs font-semibold" style="color: var(--m3-on-surface-variant);">
            管理员邀请您认领并托管游戏账号
          </div>
          <div class="text-lg font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
            {{ invite.account_name }}
          </div>
          <div class="text-[11px] font-mono" style="color: var(--m3-on-surface-variant);">
            有效期至：{{ invite.expires_at_str || '7 天内有效' }}
          </div>
        </div>

        <!-- 链接非可用状态提示 -->
        <template v-if="invite.status !== 'active'">
          <div
            class="p-4 rounded-[20px] text-xs font-bold text-center"
            style="background-color: var(--m3-error-container); color: var(--m3-on-error-container);"
          >
            {{ inviteUnavailableReason }}
          </div>
          <button
            type="button"
            class="m3-btn m3-btn-tonal w-full py-3 text-sm"
            @click="goToLogin"
          >
            前往登录页
          </button>
        </template>

        <template v-else>
          <div
            v-if="actionError"
            class="p-3.5 rounded-[18px] text-xs font-medium"
            style="background-color: var(--m3-error-container); color: var(--m3-on-error-container);"
          >
            {{ actionError }}
          </div>

          <button
            type="button"
            :disabled="submittingClaim"
            class="m3-btn m3-btn-filled w-full py-3.5 px-6 text-sm shadow-sm disabled:opacity-55"
            @click="handleLoginAndBind"
          >
            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
            </svg>
            <span>
              {{ submittingClaim ? '正在处理...' : (invite.auth_mode === 'oidc' ? `使用 ${invite.auth_brand || 'OIDC'} 登录并绑定` : '登录并绑定') }}
            </span>
          </button>

          <p class="text-[11px] text-center leading-relaxed" style="color: var(--m3-on-surface-variant);">
            <template v-if="invite.auth_mode === 'oidc'">
              点击后将跳转至 {{ invite.auth_brand || 'OIDC' }} 统一认证中心，登录成功后自动将该游戏账号绑定至您的名下。
            </template>
            <template v-else>
              点击后将为您激活该账号的专属访问密钥，并引导您完成云游戏扫码登录。
            </template>
          </p>
        </template>
      </div>

      <!-- 阶段 1.5（仅 Token 模式）：提示用户保存专属 Token -->
      <div v-else-if="step === 'save_token'" class="space-y-5">
        <div
          class="p-4 rounded-[20px] text-xs font-bold leading-relaxed"
          style="background-color: var(--m3-primary-container); color: var(--m3-on-primary-container);"
        >
          账号「{{ invite.account_name }}」已绑定！请务必复制并妥善保存下方您的专属登录密钥（Token），后续凭此密钥即可直接登录管理。
        </div>

        <div
          class="p-4 rounded-[22px] space-y-2.5"
          style="background-color: var(--m3-surface-container-highest);"
        >
          <div class="text-[11px] font-bold" style="color: var(--m3-on-surface-variant);">
            您的账号专属登录密钥 (Token)
          </div>
          <div class="font-mono text-xs sm:text-sm font-bold break-all select-all p-2.5 rounded-[14px]" style="background-color: var(--m3-surface-container-lowest); color: var(--m3-on-surface);">
            {{ claimedSecretKey }}
          </div>
          <button
            type="button"
            class="m3-btn m3-btn-tonal w-full py-2.5 text-xs"
            @click="copyToken"
          >
            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
            </svg>
            <span>{{ tokenCopied ? '已复制专属密钥' : '复制专属密钥' }}</span>
          </button>
        </div>

        <button
          type="button"
          class="m3-btn m3-btn-filled w-full py-3.5 px-6 text-sm shadow-sm"
          @click="proceedToQrStep"
        >
          <span>我已保存密钥，下一步：扫码登录游戏</span>
        </button>
      </div>

      <!-- 阶段 2：扫码登录云·星穹铁道 -->
      <div v-else-if="step === 'qr'" class="space-y-4 text-center">
        <div class="text-xs font-bold" style="color: var(--m3-on-surface);">
          请扫码登录游戏账号：{{ invite.account_name }}
        </div>

        <div
          class="p-3.5 rounded-[18px] text-xs font-bold transition-colors duration-300"
          :style="qrStatusStyle(qrState.status)"
        >
          {{ qrState.message }}
        </div>

        <div
          class="mx-auto w-56 h-56 rounded-[24px] border flex items-center justify-center overflow-hidden"
          style="background-color: var(--m3-surface-container-lowest); border-color: var(--m3-outline-variant);"
        >
          <!-- 扫码成功或登录成功：隐藏二维码并显示绿色对号与提示 -->
          <div
            v-if="qrState.status === 'scanned' || qrState.status === 'success'"
            class="flex flex-col items-center gap-3 px-4 text-center animate-fade-in"
            style="color: var(--m3-success);"
          >
            <div
              class="w-16 h-16 rounded-[22px] flex items-center justify-center shadow-xs"
              style="background-color: var(--m3-success-container); color: var(--m3-on-success-container);"
            >
              <svg class="w-9 h-9" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            </div>
            <div class="space-y-0.5">
              <span class="text-sm font-extrabold block" style="color: var(--m3-on-surface);">
                {{
                  qrState.status === 'scanned'
                    ? '扫码成功'
                    : qrState.alreadyLoggedIn
                      ? '当前已登录'
                      : '登录成功'
                }}
              </span>
              <span class="text-xs" style="color: var(--m3-on-surface-variant);">
                {{
                  qrState.status === 'scanned'
                    ? '请在手机端点击「确认登录」'
                    : qrState.alreadyLoggedIn
                      ? '如需更换账号，请清除旧会话后重扫'
                      : '登录凭证已保存，正在跳转...'
                }}
              </span>
            </div>
          </div>

          <div v-else-if="qrState.status === 'failed'" class="flex flex-col items-center gap-2 px-4" style="color: var(--m3-error);">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
            <span class="text-xs">加载失败，可点击下方重试</span>
          </div>

          <img
            v-else-if="qrState.hasQr && qrState.imageUrl"
            :src="qrState.imageUrl"
            alt="登录二维码"
            class="w-full h-full object-contain p-2 bg-white"
          />

          <div v-else class="flex flex-col items-center gap-2.5" style="color: var(--m3-on-surface-variant);">
            <div
              class="w-8 h-8 border-3 border-t-transparent rounded-full animate-spin"
              style="border-color: var(--m3-primary); border-top-color: transparent;"
            ></div>
            <span class="text-xs">正在准备二维码...</span>
          </div>
        </div>

        <p class="text-[11px]" style="color: var(--m3-on-surface-variant);">
          {{
            qrState.status === 'scanned'
              ? '已成功识别二维码，请在手机米游社上点击「确认登录」。'
              : qrState.status === 'success' && qrState.alreadyLoggedIn
                ? '检测到已有登录状态。如需扫码更换其他账号，请点击「清除并重新登录」。'
                : '请使用手机「米游社 App」扫描上方二维码并在手机端点击确认登录。'
          }}
        </p>

        <div class="pt-1 flex flex-wrap justify-center gap-2.5">
          <button
            v-if="qrState.status === 'failed'"
            type="button"
            class="m3-btn m3-btn-filled px-5 py-2.5 text-xs"
            @click="startQrLogin(true)"
          >
            重新获取二维码
          </button>
          <button
            v-if="qrState.status === 'success' && qrState.alreadyLoggedIn"
            type="button"
            class="m3-btn m3-btn-filled px-5 py-2.5 text-xs"
            @click="startQrLogin(true)"
          >
            清除并重新登录
          </button>
          <button
            v-if="qrState.status === 'success' && qrState.alreadyLoggedIn"
            type="button"
            class="m3-btn m3-btn-tonal px-5 py-2.5 text-xs"
            @click="enterCongratsStep"
          >
            使用当前账号继续
          </button>
        </div>
      </div>

      <!-- 阶段 3：恭喜完成页 + 3秒倒计时自动跳转任务配置 -->
      <div v-else-if="step === 'congrats'" class="py-4 text-center space-y-5">
        <div
          class="mx-auto w-16 h-16 rounded-[22px] flex items-center justify-center"
          style="background-color: var(--m3-success-container); color: var(--m3-on-success-container);"
        >
          <svg class="w-9 h-9" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        </div>

        <div class="space-y-1.5">
          <h2 class="text-xl font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
            恭喜！账号绑定与登录已完成
          </h2>
          <p class="text-xs leading-relaxed" style="color: var(--m3-on-surface-variant);">
            游戏账号「{{ invite.account_name }}」已准备就绪，将在 <span class="font-bold" style="color: var(--m3-primary);">{{ countdown }}</span> 秒后自动为您跳转至任务配置页面...
          </p>
        </div>

        <button
          type="button"
          class="m3-btn m3-btn-filled w-full py-3.5 px-6 text-sm shadow-sm"
          @click="goToTasksNow"
        >
          <span>立即前往任务配置</span>
        </button>
      </div>

      <p class="pt-1 text-center text-xs font-bold leading-relaxed" style="color: var(--m3-error);">
        管理员将能完全控制您的游戏账号，请确保您完全信任对方
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch, copyText, notify, refreshStatus, setSession } from '../../state.js'

const route = useRoute()
const router = useRouter()

const loadingInvite = ref(true)
const loadError = ref('')
const actionError = ref('')
const submittingClaim = ref(false)
const step = ref('welcome') // 'welcome' | 'save_token' | 'qr' | 'congrats'
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
  alreadyLoggedIn: false,
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

function qrStatusStyle(status) {
  if (status === 'success') {
    return {
      backgroundColor: 'var(--m3-success-container)',
      color: 'var(--m3-on-success-container)',
    }
  }
  if (status === 'failed') {
    return {
      backgroundColor: 'var(--m3-error-container)',
      color: 'var(--m3-on-error-container)',
    }
  }
  return {
    backgroundColor: 'var(--m3-primary-container)',
    color: 'var(--m3-on-primary-container)',
  }
}

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

async function startQrLogin(resetSession = false) {
  stopQrPoll()
  qrState.status = 'starting'
  qrState.message = resetSession
    ? '正在清除旧登录凭证并重新获取二维码...'
    : '正在启动无头浏览器并加载云·星穹铁道登录页...'
  qrState.hasQr = false
  qrState.imageUrl = ''
  qrState.alreadyLoggedIn = false

  try {
    const query = resetSession ? '?reset_session=true' : ''
    await apiFetch(`/api/accounts/${invite.account_id}/qr_login/start${query}`, {
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
    if (step.value !== 'qr') return
    qrState.status = res.status
    qrState.message = res.message || ''
    qrState.hasQr = Boolean(res.has_qr)
    qrState.alreadyLoggedIn = Boolean(res.already_logged_in)
    if (res.has_qr) {
      qrState.imageUrl = `/api/accounts/${invite.account_id}/qr_login/image?token=${encodeURIComponent(localStorage.getItem('m7a_session_token') || '')}&t=${Date.now()}`
    }
    if (res.status === 'success') {
      stopQrPoll()
      await refreshStatus()
      if (!qrState.alreadyLoggedIn && step.value === 'qr') {
        enterCongratsStep()
      }
    } else if (res.status === 'failed') {
      stopQrPoll()
    }
  } catch {
    // ignore transient poll error
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
