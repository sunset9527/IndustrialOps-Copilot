<script setup>
import { inject, ref } from 'vue'
import { useRouter } from 'vue-router'

const auth = inject('auth')
const router = useRouter()
const username = ref('')
const password = ref('')
const errorMessage = ref('')

async function submit() {
  errorMessage.value = ''
  try {
    await auth.login({ username: username.value, password: password.value })
    await router.push({ name: 'assets' })
  } catch (error) {
    errorMessage.value = error.code === 'invalid_credentials'
      ? '用户名或密码不正确，请重新输入。'
      : '暂时无法登录，请检查网络后重试。'
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel" aria-labelledby="login-title">
      <p class="eyebrow">INDUSTRIALOPS / SECURE ACCESS</p>
      <h1 id="login-title">登录运维工作台</h1>
      <p class="intro">使用项目演示账号进入设备诊断与工单审批流程。</p>
      <form @submit.prevent="submit">
        <label for="username">用户名</label>
        <input id="username" v-model="username" name="username" autocomplete="username" required>

        <label for="password">密码</label>
        <input id="password" v-model="password" name="password" type="password" autocomplete="current-password" required>

        <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
        <button type="submit">登录并进入设备总览</button>
      </form>
      <RouterLink to="/register">没有账号？注册普通用户</RouterLink>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100dvh;
  place-items: center;
  padding: 24px;
  background: #e7e9e7;
}

.login-panel {
  width: min(100%, 26rem);
  padding: 32px;
  border: 1px solid #b9c0c1;
  border-radius: 8px;
  background: #fcfcfa;
  box-shadow: 0 12px 32px rgb(31 40 45 / 12%);
}

.eyebrow {
  margin: 0 0 12px;
  color: #2c596d;
  font: 700 0.75rem ui-monospace, Consolas, monospace;
  letter-spacing: 0.08em;
}

h1 { margin: 0; font-size: 1.75rem; }
.intro { color: #59646b; line-height: 1.6; }
form { display: grid; gap: 8px; margin-top: 24px; }
label { font-weight: 700; font-size: 0.875rem; }
input, button { min-height: 44px; border-radius: 4px; font: inherit; }
input { margin-bottom: 10px; border: 1px solid #aeb7b9; padding: 0 12px; }
.form-error { margin: 4px 0 0; color: #9b2c20; font-size: 0.875rem; line-height: 1.5; }
button { margin-top: 8px; border: 0; background: #2c596d; color: #fff; font-weight: 700; cursor: pointer; }
input:focus-visible, button:focus-visible { outline: 3px solid #d7672e; outline-offset: 2px; }
</style>
