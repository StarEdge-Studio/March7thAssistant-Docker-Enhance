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

      <div v-if="store.role === 'admin'" class="flex flex-wrap items-center gap-2.5 shrink-0">
        <button
          type="button"
          class="m3-btn m3-btn-tonal px-4 py-3 text-sm"
          @click="openInviteManagerModal"
        >
          <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
          </svg>
          <span>邀请链接</span>
        </button>

        <button
          type="button"
          class="m3-btn m3-btn-filled px-5 py-3 text-sm shadow-xs"
          @click="openCreateModal"
        >
          <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          <span>新增游戏账号</span>
        </button>
      </div>
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

          <div v-if="store.role === 'admin' && !(!accountModal.isEdit && accountModal.generateInvite)" class="space-y-1.5">
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

          <!-- 生成邀请链接开关 (仅新增) -->
          <div
            v-if="store.role === 'admin' && !accountModal.isEdit"
            class="flex items-center justify-between gap-3 p-3.5 rounded-[20px]"
            style="background-color: var(--m3-surface-container-highest);"
          >
            <div class="min-w-0">
              <p class="text-sm font-bold" style="color: var(--m3-on-surface);">生成邀请链接</p>
              <p class="text-[11px] mt-0.5" style="color: var(--m3-on-surface-variant);">
                生成有效期 7 天的邀请链接，由用户自行登录绑定并扫码登录游戏账号。
              </p>
            </div>
            <M3Switch v-model="accountModal.generateInvite" />
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
              {{ accountModal.saving ? '保存中...' : (!accountModal.isEdit && accountModal.generateInvite ? '保存并复制' : '保存') }}
            </button>
          </div>
        </form>
      </div>
    </Transition>

    <!-- 邀请链接管理弹窗 -->
    <Transition name="m3-dialog">
      <div
        v-if="inviteManager.visible"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
        @click.self="inviteManager.visible = false"
      >
        <div
          class="m3-dialog-panel max-w-2xl w-full max-h-[85vh] flex flex-col p-6 sm:p-7 rounded-[28px] shadow-2xl border gap-4"
          style="background-color: var(--m3-surface-container-high); border-color: color-mix(in srgb, var(--m3-outline-variant) 50%, transparent);"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <h3 class="text-lg font-extrabold tracking-tight" style="color: var(--m3-on-surface);">邀请链接管理</h3>
              <p class="text-[11px] mt-0.5" style="color: var(--m3-on-surface-variant);">
                邀请链接有效期固定为 7 天，用户通过链接即可自助绑定并扫码登录对应游戏账号。
              </p>
            </div>
            <button
              type="button"
              class="m3-btn m3-btn-tonal w-8 h-8 text-xs shrink-0"
              @click="inviteManager.visible = false"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- 为已有账号生成新邀请 -->
          <div
            v-if="store.accounts.length > 0"
            class="flex flex-col sm:flex-row sm:items-center gap-2.5 p-3 rounded-[20px]"
            style="background-color: var(--m3-surface-container-highest);"
          >
            <select v-model="inviteManager.newAccountId" class="m3-input flex-1 text-sm">
              <option value="" disabled>选择要邀请绑定的游戏账号</option>
              <option v-for="acc in store.accounts" :key="acc.id" :value="acc.id">
                {{ acc.name }}{{ acc.username ? `（已绑定 ${acc.username}）` : '' }}
              </option>
            </select>
            <button
              type="button"
              :disabled="!inviteManager.newAccountId || inviteManager.creating"
              class="m3-btn m3-btn-filled px-4 py-2.5 text-xs shrink-0 disabled:opacity-50"
              @click="createInviteForAccount"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              <span>{{ inviteManager.creating ? '生成中...' : '生成并复制' }}</span>
            </button>
          </div>

          <div class="flex-1 overflow-y-auto space-y-2.5 pr-1 -mr-1">
            <div
              v-if="inviteManager.loading && inviteManager.list.length === 0"
              class="py-10 flex flex-col items-center gap-2.5"
              style="color: var(--m3-on-surface-variant);"
            >
              <div
                class="w-7 h-7 border-3 border-t-transparent rounded-full animate-spin"
                style="border-color: var(--m3-primary); border-top-color: transparent;"
              ></div>
              <span class="text-xs">正在加载邀请链接...</span>
            </div>

            <div
              v-else-if="inviteManager.list.length === 0"
              class="py-10 text-center text-xs"
              style="color: var(--m3-on-surface-variant);"
            >
              暂无邀请链接
            </div>

            <template v-else>
            <div
              v-for="(inv, index) in inviteManager.list"
              :key="inv.code"
              class="m3-stagger-item p-4 rounded-[20px] flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              :style="{ '--stagger-index': index, backgroundColor: 'var(--m3-surface-container-low)' }"
            >
              <div class="min-w-0 space-y-1.5">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-extrabold text-sm truncate" style="color: var(--m3-on-surface);">
                    {{ inv.account_name }}
                  </span>
                  <span
                    class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold"
                    :style="inviteStatusStyle(inv.status)"
                  >
                    <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                    {{ inviteStatusLabel(inv.status) }}
                  </span>
                </div>
                <p class="text-[11px] font-mono truncate" style="color: var(--m3-on-surface-variant);">
                  {{ inv.code }}
                </p>
                <p class="text-[11px]" style="color: var(--m3-on-surface-variant);">
                  <template v-if="inv.status === 'used'">
                    已由 <span class="font-bold" style="color: var(--m3-primary);">{{ inv.used_by || '未知用户' }}</span> 于 {{ inv.used_at }} 使用
                  </template>
                  <template v-else>
                    {{ inv.status === 'expired' ? '已于' : '有效期至' }} {{ inv.expires_at_str }}
                  </template>
                </p>
              </div>

              <div class="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  :disabled="inv.status !== 'active'"
                  class="m3-btn m3-btn-tonal px-3 py-1.5 text-xs disabled:opacity-40"
                  title="复制链接"
                  @click="copyInviteLink(inv.code)"
                >
                  <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184" />
                  </svg>
                  <span>复制</span>
                </button>
                <button
                  type="button"
                  :disabled="inv.status === 'invalid'"
                  class="m3-btn m3-btn-tonal px-3 py-1.5 text-xs disabled:opacity-40"
                  title="生成新的邀请链接（有效期 7 天）"
                  @click="refreshInvite(inv)"
                >
                  <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                  </svg>
                  <span>刷新链接</span>
                </button>
                <button
                  type="button"
                  class="m3-btn m3-btn-error w-8 h-8 text-xs"
                  title="删除邀请链接"
                  @click="deleteInvite(inv)"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>
            </template>
          </div>
        </div>
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
            <!-- 扫码成功或登录成功：隐藏二维码并显示绿色对号与提示 -->
            <div
              v-if="qrModal.status === 'scanned' || qrModal.status === 'success'"
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
                  {{ qrModal.status === 'success' ? '登录成功' : '扫码成功' }}
                </span>
                <span class="text-xs" style="color: var(--m3-on-surface-variant);">
                  {{ qrModal.status === 'success' ? '登录凭证已保存' : '请在手机端点击「确认登录」' }}
                </span>
              </div>
            </div>

            <div v-else-if="qrModal.status === 'failed'" class="flex flex-col items-center gap-2 px-4" style="color: var(--m3-error);">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <span class="text-xs">加载失败，可点击下方重试</span>
            </div>

            <img
              v-else-if="qrModal.hasQr && qrModal.imageUrl"
              :src="qrModal.imageUrl"
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
            {{ qrModal.status === 'scanned' ? '已成功识别二维码，请在手机米游社上点击「确认登录」。' : '请打开手机「米游社 App」扫描上方二维码，并在手机上点击确认。' }}
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
import { apiFetch, buildInviteUrl, canManualRun, confirmModal, copyText, notify, refreshStatus, store } from '../../state.js'

const router = useRouter()

const accountModal = reactive({
  visible: false,
  isEdit: false,
  accountId: '',
  name: '',
  username: '',
  generateInvite: false,
  saving: false,
})

const inviteManager = reactive({
  visible: false,
  loading: false,
  creating: false,
  newAccountId: '',
  list: [],
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
  accountModal.generateInvite = false
  accountModal.visible = true
}

function openEditModal(acc) {
  accountModal.isEdit = true
  accountModal.accountId = acc.id
  accountModal.name = acc.name || ''
  accountModal.username = acc.username || ''
  accountModal.generateInvite = false
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
      const withInvite = accountModal.generateInvite
      const res = await apiFetch('/api/accounts', {
        method: 'POST',
        body: JSON.stringify({
          name: accountModal.name.trim(),
          username: withInvite ? '' : accountModal.username.trim(),
          generate_invite: withInvite,
        }),
      })
      if (withInvite && res?.invite?.code) {
        const ok = await copyText(buildInviteUrl(res.invite.code))
        notify(
          ok ? '账号已创建，邀请链接（7 天有效）已复制到剪贴板' : '账号已创建，但复制失败，请在「邀请链接」中手动复制',
          ok ? 'success' : 'warning',
        )
      } else {
        notify('新账号已创建并生成独立配置', 'success')
      }
    }
    accountModal.visible = false
    await refreshStatus()
  } catch (e) {
    notify(e.message || '保存账号失败', 'error')
  } finally {
    accountModal.saving = false
  }
}

// ==================== 邀请链接管理 ====================

function inviteStatusLabel(status) {
  const map = {
    active: '待使用',
    used: '已使用',
    expired: '已过期',
    invalid: '账号已删除',
  }
  return map[status] || status
}

function inviteStatusStyle(status) {
  if (status === 'active') {
    return { backgroundColor: 'var(--m3-primary-container)', color: 'var(--m3-on-primary-container)' }
  }
  if (status === 'used') {
    return { backgroundColor: 'var(--m3-success-container)', color: 'var(--m3-on-success-container)' }
  }
  if (status === 'expired') {
    return { backgroundColor: 'var(--m3-tertiary-container)', color: 'var(--m3-on-tertiary-container)' }
  }
  return { backgroundColor: 'var(--m3-error-container)', color: 'var(--m3-on-error-container)' }
}

async function loadInvites() {
  inviteManager.loading = true
  try {
    const res = await apiFetch('/api/invites')
    inviteManager.list = Array.isArray(res) ? res : []
  } catch (e) {
    notify(e.message || '加载邀请链接失败', 'error')
  } finally {
    inviteManager.loading = false
  }
}

async function openInviteManagerModal() {
  inviteManager.visible = true
  inviteManager.newAccountId = ''
  await loadInvites()
}

async function copyInviteLink(code) {
  const ok = await copyText(buildInviteUrl(code))
  notify(ok ? '邀请链接已复制到剪贴板' : '复制失败，请检查浏览器剪贴板权限', ok ? 'success' : 'warning')
}

async function createInviteForAccount() {
  if (!inviteManager.newAccountId) return
  inviteManager.creating = true
  try {
    const inv = await apiFetch('/api/invites', {
      method: 'POST',
      body: JSON.stringify({ account_id: inviteManager.newAccountId }),
    })
    if (inv?.code) await copyInviteLink(inv.code)
    inviteManager.newAccountId = ''
    await loadInvites()
  } catch (e) {
    notify(e.message || '生成邀请链接失败', 'error')
  } finally {
    inviteManager.creating = false
  }
}

async function refreshInvite(inv) {
  const msg = inv.status === 'used'
    ? `该邀请链接已被「${inv.used_by || '未知用户'}」使用。刷新后将生成一个有效期 7 天的全新链接，旧链接将立即失效，确定继续吗？`
    : `确定要为账号「${inv.account_name}」刷新邀请链接吗？旧链接将立即失效，并生成一个有效期 7 天的全新链接。`
  const ok = await confirmModal({
    title: '刷新邀请链接',
    message: msg,
    confirmText: '确认刷新',
  })
  if (!ok) return
  try {
    const res = await apiFetch(`/api/invites/${encodeURIComponent(inv.code)}/refresh`, { method: 'POST' })
    if (res?.code) {
      const copied = await copyText(buildInviteUrl(res.code))
      notify(copied ? '新邀请链接已生成并复制到剪贴板（7 天有效）' : '已生成新邀请链接（7 天有效）', 'success')
    } else {
      notify('新邀请链接已生成（7 天有效）', 'success')
    }
    await loadInvites()
  } catch (e) {
    notify(e.message || '刷新链接失败', 'error')
  }
}

async function deleteInvite(inv) {
  const ok = await confirmModal({
    title: '删除邀请链接',
    message: `确定要删除账号「${inv.account_name}」的这条邀请链接吗？删除后该链接将立即失效。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  try {
    await apiFetch(`/api/invites/${encodeURIComponent(inv.code)}`, { method: 'DELETE' })
    notify('邀请链接已删除', 'info')
    await loadInvites()
  } catch (e) {
    notify(e.message || '删除邀请链接失败', 'error')
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
