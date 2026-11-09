<script setup>
import { createApiClient } from './api/client.js'

const api = createApiClient()
</script>

<template>
  <header>
    <nav aria-label="主导航">
      <a href="#main">IndustrialOps Copilot</a>
    </nav>
  </header>
  <main id="main">
    <h1>IndustrialOps Copilot</h1>
    <p>工业运维项目首页。工作台功能待接入。</p>
    <a :href="`${api.baseUrl}/health`">查看 API 健康状态</a>
  </main>
</template>

<style>
:root {
  font-family: system-ui, sans-serif;
  color: #192c38;
  background: #f6f8fa;
}

body {
  margin: 0;
}

header {
  background: #fff;
  border-bottom: 1px solid #d7dfe4;
}

nav,
main {
  max-width: 52rem;
  margin: auto;
  padding: 1rem;
}

nav a {
  color: inherit;
  font-weight: 650;
}

main {
  padding-block: 3rem;
}

main a {
  color: #075985;
}
</style>
