# IndustrialOps Copilot

## v1.0 正式发布（自动化门禁已完成）

IndustrialOps Copilot 是面向 Haas VF-2（NGC）与 Edwards nXDS 标准型号的本地工业运维演示平台。项目以两个冻结设备知识包支持资料查询、告警解释、证据约束诊断、安全门控和人工审批的工单草稿；不控制真实设备，也不将合成演示数据描述为现场数据。

v0.8 已完成独立 Release Candidate 验收。v1.0 只执行版本冻结、最终回归、公开材料核对与本地发布包构建，不新增功能。2026-11-22 已完成全仓 Python 回归（346 passed、5 skipped）、前端 22 项测试/生产构建、Compose 配置检查与本地 ZIP 构建；构建报告为 `passed`。当前状态为 `v1.0_release_preparing`：仍待人工抽查复核，且尚未推送 Git 标签或创建 GitHub Release。发布范围、边界与后续命令见 [v1.0 发布说明](RELEASE_NOTES_v1.0.0.md)、[数据与版权边界](docs/data/v1.0-release-data-boundary.md) 和 [本地发布就绪手册](docs/operations/v1.0-release-readiness.md)。

演示录屏由项目负责人决定本次跳过；这不影响已完成的 v0.8 HTTP/浏览器验收，也不代表项目已交付视频演示。

## v0.6 工程化与离线交付

v0.6 已交付完整演示栈的 `db → bootstrap → api → web` Compose 编排：bootstrap 显式执行迁移、合成资产初始化、冻结知识包验证与本地索引准备；API 只在 bootstrap 成功后启动。知识包和模型均以只读宿主机挂载使用，不进入镜像或 CI。默认离线模式禁止外部回答器，即使环境中存在外部 API Key 也只返回本地证据约束回答。

当前状态为 `release_verified`：2026-11-19 已完成 Docker 冷启动、双设备离线诊断、工单审批与重启恢复、备份恢复和 GitHub CI 验证。完整 Windows PowerShell 冷启动、状态排查、备份和恢复流程见 [v0.6 本地离线交付与恢复](docs/operations/v0.6-offline-delivery.md)。

## v0.7 评测收敛（已完成 · release_verified · 2026-11-21）

v0.7 已实现冻结输入哈希、append-only 评测报告、确定性安全/跨包/审批门禁、五类诊断意图的可观察轨迹，以及 Ragas 0.4.4 / DeepEval 4.3.4 的显式 DeepSeek 适配。2026-11-20 的 v1 守护栏 before/after 运行中，5 条场景均符合预期终态，且没有跨包引用、危险步骤泄露或未审批执行。该结果只是 11 条 v1 冒烟集的一部分，不是泛化能力结论。

两条具备完整证据锚点的 Hermes 场景已由项目负责人机器辅助批准，并在 2026-11-20 分别完成真实 DeepSeek Ragas/DeepEval 评分；另两条候选继续排除。2026-11-21 新增的一键 Judge CLI 会从批准 suite 运行 pack-scoped 系统检索与 `evidence_fallback` 回答，再把原始问题、系统回答和实际检索证据交给两个框架，最后写入统一报告；硬门禁失败时不会调用语义 Judge，单框架异常按稳定错误码保留。基础环境全仓回归为 **309 通过、5 个可选框架测试跳过**，装有 Ragas/DeepEval 的隔离环境为 **314 通过**；前端为 **12 文件、22 测试通过**且生产构建成功。

经明确授权后，2026-11-21 已用新 CLI 真实调用 `judge.env` 配置的 DeepSeek Judge。两条负责人机器辅助批准场景均通过硬门禁，Ragas 与 DeepEval Faithfulness 均为 1.0；结果、冻结输入哈希和脱敏 Judge 配置见 [一键 Judge 报告](data/evaluation/reports/v07/judge-live-cli-20261121-01/report.json)。这只证明两条 `evidence_fallback`、pack-scoped CNC 场景的可复跑链路，不证明在线回答模型、完整 BGE/RRF/reranker 链路或工业泛化能力。

当前状态为 `release_verified`：全量回归、隔离 MySQL/Uvicorn 双设备与审批恢复验收、真实 DeepSeek 一键 Judge 均已完成。双人独立审核/Kappa、多次 Judge 方差治理和完整 BGE-M3/reranker Judge 已明确移入“评测集扩充后的后续批次”，不构成本阶段遗留。隔离 MySQL 上的双设备诊断、工单草稿、越权审批拒绝与重启恢复事实见 [本机 HTTP 验收](docs/evaluation/v07-local-http-validation.md)；范围、报告和后续批次见 [v0.7 修复日志](docs/evaluation/v07-remediation-log.md) 与 [v0.7 已知限制](docs/evaluation/v07-known-limitations.md)。

Judge 会把批准场景的问题、系统回答和检索证据片段发送到 `judge.env` 显式配置的外部服务；执行前必须确认资料出站边界。下面的命令不会读取系统环境中的隐式 Judge，也不会回退到默认 OpenAI 提供方：

## v0.8 Release Candidate 验收（已完成 · release_verified · 2026-11-22）

v0.8 不增加产品功能，使用独立 Compose 项目名、端口、卷和不可覆盖的本地报告验证“首次获取项目”能否完成预检、无缓存启动与后续演示。本机 RC 已完成隔离冷启动、双设备 HTTP 与浏览器演练、草稿/越权拒绝/approver 审批/API 重启恢复、7 项受控故障矩阵、无阈值延迟与并发观测、声明真实性审计及全仓回归。最终脱敏报告为本地忽略文件 `data/evaluation/reports/v08/v08-full-20261122-01/report.json`；它不含模型、知识包或会话凭据。可复现命令和隔离规则见 [v0.8 RC 验收运行手册](docs/operations/v0.8-release-candidate.md)，逐项事实见 [v0.8 本机发布验收](docs/evaluation/v08-release-validation.md)。

```powershell
.\.venv-eval\Scripts\python.exe -m industrialops.evaluation.v07.run `
  --project-root . `
  --profile judge `
  --run-id judge-live-20261121-01 `
  --judge-env-file data\evaluation\v07\judge.env `
  --judge-suite-file data\evaluation\v07\hermes_owner_approved_v1.jsonl `
  --output-root data\evaluation\reports\v07
```

## 已实现

| 能力 | v0.1 范围 | 验证 |
| --- | --- | --- |
| FastAPI | `GET /health` 返回产品名和存活状态。`GET /ready` 表示 API 骨架可接收请求，依赖列表为空。未知路径返回统一的 404 错误结构。 | `tests/v01/test_api_entrypoint.py`、`test_health_routes.py` |
| 会话认证 | `POST /api/auth/register` 只能创建普通 `user` 并返回不透明 Bearer 会话；`POST /api/auth/login` 通过用户名密码创建会话；数据库只存 token 哈希。`GET /api/auth/me` 由服务端会话解析当前用户和角色。成功/失败登录分别写入 `auth.login_succeeded`/`auth.login_failed` 审计。 | `tests/v04/test_auth_sessions.py`、`test_auth_api.py` |
| 设备台账 | `GET /api/equipment/assets` 支持按知识包、型号、状态筛选与分页；`POST /api/equipment/assets`、`PATCH /api/equipment/assets/{asset_id}` 仅允许管理员。资产使用乐观版本更新，退役仅改为 `out_of_service`，不删除历史记录；创建和更新分别写入 `asset.created`/`asset.updated` 审计。 | `tests/v04/test_asset_service.py`、`test_assets_api.py` |
| 工单与审批 | `POST /api/diagnosis/query` 保存服务端诊断与引用快照；已登录用户可用 `POST /api/work-orders/drafts` 创建草稿并真实进入 LangGraph `interrupt()`。`approver` 或 `admin` 通过 `POST /api/work-orders/{work_order_id}/approve` 或 `POST /api/work-orders/{work_order_id}/reject` 恢复同一 `thread_id`；进程重建后仍可从数据库 checkpoint 恢复。`GET /api/work-orders`、`GET /api/work-orders/{work_order_id}` 提供筛选、详情、历史和审批结果；`POST /api/work-orders/{work_order_id}/transitions` 只接受指派、开始、完成、关闭或取消等确定性动作。应用内互斥与数据库行锁/唯一约束共同保证批准/拒绝竞争只产生一个最终决定；失败恢复会追加脱敏的 `workflow.resume_failed` 审计。客户端引用、目标状态和角色都不会被信任。 | `tests/v04/test_diagnosis_persistence_api.py`、`test_work_order_drafts_api.py`、`test_sqlalchemy_checkpoint_saver.py`、`test_approval_workflow.py`、`test_work_orders_api.py` |
| 请求安全 | API 限制请求体大小。Python 模块提供密码策略、角色判断、错误脱敏和审计记录。账户及审计模型在 SQLite 内存库中验证。 | `tests/v01/test_request_size_limit.py`、`test_authentication.py`、`test_authorization.py`、`test_audit_events.py`、`test_error_sanitizer.py` |
| 文件处理 | Python 模块校验上传路径和扩展名，解析 TXT、PDF、DOCX，并通过同步 worker 记录任务状态。 | `tests/v01/test_upload_security.py`、`test_document_parser.py`、`test_task_state.py`、`test_upload_worker.py` |
| 检索基础 | 内存 BM25、余弦向量检索、RRF、注入式重排、Hit@k 计算与索引快照。向量和评分函数由调用方提供。 | `tests/v01/test_bm25_retriever.py`、`test_vector_retriever.py`、`test_rank_fusion.py`、`test_reranker.py`、`test_retrieval_metrics.py`、`test_index_snapshot.py` |
| 工作流骨架 | 标准库实现请求级状态与事件，返回受控的能力边界或错误。 | `tests/v01/test_workflow_skeleton.py` |
| Vue 工业工作台（v0.5 自动化验证） | 登录、路由守卫、设备总览、服务端设备上下文、诊断、证据/安全/不确定性、工单草稿及批准/拒绝界面；设备和工单均为合成演示数据。真实浏览器验收前不标记 `release_verified`。 | `frontend/tests/` |

## 本地启动

后端需要 Python 3.13 或更新版本。以下 PowerShell 命令从仓库根目录执行。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m uvicorn api.app:app --host 127.0.0.1 --port 8100
```

在另一个终端访问健康和就绪接口。

```powershell
Invoke-RestMethod http://127.0.0.1:8100/health
Invoke-RestMethod http://127.0.0.1:8100/ready
```

[`.env.example`](.env.example) 列出可通过进程环境设置的示例值。Uvicorn 的监听端口由 `--port` 指定，Vite 开发端口在 `frontend/vite.config.js` 中设置。启动 API 骨架只需要 Python 依赖。MySQL URL 与 Redis 键前缀是预留配置。

前端需要 Node.js 22.12 或更新版本。另开终端从仓库根目录运行以下命令。

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

前端地址为 `http://localhost:5174`，默认 API 地址为 `http://localhost:8100`。如需更换 API 地址，在启动 Vite 或构建前设置 `VITE_INDUSTRIALOPS_API_BASE_URL`，或在 `frontend/.env.local` 中设置。

## Docker 完整演示栈

Docker Compose 运行 MySQL、一次性 bootstrap、FastAPI 和 Vue/Nginx。前端位于 `http://127.0.0.1:5174`，API/健康接口位于 `http://127.0.0.1:8100`。先按 [v0.6 本地离线交付与恢复](docs/operations/v0.6-offline-delivery.md) 配置 `.env`、执行预检并完成启动；不要把知识包、模型、`.env`、数据库卷或备份提交到仓库。

## v0.4 MySQL 发布验收（已完成，可复现）

2026-11-12 已在本机 MySQL 8.4.5 与 Uvicorn 上完成此流程：空库迁移至 `v04_assets_work_orders`，显式导入 2 个 synthetic 资产；创建草稿并获得 `thread_id` 后停止、重启 Uvicorn，再以 approver 恢复审批。最终数据库中该工单为 `approved`、版本为 2，存在 1 条审批决定、4 条 checkpoint 和 5 条审计事件。下列命令保留为可复现流程；不要把真实密码写入 `.env.example`、提交记录或审计内容。

```powershell
$env:INDUSTRIALOPS_DATABASE_URL = 'mysql+pymysql://<user>:<password>@127.0.0.1:3306/industrialops'
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m industrialops.demo_seed
.\.venv\Scripts\python.exe -m uvicorn api.app:app --host 127.0.0.1 --port 8100
```

`industrialops.demo_seed` 只显式插入两个 `synthetic=true` 的演示资产及其冻结知识包关联；模块导入和 API 启动不会静默写库。准备带有 `user`、`approver` 和 `admin` 角色的本地测试账户后，依次登录、提交已保存诊断创建的草稿，记录返回的 `thread_id`，停止 Uvicorn，再启动同一命令；使用 approver/admin Bearer token 调用 approve/reject，并用详情接口确认唯一审批决定、状态历史与审计动作。此过程只生成工单记录，不会控制设备。

## 测试

从仓库根目录运行阶段 0 和 v0.1 测试，再运行前端测试和构建。

```powershell
.\.venv\Scripts\python.exe -m pip install '.[test]'
$pytestTemp = Join-Path (Get-Location) ('tmp/pytest-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe -m pytest tests/phase0 tests/v01 --basetemp $pytestTemp

Push-Location frontend
npm.cmd ci
npm.cmd test
npm.cmd run build
Pop-Location
```

## 阶段 0 资料边界

阶段 0 的厂商及监管资料快照、派生语料与译文、结构化候选、评测集、冻结知识包和本地模型权重仅供本地使用，资料发布级别为 `local_evidence_only`。不要将这些内容打包进镜像或重新分发。仓库保留处理工具及来源审核元数据，自动化测试使用小型测试样例。

## v0.2（设备知识包与离线检索基础闭环）

已实现两个冻结设备包的独立完整性校验、型号/控制器/修订版过滤、告警精确索引、包级别别名增强、BM25/本地 BGE-M3 向量/RRF/本地 bge-reranker-base 重排，以及保留来源页码的离线评测报告。运行只接受本地模型；加载失败会显式失败，不会切换到 API 或输出降级指标。

2026-11-11 在本机 `E:\huggingface\model` 与 `E:\huggingface\bge-reranker-base` 上完成真实基线，报告为 `data/evaluation/reports/v02-baseline-20261111.json`（报告含冻结场景、知识包、注册表与模型指纹）。这是一组 6 条冻结场景的基线，不是对工业诊断能力的泛化宣称：CNC 向量检索 source-hit 为 100%，page-hit 为 66.7%；泵包的最佳 page-hit 为 rerank 的 33.3%。不得修改评测集或挑选结果以抬高该指标。

本机已有模型和可选依赖后，可运行下面命令生成不覆盖旧结果的离线基线报告：

```powershell
$env:PYTHONPATH = "$PWD\src"
E:\python\python.exe -m industrialops.evaluation.run_v02_baseline --project-root . --output data/evaluation/reports/v02-baseline-<timestamp>.json
```

## 当前边界

上传、浏览器检索的 HTTP 接口与 Redis 服务尚待验证；完整前端工作台不属于 v0.5。v0.5 已在本机浏览器完成普通账号注册、CNC 诊断/证据绑定草稿/人工批准，以及无需重启的真空泵切换诊断验收，状态为 `release_verified`。v0.2 当前是离线检索基线，不应包装成已上线的诊断系统。v0.4 的 MySQL/Uvicorn 重启恢复链路已真实通过；Codex 受限执行环境中的 `socketpair` 异常不代表产品运行时限制。

## v0.3（证据驱动诊断工作流，已完成）

已增加 `POST /api/diagnosis/query` 的 LangGraph 主链路、知识包范围解析、确定性安全门控、证据充分性裁剪、DeepSeek JSON 回答器与无密钥/调用失败时的本地证据降级。DeepSeek 默认模型为 `deepseek-flash`，通过 `.env.example` 中的 `INDUSTRIALOPS_DEEPSEEK_*` 环境变量配置；API 密钥不会写入项目文件、响应或日志。

冻结的 5 条 guardrail、CNC 精确告警的真实 DeepSeek 回答、CNC 与真空泵的本地模型检索链路均已验证。本机 Windows PowerShell 5.1 已通过真实 Uvicorn HTTP 验收：真空泵自然语言诊断返回可读中文、结构化检查步骤、可追溯引用和未降级的 `deepseek` 生成信息；CNC 联锁旁路请求稳定返回 `blocked` 与 `SAFETY_INTERLOCK_BYPASS`。响应统一以 UTF-8 返回，兼容 PowerShell 5.1。v0.3 状态为 `release_verified`；详见 `data/evaluation/reports/v03-release-validation-20261111.json`。
