<template>
  <div class="space-y-4">
    <!-- 顶部栏 -->
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white">游戏账号管理</h2>
        <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          <template v-if="store.authMode === 'oidc'">
            OIDC 模式下，管理员可为每个账号绑定对应的 SSO 用户名 (username)，该用户登录后即可管理对应账号。
          </template>
          <template v-else>
            Token 模式下，每个账号拥有独立的访问密钥 (Secret Key)，可用于单账号独立登录管理。
          </template>
        </p>
      </div>

      <div v-if="store.role === 'admin'" class="flex flex-wrap items-center gap-2 shrink-0">
        <button
          type="button"
          class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-500/25 flex items-center justify-center gap-1.5 transition"
          @click="openInviteManagerModal"
        >
          <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
          </svg>
          <span>邀请链接</span>
        </button>
        <button
          type="button"
          class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-sm shadow-indigo-500/20 flex items-center justify-center gap-1.5 transition"
          @click="openCreateModal"
        >
          <span>＋ 新增游戏账号</span>
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="store.accounts.length === 0"
      class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-10 text-center space-y-3"
    >
      <div class="mx-auto w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xl font-bold">
        7
      </div>
      <h3 class="text-sm font-bold text-slate-800 dark:text-slate-200">暂无游戏账号</h3>
      <p class="text-xs text-slate-500 dark:text-slate-400">
        {{ store.role === 'admin' ? '点击右上角「新增游戏账号」添加您的第一个星穹铁道账号' : '当前尚未分配游戏账号' }}
      </p>
    </div>

    <!-- 账号卡片网格 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="(acc, index) in store.accounts"
        :key="acc.id"
        class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 flex flex-col justify-between gap-4 shadow-xs hover:border-indigo-300 dark:hover:border-indigo-700/70 transition"
      >
        <div class="space-y-3.5">
          <!-- 头部：序号、名称、启用开关 -->
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2.5 min-w-0">
              <span class="px-2 py-0.5 rounded-lg text-xs font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 shrink-0">
                #{{ index + 1 }}
              </span>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5">
                  <h3 class="font-bold text-sm sm:text-base text-slate-900 dark:text-white truncate">
                    {{ acc.name }}
                  </h3>
                  <button
                    type="button"
                    class="p-1 rounded-lg text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition"
                    title="修改账号名称或绑定用户"
                    @click="openEditModal(acc)"
                  >
                    ✎
                  </button>
                </div>
                <p class="text-[11px] font-mono text-slate-400 dark:text-slate-500">ID: {{ acc.id }}</p>
              </div>
            </div>

            <!-- 启用状态开关与排序 -->
            <div class="flex items-center gap-1.5 shrink-0">
              <template v-if="store.role === 'admin' && store.accounts.length > 1">
                <button
                  type="button"
                  :disabled="index === 0"
                  class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 disabled:opacity-30 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs transition"
                  title="上移顺序"
                  @click="moveAccount(index, -1)"
                >
                  ↑
                </button>
                <button
                  type="button"
                  :disabled="index === store.accounts.length - 1"
                  class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 disabled:opacity-30 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs transition"
                  title="下移顺序"
                  @click="moveAccount(index, 1)"
                >
                  ↓
                </button>
              </template>

              <label class="inline-flex items-center gap-1.5 cursor-pointer select-none ml-1">
                <input
                  type="checkbox"
                  :checked="acc.enabled"
                  class="sr-only peer"
                  @change="toggleAccountEnabled(acc, $event.target.checked)"
                />
                <div class="w-9 h-5 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all relative peer-checked:bg-indigo-600"></div>
                <span class="text-xs font-medium text-slate-600 dark:text-slate-300">
                  {{ acc.enabled ? '已启用' : '已停用' }}
                </span>
              </label>
            </div>
          </div>

          <!-- 状态徽章栏 -->
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl font-medium"
              :class="acc.is_logged_in
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300'
                : 'bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300'"
            >
              <span class="w-1.5 h-1.5 rounded-full" :class="acc.is_logged_in ? 'bg-emerald-500' : 'bg-amber-500'"></span>
              {{ acc.is_logged_in ? '云崩铁已登录' : '待扫码登录' }}
            </span>

            <span
              v-if="acc.game_uid"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl font-mono font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300"
              title="当前绑定的星穹铁道游戏 UID"
            >
              UID: {{ acc.game_uid }}
            </span>

            <span
              v-if="acc.mihoyo_aid"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
              title="当前绑定的米哈游通行证 ID (AID)"
            >
              通行证: {{ acc.mihoyo_aid }}
            </span>

            <span
              v-if="getAccountBindingWarning(acc)"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl font-semibold bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300"
            >
              ⚠ {{ getAccountBindingWarning(acc) }}
            </span>

            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
            >
              上次运行: {{ acc.last_run_at || '从未运行' }}
              <template v-if="acc.last_run_status">
                ({{ statusLabel(acc.last_run_status) }})
              </template>
            </span>
          </div>

          <!-- 账号归属 / 密钥管理区 -->
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-xs space-y-2">
            <!-- OIDC 用户名绑定展示 -->
            <div v-if="store.authMode === 'oidc' || store.role === 'admin'" class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <span class="text-slate-400 dark:text-slate-500">OIDC 绑定用户 (username): </span>
                <span
                  class="font-mono font-semibold"
                  :class="acc.username ? 'text-indigo-600 dark:text-indigo-300' : 'text-slate-400 italic'"
                >
                  {{ acc.username || '未绑定' }}
                </span>
              </div>
              <button
                v-if="store.role === 'admin'"
                type="button"
                class="px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 font-medium shrink-0 transition"
                @click="openEditModal(acc)"
              >
                设置用户
              </button>
            </div>

            <!-- Token 模式下管理员可复制/重置专属密钥 -->
            <div v-if="store.authMode === 'token' && store.role === 'admin'" class="flex items-center justify-between gap-2 pt-1 border-t border-slate-200/60 dark:border-slate-700/60">
              <div class="min-w-0 truncate">
                <span class="text-slate-400 dark:text-slate-500">专属登录密钥: </span>
                <span class="font-mono text-slate-700 dark:text-slate-300">
                  {{ acc.secret_key ? `${acc.secret_key.slice(0, 6)}••••••${acc.secret_key.slice(-4)}` : '未生成' }}
                </span>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  class="px-2 py-1 rounded-lg bg-slate-200/70 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-300 transition"
                  @click="copySecretKey(acc.secret_key)"
                >
                  复制密钥
                </button>
                <button
                  type="button"
                  class="px-2 py-1 rounded-lg bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-300 hover:bg-amber-100 transition"
                  @click="regenerateKey(acc)"
                >
                  重置
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部操作按钮组 -->
        <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-2xs transition"
              @click="openQrModal(acc)"
            >
              📱 扫码登录
            </button>
            <button
              type="button"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition"
              @click="goToAccountConfig(acc.id)"
            >
              ⚙ 独立配置
            </button>
            <button
              v-if="canManualRun()"
              type="button"
              :disabled="store.scheduler.is_running"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 dark:bg-emerald-500/15 hover:bg-emerald-100 text-emerald-700 dark:text-emerald-300 disabled:opacity-40 transition"
              @click="runSingleAccount(acc)"
            >
              ▶ 单独运行
            </button>
          </div>

          <button
            v-if="store.role === 'admin'"
            type="button"
            class="px-2.5 py-1.5 rounded-xl text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/15 transition"
            @click="deleteAccount(acc)"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 新增 / 编辑账号弹窗 -->
    <div
      v-if="accountModal.visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs"
      @click.self="accountModal.visible = false"
    >
      <form
        class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4"
        @submit.prevent="submitAccountModal"
      >
        <h3 class="text-base font-bold text-slate-900 dark:text-white">
          {{ accountModal.isEdit ? '编辑账号信息' : '新增星穹铁道账号' }}
        </h3>

        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
            账号显示名称
          </label>
          <input
            v-model="accountModal.name"
            type="text"
            required
            placeholder="例如：开拓者大号 / 小号"
            class="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div v-if="store.role === 'admin' && !(!accountModal.isEdit && accountModal.generateInvite)">
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
            绑定 OIDC 用户名 (username，可选)
          </label>
          <input
            v-model="accountModal.username"
            type="text"
            placeholder="填写 SSO 登录的 username，留空则仅管理员可见"
            class="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-mono text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <p class="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
            当启用 OIDC 登录时，拥有该 username 的用户登录后将自动获得此账号的管理与配置权限。
          </p>
        </div>

        <!-- 生成邀请链接开关 (仅新增) -->
        <label
          v-if="store.role === 'admin' && !accountModal.isEdit"
          class="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 cursor-pointer select-none"
        >
          <div class="min-w-0">
            <p class="text-sm font-semibold text-slate-800 dark:text-slate-200">生成邀请链接</p>
            <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
              生成有效期 7 天的邀请链接，由用户自行登录绑定并扫码登录游戏账号。
            </p>
          </div>
          <input v-model="accountModal.generateInvite" type="checkbox" class="sr-only peer" />
          <div class="w-9 h-5 shrink-0 bg-slate-200 dark:bg-slate-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all relative peer-checked:bg-indigo-600"></div>
        </label>

        <div class="pt-2 flex justify-end gap-2.5">
          <button
            type="button"
            class="px-4 py-2 rounded-xl text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
            @click="accountModal.visible = false"
          >
            取消
          </button>
          <button
            type="submit"
            :disabled="accountModal.saving"
            class="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-60"
          >
            {{ accountModal.saving ? '保存中...' : (!accountModal.isEdit && accountModal.generateInvite ? '保存并复制' : '保存') }}
          </button>
        </div>
      </form>
    </div>

    <!-- 邀请链接管理弹窗 -->
    <div
      v-if="inviteManager.visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs"
      @click.self="inviteManager.visible = false"
    >
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col p-5 sm:p-6 shadow-2xl gap-4">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">邀请链接管理</h3>
            <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
              邀请链接有效期固定为 7 天，用户通过链接即可自助绑定并扫码登录对应游戏账号。
            </p>
          </div>
          <button
            type="button"
            class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 shrink-0"
            @click="inviteManager.visible = false"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- 为已有账号生成新邀请 -->
        <div v-if="store.accounts.length > 0" class="flex flex-col sm:flex-row sm:items-center gap-2">
          <select
            v-model="inviteManager.newAccountId"
            class="flex-1 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="" disabled>选择要邀请绑定的游戏账号</option>
            <option v-for="acc in store.accounts" :key="acc.id" :value="acc.id">
              {{ acc.name }}{{ acc.username ? `（已绑定 ${acc.username}）` : '' }}
            </option>
          </select>
          <button
            type="button"
            :disabled="!inviteManager.newAccountId || inviteManager.creating"
            class="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 shrink-0"
            @click="createInviteForAccount"
          >
            {{ inviteManager.creating ? '生成中...' : '生成并复制' }}
          </button>
        </div>

        <div class="flex-1 overflow-y-auto space-y-2 pr-1 -mr-1">
          <div v-if="inviteManager.loading && inviteManager.list.length === 0" class="py-10 flex flex-col items-center gap-2 text-slate-400">
            <div class="w-7 h-7 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-xs">正在加载邀请链接...</span>
          </div>
          <div v-else-if="inviteManager.list.length === 0" class="py-10 text-center text-xs text-slate-400">
            暂无邀请链接
          </div>
          <template v-else>
            <div
              v-for="inv in inviteManager.list"
              :key="inv.code"
              class="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div class="min-w-0 space-y-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-semibold text-sm text-slate-900 dark:text-white truncate">{{ inv.account_name }}</span>
                  <span class="px-2 py-0.5 rounded-lg text-[11px] font-semibold" :class="inviteStatusClass(inv.status)">
                    {{ inviteStatusLabel(inv.status) }}
                  </span>
                </div>
                <p class="text-[11px] font-mono text-slate-400 dark:text-slate-500 truncate">{{ inv.code }}</p>
                <p class="text-[11px] text-slate-500 dark:text-slate-400">
                  <template v-if="inv.status === 'used'">
                    已由 <span class="font-semibold text-indigo-600 dark:text-indigo-300">{{ inv.used_by || '未知用户' }}</span> 于 {{ inv.used_at }} 使用
                  </template>
                  <template v-else>
                    {{ inv.status === 'expired' ? '已于' : '有效期至' }} {{ inv.expires_at_str }}
                  </template>
                </p>
              </div>
              <div class="flex items-center gap-1.5 shrink-0 text-xs">
                <button
                  type="button"
                  :disabled="inv.status !== 'active'"
                  class="px-2.5 py-1.5 rounded-lg bg-slate-200/70 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-300 disabled:opacity-40 transition"
                  @click="copyInviteLink(inv.code)"
                >
                  复制
                </button>
                <button
                  type="button"
                  :disabled="inv.status === 'invalid'"
                  class="px-2.5 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 disabled:opacity-40 transition"
                  title="生成新的邀请链接（有效期 7 天）"
                  @click="refreshInvite(inv)"
                >
                  刷新链接
                </button>
                <button
                  type="button"
                  class="px-2.5 py-1.5 rounded-lg text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/15 transition"
                  @click="deleteInvite(inv)"
                >
                  删除
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 扫码登录向导弹窗 -->
    <div
      v-if="qrModal.visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/65 backdrop-blur-xs"
    >
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-md w-full p-6 shadow-2xl text-center space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-slate-900 dark:text-white">
            云·星穹铁道扫码登录 · {{ qrModal.accountName }}
          </h3>
          <button
            type="button"
            class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            @click="closeQrModal"
          >
            ✕
          </button>
        </div>

        <!-- 状态提示文字 -->
        <div
          class="p-3 rounded-xl text-xs font-medium"
          :class="{
            'bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300': ['starting', 'checking', 'fetching_qr', 'waiting_scan', 'refreshing'].includes(qrModal.status),
            'bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300': ['scanned', 'success'].includes(qrModal.status),
            'bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300': qrModal.status === 'failed',
          }"
        >
          {{ qrModal.message }}
        </div>

        <!-- 二维码展示框 -->
        <div class="mx-auto w-56 h-56 rounded-2xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center overflow-hidden">
          <!-- 扫码成功或登录成功：隐藏二维码并显示绿色对号与提示 -->
          <div v-if="qrModal.status === 'scanned' || qrModal.status === 'success'" class="text-emerald-500 flex flex-col items-center gap-2.5 px-4 text-center">
            <div class="w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            </div>
            <div class="space-y-0.5">
              <span class="text-sm font-bold text-slate-800 dark:text-slate-100 block">
                {{
                  qrModal.status === 'scanned'
                    ? '扫码成功'
                    : qrModal.alreadyLoggedIn
                      ? '当前已登录'
                      : '登录成功'
                }}
              </span>
              <span class="text-xs text-slate-500 dark:text-slate-400">
                {{
                  qrModal.status === 'scanned'
                    ? '请在手机端点击「确认登录」'
                    : qrModal.alreadyLoggedIn
                      ? '如需更换账号，请清除旧会话后重扫'
                      : qrModal.autoCloseSeconds > 0
                        ? `登录凭证已保存，${qrModal.autoCloseSeconds} 秒后自动关闭...`
                        : '登录凭证已保存'
                }}
              </span>
            </div>
          </div>

          <div v-else-if="qrModal.status === 'failed'" class="text-rose-500 flex flex-col items-center gap-2 px-4 text-center">
            <span class="text-3xl font-bold">!</span>
            <span class="text-xs">加载失败，可点击下方重试</span>
          </div>

          <img
            v-else-if="qrModal.hasQr && qrModal.imageUrl"
            :src="qrModal.imageUrl"
            alt="登录二维码"
            class="w-full h-full object-contain p-2 bg-white"
          />

          <div v-else class="flex flex-col items-center gap-2.5 text-slate-400">
            <div class="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-xs">正在准备二维码...</span>
          </div>
        </div>

        <p class="text-[11px] text-slate-400 dark:text-slate-500">
          {{
            qrModal.status === 'scanned'
              ? '已成功识别二维码，请在手机米游社上点击「确认登录」。'
              : qrModal.status === 'success' && qrModal.alreadyLoggedIn
                ? '检测到旧浏览器会话仍处于登录状态，请点击下方「清除并重新登录」获取新二维码。'
                : qrModal.status === 'success'
                  ? '新登录凭证已保存，弹窗即将自动关闭。'
                  : '请打开手机「米游社 App」扫描上方二维码，并在手机上点击确认。'
          }}
        </p>

        <div class="pt-2 flex flex-wrap justify-center gap-2.5">
          <button
            v-if="qrModal.status === 'failed'"
            type="button"
            class="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white"
            @click="startQrSession(qrModal.accountId, true)"
          >
            重新获取二维码
          </button>
          <button
            v-if="qrModal.status === 'success'"
            type="button"
            class="px-4 py-2 rounded-xl text-xs font-semibold transition-colors"
            :class="qrModal.alreadyLoggedIn
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm shadow-indigo-500/20'
              : 'bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-300 hover:bg-amber-100'"
            @click="startQrSession(qrModal.accountId, true)"
          >
            {{ qrModal.alreadyLoggedIn ? '清除并重新登录' : '切换账号重扫' }}
          </button>
          <button
            type="button"
            class="px-5 py-2 rounded-xl text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200"
            @click="closeQrModal"
          >
            {{
              qrModal.status === 'success'
                ? qrModal.autoCloseSeconds > 0
                  ? `立即关闭 (${qrModal.autoCloseSeconds}s)`
                  : '完成并关闭'
                : '取消并关闭浏览器'
            }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, buildInviteUrl, canManualRun, confirmModal, copyText, notify, refreshStatus, store } from '../state.js'

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
  alreadyLoggedIn: false,
  autoCloseSeconds: 0,
})

let qrPollTimer = null
let qrAutoCloseTimer = null

function stopQrAutoCloseTimer() {
  if (qrAutoCloseTimer) {
    clearInterval(qrAutoCloseTimer)
    qrAutoCloseTimer = null
  }
  qrModal.autoCloseSeconds = 0
}

function startQrAutoCloseTimer(seconds = 2) {
  stopQrAutoCloseTimer()
  qrModal.autoCloseSeconds = seconds
  qrAutoCloseTimer = setInterval(() => {
    qrModal.autoCloseSeconds -= 1
    if (qrModal.autoCloseSeconds <= 0) {
      stopQrAutoCloseTimer()
      closeQrModal()
    }
  }, 1000)
}

function statusLabel(st) {
  const map = {
    success: '成功',
    error: '失败',
    running: '运行中',
    stopped: '已停止',
  }
  return map[st] || st
}

function getAccountBindingWarning(acc) {
  if (!acc) return ''
  const aid = (acc.mihoyo_aid || '').trim()
  const uid = (acc.game_uid || '').trim()
  const name = (acc.name || '').trim()
  const mCardUid = name.match(/\b(\d{9})\b/)
  if (mCardUid && uid && mCardUid[1] !== uid) {
    return `卡片名称 UID 与实际登录 UID (${uid}) 不一致`
  }
  for (const other of store.accounts || []) {
    if (other.id === acc.id) continue
    if (aid && (other.mihoyo_aid || '').trim() === aid) {
      return `与「${other.name}」绑定了同一通行证`
    }
    if (uid && (other.game_uid || '').trim() === uid) {
      return `与「${other.name}」绑定了同一游戏 UID`
    }
  }
  return ''
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

function inviteStatusClass(status) {
  if (status === 'active') return 'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300'
  if (status === 'used') return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300'
  if (status === 'expired') return 'bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300'
  return 'bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300'
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

async function startQrSession(accountId, resetSession = false) {
  stopQrAutoCloseTimer()
  if (qrPollTimer) {
    clearInterval(qrPollTimer)
    qrPollTimer = null
  }
  qrModal.status = 'starting'
  qrModal.message = resetSession
    ? '正在清除旧登录凭证并重新获取二维码...'
    : '正在启动无头浏览器并加载云游戏登录框...'
  qrModal.hasQr = false
  qrModal.imageUrl = ''
  qrModal.alreadyLoggedIn = false

  try {
    const query = resetSession ? '?reset_session=true' : ''
    await apiFetch(`/api/accounts/${accountId}/qr_login/start${query}`, { method: 'POST' })
    qrPollTimer = setInterval(() => pollQrStatus(accountId), 2000)
  } catch (e) {
    qrModal.status = 'failed'
    qrModal.message = e.message || '启动扫码向导失败'
  }
}

async function pollQrStatus(accountId) {
  try {
    const res = await apiFetch(`/api/accounts/${accountId}/qr_login/status`)
    if (!qrModal.visible || qrModal.accountId !== accountId) return
    qrModal.status = res.status || 'starting'
    qrModal.message = res.message || ''
    qrModal.hasQr = Boolean(res.has_qr)
    qrModal.alreadyLoggedIn = Boolean(res.already_logged_in)
    if (res.has_qr) {
      qrModal.imageUrl = `/api/accounts/${accountId}/qr_login/image?token=${encodeURIComponent(store.token)}&t=${res.qr_mtime || Date.now()}`
    }
    if (res.status === 'success') {
      if (qrPollTimer) {
        clearInterval(qrPollTimer)
        qrPollTimer = null
      }
      if (qrModal.alreadyLoggedIn) {
        notify('检测到当前已有登录状态，可点击「清除并重新登录」', 'info')
        await refreshStatus()
      } else {
        notify('扫码登录成功！凭证已保存', 'success')
        await refreshStatus()
        if (qrModal.visible && qrModal.accountId === accountId && qrModal.status === 'success' && !qrModal.alreadyLoggedIn) {
          startQrAutoCloseTimer(2)
        }
      }
    } else if (res.status === 'failed') {
      if (qrPollTimer) {
        clearInterval(qrPollTimer)
        qrPollTimer = null
      }
    }
  } catch {
    // ignore transient poll error
  }
}

async function closeQrModal() {
  stopQrAutoCloseTimer()
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

onMounted(async () => {
  await refreshStatus()
})

onUnmounted(() => {
  stopQrAutoCloseTimer()
  if (qrPollTimer) clearInterval(qrPollTimer)
})
</script>
