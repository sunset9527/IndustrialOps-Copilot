# IndustrialOps Copilot 实施发现

## 2026-11-07

- `data/raw_archive/` 当前有 40 份 PDF、1332 页；最终来源清单在 `data/source_manifests/source_inventory_final_2026-11-04.csv`。
- Haas 的大部分服务资料是官方简体中文网页快照；2025 铣床操作手册是英文当前版本对照。
- Edwards 当前权威主手册为 `A73501880_L` 英文版。入库范围只生成项目中文译文，英文原文始终保留。
- 原始资料不应提交版本库；`.gitignore` 已排除 raw archive、派生语料、结构化文件、评测集和冻结包。
- 阶段 0 的所有结构化内容都须由现有归档来源派生，不能补充新外部资料。
