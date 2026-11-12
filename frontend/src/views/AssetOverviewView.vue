<script setup>
import { inject, onMounted, ref } from 'vue'

import AssetOverview from '../components/AssetOverview.vue'

const api = inject('api')
const assets = ref([])
const state = ref('loading')

async function loadAssets() {
  state.value = 'loading'
  try {
    const response = await api.request('/api/equipment/assets')
    assets.value = response.items
    state.value = 'success'
  } catch {
    state.value = 'error'
  }
}

onMounted(loadAssets)
</script>

<template>
  <main v-if="state === 'loading'" class="state-panel" aria-busy="true">正在加载设备台账…</main>
  <main v-else-if="state === 'error'" class="state-panel" role="alert">
    <p>暂时无法加载设备，请检查网络后重试。</p>
    <button type="button" @click="loadAssets">重试</button>
  </main>
  <main v-else-if="assets.length === 0" class="state-panel">
    <p>当前没有可用的演示设备。</p>
  </main>
  <AssetOverview v-else :assets="assets" />
</template>

<style scoped>
.state-panel { display: grid; min-height: 18rem; place-content: center; gap: 12px; padding: 32px; color: #536067; text-align: center; }
button { min-height: 44px; padding: 0 16px; border: 0; border-radius: 4px; background: #2c596d; color: #fff; font-weight: 700; cursor: pointer; }
button:focus-visible { outline: 3px solid #d7672e; outline-offset: 2px; }
</style>
