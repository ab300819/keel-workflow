# DevDocs 改造报告模板

```markdown
# DevDocs 改造报告

## 改造概览

- **项目名称**：<project>
- **改造时间**：<timestamp>
- **改造类型**：新项目改造 / 版本迁移

## 改造结果

### 文档状态

| 文档 | 改造前 | 改造后 | 动作 |
|------|--------|--------|------|
| 需求文档 | docs/req.md | docs/devdocs/01-requirements.md | 转换 + 编号 |
| 系统设计 | - | docs/devdocs/02-system-design.md | 新建 |
| 测试用例 | tests/README.md | docs/devdocs/03-test-cases.md | 转换 + 编号 |
| 开发任务 | TODO.md | docs/devdocs/04-dev-tasks.md | 标准化 |

### 编号分配

| 类型 | 数量 | 范围 |
|------|------|------|
| 功能点 (F) | 5 | F-001 ~ F-005 |
| 用户故事 (US) | 12 | US-001 ~ US-012 |
| 验收标准 (AC) | 28 | AC-001 ~ AC-028 |
| 单元测试 (UT) | 15 | UT-001 ~ UT-015 |
| 集成测试 (IT) | 4 | IT-001 ~ IT-004 |
| E2E 测试 (E2E) | 3 | E2E-001 ~ E2E-003 |

### 待完善项

以下内容标记为 [待补充]：

- [ ] AC-015 ~ AC-020 验收标准细化
- [ ] 非功能性需求-性能指标
- [ ] API 响应示例

## 下一步建议（强制路由）

改造完成后，**必须**执行以下之一建立基线：

| 场景 | 必须执行 | 说明 |
|------|----------|------|
| **补充背景信息** | `/devdocs-requirements --context` | **推荐**：补充代码中看不出的背景、约束、参考资料 |
| 首次改造 | `/devdocs-sync` | 检查追溯健康度 |
| 有待补充项 | `/devdocs-requirements` | 完善需求文档 |
| 开始开发 | `/devdocs-dev-tasks` → `/devdocs-dev-workflow` | 执行任务 |
| 添加功能 | `/devdocs-feature` | 增量开发 |

> 改造不是终点，必须通过后续 Skill 进入正常开发循环。
>
> **提示**：逆向推导只能从代码提取结构信息，建议用 `--context` 模式补充项目背景、技术约束、参考资料等代码中看不出的信息。
```
