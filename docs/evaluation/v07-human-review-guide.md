# v0.7 双人审核输入

每个审核维度使用一份独立 JSONL 文件；不要把不同维度（例如“证据支持”和“风险等级”）混在同一份文件。每位审核者独立完成标注后再合并，避免先看对方结论。

每行必须包含：

- `case_id`：已审核通过的扩展场景 ID；
- `reviewer_id`：两个不相同的人工审核者 ID；
- `label`：该维度的离散标签；
- `reviewed_at_utc`：人工审核时间。

输入文件不能含手册全文、API Key、Bearer token 或数据库凭据。候选场景在完成证据绑定与批准前不能用于 Kappa 或 Judge 汇总。

在仓库根目录运行：

```powershell
E:\python\python.exe -m industrialops.evaluation.v07.review_labels `
  --labels <两人合并后的-labels.jsonl> `
  --reviewer-a <审核者A> `
  --reviewer-b <审核者B> `
  --output data/evaluation/reports/v07/<run-id>/human-agreement.json
```

只有同一 `case_id` 同时拥有两位不同审核者的标签才进入原始一致率与 Cohen's Kappa 分母；单人、重复或缺失字段会明确失败或标为 `not_run`，绝不补造标签。
