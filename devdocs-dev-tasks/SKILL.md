---
name: devdocs-dev-tasks
description: Break down system design into executable development tasks. Use when users need task breakdown, sprint planning, or development task lists. Triggers on keywords like "dev tasks", "task breakdown", "sprint planning", "implementation tasks".
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, TodoWrite, Bash
---

# DevDocs Development Tasks

Break down system design into actionable, trackable development tasks.

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese
- Generate all documents in Chinese

## Trigger Conditions

- User has completed system design and test plan
- User asks for development task breakdown
- User needs sprint/iteration planning

## Prerequisites

- Requirements document: `docs/devdocs/01-requirements.md`
- System design document: `docs/devdocs/02-system-design.md`
- Test cases document: `docs/devdocs/03-test-cases.md`（及 `03-test-unit.md`, `03-test-integration.md`, `03-test-e2e.md`）
- If not exists, suggest running previous phases first

## Workflow

1. **Read documents**: Load all previous phase documents
2. **Identify components**: Map system modules to tasks
3. **Define dependencies**: Establish task order
4. **Estimate scope**: Ensure task granularity
5. **Create task list**: Generate structured task document
6. **Confirm with user**: Get approval
7. **Load to TodoWrite**: Optionally add tasks to tracking

## Output

**File**: `docs/devdocs/04-dev-tasks.md`

If tasks exceed 20, split into:
- `docs/devdocs/04-dev-tasks.md` - Overview and dependency graph
- `docs/devdocs/04-dev-tasks-infra.md` - Infrastructure tasks
- `docs/devdocs/04-dev-tasks-core.md` - Core logic tasks
- `docs/devdocs/04-dev-tasks-api.md` - API layer tasks
- `docs/devdocs/04-dev-tasks-test.md` - Test implementation tasks

## Task Design Principles

Every task must satisfy the **TAR** principle:

| Principle | Description | Required Content |
|-----------|-------------|------------------|
| **Testable** | Can be verified by automated or manual testing | Test method and expected result |
| **Acceptable** | Has clear acceptance criteria | Specific, measurable completion criteria |
| **Reviewable** | Can be code reviewed independently | Review focus points |

## Document Template

```markdown
# 开发任务：<功能名称>

## 任务概览

- **总任务数**：X 个
- **执行顺序**：按依赖关系

## 任务设计原则

每个任务必须满足 **TAR 原则**：
- **可测试 (Testable)**：有明确的测试方法
- **可验收 (Acceptable)**：有可量化的完成标准
- **可审查 (Reviewable)**：有独立的代码审查点

## 依赖关系图

```
T-01 ─┬─> T-03 ─> T-05
T-02 ─┘           │
                  ▼
            T-06 ─> T-07
```

## 任务列表

### 1. 基础设施

#### T-01: <任务名称>

| 属性 | 内容 |
|------|------|
| **描述** | <任务描述> |
| **依赖** | 无 |
| **优先级** | P0 |
| **关联需求** | F-001, AC-001 |
| **涉及文件** | `src/db/schema.ts` |

**测试用例**（来自 `03-test-*.md`）：
- [ ] IT-001: 验证表结构创建成功

**测试方法**：
- [ ] 运行数据库迁移脚本
- [ ] 执行 IT-001 集成测试

**验收标准**：
- [ ] 迁移脚本执行无错误
- [ ] 数据库表结构与设计文档一致

**Review 要点**：
- [ ] 字段类型是否正确
- [ ] 索引设计是否合理
- [ ] 是否有安全隐患

---

### 2. 核心逻辑

#### T-02: <任务名称>

| 属性 | 内容 |
|------|------|
| **描述** | <任务描述> |
| **依赖** | T-01 |
| **优先级** | P0 |
| **关联需求** | F-001, AC-002, AC-003 |
| **涉及文件** | `src/services/xxx.ts` |

**编码约束**（参考 `/code-quality`）：
- [ ] 函数不超过 50 行，参数不超过 5 个
- [ ] 依赖通过注入，核心逻辑可单元测试
- [ ] 遵循 MTE 原则

**测试用例**（来自 `03-test-unit.md`）：
- [ ] UT-001: AC-002 - <测试场景>
- [ ] UT-002: AC-003 - <测试场景>

**测试约束**（参考 `/testing-guide`）：
- [ ] 测试覆盖率 >= 80%
- [ ] 禁止弱断言，验证具体值
- [ ] 变异得分 >= 60%（推荐 >= 80%）

**验收标准**：
- [ ] 所有单元测试通过
- [ ] 行覆盖率 >= 80%，分支覆盖率 >= 80%

**Review 要点**：
- [ ] 业务逻辑是否正确
- [ ] 错误处理是否完善
- [ ] 代码是否符合规范

---

### 3. 接口层

#### T-03: <任务名称>

| 属性 | 内容 |
|------|------|
| **描述** | <任务描述> |
| **依赖** | T-02 |
| **优先级** | P0 |
| **关联需求** | F-001, AC-004 |
| **涉及文件** | `src/api/xxx.ts` |

**测试用例**（来自 `03-test-integration.md`）：
- [ ] IT-002: AC-004 - API 接口测试

**测试方法**：
- [ ] API 接口测试（正向/反向）
- [ ] 参数校验测试

**验收标准**：
- [ ] API 响应符合设计文档
- [ ] 错误码返回正确

**Review 要点**：
- [ ] 接口设计是否符合 RESTful 规范
- [ ] 参数校验是否完整
- [ ] 权限控制是否正确

---

### 4. UI 层（如适用）

#### T-04: <任务名称>

| 属性 | 内容 |
|------|------|
| **描述** | <任务描述> |
| **依赖** | T-03 |
| **优先级** | P1 |
| **关联需求** | F-001, US-001 |
| **涉及文件** | `src/components/xxx.tsx` |

**UI 约束**（参考 `/ui-skills`）：
- [ ] 使用 Tailwind CSS 默认值
- [ ] 使用无障碍组件原语（Base UI / Radix）
- [ ] 图标按钮必须有 aria-label
- [ ] 使用 h-dvh 替代 h-screen
- [ ] 动画仅限 transform/opacity

**测试用例**（来自 `03-test-e2e.md`）：
- [ ] E2E-001: US-001 - 完整用户流程

**验收标准**：
- [ ] 界面与设计稿一致
- [ ] E2E 测试通过
- [ ] 响应式布局正常

**Review 要点**：
- [ ] 组件是否可复用
- [ ] 是否遵循 ui-skills 约束
- [ ] 无障碍性是否达标

---

## 执行检查清单

| 任务 | 测试 | 验收 | Review | 提交 |
|------|------|------|--------|------|
| T-01: <name> | [ ] | [ ] | [ ] | [ ] |
| T-02: <name> | [ ] | [ ] | [ ] | [ ] |
| T-03: <name> | [ ] | [ ] | [ ] | [ ] |

## 风险项

| 任务 | 风险 | 缓解措施 |
|------|------|----------|
| T-XX | <潜在风险> | <缓解策略> |
```

## Constraints

### 基础约束

- [ ] **Single task must be completable within 4 hours**
- [ ] **Must specify task dependencies**
- [ ] **Must order by dependencies, no circular dependencies**
- [ ] **File paths must be specific, not "related files"**
- [ ] **Must provide dependency graph**
- [ ] Priority: P0 (blocker), P1 (important), P2 (minor)
- [ ] Task ID format: T-XX (sequential)

### 需求追溯约束

- [ ] **每个任务必须关联功能点 (F-XXX) 和验收标准 (AC-XXX)**
- [ ] **每个任务必须关联测试用例 (UT/IT/E2E-XXX)**
- [ ] 测试用例来自 `03-test-*.md` 文档

### Skill 协作约束

| 任务类型 | 约束 Skill | 检查点 |
|----------|-----------|--------|
| 核心逻辑 | `/code-quality` | MTE 原则、函数长度、依赖注入 |
| 测试编写 | `/testing-guide` | 覆盖率、断言质量、变异测试 |
| UI 实现 | `/ui-skills` | 无障碍、动画、布局约束 |
| 代码提交 | `/git-safety` | 使用 git mv/rm 处理文件 |
| 提交信息 | `/commit-convention` | 遵循项目提交规范 |

### TAR Principle Constraints

- [ ] **Every task must include test method** (how to verify)
- [ ] **Every task must include acceptance criteria** (measurable completion criteria)
- [ ] **Every task must include review focus points** (what to check in code review)
- [ ] Test method must be executable (not vague descriptions)
- [ ] Acceptance criteria must be quantifiable
- [ ] Review points must be specific to the task type

## Task Execution Workflow

When executing a task, follow this workflow:

```
1. 开始任务
   │
   ▼
2. 编写代码（遵循 /code-quality, /ui-skills 约束）
   │
   ▼
3. 编写测试（遵循 /testing-guide 约束）
   │
   ▼
4. 执行测试用例（UT/IT/E2E-XXX）
   ├── 通过 ──────────────────┐
   └── 失败 → 修复 → 重新测试 │
                              ▼
5. 检查验收标准（AC-XXX）
   ├── 全部满足 ─────────────┐
   └── 未满足 → 补充 → 重检  │
                             ▼
6. 自查 Review 要点
   │
   ▼
7. 询问用户：是否提交代码？
   ├── 是 → 提交（遵循 /git-safety, /commit-convention）
   └── 否 → 继续修改
```

## Post-completion Action

After user confirms task document:
1. Ask if user wants to start development
2. If yes, use TodoWrite to add all tasks to tracking list
3. Suggest starting with first task (T-01)

## Task Completion Flow

When completing each task during development:

1. **Execute tests**: Run the test method defined for the task
2. **Verify acceptance**: Check all acceptance criteria are met
3. **Self-review**: Go through review points
4. **Ask for commit**: Use AskUserQuestion to ask:
   - "任务 T-XX 已完成，测试通过，是否提交代码？"
   - Options: "提交" / "继续修改" / "跳过"
5. **If commit**: Execute git add and commit with task ID in message
6. **Update TodoWrite**: Mark task as completed

### Commit Message Format

遵循 `/commit-convention` 规范，格式如下：

```
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
```

**type 类型**：feat | fix | refactor | test | docs | chore

## TodoWrite Integration

When user confirms to start development:

```
Use TodoWrite to add tasks:
- Each task becomes a todo item
- Maintain task order as defined
- Include task ID in todo content
- Update status after commit
```
