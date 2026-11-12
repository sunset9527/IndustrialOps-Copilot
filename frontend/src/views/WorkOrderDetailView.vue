<script setup>
import { inject, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ApprovalPanel from '../components/ApprovalPanel.vue'
const api = inject('api'); const auth = inject('auth'); const route = useRoute(); const order = ref(null); const error = ref(false)
async function load() { try { order.value = await api.request(`/api/work-orders/${route.params.workOrderId}`); error.value = false } catch { error.value = true } }
onMounted(load)
</script>
<template><main v-if="order" class="detail"><p class="eyebrow">WORK ORDER DETAIL</p><h1>{{ order.title }}</h1><p>状态：{{ order.status }}</p><section><h2>证据快照</h2><ul><li v-for="citation in order.citations_snapshot" :key="`${citation.source_id}-${citation.page_number}`">{{ citation.source_id }} · 第 {{ citation.page_number }} 页</li></ul></section><ApprovalPanel :work-order="order" :role="auth.user.value.role" @refresh="load" /></main><main v-else-if="error" role="alert">暂时无法加载工单详情。</main><main v-else aria-busy="true">正在加载工单详情…</main></template>
<style scoped>.detail{max-width:56rem;margin:0 auto;padding:32px}.eyebrow{margin:0;color:#2c596d;font:700 .7rem ui-monospace,Consolas,monospace;letter-spacing:.08em}.detail section{margin:16px 0;padding:14px;border:1px solid #c4cbcc;border-radius:6px;background:#fcfcfa}.detail h2{font-size:1rem}</style>
