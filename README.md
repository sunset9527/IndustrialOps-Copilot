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

## v0.2（实施中）

已实现冻结知识包加载与完整性校验：两个包通过独立清单、来源、记录数和内容哈希验证后加载；外部注册表提供型号、控制器、文档修订与别名元数据。设备包过滤、告警精确检索、真实本地模型基线与完整工业检索闭环仍在实施和验证中，不能据此宣称工业诊断已经完成。

本机已有模型和可选依赖后，可运行下面命令生成不覆盖旧结果的离线基线报告。该命令仅接受本地模型；模型加载失败即失败，不会输出降级指标。

```powershell
.\.venv\Scripts\python.exe -m pip install '.[local-models]'
.\.venv\Scripts\python.exe -m industrialops.evaluation.run_v02_baseline --output data/evaluation/reports/v02-baseline-<timestamp>.json
```

## 当前边界

登录、上传和检索的 HTTP 接口尚待接入。浏览器跨域 API 调用、MySQL 实库与 Redis 服务尚待验证。设备包加载、工业诊断和工单属于后续阶段。检索测试使用小型样例，没有真实模型评测或工业场景指标。
