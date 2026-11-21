# v0.7 已知限制

- v1 检索场景的完整 BGE-M3 / reranker 运行需要本地模型、已构建索引及长时执行窗口；当前守护栏 before 报告不将它们误报为已运行。
- Ragas 0.4.4 和 DeepEval 4.3.4 已完成真实 DeepSeek Judge 调用。2026-11-21 一键 CLI 报告中两条机器辅助负责人批准场景的 Ragas/DeepEval Faithfulness 均为 1.0；2026-11-20 的分步运行中 DeepEval 为 1.0 与 0.90625，第二条独立重试曾为 0.965517。所有值均保留，说明 LLM Judge 有波动；当前尚未实现多次采样/方差治理。
- `--profile judge --judge-suite-file ...` 已完成真实外呼复跑：批准场景→pack-scoped 系统检索/`evidence_fallback` 回答→Ragas/DeepEval Faithfulness→append-only 统一报告。新报告仅覆盖 2 条 CNC 场景，不能替代完整 BGE-M3/RRF/reranker 或在线回答模型的 Judge 验收。
- 当前正式 Judge 使用 `evidence_fallback` 和 pack-scoped 检索，未同时验证生产在线回答模型与完整 BGE-M3/RRF/reranker 组合链路。
- 尚未有两名独立人工审核者的标注集，因此未计算 Cohen's Kappa，也未声称完成 Judge 与人工校准。该项与多次 Judge 采样/方差治理、完整 BGE-M3/reranker Judge 验收一并延后，待审核通过的评测场景数量扩充后统一执行。
- 双审核者一致性计算器已具备，但没有真实的两份独立标注输入前，仍不产生 Kappa。
- Ragas 0.4.4 的 `metrics.collections.Faithfulness` 只接受 InstructorLLM；当前自定义 `BaseRagasLLM` 因此显式使用同版本仍支持的兼容指标入口，并有真实 Ragas 指标测试保护。项目已固定 `ragas>=0.4.4,<0.5`；升级到后续版本前必须先迁移适配器，不能忽略弃用告警直接升级。
- 受限 shell 中的 Windows asyncio/TestClient 仍可能遇到 socket 权限限制；在具备本机 socket 权限的运行环境中，基础全仓回归已为 309 通过、5 个可选框架测试跳过，评测隔离环境已为 314 通过。因此该限制不再阻断 v0.7 本地回归结论。
- 前端依赖现已通过 lockfile 安装，Vitest 和生产构建已完成；该项不再是限制。
