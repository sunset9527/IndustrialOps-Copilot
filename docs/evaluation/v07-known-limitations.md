# v0.7 已知限制

- v1 检索场景的完整 BGE-M3 / reranker 运行需要本地模型、已构建索引及长时执行窗口；当前守护栏 before 报告不将它们误报为已运行。
- Ragas 0.4.4 和 DeepEval 4.3.4 已在隔离环境真实安装、导入并完成无网络 SDK smoke；尚无真实 Judge 报告，因为没有配置显式 Judge、embedding 模型和经人工审核的扩展场景。Judge 指标必须标为 `not_run`，不得计作 0 分或通过。
- 尚未有两名独立人工审核者的标注集，因此未计算 Cohen's Kappa，也未声称完成 Judge 与人工校准。
- 双审核者一致性计算器已具备，但没有真实的两份独立标注输入前，仍不产生 Kappa。
- 当前受限 Windows Python 3.13 执行环境在最小 `asyncio.run(asyncio.sleep(...))` 与 Starlette `TestClient` 上即阻塞，和业务路由无关；因此含 HTTP TestClient 的全仓 pytest 无法在此环境获得退出码。真实 Uvicorn 回环 HTTP 的 health/404 验收已通过，但不能替代隔离 MySQL 的双设备诊断与审批恢复验收。
- 前端依赖现已通过 lockfile 安装，Vitest 和生产构建已完成；该项不再是限制。
