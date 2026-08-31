---
name: testing-guide
description: Opinionated constraints for writing effective tests. Guide unit tests, integration tests, and E2E tests with quality metrics beyond coverage. Includes AI-driven branch coverage analysis. Use when users write tests, review test code, or need testing strategy. Triggers on keywords like "test", "testing", "单元测试", "集成测试", "E2E", "测试质量", "coverage", "断言", "分支分析", "branch analysis", "未测试路径". NOT for test case design as documentation (use ms-test-cases).
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
- 用户要求分析代码分支覆盖情况
- Code Review 中涉及测试代码
- 关键词："分支分析"、"branch analysis"、"未测试路径"、"覆盖盲区"

---

## 核心理念

```
测试的目的不是"覆盖代码"，而是"验证行为"。
测试依据来自需求，不是来自代码。
```

> **⚠️ TDD 红阶段原则**：断言必须来自 03-test-\*.md 中对应 AC 的测试用例，禁止从实现代码反推测试。BCA（分支覆盖分析）仅用于防御性逻辑补充，不替代需求驱动测试。

### 测试质量金字塔

```
Level 3: 测试有效性 ─ 变异得分≥80%, 需求追溯100%
Level 2: 断言质量   ─ 禁止弱断言, 验证行为非实现
Level 1: 代码覆盖   ─ 行/分支覆盖≥80% (必要非充分)
```

> 详细说明见 [templates/core-concepts.md](templates/core-concepts.md)

---

## Constraints

### 核心阈值表

**全仓唯一权威测试质量阈值源**。谓词语义与 [`/code-quality` 核心阈值表](../code-quality/SKILL.md#核心阈值表) 同构：**≥ 达标值 = 合规；≥ 最低值且 < 达标值 = [Suggestion]；< 最低值 = [Blocker]**。**镜像边界**：agent 侧 references / SKILL 一律**改指针不镜像**（已迁移：dev-workflow verification-flow Phase 2、ms-test-cases SKILL.md 覆盖率要求）；仅**用户侧产物模板**（如 ms-test-cases 的 test-cases / unit-test 模板，会复制进用户项目，届时本 skill 不在场）允许内联数字，且须标注"摘录自本表，变更需同 commit 同步"。
>
> 待迁移（本表的已知 agent 侧镜像，未清）：`refactor/SKILL.md:216-220,250-252,271-272,281,359`（测试状态分类以 ≥80% 定义"充分/不足"，需连带重写状态机口径）、`onboard/SKILL.md:247`。

| 指标 | 达标值 | 最低值 | 适用 |
|------|-------:|-------:|------|
| 行覆盖率 | 80% | 60% | 全部项目 |
| 分支覆盖率 | 80% | 60% | 全部项目 |
| 变异得分 | 80% | 60% | 启用变异测试的项目；核心业务逻辑按达标值要求 |
| 每测试具体断言数 | ≥ 1 | — | 弱断言（`toBeDefined`/`toBeTruthy`/`not.toBeNull`）作为唯一断言 → [Blocker] |

### 单元测试约束

- [ ] **每个测试必须有 ≥1 个具体断言**
- [ ] **禁止弱断言作为唯一断言** (`toBeDefined`, `toBeTruthy`, `not.toBeNull`)
- [ ] **测试名称必须描述预期行为**——`test('works')` 这类名字在失败时不提供任何诊断信息
- [ ] **一个测试只验证一个行为**——多个断言塞一个测试，失败时定位不到是哪条 AC 挂了
- [ ] **测试依据来自需求，不是代码**
- [ ] 只 Mock 外部依赖，不 Mock 内部实现

> 详细指南见 [templates/unit-testing.md](templates/unit-testing.md)

### 覆盖率约束

- [ ] **行/分支覆盖率达标**（阈值与分级见[核心阈值表](#核心阈值表)）

### 变异测试约束（推荐）

- [ ] 变异得分达标（阈值见[核心阈值表](#核心阈值表)；核心业务逻辑按达标值要求）

> 配置见 [templates/mutation-testing.md](templates/mutation-testing.md)

### 集成测试约束

- [ ] 必须验证模块间数据流
- [ ] 必须验证接口契约
- [ ] 测试数据必须独立

> 详细指南见 [templates/integration-testing.md](templates/integration-testing.md)

### E2E 测试约束

- [ ] **P0 场景必须 100% 覆盖**
- [ ] 使用显式等待，禁止硬编码延时

> 详细指南见 [templates/e2e-testing.md](templates/e2e-testing.md)

### 需求追溯约束

- [ ] 每个需求必须有对应测试

> 模板见 [templates/traceability-matrix.md](templates/traceability-matrix.md)

---

## 测试骨架生成

> AI 驱动的自顶向下开发：先生成测试骨架，后填充实现。

### 标注规范

测试代码必须包含追溯标注，用于 `/ms-sync` 扫描：

```typescript
/**
 * @verifies AC-XXX - 验收标准描述
 * @testcase UT/IT/E2E-XXX
 */
test('测试名称', () => {
  // 测试代码
});
```

| 标注 | 用途 | 必须性 |
|------|------|--------|
| `@verifies AC-XXX` | 关联验收标准 | **必须** |
| `@testcase UT/IT/E2E-XXX` | 测试用例编号 | **必须** |

### 骨架生成流程

```
03-test-cases.md (测试用例设计)
        │
        ▼
生成测试骨架
        ├── describe 结构（按功能点分组）
        ├── test.skip() 占位（每个测试用例）
        ├── @verifies/@testcase 标注
        └── // TODO: 实现测试 注释
        │
        ▼
逐个实现测试
        ├── 移除 skip
        ├── 编写 AAA 结构
        └── 添加具体断言
```

### 骨架示例

```typescript
// tests/user.service.test.ts

describe('UserService', () => {
  describe('createUser', () => {
    /**
     * @verifies AC-001 - 邮箱格式校验
     * @testcase UT-001
     */
    test.skip('应该拒绝无效邮箱格式', () => {
      // TODO: 实现测试
      // Arrange: 准备无效邮箱
      // Act: 调用 createUser
      // Assert: 验证抛出 ValidationError
    });

    /**
     * @verifies AC-002 - 密码强度校验
     * @testcase UT-002
     */
    test.skip('应该拒绝弱密码', () => {
      // TODO: 实现测试
    });

    /**
     * @verifies AC-003 - 用户名唯一性
     * @testcase UT-003
     */
    test.skip('应该拒绝重复用户名', () => {
      // TODO: 实现测试
    });
  });
});
```

### 骨架生成约束

- [ ] **必须使用 `test.skip()` 或 `test.todo()` 标记未实现测试**
- [ ] **必须添加 `@verifies` 和 `@testcase` 标注**
- [ ] **必须按功能点 (F-XXX) 组织 describe 结构**

### 与 DevDocs 协作

| 阶段 | Skill | 输入 | 输出 |
|------|-------|------|------|
| 测试设计 | `/ms-test-cases` | 需求文档 | 测试用例矩阵 |
| 骨架生成 | `/ms-dev-tasks` | 测试用例 | 测试骨架代码 |
| 测试实现 | `/testing-guide` | 骨架代码 | 完整测试 |
| 追溯同步 | `/ms-sync` | 代码标注 | 更新矩阵 |

---

## 代码分支覆盖分析（AI 驱动）

> 代码实现完成后，AI 分析所有代码分支，找出未被测试覆盖的路径，生成补充测试用例。
> 这是对需求驱动测试（AC → 测试）的**补充**，不是替代。

### 定位

```
需求驱动测试（AC → 测试）  ← 主路径，覆盖业务规则
         ＋
代码分支分析（代码 → 测试） ← 补充路径，覆盖防御性逻辑
         ＝
完整测试覆盖
```

### 适用场景

| 场景 | 说明 |
|------|------|
| 代码包含防御性逻辑 | 参数校验、null 检查、类型保护 |
| 复杂条件分支 | switch/case、多条件组合 |
| 覆盖率工具显示分支不足 | 行覆盖≥80% 但分支覆盖<80% |
| 变异测试发现存活变异体 | 补充测试以杀死变异体 |

### 分析流程

```
Step 1: 分析代码分支
        ├── 条件语句（if/else, switch, 三元, &&/||）
        ├── 异常处理路径（try/catch, throw）
        ├── 早返回（guard clause）
        └── 循环边界（空集合、单元素、多元素）
                │
                ▼
Step 2: 映射现有测试
        ├── 匹配 @verifies 标注的 AC 覆盖范围
        ├── 分析每个测试实际触发的分支
        └── 标记已覆盖/未覆盖分支
                │
                ▼
Step 3: 生成补充测试
        ├── 为未覆盖分支生成测试用例
        ├── 使用 BCA-XXX 编号
        ├── 添加 @covers-branch 标注
        └── 遵循 AAA 结构和断言质量约束
```

### 标注规范

```typescript
/**
 * @covers-branch createUser:null-email-guard
 * @testcase BCA-001
 */
test('createUser 应该抛出错误当 email 为 null', () => {
  // Arrange
  const dto = { email: null, password: 'Strong1234' };
  // Act & Assert
  expect(() => createUser(dto)).toThrow('Email is required');
});
```

| 标注 | 用途 | 必须性 |
|------|------|--------|
| `@covers-branch <函数>:<分支描述>` | 标记覆盖的代码分支 | **必须** |
| `@testcase BCA-XXX` | 分支补充测试编号 | **必须** |

### 分支覆盖分析约束

- [ ] **分支分析在需求驱动测试之后执行**（先 AC 测试，后分支补充）
- [ ] **补充测试必须标注 @covers-branch**（区分需求驱动和分支补充）
- [ ] **补充测试使用 BCA-XXX 编号**（不占用 UT/IT/E2E 编号空间）
- [ ] **业务逻辑分支应回溯为 AC 对应的正式测试（UT/IT/E2E），不保留为 BCA 编号**

> 详细分析流程和示例见 [templates/branch-coverage-analysis.md](templates/branch-coverage-analysis.md)

---

## Quick Reference

### 测试命名

```
[被测方法] 应该 [预期行为] 当 [条件]
```

### 测试结构 (AAA)

```
Arrange → Act → Assert (具体断言)
```

### 禁止的弱断言

```javascript
// ❌ 禁止
expect(result).toBeDefined();
expect(result).toBeTruthy();
expect(result).not.toBeNull();

// ✅ 要求
expect(result.status).toBe('success');
expect(result.items).toHaveLength(3);
```

### 常用命令

```bash
# 覆盖率
npm test -- --coverage          # Jest
pytest --cov=src               # pytest
go test -cover ./...           # Go

# 变异测试
npx stryker run                # JS/TS
mutmut run                     # Python
mvn pitest:mutationCoverage    # Java
```

---

## 模板索引

### 核心指南

| 模板 | 说明 |
|------|------|
| [core-concepts.md](templates/core-concepts.md) | 测试核心理念与质量金字塔详解 |
| [unit-testing.md](templates/unit-testing.md) | 单元测试完整指南 |
| [integration-testing.md](templates/integration-testing.md) | 集成测试策略与示例 |
| [e2e-testing.md](templates/e2e-testing.md) | E2E 测试最佳实践 |

### 工具配置

| 模板 | 说明 |
|------|------|
| [branch-coverage-analysis.md](templates/branch-coverage-analysis.md) | AI 驱动的代码分支覆盖分析详解 |
| [mutation-testing.md](templates/mutation-testing.md) | 8种语言变异测试配置 |
| [ci-integration.md](templates/ci-integration.md) | CI/CD 集成配置 |
| [traceability-matrix.md](templates/traceability-matrix.md) | 需求追溯矩阵 |
| [test-examples.md](templates/test-examples.md) | 测试代码示例集 |

### 语言最佳实践

| 语言 | 框架 | 模板 |
|------|------|------|
| JavaScript/TypeScript | Jest, Vitest | [best-practices/jest-vitest.md](templates/best-practices/jest-vitest.md) |
| Python | pytest | [best-practices/pytest.md](templates/best-practices/pytest.md) |
| Java | JUnit 5 | [best-practices/junit5.md](templates/best-practices/junit5.md) |
| C# / .NET | xUnit, NUnit | [best-practices/xunit.md](templates/best-practices/xunit.md) |
| Go | testing, testify | [best-practices/go.md](templates/best-practices/go.md) |
| Rust | cargo test | [best-practices/rust.md](templates/best-practices/rust.md) |
| Swift | XCTest | [best-practices/swift.md](templates/best-practices/swift.md) |
| C/C++ | Google Test | [best-practices/googletest.md](templates/best-practices/googletest.md) |

---

## 与其他 Skills 协作

| 场景 | Skill |
|------|-------|
| 测试用例设计 | `/ms-test-cases` |
| 代码可测试性 | `/code-quality` |
| 重构前测试 | `/refactor` |
| 分支覆盖分析 | `/ms-dev-workflow` — 完成检查阶段可选调用 |
