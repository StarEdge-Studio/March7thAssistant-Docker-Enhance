<template>
  <div class="space-y-4">
    <!-- 顶部控制条：标题 + 账号选择 + 简洁/高级模式切换 + 保存按钮 -->
    <div class="sticky top-14 md:top-0 z-20 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs flex flex-col xl:flex-row xl:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl sm:text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400">
          任务配置
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          简洁模式编辑常用项，高级模式直接编辑 YAML，保存时自动写入当前账号独立配置。
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <!-- 账号选择 -->
        <select
          v-model="selectedAccountId"
          class="px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @change="loadAccountConfig"
        >
          <option v-for="acc in store.accounts" :key="acc.id" :value="acc.id">
            {{ acc.name }}
          </option>
        </select>

        <!-- 简洁模式 / 高级模式切换（高级模式仅桌面端显示） -->
        <div class="hidden md:inline-flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
          <button
            type="button"
            class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition"
            :class="editMode === 'simple'
              ? 'bg-indigo-600 text-white shadow-2xs'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-slate-700/60'"
            @click="switchMode('simple')"
          >
            简洁模式
          </button>
          <button
            type="button"
            class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition"
            :class="editMode === 'advanced'
              ? 'bg-indigo-600 text-white shadow-2xs'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-slate-700/60'"
            @click="switchMode('advanced')"
          >
            高级模式
          </button>
        </div>

        <!-- 恢复默认 -->
        <button
          type="button"
          :disabled="loading || saving || !selectedAccountId"
          class="px-3 py-2 rounded-xl text-xs font-medium bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-400 hover:bg-rose-100 transition disabled:opacity-50"
          @click="handleResetConfig"
        >
          恢复默认
        </button>

        <!-- 保存配置 -->
        <button
          type="button"
          :disabled="loading || saving || !selectedAccountId"
          class="px-5 py-2 rounded-xl text-xs sm:text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 shadow-sm shadow-indigo-500/25 transition"
          @click="handleSaveConfig"
        >
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>

    <!-- 无账号提示 -->
    <div
      v-if="store.accounts.length === 0"
      class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-10 text-center text-xs text-slate-500"
    >
      请先在「账号配置」页面创建一个游戏账号后再进行配置。
    </div>

    <!-- 加载中 -->
    <div
      v-else-if="loading"
      class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-12 flex flex-col items-center justify-center gap-3"
    >
      <div class="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      <span class="text-xs text-slate-500">正在加载配置...</span>
    </div>

    <!-- ==================== 简洁模式 ==================== -->
    <div v-else-if="editMode === 'simple'" class="space-y-3">
      <div
        v-for="group in formGroups"
        :key="group.name"
        class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 overflow-hidden shadow-2xs"
      >
        <!-- 分组折叠头 -->
        <button
          type="button"
          class="w-full px-4 sm:px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition"
          @click="toggleGroup(group.name)"
        >
          <span class="text-sm sm:text-base font-bold text-slate-800 dark:text-slate-100">
            {{ group.title }}
          </span>
          <svg
            class="w-4 h-4 text-slate-400 transition-transform duration-200"
            :class="isGroupOpen(group.name) ? 'rotate-180' : ''"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </button>

        <!-- 分组内容体 -->
        <div
          v-show="isGroupOpen(group.name)"
          class="px-4 sm:px-5 pb-5 pt-2 border-t border-slate-100 dark:border-slate-800/80 space-y-4"
        >
          <!-- 1. 体力与副本 -->
          <template v-if="group.name === 'power'">
            <!-- (1) 培养目标（最上方，明确标注优先级高于下方配置） -->
            <div class="rounded-xl border border-indigo-200/80 dark:border-indigo-500/30 bg-indigo-50/30 dark:bg-indigo-950/20 overflow-hidden">
              <button
                type="button"
                class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-indigo-50/60 dark:hover:bg-indigo-900/20 transition"
                @click="togglePowerPanel('buildTarget')"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-sm font-bold text-indigo-950 dark:text-indigo-200">培养目标</span>
                </div>
                <svg
                  class="w-4 h-4 text-slate-400 transition-transform duration-200"
                  :class="isPowerPanelOpen('buildTarget') ? 'rotate-180' : ''"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              <div v-show="isPowerPanelOpen('buildTarget')" class="px-4 pb-4 pt-2 border-t border-indigo-100 dark:border-indigo-800/40 space-y-3">
                <div class="text-xs font-medium text-indigo-700 dark:text-indigo-300 italic">
                  如果启用培养目标，其优先级高于下方清体力设置
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  <!-- 启用培养目标 -->
                  <label class="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer">
                    <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用培养目标</span>
                    <input v-model="cfg.build_target_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
                  </label>

                  <!-- 识别方案 -->
                  <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                    <label class="text-xs font-medium text-slate-700 dark:text-slate-200">识别方案</label>
                    <select
                      v-model="cfg.build_target_scheme"
                      class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                    >
                      <option v-for="opt in buildTargetSchemeOptions" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                      </option>
                    </select>
                  </div>

                  <!-- 每周饰品提取次数 -->
                  <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                    <label class="text-xs font-medium text-slate-700 dark:text-slate-200">每周饰品提取次数</label>
                    <input
                      :value="numberField('build_target_ornament_weekly_count', 0)"
                      type="number"
                      min="0"
                      max="7"
                      class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                      @input="setNumberField('build_target_ornament_weekly_count', $event.target.value, 0, 7)"
                    />
                  </div>

                  <!-- 仅识别到侵蚀隧洞/饰品提取时使用下方副本 -->
                  <label class="flex items-center justify-between gap-2 p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer">
                    <span class="text-xs font-medium text-slate-700 dark:text-slate-200">仅识别到侵蚀隧洞/饰品提取时使用下方副本</span>
                    <input
                      v-model="cfg.build_target_use_user_instance_when_only_erosion_and_ornament"
                      type="checkbox"
                      class="w-4 h-4 accent-indigo-600 rounded shrink-0"
                    />
                  </label>
                </div>
              </div>
            </div>

            <!-- (2) 历战余响 -->
            <div class="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 overflow-hidden">
              <button
                type="button"
                class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-100/60 dark:hover:bg-slate-800/60 transition"
                @click="togglePowerPanel('war')"
              >
                <span class="text-sm font-bold text-slate-800 dark:text-slate-100">历战余响</span>
                <svg
                  class="w-4 h-4 text-slate-400 transition-transform duration-200"
                  :class="isPowerPanelOpen('war') ? 'rotate-180' : ''"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              <div v-show="isPowerPanelOpen('war')" class="px-4 pb-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3">
                <!-- 启用优先历战余响 -->
                <label class="flex flex-col justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer gap-1">
                  <div class="flex items-center justify-between gap-2">
                    <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用优先历战余响</span>
                    <input v-model="cfg.echo_of_war_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                  </div>
                  <span class="text-[11px] text-slate-400 dark:text-slate-500">启用后，会优先使用体力完成3次「历战余响」</span>
                </label>

                <!-- 开始日 -->
                <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                  <label class="text-xs font-medium text-slate-700 dark:text-slate-200">开始日</label>
                  <select
                    v-model.number="cfg.echo_of_war_start_day_of_week"
                    class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                  >
                    <option v-for="day in weekDayOptions" :key="day.value" :value="day.value">
                      {{ day.label }}
                    </option>
                  </select>
                </div>

                <!-- 历战余响选择 -->
                <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                  <label class="text-xs font-medium text-slate-700 dark:text-slate-200">历战余响选择</label>
                  <select
                    :value="instanceNameValue('历战余响', false)"
                    class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                    @change="setInstanceName('历战余响', $event.target.value)"
                  >
                    <option v-for="item in instanceNameOptions('历战余响', false)" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <!-- (3) 清体力 -->
            <div class="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 overflow-hidden">
              <button
                type="button"
                class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-100/60 dark:hover:bg-slate-800/60 transition"
                @click="togglePowerPanel('clearPower')"
              >
                <span class="text-sm font-bold text-slate-800 dark:text-slate-100">清体力</span>
                <svg
                  class="w-4 h-4 text-slate-400 transition-transform duration-200"
                  :class="isPowerPanelOpen('clearPower') ? 'rotate-180' : ''"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              <div v-show="isPowerPanelOpen('clearPower')" class="px-4 pb-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <!-- 启用清体力 -->
                <label class="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer">
                  <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用清体力</span>
                  <input v-model="cfg.power_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
                </label>

                <!-- 副本类型 -->
                <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                  <label class="text-xs font-medium text-slate-700 dark:text-slate-200">副本类型</label>
                  <select
                    :value="cfg.instance_type"
                    class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                    @change="setInstanceType($event.target.value)"
                  >
                    <option v-for="item in instanceTypeOptions(false)" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>
                </div>

                <!-- 副本名称（仅显示当前所选副本类型的选项） -->
                <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                  <label class="text-xs font-medium text-slate-700 dark:text-slate-200">副本名称</label>
                  <select
                    :value="instanceNameValue(cfg.instance_type, true)"
                    class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                    @change="setInstanceName(cfg.instance_type, $event.target.value)"
                  >
                    <option v-for="item in instanceNameOptions(cfg.instance_type, true)" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>
                </div>

                <!-- 拟造花萼（金）偏好地区 -->
                <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                  <label class="text-xs font-medium text-slate-700 dark:text-slate-200">拟造花萼（金）偏好地区</label>
                  <select
                    v-model="cfg.calyx_golden_preference"
                    class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                  >
                    <option v-for="item in calyxOptions" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <!-- (4) 通用设置 -->
            <div class="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 overflow-hidden">
              <button
                type="button"
                class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-100/60 dark:hover:bg-slate-800/60 transition"
                @click="togglePowerPanel('general')"
              >
                <span class="text-sm font-bold text-slate-800 dark:text-slate-100">通用设置</span>
                <svg
                  class="w-4 h-4 text-slate-400 transition-transform duration-200"
                  :class="isPowerPanelOpen('general') ? 'rotate-180' : ''"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              <div v-show="isPowerPanelOpen('general')" class="px-4 pb-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 space-y-3">
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <label class="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer">
                    <span class="text-xs font-medium text-slate-700 dark:text-slate-200">清体力前传送至任意锚点</span>
                    <input v-model="cfg.tp_before_instance" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
                  </label>

                  <label class="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer">
                    <span class="text-xs font-medium text-slate-700 dark:text-slate-200">使用后备开拓力</span>
                    <input v-model="cfg.use_reserved_trailblaze_power" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
                  </label>

                  <label class="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer">
                    <span class="text-xs font-medium text-slate-700 dark:text-slate-200">使用燃料</span>
                    <input v-model="cfg.use_fuel" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
                  </label>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-200/60 dark:border-slate-800">
                  <label class="flex flex-col justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer gap-1">
                    <div class="flex items-center justify-between gap-2">
                      <span class="text-xs font-medium text-slate-700 dark:text-slate-200">优先合成沉浸器</span>
                      <input v-model="cfg.merge_immersifier" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                    </div>
                    <span class="text-[11px] text-slate-400 dark:text-slate-500">优先级高于上方清体力设置</span>
                  </label>

                  <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                    <label class="text-xs font-medium text-slate-700 dark:text-slate-200">沉浸器上限</label>
                    <input
                      :value="numberField('merge_immersifier_limit', 12)"
                      type="number"
                      min="0"
                      max="99"
                      class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                      @input="setStringNumberField('merge_immersifier_limit', $event.target.value, 0, 99)"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- (5) 体力计划 -->
            <div class="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 overflow-hidden">
              <button
                type="button"
                class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-100/60 dark:hover:bg-slate-800/60 transition"
                @click="togglePowerPanel('plan')"
              >
                <div class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                  <span class="text-sm font-bold text-slate-800 dark:text-slate-100">体力计划</span>
                  <span class="text-[11px] text-slate-400 dark:text-slate-500 font-normal">
                    执行后将根据进度自动扣减次数或移除，并将变动自动保存回配置文件（最高优先级）
                  </span>
                </div>
                <svg
                  class="w-4 h-4 text-slate-400 transition-transform duration-200 shrink-0"
                  :class="isPowerPanelOpen('plan') ? 'rotate-180' : ''"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              <div v-show="isPowerPanelOpen('plan')" class="px-4 pb-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 space-y-2.5">
                <div
                  v-for="(plan, index) in powerPlans"
                  :key="'plan-' + index"
                  class="flex flex-wrap sm:flex-nowrap items-center gap-2 p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800"
                >
                  <select
                    :value="plan[0]"
                    class="w-full sm:w-40 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                    @change="setPowerPlanType(index, $event.target.value)"
                  >
                    <option v-for="item in instanceTypeOptions(false)" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>

                  <select
                    :value="plan[1]"
                    class="flex-1 min-w-[180px] px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                    @change="setPowerPlanName(index, $event.target.value)"
                  >
                    <option v-for="item in instanceNameOptions(plan[0], false)" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>

                  <input
                    :value="plan[2] || 1"
                    type="number"
                    min="1"
                    max="999"
                    class="w-20 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-center"
                    @input="setPowerPlanCount(index, $event.target.value)"
                  />

                  <button
                    type="button"
                    :disabled="index === 0"
                    class="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 transition"
                    @click="movePowerPlanUp(index)"
                  >
                    ↑ 上移
                  </button>

                  <button
                    type="button"
                    class="px-2.5 py-1.5 rounded-lg border border-rose-200 dark:border-rose-500/30 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/15 transition"
                    @click="removePowerPlan(index)"
                  >
                    删除
                  </button>
                </div>

                <button
                  type="button"
                  :disabled="powerPlans.length >= 8"
                  class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 disabled:opacity-40 transition"
                  @click="addPowerPlan"
                >
                  + 添加计划
                </button>
              </div>
            </div>
          </template>

          <!-- 2. 周积分线奖励（Beta） -->
          <template v-else-if="group.name === 'weeklyPoints'">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label class="flex flex-col justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer gap-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用周积分线奖励</span>
                  <input v-model="cfg.currencywars_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                </div>
                <span class="text-[11px] text-slate-400 dark:text-slate-500">
                  使用货币战争完成本周积分奖励，如需修改完成方式或详细策略请使用高级模式
                </span>
              </label>

              <label class="flex flex-col justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer gap-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-medium text-slate-700 dark:text-slate-200">自动消耗深度沉浸器</span>
                  <input v-model="cfg.currencywars_bonus_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                </div>
                <span class="text-[11px] text-slate-400 dark:text-slate-500">
                  领取积分奖励后自动执行位面饰品快速提取
                </span>
              </label>

              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                <label class="text-xs font-medium text-slate-700 dark:text-slate-200">深度沉浸器提取副本</label>
                <select
                  :value="instanceNameValue('饰品提取', false)"
                  class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  @change="setInstanceName('饰品提取', $event.target.value)"
                >
                  <option v-for="item in instanceNameOptions('饰品提取', false)" :key="item.value" :value="item.value">
                    {{ item.label }}
                  </option>
                </select>
                <span class="text-[11px] text-slate-400 dark:text-slate-500 leading-relaxed">
                  对应 instance_names.饰品提取，与上方体力与副本中的饰品提取副本是同一个配置；修改这里也会影响清体力选择饰品提取时使用的副本。若启用培养目标，运行时仍会优先使用培养目标识别到的饰品提取副本。
                </span>
              </div>
            </div>
          </template>

          <!-- 3. 队伍配置 -->
          <template v-else-if="group.name === 'team'">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">自动切换队伍</span>
                <input v-model="cfg.instance_team_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>

              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                <label class="text-xs font-medium text-slate-700 dark:text-slate-200">默认队伍编号</label>
                <input
                  :value="numberField('instance_team_number', 6)"
                  type="number"
                  min="1"
                  max="12"
                  class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  @input="setStringNumberField('instance_team_number', $event.target.value, 1, 12)"
                />
              </div>
            </div>
          </template>

          <!-- 4. 支援角色 -->
          <template v-else-if="group.name === 'borrow'">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用使用支援角色</span>
                <input v-model="cfg.borrow_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>

              <label class="flex flex-col justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer gap-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-medium text-slate-700 dark:text-slate-200">强制使用支援角色</span>
                  <input v-model="cfg.borrow_character_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                </div>
                <span class="text-[11px] text-slate-400 dark:text-slate-500">
                  无论何时都要使用支援角色，即使日常实训中的要求已经完成
                </span>
              </label>

              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                <label class="text-xs font-medium text-slate-700 dark:text-slate-200">滚动查找次数</label>
                <input
                  :value="numberField('borrow_scroll_times', 10)"
                  type="number"
                  min="1"
                  max="10"
                  class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  @input="setNumberField('borrow_scroll_times', $event.target.value, 1, 10)"
                />
              </div>
            </div>

            <div class="text-xs text-slate-500 dark:text-slate-400 italic px-0.5 pt-1">
              左侧选择角色，右侧输入好友名称（可选）
            </div>

            <div class="space-y-2">
              <div
                v-for="idx in 6"
                :key="'friend-' + (idx - 1)"
                class="flex flex-wrap sm:flex-nowrap items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800"
              >
                <span class="text-xs font-mono text-slate-400 w-6 text-center">{{ idx }}</span>
                <select
                  :value="borrowFriendAt(idx - 1)[0]"
                  class="w-full sm:w-56 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  @change="setBorrowFriendCharacter(idx - 1, $event.target.value)"
                >
                  <option v-for="item in characterSelectOptions" :key="item.value" :value="item.value">
                    {{ item.label }}
                  </option>
                </select>
                <input
                  :value="borrowFriendAt(idx - 1)[1]"
                  type="text"
                  placeholder="好友名称，可留空"
                  class="flex-1 min-w-[180px] px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  @input="setBorrowFriendName(idx - 1, $event.target.value)"
                />
              </div>
            </div>
          </template>

          <!-- 5. 奖励领取 -->
          <template v-else-if="group.name === 'reward'">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <label
                v-for="item in rewardFields"
                :key="item.key"
                class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer"
              >
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">{{ item.label }}</span>
                <input v-model="cfg[item.key]" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>
            </div>
          </template>

          <!-- 6. 日常任务 -->
          <template v-else-if="group.name === 'daily'">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用日常任务</span>
                <input v-model="cfg.daily_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">通过合成材料完成任务</span>
                <input v-model="cfg.daily_material_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">通过姬子试用完成任务</span>
                <input v-model="cfg.daily_himeko_try_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>
            </div>
          </template>

          <!-- 7. 资产管理 -->
          <template v-else-if="group.name === 'asset'">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用资产管理</span>
                <input v-model="cfg.asset_manager_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>

              <label class="flex flex-col justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer gap-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-medium text-slate-700 dark:text-slate-200">每月自动购买星轨专票</span>
                  <input v-model="cfg.asset_ember_special_pass_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                </div>
                <span class="text-[11px] text-slate-400 dark:text-slate-500">
                  在余烬兑换中自动购买「星轨专票」，成功后记录时间并在每月 1 号刷新
                </span>
              </label>

              <label class="flex flex-col justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer gap-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-medium text-slate-700 dark:text-slate-200">每月自动购买星轨通票</span>
                  <input v-model="cfg.asset_ember_regular_pass_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                </div>
                <span class="text-[11px] text-slate-400 dark:text-slate-500">
                  在余烬兑换中自动购买「星轨通票」，成功后记录时间并在每月 1 号刷新
                </span>
              </label>

              <label class="flex flex-col justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer gap-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-medium text-slate-700 dark:text-slate-200">每月自动购买命运的足迹</span>
                  <input v-model="cfg.asset_ember_tracks_of_destiny_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded shrink-0" />
                </div>
                <span class="text-[11px] text-slate-400 dark:text-slate-500">
                  在余烬兑换中自动购买「命运的足迹」，成功后记录时间并在每月 1 号刷新
                </span>
              </label>
            </div>
          </template>

          <!-- 8. 活动 -->
          <template v-else-if="group.name === 'activity'">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用活动功能</span>
                <input v-model="cfg.activity_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>
            </div>
          </template>

          <!-- 9. OCR 加速 -->
          <template v-else-if="group.name === 'ocr'">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 flex flex-col justify-between gap-1.5">
                <label class="text-xs font-medium text-slate-700 dark:text-slate-200">OCR 加速模式</label>
                <select
                  v-model="cfg.ocr_gpu_acceleration"
                  class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                >
                  <option v-for="item in ocrOptions" :key="item.value" :value="item.value">
                    {{ item.label }}
                  </option>
                </select>
              </div>
            </div>
          </template>

          <!-- 10. 消息推送 -->
          <template v-else-if="group.name === 'notify'">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-800 cursor-pointer">
                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">启用消息推送</span>
                <input v-model="cfg.notification_enable" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
              </label>
            </div>

            <div class="space-y-2 pt-1">
              <div
                v-for="provider in notifyProviders"
                :key="provider.name"
                class="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 overflow-hidden"
              >
                <button
                  type="button"
                  class="w-full px-4 py-2.5 flex items-center justify-between text-left hover:bg-slate-100/60 dark:hover:bg-slate-800/60 transition"
                  @click="toggleNotifyProvider(provider.name)"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-xs sm:text-sm font-semibold text-slate-800 dark:text-slate-200">{{ provider.title }}</span>
                    <span
                      v-if="cfg[`notify_${provider.name}_enable`]"
                      class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
                    >
                      已启用
                    </span>
                  </div>
                  <svg
                    class="w-4 h-4 text-slate-400 transition-transform duration-200"
                    :class="isNotifyProviderOpen(provider.name) ? 'rotate-180' : ''"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                  </svg>
                </button>

                <div
                  v-if="isNotifyProviderOpen(provider.name)"
                  class="px-4 pb-4 pt-3 border-t border-slate-200/60 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
                >
                  <template v-for="field in providerFieldModels(provider)" :key="field.key">
                    <label
                      v-if="field.type === 'bool'"
                      class="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 cursor-pointer"
                    >
                      <span class="text-xs font-medium text-slate-700 dark:text-slate-200">{{ field.label }}</span>
                      <input v-model="cfg[field.key]" type="checkbox" class="w-4 h-4 accent-indigo-600 rounded" />
                    </label>

                    <div
                      v-else-if="field.type === 'number'"
                      class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5"
                    >
                      <label class="text-xs font-medium text-slate-700 dark:text-slate-200">{{ field.label }}</label>
                      <input
                        :value="numberField(field.key, field.defaultValue)"
                        type="number"
                        :min="field.min"
                        :max="field.max"
                        class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                        @input="setNumberField(field.key, $event.target.value, field.min, field.max)"
                      />
                    </div>

                    <div
                      v-else
                      class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-1.5"
                    >
                      <label class="text-xs font-medium text-slate-700 dark:text-slate-200">{{ field.label }}</label>
                      <input
                        v-model="cfg[field.key]"
                        type="text"
                        class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
                      />
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ==================== 高级模式（桌面端专属 YAML 编辑器） ==================== -->
    <div v-else class="hidden md:flex flex-col bg-slate-950 text-slate-100 rounded-2xl border border-slate-800 overflow-hidden shadow-xl h-[calc(100vh-12rem)] min-h-[520px]">
      <div class="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between gap-4">
        <div class="flex items-center gap-2 text-xs">
          <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono font-semibold">YAML</span>
          <span class="text-slate-400">
            独立配置文件：<code class="text-slate-200">webui/data/configs/{{ selectedAccountId }}.yaml</code>
          </span>
        </div>

        <div class="flex items-center gap-2">
          <input
            v-model="yamlSearchQuery"
            type="text"
            placeholder="查找配置项或注释 (回车下一个)..."
            class="w-60 px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            @keydown.enter.prevent="findNextInYaml"
          />
          <button
            type="button"
            class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
            @click="findNextInYaml"
          >
            查找下一个
          </button>
        </div>
      </div>

      <div class="flex-1 flex overflow-hidden relative font-mono text-xs leading-6">
        <div
          ref="gutterRef"
          class="w-14 py-3 px-2 bg-slate-900/90 border-r border-slate-800 text-right text-slate-500 select-none overflow-hidden shrink-0"
        >
          <div v-for="n in yamlLineCount" :key="n">{{ n }}</div>
        </div>

        <textarea
          ref="yamlTextareaRef"
          v-model="rawYaml"
          spellcheck="false"
          wrap="off"
          class="flex-1 py-3 px-4 bg-slate-950 text-slate-100 focus:outline-none resize-none overflow-auto font-mono text-xs leading-6"
          @scroll="syncGutterScroll"
          @keydown.tab.prevent="handleYamlTab"
        ></textarea>
      </div>

      <div class="px-4 py-1.5 bg-slate-900 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span>共 {{ yamlLineCount }} 行 · 支持 Tab 缩进</span>
        <span>保存时后端将通过 ruamel.yaml 校验语法并保留注释</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiFetch, confirmModal, notify, refreshStatus, store } from '../state.js'

const route = useRoute()

const selectedAccountId = ref('')
const editMode = ref('simple') // 'simple' | 'advanced'
const loading = ref(false)
const saving = ref(false)

const cfg = ref({})
const rawYaml = ref('')
const instanceOptions = ref({})
const characterOptions = ref({})

// 默认展开「体力与副本」及内部全部 5 个子面板
const openGroups = ref(['power'])
const openPowerPanels = ref(['buildTarget', 'war', 'clearPower', 'general', 'plan'])
const openNotifyProviders = ref([])

const yamlSearchQuery = ref('')
const yamlTextareaRef = ref(null)
const gutterRef = ref(null)
let lastSearchIndex = 0

// 与原 WebUI 完全一致的 10 个顶层分组
const formGroups = [
  { name: 'power', title: '体力与副本' },
  { name: 'weeklyPoints', title: '周积分线奖励（Beta）' },
  { name: 'team', title: '队伍配置' },
  { name: 'borrow', title: '支援角色' },
  { name: 'reward', title: '奖励领取' },
  { name: 'daily', title: '日常任务' },
  { name: 'asset', title: '资产管理' },
  { name: 'activity', title: '活动' },
  { name: 'ocr', title: 'OCR 加速' },
  { name: 'notify', title: '消息推送' },
]

const weekDayOptions = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
]

const buildTargetSchemeOptions = [
  { label: '副本名称识别', value: 'instance' },
  { label: '掉落物识别', value: 'drop' },
]

const calyxOptions = [
  { label: '雅利洛-VI', value: 'Jarilo-VI' },
  { label: '仙舟「罗浮」', value: 'XianzhouLuofu' },
  { label: '匹诺康尼', value: 'Penacony' },
]

const ocrOptions = [
  { label: '自动', value: 'auto' },
  { label: 'GPU', value: 'gpu' },
  { label: 'ONNXRuntime + DirectML', value: 'onnx_dml' },
  { label: 'CPU', value: 'cpu' },
  { label: 'OpenVINO CPU', value: 'openvino_cpu' },
  { label: 'ONNXRuntime CPU', value: 'onnx_cpu' },
]

const rewardFields = [
  { key: 'reward_enable', label: '启用领取奖励' },
  { key: 'reward_dispatch_enable', label: '领取委托奖励' },
  { key: 'reward_mail_enable', label: '领取邮件奖励' },
  { key: 'reward_assist_enable', label: '领取支援奖励' },
  { key: 'reward_quest_enable', label: '领取每日实训奖励' },
  { key: 'reward_srpass_enable', label: '领取无名勋礼奖励' },
  { key: 'reward_redemption_code_enable', label: '领取兑换码奖励' },
  { key: 'reward_achievement_enable', label: '领取成就奖励' },
  { key: 'reward_message_enable', label: '领取短信奖励' },
]

const notifyProviders = [
  {
    name: 'pushchanqq',
    title: 'PushChan QQ',
    keys: ['enable', 'endpoint', 'token', 'openid', 'group'],
    fieldLabels: {
      endpoint: 'API 地址',
      openid: 'OpenID / 名称映射',
      group: '群聊推送',
    },
    boolFields: ['enable', 'group'],
  },
  { name: 'telegram', title: 'Telegram', keys: ['enable', 'token', 'userid', 'api_url', 'proxies'] },
  { name: 'matrix', title: 'Matrix', keys: ['enable', 'homeserver', 'device_id', 'user_id', 'access_token', 'room_id', 'proxy', 'separately_text_media'] },
  { name: 'serverchanturbo', title: 'Server酱 Turbo', keys: ['enable', 'sctkey', 'channel', 'openid'] },
  { name: 'serverchan3', title: 'Server酱 3', keys: ['enable', 'sendkey'] },
  { name: 'bark', title: 'Bark', keys: ['enable', 'key', 'group', 'icon', 'isarchive', 'sound', 'url', 'copy', 'autocopy', 'cipherkey', 'ciphermethod'] },
  { name: 'smtp', title: 'SMTP', keys: ['enable', 'host', 'user', 'password', 'From', 'To', 'port', 'ssl', 'starttls', 'ssl_unverified'] },
  { name: 'onebot', title: 'OneBot', keys: ['enable', 'endpoint', 'token', 'user_id', 'group_id'] },
  { name: 'gocqhttp', title: 'Go-cqhttp', keys: ['enable', 'endpoint', 'message_type', 'token', 'user_id', 'group_id'] },
  { name: 'dingtalk', title: '钉钉', keys: ['enable', 'token', 'secret'] },
  { name: 'pushplus', title: 'Pushplus', keys: ['enable', 'token', 'channel', 'webhook', 'callbackUrl'] },
  { name: 'wechatworkapp', title: '企业微信应用', keys: ['enable', 'corpid', 'corpsecret', 'agentid', 'touser', 'base_url'] },
  { name: 'wechatworkbot', title: '企业微信机器人', keys: ['enable', 'key', 'webhook_url'] },
  { name: 'gotify', title: 'Gotify', keys: ['enable', 'url', 'token', 'priority'] },
  { name: 'discord', title: 'Discord', keys: ['enable', 'webhook', 'username', 'avatar_url', 'color'] },
  { name: 'pushdeer', title: 'Pushdeer', keys: ['enable', 'token', 'url'] },
  { name: 'lark', title: '飞书', keys: ['enable', 'webhook', 'content', 'keyword', 'sign', 'imageenable', 'appid', 'secret'] },
  { name: 'kook', title: 'KOOK', keys: ['enable', 'token', 'target_id', 'chat_type'] },
  { name: 'webhook', title: 'Webhook', keys: ['enable', 'url', 'method', 'headers', 'body'] },
  { name: 'custom', title: '自定义通知', keys: ['enable', 'url', 'method', 'datatype', 'image', 'data'] },
  { name: 'meow', title: 'MeoW', keys: ['enable', 'nickname'] },
]

const notifyFieldLabels = {
  enable: '启用',
  token: 'Token',
  userid: '用户/群组 ID',
  api_url: '自定义 API 地址',
  proxies: '代理配置',
  homeserver: '服务器地址',
  device_id: '设备 ID',
  user_id: '私聊用户 ID',
  access_token: '访问令牌',
  room_id: '房间 ID',
  proxy: '代理配置',
  separately_text_media: '文字与图片分开发送',
  sctkey: 'SendKey',
  channel: '发送通道',
  openid: 'OpenID',
  sendkey: 'SendKey',
  key: 'Key',
  group: '分组名',
  icon: '图标地址',
  isarchive: '归档',
  sound: '提示音',
  url: '服务地址',
  copy: '复制内容',
  autocopy: '自动复制',
  cipherkey: '加密密钥',
  ciphermethod: '加密算法',
  host: 'SMTP 服务器',
  user: '用户名/邮箱',
  password: '密码/授权码',
  From: '发件人',
  To: '收件人',
  port: '端口',
  ssl: '启用 SSL',
  starttls: '启用 STARTTLS',
  ssl_unverified: '跳过证书验证',
  endpoint: '服务地址',
  message_type: '消息类型',
  group_id: '群组 ID',
  secret: '密钥',
  webhook: 'Webhook',
  webhook_url: 'Webhook URL',
  callbackUrl: '回调 URL',
  corpid: '企业 ID',
  corpsecret: '应用密钥',
  agentid: 'AgentId',
  touser: '目标用户',
  base_url: '自定义 API 地址',
  priority: '优先级',
  username: '用户名',
  avatar_url: '头像 URL',
  color: '颜色',
  content: '内容',
  keyword: '关键词',
  sign: '签名',
  imageenable: '启用图片信息发送',
  appid: 'AppId',
  target_id: '目标 ID',
  chat_type: '聊天类型',
  method: '请求方法',
  headers: '请求头',
  body: '请求体',
  datatype: '数据类型',
  image: '图片模板',
  data: '数据模板',
  nickname: '昵称',
}

const notifyBoolFields = new Set(['enable', 'ssl', 'starttls', 'ssl_unverified', 'separately_text_media', 'imageenable'])
const notifyNumberFields = new Set(['priority'])

const allInstanceTypes = computed(() => Object.keys(instanceOptions.value || {}))

const characterSelectOptions = computed(() => {
  const list = [{ value: 'None', label: '无' }]
  for (const [key, label] of Object.entries(characterOptions.value || {})) {
    if (key !== 'None') {
      list.push({ value: key, label })
    }
  }
  return list
})

const powerPlans = computed(() => {
  return Array.isArray(cfg.value.power_plan) ? cfg.value.power_plan : []
})

const yamlLineCount = computed(() => {
  if (!rawYaml.value) return 1
  return rawYaml.value.split('\n').length
})

function isGroupOpen(name) {
  return openGroups.value.includes(name)
}

function toggleGroup(name) {
  const idx = openGroups.value.indexOf(name)
  if (idx >= 0) {
    openGroups.value.splice(idx, 1)
  } else {
    openGroups.value.push(name)
  }
}

function isPowerPanelOpen(name) {
  return openPowerPanels.value.includes(name)
}

function togglePowerPanel(name) {
  const idx = openPowerPanels.value.indexOf(name)
  if (idx >= 0) {
    openPowerPanels.value.splice(idx, 1)
  } else {
    openPowerPanels.value.push(name)
  }
}

function isNotifyProviderOpen(name) {
  return openNotifyProviders.value.includes(name)
}

function toggleNotifyProvider(name) {
  const idx = openNotifyProviders.value.indexOf(name)
  if (idx >= 0) {
    openNotifyProviders.value.splice(idx, 1)
  } else {
    openNotifyProviders.value.push(name)
  }
}

function numberField(key, fallback = 0) {
  const val = Number(cfg.value?.[key])
  return Number.isFinite(val) ? val : fallback
}

function setNumberField(key, rawValue, min = 0, max = 999999) {
  let num = Number(rawValue)
  if (!Number.isFinite(num)) num = min
  num = Math.max(min, Math.min(max, num))
  cfg.value[key] = num
}

function setStringNumberField(key, rawValue, min = 0, max = 999999) {
  let num = Number(rawValue)
  if (!Number.isFinite(num)) num = min
  num = Math.max(min, Math.min(max, num))
  cfg.value[key] = String(num)
}

function instanceTypeOptions(includeEcho = true) {
  return allInstanceTypes.value
    .filter((type) => includeEcho || type !== '历战余响')
    .map((type) => ({ label: type, value: type }))
}

function instanceNameOptions(type, includeNone = true) {
  const names = instanceOptions.value?.[type] || {}
  return Object.entries(names)
    .filter(([name]) => includeNone || name !== '无')
    .map(([name, description]) => ({
      value: name,
      label: description ? `${name}（${description}）` : name,
    }))
}

function firstInstanceName(type, includeNone = true) {
  return instanceNameOptions(type, includeNone)[0]?.value || ''
}

function instanceNameValue(type, includeNone = true) {
  const names = cfg.value.instance_names || {}
  return names[type] || firstInstanceName(type, includeNone)
}

function setInstanceType(type) {
  cfg.value.instance_type = type
  if (!cfg.value.instance_names || typeof cfg.value.instance_names !== 'object') {
    cfg.value.instance_names = {}
  }
  if (!cfg.value.instance_names[type]) {
    cfg.value.instance_names[type] = firstInstanceName(type, true)
  }
}

function setInstanceName(type, value) {
  if (!type) return
  if (!cfg.value.instance_names || typeof cfg.value.instance_names !== 'object') {
    cfg.value.instance_names = {}
  }
  cfg.value.instance_names[type] = value
}

function ensurePowerPlanArray() {
  if (!Array.isArray(cfg.value.power_plan)) {
    cfg.value.power_plan = []
  }
  return cfg.value.power_plan
}

function addPowerPlan() {
  const plans = ensurePowerPlanArray()
  if (plans.length >= 8) return
  const currentType = cfg.value.instance_type
  const type =
    allInstanceTypes.value.includes(currentType) && currentType !== '历战余响'
      ? currentType
      : instanceTypeOptions(false)[0]?.value || '侵蚀隧洞'
  plans.push([type, firstInstanceName(type, false), 1])
}

function removePowerPlan(index) {
  const plans = ensurePowerPlanArray()
  plans.splice(index, 1)
}

function movePowerPlanUp(index) {
  if (index <= 0) return
  const plans = ensurePowerPlanArray()
  const tmp = plans[index - 1]
  plans[index - 1] = plans[index]
  plans[index] = tmp
}

function setPowerPlanType(index, type) {
  const plans = ensurePowerPlanArray()
  const currentName = plans[index]?.[1]
  const validNames = instanceNameOptions(type, false).map((item) => item.value)
  plans[index] = [
    type,
    validNames.includes(currentName) ? currentName : firstInstanceName(type, false),
    plans[index]?.[2] || 1,
  ]
}

function setPowerPlanName(index, name) {
  const plans = ensurePowerPlanArray()
  if (plans[index]) {
    plans[index][1] = name
  }
}

function setPowerPlanCount(index, rawCount) {
  const plans = ensurePowerPlanArray()
  if (plans[index]) {
    const count = Math.max(1, Math.min(999, Number(rawCount) || 1))
    plans[index][2] = count
  }
}

function normalizeBorrowFriends() {
  const raw = Array.isArray(cfg.value.borrow_friends) ? cfg.value.borrow_friends : []
  const list = raw.slice(0, 6).map((item) => [item?.[0] || 'None', item?.[1] || ''])
  while (list.length < 6) {
    list.push(['None', ''])
  }
  cfg.value.borrow_friends = list
  return list
}

function borrowFriendAt(index) {
  const friends = cfg.value.borrow_friends
  if (Array.isArray(friends) && friends[index]) {
    return [friends[index][0] || 'None', friends[index][1] || '']
  }
  return ['None', '']
}

function setBorrowFriendCharacter(index, value) {
  const friends = normalizeBorrowFriends()
  friends[index][0] = value || 'None'
}

function setBorrowFriendName(index, value) {
  const friends = normalizeBorrowFriends()
  friends[index][1] = value || ''
}

function providerFieldModels(provider) {
  const customBool = Array.isArray(provider.boolFields) ? new Set(provider.boolFields) : null
  return provider.keys.map((suffix) => ({
    key: `notify_${provider.name}_${suffix}`,
    label: provider.fieldLabels?.[suffix] || notifyFieldLabels[suffix] || suffix,
    type: (customBool ? customBool.has(suffix) : notifyBoolFields.has(suffix))
      ? 'bool'
      : notifyNumberFields.has(suffix)
        ? 'number'
        : 'text',
    min: suffix === 'priority' ? 1 : 0,
    max: suffix === 'priority' ? 10 : 9999,
    defaultValue: suffix === 'priority' ? 3 : 0,
  }))
}

async function fetchOptions() {
  try {
    const res = await apiFetch('/api/options')
    instanceOptions.value = res.instances || {}
    characterOptions.value = res.characters || {}
  } catch {
    // ignore
  }
}

async function loadAccountConfig() {
  if (!selectedAccountId.value) return
  loading.value = true
  try {
    const res = await apiFetch(`/api/accounts/${selectedAccountId.value}/config`)
    cfg.value = res.config || {}
    rawYaml.value = res.raw_yaml || ''
    normalizeBorrowFriends()
  } catch (e) {
    notify(e.message || '加载配置失败', 'error')
  } finally {
    loading.value = false
  }
}

function switchMode(targetMode) {
  editMode.value = targetMode
}

async function handleSaveConfig() {
  if (!selectedAccountId.value) return
  saving.value = true
  try {
    let res
    if (editMode.value === 'advanced') {
      res = await apiFetch(`/api/accounts/${selectedAccountId.value}/config/raw`, {
        method: 'PUT',
        body: JSON.stringify({ raw_yaml: rawYaml.value }),
      })
    } else {
      res = await apiFetch(`/api/accounts/${selectedAccountId.value}/config`, {
        method: 'PUT',
        body: JSON.stringify({ config: cfg.value }),
      })
    }
    if (res.config) {
      cfg.value = res.config
      normalizeBorrowFriends()
    }
    if (res.raw_yaml) rawYaml.value = res.raw_yaml
    notify('配置已保存', 'success')
  } catch (e) {
    notify(e.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function handleResetConfig() {
  if (!selectedAccountId.value) return
  const ok = await confirmModal({
    title: '恢复默认配置',
    message: '确定要将该账号的配置重置为 config.example.yaml 默认值吗？当前自定义修改将被覆盖。',
    confirmText: '确认重置',
    danger: true,
  })
  if (!ok) return
  saving.value = true
  try {
    const res = await apiFetch(`/api/accounts/${selectedAccountId.value}/config/reset`, {
      method: 'POST',
    })
    cfg.value = res.config || {}
    rawYaml.value = res.raw_yaml || ''
    normalizeBorrowFriends()
    notify('已恢复为默认配置', 'info')
  } catch (e) {
    notify(e.message || '重置失败', 'error')
  } finally {
    saving.value = false
  }
}

function syncGutterScroll() {
  if (gutterRef.value && yamlTextareaRef.value) {
    gutterRef.value.scrollTop = yamlTextareaRef.value.scrollTop
  }
}

function handleYamlTab(e) {
  const el = yamlTextareaRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  rawYaml.value = rawYaml.value.substring(0, start) + '  ' + rawYaml.value.substring(end)
  requestAnimationFrame(() => {
    el.selectionStart = el.selectionEnd = start + 2
  })
}

function findNextInYaml() {
  const q = yamlSearchQuery.value.trim()
  const el = yamlTextareaRef.value
  if (!q || !el) return
  const text = rawYaml.value.toLowerCase()
  const target = q.toLowerCase()
  let idx = text.indexOf(target, lastSearchIndex)
  if (idx === -1) {
    idx = text.indexOf(target, 0)
  }
  if (idx === -1) {
    notify(`未找到「${q}」`, 'warning')
    return
  }
  lastSearchIndex = idx + target.length
  el.focus()
  el.setSelectionRange(idx, idx + target.length)
  const lineNumber = rawYaml.value.substring(0, idx).split('\n').length
  const lineHeight = 24
  el.scrollTop = Math.max(0, (lineNumber - 5) * lineHeight)
}

watch(
  () => store.accounts,
  (list) => {
    if (!selectedAccountId.value && Array.isArray(list) && list.length > 0) {
      const qId = route.query.account_id
      if (qId && list.some((a) => a.id === qId)) {
        selectedAccountId.value = qId
      } else {
        selectedAccountId.value = list[0].id
      }
      loadAccountConfig()
    }
  },
  { immediate: true }
)

onMounted(async () => {
  await refreshStatus()
  await fetchOptions()
  if (route.query.account_id && store.accounts.some((a) => a.id === route.query.account_id)) {
    selectedAccountId.value = route.query.account_id
  } else if (!selectedAccountId.value && store.accounts.length > 0) {
    selectedAccountId.value = store.accounts[0].id
  }
  if (selectedAccountId.value) {
    await loadAccountConfig()
  }
})
</script>
