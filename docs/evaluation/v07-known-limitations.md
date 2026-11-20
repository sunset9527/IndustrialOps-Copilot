# v0.7 已知限制

- v1 检索场景的完整 BGE-M3 / reranker 运行需要本地模型、已构建索引及长时执行窗口；当前守护栏 before 报告不将它们误报为已运行。
- Ragas 0.4.4 和 DeepEval 4.3.4 已在隔离环境真实安装、导入并完成无网络 SDK smoke；尚无真实 Judge 报告，因为没有配置显式 Judge、embedding 模型和经人工审核的扩展场景。Judge 指标必须标为 `not_run`，不得计作 0 分或通过。
- 尚未有两名独立人工审核者的标注集，因此未计算 Cohen's Kappa，也未声称完成 Judge 与人工校准。
- 双审核者一致性计算器已具备，但没有真实的两份独立标注输入前，仍不产生 Kappa。
- 受限 shell 中的 Windows asyncio/TestClient 仍可能遇到 socket 权限限制；在具备本机 socket 权限的运行环境中，基础全仓回归已为 286 通过、1 可选依赖跳过，评测隔离环境已为 287 通过。因此该限制不再阻断 v0.7 回归结论。
- 前端依赖现已通过 lockfile 安装，Vitest 和生产构建已完成；该项不再是限制。
