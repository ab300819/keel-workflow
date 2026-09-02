# 功能日志模板

使用此模板生成或追加 `docs/devdocs/00-feature-log.md`。

```markdown
# 新功能开发日志

## v2: <功能名称> (YYYY-MM-DD)

### 新增内容

| 类型 | 编号 | 描述 |
|------|------|------|
| 功能点 | F-004 | <描述> |
| 用户故事 | US-009, US-010 | <描述> |
| 验收标准 | AC-016 ~ AC-020 | 5 条 |
| 测试用例 | UT-013 ~ UT-015, E2E-003 | 4 条 |
| 开发任务 | T-11 ~ T-14 | 4 个 |

### 影响范围

- 新增模块：<模块名>
- 修改接口：<接口名>
- 回归风险：<风险点>

### 关联文档

- [01-requirements.md](01-requirements.md) - 已更新
- [02-system-design.md](02-system-design.md) - 已更新
- [03-test-cases.md](03-test-cases.md) - 已更新
- [04-dev-tasks.md](04-dev-tasks.md) - 已更新

---

## v1: 初始版本 (YYYY-MM-DD)

...
```
