# 追溯健康度评分规则（Health Scoring）

> ℹ️ 本文件评分基于 `@satisfies` / `@verifies` 等标注扫描，属于 **layout.v1 legacy**（v2 起改读 traceability.yml，[FUTURE 状态](../../pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)）。

## 偏差检测规则

| 偏差类型 | 检测方式 | 严重程度 |
|----------|---------|----------|
| AC 无测试覆盖 | 追溯矩阵中 AC 行无关联测试 | 高 |
| F 无任务闭环 | 功能点无关联开发任务 | 高 |
| 孤立编号 | 编号存在于代码但不在文档中 | 中 |
| 标注不一致 | 代码 @verifies 与文档追溯矩阵不匹配 | 中 |
| 状态落后 | 任务已完成但文档状态未更新 | 低 |
| INS 未转化 | 已确认洞察未生成对应需求 | 低 |
| Schema drift | 产物 frontmatter.spec_version 落后 skill 常量（`/ms-sync --schema-drift` 触发） | 信息性（权重 0.05，不阻断 audit） |

## 健康度计算

健康度 = 已覆盖项 / 总检查项 × 100%

检查项包括：
- AC → 测试映射完整性（权重 0.30）
- F → 任务闭环完整性（权重 0.30）
- 编号一致性（文档 ↔ 代码）（权重 0.20）
- 状态同步度（权重 0.15）
- Schema drift（权重 0.05，仅 `--schema-drift` 启用时计入；关闭时该项权重按前 4 项原比例缩放，最终总分保留 **两位小数**呈现，避免展示抖动）

**Schema drift 计入方式**：
- 扫描结果由 `/ms-verify --schema-drift` 提供（ms-sync 不自行扫描，只消费结果）
- 计分：`drift_score = (current_count) / (current_count + drift_count + legacy_count)`；无产物时返回 1.0
- 不阻断 audit pass/fail（pass 阈值仍按前 4 项综合评分；drift 仅影响总分呈现，不改变阈值判定）

## 偏差修复路由表

| 偏差类型 | 修复 Skill | 说明 |
|----------|-----------|------|
| 设计缺失/漂移 | `/ms-system-design` | 代码有新接口但文档未记录 |
| AC 缺测试 | `/ms-test-cases` | 验收标准无对应测试用例 |
| F 缺任务闭环 | `/ms-dev-tasks` | 功能点无关联开发任务 |
| 代码已实现文档落后 | `/ms-sync --absorb` | 状态未更新、新内容未登记 |
| 追溯矩阵代码位置缺失 | `/ms-sync` | 代码标注未扫描到矩阵 |
| Schema drift | `/ms-pipeline realign` 或 `/ms-<skill> --realign` | 产物按新规范查漏补缺；权重低，仅建议不强制 |

## 引用方

- `ms-sync`：audit 阶段健康度评分
- `ms-sync --schema-drift`：启用 schema drift 权重项，委托 `ms-verify --schema-drift` 获取扫描结果
