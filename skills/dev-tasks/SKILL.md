---
name: ms-dev-tasks
description: Break down system design into executable, trackable development tasks with dependency resolution and layer classification (🔴🟡🟢⚪). Use when users need task breakdown, sprint planning, or implementation planning. Triggers on "dev tasks", "task breakdown", "sprint planning", "implementation tasks", "拆分任务", "任务列表", "implementation plan", "开发任务拆分". NOT for executing tasks (use ms-dev-workflow) or defining features (use ms-feature).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, TodoWrite, Bash
metadata:
  patterns: [generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
reads_layout: [layout.v1, layout.v2]
writes_layout: layout.v1
reads_id_scheme: [id.v1, id.v2]
writes_id_scheme: id.v1
reads_traceability: [trace.v0, trace.v1]
writes_traceability: trace.v0
on_incompatible: block
migration: /ms-pipeline realign --docs-layout
---

# 开发任务

> ℹ️ 编号双轨：v1 项目用 `T-XX`（关联 `F`/`US`），v2 项目 [FUTURE] 用 `TASK-XX`（关联 `FEAT`/`STORY`）。详见 [id-scheme-implementation.md](../pipeline/references/layout/id-scheme-implementation.md)。
>
> ℹ️ 输出路径双轨：v1 写单文件 `04-dev-tasks.md`；v2 [FUTURE] 写多文件 `tasks/TASK-NNN.md` + `tasks/index.md`（按 sprint 分组）。详见 [folder-organization-implementation.md](../pipeline/references/layout/folder-organization-implementation.md)。

> 视角：项目经理 — 关注任务粒度合理性、依赖可行性与交付优先级，而非技术偏好。

将系统设计分解为可执行、可追踪的开发任务。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户已完成系统设计和测试用例
- 用户要求拆分开发任务
- 用户需要迭代/Sprint 规划
- 来自 `/ms-feature`、`/ms-bugfix`、`/ms-insights` 的增量需求

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 系统设计文档：`docs/devdocs/02-system-design.md`
- 测试用例文档：`docs/devdocs/03-test-cases.md`
- 如不存在，建议先运行前置阶段

## 快速开始

**一句话**: 将系统设计拆分为可执行的开发任务，按 🔴🟡🟢⚪ 分层标记（层级为风险输入），并提议初始 `review_profile`（执行强度由 review_profile 决定）。

**最常见用法**: `/ms-dev-tasks`（标准模式）、`/ms-dev-tasks --fast`（跳过逐步确认）

**不适合?** 执行任务→`/ms-dev-workflow`，设计还没做→`/ms-system-design`

## 运行模式

```bash
/ms-dev-tasks                  → 标准模式（逐步确认）
/ms-dev-tasks --fast           → 跳过逐步确认，直接生成，仅最终确认
/ms-dev-tasks --realign[=scope] → 规范升级回扫（任务结构/字段差距补齐；不改任务状态）。详见 [references/realign.md](references/realign.md)；推荐 `/ms-pipeline realign`
```

### `--fast` 模式

- 使用合理默认值（不询问任务粒度偏好等）
- 仅保留最终写入前的 1 次确认
- 默认行为不变，`--fast` 是 opt-in

## 工作流程

1. **读取文档**：加载所有前置阶段文档
2. **识别组件**：将系统模块映射为任务
3. **TDD 分层**：对每个任务分类层级（🔴🟡🟢⚪）作为风险输入，按[任务分层](#任务分层)规则标记，并提议初始 `review_profile`
4. **定义依赖**：建立任务执行顺序
5. **评估范围**：确保任务粒度合适
6. **生成任务文档**：按层级分组输出，每个任务包含执行步骤参考（实际强度由 `review_profile` 决定，S1~S11 完整矩阵见 `ms-dev-workflow` execution-flow）：
   - 🔴 核心逻辑（通常 audit/guarded）：红→绿→重构三步参考（`TDD 执行步骤` 区块）
   - 🟡 接口层（通常 guarded）：红→绿两步参考（`TDD 执行步骤（推荐）` 区块）
   - 🟢 UI 层（通常 fast/guarded）：实现→验证→补测试（普通执行步骤）
   - ⚪ 基础设施（通常 fast）：实现→集成测试验证（普通执行步骤）
   - 参照 [templates/task-template.md](templates/task-template.md) 各层级示例
7. **用户确认**：获得批准
8. **加载到 TodoWrite**：可选，添加任务到追踪列表

## 上下文管理

### 分批原则

按功能点（v1: F-XXX / v2 [FUTURE]: FEAT-XXX）分批设计任务，每批完成一个功能点的全部任务拆分。

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

根据任务类型分层；层级是风险输入之一，**执行强度由 `review_profile` 决定**（S1~S11 完整矩阵见 ms-dev-workflow execution-flow）：

| 层级 | 标签 | 建议初始 review_profile | 说明 |
|------|------|------------------------|------|
| **核心逻辑** (Service/Domain) | 🔴 | audit（含高风险信号时）/ guarded | 测试先行，完整独立审查 |
| **接口层** (Controller/API) | 🟡 | guarded | 建议测试先行 |
| **UI 层** (Component/View) | 🟢 | fast / guarded | 可实现后补；有跨模块契约时升 guarded |
| **基础设施** (DB/Config) | ⚪ | fast（仅非运行时·非安全）/ audit（schema 迁移/部署） | 集成测试验证 |

> 层级标签 🔴🟡🟢⚪ 仅作分类输入；实际 review_profile 按上方[风险分类器](#review_profile-初始提议风险分类器)组合信号确定。

### review_profile 初始提议(风险分类器)

拆分时为每个任务提议初始 `review_profile`(dev-workflow 执行时可按实际 diff 升档):

- **audit** 信号(任一):不可逆数据变更/schema 迁移、安全/认证/权限/密钥、PII/隐私/合规、钱/支付、外部不可逆副作用(邮件/短信/webhook/队列/三方写)、共享核心 API 或反向依赖计数 ≥ 5 的模块、复杂算法、线上事故热修、并发/事务、依赖/lockfile/运行时升级、CI/测试框架/质量门自身、生产配置/IaC/部署/特性开关/限流/缓存/重试/幂等/超时、序列化/DTO/协议兼容、高流量热路径、依赖链根节点。
- **guarded** 信号(任一):有分支的新行为、公开/对外接口、跨模块契约、行为边界不清的新测试。
- **fast**(默认):配置(仅非运行时·非安全·非部署)、文案、样式、有覆盖的内部重构、文档、无下游叶子。
- 组合规则:命中 ≥2 个 guarded 信号 或 预估 diff > 150 行/触及 > 5 文件 → 升 audit。
- 治理:不确定默认 guarded;层级标签 🔴🟡🟢⚪ 仅作输入之一。

## 设计稿关联

当 `01-requirements.md` 中存在 `## 设计资产`（design_context）时，任务定义增加设计信息：

| 任务层级 | 设计稿关联 |
|----------|-----------|
| 🟢 UI 层 | **必须**：标注 design_ref（关联设计稿页面/组件，如 D-01:登录页） |
| 🟡 接口层 | **推荐**：标注驱动接口设计的设计稿页面 |
| 🔴 核心逻辑 | 不适用 |
| ⚪ 基础设施 | 不适用 |

- 组件库引用：🟢 UI 任务必须在 `UI 约束` 中列出使用的组件库组件
- 无 design_context 时：上述字段留空，不阻塞任务生成

> design_context schema 定义见 [prd/references/design-context.md](../prd/references/design-context.md)

## 约束

### 阶段边界约束（最高优先级）
- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码（源代码、脚本、配置变更）**（恢复方式：使用 /ms-dev-workflow 执行编码）
- [ ] Write 工具仅用于写入 `docs/devdocs/` 下的 Markdown 文档
- [ ] Bash 工具仅用于只读操作（如查看目录结构），不得执行代码修改
- [ ] 编码实现由 `/ms-dev-workflow` 负责，本 Skill 不涉及
- [ ] **⛔ 禁止继续：生成/更新文档未在顶部写入 `generated_by / spec_version / generated_at` 三字段 YAML frontmatter**（恢复方式：按 [templates/task-template.md](templates/task-template.md) 顶部示例补齐；spec_version 常量见 [references/realign.md](references/realign.md)）

### 基础约束

- [ ] **单个任务必须在 4 小时内可完成**
- [ ] **必须指定任务依赖**
- [ ] **必须按依赖排序，不能有循环依赖**
- [ ] **文件路径必须具体，不能写"相关文件"**
- [ ] **必须提供依赖关系图**
- [ ] 优先级：P0（阻塞）、P1（重要）、P2（次要）
- [ ] 任务编号格式：v1 用 `T-XX` / v2 [FUTURE] 用 `TASK-XX`（顺序编号；按项目 `AGENTS.md devdocs.id_scheme` 选择）
- [ ] 后批次任务详细程度不低于首批次（TAR 完整性、路径具体性、粒度一致性）
- [ ] 每个功能点完成后执行一致性自检

### 需求追溯约束

- [ ] **每个任务必须关联功能点（v1: F-XXX / v2 [FUTURE]: FEAT-XXX）和验收标准 (AC-XXX)**
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

> 层级 🔴🟡🟢⚪ 为**风险输入**，执行强度由 `review_profile` 决定；S1~S11 完整强制程度见 ms-dev-workflow execution-flow 矩阵。

- [ ] **核心逻辑任务标记 🔴**；`audit` 档（通常来自 🔴/高风险信号组合）走完整独立审查（红→绿→重构）；`guarded` 档走推荐独立审查
- [ ] **接口层任务标记 🟡**；通常提议 `guarded`，含推荐 TDD 执行步骤（红→绿）
- [ ] UI 层任务标记 🟢；通常提议 `fast` 或 `guarded`，执行步骤为：实现→验证→补测试
- [ ] 基础设施任务标记 ⚪；非运行时/非安全配置提议 `fast`，schema 迁移/部署提议 `audit`，执行步骤为：实现→集成测试验证
- [ ] **测试断言必须引用 AC，禁止从实现代码反推测试**
- [ ] **任务文档必须按层级分组输出**（基础设施→核心逻辑→接口层→UI 层）
- [ ] **每个任务的属性表必须包含 `TDD 模式` 行**
- [ ] **每个任务的属性表必须包含 `review_profile` 行**（`fast` | `guarded` | `audit`，按上述风险分类器提议）

### 执行约束

- [ ] **任务执行必须使用 `/ms-dev-workflow`**
- [ ] 禁止跳过 dev-workflow 直接写代码（会导致追溯失效）
- [ ] 任务完成后必须执行 `/ms-sync`

## 增量任务管理

### 来源

| 来源 Skill | 触发场景 | 操作 |
|-----------|---------|------|
| `/ms-feature` | 新增功能需求 | 追加任务到列表 |
| `/ms-bugfix` | Bug 修复需求 | 插入高优先级任务 |
| `/ms-insights` | 改进建议确认 | 追加任务到列表 |

### 增量操作

- **新增任务**：追加到任务列表末尾，重新编号
- **插入任务**：高优先级任务插入合适位置
- **更新依赖**：调整受影响任务的依赖关系
- **更新状态**：标记任务完成/进行中
- **回填 design_ref**：当 design_context 新增/更新后，由编排器触发扫描已有 🟢 UI 任务，按 D-XX 匹配补标 design_ref 和组件库映射

### design_ref 回填规则

由编排器在 post-tasks 阶段委托调用（详见文末[编排器接口](#编排器接口)）。

- 扫描 04-dev-tasks.md 中所有 🟢 UI 层任务
- 已有 design_ref 的任务跳过（幂等保护）
- 按任务关联的 US/AC 与 design_context.references[] 的 pages/描述做语义匹配，标注对应 D-XX
- 无法匹配的任务不写 design_ref，在任务备注中标注"⚠️ 待绑定设计稿"，由用户手动绑定
- 同时补充 component_library 中的组件映射（如有）

## 完成后操作

用户确认任务文档后：
1. 询问用户是否开始开发
2. 如是，使用 TodoWrite 添加所有任务到追踪列表
3. 建议从第一个任务开始，或使用批量模式：v1 `/ms-dev-workflow T-01~T-XX` / v2 [FUTURE] `/ms-dev-workflow TASK-01~TASK-XX`
4. **执行任务时必须使用 `/ms-dev-workflow`**
5. 支持按功能点（v1: `F-XXX` / v2 [FUTURE]: `FEAT-XXX`）或用户故事（v1: `US-XXX` / v2 [FUTURE]: `STORY-XXX`）批量执行

> **重要**（layout.v1 legacy）：直接写代码而不使用 dev-workflow 会导致代码缺失 `@satisfies`/`@verifies` 标注，
> 使 `/ms-sync` 无法自动追溯，破坏文档↔代码的闭环。layout.v2 起改用 `traceability.yml` 外置追溯。

## 参考资料

- [templates/task-template.md](templates/task-template.md) - 完整任务文档模板
- [templates/archive-rules.md](templates/archive-rules.md) - 任务归档规则

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-dev-tasks
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
  skill: ms-verify
  args: "--readiness"
```

## 下一步

完成后建议使用 `/ms-dev-workflow` 执行开发任务。

> **提示**：文档变更较大时，建议运行 `/agent-memory` 同步记忆文件。

## 协作 Skill

| 场景 | Skill |
|------|-------|
| 执行开发任务 | `/ms-dev-workflow` |
| 同步文档状态 | `/ms-sync` |
| 新增功能需求 | `/ms-feature` |
| 修复 Bug | `/ms-bugfix` |

## 编排器接口

> 以下模式由编排器（ms-pipeline）内部调用，用户通常不需要直接使用。

```bash
/ms-dev-tasks --backfill-design → 回填 design_ref（由 pipeline design 委托）
```
