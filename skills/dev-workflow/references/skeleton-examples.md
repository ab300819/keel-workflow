# 骨架代码示例

自顶向下开发模式中的接口骨架和测试骨架示例。

> 📝 注释风格遵循 [`/code-quality` 注释规范](../../code-quality/SKILL.md#注释规范)：代码块只展示期望 Agent 模仿的最终风格，流程说明写在 prose、不进代码注释。

## 接口骨架示例（Step 1）

```typescript
// src/services/user.service.ts

/**
 * 用户服务
 * @requirement F-001 - 用户注册
 */
export class UserService {
  /**
   * 创建用户
   * @satisfies AC-001 - 邮箱格式校验
   * @satisfies AC-002 - 密码强度校验
   * @satisfies AC-003 - 用户名唯一性
   */
  async createUser(dto: CreateUserDTO): Promise<User> {
    throw new Error('Not implemented: T-02');
  }

  /**
   * 获取用户
   * @satisfies AC-004 - 用户查询
   */
  async getUser(id: string): Promise<User | null> {
    throw new Error('Not implemented: T-03');
  }
}
```

## 测试骨架示例（Step 2）

```typescript
// tests/user.service.test.ts

describe('UserService', () => {
  /**
   * @verifies AC-001 - 邮箱格式校验
   * @testcase UT-001
   */
  test.skip('createUser 应该拒绝无效邮箱格式', () => {
    // TODO: 实现测试
    // Arrange: 准备无效邮箱
    // Act: 调用 createUser
    // Assert: 验证抛出 ValidationError
  });

  /**
   * @verifies AC-002 - 密码强度校验
   * @testcase UT-002
   */
  test.skip('createUser 应该拒绝弱密码', () => {
    // TODO: 实现测试
  });

  /**
   * @verifies AC-003 - 用户名唯一性
   * @testcase UT-003
   */
  test.skip('createUser 应该拒绝重复用户名', () => {
    // TODO: 实现测试
  });
});
```

## 骨架填充示意（Step 3-4 最小形式）

### 接口实现（最小骨架填充示意）

Impl Agent 在 S6 以最小实现让测试转绿——业务逻辑/边界/异常由测试断言驱动，不写入注释：

```typescript
export class CreateOrderService {
  async execute(input: CreateOrderInput): Promise<Order> {
    throw new Error('TODO(T-XX): replace with minimal implementation');
  }
}
```

### 测试骨架填充（Test Agent 产出）

skip/todo 标记仅限 S3 骨架阶段，S4 写完断言后必须移除：

```typescript
describe('CreateOrderService', () => {
  it.todo('should create order with valid input (AC-001)');
  it.todo('should reject input with missing customer (AC-002)');
});
```

## 行为契约 → Test Agent 断言示例

展示 Test Agent 如何从系统设计的行为契约推导完整测试断言（无需看到任何实现代码）。

### 输入：行为契约（来自 02-system-design.md Section 5）

| 类别 | 条件 | 结果 |
|------|------|------|
| 前置条件 | `dto.email` 符合邮箱格式 | — |
| 前置条件 | `dto.password` 长度>=8 且含大写和数字 | — |
| 后置条件 | 返回值包含系统生成的 `id` | `User.id` 非空 |
| 后置条件 | 返回值 `email` 与输入一致 | `User.email === dto.email` |
| 错误契约 | `dto.email` 格式无效 | `ValidationError(EMAIL_INVALID)` |
| 错误契约 | `dto.password` 不满足强度要求 | `ValidationError(PASSWORD_WEAK)` |
| 错误契约 | `dto.email` 已存在 | `ConflictError(EMAIL_DUPLICATE)` |

### 输入：测试用例（来自 03-test-unit.md）

| 编号 | AC | 场景 | 输入 | 预期 | 优先级 |
|------|-------|------|------|------|--------|
| UT-001 | AC-001 | 无效邮箱 | `"invalid"` | `ValidationError(EMAIL_INVALID)` | P0 |
| UT-004 | AC-001 | 有效邮箱创建成功 | `"test@example.com"` | `User.id` 非空 | P0 |

### 输出：Test Agent 产出的测试代码

Test Agent 产出，Impl Agent 不可修改。注意：断言来源（UT 编号、行为契约条目）不写进注释——测试名 + 断言本身表达预期，AAA 仅用纯占位：

```typescript
// tests/user.service.test.ts

describe('UserService.createUser', () => {
  /**
   * @verifies AC-001 - 邮箱格式校验
   * @testcase UT-001
   */
  test('应拒绝无效邮箱格式', async () => {
    // Arrange
    const dto = { email: 'invalid', password: 'Strong1234', username: 'test' };

    // Act & Assert
    await expect(service.createUser(dto)).rejects.toThrow(ValidationError);
  });

  /**
   * @verifies AC-001 - 邮箱格式校验（成功路径）
   * @testcase UT-004
   */
  test('有效邮箱应创建成功并返回 User', async () => {
    // Arrange
    const dto = { email: 'test@example.com', password: 'Strong1234', username: 'test' };

    // Act
    const user = await service.createUser(dto);

    // Assert
    expect(user.id).toBeTruthy();
    expect(user.email).toBe(dto.email);
  });
});
```

> **关键**：Test Agent 的断言值和异常类型全部来自行为契约和测试用例文档，不依赖任何实现细节。Impl Agent 拿到这些测试后，只需让实现通过即可。

## 骨架生成约束

- [ ] **接口骨架必须包含完整签名**（参数、返回值、泛型）
- [ ] **接口骨架必须添加追溯标注**
- [ ] **未实现方法必须抛出 Error 并注明任务编号**
- [ ] **测试骨架必须使用 skip/todo 标记**
- [ ] **测试骨架必须添加 @verifies 和 @testcase 标注**
- [ ] **测试骨架 S3 可含纯 AAA 占位**（`// Arrange` / `// Act` / `// Assert`，不带来源）；**S4 后不得保留来源记录式注释**
