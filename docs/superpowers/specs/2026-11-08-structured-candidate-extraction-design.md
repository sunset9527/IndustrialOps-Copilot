# 阶段 0：结构化候选提取与审核设计

**日期：** 2026-11-08  
**状态：** 待用户审阅  
**范围：** 从已冻结的 `retrievable_bilingual_corpus_v1.jsonl` 生成可审核的结构化候选；不生成可直接执行的诊断或维修结论。

## 1. 目标与边界

输入仅为已经通过设备、型号和选件范围审核的 1,340 条双语语料。输出发现以下六类候选：

- `alarms`：明确报警代码或报警标题；
- `components`：明确设备部件、组件或安全装置；
- `symptoms`：明确可观察的异常状态或现象；
- `failure_modes`：明确故障/原因/后果关系；
- `maintenance_tasks`：明确的检查、清洁、更换、润滑或定期维护动作；
- `safety_rules`：隔离能源、泄压、起吊、防护、危险警告和禁止条件。

本切片不做以下事情：

- 不推断未明示的故障原因、适用型号或操作步骤；
- 不把规则命中的候选直接写为正式知识；
- 不开发诊断 Agent、数据库 API 或前端；
- 不使用本次归档外的资料，也不把原始资料发送给外部服务。

## 2. 输入、输出与状态

输入文件是 `data/derived_corpus/bilingual/retrievable_bilingual_corpus_v1.jsonl`。每条输入必须已有 `pack_id`、来源 ID、来源文件、来源 SHA-256、页码、证据定位、原文和中文文本。

输出目录为 `data/structured/candidates/`，每一类各一个 JSONL 文件。每条候选至少包含：

```json
{
  "candidate_id": "deterministic hash",
  "candidate_type": "safety_rules",
  "candidate_status": "review_required",
  "pack_id": "cnc_pack_v1.0.0",
  "label": "锁定/挂牌",
  "source_record_id": "…",
  "source_id": "…",
  "source_file": "…",
  "source_sha256": "…",
  "page_number": 1,
  "evidence_locator": "…",
  "evidence_text": "…",
  "text_zh": "…",
  "extraction_reason": "matched explicit safety pattern"
}
```

其中 `source_record_id` 取源记录的 `candidate_id` 或 `unit_id`；不会重新组合跨页或跨来源内容。`candidate_id` 由候选类别、设备包、来源稳定标识和规范化标签确定，输入不变时输出稳定。

## 3. 提取与拒绝策略

采用可复现的规则发现器，不使用生成式模型判断事实。规则只在中英文文本包含明确模式时产生候选：

- 报警：`Alarm/报警` 邻近明确代码或标题；
- 安全：`warning/caution/danger/lockout/泄压/起吊/防护/禁止` 等明确安全模式；
- 维护：`maintenance/inspect/clean/replace/lubricate/检查/清洁/更换/润滑` 等明确动作模式；
- 部件、症状、故障模式：只识别受控词表中被正文明确提及的词或关系提示词。

下列记录一律拒绝写入候选文件：缺少任一来源证据字段、设备包不在两个声明包内、双语语料状态不完整、或文本为空。单条语料可产生多个不同类别候选，但同类别同标签只保留一个确定性候选。

所有候选均为 `review_required`。尤其是安全与维护候选不携带新生成的行动顺序；它们只摘取现有证据文本，供后续人工审核。

## 4. 校验与可见性

生成器会输出候选清单，列出各类别计数、输入/输出 SHA-256 和拒绝计数。输出文件使用临时文件写完后原子替换，避免半成品被使用。

测试先行覆盖：

1. 安全规则候选继承完整来源证据并为 `review_required`；
2. 缺少证据定位的输入被拒绝；
3. 相同输入的候选 ID 与输出顺序稳定；
4. 跨设备包或未知包不得输出；
5. 维护候选只能摘取原语料证据，不能生成额外操作文字；
6. 输出清单计数与 JSONL 内容一致。

## 5. 验收

完成后，阶段 0 的结构化候选只可作为人工审核队列使用。只有后续具有明确批准状态、证据完整且通过安全/兼容性审核的记录，才可能进入冻结包。
