---
name: devdocs-dev-tasks
description: Break down system design into executable development tasks. Use when users need task breakdown, sprint planning, or development task lists. Triggers on keywords like "dev tasks", "task breakdown", "sprint planning", "implementation tasks".
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, TodoWrite, Bash
---

# 开发任务

将系统设计分解为可执行、可追踪的开发任务。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户已完成系统设计和测试用例
- 用户要求拆分开发任务
- 用户需要迭代/Sprint 规划

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 系统设计文档：`docs/devdocs/02-system-design.md`
- 测试用例文档：`docs/devdocs/03-test-cases.md`
- 如不存在，建议先运行前置阶段

## 工作流程

1. **读取文档**：加载所有前置阶段文档
2. **识别组件**：将系统模块映射为任务
3. **定义依赖**：建立任务执行顺序
4. **评估范围**：确保任务粒度合适
5. **创建任务列表**：生成结构化任务文档
6. **用户确认**：获得批准
7. **加载到 TodoWrite**：可选，添加任务到追踪列表

## 输出文件

**主文件**：`docs/devdocs/04-dev-tasks.md`

### 文档拆分规则

当满足以下条件时，应拆分文档：
- 任务数量超过 **20 个**
- 文档超过 **300 行**
- 涉及多个独立模块

**拆分方式**：

```
docs/devdocs/
├── 04-dev-tasks.md              # 主文档：任务概览、依赖图、执行检查清单
├── 04-dev-tasks-infra.md        # 基础设施任务
├── 04-dev-tasks-core.md         # 核心逻辑任务
├── 04-dev-tasks-api.md          # 接口层任务
└── 04-dev-tasks-test.md         # 测试任务
```

### 任务归档

已完成任务过多时归档到 `04-dev-tasks-archive.md`。

详见 [archive-rules.md](archive-rules.md)

## 任务设计原则

每个任务必须满足 **TAR 原则**：

| 原则 | 说明 | 必需内容 |
|------|------|----------|
| **可测试 (Testable)** | 可通过自动化或手动测试验证 | 测试方法和预期结果 |
| **可验收 (Acceptable)** | 有明确的验收标准 | 具体、可量化的完成标准 |
| **可审查 (Reviewable)** | 可独立进行代码审查 | Review 要点 |

## 代码追溯标注规范

> 实现文档↔代码的双向追溯，AI 在生成代码时自动添加标注。

### 标注类型

| 标注 | 用途 | 位置 |
|------|------|------|
| `@requirement F-XXX` | 关联功能点 | 接口/类/模块 |
| `@satisfies AC-XXX` | 满足的验收标准 | 接口/方法 |
| `@verifies AC-XXX` | 验证的验收标准 | 测试用例 |
| `@testcase UT/IT/E2E-XXX` | 测试编号 | 测试用例 |

### 标注示例

```typescript
/**
 * 创建用户
 * @requirement F-001 - 用户注册
 * @satisfies AC-001 - 邮箱格式校验
 * @satisfies AC-002 - 密码强度校验
 */
export async function createUser(dto: CreateUserDTO): Promise<User> {
  // 实现代码
}

/**
 * @verifies AC-001 - 邮箱格式校验
 * @testcase UT-001
 */
test('createUser 应该拒绝无效邮箱格式', () => {
  // 测试代码
});
```

### 标注规则

| 层级 | 标注位置 | 强制性 |
|------|----------|--------|
| 公共接口 | Service/API 入口方法 | **必须** |
| 测试文件 | 每个测试用例 | **必须** |
| 内部实现 | 复杂逻辑 | 可选 |

详细骨架示例见 [skeleton-examples.md](skeleton-examples.md)

## 自顶向下开发模式

> 先定义骨架，后填充细节。确保追溯链在代码生成时就建立。

### 开发流程

```
Step 1: 生成接口骨架
        ├── 方法签名（来自 02-system-design.md）
        ├── 添加 @requirement/@satisfies 标注
        └── 方法体: throw new Error('Not implemented')
                │
                ▼
Step 2: 生成测试骨架
        ├── 测试结构（来自 03-test-cases.md）
        ├── 添加 @verifies/@testcase 标注
        └── 测试体: test.skip() 或 test.todo()
                │
                ▼
Step 3: 实现接口细节（遵循 /code-quality）
                │
                ▼
Step 4: 完善测试（遵循 /testing-guide）
                │
                ▼
Step 5: 运行 /devdocs-sync --trace 更新追溯矩阵
```

### 骨架生成约束

- [ ] **接口骨架必须包含完整签名**（参数、返回值、泛型）
- [ ] **接口骨架必须添加追溯标注**
- [ ] **未实现方法必须抛出 Error 并注明任务编号**
- [ ] **测试骨架必须使用 skip/todo 标记**
- [ ] **测试骨架必须添加 @verifies 和 @testcase 标注**

详见 [skeleton-examples.md](skeleton-examples.md)

## 分层 TDD 模式

根据任务类型决定测试优先级：

| 层级 | TDD 模式 | 说明 |
|------|----------|------|
| **核心逻辑** (Service/Domain) | 🔴 强制 | 测试先行 |
| **接口层** (Controller/API) | 🟡 推荐 | 建议测试先行 |
| **UI 层** (Component/View) | 🟢 可选 | 可实现后补 |
| **基础设施** (DB/Config) | ⚪ 不适用 | 集成测试验证 |

### TDD 循环

```
┌─────┐    ┌─────┐    ┌─────┐
│ 红  │ → │ 绿  │ → │重构 │ ──┐
│写测试│    │写实现│    │优化 │   │
│(失败)│    │(通过)│    │代码 │   │
└─────┘    └─────┘    └─────┘   │
    ↑                           │
    └───────────────────────────┘
```

详细执行流程见 [execution-flow.md](execution-flow.md)

## 约束

### 基础约束

- [ ] **单个任务必须在 4 小时内可完成**
- [ ] **必须指定任务依赖**
- [ ] **必须按依赖排序，不能有循环依赖**
- [ ] **文件路径必须具体，不能写"相关文件"**
- [ ] **必须提供依赖关系图**
- [ ] 优先级：P0（阻塞）、P1（重要）、P2（次要）
- [ ] 任务编号格式：T-XX（顺序编号）

### 需求追溯约束

- [ ] **每个任务必须关联功能点 (F-XXX) 和验收标准 (AC-XXX)**
- [ ] **每个任务必须关联测试用例 (UT/IT/E2E-XXX)**
- [ ] 测试用例来自 `03-test-*.md` 文档

### Skill 协作约束

| 任务类型 | 约束 Skill | 检查点 |
|----------|-----------|--------|
| 核心逻辑 🔴 | `/code-quality`, `/testing-guide` | TDD 流程、MTE 原则、依赖注入 |
| 接口层 🟡 | `/testing-guide` | 接口测试、契约验证 |
| UI 实现 🟢 | `/ui-skills` | 无障碍、动画、布局约束 |
| 测试编写 | `/testing-guide` | 覆盖率、断言质量、变异测试 |
| 代码提交 | `/git-safety` | 使用 git mv/rm 处理文件 |
| 提交信息 | `/commit-convention` | 遵循项目提交规范 |

### TAR 原则约束

- [ ] **每个任务必须包含测试方法**（如何验证）
- [ ] **每个任务必须包含验收标准**（可量化的完成标准）
- [ ] **每个任务必须包含 Review 要点**（代码审查关注点）
- [ ] 测试方法必须可执行（不能是模糊描述）
- [ ] 验收标准必须可量化
- [ ] Review 要点必须针对任务类型

### 分层 TDD 约束

- [ ] **核心逻辑任务必须标记 🔴 强制 TDD**
- [ ] **核心逻辑任务必须先写测试，后写实现**
- [ ] **核心逻辑任务禁止在测试通过前提交**
- [ ] 接口层任务标记 🟡 推荐 TDD
- [ ] UI 层任务标记 🟢 可选 TDD
- [ ] 基础设施任务标记 ⚪ 不适用 TDD
- [ ] TDD 任务必须包含红-绿-重构三步骤

## 完成后操作

用户确认任务文档后：
1. 询问用户是否开始开发
2. 如是，使用 TodoWrite 添加所有任务到追踪列表
3. 建议从第一个任务（T-01）开始

## 参考资料

- [task-template.md](task-template.md) - 完整任务文档模板
- [skeleton-examples.md](skeleton-examples.md) - 接口/测试骨架示例
- [execution-flow.md](execution-flow.md) - 任务执行流程详解
- [archive-rules.md](archive-rules.md) - 任务归档规则
