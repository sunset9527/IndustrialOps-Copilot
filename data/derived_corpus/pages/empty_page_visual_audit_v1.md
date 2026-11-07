# 页级空文本视觉审核记录 v1

审核日期：2026-11-07  
输入：`page_corpus_v1.jsonl` 中 `text_extraction_status: empty` 的 36 页  
审核方法：将每个候选页渲染为 PNG；对全部页进行预览，并对代表性封面页、目录末页、刀库故障指南末页和英文操作手册前页进行高分辨率复核。

## 结论

36 页均为纯白页面，或仅包含网页快照的非业务视觉残留（黑色导航框/页框）。未观察到操作正文、报警表、维修步骤、技术图注、可读表格或可用设备示意图。

统一处理：

- `classification`: `non_operational_blank_or_navigation_artifact`
- `index_action`: `exclude`
- `ocr_required`: `false`
- `reason`: 不包含本知识包需要的可检索运维证据；OCR 不会增加有效正文。

## 已审核页

| 来源 | 页码 | 数量 | 视觉结论 |
|---|---:|---:|---|
| `HAAS-VF2-SCOPE-ZH` | 7-18 | 12 | 纯白页 |
| `HAAS-UMBRELLA-TSG-ZH` | 1, 30 | 2 | 空白/导航页框残留 |
| `HAAS-TOOL-CHANGER-TOC-ZH` | 1, 4 | 2 | 空白/导航页框残留 |
| `HAAS-40T-MOTOR-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-VECTOR-DRIVE-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-UMBRELLA-REPLACE-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-UMBRELLA-ALIGN-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-SERVO-MOTOR-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-SERVO-AMP-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-OP-EN-2025` | 2 | 1 | 空白页 |
| `HAAS-VFVM-SPECS-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-NGC-PSUP-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-NGC-ICONS-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-NGC-ERROR-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-NGC-BREAKER-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-MAINTENANCE-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-LUBE-INTRO-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-HALO-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-FLOOD-COOLANT-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-AXIS-MOTION-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-40T-SPINDLE-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-NGC-IO-ZH` | 1 | 1 | 空白/导航页框残留 |
| `HAAS-WYE-DELTA-ZH` | 1 | 1 | 空白/导航页框残留 |

合计：36 页。该审核只决定文本索引/OCR 行为；原始 PDF 和页级记录均保持不变。
