# MTE 正反例代码

> 配合 [SKILL.md](../SKILL.md) 使用。规则与阈值以主文件为权威，本文件仅提供示例展开。

## 模块设计

### 单一职责

```
✅ 正确：一个类/函数只做一件事
- UserService: 用户业务逻辑
- UserRepository: 用户数据访问
- UserValidator: 用户数据校验

❌ 错误：一个类做多件事
- UserManager: 业务逻辑 + 数据访问 + 校验 + 发送邮件
```

### 依赖方向

```
┌─────────────────────────────────────┐
│           Interface Layer           │  ← 薄层，无业务逻辑
├─────────────────────────────────────┤
│           Service Layer             │  ← 业务逻辑（核心）
├─────────────────────────────────────┤
│           Domain Layer              │  ← 领域模型
├─────────────────────────────────────┤
│         Infrastructure Layer        │  ← 可替换
└─────────────────────────────────────┘

依赖规则：
- 外层依赖内层 ✅
- 内层依赖外层 ❌
- 依赖接口，不依赖实现 ✅
```

## 函数设计

### 参数对象

```typescript
// ❌ 参数过多
function createUser(name, email, age, role, department, manager) {}

// ✅ 使用参数对象
function createUser(params: CreateUserParams) {}
```

### 早返回

```typescript
// ❌ 嵌套过深
if (a) {
  if (b) {
    if (c) {
      // ...
    }
  }
}

// ✅ 早返回
if (!a) return;
if (!b) return;
if (!c) return;
// ...
```

## 可测试性

### 依赖注入

```typescript
// ❌ 硬编码依赖
class UserService {
  private db = new Database();
  private mailer = new EmailService();
}

// ✅ 依赖注入
class UserService {
  constructor(
    private db: IDatabase,
    private mailer: IEmailService
  ) {}
}
```

### 纯函数优先

```typescript
// ❌ 有副作用，难测试
function calculateTotal(items) {
  const total = items.reduce((sum, item) => sum + item.price, 0);
  console.log(`Total: ${total}`);  // 副作用
  analytics.track('calculate');     // 副作用
  return total;
}

// ✅ 纯函数，易测试
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

### 边界分离

```typescript
// ❌ 业务逻辑混合 IO
async function processOrder(orderId) {
  const order = await db.findOrder(orderId);  // IO
  if (order.total > 1000) {                   // 业务逻辑
    order.discount = 0.1;
  }
  await db.save(order);                       // IO
  await email.send(order.user, 'confirmed');  // IO
}

// ✅ 分离业务逻辑
function applyDiscount(order) {  // 纯业务逻辑，可测试
  if (order.total > 1000) {
    return { ...order, discount: 0.1 };
  }
  return order;
}

async function processOrder(orderId) {
  const order = await db.findOrder(orderId);
  const updated = applyDiscount(order);
  await db.save(updated);
  await email.send(order.user, 'confirmed');
}
```

## 避免过度设计

### YAGNI

```typescript
// ❌ 过度设计：为假设需求添加配置
const config = {
  maxRetries: 3,
  retryDelay: 1000,
  enableCache: true,
  cacheExpiry: 3600,
  enableRateLimit: false,  // 从未使用
  rateLimitWindow: 60000,  // 从未使用
  enableMetrics: false,    // 从未使用
  metricsEndpoint: '',     // 从未使用
};

// ✅ 只添加当前需要的配置
const config = {
  maxRetries: 3,
  retryDelay: 1000,
  cacheExpiry: 3600,
};
```

### 抽象时机

```
❌ 过早抽象：
- 只有一个实现就创建接口
- 只有一处使用就提取函数
- 只有两个相似场景就创建基类

✅ 适时抽象（Rule of Three）：
- 3 个以上实现时考虑接口
- 第 3 处重复即提取（>3 处未提取 = Blocker，见主文件阈值表）
- 3 个以上相似场景时考虑基类
```

### 简单方案优先

```typescript
// ❌ 过度设计：简单场景用复杂模式
class UserFactory {
  createAdmin() { return new AdminUser(); }
  createMember() { return new MemberUser(); }
  createGuest() { return new GuestUser(); }
}

// ✅ 简单场景用简单方案
function createUser(role: 'admin' | 'member' | 'guest') {
  return { role, permissions: getPermissions(role) };
}
```
