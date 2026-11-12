<template>
  <RouterView v-slot="{ Component, route }">
    <component :is="Component" v-if="route.meta.public" />
    <div v-else class="app-shell"><header><strong>INDUSTRIALOPS</strong><span>证据驱动工业运维</span></header><nav aria-label="主导航"><RouterLink to="/assets">设备总览</RouterLink><RouterLink to="/work-orders">工单审批</RouterLink></nav><component :is="Component" /></div>
  </RouterView>
</template>

<style>
:root {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  color: #20262d;
  background: #e7e9e7;
}
body { margin: 0; }.app-shell { min-height:100dvh; background:#f3f4f2; }.app-shell > header { display:flex;align-items:baseline;gap:12px;padding:18px 32px;background:#242b31;color:#fff; }.app-shell > header strong{letter-spacing:.1em}.app-shell > header span{color:#aeb8bd;font-size:.8125rem}.app-shell > nav{display:flex;gap:4px;padding:10px 32px;background:#303941}.app-shell > nav a{padding:10px 12px;border-radius:4px;color:#c9d0d3;font-size:.875rem;font-weight:700;text-decoration:none}.app-shell > nav a.router-link-active{border-left:3px solid #d7672e;background:#3b454d;color:#fff}
</style>
