# IndustrialOps Copilot

v0.4 已完成真实发布验证：设备台账、证据绑定工单、人工审批中断/恢复、确定性状态流转和审计链路均已接入后端 API，并在本机 MySQL + Uvicorn 重启恢复链路中验证。当前状态为 `release_verified`。

## 已实现

| 能力 | v0.1 范围 | 验证 |
| --- | --- | --- |
| FastAPI | `GET /health` 返回产品名和存活状态。`GET /ready` 表示 API 骨架可接收请求，依赖列表为空。未知路径返回统一的 404 错误结构。 | `tests/v01/test_api_entrypoint.py`、`test_health_routes.py` |
| 会话认证 | `POST /api/auth/login` 通过用户名密码创建不透明 Bearer 会话；数据库只存 token 哈希。`GET /api/auth/me` 由服务端会话解析当前用户和角色。成功/失败登录分别写入 `auth.login_succeeded`/`auth.login_failed` 审计。 | `tests/v04/test_auth_sessions.py`、`test_auth_api.py` |
| 设备台账 | `GET /api/equipment/assets` 支持按知识包、型号、状态筛选与分页；`POST /api/equipment/assets`、`PATCH /api/equipment/assets/{asset_id}` 仅允许管理员。资产使用乐观版本更新，退役仅改为 `out_of_service`，不删除历史记录；创建和更新分别写入 `asset.created`/`asset.updated` 审计。 | `tests/v04/test_asset_service.py`、`test_assets_api.py` |
| 工单与审批 | `POST /api/diagnosis/query` 保存服务端诊断与引用快照；已登录用户可用 `POST /api/work-orders/drafts` 创建草稿并真实进入 LangGraph `interrupt()`。`approver` 或 `admin` 通过 `POST /api/work-orders/{work_order_id}/approve` 或 `POST /api/work-orders/{work_order_id}/reject` 恢复同一 `thread_id`；进程重建后仍可从数据库 checkpoint 恢复。`GET /api/work-orders`、`GET /api/work-orders/{work_order_id}` 提供筛选、详情、历史和审批结果；`POST /api/work-orders/{work_order_id}/transitions` 只接受指派、开始、完成、关闭或取消等确定性动作。应用内互斥与数据库行锁/唯一约束共同保证批准/拒绝竞争只产生一个最终决定；失败恢复会追加脱敏的 `workflow.resume_failed` 审计。客户端引用、目标状态和角色都不会被信任。 | `tests/v04/test_diagnosis_persistence_api.py`、`test_work_order_drafts_api.py`、`test_sqlalchemy_checkpoint_saver.py`、`test_approval_workflow.py`、`test_work_orders_api.py` |
| 请求安全 | API 限制请求体大小。Python 模块提供密码策略、角色判断、错误脱敏和审计记录。账户及审计模型在 SQLite 内存库中验证。 | `tests/v01/test_request_size_limit.py`、`test_authentication.py`、`test_authorization.py`、`test_audit_events.py`、`test_error_sanitizer.py` |
| 文件处理 | Python 模块校验上传路径和扩展名，解析 TXT、PDF、DOCX，并通过同步 worker 记录任务状态。 | `tests/v01/test_upload_security.py`、`test_document_parser.py`、`test_task_state.py`、`test_upload_worker.py` |
| 检索基础 | 内存 BM25、余弦向量检索、RRF、注入式重排、Hit@k 计算与索引快照。向量和评分函数由调用方提供。 | `tests/v01/test_bm25_retriever.py`、`test_vector_retriever.py`、`test_rank_fusion.py`、`test_reranker.py`、`test_retrieval_metrics.py`、`test_index_snapshot.py` |
| 工作流骨架 | 标准库实现请求级状态与事件，返回受控的能力边界或错误。 | `tests/v01/test_workflow_skeleton.py` |
| Vue 首页 | 提供 API 健康检查链接。API 客户端在内存管理 Bearer 令牌，处理 401 和结构化错误。 | `frontend/tests/` |

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

## Docker API

安装 Docker Engine 和 Compose 后，从仓库根目录执行以下命令。镜像构建需要 Python 基础镜像及可访问的 Python 包索引。

```powershell
docker compose config
docker compose up --build -d
Invoke-RestMethod http://127.0.0.1:8100/health
docker compose down
```

Compose 只运行 `industrialops-api` 并绑定本机的 `8100` 端口。Vue 仍可按上面的 Vite 命令运行。

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

上传和检索的 HTTP 接口、浏览器跨域 API与 Redis 服务尚待验证；Vue 设备台账/工单审批前端工作台属于 v0.5，未在本阶段实现。v0.2 当前是离线检索基线，不应包装成已上线的诊断系统。v0.4 的 MySQL/Uvicorn 重启恢复链路已真实通过；Codex 受限执行环境中的 `socketpair` 异常不代表产品运行时限制。

## v0.3（证据驱动诊断工作流，已完成）

已增加 `POST /api/diagnosis/query` 的 LangGraph 主链路、知识包范围解析、确定性安全门控、证据充分性裁剪、DeepSeek JSON 回答器与无密钥/调用失败时的本地证据降级。DeepSeek 默认模型为 `deepseek-flash`，通过 `.env.example` 中的 `INDUSTRIALOPS_DEEPSEEK_*` 环境变量配置；API 密钥不会写入项目文件、响应或日志。

冻结的 5 条 guardrail、CNC 精确告警的真实 DeepSeek 回答、CNC 与真空泵的本地模型检索链路均已验证。本机 Windows PowerShell 5.1 已通过真实 Uvicorn HTTP 验收：真空泵自然语言诊断返回可读中文、结构化检查步骤、可追溯引用和未降级的 `deepseek` 生成信息；CNC 联锁旁路请求稳定返回 `blocked` 与 `SAFETY_INTERLOCK_BYPASS`。响应统一以 UTF-8 返回，兼容 PowerShell 5.1。v0.3 状态为 `release_verified`；详见 `data/evaluation/reports/v03-release-validation-20261111.json`。
