# v0.8 RC 本机发布验收

**状态：** `release_verified`（2026-11-22）  
**本地报告：** `data/evaluation/reports/v08/v08-full-20261122-01/report.json`（Git 忽略，不含私有资料、路径、密码或会话令牌）

## 隔离边界

验收使用独立 Compose 项目 `industrialops_rc_v08_full_20261122_01`，API/Web 分别使用回环端口 `18100` / `15174`。知识包和本地模型为只读挂载；默认 `industrialops` Compose 资源未被操作。

## 强制项结果

| 项目 | 结果 | 证据摘要 |
| --- | --- | --- |
| 无缓存冷启动 | 通过 | 镜像构建后，bootstrap 完成迁移、合成资产、两个冻结包与索引准备；API/Web 就绪。 |
| HTTP 主链路 | 通过 | CNC 552 与 nXDS10i 维护查询均为 `answered`，引用各自知识包；草稿、普通用户 403、approver 批准及 API 重启恢复均通过。 |
| 故障矩阵 | 通过 | 受控容器检查观察到 `MODEL_UNAVAILABLE`、`PACK_UNAVAILABLE`、`INDEX_UNAVAILABLE`、`DATABASE_UNAVAILABLE` 并恢复；本地 MockTransport 契约覆盖 LLM 超时、LLM 请求拒绝和离线零出站。 |
| 基线 | 通过 | `/ready` 十次观测：最小 698.87 ms、中位 723.24 ms、p95 873.95 ms、最大 873.95 ms；3 个并发只读请求均为 200。数值为观测值，不是性能阈值或泛化承诺。 |
| 浏览器 | 通过 | Chrome/CDP 完成普通用户注册、两台设备切换与诊断、证据展示、草稿和 approver 页面验证。 |
| 声明真实性 | 通过 | README、架构、数据边界、离线策略和审批恢复主张均由版本化清单与自动化测试核对。 |
| 回归 | 通过 | v0.8 定向测试、全仓 Python 回归、前端 12 文件/22 测试及 Vite 生产构建通过。 |

## 结论与边界

本验收只证明本机、冻结输入、离线模式和上述运行环境下的发布候选交付闭环；它不代表现场设备控制授权、厂商资料再分发权、在线模型泛化能力或长期性能 SLA。v1.0 阶段才负责版本冻结与正式发布。
