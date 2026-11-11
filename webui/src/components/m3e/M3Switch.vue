<template>
  <button
    type="button"
    role="switch"
    :aria-checked="!!modelValue"
    :disabled="disabled"
    class="group relative inline-flex items-center w-[52px] h-8 rounded-full shrink-0 cursor-pointer transition-colors duration-250 focus:outline-none disabled:opacity-45 disabled:cursor-not-allowed select-none"
    :style="trackStyle"
    @click.stop="toggle"
  >
    <span
      class="flex items-center justify-center rounded-full transition-all duration-300 group-hover:scale-105 group-active:scale-x-125 group-active:scale-y-95"
      :style="thumbStyle"
    >
      <svg
        class="w-3.5 h-3.5 transition-all duration-300"
        :class="modelValue ? 'scale-100 rotate-0 opacity-100' : 'scale-0 -rotate-45 opacity-0'"
        :style="{ color: 'var(--m3-primary)', transitionTimingFunction: 'var(--m3-spring)' }"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
      </svg>
    </span>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

function toggle() {
  if (props.disabled) return
  const next = !props.modelValue
  emit('update:modelValue', next)
  emit('change', next)
}

const trackStyle = computed(() => {
  if (props.modelValue) {
    return {
      backgroundColor: 'var(--m3-primary)',
      border: '2px solid var(--m3-primary)',
    }
  }
  return {
    backgroundColor: 'var(--m3-surface-container-highest)',
    border: '2px solid var(--m3-outline)',
  }
})

const thumbStyle = computed(() => {
  if (props.modelValue) {
    return {
      width: '24px',
      height: '24px',
      transform: 'translateX(22px)',
      backgroundColor: 'var(--m3-on-primary)',
      transitionTimingFunction: 'var(--m3-spring)',
    }
  }
  return {
    width: '16px',
    height: '16px',
    transform: 'translateX(6px)',
    backgroundColor: 'var(--m3-outline)',
    transitionTimingFunction: 'var(--m3-spring)',
  }
})
</script>
