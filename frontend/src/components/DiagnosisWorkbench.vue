<script setup>
import { inject, ref, watch } from 'vue'

import DiagnosisResult from './DiagnosisResult.vue'

const props = defineProps({
  asset: { type: Object, required: true },
})

const api = inject('api')
const question = ref('')
const result = ref(null)

watch(() => props.asset.asset_id, () => {
  result.value = null
})

async function submit() {
  result.value = await api.request('/api/diagnosis/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: question.value,
      pack_id: props.asset.pack_id,
      asset_id: props.asset.asset_id,
      model: props.asset.model_name,
      controller: props.asset.controller_or_firmware_scope,
    }),
  })
}
</script>

<template>
  <section class="workbench" aria-labelledby="diagnosis-title">
    <header>
      <p class="eyebrow">DIAGNOSIS WORKBENCH</p>
      <h1 id="diagnosis-title">设备故障诊断</h1>
      <p>{{ asset.display_name }} · {{ asset.pack_id }}</p>
    </header>
    <form @submit.prevent="submit">
      <label for="question">描述报警码、故障现象和已执行检查</label>
      <textarea id="question" v-model="question" name="question" required />
      <button type="submit">运行诊断</button>
    </form>
    <DiagnosisResult v-if="result" :result="result" />
  </section>
</template>

<style scoped>
.workbench { display: grid; gap: 16px; max-width: 56rem; margin: 0 auto; padding: 32px; }.eyebrow { margin: 0 0 5px; color: #2c596d; font: 700 0.7rem ui-monospace, Consolas, monospace; letter-spacing: 0.08em; } h1 { margin: 0; font-size: 1.75rem; } header > p:last-child { margin: 8px 0 0; color: #5c686f; font-size: 0.875rem; } form { display: grid; gap: 8px; padding: 16px; border: 1px solid #c4cbcc; border-radius: 6px; background: #fcfcfa; } label { font-size: 0.875rem; font-weight: 700; } textarea { min-height: 96px; resize: vertical; border: 1px solid #b1babd; border-radius: 4px; padding: 10px; font: inherit; line-height: 1.5; } button { justify-self: end; min-height: 44px; padding: 0 16px; border: 0; border-radius: 4px; background: #2c596d; color: #fff; font-weight: 700; cursor: pointer; } textarea:focus-visible, button:focus-visible { outline: 3px solid #d7672e; outline-offset: 2px; }
</style>
