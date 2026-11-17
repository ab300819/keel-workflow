# 追溯健康度评分规则（Health Scoring）

## 偏差检测规则

| 偏差类型 | 检测方式 | 严重程度 |
|----------|---------|----------|
| AC 无测试覆盖 | 追溯矩阵中 AC 行无关联测试 | 高 |
| F 无任务闭环 | 功能点无关联开发任务 | 高 |
| 孤立编号 | 有定义但没挂到任何 AC / F 的测试或任务（定义见 [audit-mode.md](audit-mode.md)）；「被引用但无定义」是死链，归 health-lint 的 `health/dead-link` | 中 |
| 变更来源失效 | 追溯矩阵的 `<repository>@<sha>` 在对应代码根解析不到 | 中 |
| 状态落后 | 任务已完成但文档状态未更新 | 低 |
| INS 未转化 | 已确认洞察未生成对应需求 | 低 |
| Schema drift | 产物 frontmatter.spec_version 落后 skill 常量（`/verify --schema-drift` 触发，sync 仅合并其结果） | 信息性（权重 0.05，不阻断 audit） |

## 健康度计算

健康度 = 已覆盖项 / 总检查项 × 100%

检查项包括：
- AC → 测试映射完整性（权重 0.30）
- F → 任务闭环完整性（权重 0.30）
- 编号一致性（无孤立编号）（权重 0.20）
- 状态同步度（权重 0.15）
- Schema drift（权重 0.05，仅 `--schema-drift` 启用时计入；关闭时该项权重按前 4 项原比例缩放，最终总分保留 **两位小数**呈现，避免展示抖动）

**Schema drift 计入方式**：
- 扫描结果由 `/verify --schema-drift` 提供（sync 不自行扫描，只消费结果）
- 计分：`drift_score = (current_count) / (current_count + drift_count + legacy_count)`；无产物时返回 1.0
- 不阻断 audit pass/fail（pass 阈值仍按前 4 项综合评分；drift 仅影响总分呈现，不改变阈值判定）

## 偏差修复路由表

| 偏差类型 | 修复 Skill | 说明 |
|----------|-----------|------|
| 设计缺失/漂移 | `/system-design` | 代码有新接口但文档未记录 |
| AC 缺测试 | `/test-cases` | 验收标准无对应测试用例 |
| F 缺任务闭环 | `/dev-tasks` | 功能点无关联开发任务 |
| 代码已实现文档落后 | `/sync` | 状态未更新、新内容未登记，默认流程的吸收阶段处理 |
| 追溯矩阵「变更来源」缺失或失效 | `/sync` | trace 阶段校验补齐 |
| Schema drift | `/pipeline realign` 或 `/<skill> --realign` | 产物按新规范查漏补缺；权重低，仅建议不强制 |

## 引用方

- `sync`：audit 阶段健康度评分
- `verify --schema-drift`：提供 schema drift 扫描结果，供本评分的 drift 权重项使用
