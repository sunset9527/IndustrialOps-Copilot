<script setup>
import { inject } from 'vue'
import { useRouter } from 'vue-router'

const auth = inject('auth')
const router = useRouter()
const currentUser = auth.user

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <RouterView v-slot="{ Component, route }">
    <component :is="Component" v-if="route.meta.public" />
    <div v-else class="app-shell"><header><div><strong>INDUSTRIALOPS</strong><span>证据驱动工业运维</span></div><div class="session"><span>{{ currentUser.username }} · {{ currentUser.role }}</span><button aria-label="退出登录" type="button" @click="logout">退出</button></div></header><nav aria-label="主导航"><RouterLink to="/assets">设备总览</RouterLink><RouterLink to="/work-orders">工单审批</RouterLink></nav><component :is="Component" /></div>
  </RouterView>
</template>

<style>
:root {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  color: #20262d;
  background: #e7e9e7;
}
body { margin: 0; }.app-shell { min-height:100dvh; background:#f3f4f2; }.app-shell > header { display:flex;align-items:center;justify-content:space-between;gap:12px;padding:18px 32px;background:#242b31;color:#fff; }.app-shell > header strong{letter-spacing:.1em}.app-shell > header span{color:#aeb8bd;font-size:.8125rem}.session{display:flex;align-items:center;gap:12px}.session button{min-height:36px;border:1px solid #7d8a90;border-radius:4px;background:transparent;color:#fff;font:inherit}.app-shell > nav{display:flex;gap:4px;padding:10px 32px;background:#303941}.app-shell > nav a{padding:10px 12px;border-radius:4px;color:#c9d0d3;font-size:.875rem;font-weight:700;text-decoration:none}.app-shell > nav a.router-link-active{border-left:3px solid #d7672e;background:#3b454d;color:#fff}
</style>
