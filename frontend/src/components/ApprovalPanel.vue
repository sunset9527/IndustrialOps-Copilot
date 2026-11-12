<script setup>
import { computed, inject, ref } from 'vue'

const props = defineProps({ workOrder: { type: Object, required: true }, role: { type: String, required: true } })
const emit = defineEmits(['refresh'])
const api = inject('api')
const status = ref(props.workOrder.status)
const canApprove = computed(() => ['approver', 'admin'].includes(props.role))
const rejectionReason = ref('')
const errorMessage = ref('')

async function approve() {
  try { const response = await api.request(`/api/work-orders/${props.workOrder.work_order_id}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason: null }) }); status.value = response.status } catch (error) { if (error.code === 'approval_already_decided' || error.code === 'stale_resource_version') emit('refresh'); else throw error }
}

async function reject() {
  if (!rejectionReason.value.trim()) {
    errorMessage.value = '请填写拒绝理由。'
    return
  }
  errorMessage.value = ''
  try { const response = await api.request(`/api/work-orders/${props.workOrder.work_order_id}/reject`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason: rejectionReason.value }) }); status.value = response.status } catch (error) { if (error.code === 'approval_already_decided' || error.code === 'stale_resource_version') emit('refresh'); else throw error }
}
</script>

<template>
  <section class="approval"><h2>人工审批</h2><p>当前状态：<strong>{{ status }}</strong></p><template v-if="canApprove"><label for="rejectionReason">拒绝理由</label><textarea id="rejectionReason" v-model="rejectionReason" name="rejectionReason" /><p v-if="errorMessage" role="alert">{{ errorMessage }}</p><div class="actions"><button name="approve" type="button" @click="approve">批准工单</button><button name="reject" type="button" @click="reject">拒绝工单</button></div></template></section>
</template>

<style scoped>.approval{display:grid;gap:8px;padding:16px;border:1px solid #c4cbcc;border-radius:6px;background:#fcfcfa}.approval h2{margin:0;font-size:1rem}.approval p{color:#5c686f}.approval label{font-size:.875rem;font-weight:700}.approval textarea{min-height:72px;padding:8px;border:1px solid #b1babd;border-radius:4px;font:inherit}.approval [role="alert"]{margin:0;color:#9b2c20}.actions{display:flex;gap:8px}.actions button{min-height:44px;padding:0 16px;border:0;border-radius:4px;color:#fff;font-weight:700;cursor:pointer}.actions button[name="approve"]{background:#2e6a4e}.actions button[name="reject"]{background:#9b2c20}</style>
