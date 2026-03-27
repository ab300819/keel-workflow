# 重构报告模板

```markdown
# 重构报告

## 概览

- **重构范围**: <scope>
- **重构时间**: <timestamp>
- **重构类型**: 普通重构 / 重写

## 重构前状态

| 指标 | 值 |
|------|-----|
| 文件数 | 5 |
| 代码行数 | 1,200 |
| 测试覆盖率（行） | 45% |
| 测试覆盖率（分支） | 38% |
| 主要问题 | 上帝类、过长函数 |

## 重构后状态

| 指标 | 值 | 变化 |
|------|-----|------|
| 文件数 | 8 | +3 |
| 代码行数 | 980 | -220 |
| 测试覆盖率（行） | 85% | +40% |
| 测试覆盖率（分支） | 82% | +44% |

## 重构内容

### 已完成

1. [x] UserService 拆分为 UserQueryService + UserCommandService
2. [x] 提取 validateUser、formatUser 函数
3. [x] 消除 processData 重复代码
4. [x] 补充单元测试 23 个

### 变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/services/user.ts` | 修改 | 拆分职责 |
| `src/services/user-query.ts` | 新增 | 查询服务 |
| `src/services/user-command.ts` | 新增 | 命令服务 |
| `src/utils/user-utils.ts` | 新增 | 提取的工具函数 |
| `tests/services/user.test.ts` | 修改 | 补充测试 |

## 测试报告

```
Test Suites: 12 passed, 12 total
Tests:       89 passed, 89 total
Coverage:
  Lines:     85.2%
  Branches:  82.1%
  Functions: 88.5%
```

## 风险与注意事项

- `UserQueryService` 和 `UserCommandService` 需要分别注入
- 原 `UserService` 保留为门面类，后续可逐步迁移调用方

## 下一步建议

1. 更新调用方代码，逐步使用新的服务类
2. 监控生产环境，确保行为一致
3. 考虑删除原 UserService 门面类
```
