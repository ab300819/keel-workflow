---
name: devdocs-dev-tasks
description: Break down system design into executable, trackable development tasks with dependency resolution and layer classification (🔴🟡🟢⚪). Use when users need task breakdown, sprint planning, or implementation planning. Triggers on "dev tasks", "task breakdown", "sprint planning", "implementation tasks", "拆分任务", "任务列表", "implementation plan", "开发任务拆分". NOT for executing tasks (use devdocs-dev-workflow) or defining features (use devdocs-feature).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, TodoWrite, Bash
metadata:
  patterns: [generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
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
- 来自 `/devdocs-feature`、`/devdocs-bugfix`、`/devdocs-insights` 的增量需求

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 系统设计文档：`docs/devdocs/02-system-design.md`
- 测试用例文档：`docs/devdocs/03-test-cases.md`
- 如不存在，建议先运行前置阶段

## 运行模式

```bash
/devdocs-dev-tasks              → 标准模式（逐步确认）
/devdocs-dev-tasks --fast       → 跳过逐步确认，直接生成，仅最终确认
```

### `--fast` 模式

- 使用合理默认值（不询问任务粒度偏好等）
- 仅保留最终写入前的 1 次确认
- 默认行为不变，`--fast` 是 opt-in

## 工作流程

1. **读取文档**：加载所有前置阶段文档
2. **识别组件**：将系统模块映射为任务
3. **TDD 分层**：对每个任务分类层级（🔴🟡🟢⚪），按[任务分层](#任务分层)规则标记
4. **定义依赖**：建立任务执行顺序
5. **评估范围**：确保任务粒度合适
6. **生成任务文档**：按层级分组输出，每个任务必须包含对应的 TDD 执行步骤：
   - 🔴 核心逻辑：红→绿→重构三步（必须包含 `TDD 执行步骤` 区块）
   - 🟡 接口层：红→绿两步（`TDD 执行步骤（推荐）` 区块）
   - 🟢 UI 层：实现→验证→补测试（普通执行步骤）
   - ⚪ 基础设施：实现→集成测试验证（普通执行步骤）
   - 参照 [templates/task-template.md](templates/task-template.md) 各层级示例
7. **用户确认**：获得批准
8. **加载到 TodoWrite**：可选，添加任务到追踪列表

## 上下文管理

### 分批原则

按功能点 (F-XXX) 分批设计任务，每批完成一个功能点的全部任务拆分。

### 质量锚点

- 首个功能点的任务列表作为**质量锚点**
- 每个新功能点开始前，回顾首批任务的详细程度（TAR 字段完整性、文件路径具体性、依赖关系明确性）
- 若当前批次详细程度明显低于锚点，立即补充

### 一致性自检

每个功能点的任务设计完成后，对比检查：
- [ ] TAR 三字段是否与首批一致（无缺项）
- [ ] 文件路径是否具体到文件名（非"相关文件"等模糊描述）
- [ ] 任务粒度是否一致（无超过 4 小时的任务）

## 输出文件

**主文件**：`docs/devdocs/04-dev-tasks.md`

### 文档拆分规则

当满足以下条件时，应拆分文档：
- 任务数量超过 **20 个**
- 文档超过 **300 行**
- 涉及多个独立模块

**拆分方式**：

```text
docs/devdocs/
├── 04-dev-tasks.md              # 主文档：任务概览、依赖图、执行检查清单
├── 04-dev-tasks-infra.md        # 基础设施任务
├── 04-dev-tasks-core.md         # 核心逻辑任务
├── 04-dev-tasks-api.md          # 接口层任务
└── 04-dev-tasks-test.md         # 测试任务
```

### 任务归档

已完成任务过多时归档到 `04-dev-tasks-archive.md`。

详见 [templates/archive-rules.md](templates/archive-rules.md)

## 任务设计原则

每个任务必须满足 **TAR 原则**：

| 原则 | 说明 | 必需内容 |
|------|------|----------|
| **可测试 (Testable)** | 可通过自动化或手动测试验证 | 测试方法和预期结果 |
| **可验收 (Acceptable)** | 有明确的验收标准 | 具体、可量化的完成标准 |
| **可审查 (Reviewable)** | 可独立进行代码审查 | Review 要点 |

## 任务分层

根据任务类型分层，决定 TDD 模式：

| 层级 | TDD 模式 | 说明 |
|------|----------|------|
| **核心逻辑** (Service/Domain) | 🔴 强制 | 测试先行 |
| **接口层** (Controller/API) | 🟡 推荐 | 建议测试先行 |
| **UI 层** (Component/View) | 🟢 可选 | 可实现后补 |
| **基础设施** (DB/Config) | ⚪ 不适用 | 集成测试验证 |

## 约束

### 阶段边界约束（最高优先级）
- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码（源代码、脚本、配置变更）**（恢复方式：使用 /devdocs-dev-workflow 执行编码）
- [ ] Write 工具仅用于写入 `docs/devdocs/` 下的 Markdown 文档
- [ ] Bash 工具仅用于只读操作（如查看目录结构），不得执行代码修改
- [ ] 编码实现由 `/devdocs-dev-workflow` 负责，本 Skill 不涉及

### 基础约束

- [ ] **单个任务必须在 4 小时内可完成**
- [ ] **必须指定任务依赖**
- [ ] **必须按依赖排序，不能有循环依赖**
- [ ] **文件路径必须具体，不能写"相关文件"**
- [ ] **必须提供依赖关系图**
- [ ] 优先级：P0（阻塞）、P1（重要）、P2（次要）
- [ ] 任务编号格式：T-XX（顺序编号）
- [ ] 后批次任务详细程度不低于首批次（TAR 完整性、路径具体性、粒度一致性）
- [ ] 每个功能点完成后执行一致性自检

### 需求追溯约束

- [ ] **每个任务必须关联功能点 (F-XXX) 和验收标准 (AC-XXX)**
- [ ] **每个任务必须关联测试用例 (UT/IT/E2E-XXX)**
- [ ] 测试用例来自 `03-test-*.md` 文档
- [ ] **TDD 执行步骤必须明确引用 AC 编号与对应的测试编号**

### TAR 原则约束

TAR 原则详述和具体性检查标准详见 [references/tar-rubric.md](references/tar-rubric.md)，执行时按需加载。

- [ ] **每个任务必须包含测试方法**（如何验证）
- [ ] **每个任务必须包含验收标准**（可量化的完成标准）
- [ ] **每个任务必须包含 Review 要点**（代码审查关注点）

### Generator 自检（用户确认前自动执行）

在呈现给用户确认前，加载 [references/tar-rubric.md](references/tar-rubric.md) 并自动验证：

- [ ] TAR 三字段完整（测试方法 + 验收标准 + Review 要点）
- [ ] 文件路径具体到文件名
- [ ] 预估 ≤ 4h
- [ ] 依赖无环（拓扑排序验证）

自检不通过项自动修复后再呈现用户，不增加用户交互步骤。

### 分层约束

- [ ] **核心逻辑任务必须标记 🔴 并包含完整 TDD 执行步骤**（红🔴→绿🟢→重构🔵）
- [ ] **接口层任务必须标记 🟡 并包含推荐 TDD 执行步骤**（红🔴→绿🟢）
- [ ] UI 层任务标记 🟢 可选 TDD，执行步骤为：实现→验证→补测试
- [ ] 基础设施任务标记 ⚪ 不适用 TDD，执行步骤为：实现→集成测试验证
- [ ] **测试断言必须引用 AC，禁止从实现代码反推测试**
- [ ] **任务文档必须按层级分组输出**（基础设施→核心逻辑→接口层→UI 层）
- [ ] **每个任务的属性表必须包含 `TDD 模式` 行**

### 执行约束

- [ ] **任务执行必须使用 `/devdocs-dev-workflow`**
- [ ] 禁止跳过 dev-workflow 直接写代码（会导致追溯失效）
- [ ] 任务完成后必须执行 `/devdocs-sync`

## 增量任务管理

### 来源

| 来源 Skill | 触发场景 | 操作 |
|-----------|---------|------|
| `/devdocs-feature` | 新增功能需求 | 追加任务到列表 |
| `/devdocs-bugfix` | Bug 修复需求 | 插入高优先级任务 |
| `/devdocs-insights` | 改进建议确认 | 追加任务到列表 |

### 增量操作

- **新增任务**：追加到任务列表末尾，重新编号
- **插入任务**：高优先级任务插入合适位置
- **更新依赖**：调整受影响任务的依赖关系
- **更新状态**：标记任务完成/进行中

## 完成后操作

用户确认任务文档后：
1. 询问用户是否开始开发
2. 如是，使用 TodoWrite 添加所有任务到追踪列表
3. 建议从第一个任务开始，或使用批量模式：`/devdocs-dev-workflow T-01~T-XX`
4. **执行任务时必须使用 `/devdocs-dev-workflow`**
5. 支持按功能点（`F-XXX`）或用户故事（`US-XXX`）批量执行

> **重要**：直接写代码而不使用 dev-workflow 会导致代码缺失 `@satisfies`/`@verifies` 标注，
> 使 `/devdocs-sync` 无法自动追溯，破坏文档↔代码的闭环。

## 参考资料

- [templates/task-template.md](templates/task-template.md) - 完整任务文档模板
- [templates/archive-rules.md](templates/archive-rules.md) - 任务归档规则

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: devdocs-dev-tasks
status: success | failed | partial
summary:
  headline: "任务拆分完成，10 个任务（4🔴 3🟡 2🟢 1⚪）"
  details:
    tasks_created: X
    task_range: "T-01~T-10"
    layers:
      core: X      # 🔴
      api: X       # 🟡
      ui: X        # 🟢
      infra: X     # ⚪
blockers: []
output_files:
  - docs/devdocs/04-dev-tasks.md
new_ids:
  tasks: [T-01~T-10]
next_recommended:
  skill: devdocs-verify
  args: "--readiness"
```

## 下一步

完成后建议使用 `/devdocs-dev-workflow` 执行开发任务。

> **提示**：文档变更较大时，建议运行 `/agent-memory` 同步记忆文件。

## 协作 Skill

| 场景 | Skill |
|------|-------|
| 执行开发任务 | `/devdocs-dev-workflow` |
| 同步文档状态 | `/devdocs-sync` |
| 新增功能需求 | `/devdocs-feature` |
| 修复 Bug | `/devdocs-bugfix` |
