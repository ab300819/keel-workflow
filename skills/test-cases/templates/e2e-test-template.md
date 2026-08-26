# E2E 测试模板

> ℹ️ E2E 编号 v1/v2 一致；引用的 AC / F-vs-FEAT 走双轨。详见 [id-scheme-implementation.md](../../pipeline/references/layout/id-scheme-implementation.md)。

使用此模板生成 `docs/devdocs/03-test-e2e.md`

---

```markdown
# E2E 测试用例：<功能名称>

## 测试框架

- **框架**：<Playwright / Cypress>
- **语言**：<TypeScript / JavaScript>

## 覆盖要求

- E2E 覆盖按风险与成本决定，核心路径优先
- 覆盖完整用户流程
- 验证关键验收标准

---

## 外部依赖 Provider 策略

E2E 测试默认运行在真实环境，但部分外部依赖（第三方支付、短信网关、OAuth 等）需要 Mock 降级能力。通过 Provider 模式实现配置化切换。

### 策略总览

| 外部依赖 | 接口 | Mock 方式 | 真实方式 | 默认模式 |
|----------|------|-----------|----------|----------|
| 后端 API | - | - | 真实调用 | real |
| 第三方支付 | `IPaymentGateway` | 路由拦截 | 真实回调 | mock |
| 短信验证码 | `ISmsGateway` | 固定验证码 | 真实短信 | mock |
| OAuth 登录 | `IOAuthProvider` | 模拟回调 | 真实跳转 | mock |

> **核心原则**：前后端交互全真实，不可控的第三方服务通过 Provider 可切换。

### 切换方式

通过环境变量 `E2E_PROVIDER_MODE=mock|real` 控制。工厂函数根据该变量返回对应的 Provider 实现。

---

## Provider 目录结构

```
tests/
├── e2e/
│   ├── providers/
│   │   ├── index.ts              # Provider 工厂：根据环境变量创建对应实现
│   │   ├── payment.provider.ts   # IPaymentGateway 接口定义
│   │   ├── payment.mock.ts       # Mock：路由拦截模拟支付回调
│   │   ├── payment.real.ts       # 真实：对接支付网关
│   │   ├── sms.provider.ts       # ISmsGateway 接口定义
│   │   ├── sms.mock.ts           # Mock：返回固定验证码
│   │   └── sms.real.ts           # 真实：从测试环境 API 查询验证码
│   ├── fixtures/
│   │   └── test-data.ts
│   ├── pages/                    # Page Object 模式
│   │   ├── LoginPage.ts          # 封装登录页交互
│   │   ├── RegisterPage.ts       # 封装注册页交互
│   │   └── DashboardPage.ts      # 封装首页交互
│   └── specs/
│       ├── auth.spec.ts
│       └── user.spec.ts
└── playwright.config.ts
```

### Provider 接口说明

| 接口 | 方法 | 职责 |
|------|------|------|
| `ISmsGateway` | `setup(page)` | Mock 模式下设置路由拦截 |
| `ISmsGateway` | `getVerificationCode(phone)` | Mock 返回固定值，真实模式从 API 查询 |
| `ISmsGateway` | `teardown()` | 清理拦截 |
| `IPaymentGateway` | `setup(page)` | Mock 模式下拦截支付回调 |
| `IPaymentGateway` | `verifyPayment(orderId)` | 验证支付状态 |

### Mock 与真实实现的行为差异

| Provider | Mock 行为 | 真实行为 |
|----------|-----------|----------|
| `SmsGateway` | 拦截短信发送 API，`getVerificationCode` 返回固定值 `123456` | 不拦截，`getVerificationCode` 从测试环境 API 查询最新验证码 |
| `PaymentGateway` | 拦截支付回调，立即返回成功 | 对接真实支付网关，等待回调 |

### Page Object 模式

每个页面封装为一个 Page Object 类，负责：
- 页面导航（`goto()`）
- 用户交互（`login(email, password)`、`register(email, password)` 等）
- 断言辅助（`expectError(message)`、`expectSuccess()` 等）

测试用例通过 Page Object 组合操作，而非直接操作 DOM 选择器。

---

## 测试用例

### F-001: <功能点名称>

| 编号 | 用户故事 | 验收标准 | 测试场景 | 优先级 |
|------|----------|----------|----------|--------|
| E2E-001 | US-001 | AC-001~AC-003 | 完整注册流程 | P0 |
| E2E-002 | US-002 | AC-004, AC-005 | 密码强度校验 | P1 |

#### E2E-001: 完整注册流程

**关联**：
- 用户故事：US-001
- 验收标准：AC-001, AC-002, AC-003

**操作步骤**：
1. 打开注册页面 `/register`
2. 输入有效邮箱
3. 输入符合要求的密码
4. 点击注册按钮

**预期结果**：
- 注册成功，跳转到欢迎页 `/welcome`
- 欢迎消息可见
- 收到验证邮件（可选验证）

---

### F-002: <功能点名称>

| 编号 | 用户故事 | 验收标准 | 测试场景 | 优先级 |
|------|----------|----------|----------|--------|
| E2E-003 | US-003 | AC-006~AC-008 | 完整登录流程 | P0 |

#### E2E-003: 完整登录流程

**关联**：
- 用户故事：US-003
- 验收标准：AC-006, AC-007, AC-008

**操作步骤**：
1. 打开登录页面 `/login`
2. 输入已注册邮箱
3. 输入正确密码
4. 点击登录按钮

**预期结果**：
- 登录成功，跳转到首页 `/dashboard`
- 显示用户名称

---

## 用户旅程测试

用户旅程串联多个用户故事，验证跨功能的完整业务闭环。与单 US E2E 的区别：

- **E2E-XXX**：单个用户故事的完整交互（如"完成注册"）
- **Journey-XXX**：串联 >= 2 个 US 的业务闭环（如"注册 → 验证 → 登录 → 使用"），关注步骤间状态传递

### 设计指导

- 至少 1 条核心旅程；中大型产品通常 2-3 条
- 旅程必须串联 **>= 2 个 US**，否则属于单 US E2E
- 旅程关注 **步骤间状态传递**（上一步的输出是下一步的前置）
- 典型旅程类型：新用户首次体验、核心业务闭环、异常恢复路径

### 旅程用例格式

| 编号 | 角色 | 串联故事 | 旅程步骤摘要 | 优先级 |
|------|------|----------|-------------|--------|
| Journey-001 | <用户角色> | US-001 → US-003 | <步骤摘要> | P0 |

#### Journey-001: <旅程名称>

**角色**：<用户角色>
**串联故事**：US-001 → US-003 → US-005
**覆盖 AC**：AC-001, AC-002, AC-006, AC-007, AC-015

**旅程步骤**：

| 步骤 | 对应 US | 用户操作 | 预期结果 | 检查点 |
|------|---------|----------|----------|--------|
| 1 | US-001 | 注册账号 | 跳转验证页 | 账号已创建 |
| 2 | US-001 | 验证邮箱 | 跳转登录页 | 邮箱已验证 |
| 3 | US-003 | 登录 | 进入首页 | Token 有效 |
| 4 | US-005 | 执行核心操作 | 操作成功 | 数据已持久化 |

---

## 测试数据管理

### 数据准备

| 场景 | 所需数据 | 准备方式 | 外部依赖 Provider | 清理方式 |
|------|----------|----------|-------------------|----------|
| 注册 | 无 | - | SMS: MockSmsGateway | 删除测试用户 |
| 登录 | 测试用户 | API 预创建 | - | 测试后删除 |
| 支付 | 测试订单 | API 预创建 | Payment: MockPaymentGateway | 测试后删除 |

### 数据隔离

每个测试用例通过 `beforeEach` 调用 API 创建隔离数据（使用时间戳唯一标识），`afterEach` 调用 API 清理。

---

## 追溯汇总

| 编号 | 用户故事 | 验收标准 | 测试场景 | 状态 |
|------|----------|----------|----------|------|
| E2E-001 | US-001 | AC-001~AC-003 | 完整注册流程 | ✅ |
| E2E-002 | US-002 | AC-004, AC-005 | 密码强度校验 | ✅ |
| E2E-003 | US-003 | AC-006~AC-008 | 完整登录流程 | ✅ |
| Journey-001 | US-001→US-003 | AC-001~AC-008 | 新用户首次体验 | ✅ |
```

---

## 编号规范

- **E2E 格式**：`E2E-XXX`（全局顺序编号），关联单个 US
- **Journey 格式**：`Journey-XXX`（全局顺序编号），串联 >= 2 个 US
- **关联**：E2E 必须关联 US + AC；Journey 必须关联串联的多个 US + 覆盖的 AC
