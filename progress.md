# IndustrialOps Copilot 实施日志

## 2026-11-07

- 用户确认阶段 0 设计，授权开始实施。
- 已初始化 Git 仓库，设计规格提交为 `d802b1d`。
- 已建立阶段 0 持久实施计划；第一切片为只读来源审计。
- 已确认 Python 3.13、pytest、pypdf 可用。
- 已写 `source_audit` 行为测试，并确认其在实现缺失时以 `ModuleNotFoundError` 失败。
- 已补最小实现；首次绿色验证被 pytest 默认临时目录拦截：运行环境的 `%TEMP%` 是受沙箱管理的目录，而项目内 `tmp\pytest` 可写。下一步仅用 `--basetemp tmp\pytest-run` 验证该环境根因。
- 已确认通过项目内 pytest 临时目录后，来源审计 3 项测试全绿。
- 真实归档审计首次执行未启动审计：PowerShell 嵌套转义截断 Python 单行命令，触发 `SyntaxError`。将改用无嵌套转义命令重跑。
- 无嵌套命令确认后，普通 Python 进程未加载 `src/`，出现 `ModuleNotFoundError: industrialops`；pytest 的 `pythonpath` 配置仅对测试生效。真实审计将显式设置一次性 `PYTHONPATH=src`，后续补正式 CLI 入口。
- 已增加正式模块命令 `python -m industrialops.phase0.source_audit`；全部 4 个来源审计测试通过。
- 已通过该命令重新审计真实归档：40 份 PDF、1332 页、101285488 字节，输出 `data/source_manifests/source_audit_v1.jsonl`。
- 下一步：补齐来源清单的文档号、版本、语言、获取日期和分发边界，然后开始页级解析。
- 复核既有下载 CSV：它保留了一个已删除的无效中文报警快照，且遗漏两个后来有效归档的文件。下一步会建立以实际归档文件为准的来源登记，而不是直接继承旧 CSV 的状态。
- 已建立 `source_registry`：以实际存在的 PDF 为准，忽略历史下载状态，但保留官方 URL、来源 ID、语言、类型和获取日期。
- 已用 `config/phase0_source_overrides.json` 补齐 Haas 英文报警帮助页、Edwards 英文产品册，并纠正两份 OSHA 快照和多语言起吊指南的语言标签。
- `source_registry_v1.jsonl` 已校验为 40 条、40 个唯一来源 ID；语言为 27 份 `zh-CN`、12 份 `en`、1 份 `multi_zh-CN`。全量测试：7 通过。
- 下一步：建立页级文本解析器；所有输出保留文件哈希、来源 ID 和页码。
- 已实现页级解析器和正式模块命令；每页记录 `pack_id`、来源 ID、原文件、来源 SHA-256、页码、文本、提取状态与证据定位。
- 已增加终端实时进度与状态文件：每处理完一份来源就输出文件/页进度，并更新 `data/derived_corpus/pages/parse_status.json`。
- 真实全量解析完成：40/40 份、1332/1332 页；1296 页文本已提取，36 页为空文本，失败为 0。页级语料输出为 `data/derived_corpus/pages/page_corpus_v1.jsonl`。
- 下一步：审计 36 个空文本页，区分正常封面/图片页与需要 OCR 的正文页，再做片段、白名单与双语派生。
- 空页视觉核验中：VF-2 产品范围快照 12 个空页确认为纯白页面。一次高分辨率抽样渲染因临时诊断脚本错误引用 `page_number` 而未生成图片；将改用正确的样本页字段重跑，原始资料与派生语料未受影响。
- 空页视觉审核完成：36 页均为纯白页或网页快照导航/页框残留，不含运维正文、表格、报警、步骤或可用图示；不需要 OCR，统一排除出正式文本索引。审核记录：`data/derived_corpus/pages/empty_page_visual_audit_v1.md`。
- 当前进入章节/片段切分和设备白名单过滤。
- 为后续中英双语处理补齐了页级 `language` 字段；已重新解析真实资料并确认状态为 completed（40/40、1332/1332），首条语料记录为 `zh-CN`。全量测试：11 通过。
- 已生成 `data/derived_corpus/candidates/page_candidates_v1.jsonl`：1295 条有文本、非 `90_reference_only` 的可追溯页级候选。每条有稳定 ID、设备包、语言、文件哈希、页码与证据定位，并统一标为 `review_required`。
- 下一步：把 VF-2 NGC 标准配置与 nXDS 标准型号的白名单规则应用到候选；未经明确适用性审核的内容仍不得检索或翻译入库。
- 已应用第一轮范围外术语屏蔽词。抽样发现“命中即整页排除”会错误丢弃含范围外交叉引用的通用资料，已修正为 `mixed_scope_review`：184 条进入混合范围细粒度审核，1111 条仍为 `review_required`，没有任何候选被自动放行或自动删除。
- 混合范围页的 PDF 提取文本多为单换行而非空段落；段落切分器已改为在该模式按单换行边界组合。184 个候选已生成 443 个不跨页片段，134 个页面被有效拆分，输出 `data/derived_corpus/candidates/mixed_scope_segments_v1.jsonl`。全量测试：17 通过。
- 已建立来源级范围策略：两本跨机型 Haas 操作手册继续待审核；Edwards Documents、Haas 刀库目录和报警搜索帮助等纯目录/导航页排除。应用后：438 条 `provisionally_in_scope`、184 条 `mixed_scope_review`、670 条 `review_required`、3 条 `excluded`；全量测试：19 通过。正式检索仍未开启。
- 已输出 `data/structured/scope_review_queue_v1.jsonl`：854 条适用性审核任务，184 条高优先级混合范围内容、670 条跨机型手册内容。任务按风险、来源和页码稳定排序，保留候选 ID 与来源页；全量测试：20 通过。
- 发现目录/导航来源的排除优先级低于关键词筛选，已修正为目录来源无条件排除。重新生成后：438 条 `provisionally_in_scope`、181 条 `mixed_scope_review`、670 条 `review_required`、6 条 `excluded`；审核队列为 851 条。全量测试：20 通过。
- 已增加非运维文档类型过滤：合规声明页无法支持诊断、维修或安全结论，统一以可追溯理由排除。重新生成后：438 条 `provisionally_in_scope`、179 条 `mixed_scope_review`、669 条 `review_required`、9 条 `excluded`；审核队列为 848 条。全量测试：22 通过。
