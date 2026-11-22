# IndustrialOps Copilot v1.0.0 发布说明

**发布状态：** 本地发布准备中；尚未推送标签或创建 GitHub Release。  
**范围基线：** v0.8 `release_verified`（2026-11-22）。

## 已验证能力

- 在两个冻结设备包范围内处理 CNC 告警、真空泵维护、设备上下文和来源引用；
- 使用结构化证据、型号/版本兼容性约束、安全门控和证据不足保守处理辅助诊断；
- 基于服务端诊断快照创建工单草稿，并由 `approver` 或 `admin` 人工批准/拒绝，支持重启恢复；
- 通过独立 Compose RC 验收双设备链路、浏览器演示、受控故障恢复、离线行为与脱敏报告。

## 适用边界

- 仅覆盖 Haas VF-2（NGC）和 Edwards nXDS 标准型号的已声明资料范围；
- 不执行 PLC、CNC、真空泵或其他真实设备控制；
- 不提供预测性维护、实时传感器分析、真实 CMMS 写入或厂商资料再分发；
- 设备、告警历史和工单是合成演示数据；厂商资料、派生语料、冻结包和本地模型只在本机合法使用；
- v0.7 的真实 Judge 仅覆盖两条 CNC `evidence_fallback` 场景，不能外推为在线回答、完整检索链路或工业泛化质量。

## 评测与已知限制

发布候选验收事实见 [v0.8 RC 本机发布验收](docs/evaluation/v08-release-validation.md)，完整限制见 [v0.7 已知限制](docs/evaluation/v07-known-limitations.md)，v1.0 汇总见 [v1.0 评测摘要](docs/evaluation/v1.0-release-summary.md)。

## 本次跳过项

按照项目负责人决定，CNC 主案例与真空泵迁移案例的视频录制不属于本次交付；项目保留可复现的演示与验收步骤，但不声称已附带演示视频。

## 后续外部发布

本地验证通过后，项目负责人自行检查提交与 `dist/` 中的 ZIP/校验文件，再执行推送、创建 `v1.0.0` 标签并在 GitHub 创建 Release。精确命令与校验顺序见[本地发布就绪手册](docs/operations/v1.0-release-readiness.md)。
