# 集成测试模板

使用此模板生成 `docs/devdocs/03-test-integration.md`

---

```markdown
# 集成测试用例：<功能名称>

## 测试范围

集成测试验证多个组件协作的正确性，包括：
- 服务间调用
- 数据库操作
- 外部服务集成（邮件、支付等）
- API 端到端调用

## 覆盖要求

- 每个功能点至少 1 个集成测试
- 覆盖核心业务流程
- 验证组件间数据传递

---

## Provider 策略

集成测试通过 **Provider 模式**管理外部依赖，测试代码只依赖接口，不直接创建 Mock。

### 策略总览

| 组件类型 | 接口 | Mock 实现 | 真实实现 | 默认模式 |
|----------|------|-----------|----------|----------|
| 数据库 | `IDatabase` | - | 真实测试库 | real |
| 内部服务 | - | - | 真实调用 | real |
| 外部 API | `IPaymentProvider` | `MockPaymentProvider` | `RealPaymentProvider` | mock |
| 邮件服务 | `IEmailProvider` | `MockEmailProvider` | `RealEmailProvider` | mock |

> **核心原则**：内部组件真实调用，外部依赖通过 Provider 接口可切换。

### 切换方式

通过环境变量 `IT_PROVIDER_MODE=mock|real` 控制。工厂函数根据该变量返回对应的 Provider 实现。

> **命名规则**：各测试类型统一使用 `<TEST_TYPE>_PROVIDER_MODE` 格式（IT 用 `IT_PROVIDER_MODE`，E2E 用 `E2E_PROVIDER_MODE`）。

---

## Provider 目录结构

```
tests/
├── providers/
│   ├── index.ts                # Provider 工厂：根据环境变量创建对应实现
│   ├── email.provider.ts       # IEmailProvider 接口定义
│   ├── email.mock.ts           # Mock 实现：内存记录调用，不发送真实邮件
│   ├── email.real.ts           # 真实实现：对接外部邮件服务 API
│   ├── payment.provider.ts     # IPaymentProvider 接口定义
│   ├── payment.mock.ts         # Mock 实现：模拟支付回调
│   └── payment.real.ts         # 真实实现：对接支付网关
├── integration/
│   └── auth.integration.test.ts
└── test.config.ts              # 读取 IT_PROVIDER_MODE 环境变量
```

### Provider 接口说明

| 接口 | 方法 | 职责 |
|------|------|------|
| `IEmailProvider` | `sendVerificationEmail(to, token)` | 发送验证邮件，返回 `{ messageId }` |
| `IPaymentProvider` | `createCharge(amount, currency)` | 创建支付，返回 `{ chargeId, status }` |

### Mock 与真实实现的行为差异

| Provider | Mock 行为 | 真实行为 |
|----------|-----------|----------|
| `EmailProvider` | 内存记录发送参数，提供 `findByRecipient()` 查询 | 调用外部邮件 API |
| `PaymentProvider` | 立即返回成功/失败（可配置） | 调用支付网关，等待回调 |

---

## 测试用例

### F-001: <功能点名称>

| 编号 | 验收标准 | 测试场景 | 涉及组件 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| IT-001 | AC-003 | <场景描述> | <组件A + 组件B> | <预期结果> | P0 |

**测试步骤**：
1. <准备步骤>
2. <执行步骤>
3. <验证步骤>

---

### F-002: <功能点名称>

| 编号 | 验收标准 | 测试场景 | 涉及组件 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| IT-002 | AC-006 | <场景描述> | <组件A + 组件B> | <预期结果> | P0 |

---

## 测试数据管理

### 数据隔离

每个测试用例运行前清理相关测试数据，运行后关闭连接。使用带时间戳的唯一标识（如 `test-{timestamp}@test.com`）确保用例间数据隔离。

### 测试数据工厂

通过工厂函数集中管理测试数据，支持参数覆盖默认值，避免用例中重复构造数据。

---

## 追溯汇总

| 编号 | 验收标准 | 测试场景 | 状态 |
|------|----------|----------|------|
| IT-001 | AC-003 | <场景> | ✅ |
| IT-002 | AC-006 | <场景> | ✅ |
```

---

## 示例：用户认证功能

```markdown
# 集成测试用例：用户认证

## 测试范围

- UserService + Database：用户数据持久化
- AuthService + EmailProvider：认证邮件发送
- TokenService + Database：Token 存储和验证

## Provider 策略

| 组件类型 | 接口 | Mock 实现 | 真实实现 | 默认模式 |
|----------|------|-----------|----------|----------|
| 数据库 | `IDatabase` | - | 测试数据库 | real |
| 邮件服务 | `IEmailProvider` | `MockEmailProvider` | `RealEmailProvider` | mock |
| Token 存储 | `IDatabase` | - | 测试数据库 | real |

---

## 测试用例

### F-001: 用户注册

| 编号 | 验收标准 | 测试场景 | 涉及组件 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| IT-001 | AC-003 | 注册后发送验证邮件 | UserService + EmailProvider + DB | 用户创建成功，邮件发送调用正确 | P0 |

**测试步骤**：
1. 准备：通过工厂函数创建测试用户数据
2. 执行：调用 `userService.register(userData)`
3. 验证用户：查询数据库确认用户已创建，邮箱匹配
4. 验证邮件：确认 EmailProvider 收到正确的收件人和 token 参数

---

### F-002: 用户登录

| 编号 | 验收标准 | 测试场景 | 涉及组件 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| IT-002 | AC-006~AC-008 | 完整登录流程 | AuthService + UserService + TokenService | 返回有效 Token，刷新 Token 存储 | P0 |

**测试步骤**：
1. 准备：创建并保存测试用户
2. 执行：调用 `authService.login(email, password)`
3. 验证 Token：确认返回 accessToken 和 refreshToken
4. 验证存储：查询数据库确认 refreshToken 已持久化

**异常路径**：
- 连续 5 次错误密码后，确认账号锁定（`lockedUntil` 字段大于当前时间）

---

### F-003: 密码找回

| 编号 | 验收标准 | 测试场景 | 涉及组件 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| IT-003 | AC-011~AC-013 | 密码重置流程 | AuthService + EmailProvider + TokenService | Token 生成、邮件发送、密码更新 | P1 |

---

## 追溯汇总

| 编号 | 验收标准 | 测试场景 | 状态 |
|------|----------|----------|------|
| IT-001 | AC-003 | 注册后发送验证邮件 | ✅ |
| IT-002 | AC-006~AC-008 | 完整登录流程 | ✅ |
| IT-003 | AC-011~AC-013 | 密码重置流程 | ✅ |
```
