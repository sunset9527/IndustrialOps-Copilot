# IndustrialOps Copilot 实施日志

## 2026-11-08（v0.1 规划）

- 已复核 HeritageMind：工作区干净，`main` 与 `origin/main` 同步，迁移基线固定为 `1edc5c4 feat(stage1): harden API security and resilience`。
- 用户已确认 v0.1 方案 A：保持 IndustrialOps 现有阶段 0 Git 历史，以选择性迁移替代整仓复制；不覆盖冻结包和现有未跟踪下载脚本。
- v0.1 设计规格已完成自检、经用户确认并提交为 `cf90953 docs: design v0.1 HeritageMind derivation`。
- 当前环境没有 `writing-plans` 技能；遵守既有设计门禁，使用项目内持久实施计划作为替代：`docs/superpowers/plans/2026-11-08-v0.1-heritagemind-derivation-plan.md`。
- 下一步：执行切片 1。先编写迁移台账/独立性护栏的失败测试，确认其因实现缺失而失败，再写最小实现。不得在测试前复制任何生产模块。
- 切片 1 已完成 TDD：先新增 `tests/v01/test_migration_audit.py`，首次运行因 `industrialops.migration_audit` 尚不存在而以 `ModuleNotFoundError` 失败；随后新增只读台账加载器、运行时残留扫描器与 JSON 台账，替代实现后 4 项测试通过。
- 首次绿色验证受项目已有 `tmp/pytest-run` 删除权限阻断：3 项通过、1 项 setup 错误，错误为 `WinError 5`。改用 `E:\python\industrialops_v01_pytest_tmp` 作为独立 pytest 基目录后，新测试 4 项全绿；未重复同一失败命令。
- 已运行阶段 0 全量回归，结果为 68 通过（1.93 秒），冻结包及阶段 0 工具未受影响。
- 下一步：切片 2。为产品元数据、IndustrialOps 配置和健康/就绪接口先编写失败测试，再迁移最小应用骨架。
- 切片 2 已完成 TDD：产品元数据与配置测试首次因 `industrialops.app_metadata` 缺失而失败，新增无外部依赖的 `Settings` 后 3 项通过；健康接口测试首次因 `industrialops.api` 缺失而失败，新增最小 FastAPI 应用工厂后 2 项通过。
- 已新增 404 错误契约测试，先观察到 FastAPI 默认 `{"detail": "Not Found"}` 断言失败，再添加 HTTP 异常处理器，确保外部返回稳定的 `not_found` 结构而非框架默认细节。
- 已新增 `api.app:app` ASGI 入口测试，首次因 `api` 包不存在而失败，新增标准入口后转绿。
- 切片 2 组合回归：`tests/v01` 与 `tests/phase0` 共 79 项通过（2.11 秒）。下一步进入切片 3，先选择认证、审计与请求安全中没有非遗耦合的最小一项。
- 切片 3 进行中。密码策略测试首次因 `industrialops.services` 不存在而失败；实现后 6 项通过。错误脱敏测试首次因模块缺失而失败；实现后 2 项通过，并验证数据库 URL、Bearer Token 与 Windows 路径不回显。
- 请求体限制器测试首次因 `industrialops.middleware` 缺失而失败；实现后 3 项通过。应用接入测试首次因 `Settings` 缺少 `request_max_bytes` 而失败；新增明确的 `INDUSTRIALOPS_REQUEST_MAX_BYTES` 配置并接入 FastAPI 后，配置/健康/限制组合 10 项通过。
- 切片 3 尚未实现用户数据模型、认证、授权或审计；当前状态必须保持 `in_progress`。下一步将先为最小的认证数据模型和审计事件写失败测试。

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
- 已增加目录页过滤：目录仅指向内容，不能作为运维结论或诊断证据。重新生成后：435 条 `provisionally_in_scope`、179 条 `mixed_scope_review`、669 条 `review_required`、12 条 `excluded`；审核队列仍为 848 条。全量测试：23 通过。
- 已增加版权出版说明页过滤：仅对以 `Copyright notice` 开头、且仅含版权与关联资料的页面排除，不以宽泛版权词匹配。重新生成后：434 条 `provisionally_in_scope`、177 条 `mixed_scope_review`、669 条 `review_required`、15 条 `excluded`；审核队列为 846 条。全量测试：24 通过。
- 已增加仅范围外 nXDS 型号页过滤：页面列出的型号若全部是 C/R 变体，则排除；同时列出标准 `nXDS*i` 的页面仍保留审核。已排除 Tip Seal 手册中仅写 `nXDS15iR/nXDS20iR` 的 1 页。重新生成后：434 条 `provisionally_in_scope`、176 条 `mixed_scope_review`、669 条 `review_required`、16 条 `excluded`；审核队列为 845 条。全量测试：26 通过。
- 审核队列现含 `source_file`、`evidence_locator`、500 字符正文预览和 `pending` 状态，可不重新定位 PDF 即逐项审核。发现 Edwards PDF 的 `Declaration of Conformity` 被提取为 `Con formity`，新增去空白识别后排除 3 个漏检合规页。重新生成后：434 条 `provisionally_in_scope`、173 条 `mixed_scope_review`、669 条 `review_required`、19 条 `excluded`；审核队列为 842 条。全量测试：27 通过。
- 已基于最终筛选候选重新生成混合范围片段，输出 `data/derived_corpus/candidates/mixed_scope_segments_screened_v1.jsonl`：173 个混合页面对应 765 个同页片段，158 个页面被拆分。旧的 443 片段文件保留为筛选前派生产物，后续审核和入库只使用 `screened` 版本；筛选后片段与审核单元统一采用 500 字符上限及编号小节边界。
- 发现 Edwards 服务页可能同时含标准型号和 C/R 变体专用套件，页面级“纳入/排除”会造成错误二选一。因此新增审核单元与决定台账：`data/structured/scope_review_units_v1.jsonl` 和 `scope_decision_ledger_v1.jsonl`。混合页按 500 字符、不跨页片段审核，跨机型 Haas 手册保持整页审核。又增加了“编号小节优先断开”：如 9.4.6/9.4.7 不再拼为同一审核单元。当前共 1,434 个待决单元（765 高优先级、669 常规）；全量测试：32 通过。
- 已建立受版本控制的 `config/phase0_scope_decisions_v1.jsonl`，决定会同时生成已解析审核单元和台账，未决定单元保持 `pending`。首批依据官方正文完成 2 条：排除 Edwards nXDS 手册封面（仅标识/跨变体列表），纳入轴承套件小节（明确适用于 nXDS 泵且无 C/R 专属限制）。当前为 1 条纳入、1 条排除、1,432 条待决；全量测试：34 通过（使用唯一项目内临时目录，规避固定 pytest 临时目录权限锁）。
- 已对 765 个混合范围片段重新执行术语与来源策略，而不是继承整页风险标记：66 个片段回到 `provisionally_in_scope`，224 个确实仍为 `mixed_scope_review`，475 个因来自跨机型 Haas 手册为 `review_required`。结果保存为 `data/derived_corpus/candidates/mixed_scope_segments_reclassified_v1.jsonl`，暂不覆盖现有审核队列；全量测试：36 通过。
- 已将片段级复筛接入第二版审核产物，保留 v1 原状以供追溯。`scope_review_units_v2.jsonl` 仅含未决单元：223 高优先级、1,144 常规，共 1,367 条；`scope_decision_ledger_v2.jsonl` 另含已有的 1 条纳入和 1 条排除决定。全量测试：36 通过。
- 已完成 Edwards 首批高风险片段审核：排除两段纯产品/订货目录；纳入 Edwards 干泵通用泄漏检测与轴封安全说明（`gearbox` 是泵安全上下文，不是 Haas 选件）。标准/R/C 共用排气阀套件表仍待细分，不作猜测性结论。v2 更新为 220 高优先级、1,144 常规、共 1,364 待决；已有 2 条纳入、3 条排除。全量测试：36 通过。
- 已完成 Haas 首批明确范围外片段审核：排除 VF-2 销售选项包、目录行、SMTC 双臂/轨道刀库和 HSK 专用说明共 6 条。通用 40T 紧固件扭矩和拉杆力内容即使交叉提到 SMTC、50T 或 HSK，仍未排除。v2 更新为 214 高优先级、1,144 常规、共 1,358 待决；已有 2 条纳入、9 条排除。全量测试：36 通过。
- 已排除 5 条纯 SMTC 双臂/凸轮盒步骤；其对伞式刀库的提及仅为交叉引用，不能作为标准 VF-2 证据。40T 主轴和电机中“标准维修步骤 + TSC 条件步骤”混合的片段保持待审，待按症状表行/条件步骤进一步细化。v2 更新为 209 高优先级、1,144 常规、共 1,353 待决；已有 2 条纳入、14 条排除。全量测试：36 通过。
- 对 40T 电机/主轴资料试算后，确认全量缩短切分会过度拆散表格，因此只在该两份来源启用 250 字符上限，其余保持 500 字符。重生成后混合片段为 775 条，其中 75 条 `provisionally_in_scope`（较原先多 10 条标准 40T 内容），高优先级和待决数不变。全量测试：37 通过。
- 已在片段级复筛后再次执行目录过滤，新增识别“标题 + 多个点线 + 页码”的纯目录行，不以普通正文中的点号为依据。291 个片段被安全排除为目录，原始 PDF 和页级审计仍保留。v2 更新为 191 高优先级、871 常规、共 1,062 待决；已有 2 条纳入、14 条排除。全量测试：38 通过。
- 已从 Haas 跨机型英文操作手册排除 13 条机器人专属正文：Robot Cell、Robot Package、FANUC DCS、机器人电池、Robot Interface 及 M300 机器人序列。通用门锁安全和机床概览等混合内容未因页面内机器人提及而自动排除。v2 更新为 178 高优先级、871 常规、共 1,049 待决；已有 2 条纳入、27 条排除。全量测试：38 通过。
- 适用性审核完成，不再存在待决单元。对两本跨机型 Haas 操作手册，先按显式范围外选件筛选，再以型号标记将 42 条其他机型内容转入严格审核；829 条无范围外选件/型号标记的通用铣床内容按正式策略纳入。其余 220 条显式选件或型号歧义片段不推断适用性，统一标记 `not_retrievable`。最终台账：831 纳入、27 排除、220 不可检索、0 待决；专用来源策略纳入 434 条，正式可检索单元总数为 1,340。全量测试：41 通过。

## 2026-11-08

- 已生成正式双语入库语料 `data/derived_corpus/bilingual/retrievable_bilingual_corpus_v1.jsonl`。1,340 条正式可检索记录中，564 条中文/多语言中文记录直接以原文作为 `text_zh`；776 条英文记录保留 `text` 与 `original_text`，并以 `machine_translated_project_zh` 标明离线生成的项目中文译文。
- 已生成双语语料清单 `retrievable_bilingual_corpus_v1_manifest.json`：输入 SHA-256 为 `f1510e29a9ac8f9fa742c1a5524c1a1a8736ce56136be130e00ae4dd5897293f`，输出 SHA-256 为 `d3ab068f766179f9be8c691721df6c0a789c2359570b6e1825aa49479400bba7`。
- 已逐条验证输入/输出记录数、稳定标识、原文、设备包、来源文件、来源哈希、页码和证据定位完全一致，并验证所有译文非空、中文原文未改写。全量测试：46 通过。
- 已实现并执行结构化候选提取器。它只从正式双语语料的明确模式中发现候选，所有输出均为 `review_required`，并继承原语料的稳定标识、设备包、来源文件、SHA-256、页码、证据定位、中英证据文本；不生成新的维修步骤或诊断结论。
- 首轮生成 `data/structured/candidates/`：1,949 条候选，其中告警 24、部件 439、症状 60、故障模式 260、维护 650、安全 516。两设备包分别为 CNC 1,722 条、干式真空泵 227 条；候选 ID 唯一，全部为待审核状态。全量测试：56 通过。
- 已完成保守自动审核台账，覆盖全部 1,949 条候选：1,362 条 `include`、586 条 `not_retrievable`、1 条 `exclude`。自动通过项被投影为 `structured_candidates_auto_reviewed_v1.jsonl`，并明确标为 `auto_reviewed_include`；不可检索/排除项未进入该文件。投影与台账候选 ID 集合已校验一致。全量测试：62 通过。
- 已建立独立评测集：6 条场景检索题与 5 条规则边界题，覆盖两设备包的检索、SMTC 范围外选件、nXDS C/R 变体、跨设备借用证据、危险维护前置条件和范围歧义。评测题干未与正式索引原文完全重复；全量测试：66 通过。
- 已完成来源发布边界审核：40 份归档来源均标为 `local_evidence_only`，仅作为本地项目证据保存；不将原始厂商/监管快照或其派生语料视为可公开再分发内容。
- 已冻结阶段 0：来源哈希与双语语料逐条交叉校验后生成两个只读本地包。CNC 包含 1,212 条语料、1,196 条自动审核结构化候选和 30 个被引用来源；干式真空泵包包含 128 条语料、166 条候选和 6 个被引用来源。冻结总清单记录 40 个审核来源、1,340 条语料、1,362 条自动审核候选和 11 条评测题；全量测试：68 通过。
