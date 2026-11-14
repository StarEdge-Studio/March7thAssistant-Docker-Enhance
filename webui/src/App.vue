<template>
  <SimpleApp v-if="store.uiTheme === 'simple'" />
  <M3EApp v-else />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import M3EApp from './M3EApp.vue'
import SimpleApp from './SimpleApp.vue'
import { refreshStatus, store } from './state.js'

let statusTimer = null
onMounted(() => {
  refreshStatus()
  statusTimer = setInterval(() => {
    if (store.token && store.role && store.role !== 'unauthorized') {
      refreshStatus()
    }
  }, 3000)
})

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
})
</script>
