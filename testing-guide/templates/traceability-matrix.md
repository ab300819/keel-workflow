# 需求-测试追溯矩阵模板

## 矩阵格式

```markdown
# 需求-测试追溯矩阵

## 概览

| 指标 | 值 |
|------|-----|
| 总需求数 | XX |
| 已覆盖需求 | XX |
| 覆盖率 | XX% |
| 最后更新 | YYYY-MM-DD |

## 追溯矩阵

| 需求ID | 需求描述 | 优先级 | 单元测试 | 集成测试 | E2E测试 | 状态 |
|--------|----------|--------|----------|----------|---------|------|
| REQ-001 | 用户注册 | P0 | UT-001~005 | IT-001 | E2E-001 | ✅ |
| REQ-002 | 用户登录 | P0 | UT-006~010 | IT-002 | E2E-002 | ✅ |
| REQ-003 | 密码重置 | P1 | UT-011~015 | IT-003 | - | ⚠️ |
| REQ-004 | 账号锁定 | P1 | - | - | - | ❌ |

### 状态说明

- ✅ 完整覆盖：所有测试层级都有覆盖
- ⚠️ 部分覆盖：缺少某些层级的测试
- ❌ 未覆盖：没有任何测试覆盖

## 详细追溯

### REQ-001: 用户注册

**需求描述**: 用户可以使用邮箱注册账号

**验收标准**:
- AC-001: 有效邮箱可以注册成功
- AC-002: 已存在的邮箱无法重复注册
- AC-003: 无效邮箱格式应该被拒绝
- AC-004: 密码必须符合安全要求

**测试覆盖**:

| 验收标准 | 测试ID | 测试描述 | 测试层级 |
|----------|--------|----------|----------|
| AC-001 | UT-001 | register 应该创建用户当邮箱有效 | 单元 |
| AC-001 | IT-001 | 注册流程应该将用户保存到数据库 | 集成 |
| AC-001 | E2E-001 | 新用户应该能完成注册流程 | E2E |
| AC-002 | UT-002 | register 应该抛出错误当邮箱已存在 | 单元 |
| AC-003 | UT-003 | validateEmail 应该返回false当格式无效 | 单元 |
| AC-004 | UT-004 | validatePassword 应该检查密码强度 | 单元 |

### REQ-002: 用户登录

...（同样格式）
```

## 测试代码标注

### 方式一：JSDoc 注释

```typescript
/**
 * @requirement REQ-001
 * @acceptance AC-001, AC-002
 */
describe('UserService.register', () => {
  /**
   * @testId UT-001
   * @acceptance AC-001
   */
  it('应该创建用户当邮箱有效', () => {
    // ...
  });

  /**
   * @testId UT-002
   * @acceptance AC-002
   */
  it('应该抛出错误当邮箱已存在', () => {
    // ...
  });
});
```

### 方式二：测试命名约定

```typescript
describe('REQ-001: 用户注册', () => {
  describe('AC-001: 有效邮箱注册', () => {
    it('UT-001: register 应该创建用户当邮箱有效', () => {});
  });

  describe('AC-002: 重复邮箱检查', () => {
    it('UT-002: register 应该抛出错误当邮箱已存在', () => {});
  });
});
```

### 方式三：使用标签/标记

```typescript
// Jest with jest-each
describe.each([
  { testId: 'UT-001', req: 'REQ-001', ac: 'AC-001' },
  { testId: 'UT-002', req: 'REQ-001', ac: 'AC-002' },
])('$testId ($req/$ac)', ({ testId, req, ac }) => {
  it(`should pass for ${testId}`, () => {});
});
```

## 自动化生成脚本

### 从代码提取追溯信息

```bash
#!/bin/bash
# extract-traceability.sh

echo "# 自动生成的追溯矩阵"
echo ""
echo "| 测试ID | 需求ID | 验收标准 | 文件位置 |"
echo "|--------|--------|----------|----------|"

grep -r "@requirement\|@testId\|@acceptance" tests/ --include="*.ts" | \
  awk -F: '{
    file=$1;
    gsub(/.*@requirement /, "REQ:", $0);
    gsub(/.*@testId /, "TEST:", $0);
    gsub(/.*@acceptance /, "AC:", $0);
    print "| " $0 " | " file " |"
  }'
```

### 检查未覆盖需求

```bash
#!/bin/bash
# check-coverage.sh

# 从需求文档提取需求ID
REQUIREMENTS=$(grep -oE "REQ-[0-9]+" docs/requirements.md | sort | uniq)

# 从测试代码提取已覆盖的需求ID
COVERED=$(grep -rhoE "@requirement REQ-[0-9]+" tests/ | sort | uniq)

echo "未覆盖的需求:"
comm -23 <(echo "$REQUIREMENTS") <(echo "$COVERED")
```

## 维护建议

1. **新增需求时**
   - 立即在追溯矩阵中添加条目
   - 状态标记为 ❌ 未覆盖

2. **编写测试时**
   - 在测试代码中添加 @requirement 标注
   - 更新追溯矩阵状态

3. **定期审查**
   - 每个 Sprint 结束检查覆盖状态
   - 确保 P0 需求 100% 覆盖

4. **自动化**
   - CI 中运行脚本检查未覆盖需求
   - P0 需求未覆盖时构建失败
