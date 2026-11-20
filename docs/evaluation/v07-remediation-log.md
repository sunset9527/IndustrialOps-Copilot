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

## 2026-11-20：after 关联、指标与前端回归

- `after-guardrail-20261120` 已真实引用 `before-guardrail-20261120`；5 个 v1 守护栏案例继续全部通过，两个输入 SHA-256 在 before/after 中一致，且不存在失败样本。
- 每个 v0.7 run 现在同时保留 `report.json`、逐案例 `cases.jsonl`、`failures.jsonl` 与不含密钥的 `environment.json`。
- 新增确定性指标 DTO：Source/Page Hit@1/3/5、MRR、nDCG@5、检查步骤证据覆盖率及二元工业指标都输出分子、分母、案例 ID；`not_run` 不会被写成 0 分。
- 新增无 Judge 的工作流路径契约：安全短路、终态和稳定原因码可被确定性评估，不能被 LLM Judge 覆盖。
- 前端依赖已按 lockfile 重建；Vitest 为 **12 文件、22 测试全部通过**，Vite 生产构建通过。

## 2026-11-20：人工审核校准能力

- 已新增纯本地的双审核者标签校验、原始一致率、Cohen's Kappa 和分歧案例计算。它仅接受两个显式、不同审核者的一题一标；单人数据返回 `not_run`，重复标签会被拒绝，绝不把模型输出或重复采样伪装成人工复核。

## 2026-11-20：隔离 MySQL 与真实 HTTP 验收

- 创建独立 `industrialops_v07_validation` 库并运行现有迁移与 synthetic 资产初始化；未修改既有 `industrialops` 库。
- 现有 bootstrap 完成两个冻结包验证和两个本地索引构建。
- 临时 Uvicorn HTTP 验收已完成双设备诊断、引用包隔离、普通用户 403 审批拒绝、approver 批准和停止/重启后的同 `thread_id` 恢复。完整事实见 [本机 HTTP 验收](v07-local-http-validation.md)。

## 2026-11-20：全量 Python 回归

- 在具备本机 socket 权限的基础运行环境执行 `pytest tests`：**286 passed, 1 skipped**。唯一跳过项是基础环境未安装的可选 Ragas/DeepEval smoke。
- 在 `.venv-eval`（Ragas 0.4.4、DeepEval 4.3.4 已安装）执行同一命令：**287 passed**。因此可选框架 smoke 不再只是声明或 skip。

## 2026-11-20：Judge 实测与未收口项

- Hermes 4 条候选中仅 2 条具有完整证据锚点；经项目负责人机器辅助批准后进入独立 suite，另 2 条继续排除。
- 两框架已用 DeepSeek 完成真实评分；结果保存在 `judge-owner-hermes-20261120-reconciled` 与统一 `judge-unified-20261120` 报告中。
- Ragas 默认 Instructor 与 DeepSeek 结构化输出不兼容，已新增非思考 JSON 适配器；但该适配器尚未被正式 Judge CLI 调用。
- 未完成项：端到端 Judge Runner、最新全量回归、README/项目规划最终收口、双人审核/Kappa、多次 Judge 采样与方差治理。
