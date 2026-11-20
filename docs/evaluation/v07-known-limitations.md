# v0.7 已知限制

- v1 检索场景的完整 BGE-M3 / reranker 运行需要本地模型、已构建索引及长时执行窗口；当前守护栏 before 报告不将它们误报为已运行。
- Ragas 0.4.4 和 DeepEval 4.3.4 已完成真实 DeepSeek Judge 调用。两条机器辅助负责人批准场景的 Ragas Faithfulness 均为 1.0；DeepEval 为 1.0 与 0.90625。第二条 DeepEval 独立重试曾得 0.965517，说明 LLM Judge 有波动；当前尚未实现多次采样/方差治理。
- `--profile judge` 当前仅能把已有 Judge 指标写入统一报告，尚未完成“批准场景→系统检索/回答→两框架评分→统一报告”的单命令端到端执行器。不得将其描述为完整可重跑 Judge 链路。
- 当前正式 Judge 使用 `evidence_fallback` 和 pack-scoped 检索，未同时验证生产在线回答模型与完整 BGE-M3/RRF/reranker 组合链路。
- 尚未有两名独立人工审核者的标注集，因此未计算 Cohen's Kappa，也未声称完成 Judge 与人工校准。
- 双审核者一致性计算器已具备，但没有真实的两份独立标注输入前，仍不产生 Kappa。
- 受限 shell 中的 Windows asyncio/TestClient 仍可能遇到 socket 权限限制；在具备本机 socket 权限的运行环境中，基础全仓回归已为 286 通过、1 可选依赖跳过，评测隔离环境已为 287 通过。因此该限制不再阻断 v0.7 回归结论。
- 前端依赖现已通过 lockfile 安装，Vitest 和生产构建已完成；该项不再是限制。
