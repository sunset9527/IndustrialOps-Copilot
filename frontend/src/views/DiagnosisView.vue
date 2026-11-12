<script setup>
import { inject, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import DiagnosisWorkbench from '../components/DiagnosisWorkbench.vue'

const api = inject('api')
const route = useRoute()
const asset = ref(null)
const error = ref(false)

onMounted(async () => {
  try {
    const response = await api.request('/api/equipment/assets')
    asset.value = response.items.find((item) => item.asset_id === route.params.assetId) ?? null
    error.value = asset.value === null
  } catch {
    error.value = true
  }
})
</script>

<template>
  <DiagnosisWorkbench v-if="asset" :asset="asset" />
  <main v-else-if="error" class="state" role="alert">未找到该设备，或暂时无法加载设备上下文。</main>
  <main v-else class="state" aria-busy="true">正在加载设备上下文…</main>
</template>

<style scoped>.state { display:grid; min-height:18rem; place-content:center; padding:24px; color:#536067; }</style>
