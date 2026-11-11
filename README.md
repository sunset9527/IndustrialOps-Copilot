# IndustrialOps Copilot

v0.1 是工业运维项目的通用底座。FastAPI 和 Vue 首页可以独立运行，通用服务通过模块测试验证。

## 已实现

| 能力 | v0.1 范围 | 验证 |
| --- | --- | --- |
| FastAPI | `GET /health` 返回产品名和存活状态。`GET /ready` 表示 API 骨架可接收请求，依赖列表为空。未知路径返回统一的 404 错误结构。 | `tests/v01/test_api_entrypoint.py`、`test_health_routes.py` |
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

登录、上传和检索的 HTTP 接口尚待接入；浏览器跨域 API 调用、MySQL 实库与 Redis 服务尚待验证。工业诊断决策与工单属于后续阶段。v0.2 当前是离线检索基线，不应包装成已上线的诊断系统。2026-11-11 已在本机正常 PowerShell 验证全仓 Python 自动化测试 **148 passed**；Codex 受限执行环境中的 `socketpair` 异常不代表项目运行时限制。

## v0.3（证据驱动诊断工作流，实施中）

已增加 `POST /api/diagnosis/query` 的 LangGraph 主链路、知识包范围解析、确定性安全门控、证据充分性裁剪、DeepSeek JSON 回答器与无密钥/调用失败时的本地证据降级。DeepSeek 默认模型为 `deepseek-flash`，通过 `.env.example` 中的 `INDUSTRIALOPS_DEEPSEEK_*` 环境变量配置；API 密钥不会写入项目文件、响应或日志。

当前代码仍处于 `implemented`：非 HTTP 的 v0.3 单元测试已通过；API 契约、完整 guardrail 评测、真实本地检索模型以及真实 DeepSeek 调用尚需在本机正常 PowerShell 中完成，完成前不得标记为 `automated_verified` 或 `release_verified`。
