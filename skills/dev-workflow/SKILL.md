---
name: ms-dev-workflow
description: Execute development tasks with skeleton-first approach and layered TDD. Supports single task, batch execution (by range, feature, user story), dependency resolution, and breakpoint resume. Includes optional adversarial verification and --headless unattended mode (无人值守). Triggers on "execute task", "start T-XX", "batch", "resume", "开发任务", "执行任务", "批量开发", "继续开发", "开始写代码", "开始开发", "--review", "--headless", "无人值守". NOT for task breakdown (use ms-dev-tasks) or bug fixes (use ms-bugfix).
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, TodoWrite, Task
metadata:
  patterns: [pipeline, reviewer]
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

# 开发工作流

> ℹ️ 编号双轨：v1 项目用 `T-XX`，v2 项目 [FUTURE] 用 `TASK-XX`。详见 [id-scheme-implementation.md](../pipeline/references/layout/id-scheme-implementation.md)。
>
> ℹ️ 输入路径双轨：v1 读 `04-dev-tasks.md` 找任务；v2 [FUTURE] 读 `tasks/<ID>.md` + 写回状态到该文件。详见 [folder-organization-implementation.md](../pipeline/references/layout/folder-organization-implementation.md)。

> 视角：资深开发者 — 务实优先，不过度设计，测试先行，提交原子化。

执行开发任务的工作流指导，支持单任务和批量执行，采用自顶向下开发模式和分层 TDD。

## 快速开始

**一句话**: 执行开发任务，采用骨架先行 + 分层 TDD。**最常见用法**: `/ms-dev-workflow T-03`（单任务）、`T-01~T-05`（批量）。**不适合?** 拆分任务→`/ms-dev-tasks`，修 Bug→`/ms-bugfix`。**语言**: 支持中英文提问，统一中文回复。

## 模式选择

入口处根据任务规模选择合适的开发模式：

| 模式 | 适用场景 | 流程 |
|------|---------|------|
| **轻量** | Bug fix、小改动、配置变更 | → `/ms-bugfix`（已有） |
| **标准** | 新功能、需求变更 | → 完整 Requirements→Design→Tests→Tasks→Dev |
| **探索** | 原型、技术调研 | → 允许跳过部分验证，事后 `/ms-retrofit` 补文档 |

### 模式判断指引

- 若任务来自 `ms-dev-tasks`（已有完整文档链）→ **标准模式**
- 若用户描述为 bug/hotfix/配置变更 → **轻量模式**，路由到 `/ms-bugfix`
- 若用户描述为原型/调研/探索/spike → **探索模式**，跳过对抗式验证和追溯标注强制，开发完成后提示运行 `/ms-retrofit`

> **探索模式最小行为验证**：可跳过文档强制（AC/追溯标注/完整 TDD）和对抗式验证，但**不得跳过** S6 绿验（skipped/todo=0）和至少 1 条"目标行为证据"（AC / UT/IT 断言 / `--ui --live` 截图 / 显式豁免）；写入 Commit 1 `Exploration-Mode: true` 尾注便于 `/ms-retrofit` 补 AC。无证据 ⛔ 阻止提交。

> 以下流程为**标准模式**。轻量/探索模式见上述路由。

## 触发条件

用户开始/批量/继续开发任务（v1: T-01/T-01~T-05/F-001/--all；v2 [FUTURE]: TASK-01/TASK-01~TASK-05/FEAT-001/--all）；关键词如"开发任务"、"执行任务"、"开始 T-XX / TASK-XX"、"批量开发"、"继续开发"。

## 运行模式

### 语法

| 指定符 | 示例 | 说明 |
|--------|------|------|
| 单任务 | `T-03`（v1）/ `TASK-03`（v2 [FUTURE]）| 执行单个任务（现有行为） |
| 范围 | `T-01~T-05`（v1）/ `TASK-01~TASK-05`（v2 [FUTURE]）| 执行范围内所有任务 |
| 枚举 | `T-01,T-03,T-07`（v1）/ `TASK-01,TASK-03,TASK-07`（v2 [FUTURE]）| 执行指定任务列表 |
| 功能点 | `F-001`（v1）/ `FEAT-001`（v2 [FUTURE]）| 通过 `关联需求` 字段反查所有关联任务 |
| 用户故事 | `US-001`（v1）/ `STORY-001`（v2 [FUTURE]）| 同上 |
| 全部 | `--all` | 所有 `状态≠已完成` 的任务 |
| 无人值守 | `--headless` | 批量模式 + 全自动决策（fail-fast） |
| 自动提交 | `--auto-commit` | 测试通过自动提交，仅 Blocker 时暂停（与 `--headless` 互斥） |
| 上下文重置 | `--context-reset N` | 每 N 个任务后编排器重置上下文（默认 3，仅批量模式） |
| 跳过审查（🔴 限定） | `--skip-review-reason="<原因>"` | 仅 🔴 任务可用；必须带 reason，否则视为非法参数（详见[对抗式验证](#对抗式验证可选)） |
| 跳过 trace 校验 | `--skip-trace="<原因>"` | 单任务模式关闭 `--affected` 后置校验；必须带 reason，写入 `Skip-Trace-Reason:` 尾注 |
| 外部对抗审查（Phase 4） | `--external-review` | 🟡/🟢/⚪ 层级显式启用 Phase 4 外部对抗审查（🔴 默认开启，无需此 flag） |
| 外部对抗审查跳过（🔴 限定） | `--skip-external-review-reason="<原因>"` | **仅交互模式 + 🔴 任务可用**；跳过 Phase 4 并登记原因；自动标 `EXT_PENDING`，Step 1.5 [D2] 会拦截。`--headless` 下传入此参数视为非法参数 |
| 外部对抗审查轮次 | `--external-rounds N` | 覆盖 Phase 4 默认 `max_rounds=3`；上限 5（对齐 /adversarial-review skill 的 max_rounds） |
| 规范升级回扫 | `--realign` | 已完成任务按新 spec_version 查漏补缺；**独立于 12 种续做信号**，不覆盖原证据，仅追加补齐+`Realigned-From` 尾注。详见 [references/realign.md](references/realign.md)。推荐用户入口：`/ms-pipeline realign`。 |

### 模式对比

| 特性 | 单任务模式 | 批量模式（交互） | `--auto-commit` | `--headless` |
|------|-----------|----------------|----------------|--------------|
| 依赖解析 | 自动补充前置依赖 | 拓扑排序全部任务 | 拓扑排序全部任务 | 拓扑排序 + 前置校验 |
| 断点检测 | 编排器轻量执行 | 编排器轻量执行 | 编排器轻量执行 | 编排器轻量执行 |
| 提交方式 | 子 Agent 内交互确认 | 子 Agent 内交互确认 | 测试通过自动提交 | 自动提交（安全不变量保证） |
| 中断处理 | 子 Agent 内交互 | 子 Agent 内交互 | Blocker 时暂停询问 | fail-fast 终止 + 续做命令 |
| 完成汇总 | 任务完成摘要 | 批量执行报告 | 批量执行报告 | 交付报告 + 检查点文件 |
| 执行模式 | 编排器 + 子 Agent | 编排器 + 子 Agent | 编排器 + 子 Agent | 编排器 + 子 Agent |
| 上下文隔离 | 任务执行隔离 | 每任务独立上下文 | 每任务独立上下文 | 每任务独立上下文 |

### 统一编排流程

所有模式均采用**编排器 + 子 Agent** 架构，主 Agent 只做编排和决策，不直接执行 TDD 循环：

```text
解析任务指定符 → 依赖解析
  ├── 扩展后仅 1 任务 → 启动子 Agent 执行完整流程 → 接收摘要 → 后续步骤
  └── 扩展后 >1 任务 → 拓扑排序 → 逐任务循环（断点检测 → 子 Agent 执行 → 原子提交）→ 汇总
```

**编排器（主 Agent）职责**：解析指定符、依赖解析、断点检测、启动子 Agent、接收摘要、展示结果、调度后续子 Agent（sync/compound/test-run）

**任务子 Agent 职责**：执行开发流程（步骤 1→5），包括 TDD 循环、对抗式验证、Blocker 修复闭环、code-self-describe、Commit 1（代码提交）。Commit 2（文档同步）由编排器调度 /ms-sync 子 Agent 完成。

> 详见 [task-orchestration.md](references/task-orchestration.md)

## 前置条件

- 任务文档：`docs/devdocs/04-dev-tasks.md`
- 任务已定义并包含：关联需求、验收标准、测试方法

## 工作流程

```text
1. 读取任务定义
   ├── 从 04-dev-tasks.md 获取任务详情
   ├── 确认关联的功能点（v1: F-XXX / v2 [FUTURE]: FEAT-XXX）和 AC-XXX
   └── 确认关联的测试用例 UT/IT/E2E-XXX（v1/v2 一致）
           │
           ▼
1.5 Sprint Contract（验收契约协商）
   ├── Test Agent 基于 AC + 当前代码上下文，生成可执行的验收契约
   │   └── 具体到：函数签名、返回值类型、边界条件、异常场景
   ├── 编排器审核契约合理性（过度 vs 不足）
   │   ├── 过度：契约超出 AC 范围 → 裁剪
   │   └── 不足：契约未覆盖 AC 关键行为 → 补充
   └── 契约确认后作为 Test Agent 写测试的输入约束
           │
           ▼
2. 生成骨架代码（自顶向下）
   ├── 接口骨架 + @requirement/@satisfies 标注 [layout.v1 legacy]
   └── 测试骨架 + @verifies/@testcase 标注（基于 Sprint Contract）[layout.v1 legacy]
           │
           ▼
3. 执行开发（统一流程，分级强制）
   ├── 所有层级遵循统一 11 步流程
   ├── 层级标记（🔴🟡🟢⚪）决定各步骤强制程度
   └── 详见 [execution-flow.md](references/execution-flow.md) 强制程度矩阵
           │
           ▼
4. 完成检查
   ├── 基础检查（始终执行）
   │   ├── AC 完备性表：逐条 AC 产出「AC 类型（行为型/视觉型/结构型）/证据类型/代码或测试位置/判定」
   │   │   └── 任一 AC 缺证据 / 违反 AC 类型×证据类型分级矩阵 → ⛔ 禁止继续（补实现/补证据后重跑）
   │   ├── 声称 vs 实际 diff 交叉验证（对比 AC 列表与 git diff）
   │   │   └── 遗漏实现 / 未关联 AC 的大块变更 → ⛔ 禁止继续
   │   ├── 测试通过（skipped/todo 计数=0，豁免见下方约束）
   │   └── Review 要点自查
   │
   ├── 前置验证（按层级默认触发，`--review` 作为"增强"叠加对抗式验证）
   │   ├── 🔴：/ms-verify --impl（前置） + 对抗式验证（自动）
   │   ├── 🟡：/ms-verify --impl（默认必做）
   │   ├── 🟢：
   │   │   ├── 有设计稿 → /ms-verify --impl（AC + 追溯）＋ /ms-verify --ui --impl（设计稿↔实现）两次显式调用
   │   │   └── 无设计稿 → Phase 2-UI 自查 + /ms-verify --impl
   │   └── ⚪：/ms-verify --impl --trace（追溯子集，非完整 AC 语义对齐）
   │
   ├── 对抗式验证 Phase 1~3（🔴 自动触发 / 🟡🟢⚪ 通过 `--review` 手动叠加；`--skip-review-reason` 仅 🔴 可用）
   │   └── 同进程角色切换式自审（内置），产物落 `INT_*` canonical state
   │
   └── **Phase 4：外部对抗审查（embedded-headless 模式）** —— 🔴 默认触发；🟡🟢⚪ `--external-review` 显式触发
       ├── 双通道：T1 codex CLI → T2 codex-mcp（T1/T2 全失败 → fail-fast，不设 Task 子 Agent 兜底）
       ├── 最大轮次：默认 max_rounds=3，`--external-rounds N` 覆盖至 5
       ├── 状态：`EXT_REVIEWED | EXT_PENDING | EXT_UNRESOLVED | EXT_BLOCKED`（见 verification-flow.md 真值表）
       └── `--skip-external-review-reason="<原因>"` 仅 🔴 可用；自动标 `EXT_PENDING`
           │
           ▼
4.5 更新自描述（/code-self-describe --update）
           │
           ▼
5. 提交代码（Commit 1: 代码，遵循 /commit-convention）
           │
           ▼
6. 更新追溯 + 文档提交（/ms-sync → Commit 2: 文档）
        │
        ▼
6.5 更新 AGENTS.md "当前状态"（若存在）
    ├── 更新活跃任务编号（v1: T-XX / v2 [FUTURE]: TASK-XX）
    └── 更新进度统计 (X/Y)
        │
        ▼
7. [推荐] 知识沉淀（/ms-compound）
    ├── 批量模式完成后默认执行（用户可跳过）
    └── 单任务模式：提示用户是否运行 /ms-compound
```

### 步骤状态追踪

11 步执行流程中，每步完成后记录状态标记（S1~S11），用于断点恢复时精确定位。比原有 5 步检查点更精确，减少重复工作。

> 详见 [execution-flow.md](references/execution-flow.md) 步骤状态追踪表

## 代码追溯标注规范（layout.v1 legacy）

> ⚠️ **layout.v2 起改用 [traceability.yml](../pipeline/references/layout/layout-metadata-schema.md#4-traceabilityyml-schematracev1) 外置追溯**。**禁止新增** `@satisfies` / `@verifies` 注释；legacy retained 注释允许保留直到 layout.v3。
>
> **layout.v1 标注类型**（仅历史代码兼容）：`@requirement F-XXX`（功能点）/ `@satisfies AC-XXX`（接口）/ `@verifies AC-XXX`（测试用例）/ `@testcase UT/IT/E2E-XXX`（测试编号）。**强制性**：公共接口 + 测试文件每用例**必须**标注；内部实现可选。

## 自顶向下开发模式

> 先定义骨架，后填充细节。确保追溯链在代码生成时就建立。双 Agent 模型（Test Agent → 红色验证 → Impl Agent → 完成检查+提交）已在上方"工作流程"和 [execution-flow.md](references/execution-flow.md) 强制程度矩阵中完整展开。

### 骨架生成约束

- [ ] **接口骨架必须包含完整签名**（参数、返回值、泛型）
- [ ] **接口骨架必须添加追溯标注**（layout.v1 legacy — layout.v2 起改用 traceability.yml；本约束在 v1 项目仍生效）
- [ ] **未实现方法必须抛出 Error 并注明任务编号**
- [ ] **测试骨架必须使用 skip/todo 标记**
- [ ] **测试骨架必须添加 @verifies 和 @testcase 标注**（layout.v1 legacy）

详见 [skeleton-examples.md](references/skeleton-examples.md)

## 分层 TDD 模式

所有层级遵循统一 11 步执行流程，层级标记仅决定各步骤的**强制程度**：

| 层级 | 标记 | 强制步骤 | 推荐步骤 | 可选步骤 |
|------|------|----------|----------|----------|
| **核心逻辑** (Service/Domain) | 🔴 | 全部 11 步 | — | — |
| **接口层** (Controller/API) | 🟡 | 骨架/实现/绿/AC/自描述/提交 | 测试断言/红/重构/验证 | — |
| **UI 层** (Component/View) | 🟢 | 骨架/测试骨架/实现/绿/AC/自描述/提交；测试断言/红验按 ■\* 条件升级（见 execution-flow） | 验证 | 重构 |
| **基础设施** (DB/Config) | ⚪ | 骨架/实现/绿/AC/自描述/提交 | 测试骨架 | 测试断言/红/重构/验证 |

> **🟢 UI 层补充**：UI 层不是"简化版 🔴"，而是"不同维度的严格"。
> - S1：design_context 存在时，按 [ui-quality-checklist.md](references/ui-quality-checklist.md) 设计稿读取协议获取设计规格
> - S3：Test Agent 在产出测试骨架的同时，必须额外产出 UI 验收清单（生成规则详见同文档）
> - S9：Phase 1/2/3 不变，在 Phase 2 之后新增 Phase 2-UI（UI 质量自查，静态代理指标，详见同文档）
> - 正式设计稿↔实现对比由 `/ms-verify --ui` 负责，Phase 2-UI 仅做代码级自查

### TDD 循环（双 Agent 模型）

```text
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Test Agent│ →  │ 红色验证  │ →  │ Impl Agent│
│ 写骨架+  │     │ 编排器确认│     │ 写实现+  │
│ 写测试   │     │ 测试失败  │     │ 重构     │
└──────────┘     └──────────┘     └──────────┘
```

> **⛔ 信息屏障：Test Agent 不得看到实现代码；Impl Agent 不得看到 03-test-\*.md（只看测试代码文件）**（恢复方式：检查子 Agent prompt 中的文件访问列表）。

> **⛔ 测试不可变：Impl Agent 严禁修改 Test Agent 产出的测试代码。测试失败只能修改实现。疑似测试缺陷须 AskUserQuestion 确认后回退 Test Agent 修复。**

> 详见 [execution-flow.md](references/execution-flow.md) 统一任务执行流程 + 强制程度矩阵

## 编排规范（子 Agent 调度）

**所有模式（含单任务）的开发执行和技能调用，必须通过 Task tool 启动子 Agent**：

| 阶段 | 被调度内容 | 调度方式 |
|------|-----------|----------|
| **验收契约** | Test Agent：Sprint Contract 生成 → 编排器审核 | Test Agent 产出 + 编排器轻量审核 |
| **测试编写** | Test Agent：骨架 + 测试代码（约束于 Contract） | Task tool 子 Agent |
| **红色验证** | 运行测试确认失败 | 编排器轻量执行 |
| **实现编写** | Impl Agent：实现 + 重构 | Task tool 子 Agent |
| 前置验证 | `/ms-verify --impl` | Task tool 子 Agent |
| UI 对齐 | `/ms-verify --ui` | Task tool 子 Agent |
| 追溯同步 | `/ms-sync` | Task tool 子 Agent |
| 知识沉淀 | `/ms-compound` | Task tool 子 Agent |
| 全量测试 | `/ms-test-run` | Task tool 子 Agent |

### 调度原则

1. **上下文隔离 + 信息屏障**：子 Agent 自行读取文档；Test Agent 和 Impl Agent 可读范围严格隔离（详见编排隔离约束）
2. **摘要传递**：只接收 YAML 摘要，`test_defects` 非空时触发用户确认
3. **测试不可变**：Impl Agent 完成后 diff 测试文件，有变更即为 Blocker
4. **主 Agent 禁止直接执行 TDD**：编排器不写代码——红色验证和断点检测的轻量文件扫描除外

## Skill 协作

| 阶段 | 协作 Skill | 说明 |
|------|-----------|------|
| 写业务代码 | `/code-quality` | MTE 原则、依赖注入、避免过度设计 |
| 写测试代码 | `/testing-guide` | 断言质量、变异测试、覆盖率 |
| UI 实现 | `/ui-orchestrator` | 无障碍、动画、布局约束 |
| 实现审查 | `/ms-verify --impl` | **按层级默认必做**：🔴/🟡 全量 AC；⚪ 仅 `--trace` 子集 |
| UI 对齐 | `/ms-verify --ui --impl` | **按层级默认必做**：🟢 有设计稿时与 `/ms-verify --impl` **并行各跑一次**（不得合并为单次调用，`--ui --impl` 仅覆盖设计稿↔实现一维）；无设计稿降级为 Phase 2-UI 自查 |
| 完成验证 | `/code-quality` + `/testing-guide` | 对抗式验证（🔴 自动 / 其他层级 `--review` 叠加） |
| 完成检查 | `/code-self-describe` | 更新模块自描述（--update） |
| 代码提交 | `/git-safety` | 使用 git mv/rm 处理文件 |
| 提交信息 | `/commit-convention` | 遵循项目提交规范 |
| 依赖解析 | `/ms-dev-tasks` | 读取任务依赖关系和状态 |
| 任务完成 | `/ms-sync` | 后续：更新追溯矩阵（追溯同步） |
| 知识沉淀 | `/ms-compound` | 推荐：sync 后提取经验模式（批量模式默认执行） |
| 全量测试 | `/ms-test-run` | 批量完成后 `--trace`（全量+追溯）；单任务完成后 `--affected`（受变更影响测试），affected 无匹配时回退 `--trace` |
| 外部对抗审查（契约复用） | `/adversarial-review` | **dev-workflow S9 Phase 4 仅复用其 `references/external-reviewer-integration.md` 底层 T1/T2 双通道 + 熔断协议**（不使用 T3 Task 子 Agent 兜底），不直接调用整个 multi-turn skill（避免 AskUserQuestion 阻塞）。Phase 4 调度器以 embedded-headless 模式运行；`/adversarial-review` 仍可被用户独立调用做交互式审查 |

## 约束

### 分层 TDD 约束

- [ ] **所有层级遵循统一执行流程（S1~S12 + S1.5 Contract）**（层级标记仅决定强制程度）
- [ ] **核心逻辑任务必须标记 🔴 强制 TDD**（全部步骤 ■ 必须）
- [ ] **Test Agent 先写测试，Impl Agent 后写实现**（物理隔离）
- [ ] **核心逻辑任务禁止在测试通过前提交**
- [ ] 接口层任务标记 🟡 推荐 TDD；**一旦产出测试骨架/测试文件**，S4 断言与 S5 红验升级为必做（■*）
- [ ] UI 层任务标记 🟢 **最小 TDD（UI 清单 + 状态断言）**；S3 测试骨架必做，存在骨架即触发 S4/S5 ■\* 条件升级；清单 Blocker 项必须对应证据（见 ui-quality-checklist.md）
- [ ] 基础设施任务标记 ⚪ 推荐测试骨架（骨架产出后断言仍为可选）
- [ ] **Test Agent 断言来自行为契约 + 03-test-\*.md，Impl Agent 禁止读取 03-test-\*.md**
- [ ] **Impl Agent 严禁修改 Test Agent 产出的测试代码**（疑似缺陷须 AskUserQuestion 确认）
- [ ] TDD 任务必须包含红-绿-重构三步骤（跨越 Test Agent → 编排器 → Impl Agent）
- [ ] □/○ 步骤跳过时必须在提交信息中记录原因

### 完成检查约束

- [ ] **S8 必须产出 AC 完备性表**（逐条 AC：编号/**AC 类型**（行为型/视觉型/结构型，必填）/证据类型/代码或测试位置/判定）
- [ ] **任一 AC 缺失有效证据 / 违反 AC 类型×证据类型分级矩阵 → ⛔ 禁止继续**（恢复方式：补实现或补测试后重新生成证据表）
- [ ] **Phase 4 `ext_review_state` 必须为 `EXT_REVIEWED`（🔴 任务）或非 🔴 任务未触发 Phase 4 时 `EXT_REVIEWED`/空** 才能进入 Commit 1；`EXT_UNRESOLVED` / `EXT_BLOCKED` ⛔ 阻塞（恢复方式见 [verification-flow.md 真值表](references/verification-flow.md)）
- [ ] **声称 vs 实际 diff 交叉验证必做**（所有层级 S8 必做，不再是 --review 才触发）
- [ ] **测试通过判定排除 skipped / todo**（skipped/todo 计数 > 0 → ⛔ 禁止继续，除非任务文档显式豁免并记录原因）
- [ ] **Review 要点自查完成**
- [ ] 代码追溯标注完整
- [ ] 代码分支覆盖分析完成（可选，**补充性质**，使用 `/testing-guide` 分支分析；业务逻辑分支应回溯为 AC 对应的正式测试）

> **AC 完备性表模板、AC 类型分类（行为型/视觉型/结构型）、AC 类型 × 证据类型分级矩阵、Step 1.5 [A] 可复核判据** 见 [verification-flow.md AC 完备性章节](references/verification-flow.md)。违反分级表 → S8 直接 ⛔ 判失败（恢复方式：补测试断言或走豁免枚举）。

## 对抗式验证（可选）

> 以不同角色视角审查代码，模拟 "开发 → 审查 → 测试" 的多人协作模式。

### 触发条件

> **层级判定**：任务层级标记（🔴🟡🟢⚪）来自 `04-dev-tasks.md` 中的任务定义，由 `/ms-dev-tasks` 在任务拆分时根据任务分层规则分配。

| 任务层级 | 默认前置验证（按层级最小必做） | Phase 1~3 自审 | Phase 4 外部对抗 | 手动控制 |
|---------|-------------------------------|---------------|------------------|---------|
| 🔴 核心逻辑 | `/ms-verify --impl` | **自动触发** | **自动触发**（走 T1 → T2 降级链，T1/T2 全失败 → fail-fast） | `--skip-review-reason="<原因>"` 跳过 Phase 1~3（见下方约束）；`--skip-external-review-reason="<原因>"` 跳过 Phase 4（仅交互模式）；`--external-rounds N` 覆盖 max_rounds；`--impl` 前置验证不可跳过 |
| 🟡 接口层 | `/ms-verify --impl` | 不触发 | 不触发 | `--review` 叠加 Phase 1~3；`--external-review` 叠加 Phase 4（独立判定） |
| 🟢 UI 层 | 有设计稿 → `/ms-verify --impl` + `/ms-verify --ui --impl`（两次调用）；无设计稿 → Phase 2-UI 自查 + `/ms-verify --impl`（降级） | 不触发 | 不触发 | `--review` 叠加 Phase 1~3；`--external-review` 叠加 Phase 4 |
| ⚪ 基础设施 | `/ms-verify --impl --trace`（仅追溯子集） | 不触发 | 不触发 | `--review` 叠加 Phase 1~3；`--external-review` 叠加 Phase 4 |

**设计原则**：

- 前置验证"按层级最小必做"，保证每层都有独立验证者（非 🔴 默认不再无验证）。
- Phase 1~3（内置角色演绎）与 Phase 4（外部独立审查）**独立判定**：各自维护 `INT_*` / `EXT_*` canonical state；`--review` 控 Phase 1~3，`--external-review` 控 Phase 4。
- 前置验证失败（Blocker）⛔ 阻塞 Commit 1，不因"未加 --review"而放行。

**Skip 参数收紧（均仅作用于 🔴）**：

| 参数 | 作用对象 | 约束 | 自动标记 |
|------|---------|------|---------|
| `--skip-review-reason="<原因>"` | Phase 1~3 | 必须带 reason；写入 Commit 1 `Skip-Review-Reason:` 尾注 | `INT_PENDING`，Step 1.5 [D1] 拦截至补跑 |
| `--skip-external-review-reason="<原因>"` | Phase 4 | 必须带 reason；**仅交互模式**（`--headless` 下视为非法）；写入 `Skip-External-Review-Reason:` 尾注 | `EXT_PENDING`，Step 1.5 [D2] 拦截至补跑 |
| 双 skip 同时 | 双 | ⛔ **非法参数组合**（不设例外通道） | — |

> Phase 4 详细调用契约（T1/T2 双通道、max_rounds、真值表、L2 权威证据协议）见 [verification-flow.md Phase 4 章节](references/verification-flow.md)。Phase 1~3 验证流程（代码质量/测试完备/UI 自查/综合报告/AC↔diff 交叉验证）同文件。

### 对抗式验证约束

- [ ] **Blocker 必须修复后才能提交**；每个 Phase 声明审查角色；结果分级（Blocker/Suggestion）
- [ ] 核心逻辑（🔴）Phase 1~3 + Phase 4 均默认触发；修复 Blocker 后重新运行验证
- [ ] Skip 参数遵循上表（必须带 reason；🟡/🟢/⚪ 使用 skip 参数视为非法）
- [ ] 双 skip 组合 → 非法参数组合直接拒绝

### 依赖解析约束

- [ ] **执行前必须完成依赖解析**
- [ ] **循环依赖必须报错终止**（列出循环路径）
- [ ] **已完成依赖跳过**，不重复执行
- [ ] 自动补充未完成的前置依赖到执行队列
- [ ] "进行中"依赖通过 AskUserQuestion 询问用户

### 原子提交约束

- [ ] **每个任务独立提交**，不跨任务合并
- [ ] **代码提交和文档提交分离**（Commit 1: 代码，Commit 2: 文档状态 + trace 同步结果）
- [ ] **提交前必须通过完成检查**
- [ ] 提交后更新 04-dev-tasks*.md 任务状态为 `已完成`
- [ ] `--single-commit` 可将代码+文档合并为单次提交

### 断点续做约束

- [ ] **每个任务开始前执行状态检测**（6 步流水线：Step 1 / 1.5 证据复核 / 2~5）
- [ ] **不相关变更必须警告用户**（AskUserQuestion：stash/忽略/终止）
- [ ] **存在完成痕迹的任务必须通过 Step 1.5 五项证据复核才允许跳过**：[A] AC 表可复核 / [B] 测试无 skip/todo / [C] trace 已同步 / [D1] Phase 1~3 内置对抗式验证证据（🔴 必查，`Skip-Review-Reason` 不得作为放行）/ [D2] Phase 4 外部对抗审查证据（🔴 必查，`ext_review_state=EXT_REVIEWED` 且 L2 yaml 可读；`Skip-External-Review-Reason` 不得作为放行）/ [E] 后置测试证据（`Skip-Trace-Reason` 不得作为放行）
- [ ] **Git 历史有 code+doc commit 但任务状态≠已完成**：不再直接跳过，改为进入 Step 1.5 证据复核路径
- [ ] 旧任务（前版本完成，无 A/D1/D2/E 产物）→ AskUserQuestion：复核续做 / 登记豁免原因 / 终止
- [ ] 进行中任务分析续做起点（精确定位：S1~S12 + S1.5，含续做 Agent 判定）
- [ ] 文档状态 + 证据复核 + Git 历史 + 工作区四重验证

> 详见 [task-orchestration.md](references/task-orchestration.md)

### `--auto-commit` 约束

- [ ] **交互模式（非 headless），用户仍可观察过程**
- [ ] **测试全部通过且无 Blocker 时自动提交，不询问**
- [ ] **出现 Blocker 或测试失败时暂停询问**
- [ ] 与 `--headless` 互斥（`--headless` 已包含自动提交语义）
- [ ] 安全不变量同 `--headless`：测试未通过不提交、Blocker 未解决不提交

### 记忆文件同步约束

- [ ] **任务完成后检查项目根目录是否存在 AGENTS.md**
- [ ] **仅允许更新 `## 当前状态` 章节**（活跃任务编号、进度统计）
- [ ] **禁止修改结构性章节**（Project Overview、Skill Architecture、Conventions 等由 /agent-memory 管理）
- [ ] CLAUDE.md 通过 @AGENTS.md 自动导入，无需同步
- [ ] 仅做文本替换，不调用 /agent-memory
- [ ] 格式须与 `/agent-memory` 模板保持一致
- [ ] 若 AGENTS.md 不存在则跳过

### 编排隔离约束

- [ ] **每任务双 Agent：Test Agent（骨架+测试）→ 红色验证 → Impl Agent（实现+重构）**
- [ ] **Test Agent 禁读 src/ 已有实现；Impl Agent 禁读 03-test-\*.md、01-requirements.md**
- [ ] **编排器在 Impl Agent 完成后 diff 测试文件，有变更即为 ⛔ Blocker**
- [ ] **主 Agent 只做编排和决策，不直接执行 TDD**
- [ ] **依赖扩展后 >1 任务时，自动升级为批量编排**

### 全量测试验证约束

- [ ] **批量模式完成后必须调用 `/ms-test-run --trace`**（全量 + 追溯完整性）
- [ ] **单任务模式完成后必须调用 `/ms-test-run --affected`**（受变更影响的测试，基于 git diff，见 `/ms-test-run` SKILL）
   - `--affected` 无匹配时（ms-test-run 返回"建议运行全量"）→ 回退 `/ms-test-run --trace`
   - 单任务不得完全跳过该校验，除非显式 `--skip-trace="<原因>"` 并登记
- [ ] **`--skip-trace` 收紧**：理由必须写入 Commit 1 `Skip-Trace-Reason:` 尾注，批量交付报告单列（便于事后补跑）
- [ ] **使用 `--skip-trace` 的任务自动标 `postcheck_pending`**，不得进入"已完成可跳过"态（恢复方式：补跑 `/ms-test-run --affected` 或 `--trace`，Step 1.5 [E] 才放行）
- [ ] 全量/受影响测试失败不回滚已提交任务（原子提交已落盘）
- [ ] 交互模式：AskUserQuestion 询问是否修复失败测试
- [ ] --headless / --auto-commit 模式：记录警告到交付报告，不中断

### 无人值守约束（--headless）

- [ ] **工作区必须洁净**（启动前 + 每任务 Commit 2 后校验）
- [ ] **前置依赖不得处于"进行中"状态**（否则 fail-fast）
- [ ] **fail-fast 后输出续做命令**
- [ ] **修复过程中标注不得删减**
- [ ] **修复过程中断言数量不得减少**
- [ ] **Suggestion 自动跳过**（除非 `--fix-suggestions`）
- [ ] **绝不推送远程**

> 详见 [auto-mode.md](references/auto-mode.md)

## 任务完成流程

Impl Agent 完成后，编排器执行：测试文件不可变校验（diff）→ AC 验证 → 对抗式验证 → 自描述更新 → 提交决策 → 原子提交（Commit 1 代码 + Commit 2 文档）

> 详见 [execution-flow.md](references/execution-flow.md) 完整步骤和强制矩阵
## 提交信息格式

遵循 `/commit-convention` 规范，格式如下：

> ℹ️ 提交标题与 `关联` 字段按项目 `AGENTS.md devdocs.id_scheme` 选择：v1 用 `T-XX/F-XXX/US-XXX`，v2 [FUTURE] 用 `TASK-XX/FEAT-XXX/STORY-XXX`。`AC/UT/IT/E2E` 编号双轨一致。

```markdown
<type>(T-XX): <任务名称>   # v1；v2 [FUTURE] 用 (TASK-XX)

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX        # v1；v2 [FUTURE] 用 FEAT-XXX/STORY-XXX
测试: UT-XXX, IT-XXX 通过
External-Review-Verdict: <EXT_REVIEWED | EXT_PENDING | EXT_UNRESOLVED | EXT_BLOCKED>（Phase 4 触发时必填，含 rounds 和 health_scores）
External-Review-Channel: <T1 | T2 | none>（非状态字段，Phase 4 触发时记录实际通道）
Skip-Review-Reason: <仅 🔴 任务使用 --skip-review-reason 时填写；其他情况省略此行>
Skip-External-Review-Reason: <仅 🔴 任务使用 --skip-external-review-reason 时填写>
Skip-Trace-Reason: <单任务使用 --skip-trace 时填写；其他情况省略此行>
Exploration-Mode: <探索模式设为 true 并登记证据/豁免原因；其他情况省略此行>
```

**合法 `External-Review-Verdict` 枚举**：`EXT_REVIEWED` / `EXT_PENDING` / `EXT_UNRESOLVED` / `EXT_BLOCKED`。禁用 `CONVERGED` / `DEGRADED` / `SKIPPED` 等非 canonical 词汇。

**type 类型**：feat | fix | refactor | test | docs | chore

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-dev-workflow
status: success | failed
summary:
  headline: "T-03 开发完成，测试全部通过"
  details:
    task: T-XX           # v1；v2 [FUTURE] 用 TASK-XX
    commits:
      code: "abc1234"
      docs: "def5678"
    test_summary:
      passed: X
      failed: 0
      coverage: "XX%"
    blockers_resolved: 0
    suggestions_skipped: 0
    ac_verified: [AC-001, AC-002]
    decision_log: []  # 关键决策事件（Contract 审核、重试、Blocker 修复等）
blockers: []
output_files: []
new_ids: {}
next_recommended:
  skill: ms-sync
```

## 参考资料

- [skeleton-examples.md](references/skeleton-examples.md) - 接口/测试骨架示例
- [execution-flow.md](references/execution-flow.md) - 任务执行流程详解
- [verification-flow.md](references/verification-flow.md) - 对抗式验证流程详解
- [task-orchestration.md](references/task-orchestration.md) - 多任务编排（批量/依赖/断点续做）
- [auto-mode.md](references/auto-mode.md) - 无人值守模式详解
