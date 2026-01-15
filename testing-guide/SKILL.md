---
name: testing-guide
description: Opinionated constraints for writing effective tests. Guide unit tests, integration tests, and E2E tests with quality metrics beyond coverage. Use when users write tests, review test code, or need testing strategy. Triggers on keywords like "test", "testing", "单元测试", "集成测试", "E2E", "测试质量", "coverage", "断言".
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
---

# Testing Guide

编写高质量测试的约束规范，确保测试真正验证行为而非仅仅覆盖代码。

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese

## Trigger Conditions

- 用户正在编写测试代码
- 用户需要测试策略指导
- 用户提到测试覆盖率、断言、变异测试
- Code Review 中涉及测试代码

## 核心理念

### 测试的目的

```
测试的目的不是"覆盖代码"，而是"验证行为"。

❌ 错误理解：让每一行代码都被执行过
✅ 正确理解：确保系统按照需求正确工作
```

### 测试质量金字塔

```
┌─────────────────────────────────────────────────────────────┐
│                    测试质量金字塔                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 3: 测试有效性（最高标准）                              │
│    - 变异得分 (Mutation Score) ≥ 80%                        │
│    - 需求-测试追溯覆盖 100%                                  │
│    - 测试能捕获真实缺陷                                      │
│                                                             │
│  Level 2: 断言质量（核心要求）                                │
│    - 禁止弱断言                                              │
│    - 每个测试 ≥1 个具体断言                                  │
│    - 测试名称描述预期行为                                     │
│    - 断言验证行为而非实现                                     │
│                                                             │
│  Level 1: 代码覆盖（基础门槛）                                │
│    - 行覆盖率 ≥ 80%                                          │
│    - 分支覆盖率 ≥ 80%                                        │
│    - ⚠️ 这只是必要条件，不是充分条件                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# Part 1: 单元测试

## 单元测试的依据

单元测试的依据**不是代码本身**，而是：

| 优先级 | 依据来源 | 测试类型 | 验证内容 |
|--------|----------|----------|----------|
| 1 | **需求/验收标准** | 功能测试 | 业务规则是否正确 |
| 2 | **接口契约** | 契约测试 | 输入输出是否符合约定 |
| 3 | **边界条件** | 边界测试 | 极端情况是否处理 |
| 4 | **错误场景** | 异常测试 | 错误是否正确处理 |
| 5 | 代码路径 | 覆盖率 | 代码是否被执行 |

### 从需求推导测试

```
需求: "用户密码必须至少8位，包含大小写字母和数字"
  │
  ▼
测试用例推导（不是看代码写测试）:
  ├── [正向] 8位有效密码（含大小写和数字）→ 通过
  ├── [边界] 恰好8位有效密码 → 通过
  ├── [边界] 7位密码 → 拒绝
  ├── [规则] 无大写字母 → 拒绝
  ├── [规则] 无小写字母 → 拒绝
  ├── [规则] 无数字 → 拒绝
  └── [边界] 空密码 → 拒绝
```

### 从接口契约推导测试

```typescript
// 接口契约
interface UserService {
  /**
   * 根据ID获取用户
   * @param id - 用户ID，必须为正整数
   * @returns 用户对象，如果不存在返回 null
   * @throws InvalidIdError - 当 id 不是正整数时
   */
  getUser(id: number): User | null;
}

// 从契约推导的测试
describe('UserService.getUser', () => {
  it('应该返回存在的用户', () => {});           // 正常返回
  it('应该返回 null 当用户不存在时', () => {}); // null 返回
  it('应该抛出 InvalidIdError 当 id <= 0', () => {}); // 异常
  it('应该抛出 InvalidIdError 当 id 不是整数', () => {}); // 异常
});
```

## 断言质量

### 禁止弱断言

```typescript
// ❌ 弱断言：几乎不验证任何东西
expect(result).toBeDefined();
expect(result).toBeTruthy();
expect(result).not.toBeNull();
expect(typeof result).toBe('object');

// ✅ 强断言：验证具体的值和行为
expect(result.status).toBe('success');
expect(result.total).toBe(150);
expect(result.items).toHaveLength(3);
expect(result.user.email).toBe('test@example.com');
```

### 断言分类

| 断言类型 | 强度 | 使用场景 | 示例 |
|----------|------|----------|------|
| **值相等** | 强 | 验证具体返回值 | `toBe(100)`, `toEqual({...})` |
| **结构验证** | 强 | 验证对象结构 | `toMatchObject({...})` |
| **集合验证** | 强 | 验证数组内容 | `toContain()`, `toHaveLength()` |
| **异常验证** | 强 | 验证错误抛出 | `toThrow(ErrorType)` |
| **类型验证** | 弱 | 仅作为辅助 | `toBeDefined()`, `toBeInstanceOf()` |
| **存在性验证** | 弱 | ⚠️ 避免单独使用 | `toBeTruthy()`, `not.toBeNull()` |

### 测试命名规范

```typescript
// ❌ 不好的命名：不清楚测试什么
test('getUser', () => {});
test('test1', () => {});
test('should work', () => {});

// ✅ 好的命名：描述预期行为
test('getUser 应该返回用户信息当用户存在时', () => {});
test('getUser 应该返回 null 当用户不存在时', () => {});
test('getUser 应该抛出 InvalidIdError 当 ID 为负数时', () => {});

// 推荐格式
// [被测方法] 应该 [预期行为] 当 [条件]
// [Subject] should [expected behavior] when [condition]
```

## 测试结构

### AAA 模式

```typescript
test('calculateDiscount 应该返回10%折扣当订单金额超过1000时', () => {
  // Arrange - 准备测试数据
  const order = {
    items: [{ price: 500 }, { price: 600 }],
    total: 1100,
  };

  // Act - 执行被测行为
  const result = calculateDiscount(order);

  // Assert - 验证结果
  expect(result.discountRate).toBe(0.1);
  expect(result.discountAmount).toBe(110);
  expect(result.finalTotal).toBe(990);
});
```

### 单一职责

```typescript
// ❌ 一个测试验证多个行为
test('用户服务', () => {
  const user = createUser({ name: 'test' });
  expect(user.id).toBeDefined();

  const updated = updateUser(user.id, { name: 'updated' });
  expect(updated.name).toBe('updated');

  deleteUser(user.id);
  expect(getUser(user.id)).toBeNull();
});

// ✅ 每个测试只验证一个行为
test('createUser 应该创建用户并返回ID', () => {});
test('updateUser 应该更新用户名称', () => {});
test('deleteUser 应该删除用户', () => {});
```

## Mock 策略

### Mock 原则

```
只 Mock 你不拥有的东西:
✅ 外部 API
✅ 数据库
✅ 文件系统
✅ 网络请求
✅ 第三方服务

不要 Mock:
❌ 被测模块的内部实现
❌ 纯函数
❌ 你自己的业务逻辑
```

### Mock 质量检查

```typescript
// ❌ Mock 返回值但不验证调用
jest.mock('./api', () => ({
  fetchUser: jest.fn().mockResolvedValue({ id: 1, name: 'test' }),
}));

test('loadUser', async () => {
  const result = await loadUser(1);
  expect(result.name).toBe('test');
  // 没有验证 fetchUser 是否被正确调用！
});

// ✅ Mock 并验证调用参数
test('loadUser 应该用正确的ID调用API', async () => {
  const mockFetch = jest.fn().mockResolvedValue({ id: 1, name: 'test' });

  const result = await loadUser(1, { fetchUser: mockFetch });

  expect(mockFetch).toHaveBeenCalledWith(1);  // 验证调用
  expect(mockFetch).toHaveBeenCalledTimes(1); // 验证次数
  expect(result.name).toBe('test');
});
```

---

# Part 2: 集成测试

## 集成测试的关注点

集成测试验证**模块之间的协作**，不是验证单个模块的逻辑。

| 关注点 | 验证内容 | 不验证 |
|--------|----------|--------|
| **数据流** | 数据在模块间正确传递 | 单个模块内部逻辑 |
| **接口契约** | 模块间调用参数和返回值符合约定 | 参数的详细验证 |
| **错误传播** | 错误正确地跨模块传播 | 错误的详细处理 |
| **事务边界** | 数据库事务正确提交/回滚 | 单条SQL正确性 |

## 集成测试策略

### 边界定义

```
系统边界图:

┌─────────────────────────────────────────────────────────┐
│                    Application                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │ Handler │───▶│ Service │───▶│  Repo   │             │
│  └─────────┘    └─────────┘    └─────────┘             │
│                      │              │                   │
│                      ▼              ▼                   │
│              ┌─────────────┐ ┌─────────────┐           │
│              │ External API│ │  Database   │           │
│              └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────┘

集成测试边界:
- Handler → Service → Repo（真实调用，Mock 数据库）
- Service → External API（Mock API，验证请求格式）
```

### 测试数据库策略

| 策略 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **内存数据库** | 快速测试 | 速度快、无状态 | 可能与生产不一致 |
| **Docker 容器** | CI 环境 | 与生产一致 | 启动较慢 |
| **测试专用库** | 本地开发 | 真实环境 | 需要清理数据 |
| **事务回滚** | 任何场景 | 自动清理 | 无法测试事务本身 |

```typescript
// 推荐：事务回滚模式
describe('UserRepository', () => {
  let transaction: Transaction;

  beforeEach(async () => {
    transaction = await db.beginTransaction();
  });

  afterEach(async () => {
    await transaction.rollback();  // 自动清理
  });

  test('createUser 应该插入数据库记录', async () => {
    const repo = new UserRepository(transaction);
    const user = await repo.create({ name: 'test' });

    const found = await repo.findById(user.id);
    expect(found.name).toBe('test');
  });
});
```

## 契约测试

### 消费者驱动契约

```typescript
// Consumer 定义期望的契约
const userApiContract = {
  request: {
    method: 'GET',
    path: '/users/1',
  },
  response: {
    status: 200,
    body: {
      id: 1,
      name: Matchers.string(),
      email: Matchers.email(),
      createdAt: Matchers.iso8601DateTime(),
    },
  },
};

// Provider 验证是否满足契约
describe('User API Contract', () => {
  it('GET /users/:id 应该符合契约', async () => {
    const response = await api.get('/users/1');
    expect(response).toMatchContract(userApiContract);
  });
});
```

---

# Part 3: E2E 测试

## E2E 测试的关注点

E2E 测试验证**用户场景**，从用户视角验证系统行为。

```
E2E 测试 = 用户能完成他们的目标

关注:
✅ 用户能否完成核心流程
✅ 页面交互是否正确
✅ 数据是否正确保存和展示
✅ 错误提示是否清晰

不关注:
❌ 内部实现细节
❌ 单个组件的边界条件
❌ API 的详细响应结构
```

## E2E 测试策略

### 场景优先级

| 优先级 | 场景类型 | 覆盖要求 | 示例 |
|--------|----------|----------|------|
| **P0** | 核心业务流程 | 100% | 注册、登录、支付、核心功能 |
| **P1** | 重要功能 | ≥80% | 搜索、筛选、设置 |
| **P2** | 辅助功能 | 可选 | 帮助页面、偏好设置 |

### 测试粒度

```typescript
// ❌ 粒度太细：像单元测试
test('登录按钮应该有正确的文本', () => {
  expect(page.locator('button')).toHaveText('登录');
});

// ❌ 粒度太粗：一个测试做太多事
test('用户流程', async () => {
  await register();
  await login();
  await createOrder();
  await pay();
  await viewHistory();
});

// ✅ 合适的粒度：一个用户目标
test('新用户应该能够完成注册流程', async () => {
  await page.goto('/register');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'SecurePass123');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('.welcome')).toContainText('欢迎');
});
```

### 测试可靠性

```typescript
// ❌ 不可靠：硬编码等待时间
await page.click('button');
await page.waitForTimeout(3000);  // 可能太短或太长

// ✅ 可靠：等待具体条件
await page.click('button');
await page.waitForSelector('.success-message');
await expect(page.locator('.success-message')).toBeVisible();

// ✅ 更好：使用自动等待
await page.click('button');
await expect(page.locator('.result')).toHaveText('完成', {
  timeout: 10000,  // 最大等待时间
});
```

### 测试数据策略

```
E2E 测试数据原则:

1. 测试数据独立
   - 每个测试使用唯一数据
   - 不依赖其他测试创建的数据

2. 测试后清理
   - 使用 API 清理测试数据
   - 或使用专门的测试账号

3. 避免测试间依赖
   - 测试可以独立运行
   - 测试顺序不影响结果
```

---

# Part 4: 变异测试

## 什么是变异测试

变异测试通过**自动修改代码**来检验测试的有效性。

```
原理:
1. 自动生成代码"变异体"（修改后的代码）
2. 对每个变异体运行测试
3. 如果测试通过 → 测试无效（未能发现bug）
4. 如果测试失败 → 测试有效（成功捕获变异）

变异得分 = 被杀死的变异体 / 总变异体 × 100%
```

## 变异操作类型

| 变异类型 | 原代码 | 变异后 | 检测能力 |
|----------|--------|--------|----------|
| **边界变异** | `a > b` | `a >= b` | 边界条件测试 |
| **操作符变异** | `a + b` | `a - b` | 计算逻辑测试 |
| **常量变异** | `return 0` | `return 1` | 返回值测试 |
| **否定变异** | `if (cond)` | `if (!cond)` | 条件逻辑测试 |
| **删除变异** | `func()` | `// removed` | 副作用测试 |

## 变异测试工具

| 语言 | 工具 | 安装 |
|------|------|------|
| JavaScript/TypeScript | **Stryker** | `npm i -D @stryker-mutator/core` |
| Python | **mutmut** | `pip install mutmut` |
| Java | **PIT** | Maven/Gradle 插件 |
| C# (.NET) | **Stryker.NET** | `dotnet tool install dotnet-stryker` |
| C/C++ | **Mull** | `brew install mull-project/mull/mull-runner` |
| Swift | **Muter** | `brew install muter-mutation-testing/muter/muter` |
| Go | **go-mutesting** | `go install github.com/zimmski/go-mutesting/cmd/go-mutesting@latest` |
| Rust | **cargo-mutants** | `cargo install cargo-mutants` |

> 详细配置见 [templates/mutation-testing.md](templates/mutation-testing.md)

### 工具配置

> 详细配置模板见 [templates/mutation-testing.md](templates/mutation-testing.md)

```bash
# JavaScript/TypeScript (Stryker)
npx stryker run

# Python (mutmut)
mutmut run

# Java (PIT)
mvn org.pitest:pitest-maven:mutationCoverage

# Go (go-mutesting)
go-mutesting ./...

# C# (Stryker.NET)
dotnet stryker

# Rust (cargo-mutants)
cargo mutants
```

## 变异测试的价值

```
场景：100% 代码覆盖率但测试无效

function add(a, b) {
  return a + b;
}

// 100% 覆盖率的无效测试
test('add', () => {
  add(1, 2);  // 没有断言！
});

变异测试结果：
- 变异: return a - b  → 测试通过 → 变异体存活 ❌
- 变异: return a * b  → 测试通过 → 变异体存活 ❌
- 变异: return 0      → 测试通过 → 变异体存活 ❌

变异得分: 0%（覆盖率 100%！）
```

---

# Part 5: 需求追溯

## 追溯矩阵

```markdown
# 需求-测试追溯矩阵

| 需求ID | 需求描述 | 单元测试 | 集成测试 | E2E测试 | 覆盖状态 |
|--------|----------|----------|----------|---------|----------|
| REQ-001 | 用户登录 | UT-001~003 | IT-001 | E2E-001 | ✅ 完整 |
| REQ-002 | 密码验证 | UT-004~008 | - | E2E-002 | ✅ 完整 |
| REQ-003 | 记住登录 | UT-009 | IT-002 | - | ⚠️ 缺E2E |
| REQ-004 | 登录失败锁定 | - | - | - | ❌ 未覆盖 |
```

## 自动化追溯

```typescript
/**
 * @requirement REQ-001 用户登录
 * @acceptance AC-001 有效凭证应该登录成功
 */
test('login 应该返回 token 当凭证有效时', () => {
  // ...
});

/**
 * @requirement REQ-002 密码验证
 * @acceptance AC-002 密码少于8位应该拒绝
 */
test('validatePassword 应该返回 false 当密码少于8位时', () => {
  // ...
});
```

```bash
# 生成追溯报告
grep -r "@requirement" tests/ | sort | uniq
```

---

# Part 6: 自动化质量检查

## CI 集成检查点

```yaml
# .github/workflows/test-quality.yml
name: Test Quality

on: [push, pull_request]

jobs:
  test-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Level 1: 覆盖率检查
      - name: Run Tests with Coverage
        run: npm test -- --coverage

      - name: Check Coverage Threshold
        run: |
          LINES=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          BRANCHES=$(cat coverage/coverage-summary.json | jq '.total.branches.pct')
          if (( $(echo "$LINES < 80" | bc -l) )); then
            echo "Line coverage $LINES% < 80%"
            exit 1
          fi
          if (( $(echo "$BRANCHES < 80" | bc -l) )); then
            echo "Branch coverage $BRANCHES% < 80%"
            exit 1
          fi

      # Level 2: 断言质量检查（可选）
      - name: Check Assertion Quality
        run: |
          # 检查是否有无断言的测试
          EMPTY_TESTS=$(grep -r "test\|it(" tests/ | grep -v "expect\|assert" | wc -l)
          if [ "$EMPTY_TESTS" -gt 0 ]; then
            echo "Found $EMPTY_TESTS tests without assertions"
            exit 1
          fi

      # Level 3: 变异测试（可选，耗时较长）
      - name: Mutation Testing
        run: npx stryker run
        if: github.event_name == 'pull_request'
```

## 质量门禁

| 检查级别 | 检查项 | 门禁要求 | 强制/建议 |
|----------|--------|----------|-----------|
| **L1** | 行覆盖率 | ≥ 80% | 强制 |
| **L1** | 分支覆盖率 | ≥ 80% | 强制 |
| **L2** | 无弱断言 | 0 个 | 建议 |
| **L2** | 测试命名规范 | 100% | 建议 |
| **L3** | 变异得分 | ≥ 60% | 建议 |
| **L3** | 需求追溯 | 100% | 建议 |

---

# Part 7: 测试代码 Review

## Review 检查清单

### 测试有效性

- [ ] 测试是否验证行为而非实现？
- [ ] 每个测试是否有明确的断言？
- [ ] 断言是否足够具体（不是弱断言）？
- [ ] 测试名称是否描述预期行为？

### 测试独立性

- [ ] 测试是否可以独立运行？
- [ ] 测试之间是否有数据依赖？
- [ ] 测试顺序是否影响结果？
- [ ] 测试数据是否在测试后清理？

### Mock 质量

- [ ] Mock 是否只用于外部依赖？
- [ ] Mock 是否验证了调用参数？
- [ ] Mock 返回值是否合理？
- [ ] 是否避免了过度 Mock？

### 可维护性

- [ ] 测试代码是否遵循 DRY 原则？
- [ ] 测试数据是否使用工厂函数？
- [ ] 测试结构是否清晰（AAA 模式）？
- [ ] 测试失败时错误信息是否清晰？

## Review 反馈示例

```
[Blocker] 测试缺少断言
位置: user.test.ts:45
当前: test('createUser', () => { createUser({...}); });
建议: 添加断言验证返回值: expect(result.id).toBeDefined();

[Suggestion] 使用弱断言
位置: order.test.ts:78
当前: expect(result).toBeTruthy();
建议: 使用更具体的断言: expect(result.status).toBe('success');

[Question] 为什么 Mock 内部函数？
位置: payment.test.ts:120
问题: calculateFee 是 PaymentService 的内部函数，为什么要 Mock？
建议: 只 Mock 外部依赖，让内部逻辑真实执行
```

---

## Constraints

### 单元测试约束

- [ ] **每个测试必须有 ≥1 个具体断言**
- [ ] **禁止使用弱断言作为唯一断言**（toBeDefined, toBeTruthy, not.toBeNull）
- [ ] **测试名称必须描述预期行为**
- [ ] **测试依据来自需求，不是来自代码**
- [ ] 只 Mock 外部依赖，不 Mock 内部实现
- [ ] 每个测试只验证一个行为

### 覆盖率约束

- [ ] **行覆盖率 ≥ 80%**
- [ ] **分支覆盖率 ≥ 80%**
- [ ] 覆盖率是必要条件，不是充分条件
- [ ] 新代码覆盖率不得低于现有水平

### 变异测试约束（推荐）

- [ ] 变异得分 ≥ 60%（建议 ≥ 80%）
- [ ] 核心业务逻辑变异得分 ≥ 80%
- [ ] PR 中新增代码应通过变异测试

### 集成测试约束

- [ ] 必须验证模块间数据流
- [ ] 必须验证接口契约
- [ ] 测试数据必须独立，不依赖其他测试

### E2E 测试约束

- [ ] **P0 场景必须 100% 覆盖**
- [ ] 使用显式等待，禁止硬编码延时
- [ ] 测试必须可独立运行
- [ ] 测试数据必须独立创建和清理

### 需求追溯约束

- [ ] 每个需求必须有对应测试
- [ ] 测试代码应标注对应需求ID
- [ ] 维护需求-测试追溯矩阵

---

## 与其他 Skills 的协作

| 场景 | 协作 Skill | 说明 |
|------|------------|------|
| 测试计划生成 | `/devdocs-test-plan` | 生成测试策略文档 |
| 代码可测试性 | `/code-quality` | 确保代码可测试（依赖注入、纯函数） |
| 重构前测试 | `/refactor` | 重构前确保测试覆盖 |
| UI 测试 | `/ui-skills` | E2E 测试关注可访问性 |

---

## 模板资源

### 通用模板

| 模板 | 说明 | 链接 |
|------|------|------|
| **变异测试配置** | 8种语言的变异测试工具配置 | [mutation-testing.md](templates/mutation-testing.md) |
| **需求追溯矩阵** | 需求-测试追溯模板和自动化脚本 | [traceability-matrix.md](templates/traceability-matrix.md) |
| **CI 集成配置** | GitHub Actions/GitLab CI 完整配置 | [ci-integration.md](templates/ci-integration.md) |
| **测试代码示例** | 单元/集成/E2E 测试示例代码 | [test-examples.md](templates/test-examples.md) |

### 语言/框架最佳实践

| 语言 | 框架 | 链接 |
|------|------|------|
| **JavaScript/TypeScript** | Jest, Vitest | [jest-vitest-best-practices.md](templates/jest-vitest-best-practices.md) |
| **Python** | pytest | [pytest-best-practices.md](templates/pytest-best-practices.md) |
| **Java** | JUnit 5, AssertJ, Mockito | [junit5-best-practices.md](templates/junit5-best-practices.md) |
| **C# / .NET** | xUnit, NUnit, FluentAssertions | [xunit-best-practices.md](templates/xunit-best-practices.md) |
| **Go** | testing, testify | [go-testing-best-practices.md](templates/go-testing-best-practices.md) |
| **Rust** | cargo test, mockall | [rust-testing-best-practices.md](templates/rust-testing-best-practices.md) |
| **Swift** | XCTest | [xctest-best-practices.md](templates/xctest-best-practices.md) |
| **C/C++** | Google Test, Catch2 | [googletest-best-practices.md](templates/googletest-best-practices.md) |

---

## Quick Reference

### 测试命名模板

```
[被测方法] 应该 [预期行为] 当 [条件]

示例:
- calculateDiscount 应该返回10%折扣当订单超过1000元时
- validateEmail 应该返回false当邮箱格式无效时
- getUser 应该抛出NotFoundError当用户不存在时
```

### 测试结构模板

```typescript
describe('模块名', () => {
  describe('方法名', () => {
    // 正常路径
    it('应该 [预期行为] 当 [正常条件]', () => {
      // Arrange
      // Act
      // Assert (具体断言)
    });

    // 边界条件
    it('应该 [预期行为] 当 [边界条件]', () => {});

    // 错误路径
    it('应该抛出 [错误] 当 [异常条件]', () => {});
  });
});
```

### 覆盖率命令

```bash
# Jest
npm test -- --coverage

# Vitest
npx vitest --coverage

# pytest
pytest --cov=src --cov-report=html

# Go
go test -cover ./...
```

### 变异测试命令

```bash
# Stryker (JS/TS)
npx stryker run

# mutmut (Python)
mutmut run && mutmut results

# PIT (Java)
mvn org.pitest:pitest-maven:mutationCoverage

# Stryker.NET (C#)
dotnet stryker

# Mull (C/C++)
mull-runner ./your_test_binary

# Muter (Swift)
muter run

# go-mutesting (Go)
go-mutesting ./...

# cargo-mutants (Rust)
cargo mutants
```

> 详细配置见 [templates/mutation-testing.md](templates/mutation-testing.md)
