# IndustrialOps Copilot 实施计划

## 目标

在不新增外部资料、不中途进入诊断功能开发的前提下，完成 Haas VF-2（NGC）与 Edwards nXDS 标准型号的阶段 0 知识包解析、审核、评测和冻结；随后按已确认规格完成 v0.1 HeritageMind 派生与去领域化。

## 当前阶段

- 状态：`v1.0_release_preparing`（2026-11-22）。v0.8 已 `release_verified`；v1.0 仅冻结版本、运行最终门禁、整理公开材料和生成本地发布包。不会自动推送、打标签、创建 GitHub Release 或录制视频。
- 当前门禁：阶段 0 已完成并冻结；后续工作不得修改冻结包，新增资料或规则须创建新版本。v0.6 不增加设备资料或诊断产品功能。
- 设计依据：`docs/superpowers/specs/2026-11-18-v0.6-engineering-offline-delivery-design.md`（提交 `6abe424`）与 `docs/superpowers/plans/2026-11-18-v0.6-engineering-offline-delivery-plan.md`。

## v1.0 发布冻结计划

1. `[complete]` 提交 v1.0 设计规格与实施计划；明确本地发布就绪不等于 GitHub 已发布，且演示视频由负责人决定跳过。
2. `[complete]` 按 TDD 建立发布清单校验、版本/Alembic head/公开文件哈希门禁、Git 跟踪文件打包、敏感路径/连接串扫描、SHA-256 和干净工作树拒绝；v1.0 定向测试 9 项通过。
3. `[complete]` 编写发布说明、数据边界、评测摘要、人工抽查清单和本地发布手册；公开材料保留已知限制与合成数据标识。
4. `[blocked_by_environment]` 前端 12 文件/22 测试、生产构建和 Compose 配置已通过；受限 Windows socket 环境在 `tests/v03/test_diagnosis_api.py::test_diagnosis_query_route_invokes_the_injected_workflow_and_returns_the_stable_contract` 可复现挂起，因此未将全仓 Python 回归或发布包标为通过。需在正常本机环境继续完成 Python/人工抽查/归档验证。
5. `[pending]` 所有门禁通过后标记 `v1.0_release_ready`，提交本地代码与文档，并仅提供由负责人执行的推送、标签和 GitHub Release 命令。

## v0.8 分片计划

1. `[complete]` 建立测试先行的 RC 验收核心：运行隔离、报告原子追加、脱敏、故障判定和基线统计；v0.8 定向回归 5 项通过。
2. `[complete]` 实现预检与 README/API/架构/许可证/数据声明的真实性审计；预检覆盖离线、包、模型、端口和发布材料，5 条关键公开主张均以版本化清单绑定代码/测试/Compose 配置证据，新增 `docs/architecture.md`。
3. `[complete]` 实现隔离 Compose 覆盖、资源所有权、无缓存冷启动观测及安全保留/清理；2026-11-22 Docker Desktop Linux Engine 上完成独立 RC 构建、bootstrap、API 与 Web 启动。
4. `[complete]` 完成真实 HTTP 主链路、离线诱饵、受控故障注入与恢复验证；7 项故障矩阵均以稳定原因码通过并恢复。
5. `[complete]` 完成浏览器验收与延迟、资源、并发基线采样；两台设备、来源引用、草稿/审批和恢复均在 CDP 浏览器中观察。
6. `[complete]` 在真实 Docker 环境完成 RC 验收、全仓 Python 与前端回归，并保存不可覆盖报告。

## v0.7 后续评测批次（不阻塞 v0.7 完成）

1. `[deferred]` 待审核通过的评测场景数量扩充后，由两名审核者基于冻结手册完成非同义改写的扩展场景与证据标注，随后冻结为独立 suite 并计算一致性。
2. `[deferred]` 随扩充后的评测集运行多次 Ragas/DeepEval Judge 与完整 BGE-M3/reranker Judge，记录模型、版本、成本、错误、方差与同源偏差；不影响确定性硬门禁。
3. `[complete]` 在隔离 MySQL 上运行 bootstrap；完成 CNC 告警、真空泵维护、跨包引用隔离、草稿、普通用户 403、approver 批准和 Uvicorn 重启恢复的真实 HTTP 验收。记录见 `docs/evaluation/v07-local-http-validation.md`。
4. `[complete]` 在具备本机 socket 权限的基础环境运行全仓 pytest（309 通过、5 个可选依赖跳过）；在 Ragas/DeepEval 隔离环境运行全仓 pytest（314 通过）；前端 Vitest 22 通过和生产构建通过。
5. `[complete]` 对 2 条负责人机器辅助批准场景执行真实 DeepSeek 一键 Judge；硬门禁均通过，Ragas/DeepEval Faithfulness 均为 1.0，报告为 `judge-live-cli-20261121-01`。

## v0.6 分片计划

1. `[complete]` 配置扩展与离线门控：新增显式知识包、索引和本地模型路径；离线模式即使存在 API Key 也不会构造 DeepSeek HTTP 请求。
2. `[complete]` 可再生索引：索引身份绑定知识包内容哈希、注册表哈希、BGE 指纹与格式版本；完整索引可复用，损坏或身份不一致显式拒绝。
3. `[complete]` bootstrap 与就绪：显式顺序执行预检、迁移、合成资产初始化、知识包校验和索引准备；`/health` 与可报告依赖状态的 `/ready` 分离。
4. `[complete]` 容器、日志与 CI：交付 MySQL、bootstrap、API、Vue/Nginx 四服务编排，只读挂载私有资料、索引卷、输出脱敏和 CI 配置。
5. `[pending]` 启动 Docker Desktop 后按 `docs/operations/v0.6-offline-delivery.md` 完成镜像构建、无历史卷冷启动、离线双设备诊断、工单重启恢复、备份恢复与验收报告。

## v0.4 分片计划

1. `[complete]` 建立纯领域工单状态机与角色规则，覆盖全部合法/非法转换；v0.4 目标测试 21 项与全仓 194 项测试均通过。
2. `[complete]` 增加设备、诊断、工单、审批、认证会话与 checkpoint SQLAlchemy 模型，并写 Alembic 迁移；模型/升级降级 7 项与全仓 201 项测试均通过。
3. `[complete]` 实现不透明 Bearer 会话与 FastAPI 数据库依赖，保持凭据脱敏；认证分片 4 项与全仓 205 项测试均通过。
4. `[complete]` 实现设备台账服务与管理员 API，包含筛选、分页和软下线；分片 3 项与全仓 208 项测试均通过。
5. `[complete]` 将 v0.3 诊断结果持久化，并实现证据绑定工单草稿服务；全仓 212 项测试通过。
6. `[complete]` 实现同步 `SQLAlchemyCheckpointSaver`，覆盖 checkpoint、writes、列出、删除、typed serializer 和绑定外层事务；SQLite 契约测试通过。
7. `[complete]` 实现包含 `interrupt()`/`Command(resume=...)` 的审批图，并验证销毁后重建 workflow/saver 仍可按同一 `thread_id` 恢复。
8. `[complete]` 实现工单审批、转换、审计和幂等 API；`approver` 与 `admin` 可审批，普通用户被拒绝，版本和被指派人规则可验证。补齐成功/失败登录、资产创建/更新、恢复失败审计；并发批准/拒绝竞争的自动化测试验证仅产生一个最终决定。
9. `[release_verified]` 完成 Alembic SQLite 冒烟、全量自动化回归、显式合成资产初始化命令与 Windows PowerShell MySQL/Uvicorn 重启恢复验收。2026-11-12 在空 MySQL 8.4.5 库迁移至 head、导入合成资产、创建草稿、停止并重启 Uvicorn、按同一 thread 恢复审批后，数据库核验通过。

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
| 2026-11-21 | 初次读取 v0.7 报告测试时假定存在 `tests/v07/test_run_store.py` | 文件实际不存在，相关覆盖位于 `tests/v07/test_v07_reporting.py`；已改用实际测试文件，不重复该路径。 |
| 2026-11-21 | v0.8 首次 RED 命令使用 `./.venv/Scripts/python.exe`，但项目根目录不存在 `.venv` | pytest 未启动，不能作为 RED 证据；定位项目现有虚拟环境或可用 Python 后再执行同一测试。 |
| 2026-11-21 | 初次读取 v0.6 Compose 测试时假定存在 `tests/v06/test_compose_delivery.py` | 文件实际不存在；Compose 相关覆盖位于 `test_container_delivery.py` 与 `test_ci_delivery.py`，后续按真实路径读取。 |
| 2026-11-21 | Compose 测试使用仓库内固定 `reports/20261121-env`，第二次运行触发正确的不可覆盖保护 | 改用 pytest `tmp_path`；已核对并删除本测试创建的空目录，后续测试不再写入仓库报告路径。 |
| 2026-11-21 | v0.8 真实无缓存 Docker cold-start 无法连接 `dockerDesktopLinuxEngine`，并返回受限 Docker 构建访问错误 | CLI 已在 build 阶段 fail-closed，未执行 `up` 或清理；报告为本地忽略文件 `v08-cold-20261121-01`。需启动 Docker Desktop Linux Engine 后使用新 run ID 重新运行。 |
