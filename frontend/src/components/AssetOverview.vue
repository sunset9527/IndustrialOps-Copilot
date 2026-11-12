<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  assets: { type: Array, required: true },
})

function modelContext(asset) {
  const controller = asset.controller_or_firmware_scope ? ` / ${asset.controller_or_firmware_scope}` : ''
  return `${asset.manufacturer} ${asset.model_name}${controller}`
}
</script>

<template>
  <section class="asset-overview" aria-labelledby="asset-overview-title">
    <div class="heading">
      <div>
        <p class="eyebrow">ASSET LEDGER</p>
        <h1 id="asset-overview-title">设备总览</h1>
      </div>
      <p>演示资产均为合成数据，仅用于辅助诊断流程展示。</p>
    </div>

    <ul class="asset-list">
      <li v-for="asset in assets" :key="asset.asset_id" class="asset-card">
        <div class="asset-id">{{ asset.asset_id }}</div>
        <div class="content">
          <h2>{{ asset.display_name }}</h2>
          <p>{{ modelContext(asset) }}</p>
          <dl>
            <div><dt>知识包</dt><dd>{{ asset.pack_id }}</dd></div>
            <div><dt>状态</dt><dd>{{ asset.status }}</dd></div>
          </dl>
          <p v-if="asset.synthetic" class="synthetic">合成演示资产</p>
        </div>
        <RouterLink :to="{ name: 'diagnosis', params: { assetId: asset.asset_id } }">进入诊断</RouterLink>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.asset-overview { max-width: 72rem; margin: 0 auto; padding: 32px; }
.heading { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 24px; }
.heading h1 { margin: 0; font-size: 1.75rem; }
.heading > p { max-width: 28rem; margin: 0; color: #5b646c; line-height: 1.5; }
.eyebrow { margin: 0 0 6px; color: #2c596d; font: 700 0.75rem ui-monospace, Consolas, monospace; letter-spacing: 0.08em; }
.asset-list { display: grid; gap: 12px; margin: 0; padding: 0; list-style: none; }
.asset-card { display: grid; grid-template-columns: auto 1fr auto; gap: 20px; align-items: center; padding: 18px; border: 1px solid #bcc3c4; border-radius: 6px; background: #fcfcfa; }
.asset-id, dd { font: 700 0.75rem ui-monospace, Consolas, monospace; }
.asset-id { align-self: start; padding: 6px 8px; border: 1px solid #b8c0c2; border-radius: 3px; background: #e7e9e7; }
h2 { margin: 0; font-size: 1.0625rem; } .content > p { margin: 5px 0; color: #5b646c; }
dl { display: flex; gap: 24px; margin: 12px 0 0; } dt { color: #69747a; font-size: 0.75rem; } dd { margin: 3px 0 0; }
.synthetic { color: #2e6a4e !important; font-size: 0.8125rem; font-weight: 700; }
a { display: inline-grid; min-height: 44px; align-items: center; padding: 0 14px; border-radius: 4px; background: #2c596d; color: #fff; font-weight: 700; text-decoration: none; }
a:focus-visible { outline: 3px solid #d7672e; outline-offset: 2px; }
@media (max-width: 680px) { .asset-overview { padding: 20px; }.heading, .asset-card { grid-template-columns: 1fr; align-items: start; }.heading { align-items: start; flex-direction: column; }.asset-card a { justify-self: stretch; justify-content: center; } }
</style>
