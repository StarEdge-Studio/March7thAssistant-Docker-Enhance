<template>
  <Transition name="m3-dialog">
    <div
      v-if="visible"
      class="fixed inset-0 z-[85] flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="m3-notice-modal-title"
    >
      <div
        class="m3-dialog-panel flex max-h-[88vh] w-full max-w-xl flex-col overflow-hidden rounded-[28px] border border-[var(--m3-outline-variant)]/60 bg-[var(--m3-surface-container-lowest)] shadow-2xl"
        @click.stop
      >
        <!-- Header -->
        <div
          class="flex shrink-0 items-start gap-3.5 border-b border-[var(--m3-outline-variant)]/40 bg-[var(--m3-surface-container-low)] px-6 py-5"
        >
          <div
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--m3-primary-container)] text-[var(--m3-on-primary-container)]"
          >
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
              />
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <span
              class="inline-flex items-center rounded-full bg-[var(--m3-secondary-container)] px-2.5 py-0.5 text-[11px] font-bold tracking-wide text-[var(--m3-on-secondary-container)]"
            >
              {{ notice.badge }}
            </span>
            <h2
              id="m3-notice-modal-title"
              class="mt-1.5 text-lg font-extrabold leading-snug text-[var(--m3-on-surface)]"
            >
              {{ notice.title }}
            </h2>
            <p class="mt-0.5 text-xs text-[var(--m3-on-surface-variant)]">
              {{ notice.subtitle }}
            </p>
          </div>
        </div>

        <!-- Scrollable Notice Body -->
        <div class="flex-1 space-y-3.5 overflow-y-auto px-6 py-5">
          <div
            v-for="section in notice.sections"
            :key="section.id"
            class="rounded-2xl border p-4"
            :class="sectionClass(section.tone)"
          >
            <div class="flex items-center gap-2">
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg"
                :class="iconBadgeClass(section.tone)"
              >
                <svg
                  v-if="section.icon === 'ban'"
                  class="h-3.5 w-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                >
                  <circle cx="12" cy="12" r="9" />
                  <path stroke-linecap="round" d="M5.64 5.64l12.72 12.72" />
                </svg>
                <svg
                  v-else-if="section.icon === 'alert'"
                  class="h-3.5 w-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                  />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01" />
                </svg>
                <svg
                  v-else
                  class="h-3.5 w-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
                  />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4" />
                </svg>
              </span>
              <h3 class="text-sm font-bold text-[var(--m3-on-surface)]">
                {{ section.title }}
              </h3>
            </div>
            <ul class="mt-2.5 space-y-1.5 text-xs leading-relaxed text-[var(--m3-on-surface-variant)]">
              <li v-for="(item, idx) in section.items" :key="idx" class="flex items-start gap-2">
                <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-60"></span>
                <span>
                  <template v-for="(seg, sIdx) in normalizeNoticeSegments(item)" :key="sIdx">
                    <span v-if="seg.highlight" :class="highlightClass(seg.highlight)">{{ seg.text }}</span>
                    <template v-else>{{ seg.text }}</template>
                  </template>
                </span>
              </li>
            </ul>
          </div>

          <!-- Open Source Repository Links -->
          <div
            class="rounded-2xl border border-[var(--m3-outline-variant)]/50 bg-[var(--m3-surface-container)] p-4"
          >
            <div class="flex items-center gap-2 text-xs font-bold text-[var(--m3-on-surface)]">
              <svg class="h-4 w-4 text-[var(--m3-primary)]" viewBox="0 0 24 24" fill="currentColor">
                <path
                  fill-rule="evenodd"
                  clip-rule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                />
              </svg>
              <span>开源项目地址</span>
            </div>
            <div class="mt-2.5 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <a
                :href="originalRepoUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-center justify-between gap-2 rounded-xl border border-[var(--m3-outline-variant)]/50 bg-[var(--m3-surface-container-lowest)] px-3 py-2 text-xs transition hover:border-[var(--m3-primary)] hover:bg-[var(--m3-primary-container)]/35"
              >
                <div class="min-w-0">
                  <div class="font-semibold text-[var(--m3-on-surface)]">原项目 · March7thAssistant</div>
                  <div class="truncate font-mono text-[11px] text-[var(--m3-on-surface-variant)]">
                    moesnow/March7thAssistant
                  </div>
                </div>
                <svg
                  class="h-3.5 w-3.5 shrink-0 text-[var(--m3-primary)]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 3h6v6M10 14L21 3" />
                </svg>
              </a>
              <a
                :href="projectRepoUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-center justify-between gap-2 rounded-xl border border-[var(--m3-outline-variant)]/50 bg-[var(--m3-surface-container-lowest)] px-3 py-2 text-xs transition hover:border-[var(--m3-primary)] hover:bg-[var(--m3-primary-container)]/35"
              >
                <div class="min-w-0">
                  <div class="font-semibold text-[var(--m3-on-surface)]">本项目 · Docker-Enhance</div>
                  <div class="truncate font-mono text-[11px] text-[var(--m3-on-surface-variant)]">
                    staredge-studio/...-Docker-Enhance
                  </div>
                </div>
                <svg
                  class="h-3.5 w-3.5 shrink-0 text-[var(--m3-primary)]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 3h6v6M10 14L21 3" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        <!-- Sticky Footer with Mandatory Countdown -->
        <div
          class="flex shrink-0 flex-col gap-2.5 border-t border-[var(--m3-outline-variant)]/40 bg-[var(--m3-surface-container-low)] px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <p class="text-[11px] text-[var(--m3-on-surface-variant)]">
            {{
              canConfirm
                ? '阅读计时已完成，确认后本设备同一身份不再弹出'
                : `请仔细阅读上述内容，剩余 ${countdown} 秒后可确认`
            }}
          </p>
          <button
            type="button"
            class="m3-btn m3-btn-filled w-full shrink-0 whitespace-nowrap px-6 py-2.5 text-sm disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            :disabled="!canConfirm"
            @click="confirmNotice"
          >
            {{ canConfirm ? '我已知晓并同意' : `请认真阅读须知 (${countdown}s)` }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { getNoticeHighlightClass, normalizeNoticeSegments, useNoticeModal } from '../../notice.js'

const props = defineProps({
  isStandalone: {
    type: Boolean,
    default: false,
  },
})

const {
  visible,
  countdown,
  canConfirm,
  notice,
  confirmNotice,
  originalRepoUrl,
  projectRepoUrl,
} = useNoticeModal(() => props.isStandalone)

const highlightClass = getNoticeHighlightClass

const sectionClass = (tone) => {
  if (tone === 'danger') {
    return 'border-[var(--m3-error)]/30 bg-[var(--m3-error-container)]/30'
  }
  if (tone === 'primary') {
    return 'border-[var(--m3-primary)]/25 bg-[var(--m3-primary-container)]/30'
  }
  return 'border-[var(--m3-outline-variant)]/50 bg-[var(--m3-surface-container)]'
}

const iconBadgeClass = (tone) => {
  if (tone === 'danger') {
    return 'bg-[var(--m3-error-container)] text-[var(--m3-on-error-container)]'
  }
  if (tone === 'primary') {
    return 'bg-[var(--m3-primary-container)] text-[var(--m3-on-primary-container)]'
  }
  return 'bg-[var(--m3-surface-container-highest)] text-[var(--m3-on-surface-variant)]'
}
</script>
