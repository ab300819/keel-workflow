# 骨架代码示例

自顶向下开发模式中的接口骨架和测试骨架示例。

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

## 完整实现示例（Step 3-4）

### 接口实现

```typescript
// src/services/user.service.ts

/**
 * 用户服务
 * @requirement F-001 - 用户注册
 */
export class UserService {
  constructor(private readonly userRepo: IUserRepository) {}

  /**
   * 创建用户
   * @satisfies AC-001 - 邮箱格式校验
   * @satisfies AC-002 - 密码强度校验
   * @satisfies AC-003 - 用户名唯一性
   */
  async createUser(dto: CreateUserDTO): Promise<User> {
    // AC-001: 邮箱格式校验
    if (!this.isValidEmail(dto.email)) {
      throw new ValidationError('Invalid email format');
    }

    // AC-002: 密码强度校验
    if (!this.isStrongPassword(dto.password)) {
      throw new ValidationError('Password too weak');
    }

    // AC-003: 用户名唯一性
    const existing = await this.userRepo.findByUsername(dto.username);
    if (existing) {
      throw new ConflictError('Username already exists');
    }

    return this.userRepo.create(dto);
  }

  private isValidEmail(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  private isStrongPassword(password: string): boolean {
    return password.length >= 8 && /[A-Z]/.test(password) && /\d/.test(password);
  }
}
```

### 测试实现

```typescript
// tests/user.service.test.ts

describe('UserService', () => {
  let service: UserService;
  let mockRepo: jest.Mocked<IUserRepository>;

  beforeEach(() => {
    mockRepo = {
      findByUsername: jest.fn(),
      create: jest.fn(),
    };
    service = new UserService(mockRepo);
  });

  /**
   * @verifies AC-001 - 邮箱格式校验
   * @testcase UT-001
   */
  test('createUser 应该拒绝无效邮箱格式', async () => {
    // Arrange
    const dto = { email: 'invalid', password: 'Strong1234', username: 'test' };

    // Act & Assert
    await expect(service.createUser(dto)).rejects.toThrow(ValidationError);
    await expect(service.createUser(dto)).rejects.toThrow('Invalid email format');
  });

  /**
   * @verifies AC-002 - 密码强度校验
   * @testcase UT-002
   */
  test('createUser 应该拒绝弱密码', async () => {
    // Arrange
    const dto = { email: 'test@example.com', password: 'weak', username: 'test' };

    // Act & Assert
    await expect(service.createUser(dto)).rejects.toThrow(ValidationError);
    await expect(service.createUser(dto)).rejects.toThrow('Password too weak');
  });

  /**
   * @verifies AC-003 - 用户名唯一性
   * @testcase UT-003
   */
  test('createUser 应该拒绝重复用户名', async () => {
    // Arrange
    const dto = { email: 'test@example.com', password: 'Strong1234', username: 'existing' };
    mockRepo.findByUsername.mockResolvedValue({ id: '1', username: 'existing' });

    // Act & Assert
    await expect(service.createUser(dto)).rejects.toThrow(ConflictError);
  });
});
```

## 骨架生成约束

- [ ] **接口骨架必须包含完整签名**（参数、返回值、泛型）
- [ ] **接口骨架必须添加追溯标注**
- [ ] **未实现方法必须抛出 Error 并注明任务编号**
- [ ] **测试骨架必须使用 skip/todo 标记**
- [ ] **测试骨架必须添加 @verifies 和 @testcase 标注**
- [ ] **测试骨架必须包含 AAA 结构注释提示**
