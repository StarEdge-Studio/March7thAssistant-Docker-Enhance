<template>
  <div class="space-y-5">
    <!-- M3E 顶部栏 -->
    <div
      class="rounded-[28px] p-5 sm:p-6 border flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      style="background-color: var(--m3-surface-container-low); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
    >
      <div>
        <h2 class="text-lg sm:text-xl font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
          账号配置
        </h2>
        <p class="mt-1 text-xs sm:text-sm" style="color: var(--m3-on-surface-variant);">
          <template v-if="store.authMode === 'oidc'">
            OIDC 模式下，管理员可为每个账号绑定对应的 SSO 用户名 (username)，该用户登录后即可管理对应账号。
          </template>
          <template v-else>
            Token 模式下，每个账号拥有独立的访问密钥 (Secret Key)，可用于单账号独立登录管理。
          </template>
        </p>
      </div>

      <button
        v-if="store.role === 'admin'"
        type="button"
        class="m3-btn m3-btn-filled px-5 py-3 text-sm shrink-0 shadow-xs"
        @click="openCreateModal"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        <span>新增游戏账号</span>
      </button>
    </div>

    <!-- 空状态 -->
    <div
      v-if="store.accounts.length === 0"
      class="m3-card p-12 text-center space-y-3"
    >
      <div
        class="mx-auto w-14 h-14 rounded-[20px] flex items-center justify-center text-2xl font-black"
        style="background-color: var(--m3-primary-container); color: var(--m3-on-primary-container);"
      >
        7
      </div>
      <h3 class="text-base font-bold" style="color: var(--m3-on-surface);">暂无游戏账号</h3>
      <p class="text-xs sm:text-sm" style="color: var(--m3-on-surface-variant);">
        {{ store.role === 'admin' ? '点击右上角「新增游戏账号」添加您的第一个星穹铁道账号' : '当前尚未分配游戏账号' }}
      </p>
    </div>

    <!-- 账号卡片网格 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div
        v-for="(acc, index) in store.accounts"
        :key="acc.id"
        class="m3-card m3-card-interactive m3-stagger-item p-5 sm:p-6 flex flex-col justify-between gap-4"
        :style="{ '--stagger-index': index }"
      >
        <div class="space-y-4">
          <!-- 头部：序号、名称、启用开关 -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
              <span
                class="w-10 h-10 rounded-[14px] flex items-center justify-center text-xs font-mono font-extrabold shrink-0"
                style="background-color: var(--m3-secondary-container); color: var(--m3-on-secondary-container);"
              >
                #{{ index + 1 }}
              </span>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5">
                  <h3 class="font-extrabold text-base truncate" style="color: var(--m3-on-surface);">
                    {{ acc.name }}
                  </h3>
                  <button
                    type="button"
                    class="m3-btn m3-btn-tonal w-7 h-7 text-xs"
                    title="修改账号名称或绑定用户"
                    @click="openEditModal(acc)"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
                    </svg>
                  </button>
                </div>
                <p class="text-[11px] font-mono mt-0.5" style="color: var(--m3-on-surface-variant);">
                  ID: {{ acc.id }}
                </p>
              </div>
            </div>

            <!-- 排序与 M3Switch 启用开关 -->
            <div class="flex items-center gap-2 shrink-0">
              <template v-if="store.role === 'admin' && store.accounts.length > 1">
                <button
                  type="button"
                  :disabled="index === 0"
                  class="m3-btn m3-btn-tonal w-8 h-8 text-xs disabled:opacity-30"
                  title="上移顺序"
                  @click="moveAccount(index, -1)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                  </svg>
                </button>
                <button
                  type="button"
                  :disabled="index === store.accounts.length - 1"
                  class="m3-btn m3-btn-tonal w-8 h-8 text-xs disabled:opacity-30"
                  title="下移顺序"
                  @click="moveAccount(index, 1)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
                  </svg>
                </button>
              </template>

              <M3Switch
                :model-value="acc.enabled"
                @update:model-value="toggleAccountEnabled(acc, $event)"
              />
            </div>
          </div>

          <!-- 状态胶囊徽章 -->
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span
              class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold"
              :style="acc.is_logged_in
                ? { backgroundColor: 'var(--m3-success-container)', color: 'var(--m3-on-success-container)' }
                : { backgroundColor: 'var(--m3-tertiary-container)', color: 'var(--m3-on-tertiary-container)' }"
            >
              <span class="w-2 h-2 rounded-full bg-current"></span>
              {{ acc.is_logged_in ? '云崩铁已登录' : '待扫码登录' }}
            </span>

            <span
              class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-medium"
              style="background-color: var(--m3-surface-container-highest); color: var(--m3-on-surface-variant);"
            >
              上次运行: {{ acc.last_run_at || '从未运行' }}
              <template v-if="acc.last_run_status">
                ({{ statusLabel(acc.last_run_status) }})
              </template>
            </span>
          </div>

          <!-- 账号归属 / 密钥管理区 -->
          <div
            class="p-3.5 rounded-[20px] text-xs space-y-2.5"
            style="background-color: var(--m3-surface-container-high);"
          >
            <!-- OIDC 用户名绑定展示 -->
            <div v-if="store.authMode === 'oidc' || store.role === 'admin'" class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <span style="color: var(--m3-on-surface-variant);">OIDC 绑定用户 (username): </span>
                <span
                  class="font-mono font-bold"
                  :style="acc.username ? { color: 'var(--m3-primary)' } : { color: 'var(--m3-on-surface-variant)' }"
                >
                  {{ acc.username || '未绑定' }}
                </span>
              </div>
              <button
                v-if="store.role === 'admin'"
                type="button"
                class="m3-btn m3-btn-tonal px-3 py-1 text-xs shrink-0"
                @click="openEditModal(acc)"
              >
                设置用户
              </button>
            </div>

            <!-- Token 模式下管理员可复制/重置专属密钥 -->
            <div
              v-if="store.authMode === 'token' && store.role === 'admin'"
              class="flex items-center justify-between gap-2 pt-2 border-t"
              style="border-color: color-mix(in srgb, var(--m3-outline-variant) 45%, transparent);"
            >
              <div class="min-w-0 truncate">
                <span style="color: var(--m3-on-surface-variant);">专属登录密钥: </span>
                <span class="font-mono font-semibold" style="color: var(--m3-on-surface);">
                  {{ acc.secret_key ? `${acc.secret_key.slice(0, 6)}••••••${acc.secret_key.slice(-4)}` : '未生成' }}
                </span>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  class="m3-btn m3-btn-tonal px-3 py-1 text-xs"
                  @click="copySecretKey(acc.secret_key)"
                >
                  复制密钥
                </button>
                <button
                  type="button"
                  class="m3-btn m3-btn-tertiary px-3 py-1 text-xs"
                  @click="regenerateKey(acc)"
                >
                  重置
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部 M3E 操作按钮组 -->
        <div
          class="pt-3 border-t flex flex-wrap items-center justify-between gap-2"
          style="border-color: color-mix(in srgb, var(--m3-outline-variant) 40%, transparent);"
        >
          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              class="m3-btn m3-btn-filled px-4 py-2 text-xs"
              @click="openQrModal(acc)"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 3.75 9.375v-4.5ZM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 0 1-1.125-1.125v-4.5ZM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 13.5 9.375v-4.5Z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 6.75h.75v.75h-.75v-.75ZM6.75 16.5h.75v.75h-.75v-.75ZM16.5 6.75h.75v.75h-.75v-.75ZM13.5 13.5h.75v.75h-.75v-.75ZM13.5 19.5h.75v.75h-.75v-.75ZM19.5 13.5h.75v.75h-.75v-.75ZM19.5 19.5h.75v.75h-.75v-.75ZM16.5 16.5h.75v.75h-.75v-.75Z" />
              </svg>
              <span>扫码登录</span>
            </button>
            <button
              type="button"
              class="m3-btn m3-btn-tonal px-4 py-2 text-xs"
              @click="goToAccountConfig(acc.id)"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75" />
              </svg>
              <span>独立配置</span>
            </button>
            <button
              v-if="canManualRun()"
              type="button"
              :disabled="store.scheduler.is_running"
              class="m3-btn m3-btn-tertiary px-4 py-2 text-xs disabled:opacity-40"
              @click="runSingleAccount(acc)"
            >
              <svg class="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.84A1.5 1.5 0 0 0 4 4.11v11.78a1.5 1.5 0 0 0 2.3 1.27l9.344-5.891a1.5 1.5 0 0 0 0-2.538L6.3 2.841Z" />
              </svg>
              <span>单独运行</span>
            </button>
          </div>

          <button
            v-if="store.role === 'admin'"
            type="button"
            class="m3-btn m3-btn-error px-3.5 py-2 text-xs"
            @click="deleteAccount(acc)"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 新增 / 编辑账号弹窗 (M3E 28px Dialog) -->
    <Transition name="m3-dialog">
      <div
        v-if="accountModal.visible"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
        @click.self="accountModal.visible = false"
      >
        <form
          class="m3-dialog-panel max-w-md w-full p-7 rounded-[28px] shadow-2xl border space-y-5"
          style="background-color: var(--m3-surface-container-high); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
          @submit.prevent="submitAccountModal"
        >
          <h3 class="text-lg font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
            {{ accountModal.isEdit ? '编辑账号信息' : '新增星穹铁道账号' }}
          </h3>

          <div class="space-y-1.5">
            <label class="block text-xs font-bold px-1" style="color: var(--m3-on-surface-variant);">
              账号显示名称
            </label>
            <input
              v-model="accountModal.name"
              type="text"
              required
              placeholder="例如：开拓者大号 / 小号"
              class="m3-input w-full"
            />
          </div>

          <div v-if="store.role === 'admin'" class="space-y-1.5">
            <label class="block text-xs font-bold px-1" style="color: var(--m3-on-surface-variant);">
              绑定 OIDC 用户名 (username，可选)
            </label>
            <input
              v-model="accountModal.username"
              type="text"
              placeholder="填写 SSO 登录的 username，留空则仅管理员可见"
              class="m3-input w-full font-mono"
            />
            <p class="text-[11px] px-1" style="color: var(--m3-on-surface-variant);">
              当启用 OIDC 登录时，拥有该 username 的用户登录后将自动获得此账号的管理与配置权限。
            </p>
          </div>

          <div class="pt-2 flex justify-end gap-2.5">
            <button
              type="button"
              class="m3-btn m3-btn-tonal px-5 py-2.5 text-xs"
              @click="accountModal.visible = false"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="accountModal.saving"
              class="m3-btn m3-btn-filled px-6 py-2.5 text-xs disabled:opacity-55"
            >
              {{ accountModal.saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </Transition>

    <!-- 扫码登录向导弹窗 (M3E 32px Dialog) -->
    <Transition name="m3-dialog">
      <div
        v-if="qrModal.visible"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/55 backdrop-blur-xs"
      >
        <div
          class="m3-dialog-panel max-w-md w-full p-7 rounded-[32px] shadow-2xl border text-center space-y-4"
          style="background-color: var(--m3-surface-container-high); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-base font-extrabold tracking-tight" style="color: var(--m3-on-surface);">
              云·星穹铁道扫码登录 · {{ qrModal.accountName }}
            </h3>
            <button
              type="button"
              class="m3-btn m3-btn-tonal w-8 h-8 text-xs"
              @click="closeQrModal"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div
            class="p-3.5 rounded-[18px] text-xs font-bold transition-colors duration-300"
            :style="qrStatusStyle(qrModal.status)"
          >
            {{ qrModal.message }}
          </div>

          <div
            class="mx-auto w-56 h-56 rounded-[24px] border flex items-center justify-center overflow-hidden"
            style="background-color: var(--m3-surface-container-lowest); border-color: var(--m3-outline-variant);"
          >
            <img
              v-if="qrModal.hasQr && qrModal.imageUrl"
              :src="qrModal.imageUrl"
              alt="登录二维码"
              class="w-full h-full object-contain p-2 bg-white"
            />
            <div v-else-if="qrModal.status === 'success'" class="flex flex-col items-center gap-2" style="color: var(--m3-primary);">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              <span class="text-xs font-bold">登录凭证已保存</span>
            </div>
            <div v-else-if="qrModal.status === 'failed'" class="flex flex-col items-center gap-2 px-4" style="color: var(--m3-error);">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <span class="text-xs">加载失败，可点击下方重试</span>
            </div>
            <div v-else class="flex flex-col items-center gap-2.5" style="color: var(--m3-on-surface-variant);">
              <div
                class="w-8 h-8 border-3 border-t-transparent rounded-full animate-spin"
                style="border-color: var(--m3-primary); border-top-color: transparent;"
              ></div>
              <span class="text-xs">正在准备二维码...</span>
            </div>
          </div>

          <p class="text-[11px]" style="color: var(--m3-on-surface-variant);">
            请打开手机「米游社 App」扫描上方二维码，并在手机上点击确认。
          </p>

          <div class="pt-2 flex justify-center gap-3">
            <button
              v-if="qrModal.status === 'failed'"
              type="button"
              class="m3-btn m3-btn-filled px-5 py-2.5 text-xs"
              @click="startQrSession(qrModal.accountId)"
            >
              重新获取二维码
            </button>
            <button
              type="button"
              class="m3-btn m3-btn-tonal px-5 py-2.5 text-xs"
              @click="closeQrModal"
            >
              {{ qrModal.status === 'success' ? '完成并关闭' : '取消并关闭浏览器' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { onUnmounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import M3Switch from '../../components/m3e/M3Switch.vue'
import { apiFetch, canManualRun, confirmModal, notify, refreshStatus, store } from '../../state.js'

const router = useRouter()

const accountModal = reactive({
  visible: false,
  isEdit: false,
  accountId: '',
  name: '',
  username: '',
  saving: false,
})

const qrModal = reactive({
  visible: false,
  accountId: '',
  accountName: '',
  status: 'starting',
  message: '正在启动无头浏览器...',
  hasQr: false,
  imageUrl: '',
})

let qrPollTimer = null

function statusLabel(st) {
  const map = {
    success: '成功',
    error: '失败',
    running: '运行中',
    stopped: '已停止',
  }
  return map[st] || st
}

function qrStatusStyle(status) {
  if (status === 'failed') {
    return { backgroundColor: 'var(--m3-error-container)', color: 'var(--m3-on-error-container)' }
  }
  if (status === 'scanned' || status === 'success') {
    return { backgroundColor: 'var(--m3-success-container)', color: 'var(--m3-on-success-container)' }
  }
  return { backgroundColor: 'var(--m3-primary-container)', color: 'var(--m3-on-primary-container)' }
}

function openCreateModal() {
  accountModal.isEdit = false
  accountModal.accountId = ''
  accountModal.name = ''
  accountModal.username = ''
  accountModal.visible = true
}

function openEditModal(acc) {
  accountModal.isEdit = true
  accountModal.accountId = acc.id
  accountModal.name = acc.name || ''
  accountModal.username = acc.username || ''
  accountModal.visible = true
}

async function submitAccountModal() {
  if (!accountModal.name.trim()) return
  accountModal.saving = true
  try {
    if (accountModal.isEdit) {
      await apiFetch(`/api/accounts/${accountModal.accountId}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: accountModal.name.trim(),
          username: accountModal.username.trim(),
        }),
      })
      notify('账号信息已更新', 'success')
    } else {
      await apiFetch('/api/accounts', {
        method: 'POST',
        body: JSON.stringify({
          name: accountModal.name.trim(),
          username: accountModal.username.trim(),
        }),
      })
      notify('新账号已创建并生成独立配置', 'success')
    }
    accountModal.visible = false
    await refreshStatus()
  } catch (e) {
    notify(e.message || '保存账号失败', 'error')
  } finally {
    accountModal.saving = false
  }
}

async function toggleAccountEnabled(acc, enabled) {
  try {
    await apiFetch(`/api/accounts/${acc.id}`, {
      method: 'PUT',
      body: JSON.stringify({ enabled }),
    })
    acc.enabled = enabled
    notify(`${acc.name} 已${enabled ? '启用' : '停用'}`, 'info')
    await refreshStatus()
  } catch (e) {
    notify(e.message || '更新状态失败', 'error')
  }
}

async function moveAccount(index, delta) {
  const list = [...store.accounts]
  const targetIdx = index + delta
  if (targetIdx < 0 || targetIdx >= list.length) return
  const temp = list[index]
  list[index] = list[targetIdx]
  list[targetIdx] = temp
  const ids = list.map((a) => a.id)
  try {
    await apiFetch('/api/accounts/reorder', {
      method: 'PUT',
      body: JSON.stringify({ account_ids: ids }),
    })
    await refreshStatus()
  } catch (e) {
    notify(e.message || '调整排序失败', 'error')
  }
}

async function copySecretKey(key) {
  if (!key) return
  try {
    await navigator.clipboard.writeText(key)
    notify('专属访问密钥已复制到剪贴板', 'success')
  } catch {
    notify('复制失败，请检查浏览器剪贴板权限', 'warning')
  }
}

async function regenerateKey(acc) {
  const ok = await confirmModal({
    title: '重置专属访问密钥',
    message: `确定要重新生成账号「${acc.name}」的访问密钥吗？旧密钥将立即失效。`,
    confirmText: '确认重置',
    danger: true,
  })
  if (!ok) return
  try {
    const res = await apiFetch(`/api/accounts/${acc.id}/regenerate_key`, { method: 'POST' })
    notify('已生成新的专属访问密钥', 'success')
    await refreshStatus()
    if (res.secret_key) {
      await copySecretKey(res.secret_key)
    }
  } catch (e) {
    notify(e.message || '重置密钥失败', 'error')
  }
}

async function deleteAccount(acc) {
  const ok = await confirmModal({
    title: '删除游戏账号',
    message: `确定要永久删除账号「${acc.name}」及其独立配置文件和浏览器登录数据吗？此操作不可恢复。`,
    confirmText: '永久删除',
    danger: true,
  })
  if (!ok) return
  try {
    await apiFetch(`/api/accounts/${acc.id}`, { method: 'DELETE' })
    notify(`账号「${acc.name}」已删除`, 'info')
    await refreshStatus()
  } catch (e) {
    notify(e.message || '删除失败', 'error')
  }
}

function goToAccountConfig(accountId) {
  router.push({ name: 'tasks', query: { account_id: accountId } })
}

async function runSingleAccount(acc) {
  try {
    const res = await apiFetch('/api/run/start', {
      method: 'POST',
      body: JSON.stringify({ account_id: acc.id }),
    })
    notify(res.message || `开始执行账号：${acc.name}`, 'success')
    await refreshStatus()
    router.push({ name: 'dashboard' })
  } catch (e) {
    notify(e.message || '启动失败', 'error')
  }
}

async function openQrModal(acc) {
  qrModal.visible = true
  qrModal.accountId = acc.id
  qrModal.accountName = acc.name
  await startQrSession(acc.id)
}

async function startQrSession(accountId) {
  if (qrPollTimer) {
    clearInterval(qrPollTimer)
    qrPollTimer = null
  }
  qrModal.status = 'starting'
  qrModal.message = '正在启动无头浏览器并加载云游戏登录框...'
  qrModal.hasQr = false
  qrModal.imageUrl = ''

  try {
    await apiFetch(`/api/accounts/${accountId}/qr_login/start`, { method: 'POST' })
    qrPollTimer = setInterval(() => pollQrStatus(accountId), 2000)
  } catch (e) {
    qrModal.status = 'failed'
    qrModal.message = e.message || '启动扫码向导失败'
  }
}

async function pollQrStatus(accountId) {
  try {
    const res = await apiFetch(`/api/accounts/${accountId}/qr_login/status`)
    qrModal.status = res.status || 'starting'
    qrModal.message = res.message || ''
    qrModal.hasQr = Boolean(res.has_qr)
    if (res.has_qr) {
      qrModal.imageUrl = `/api/accounts/${accountId}/qr_login/image?token=${encodeURIComponent(store.token)}&t=${res.qr_mtime || Date.now()}`
    }
    if (res.status === 'success') {
      if (qrPollTimer) {
        clearInterval(qrPollTimer)
        qrPollTimer = null
      }
      notify('扫码登录成功！凭证已保存', 'success')
      await refreshStatus()
    } else if (res.status === 'failed') {
      if (qrPollTimer) {
        clearInterval(qrPollTimer)
        qrPollTimer = null
      }
    }
  } catch {
    // ignore
  }
}

async function closeQrModal() {
  if (qrPollTimer) {
    clearInterval(qrPollTimer)
    qrPollTimer = null
  }
  const accId = qrModal.accountId
  qrModal.visible = false
  if (accId) {
    try {
      await apiFetch(`/api/accounts/${accId}/qr_login/stop`, { method: 'POST' })
    } catch {
      // ignore
    }
    await refreshStatus()
  }
}

onUnmounted(() => {
  if (qrPollTimer) clearInterval(qrPollTimer)
})
</script>
