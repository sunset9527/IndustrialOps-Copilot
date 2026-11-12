<script setup>
import { computed, inject, ref } from 'vue'

const props = defineProps({ workOrder: { type: Object, required: true }, role: { type: String, required: true } })
const api = inject('api')
const status = ref(props.workOrder.status)
const canApprove = computed(() => ['approver', 'admin'].includes(props.role))

async function approve() {
  const response = await api.request(`/api/work-orders/${props.workOrder.work_order_id}/approve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason: null }),
  })
  status.value = response.status
}
</script>

<template>
  <section class="approval"><h2>人工审批</h2><p>当前状态：<strong>{{ status }}</strong></p><button v-if="canApprove" name="approve" type="button" @click="approve">批准工单</button></section>
</template>

<style scoped>.approval{padding:16px;border:1px solid #c4cbcc;border-radius:6px;background:#fcfcfa}.approval h2{margin:0;font-size:1rem}.approval p{color:#5c686f}button{min-height:44px;padding:0 16px;border:0;border-radius:4px;background:#2e6a4e;color:#fff;font-weight:700;cursor:pointer}</style>
