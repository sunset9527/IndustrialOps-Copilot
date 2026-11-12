<script setup>
import { computed, inject, ref } from 'vue'

const props = defineProps({ asset: { type: Object, required: true }, diagnosis: { type: Object, required: true } })
const api = inject('api')
const open = ref(false)
const submitted = ref(null)
const title = ref('')
const description = ref('')
const priority = ref('medium')
const allowed = computed(() => props.diagnosis.status === 'answered' && props.diagnosis.inspection_steps?.length > 0)

function show() {
  title.value = `检查 ${props.asset.display_name}`
  description.value = props.diagnosis.candidate_causes?.join('；') || '请根据诊断记录执行人工检查。'
  open.value = true
}
async function submit() {
  submitted.value = await api.request('/api/work-orders/drafts', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ diagnosis_request_id: props.diagnosis.request_id, asset_id: props.asset.asset_id, title: title.value, description: description.value, priority: priority.value }),
  })
}
</script>
<template>
  <section v-if="allowed" class="draft"><button v-if="!open" name="open-draft" type="button" @click="show">生成工单草稿</button><form v-else-if="!submitted" @submit.prevent="submit"><label>标题<input v-model="title" name="title" required></label><label>说明<textarea v-model="description" name="description" required /></label><label>优先级<select v-model="priority" name="priority"><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label><button type="submit">提交草稿</button></form><div v-else class="pending"><strong>等待人工审批</strong><span>工单：{{ submitted.work_order_id }}</span><code>{{ submitted.thread_id }}</code></div></section>
</template>
<style scoped>.draft{margin-top:12px}.draft button{min-height:44px;padding:0 16px;border:0;border-radius:4px;background:#2c596d;color:#fff;font-weight:700;cursor:pointer}.draft form{display:grid;gap:8px;padding:16px;border:1px solid #c4cbcc;border-radius:6px;background:#fcfcfa}.draft label{display:grid;gap:4px;font-size:.875rem;font-weight:700}.draft input,.draft textarea,.draft select{min-height:40px;padding:8px;border:1px solid #b1babd;border-radius:4px;font:inherit}.draft textarea{min-height:72px}.pending{display:grid;gap:6px;padding:14px;border-left:4px solid #d7672e;background:#fff1e8}.pending code{font-size:.75rem;overflow-wrap:anywhere}</style>
