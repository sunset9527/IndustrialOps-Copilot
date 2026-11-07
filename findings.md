# IndustrialOps Copilot 实施发现

## 2026-11-07

- `data/raw_archive/` 当前有 40 份 PDF、1332 页；最终来源清单在 `data/source_manifests/source_inventory_final_2026-11-04.csv`。
- Haas 的大部分服务资料是官方简体中文网页快照；2025 铣床操作手册是英文当前版本对照。
- Edwards 当前权威主手册为 `A73501880_L` 英文版。入库范围只生成项目中文译文，英文原文始终保留。
- 原始资料不应提交版本库；`.gitignore` 已排除 raw archive、派生语料、结构化文件、评测集和冻结包。
- 阶段 0 的所有结构化内容都须由现有归档来源派生，不能补充新外部资料。
- 现有下载记录有 42 行（35 downloaded、7 failed），但与当前 40 个真实 PDF 不是一对一：已删除的 `HAAS-ALARM-HELP-ZH` 仍显示为 downloaded；英文 Haas 报警帮助和 Edwards 英文产品册尚无下载记录映射。最终来源登记器必须以实际存在的归档文件为基准，并显式处理这些补充映射，不能直接把旧下载 CSV 当作冻结依据。
- 旧 CSV 的 `status` 不能作为资料真实性判断：至少四份浏览器辅助下载的 Edwards 资料虽在旧表中标为 failed，但真实 PDF 已存在且可解析。
- 通过覆盖项补齐与修正后，最终来源登记有 40 条唯一 `source_id`；OSHA 两份快照正确标为英文，Edwards 起吊指南统一标为 `multi_zh-CN`。
- 页级解析已覆盖所有 1332 页：1296 页可提取文本，36 页为空文本，未发生 PDF/哈希失败。空文本不是自动错误；后续必须按页审计，确认其为封面、图片页或 OCR 缺失的正文。
