# P 级别判定标准（P-Severity Rubric）

> ℹ️ 本文件提及的 `@satisfies` / `@verifies` 标注属于 **layout.v1 legacy**（v2 起改读 traceability.yml，[FUTURE 状态](../../pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)）。

所有维度发现统一按优先级分级。

## P1 判定标准（阻塞发布，必须修复）

- **--docs**：原始需求遗漏（层 1）、AC 无设计支撑（层 2）、AC 无对应测试（层 3）
- **--impl**：AC 未满足（❌）、接口签名与设计不符、模块职责严重偏离、核心 AC 无 @satisfies 标注
- **--impl 增强（盲区 6 → 阻断 DoD ✅）**：spec 显式提及 IT-XXX 期望 N 类断言但实际 < N，且 DoD 整项 ✅；或测试用例部分完成（K/N 类）DoD 仍整项 ✅ 未拆分
- **--impl 增强（盲区 7 → 阻断 SPI 升级合并）**：SPI / 对外契约 DTO 字段集变化时上游 PO 视觉展示性字段（BigDecimal / String / LocalDateTime / Enum 等）未透传且无 `DEFER:<原因>` + 前端锚点 cross-link；或 task spec 缺"字段透传矩阵"三列映射表
- **--ui**：布局结构与设计稿不符、关键交互状态未实现、AC 描述的 UI 行为在设计稿中缺失
- **--readiness**：AC 无对应测试用例（D1）、任务存在循环依赖（D3）、孤立任务无需求关联（D4）

## P2 判定标准（应修复，建议转入 ms-insights）

- **--docs**：原始需求偏移（层 1）、AC 缺异常路径测试（层 3）
- **--impl**：AC 部分满足（⚠️）、数据流轻微偏离、@satisfies 覆盖率 < 80%
- **--ui**：间距/颜色/字体的显著偏差、响应式断点差异
- **--readiness**：任务文件路径不够具体（D2）、设计↔任务文件路径不一致（D4）

## P3 判定标准（可优化，记录备忘）

- **--docs**：过度扩展（层 1）、设计孤立项（层 2）
- **--impl**：非核心代码缺少标注、非关键路径微偏离
- **--ui**：间距/颜色/字体的轻微偏差
- **--readiness**：任务描述过于简略但路径具体

## 处理方式

| 优先级 | 含义 | 处理方式 |
|--------|------|----------|
| **P1** | 阻塞发布 | 必须修复，建议转入 ms-dev-tasks |
| **P2** | 应修复 | 建议修复，建议转入 ms-insights |
| **P3** | 可优化 | 可选修复，记录备忘 |
