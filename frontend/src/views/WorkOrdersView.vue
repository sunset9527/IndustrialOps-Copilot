<script setup>
import { inject, onMounted, ref } from 'vue'

const api = inject('api')
const workOrders = ref([])
const error = ref(false)

onMounted(async () => {
  try { workOrders.value = (await api.request('/api/work-orders')).items } catch { error.value = true }
})
</script>

<template>
  <main class="orders">
    <p class="eyebrow">WORK ORDER QUEUE</p><h1>工单审批</h1>
    <p v-if="error" role="alert">暂时无法加载工单，请稍后重试。</p>
    <p v-else-if="workOrders.length === 0">当前没有待处理工单。</p>
    <ul v-else><li v-for="order in workOrders" :key="order.work_order_id"><strong>{{ order.work_order_id }}</strong><span>{{ order.title }}</span><span>{{ order.status }}</span></li></ul>
  </main>
</template>

<style scoped>.orders{max-width:72rem;margin:0 auto;padding:32px}.eyebrow{margin:0 0 5px;color:#2c596d;font:700 .7rem ui-monospace,Consolas,monospace;letter-spacing:.08em}h1{margin:0 0 20px}ul{display:grid;gap:8px;padding:0;list-style:none}li{display:grid;grid-template-columns:12rem 1fr auto;gap:12px;padding:14px;border:1px solid #c4cbcc;border-radius:5px;background:#fcfcfa}strong{font:700 .75rem ui-monospace,Consolas,monospace}</style>
