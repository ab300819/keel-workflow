---
name: ms-dev-workflow
description: Execute development tasks with skeleton-first approach and layered TDD. Supports single task, batch execution (by range, feature, user story), dependency resolution, and breakpoint resume. Includes optional adversarial verification and unattended mode (无人值守，由用户明示授权触发). Triggers on "execute task", "start T-XX", "batch", "resume", "开发任务", "执行任务", "批量开发", "继续开发", "开始写代码", "开始开发", "无人值守", "别问我". NOT for task breakdown (use ms-dev-tasks), bug fixes (use ms-bugfix), or non-DevDocs plan/prompt-driven development (use dev-flow).
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
migration: /ms-pipeline realign --scope=layout
spec_version: 3.1
spec_version_notes: |
  1.1 = P0-A 文档收敛 + 累计审计删减 (Phase 1)
        P1 S9 并行化、P2 批量 Batch-Id trailer 标记 [FUTURE]，待 Phase 2 实施；
        并行化前置依赖 worktree 隔离协议（工作区所有权/文档 SSOT 合并/review-drain 回收），
        触发 = 真实并行需求（2026-07-22 吸收评审结论，见 docs/workflows.md § 与 superpowers 共存）
  2.0 = 重新定位(代码SSOT/文档记忆)+ review_profile 三档替代层级 + 质量地板恒定 + 独立审查延后 drain + review_pending 状态(Plan A)
  3.0 = 修复延后外审空 diff(Phase 4 按 inline/drain 分离 diff 源)+ 删 skip 参数族
        (2 flag / INT_PENDING·EXT_PENDING 2 enum 值 / 2 trailer / 双 skip 禁令)+ 删最低发现数门槛
  3.1 = 删 External-Review-Channel trailer(派生自 L2 external_review_channel_used,无门禁消费者)
        + 删与「分层 TDD 模式」档位表重复的「触发条件」表
---

# 开发工作流

- 共享约束 SSOT：[../_shared/constraints.md](../_shared/constraints.md)

> 本 skill 遵循共享约束 SSOT：门控标记、yaml-summary-v1、Task 委托、用户确认、Recovery 格式、只读 / dry-run、FUTURE 三态、realign / spec_version 见 [skills/_shared/constraints.md](../_shared/constraints.md)。本文件只描述 ms-dev-workflow 私有规则（11 步流程、Sprint Contract、headless 安全、Step 1.5 五项证据、Phase 1-4 外部审查、EXT 状态机、Commit 1/2 双 commit）。
>
> ℹ️ 编号双轨：v1 项目用 `T-XX`，v2 项目 [FUTURE] 用 `TASK-XX`。详见 [id-scheme-implementation.md](../pipeline/references/layout/id-scheme-implementation.md)。
>
> ℹ️ 输入路径双轨：v1 读 `04-dev-tasks.md` 找任务；v2 [FUTURE] 读 `tasks/<ID>.md` + 写回状态到该文件。详见 [folder-organization-implementation.md](../pipeline/references/layout/folder-organization-implementation.md)。

> **权威文件唯一原则**（spec_version 1.1 起强制）：
> - Phase 4 / 并行调度 / `diff_hash` / 重跑机制 → [verification-flow.md](references/verification-flow.md) 唯一权威
> - Step 1.5 各分支 / Batch-Id 识别 → [task-orchestration.md](references/task-orchestration.md) 唯一权威
> - Phase 2-UI 审查清单 → [ui-quality-checklist.md](references/ui-quality-checklist.md) 唯一权威
> - review_profile / drain / review_pending → [verification-flow.md](references/verification-flow.md) + [task-orchestration.md](references/task-orchestration.md)
> - 风险分类器(review_profile 提议)→ /ms-dev-tasks
> - 其他文件（SKILL.md / auto-mode.md / execution-flow.md）**仅允许 2-3 行指针引用**，严禁重复转述。违反此原则视为复杂度退化，必须 revert。

> 视角：资深开发者 — 务实优先，不过度设计，测试先行，提交原子化。

## 快速开始

执行开发任务，采用骨架先行 + 分层 TDD。常见用法：`/ms-dev-workflow T-03`（单任务）、`T-01~T-05`（批量）。拆分任务用 `/ms-dev-tasks`，修 Bug 用 `/ms-bugfix`。支持中英文提问，统一中文回复。

## 模式选择

| 模式 | 适用场景 | 流程 |
|------|---------|------|
| **轻量** | Bug fix、小改动、配置变更 | → `/ms-bugfix`（已有） |
| **标准** | 新功能、需求变更 | → 完整 Requirements→Design→Tests→Tasks→Dev |
| **探索** | 原型、技术调研 | → 允许跳过部分验证，事后由用户确认目标行为后补建 AC |

> **探索模式最小行为验证**：可跳过文档强制（AC/追溯标注/完整 TDD）和对抗式验证，但**不得跳过** S6 绿验（skipped/todo=0）和至少 1 条"目标行为证据"（AC / UT/IT 断言 / `--ui --live` 截图 / 显式豁免）；写入 Commit 1 `Exploration-Mode: true` 尾注，便于事后由用户确认目标行为后补建真实 AC。无证据 ⛔ 阻止提交。

## 触发条件

用户开始/批量/继续开发任务（v1: T-01 / T-01~T-05 / F-001 / 「把剩下的都跑完」；v2 [FUTURE]: TASK-01 / TASK-01~TASK-05 / FEAT-001）；关键词如"开发任务"、"执行任务"、"开始 T-XX"、"批量开发"、"继续开发"、"无人值守"。

## 运行模式

### 语法

| 指定符 | 示例 | 说明 |
|--------|------|------|
| 单任务 | `T-03`（v1）/ `TASK-03`（v2 [FUTURE]）| 执行单个任务（现有行为） |
| 范围 | `T-01~T-05`（v1）/ `TASK-01~TASK-05`（v2 [FUTURE]）| 执行范围内所有任务 |
| 枚举 | `T-01,T-03,T-07`（v1）/ `TASK-01,TASK-03,TASK-07`（v2 [FUTURE]）| 执行指定任务列表 |
| 功能点 | `F-001`（v1）/ `FEAT-001`（v2 [FUTURE]）| 通过 `关联需求` 字段反查所有关联任务 |
| 用户故事 | `US-001`（v1）/ `STORY-001`（v2 [FUTURE]）| 同上 |
| 轻量入口 | 直接描述任务 + 验收标准 | 无 04 文档也可进入:按 [inline-entry.md](references/inline-entry.md) 物化 stub(01 AC 条目 + 04 任务条目)后转单任务路径;review_profile 下限 guarded |

> **协议参数不在用户面。** 无人值守 / 自动提交 / 审查档位 / 外部审查轮次 / 上下文重置 / 单次提交 / 跳过追溯，都由编排层从你的自然语言归一化后下传（[`task/intent-normalization`](../_shared/constraints.md)），你不需要记参数名。
>
> **授权要你开口**：无人值守和自动提交不是默认行为，须明说；反过来，超出你授权范围的不可逆动作一律在发生时就地确认（[`task/consent-at-action`](../_shared/constraints.md)）。

### 统一编排流程

所有模式均采用**编排器 + 子 Agent**：编排器解析指定符、依赖/断点、启动子 Agent、接收 yaml-summary-v1、调度 `/ms-sync`/`/ms-test-run`/`/ms-compound`；任务子 Agent 执行 TDD、对抗式验证、Blocker 修复、自描述和 Commit 1。扩展后 >1 任务时拓扑排序并逐任务原子提交。通用 Task 委托协议见共享约束 §3，批量/续做细节见 [task-orchestration.md](references/task-orchestration.md)。

## 前置条件

- 任务文档：`docs/devdocs/04-dev-tasks.md`,且任务已定义并包含:关联需求、验收标准、测试方法
- **或**直接给出任务定义与验收标准（无需参数）:按 [inline-entry.md](references/inline-entry.md) 物化 stub 后进入 S1;Test Agent 输入中 02/03 字段标 `—(inline)`,以 S1.5 Sprint Contract 为测试输入约束

## 工作流程

本文件保留 S1~S11 骨架；S12 文档同步/知识沉淀属于 Commit 2 后置流程，详见 [execution-flow.md](references/execution-flow.md)。

| 步骤 | 质量门 |
|------|--------|
| S1 读取任务定义 | 从 `04-dev-tasks.md` 获取任务、F/AC/UT/IT/E2E 关联 |
| S1.5 Sprint Contract | Test Agent 基于 AC + 当前代码上下文生成可执行验收契约（函数签名、返回值类型、边界条件、异常场景）；编排器裁剪过度契约、补足遗漏契约，确认后作为测试输入约束 |
| S2-S3 骨架 | 接口骨架 + 测试骨架；layout.v1 legacy 使用 `@requirement`/`@satisfies`/`@verifies`/`@testcase`，layout.v2 改用 `traceability.yml` |
| S4-S7 红绿重构 | Test Agent 写断言；编排器红验；Impl Agent 实现、绿验、重构；绿验必须 `skipped/todo=0`；注释遵循 [`/code-quality` 注释规范](../code-quality/SKILL.md#注释规范)（禁止变更日志式/来源记录式注释，含修复循环），日志遵循 [日志规范](../code-quality/SKILL.md#日志规范)（安全红线/级别纪律/禁 log-and-throw）|
| S8 完成检查 | 质量地板 5 条 + AC 完备性表（fast 证据摘要 / audit 完整 AC 类型×证据矩阵）+ 声称 vs 实际 diff 交叉验证；缺证据或未关联大块 diff → ⛔ 禁止继续 |
| S9 前置验证 | guarded/audit `/ms-verify --impl`；fast 仅质量地板（不跑前置验证）；🟢 UI 任务有设计稿时另跑 `/ms-verify --ui --impl` 对齐设计稿（不随 profile 变） |
| S9 Phase 1~3 | 内置角色演绎对抗式验证（独立审查）：**audit inline fail-fast**；**fast/guarded 延后**到 `/ms-verify --review-drain`，任务期间标 `review_pending`；`--review` 可临时叠加 inline |
| S9 Phase 4 | 外部对抗审查 embedded-headless（独立审查）：**audit inline**；**fast/guarded 延后** drain；T1 codex CLI → T2 codex-mcp，T1/T2 全失败 fail-fast；状态 `EXT_REVIEWED`/`EXT_UNRESOLVED`/`EXT_BLOCKED`（与 `review_pending` 区分） |
| S10 自描述 | `/code-self-describe --update`（`workspace_context.capabilities.code_metadata_write_policy` 为 `explicit_opt_in` 时**默认跳过**——自描述产物写在代码目录内，违反零污染红线。跳过须在 yaml 摘要里以 ℹ️ 记录 `skipped: code_metadata_write_policy=explicit_opt_in`。用户显式 `--force-code-docs` 才执行） |
| S11 Commit 1 | 代码提交，遵循 `/commit-convention`，Phase 4 触发时必须写 `External-Review-Verdict` |
| Commit 2 后置 | `/ms-sync` 更新 trace + 文档提交；若有 AGENTS.md 仅更新“当前状态”；批量默认 `/ms-compound` |

步骤状态（S1~S11 + S1.5）用于断点恢复；详细矩阵、S12 后置同步和状态标记见 [execution-flow.md](references/execution-flow.md)。

## 代码追溯标注规范（layout.v1 legacy）

> ⚠️ **layout.v2 起改用 [traceability.yml](../pipeline/references/layout/layout-metadata-schema.md#4-traceabilityyml-schematracev1) 外置追溯**。**禁止新增** `@satisfies` / `@verifies` 注释；legacy retained 注释允许保留直到 layout.v3。
>
> **layout.v1 标注类型**（仅历史代码兼容）：`@requirement F-XXX`（功能点）/ `@satisfies AC-XXX`（接口）/ `@verifies AC-XXX`（测试用例）/ `@testcase UT/IT/E2E-XXX`（测试编号）。**强制性**：公共接口 + 测试文件每用例**必须**标注；内部实现可选。

## 自顶向下开发模式

> 先定义骨架，后填充细节。确保追溯链在代码生成时就建立。双 Agent 模型（Test Agent → 红色验证 → Impl Agent → 完成检查+提交）已在上方"工作流程"和 [execution-flow.md](references/execution-flow.md) 强制程度矩阵中完整展开。

### 骨架生成约束

判据清单见 [skeleton-examples.md](references/skeleton-examples.md)（接口签名完整性 / 追溯标注 / 未实现方法抛错 / 测试骨架 skip 标记）。

## 分层 TDD 模式

所有任务遵循统一 11 步执行流程 + 5 条质量地板(恒定 inline);`review_profile` 只决定**独立审查(Phase 1~3 + Phase 4)的时机**:

| review_profile | 触发 | 双 Agent | 质量地板 | 前置验证 | Phase 1~3 | Phase 4 | 提交状态 |
|------|------|:---:|:---:|:---:|------|------|------|
| **fast**(默认) | 低风险(见风险分类器) | ✓ | ✓ | — | 延后 drain | 延后 drain | `review_pending` |
| **guarded** | 中风险 | ✓ | ✓ | `/ms-verify --impl` inline | 风险触发 inline 否则延后 | 延后 drain | `review_pending` |
| **audit** | 高风险 | ✓ | ✓ | `/ms-verify --impl` inline | **inline fail-fast** | **inline fail-fast** | 审过才提交 |

> 详细判据见 [verification-flow.md](references/verification-flow.md);风险分类器信号判据 → /ms-dev-tasks(初始提议);执行期复核(只升不降)→ [task-orchestration.md](references/task-orchestration.md);共享定义见 [../_shared/constraints.md](../_shared/constraints.md)。
> 旧 🔴🟡🟢⚪ 层级标签**降级为风险分类器的输入信号之一**,不再独立决定流程强度。

> 各 review_profile 的 S1~S11 强制程度差异详见 [execution-flow.md](references/execution-flow.md)。UI 任务的 Phase 2-UI 自查仍按 [ui-quality-checklist.md](references/ui-quality-checklist.md)。

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
| 写业务代码 | `/code-quality` | MTE 原则、依赖注入、避免过度设计、注释规范、日志规范 |
| 写测试代码 | `/testing-guide` | 断言质量、变异测试、覆盖率 |
| UI 实现 | `/ui-orchestrator` | 无障碍、动画、布局约束 |
| 实现审查 | `/ms-verify --impl` | **guarded/audit 默认必做（全量 AC）；fast 不跑前置验证（仅质量地板）** |
| UI 对齐 | `/ms-verify --ui --impl` | **UI 任务有设计稿时**与 `/ms-verify --impl` **并行各跑一次**（不得合并为单次调用，`--ui --impl` 仅覆盖设计稿↔实现一维）；无设计稿降级为 Phase 2-UI 自查（不随 profile 变） |
| 完成验证 | `/code-quality` + `/testing-guide` | 对抗式验证：audit inline 自动 / fast,guarded 延后 drain；`--review` 临时叠加 |
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

- [ ] **audit/guarded 任务强制 test-first**（双 Agent 红绿 + 测试冻结）；**质量地板 5 条所有 profile 恒定**
- [ ] **Test Agent 先写测试，Impl Agent 后写实现**（物理隔离）
- [ ] **Test Agent 断言来自行为契约 + 03-test-\*.md，Impl Agent 禁止读取 03-test-\*.md**
- [ ] **Impl Agent 严禁修改 Test Agent 产出的测试代码**（疑似缺陷须 AskUserQuestion 确认）
- [ ] □/○ 步骤跳过时必须在提交信息中记录原因

### 完成检查约束

- [ ] **S8 必须产出 AC 完备性表**（逐条 AC：编号/**AC 类型**（行为型/视觉型/结构型，必填）/证据类型/代码或测试位置/判定）
- [ ] **任一 AC 缺失有效证据 / 违反 AC 类型×证据类型分级矩阵 → ⛔ 禁止继续**（恢复方式：补实现或补测试后重新生成证据表）
- [ ] **Phase 4 `ext_review_state` 必须为 `EXT_REVIEWED`（audit 任务 inline 触发）或未触发 Phase 4 时 `EXT_REVIEWED`/空** 才能进入 Commit 1；fast/guarded 延后 drain 期间提交状态为 `review_pending`；`EXT_UNRESOLVED` / `EXT_BLOCKED` ⛔ 阻塞（恢复方式见 [verification-flow.md 真值表](references/verification-flow.md)）
- [ ] **声称 vs 实际 diff 交叉验证必做**（所有层级 S8 必做，不再是 --review 才触发）
- [ ] **测试通过判定排除 skipped / todo**（skipped/todo 计数 > 0 → ⛔ 禁止继续，除非任务文档显式豁免并记录原因）

> **AC 完备性表模板、AC 类型分类（行为型/视觉型/结构型）、AC 类型 × 证据类型分级矩阵、Step 1.5 [A] 可复核判据** 见 [verification-flow.md AC 完备性章节](references/verification-flow.md)。违反分级表 → S8 直接 ⛔ 判失败（恢复方式：补测试断言或走豁免枚举）。

## 质量地板(所有 review_profile 恒定 inline,不可降)

无论档位高低,5 条不变量永远 inline 生效(定义见 [../_shared/constraints.md](../_shared/constraints.md)):绿验 `skipped/todo=0` / 测试冻结 / 声称vs实际 diff 一致 / 行为型 AC 至少 1 条独立证据 / 受影响测试后置。

> **三类机制区分(关键,勿混)**:
> 1. **质量地板**(上述 5 条)——所有档 inline。
> 2. **前置验证 `/ms-verify --impl`**(AC↔实现语义一致)——属"前置验证门",Blocker inline 阻塞提交;guarded/audit 跑,fast 不跑。
> 3. **独立对抗审查**(Phase 1~3 + Phase 4)——**唯一可延后**的部分,fast/guarded 延后到 drain,audit inline。
>
> "review_profile 只改独立审查时机"成立:地板与前置验证永远 inline,不在延后范围。

## 对抗式验证（可选）

> 以不同角色视角审查代码，模拟 "开发 → 审查 → 测试" 的多人协作模式。

> **与 review_profile 的关系（重要）**：本节描述的是独立审查的**机制**（Phase 1~3/4、INT/EXT 状态），其**触发时机**由 `review_profile` 决定——档位表见上文「分层 TDD 模式」，本节不重复。

**设计原则**：

- 前置验证按 review_profile 最小必做：guarded/audit 必有独立前置验证者（`/ms-verify --impl`）；fast 仅质量地板。
- Phase 1~3（内置角色演绎）与 Phase 4（外部独立审查）**独立判定**：各自维护 `INT_*` / `EXT_*` canonical state；`--review` 控 Phase 1~3，`--external-review` 控 Phase 4；**audit inline / fast,guarded defer** 到 `/ms-verify --review-drain`。
- 前置验证失败（Blocker）⛔ 阻塞 Commit 1，不因"未加 --review"而放行。

**无 skip 通道**：Phase 1~3 与 Phase 4 **不提供跳过参数**。原 `--skip-review-reason` / `--skip-external-review-reason` 已删除——二者标记的 `INT_PENDING`/`EXT_PENDING` 在所有放行路径下都阻塞，与"未跑审查 → `*_UNRESOLVED`"在阻塞性和恢复动作上完全等价，唯一差别是那句 reason（可写进 commit body）。保留它们的效果只是把"现在必须做"改造成"事后要补的债"。

> Phase 4 详细调用契约（T1/T2 双通道、max_rounds、真值表、L2 权威证据协议）见 [verification-flow.md Phase 4 章节](references/verification-flow.md)。Phase 1~3 验证流程（代码质量/测试完备/UI 自查/综合报告/AC↔diff 交叉验证）同文件。

### 对抗式验证约束

- [ ] **Blocker 必须修复后才能提交**；每个 Phase 声明审查角色；结果分级（Blocker/Suggestion）
- [ ] **audit 默认 inline 触发 Phase 1~3+4**；**fast/guarded 延后 drain**（任务期间标 `review_pending`）；修复 Blocker 后重新运行验证
- [ ] **drain 侧外审必须用 Commit 1 的提交 diff**，⛔ 不得用工作区 diff（否则收到空 diff，等于未审）；见 [verification-flow.md § diff 源](references/verification-flow.md)

### 依赖解析约束

- [ ] **循环依赖必须报错终止**（列出循环路径）
- [ ] "进行中"依赖通过 AskUserQuestion 询问用户

### 原子提交约束

- [ ] **每个任务独立提交**，不跨任务合并
- [ ] **代码提交和文档提交分离**（Commit 1: 代码，Commit 2: 文档状态 + trace 同步结果）
- [ ] 提交后更新状态：**audit → 已完成**；**fast/guarded → `review_pending`**（经 `/ms-verify --review-drain` 通过才转已完成）
- [ ] **`mode` 不是 `inline` 时展开为 N+1 仓提交**：Commit 1 拆成每个有变更的代码根一个 commit，Commit 2 是外壳仓一次 commit（文档 + 所有变更子模块的指针 bump；`linked` 下无指针，仅文档）。协议见 [workspace-topology/references/protocol.md § N+1 仓提交协议](../workspace-topology/references/protocol.md)。代码根取自握手 `workspace_context.code_roots`（`inline` 时为单项，`path` = 仓库根绝对路径，退化为今天的 Commit 1 + Commit 2）。`mode` 为 `linked` 时代码根不归本仓所有，各仓各自提交、⛔ 不 bump 指针，见 [protocol.md §6.5](../workspace-topology/references/protocol.md#65-linked-下无-n1无指针)。
- [ ] **提交前必过 detached HEAD 门**：每个变更的子模块代码根 `git -C <path> symbolic-ref -q HEAD` 失败即 ⛔ 阻塞，处置见 [workspace-topology/references/migration.md § detached HEAD 处置](../workspace-topology/references/migration.md#detached-head-处置)
- [ ] **`mode` 不是 `inline` 时 `--single-commit` 不可用**：跨仓无法合并为单 commit，⚠️ 忽略该 flag 并提示

### 断点续做约束

- [ ] **每个任务开始前执行状态检测**（6 步流水线：Step 1 / 1.5 证据复核 / 2~5）
- [ ] **不相关变更必须警告用户**（AskUserQuestion：stash/忽略/终止）
- [ ] **存在完成痕迹的任务必须通过 Step 1.5 五项证据复核才允许跳过**：[A] AC 表可复核 / [B] 测试无 skip/todo / [C] trace 矩阵按需维护的索引——缺失记 `trace_pending` 增量补齐，不作为放行硬门 / [D1] Phase 1~3 内置对抗式验证证据（audit 任务必查）/ [D2] Phase 4 外部对抗审查证据（audit 任务必查，`ext_review_state=EXT_REVIEWED` 且 L2 yaml 可读）/ [E] 后置测试证据（`Skip-Trace-Reason` 不得作为放行）
- [ ] **Git 历史有 code+doc commit 但任务状态非已完成**：不再直接跳过，改为进入 Step 1.5 证据复核路径
- [ ] 旧任务（前版本完成，无 A/D1/D2/E 产物）→ AskUserQuestion：复核续做 / 登记豁免原因 / 终止
- [ ] **`mode` 不是 `inline` 时状态检测扩为五重**：「工作区」维遍历 N+1 个仓；「Git 历史」维收紧为「外壳仓存在带该 T-XX 的 commit **且** body 记录的子模块 SHA 与当前指针一致」；新增第五维「指针一致性」，不一致 → 进 Step 1.5 证据复核不直接跳过。**「证据复核」维（A/B/C/D1/D2/E）不变**——它复核 AC 表 / 测试 / trace / 对抗验证证据，与仓库拓扑无关

> 详见 [task-orchestration.md](references/task-orchestration.md)

### 自动提交约束（协议参数 `auto_commit`）

- [ ] **测试全部通过且无 Blocker 时自动提交，不询问**
- [ ] **出现 Blocker 或测试失败时暂停询问**
- [ ] 与 `--headless` 互斥（`--headless` 已包含自动提交语义）
- [ ] 安全不变量同 `--headless`：测试未通过不提交、Blocker 未解决不提交

### 记忆文件同步约束

- [ ] **仅允许更新 `## 当前状态` 章节**（活跃任务编号、进度统计）
- [ ] **禁止修改结构性章节**（Project Overview、Skill Architecture、Conventions 等由 /agent-memory 管理）
- [ ] CLAUDE.md 通过 @AGENTS.md 自动导入，无需同步
- [ ] 仅做文本替换，不调用 /agent-memory
- [ ] 若 AGENTS.md 不存在则跳过

### 编排隔离约束

- [ ] **Test Agent 禁读 src/ 已有实现；Impl Agent 禁读 03-test-\*.md、01-requirements.md**
- [ ] **编排器在 Impl Agent 完成后 diff 测试文件，有变更即为 ⛔ Blocker**
- [ ] **主 Agent 只做编排和决策，不直接执行 TDD**

### 全量测试验证约束

- [ ] **批量模式完成后建议调用 `/ms-test-run --trace`**（全量验证 + 追溯校验）；trace 追溯校验可增量/惰性，不阻塞提交；trace 缺口记 `trace_pending` 而非阻断；测试本身（affected/绿验 skipped/todo=0）仍为质量地板不可降
- [ ] **单任务模式完成后必须调用 `/ms-test-run --affected`**（受变更影响的测试，基于 git diff，见 `/ms-test-run` SKILL）
   - `--affected` 无匹配时（ms-test-run 返回"建议运行全量"）→ 回退 `/ms-test-run --trace`
   - 单任务不得完全跳过该校验，除非显式 `--skip-trace="<原因>"` 并登记
- [ ] **`--skip-trace` 收紧**：理由必须写入 Commit 1 `Skip-Trace-Reason:` 尾注，批量交付报告单列（便于事后补跑）
- [ ] **使用 `--skip-trace` 的任务自动标 `postcheck_pending`**，不得进入"已完成可跳过"态（恢复方式：补跑 `/ms-test-run --affected` 或 `--trace`，Step 1.5 [E] 才放行）
- [ ] 全量/受影响测试失败不回滚已提交任务（原子提交已落盘）
- [ ] --headless / --auto-commit 模式：记录警告到交付报告，不中断

### 无人值守约束（协议参数 `unattended`）

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
External-Review-Verdict: <EXT_REVIEWED | EXT_UNRESOLVED | EXT_BLOCKED>（Phase 4 触发时必填，含 rounds 和 health_scores）
Skip-Trace-Reason: <单任务使用 --skip-trace 时填写；其他情况省略此行>
Profile-Downgrade-Reason: <使用 --review-profile 降档时必填；Step 1.5 复核校验降档理由是否合规；batch 交付报告按 `Review-Batch-Id` 聚合 review_pending 清单>
Review-Batch-Id: <fast/guarded 任务标 review_pending 时填写 batch ID；消费者：/ms-verify --review-drain 批量交付报告>
Review-Due: <review_pending 任务的计划 drain 截止时间；消费者：batch 交付报告>
Pending-Reason: <review_pending 或 trace_pending 的延后原因；消费者：Step 1.5 复核 + batch 交付报告>
Exploration-Mode: <探索模式设为 true 并登记证据/豁免原因；其他情况省略此行>
```

**合法 `External-Review-Verdict` 枚举**：`EXT_REVIEWED` / `EXT_UNRESOLVED` / `EXT_BLOCKED`。禁用 `CONVERGED` / `DEGRADED` / `SKIPPED` 等非 canonical 词汇。

**type 类型**：feat | fix | refactor | test | docs | chore

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，envelope 遵循共享约束 §2 `yaml-summary-v1`；私有字段仅放 `summary.details`：

| details 字段 | 含义 |
|---|---|
| `task` | 任务编号，v1 `T-XX`，v2 [FUTURE] `TASK-XX` |
| `commits.code` / `commits.docs` | Commit 1 代码提交、Commit 2 文档提交 |
| `test_summary` | passed/failed/coverage |
| `blockers_resolved` / `suggestions_skipped` | 本任务处理结果 |
| `ac_verified` | 已验证 AC 列表 |
| `decision_log` | Contract 审核、重试、Blocker 修复等关键决策事件 |

`next_recommended` 常用 `/ms-sync`；若已完成 Commit 2，可推荐 `/ms-compound` 或为空。

## 参考资料

- [skeleton-examples.md](references/skeleton-examples.md) - 接口/测试骨架示例
- [execution-flow.md](references/execution-flow.md) - 任务执行流程详解
- [verification-flow.md](references/verification-flow.md) - 对抗式验证流程详解
- [task-orchestration.md](references/task-orchestration.md) - 多任务编排（批量/依赖/断点续做）
- [auto-mode.md](references/auto-mode.md) - 无人值守模式详解
- [realign.md](references/realign.md) - dev-workflow spec_version 回扫
