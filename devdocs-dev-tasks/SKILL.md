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
- Test plan: `docs/devdocs/03-test-plan.md`
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
| **涉及文件** | `src/db/schema.ts` |

**测试方法**：
- [ ] 运行数据库迁移脚本
- [ ] 验证表结构创建成功

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
| **涉及文件** | `src/services/xxx.ts` |

**测试方法**：
- [ ] 单元测试覆盖所有公共方法
- [ ] 测试覆盖率 >= 80%

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
| **涉及文件** | `src/api/xxx.ts` |

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

- [ ] **Single task must be completable within 4 hours**
- [ ] **Must specify task dependencies**
- [ ] **Must order by dependencies, no circular dependencies**
- [ ] **File paths must be specific, not "related files"**
- [ ] **Must provide dependency graph**
- [ ] Priority: P0 (blocker), P1 (important), P2 (minor)
- [ ] Task ID format: T-XX (sequential)
- [ ] Testing tasks should reference test plan document

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
2. 编写代码
   │
   ▼
3. 执行测试方法
   ├── 通过 ──────────────────┐
   └── 失败 → 修复 → 重新测试 │
                              ▼
4. 检查验收标准
   ├── 全部满足 ─────────────┐
   └── 未满足 → 补充 → 重检  │
                             ▼
5. 自查 Review 要点
   │
   ▼
6. 询问用户：是否提交代码？
   ├── 是 → git add & commit
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

```
feat(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

测试: <测试结果>
验收: <验收状态>
```

## TodoWrite Integration

When user confirms to start development:

```
Use TodoWrite to add tasks:
- Each task becomes a todo item
- Maintain task order as defined
- Include task ID in todo content
- Update status after commit
```
