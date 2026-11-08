# IndustrialOps Copilot 实施计划

## 目标

在不新增外部资料、不中途进入诊断功能开发的前提下，完成 Haas VF-2（NGC）与 Edwards nXDS 标准型号的阶段 0 知识包解析、审核、评测和冻结；随后按已确认规格完成 v0.1 HeritageMind 派生与去领域化。

## 当前阶段

- 状态：`v0.1_planned`
- 当前门禁：阶段 0 已完成并冻结；后续工作不得修改冻结包，新增资料或规则须创建新版本。v0.1 只迁移通用项目底座，不提前实现工业检索或诊断。
- 设计依据：`docs/superpowers/specs/2026-11-07-phase0-knowledge-pack-design.md`、`docs/superpowers/specs/2026-11-08-v0.1-heritagemind-derivation-design.md`

## 分阶段计划

1. `[complete]` 初始化可测试的阶段 0 工具工程；建立来源审计的测试、模块命令与最小实现。全量测试：4 通过。
2. `[complete]` 已生成并审核最终来源清单：40 份资料的文件、页数、SHA-256、语言和访问地址均在来源登记中；新增 `source_rights_review_v1.jsonl` 将全部来源明确为 `local_evidence_only`，仅作为本地项目证据保留，不构成公开再分发授权。
3. `[complete]` 生成页级解析语料；记录每页可提取性、来源文件、页码和哈希。已完成 1332 页生成；36 个空文本页完成视觉审核，均为非业务空白/导航残留，不需要 OCR。
4. `[complete]` 定义设备/型号/选件白名单并生成正式可检索候选。最终台账 `scope_decision_ledger_final_v1.jsonl` 覆盖 1,078 个需决单元：831 条纳入、27 条排除、220 条因官方文本仍存在范围歧义而标记 `not_retrievable`，待决为 0。另有 434 条经专用来源策略纳入；最终可检索单元 `retrievable_scope_units_v1.jsonl` 为 1,340 条，均带设备包、语言、原文件、SHA-256 和页码证据。v1/v2/v3 中间台账保留用于审计。
5. `[complete]` 已生成 `retrievable_bilingual_corpus_v1.jsonl`：1,340 条正式可检索语料，其中 564 条直接保留中文原文、776 条保留完整英文原文并附离线生成的项目中文译文。每条仍保留设备包、原文件、SHA-256、页码和证据定位；清单 `retrievable_bilingual_corpus_v1_manifest.json` 已校验输入/输出哈希与逐条来源一致性。
6. `[complete]` 已按候选优先方案生成并完成保守自动审核。1,949 条候选中，1,362 条具备明确标签、完整证据且未触发范围/安全阻断，写入 `structured_candidates_auto_reviewed_v1.jsonl` 并标为 `auto_reviewed_include`；586 条范围或安全条件不充分而保持 `not_retrievable`，1 条导航内容排除。所有决定均在 `structured_candidate_decision_ledger_v1.jsonl` 中可追溯；自动审核不等同于制造商认证或现场安全许可。
7. `[complete]` 已建立与语料分离的评测集和确定性校验器：6 条场景检索题、5 条安全/兼容性/跨设备规则题。校验器验证题目字段、评测题干与索引原文不完全重复、检索来源/页码允许集、跨设备隔离和安全升级标记；未执行真实检索/回答系统，故未生成或宣称任何虚假能力指标。
8. `[complete]` 已执行覆盖与完整性验收、来源哈希交叉校验和只读冻结。输出 `cnc_pack_v1.0.0`（1,212 条双语语料、1,196 条自动审核结构化候选、30 个来源）与 `dry_vacuum_pump_pack_v1.0.0`（128 条双语语料、166 条自动审核结构化候选、6 个来源）；冻结清单为 `freeze_acceptance_v1.json`。
9. `[complete]` 用户确认 v0.1 采用方案 A：保留 IndustrialOps 阶段 0 Git 历史，依据 HeritageMind 已提交且已同步的 `1edc5c4` 选择性迁移通用能力；不整仓覆盖。
10. `[complete]` v0.1 设计规格已自检并提交为 `cf90953`；详细实现计划位于 `docs/superpowers/plans/2026-11-08-v0.1-heritagemind-derivation-plan.md`。
11. `[complete]` v0.1 切片 1：迁移台账与独立性护栏（测试先行）。已新增固定母体提交、选择性迁移策略、明确排除范围的 JSON 台账；运行时扫描器仅检查 `src/` 与 `api/`，避免把文档历史说明误判为运行时耦合。新测试 4 项与阶段 0 回归 68 项均通过。
12. `[complete]` v0.1 切片 2：应用配置与安全骨架（测试先行）。已建立仅接受 `INDUSTRIALOPS_*` 的产品配置、标准 `api.app:app` ASGI 入口、`/health`、`/ready` 和统一 404 错误响应。v0.1 + 阶段 0 回归共 79 项通过。
13. `[complete]` v0.1 切片 3：数据、认证、审计与请求安全。已完成密码策略、错误脱敏、请求大小限制、SQLAlchemy 用户模型、密码散列认证、角色判断和通用审计事件；所有测试使用 SQLite 内存库，未连接本机 MySQL。v0.1 + 阶段 0 回归共 97 项通过。
14. `[in_progress]` v0.1 切片 4：上传、解析与后台任务基础。已完成上传路径、扩展名和冻结/派生数据目录保护；文档解析、任务状态与 worker 尚未开始。
15. `[pending]` v0.1 切片 5-8：检索评测、工作流、前端和部署的选择性迁移（每一切片单独测试先行）。
16. `[pending]` v0.1 切片 9：全量验收、残留扫描、README 真实性检查和提交。

## 首批可验证切片

实现 `source_audit`：给定来源目录，生成稳定的 JSONL 清单，并在文件缺失、哈希异常、PDF 页数不可读时失败。该切片不修改原始资料。

## 不变量

- `data/raw_archive/` 只读，不能由任何流水线写入。
- 正式入库记录必须有 `source_id`、`source_file`、`source_sha256`、`page_number` 和 `evidence_locator`。
- Edwards 英文入库记录须保留英文原文，中文译文只能标为 `project_translation`。
- 混合页面、排除型号、未知适用性不得进入正式索引。
- 评测集不得复用索引语料的问答文本。

## 已知问题/错误

| 日期 | 问题 | 处理 |
|---|---|---|
| 2026-11-07 | `writing-plans` 技能在当前环境不存在 | 使用已确认规格与本项目持久计划文件替代，保持测试先行。 |
| 2026-11-07 | pytest 默认临时目录不可创建 | 已确认项目内 `tmp\pytest` 可写；将通过单独指定 pytest `--basetemp` 验证环境根因。 |
| 2026-11-07 | 真实审计命令的 Python 单行代码被 PowerShell 嵌套引号截断 | 不改动资料，使用无嵌套转义的命令重跑。 |
| 2026-11-07 | 普通 Python 进程不加载 `src/` | pytest 的 `pythonpath` 只影响测试；临时显式设定 `PYTHONPATH=src`，并在后续切片提供正式 CLI。 |
| 2026-11-07 | 空页质检的高分辨率临时渲染未生成图片 | 诊断脚本错误引用样本对象的 `page_number` 字段；改用实际 `page` 字段重跑，不影响任何原始/派生数据。 |
| 2026-11-08 | `writing-plans` 技能在当前环境不可用 | 用户确认 v0.1 规格后，改以项目内持久计划 `docs/superpowers/plans/2026-11-08-v0.1-heritagemind-derivation-plan.md` 替代，并保持测试先行。 |
