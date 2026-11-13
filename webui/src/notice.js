import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { store } from './state.js'

export const ORIGINAL_REPO_URL = 'https://github.com/moesnow/March7thAssistant'
export const PROJECT_REPO_URL = 'https://github.com/staredge-studio/March7thAssistant-Docker-Enhance'
export const NOTICE_COUNTDOWN_SECONDS = 50

const STORAGE_KEY_PREFIX = 'm7a_notice_accepted_'
const STORAGE_VERSION = '_v1'

export function normalizeNoticeRole(role) {
  return role === 'admin' ? 'admin' : role === 'user' ? 'user' : ''
}

export function getNoticeStorageKey(role) {
  const normalized = normalizeNoticeRole(role)
  return normalized ? `${STORAGE_KEY_PREFIX}${normalized}${STORAGE_VERSION}` : ''
}

export function hasAcceptedNotice(role) {
  const key = getNoticeStorageKey(role)
  if (!key) return true
  try {
    return window.localStorage.getItem(key) === '1'
  } catch {
    return false
  }
}

export function markNoticeAccepted(role) {
  const key = getNoticeStorageKey(role)
  if (!key) return
  try {
    window.localStorage.setItem(key, '1')
  } catch {
    // 忽略隐私模式或存储受限异常
  }
}

const ADMIN_NOTICE = {
  badge: '管理员须知',
  title: '管理员控制台使用须知',
  subtitle: '首次进入管理控制台前，请认真阅读并知悉以下条款',
  sections: [
    {
      id: 'commercial',
      tone: 'danger',
      icon: 'ban',
      title: '严禁任何商业用途',
      items: [
        [
          { text: '原项目、本项目及所含全部功能' },
          { text: '仅供个人学习研究、自用或免费帮助身边朋友使用', highlight: 'yellow' },
          { text: '。' },
        ],
        [
          { text: '严禁以任何形式将本项目用于商业营利', highlight: 'red' },
          { text: '，包括但不限于：' },
          { text: '收费代肝/代练、商用云托管平台、售卖使用名额、倒卖邀请链接或登录凭证（Token）', highlight: 'yellow' },
          { text: '等。' },
        ],
      ],
    },
    {
      id: 'responsibility',
      tone: 'primary',
      icon: 'shield',
      title: '部署安全与管理规范',
      items: [
        [
          { text: '请妥善保管' },
          { text: '管理员 Token（WEBUI_TOKEN）与 OIDC 配置密钥', highlight: 'yellow' },
          { text: '；对外提供访问时' },
          { text: '建议启用 HTTPS 与严格的身份鉴权', highlight: 'yellow' },
          { text: '。' },
        ],
        [
          { text: '发放账号受邀绑定链接时，请确保受邀方为本人或可信亲友，并充分告知潜在账号风险；如发现' },
          { text: '违规分发或异常占用请及时清理', highlight: 'red' },
          { text: '。' },
        ],
      ],
    },
    {
      id: 'disclaimer',
      tone: 'neutral',
      icon: 'alert',
      title: '风险提示与免责声明',
      items: [
        [
          { text: '游戏自动化及模拟登录方案可能触发官方风控机制，存在' },
          { text: '被限制功能或封禁账号的风险', highlight: 'red' },
          { text: '，由此产生的一切后果' },
          { text: '由部署者与使用者自行承担', highlight: 'yellow' },
          { text: '。' },
        ],
      ],
    },
  ],
}

const USER_NOTICE = {
  badge: '用户须知',
  title: '使用须知与防骗提醒',
  subtitle: '首次进入控制台前，为保障您的账号与财产安全，请仔细阅读',
  sections: [
    {
      id: 'risk',
      tone: 'danger',
      icon: 'alert',
      title: '使用须知与封号风险提示',
      items: [
        [
          { text: '自动化脚本与云端模拟登录属于非官方辅助方式，可能触发游戏官方检测，存在' },
          { text: '限制登录、扣除收益乃至永久封号等风险', highlight: 'red' },
          { text: '。' },
        ],
        [
          { text: '请' },
          { text: '谨慎评估风险', highlight: 'yellow' },
          { text: '后再行使用；如不同意承担上述风险，请' },
          { text: '立即停止使用并联系管理员移除您的账号配置', highlight: 'yellow' },
          { text: '。' },
        ],
      ],
    },
    {
      id: 'commercial',
      tone: 'primary',
      icon: 'ban',
      title: '严禁商业使用',
      items: [
        [
          { text: '原项目、本项目及全部功能均基于开源协议' },
          { text: '免费提供，仅限个人自用或亲友间免费互助', highlight: 'yellow' },
          { text: '，' },
          { text: '严禁用于收费托管、商业代肝或任何营利性服务', highlight: 'red' },
          { text: '。' },
        ],
      ],
    },
    {
      id: 'antiscam',
      tone: 'danger',
      icon: 'shield',
      title: '防骗须知（重要）',
      items: [
        [
          { text: '本项目完全免费开源！', highlight: 'yellow' },
          { text: '如果您是通过付费购买软件、有偿代挂、购买邀请链接或付费 Token 等渠道进入本页面，请注意甄别' },
          { text: '诈骗、卷款跑路或恶意盗号风险', highlight: 'red' },
          { text: '；如已被收取费用，请' },
          { text: '立即保存凭证申请退款并举报卖家/收费者', highlight: 'red' },
          { text: '。' },
        ],
        [
          { text: '管理员将能完全控制您的游戏账号', highlight: 'red' },
          { text: '，请' },
          { text: '再次确保完全信任管理员', highlight: 'yellow' },
          { text: '，否则请打开' },
          { text: '「米游社 App」-「账号与安全」页面移除登录设备', highlight: 'red' },
          { text: '。' },
        ],
      ],
    },
  ],
}

export function normalizeNoticeSegments(item) {
  if (Array.isArray(item)) return item
  return [{ text: String(item ?? '') }]
}

export function getNoticeHighlightClass(tone) {
  if (tone === 'red') {
    return 'font-bold text-rose-600 dark:text-rose-400'
  }
  if (tone === 'yellow') {
    return 'rounded px-1 py-0.5 font-semibold bg-amber-300/65 text-amber-950 dark:bg-amber-400/25 dark:text-amber-200'
  }
  return ''
}

export function getNoticeContent(role) {
  return role === 'admin' ? ADMIN_NOTICE : USER_NOTICE
}

export function useNoticeModal(isStandaloneGetter) {
  const visible = ref(false)
  const activeRole = ref('')
  const countdown = ref(NOTICE_COUNTDOWN_SECONDS)
  let timerId = null

  const stopTimer = () => {
    if (timerId !== null) {
      window.clearInterval(timerId)
      timerId = null
    }
  }

  const startCountdown = () => {
    stopTimer()
    countdown.value = NOTICE_COUNTDOWN_SECONDS
    timerId = window.setInterval(() => {
      if (countdown.value <= 1) {
        countdown.value = 0
        stopTimer()
        return
      }
      countdown.value -= 1
    }, 1000)
  }

  const syncVisibility = () => {
    const isStandalone = Boolean(isStandaloneGetter())
    const role = normalizeNoticeRole(store.role)
    if (isStandalone || !store.token || !role) {
      stopTimer()
      visible.value = false
      activeRole.value = ''
      return
    }
    if (hasAcceptedNotice(role)) {
      stopTimer()
      visible.value = false
      activeRole.value = role
      return
    }
    if (!visible.value || activeRole.value !== role) {
      activeRole.value = role
      visible.value = true
      startCountdown()
    }
  }

  watch(
    [() => store.token, () => store.role, isStandaloneGetter],
    () => {
      syncVisibility()
    },
    { immediate: true },
  )

  onBeforeUnmount(() => {
    stopTimer()
  })

  const notice = computed(() => getNoticeContent(activeRole.value || store.role))
  const canConfirm = computed(() => countdown.value <= 0)

  const confirmNotice = () => {
    if (!canConfirm.value) return
    const role = activeRole.value || normalizeNoticeRole(store.role)
    markNoticeAccepted(role)
    stopTimer()
    visible.value = false
  }

  return {
    visible,
    countdown,
    canConfirm,
    notice,
    confirmNotice,
    originalRepoUrl: ORIGINAL_REPO_URL,
    projectRepoUrl: PROJECT_REPO_URL,
  }
}
