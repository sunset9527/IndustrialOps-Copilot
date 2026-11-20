# v0.7 修复日志

## 2026-11-20：评测启动与可观察性

- **before 运行：** `before-guardrail-20261120`。
- **冻结输入：** `scenario_eval_v1.jsonl` 和 `guardrail_eval_v1.jsonl` 的 SHA-256 已随本地报告保存；运行前后保持一致。
- **结果：** 5 条 v1 guardrail 场景均符合预期终态，且未触发跨包引用、危险步骤泄露或审批绕过门禁。
- **修复：** `work_order_draft` 不再错误提示“v0.4 未开放”；它现在明确要求先保存诊断，再走既有工单草稿与人工审批接口。
- **回归：** 新增结构化 `workflow_events`，保留旧 `workflow_trace`；事件记录实际节点耗时、计数、状态及稳定原因码，不记录问题、证据正文、密钥或隐藏思维链。

## 2026-11-20：报告与硬门禁

- 运行目录为 append-only，重复 `run_id` 会失败。
- after 报告必须引用 before run；硬门禁失败样本保留案例 ID 和 violation IDs。
- 门禁覆盖跨包引用、危险步骤泄露、未审批执行、审批前后快照变更。

## 2026-11-20：真实框架 SDK 与回归证据

- 独立环境 `.venv-eval` 中已真实导入 **Ragas 0.4.4** 和 **DeepEval 4.3.4**，`pip check` 无依赖冲突。
- 已将审核的 RAG 行映射为真实 `ragas.EvaluationDataset`/`SingleTurnSample`，并将脱敏工作流 span 映射为真实 `deepeval.test_case.LLMTestCase`；无 Judge、无默认 OpenAI client、无 trace 上传。
- 框架 SDK smoke 与适配器测试在该环境中为 4 通过。基础运行环境未安装可选框架时，该测试明确 skip，不将其算作成功指标。
- 五类支持意图（手册、显式告警、维护、故障诊断、工单草稿）各有端到端测试，5 通过；工单意图只能返回受约束下一步，不能绕过现有审批链。
- 纯同步回归分组为：阶段 0 为 68 通过；v0.2/v0.3（不含 HTTP TestClient）为 34 通过；v0.4（不含 HTTP TestClient）为 42 通过；v0.6/v0.7（不含 HTTP TestClient）为 45 通过、1 跳过。
- 真实临时 Uvicorn 回环验收：`GET /health` 返回 200 与 `IndustrialOps Copilot`；未知路由返回 404 和稳定的 `not_found` 错误包。进程在验收后已停止。
