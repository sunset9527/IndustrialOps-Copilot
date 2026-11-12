import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8100',
      '/health': 'http://127.0.0.1:8100',
      '/ready': 'http://127.0.0.1:8100',
    },
  },
})
