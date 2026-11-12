# IndustrialOps Copilot 实施计划

## 目标

在不新增外部资料、不中途进入诊断功能开发的前提下，完成 Haas VF-2（NGC）与 Edwards nXDS 标准型号的阶段 0 知识包解析、审核、评测和冻结；随后按已确认规格完成 v0.1 HeritageMind 派生与去领域化。

## 当前阶段

- 状态：`v0.4_automated_verified`。v0.1、v0.2 与 v0.3 已分别完成发布验收；v0.4 后端、迁移和自动化验收已完成，等待用户在本机 MySQL/Uvicorn 进行真实发布验收。
- 当前门禁：阶段 0 已完成并冻结；后续工作不得修改冻结包，新增资料或规则须创建新版本。v0.4 只交付后端、数据库迁移和 API，不提前实现 v0.5 前端。
- 设计依据：`docs/superpowers/specs/2026-11-11-v0.4-assets-work-orders-approval-design.md`（提交 `efa2c8c`）。

## v0.4 分片计划

1. `[complete]` 建立纯领域工单状态机与角色规则，覆盖全部合法/非法转换；v0.4 目标测试 21 项与全仓 194 项测试均通过。
2. `[complete]` 增加设备、诊断、工单、审批、认证会话与 checkpoint SQLAlchemy 模型，并写 Alembic 迁移；模型/升级降级 7 项与全仓 201 项测试均通过。
3. `[complete]` 实现不透明 Bearer 会话与 FastAPI 数据库依赖，保持凭据脱敏；认证分片 4 项与全仓 205 项测试均通过。
4. `[complete]` 实现设备台账服务与管理员 API，包含筛选、分页和软下线；分片 3 项与全仓 208 项测试均通过。
5. `[complete]` 将 v0.3 诊断结果持久化，并实现证据绑定工单草稿服务；全仓 212 项测试通过。
6. `[complete]` 实现同步 `SQLAlchemyCheckpointSaver`，覆盖 checkpoint、writes、列出、删除、typed serializer 和绑定外层事务；SQLite 契约测试通过。
7. `[complete]` 实现包含 `interrupt()`/`Command(resume=...)` 的审批图，并验证销毁后重建 workflow/saver 仍可按同一 `thread_id` 恢复。
8. `[complete]` 实现工单审批、转换、审计和幂等 API；`approver` 与 `admin` 可审批，普通用户被拒绝，版本和被指派人规则可验证。
9. `[complete]` 完成 Alembic SQLite 冒烟、全量自动化回归、显式合成资产初始化命令与 Windows PowerShell MySQL/Uvicorn 重启恢复发布验收说明；真实 MySQL 验收按规格保留给用户执行。

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
14. `[complete]` v0.1 切片 4：上传、解析与后台任务基础。已完成上传路径/扩展名/保护目录校验、TXT/PDF/DOCX 解析、受控任务状态与同步 worker 适配器；worker 不建索引、不写冻结包。v0.1 + 阶段 0 回归共 110 项通过。
15. `[complete]` v0.1 切片 5：通用检索与评测基础。已完成纯内存 BM25、RRF、余弦向量检索接口、本地重排适配器、Hit@k 与稳定索引快照。未运行真实向量模型评测。
16. `[complete]` v0.1 切片 6：中性工作流骨架。已验证能力边界、安全错误和按请求隔离的事件。v0.1 + 阶段 0 回归共 130 项通过。
17. `[complete]` v0.1 切片 7：Vue 基础壳、健康检查链接和通用 API 客户端。前端 8 项测试、默认及覆盖 API 地址的生产构建、运行时残留扫描均通过。登录页和登录 API 待接入。
18. `[complete]` v0.1 切片 8：已交付 Python 包元数据、环境示例、API 容器配置、README、第三方声明与迁移台账。8 项静态交付测试和 `docker compose config` 通过。
19. `[release_verified]` v0.1 切片 9：Python 138 项（阶段 0 为 68 项）、前端 8 项及生产构建通过，运行时残留扫描通过。全新虚拟环境已通过标准 `pip install .` 并成功导入应用；Docker 镜像冷启动后 `industrialops-api` 保持 healthy，宿主机 `/health` 和 `/ready` 均返回预期 JSON。

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
| 2026-11-09 | 全新虚拟环境无法从包索引下载构建依赖 | pip 在获取 `setuptools` 时收到 `WinError 10013`。已用本机依赖完成 wheel 安装和 Uvicorn 冒烟测试，标准安装待联网验证。 |
| 2026-11-09 | Docker Engine 初始不可用 | 用户启动 Docker Desktop 后，以桌面账号权限完成镜像构建、容器启动与健康端点验证。 |
| 2026-11-11 | 首次更新 v0.4 持久计划的补丁未找到 `progress.md` 预期标题 | 未写入任何文件；读取准确标题后使用小范围补丁追加，不重复使用原补丁。 |
| 2026-11-11 | 沙箱内 FastAPI `TestClient` 在 Windows Proactor 内部 `socketpair` 的 `accept()` 阻塞 | 已用 faulthandler 定位；相同测试在沙箱外通过。后续含 TestClient 的 pytest 使用已授权的 `python -m pytest` 沙箱外执行。 |
