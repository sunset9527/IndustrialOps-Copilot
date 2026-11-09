# IndustrialOps Copilot 前端

Vue 3 项目首页包含 `/health` 检查链接。API 客户端可在内存中保存 Bearer 令牌，遇到 `401` 时清除对应会话，并读取后端的 `error.code` 与 `error.message`。登录页和登录 API 待接入。

在 `frontend` 目录下用 Node.js 22.12 或更新版本运行以下命令。

```powershell
npm.cmd ci
npm.cmd test
npm.cmd run build
npm.cmd run dev
```

开发页面使用 `http://localhost:5174`。API 地址默认为 `http://localhost:8100`。如果需要覆盖，可在启动 Vite 或构建前设置 `VITE_INDUSTRIALOPS_API_BASE_URL`，也可在本目录的 `.env.local` 中设置。构建输出位于 `dist/`。
