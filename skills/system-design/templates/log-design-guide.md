# 日志设计指南

> 日志是调试和问题排查的关键工具，特别是对于手动测试和 E2E 测试场景。
>
> ℹ️ 文中编号示例使用 v1 前缀；v2 项目 [FUTURE] 走双轨。详见 [id-scheme-implementation.md](../../pipeline/references/layout/id-scheme-implementation.md)。

## 日志级别

| 级别 | 用途 | 示例场景 |
|------|------|----------|
| **ERROR** | 需要立即处理的错误 | 数据库连接失败、支付失败、关键服务不可用 |
| **WARN** | 潜在问题但不影响核心功能 | 重试成功、降级处理、资源接近阈值 |
| **INFO** | 关键业务操作 | 用户登录、订单创建、状态变更 |
| **DEBUG** | 调试信息 | 函数入参、中间状态、性能指标 |

## 关键日志点

设计文档中应列出关键操作的日志点：

```markdown
| 操作 | 日志级别 | 日志内容 | 关联编号 |
|------|----------|----------|----------|
| 用户登录成功 | INFO | `[F-002] User login: userId={}, ip={}` | F-002, AC-006 |
| 用户登录失败 | WARN | `[F-002] Login failed: userId={}, reason={}` | F-002, AC-007 |
| 密码验证失败 | WARN | `[F-002] Password mismatch: userId={}` | AC-007 |
| 数据库异常 | ERROR | `[INFRA] DB error: {}, query={}` | - |
| 订单创建 | INFO | `[F-003] Order created: orderId={}, userId={}` | F-003 |
```

## 日志格式

```
[时间] [级别] [追溯ID] [模块] 消息 {结构化数据}
```

**示例**：
```
2024-01-26 10:30:15 INFO [req-abc123] [UserService] User created {"userId": "u001", "email": "user@example.com"}
2024-01-26 10:30:16 ERROR [req-abc123] [EmailService] Failed to send verification email {"userId": "u001", "error": "SMTP timeout"}
```

## 追溯 ID (Correlation ID)

| 属性 | 说明 |
|------|------|
| **生成时机** | 每个请求入口生成唯一 ID |
| **传递方式** | 通过 Context/Header 贯穿整个调用链 |
| **命名约定** | `traceId` 或 `correlationId` |
| **格式** | UUID 或 `req-{timestamp}-{random}` |

**用途**：
- E2E 测试失败时，通过 `traceId` 查询完整日志链
- 分布式系统中跨服务追踪
- 问题排查时关联所有相关日志

## E2E 测试日志策略

| 场景 | 日志策略 | 说明 |
|------|----------|------|
| 测试通过 | 仅保留 ERROR/WARN | 减少日志量 |
| 测试失败 | 保留完整日志（含 DEBUG） | 便于排查 |
| 手动复现 | 启用 DEBUG 级别 | 最大化信息 |

**失败分析流程**：
```
1. 获取失败测试的 traceId
   │
   ▼
2. 查询该 traceId 的完整日志链
   │
   ▼
3. 定位首个 ERROR/异常点
   │
   ▼
4. 分析上下文日志
```
