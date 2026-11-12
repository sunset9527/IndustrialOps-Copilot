<script setup>
defineProps({
  result: { type: Object, required: true },
})

const sections = [
  ['已确认事实', 'confirmed_facts'],
  ['候选原因', 'candidate_causes'],
  ['建议检查顺序', 'inspection_steps'],
  ['安全前置条件', 'safety_prerequisites'],
  ['不确定性', 'uncertainties'],
  ['仍需补充的信息', 'required_information'],
  ['人工升级条件', 'escalation_conditions'],
]
</script>

<template>
  <section class="result" aria-labelledby="diagnosis-result-title">
    <header>
      <div>
        <p class="eyebrow">EVIDENCE-BOUND OUTPUT</p>
        <h2 id="diagnosis-result-title">诊断结果</h2>
      </div>
      <span class="status">{{ result.status }}</span>
    </header>

    <div v-for="([label, key]) in sections" :key="key" class="section" :class="{ safety: key === 'safety_prerequisites' }">
      <template v-if="result[key]?.length">
        <h3>{{ label }}</h3>
        <ul><li v-for="item in result[key]" :key="item">{{ item }}</li></ul>
      </template>
    </div>

    <section v-if="result.citations?.length" class="citations" aria-label="来源引用">
      <h3>来源引用</h3>
      <article v-for="citation in result.citations" :key="`${citation.source_id}-${citation.page_number}`">
        <strong>{{ citation.source_id }} · 修订版 {{ citation.document_revision }} · 第 {{ citation.page_number }} 页</strong>
        <code>{{ citation.evidence_locator }}</code>
      </article>
    </section>
  </section>
</template>

<style scoped>
.result { border: 1px solid #c4cbcc; border-radius: 6px; background: #fcfcfa; }
header { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px; border-bottom: 1px solid #d9dddd; }
.eyebrow { margin: 0 0 4px; color: #2c596d; font: 700 0.7rem ui-monospace, Consolas, monospace; letter-spacing: 0.08em; }
h2 { margin: 0; font-size: 1.125rem; } h3 { margin: 0 0 8px; font-size: 0.875rem; }
.status { padding: 5px 7px; border: 1px solid #7ca88f; border-radius: 3px; color: #2e6a4e; font: 700 0.7rem ui-monospace, Consolas, monospace; }
.section, .citations { padding: 14px 16px; border-bottom: 1px solid #e0e4e4; }.section:last-of-type { border-bottom: 0; }
.safety { border-left: 4px solid #d7672e; background: #fff1e8; } ul { display: grid; gap: 7px; margin: 0; padding-left: 20px; color: #48545b; line-height: 1.5; }
.citations { background: #f3f5f4; }.citations article { display: grid; gap: 5px; margin-top: 8px; padding: 10px; border: 1px solid #d4dada; border-radius: 4px; background: #fff; font-size: 0.8125rem; }.citations code { color: #68757b; font-size: 0.75rem; overflow-wrap: anywhere; }
</style>
