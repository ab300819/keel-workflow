---
name: devdocs-dev-workflow
description: Execute development tasks with skeleton-first approach and layered TDD. Includes optional adversarial verification (code quality + test completeness review). Use when users start working on a task (T-XX), need development guidance, or implement features/bugfixes. Triggers on keywords like "execute task", "start T-XX", "implement", "develop", "开发任务", "执行任务", "对抗式验证", "--review".
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, TodoWrite
---

# 开发工作流

执行单个开发任务的工作流指导，采用自顶向下开发模式和分层 TDD。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 触发条件

- 用户开始执行某个任务（如 T-01）
- 用户需要开发指导
- 用户从 devdocs-dev-tasks 进入开发阶段
- 关键词："开发任务"、"执行任务"、"开始 T-XX"

## 前置条件

- 任务文档：`docs/devdocs/04-dev-tasks.md`
- 任务已定义并包含：关联需求、验收标准、测试方法

## 工作流程

```
1. 读取任务定义
   ├── 从 04-dev-tasks.md 获取任务详情
   ├── 确认关联的 F-XXX、AC-XXX
   └── 确认关联的测试用例 UT/IT/E2E-XXX
           │
           ▼
2. 生成骨架代码（自顶向下）
   ├── 接口骨架 + @requirement/@satisfies 标注
   └── 测试骨架 + @verifies/@testcase 标注
           │
           ▼
3. 执行开发（分层 TDD）
   ├── 核心逻辑 🔴：测试先行
   ├── 接口层 🟡：推荐测试先行
   ├── UI 层 🟢：可实现后补测试
   └── 基础设施 ⚪：集成测试验证
           │
           ▼
4. 完成检查
   ├── 基础检查（始终执行）
   │   ├── 验收标准全部满足
   │   ├── 测试通过
   │   └── Review 要点自查
   │
   └── 对抗式验证（🔴自动触发 / 其他层级 --review 手动触发）
       ├── 🔍 代码质量审查（/code-quality 视角）
       ├── 🧪 测试完备性审查（/testing-guide 视角）
       └── 📋 综合审查报告
           │
           ▼
4.5 更新自描述（/code-self-describe --update）
           │
           ▼
5. 提交代码（遵循 /commit-convention）
           │
           ▼
6. 更新追溯（运行 /devdocs-sync --trace）
```

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

## Skill 协作

| 阶段 | 协作 Skill | 说明 |
|------|-----------|------|
| 写业务代码 | `/code-quality` | MTE 原则、依赖注入、避免过度设计 |
| 写测试代码 | `/testing-guide` | 断言质量、变异测试、覆盖率 |
| UI 实现 | `/ui-orchestrator` | 无障碍、动画、布局约束 |
| 完成验证 | `/code-quality` + `/testing-guide` | 对抗式验证：多视角审查 |
| 完成检查 | `/code-self-describe` | 更新模块自描述（--update） |
| 代码提交 | `/git-safety` | 使用 git mv/rm 处理文件 |
| 提交信息 | `/commit-convention` | 遵循项目提交规范 |
| 任务完成 | `/devdocs-sync` | 后续：更新追溯矩阵（--trace） |

## 约束

### 骨架生成约束

- [ ] **接口骨架必须包含完整签名**
- [ ] **接口骨架必须添加追溯标注**
- [ ] **未实现方法必须抛出 Error**
- [ ] **测试骨架必须使用 skip/todo 标记**
- [ ] **测试骨架必须添加 @verifies 和 @testcase 标注**

### 分层 TDD 约束

- [ ] **核心逻辑任务必须标记 🔴 强制 TDD**
- [ ] **核心逻辑任务必须先写测试，后写实现**
- [ ] **核心逻辑任务禁止在测试通过前提交**
- [ ] 接口层任务标记 🟡 推荐 TDD
- [ ] UI 层任务标记 🟢 可选 TDD
- [ ] 基础设施任务标记 ⚪ 不适用 TDD
- [ ] TDD 任务必须包含红-绿-重构三步骤

### 完成检查约束

- [ ] **验收标准 (AC-XXX) 全部满足**
- [ ] **关联测试全部通过**
- [ ] **Review 要点自查完成**
- [ ] 代码追溯标注完整
- [ ] 代码分支覆盖分析完成（可选，使用 `/testing-guide` 分支分析）

## 对抗式验证（可选）

> 以不同角色视角审查代码，模拟 "开发 → 审查 → 测试" 的多人协作模式。
> 核心逻辑任务（🔴）自动触发，其他层级通过 `--review` 手动触发。

### 触发条件

| 任务层级 | 默认行为 | 手动控制 |
|---------|---------|---------|
| 🔴 核心逻辑 | **自动触发** | `--skip-review` 跳过 |
| 🟡 接口层 | 不触发 | `--review` 启用 |
| 🟢 UI 层 | 不触发 | `--review` 启用 |
| ⚪ 基础设施 | 不触发 | `--review` 启用 |

### 验证流程

```
基础完成检查（始终执行）
        │
        ├── AC 全部满足 ✅
        ├── 测试全部通过 ✅
        ├── 代码标注完整 ✅
        │
        ▼ （对抗式验证触发时）
Phase 1: 代码质量审查 🔍
        ├── 切换到 /code-quality 视角
        ├── MTE 原则检查（函数长度/参数/嵌套/职责）
        ├── 依赖方向检查
        ├── 安全检查
        └── 输出: 问题列表（Blocker/Suggestion）
        │
        ▼
Phase 2: 测试完备性审查 🧪
        ├── 切换到 /testing-guide 视角
        ├── 断言质量检查（禁止弱断言）
        ├── 覆盖率检查（行/分支 ≥80%）
        ├── 需求追溯检查（AC 全覆盖）
        ├── [可选] 代码分支覆盖分析
        └── 输出: 问题列表（Blocker/Suggestion）
        │
        ▼
Phase 3: 综合审查报告 📋
        ├── 汇总所有问题
        ├── 🚫 Blocker → 必须修复后重新验证
        └── 💡 Suggestion → 询问用户是否修复
```

### 审查结果分级

| 级别 | 标记 | 处理 |
|------|------|------|
| 🚫 Blocker | 必须修复 | 阻止提交，修复后重新验证 |
| 💡 Suggestion | 建议修复 | 询问用户，可选择忽略 |

### 对抗式验证约束

- [ ] **Blocker 问题必须修复后才能提交**
- [ ] **每个 Phase 必须明确声明当前审查角色**
- [ ] **审查结果必须分级（Blocker/Suggestion）**
- [ ] 核心逻辑任务（🔴）默认触发
- [ ] 修复 Blocker 后必须重新运行验证

> 详细审查清单和报告模板见 [verification-flow.md](verification-flow.md)

## 任务完成流程

### TDD 任务（核心逻辑 🔴）

1. **确认测试先行**：检查是否先写了测试
2. **确认红-绿循环**：测试从失败到通过
3. **检查重构**：代码是否经过优化
4. **验证验收标准**：检查所有 AC 是否满足
5. **对抗式验证**（自动触发）：
   - Phase 1: 代码质量审查（/code-quality 视角）
   - Phase 2: 测试完备性审查（/testing-guide 视角）
   - Phase 3: 综合报告，处理 Blocker
6. **更新自描述**：运行 /code-self-describe --update
7. **询问提交**：使用 AskUserQuestion 询问：
   - "任务 T-XX（TDD）已完成，测试通过，是否提交代码？"
   - 选项："提交" / "继续修改" / "跳过"
8. **如提交**：执行 git add 和 commit，消息包含任务编号
9. **更新状态**：将任务标记为已完成

### 非 TDD 任务（接口/UI/基础设施）

1. **执行测试**：运行任务定义的测试方法
2. **验证验收标准**：检查所有验收标准是否满足
3. **对抗式验证**（如 --review 触发）：同上 Phase 1-3
4. **自查 Review 要点**：检查代码审查要点
5. **询问提交**：使用 AskUserQuestion 询问
6. **如提交**：执行 git add 和 commit
7. **更新状态**：将任务标记为已完成

## 提交信息格式

遵循 `/commit-convention` 规范，格式如下：

```
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
```

**type 类型**：feat | fix | refactor | test | docs | chore

## 参考资料

- [skeleton-examples.md](skeleton-examples.md) - 接口/测试骨架示例
- [execution-flow.md](execution-flow.md) - 任务执行流程详解
- [verification-flow.md](verification-flow.md) - 对抗式验证流程详解
