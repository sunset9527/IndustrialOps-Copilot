# v0.7 本机 Uvicorn HTTP 验收

**日期：** 2026-11-20  
**状态：** 已完成（仅限本机隔离验收）

## 隔离边界

- 数据库：`industrialops_v07_validation`；仅包含项目迁移、两条 `synthetic=true` 演示资产和本次验收账户/工单；
- 服务：临时 Uvicorn，`127.0.0.1:8117`，每次验收结束后停止；
- 推理：`INDUSTRIALOPS_OFFLINE=true`，只使用已存在的 BGE-M3、reranker、冻结知识包和本地索引；
- 初始化：`industrialops.bootstrap` 已完成预检、迁移、synthetic 资产幂等初始化、两个冻结包验证和两个本地索引构建。

## 验收结果

| 场景 | 可观察结果 |
| --- | --- |
| 存活接口 | `GET /health` 返回 `200` 与 `{"status":"ok","product":"IndustrialOps Copilot"}`。 |
| CNC 告警 | `VF-2 报警 552` 返回 `answered`、`alarm_lookup`；所有引用包均为 `cnc_pack_v1.0.0`。 |
| 真空泵维护 | `nXDS10i maintenance schedule` 返回 `answered`、`maintenance_plan`；所有引用包均为 `dry_vacuum_pump_pack_v1.0.0`。 |
| 人在回路 | 从已保存 CNC 诊断创建草稿成功；普通 `user` 调用 approve 返回 `403`；独立 `approver` 成功批准。 |
| 审计 | 草稿/审批链包含 `work_order.draft_created`、`work_order.approval_requested`、`workflow.interrupted`、`workflow.resumed`、`work_order.approved`。 |
| 重启恢复 | 草稿创建后停止 Uvicorn、重新启动，再用同一持久化 `thread_id` 审批；最终为 `approved`，审计链完整。 |

## 结论与边界

此验收证明 v0.7 的本机 HTTP 双设备隔离、离线诊断、证据绑定草稿、权限拒绝、批准和重启恢复链路可用。它不替代 Docker 冷启动、浏览器验收或并发/性能基准；这些 v0.8 强制项已在 2026-11-22 的 [v0.8 本机发布验收](v08-release-validation.md) 完成。
