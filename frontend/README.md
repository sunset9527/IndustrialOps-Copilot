# IndustrialOps Copilot 前端

Vue 3 工业运维工作台包含登录、设备总览、设备诊断、证据/安全/不确定性展示、证据绑定工单草稿与工单审批。设备包、型号和控制器上下文全部来自服务端资产响应；切换资产会清除旧诊断结果，避免 CNC 与真空泵资料串用。设备与工单均为合成演示数据，系统不控制真实设备。

在 `frontend` 目录下用 Node.js 22.12 或更新版本运行以下命令。

```powershell
npm.cmd ci
npm.cmd test
npm.cmd run build
npm.cmd run dev
```

开发页面使用 `http://localhost:5174`。默认通过 Vite 同源代理访问 `http://127.0.0.1:8100` 的 `/api`、`/health` 和 `/ready`；如需直连其他 API 地址，可在启动前设置 `VITE_INDUSTRIALOPS_API_BASE_URL`。构建输出位于 `dist/`。
