---
name: dev-workflow
description: 执行或恢复 keel 开发任务，支持单项、批量和明确授权的无人值守。任务拆分用 dev-tasks；非 keel 开发用 dev-flow。
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, TodoWrite, Task
metadata:
  patterns: [pipeline, reviewer]
  interaction: multi-turn
  handoff: yaml-summary-v1
spec_version: 3.4
spec_version_notes: |
  1.1 = P0-A 文档收敛 + 累计审计删减 (Phase 1)
        本 skill 不做任务并行（S9 并行化）——前置依赖 worktree 隔离协议
        （工作区所有权 / 文档 SSOT 合并 / review-drain 回收）尚未成立；
        需要并行时手动用 worktree 隔离。见 docs/workflows.md § 与 superpowers 共存
  2.0 = 重新定位(代码SSOT/文档记忆)+ review_profile 三档替代层级 + 质量地板恒定 + 独立审查延后 drain + review_pending 状态(Plan A)
  3.0 = 修复延后外审空 diff(Phase 4 按 inline/drain 分离 diff 源)+ 删 skip 参数族
        (2 flag / INT_PENDING·EXT_PENDING 2 enum 值 / 2 trailer / 双 skip 禁令)+ 删最低发现数门槛
  3.1 = 删 External-Review-Channel trailer(派生自 L2 external_review_channel_used,无门禁消费者)
  3.2 = 追溯改反向依赖:删「代码追溯标注规范」节 + S2-S3 骨架不写 keel 编号 +
        标注删减检测改用例删减检测(devflow.v2→v3;存量标注留着不清理,只约束新增)
  3.3 = commit 模板重定(Why + Tests 两项,词法级禁占位)+ 7 个流程 trailer 迁到
        任务台账(主体是任务不是 commit);drain 改读台账 commits 字段,不再 grep git log
        + 删与「分层 TDD 模式」档位表重复的「触发条件」表
  3.4 = 里程碑分段执行(可选):队列按 01 §2 归属列切段 + 段末人工验证停点 +
        01 §2.5 验收状态列(人验持久源)+ headless 段末返 partial(devflow.v5→v6);
        未划里程碑的项目行为完全不变
---

# 开发工作流

- 共享约束 SSOT：[../shared/constraints.md](../shared/constraints.md)

> 本 skill 遵循共享约束 SSOT：门控标记、yaml-summary-v1、Task 委托、用户确认、Recovery 格式、只读 / dry-run、FUTURE 三态、realign / spec_version 见 [skills/shared/constraints.md](../shared/constraints.md)。本文件只描述 dev-workflow 私有规则（11 步流程、Sprint Contract、headless 安全、Step 1.5 五项证据、Phase 1-4 外部审查、EXT 状态机、Commit 1/2 双 commit）。
>
>

> **权威文件唯一原则**（spec_version 1.1 起强制）：
> - Phase 4 / 并行调度 / `diff_hash` / 重跑机制 → [verification-flow.md](references/verification-flow.md) 唯一权威
> - Step 1.5 各分支 / Batch-Id 识别 → [task-orchestration.md](references/task-orchestration.md) 唯一权威
> - Phase 2-UI 审查清单 → [ui-quality-checklist.md](references/ui-quality-checklist.md) 唯一权威
> - review_profile / drain / review_pending → [verification-flow.md](references/verification-flow.md) + [task-orchestration.md](references/task-orchestration.md)
> - 风险分类器(review_profile 提议)→ /dev-tasks
> - 其他文件（SKILL.md / auto-mode.md / execution-flow.md）**仅允许 2-3 行指针引用**，严禁重复转述。违反此原则视为复杂度退化，必须 revert。

> 视角：资深开发者 — 务实优先，不过度设计，测试先行，提交原子化。

## 快速开始

执行开发任务，采用骨架先行 + 分层 TDD。常见用法：`/dev-workflow T-03`（单任务）、`T-01~T-05`（批量）。拆分任务用 `/dev-tasks`，修 Bug 用 `/bugfix`。支持中英文提问，统一中文回复。

## 模式选择

| 模式 | 适用场景 | 流程 |
|------|---------|------|
| **轻量** | Bug fix、小改动、配置变更 | → `/bugfix`（已有） |
| **标准** | 新功能、需求变更 | → 完整 Requirements→Design→Tests→Tasks→Dev |
| **探索** | 原型、技术调研 | → 允许跳过部分验证，事后由用户确认目标行为后补建 AC |

> **探索模式最小行为验证**：可跳过文档强制（AC/追溯标注/完整 TDD）和对抗式验证，但**不得跳过** S6 绿验（skipped/todo=0）和至少 1 条"目标行为证据"（AC / UT/IT 断言 / `--ui --live` 截图 / 显式豁免）；写入任务台账 `exploration_mode: true`，便于事后由用户确认目标行为后补建真实 AC。无证据 ⛔ 阻止提交。

## 触发条件

用户开始/批量/继续开发任务（T-01 / T-01~T-05 / F-001 / 「把剩下的都跑完」）；关键词如"开发任务"、"执行任务"、"开始 T-XX"、"批量开发"、"继续开发"、"无人值守"。

## 运行模式

### 语法

| 指定符 | 示例 | 说明 |
|--------|------|------|
| 单任务 | `T-03` | 执行单个任务（现有行为） |
| 范围 | `T-01~T-05` | 执行范围内所有任务 |
| 枚举 | `T-01,T-03,T-07` | 执行指定任务列表 |
| 功能点 | `F-001` | 通过 `关联需求` 字段反查所有关联任务 |
| 用户故事 | `US-001` | 同上 |
| 轻量入口 | 直接描述任务 + 验收标准 | 无 04 文档也可进入:按 [inline-entry.md](references/inline-entry.md) 物化 stub(01 AC 条目 + 04 任务条目)后转单任务路径;review_profile 下限 guarded |

> ⛔ **没有 `M-XXX` 指定符**。里程碑不是执行单元——要跑某段就按它的 `F-XXX` 或 `T-XX` 范围指定。

**跑到一半停下来是正常的。** `01-requirements.md` 划了里程碑时，队列按段执行，**一段做完会停下来请你实际用一遍**——不是卡住，是这套流程的目的：F 全做完、单测全过，连起来用却全是问题，这类事只有人去用才发现得了。你用完说「能用」就继续下一段，说「有问题」就先修。不划里程碑的项目不会有这个停点。分段规则见 [task-orchestration.md § 1.5](references/task-orchestration.md)。

> **协议参数不在用户面。** 无人值守 / 自动提交 / 审查档位 / 外部审查轮次 / 上下文重置 / 单次提交 / 跳过追溯，都由编排层从你的自然语言归一化后下传（[`task/intent-normalization`](../shared/constraints.md)），你不需要记参数名。
>
> **授权要你开口**：无人值守和自动提交不是默认行为，须明说；反过来，超出你授权范围的不可逆动作一律在发生时就地确认（[`task/consent-at-action`](../shared/constraints.md)）。

### 统一编排流程

所有模式均采用**编排器 + 子 Agent**：编排器解析指定符、依赖/断点、启动子 Agent、接收 yaml-summary-v1、调度 `/sync`/`/test-run`/`/compound`；任务子 Agent 执行 TDD、对抗式验证、Blocker 修复、自描述和 Commit 1。扩展后 >1 任务时拓扑排序并逐任务原子提交。通用 Task 委托协议见共享约束 §3，批量/续做细节见 [task-orchestration.md](references/task-orchestration.md)。

## 前置条件

- 任务文档：`docs/devdocs/04-dev-tasks.md`,且任务已定义并包含:关联需求、验收标准、测试方法
- **或**直接给出任务定义与验收标准（无需参数）:按 [inline-entry.md](references/inline-entry.md) 物化 stub 后进入 S1;Test Agent 输入中 02/03 字段标 `—(inline)`,以 S1.5 Sprint Contract 为测试输入约束

## 工作流程

本文件保留 S1~S11 骨架；S12 文档同步/知识沉淀属于 Commit 2 后置流程，详见 [execution-flow.md](references/execution-flow.md)。

| 步骤 | 质量门 |
|------|--------|
| S1 读取任务定义 | 从 `04-dev-tasks.md` 获取任务、F/AC/UT/IT/E2E 关联 |
| S1.5 Sprint Contract | Test Agent 基于 AC + 当前代码上下文生成可执行验收契约（函数签名、返回值类型、边界条件、异常场景）；编排器裁剪过度契约、补足遗漏契约，确认后作为测试输入约束 |
| S2-S3 骨架 | 接口骨架 + 测试骨架；⛔ 代码内不写任何 keel 编号，追溯由 Commit 2 写入文档 |
| S4-S7 红绿重构 | Test Agent 写断言；编排器红验；Impl Agent 实现、绿验、重构；绿验必须 `skipped/todo=0`；注释遵循 [`/code-quality` 注释规范](../code-quality/SKILL.md#注释规范)（禁止变更日志式/来源记录式注释，含修复循环），日志遵循 [日志规范](../code-quality/SKILL.md#日志规范)（安全红线/级别纪律/禁 log-and-throw）|
| S8 完成检查 | 质量地板 5 条 + AC 完备性表（fast 证据摘要 / audit 完整 AC 类型×证据矩阵）+ 声称 vs 实际 diff 交叉验证；缺证据或未关联大块 diff → ⛔ 禁止继续 |
| S9 前置验证 | guarded/audit `/verify --impl`；fast 仅质量地板（不跑前置验证）；🟢 UI 任务有设计稿时另跑 `/verify --ui --impl` 对齐设计稿（不随 profile 变） |
| S9 Phase 1~3 | 内置角色演绎对抗式验证（独立审查）：**audit inline fail-fast**；**fast/guarded 延后**到 `/verify --review-drain`，任务期间标 `review_pending`；`--review` 可临时叠加 inline |
| S9 Phase 4 | 外部对抗审查 embedded-headless（独立审查）：**audit inline**；**fast/guarded 延后** drain；T1 codex CLI → T2 codex-mcp，T1/T2 全失败 fail-fast；状态 `EXT_REVIEWED`/`EXT_UNRESOLVED`/`EXT_BLOCKED`（与 `review_pending` 区分） |
| S10 自描述 | `/code-self-describe --update`（`workspace_context.capabilities.code_metadata_write_policy` 为 `explicit_opt_in` 时**默认跳过**——自描述产物写在代码目录内，违反零污染红线。跳过须在 yaml 摘要里以 ℹ️ 记录 `skipped: code_metadata_write_policy=explicit_opt_in`。用户显式 `--force-code-docs` 才执行） |
| S11 Commit 1 | 代码提交，遵循「提交信息格式」；Phase 4 触发时把 `ext_review_state` 写进任务台账 |
| Commit 2 后置 | `/sync` 更新 trace + 文档提交；若有 AGENTS.md 仅更新“当前状态”；批量默认 `/compound` |

步骤状态（S1~S11 + S1.5）用于断点恢复；详细矩阵、S12 后置同步和状态标记见 [execution-flow.md](references/execution-flow.md)。

### 失效任务卡前置门（S1 内，⛔ 阻断）

任务卡带 `superseded_by` 字段 → **⛔ 立即停止，不进入 S1.5**。

```text
⛔ T-01 已被 ADR-015 取代（superseded_by: ADR-015）
   该任务卡的执行步骤属于旧决策，照它执行会复原已被删除的设计。
   请先读指向的 ADR 确认当前决策，再决定：
   (a) 做新决策下的等价工作 → 用 /dev-tasks 立新任务
   (b) 确实要复原旧行为 → 需先推翻该 ADR
```

**为什么阻断而非警告**：失效任务卡的危险在于它**看起来完全正常**——状态 ✅ 已完成、步骤具体、路径明确。执行者没有线索知道这些步骤已过期，警告会被当噪音划过去。⛔ 不提供 `--force` 跳过。

## 自顶向下开发模式

> 先定义骨架，后填充细节。确保追溯链在代码生成时就建立。双 Agent 模型（Test Agent → 红色验证 → Impl Agent → 完成检查+提交）已在上方"工作流程"和 [execution-flow.md](references/execution-flow.md) 强制程度矩阵中完整展开。

### 骨架生成约束

判据清单见 [skeleton-examples.md](references/skeleton-examples.md)（接口签名完整性 / 追溯标注 / 未实现方法抛错 / 测试骨架 skip 标记）。

## 分层 TDD 模式

所有任务遵循统一 11 步执行流程 + 5 条质量地板(恒定 inline);`review_profile` 只决定**独立审查(Phase 1~3 + Phase 4)的时机**:

| review_profile | 触发 | 双 Agent | 质量地板 | 前置验证 | Phase 1~3 | Phase 4 | 提交状态 |
|------|------|:---:|:---:|:---:|------|------|------|
| **fast**(默认) | 低风险(见风险分类器) | ✓ | ✓ | — | 延后 drain | 延后 drain | `review_pending` |
| **guarded** | 中风险 | ✓ | ✓ | `/verify --impl` inline | 风险触发 inline 否则延后 | 延后 drain | `review_pending` |
| **audit** | 高风险 | ✓ | ✓ | `/verify --impl` inline | **inline fail-fast** | **inline fail-fast** | 审过才提交 |

> 详细判据见 [verification-flow.md](references/verification-flow.md);风险分类器信号判据 → /dev-tasks(初始提议);执行期复核(只升不降)→ [task-orchestration.md](references/task-orchestration.md);共享定义见 [../shared/constraints.md](../shared/constraints.md)。
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
| 前置验证 | `/verify --impl` | Task tool 子 Agent |
| UI 对齐 | `/verify --ui` | Task tool 子 Agent |
| 追溯同步 | `/sync` | Task tool 子 Agent |
| 知识沉淀 | `/compound` | Task tool 子 Agent |
| 全量测试 | `/test-run` | Task tool 子 Agent |

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
| 实现审查 | `/verify --impl` | **guarded/audit 默认必做（全量 AC）；fast 不跑前置验证（仅质量地板）** |
| UI 对齐 | `/verify --ui --impl` | **UI 任务有设计稿时**与 `/verify --impl` **并行各跑一次**（不得合并为单次调用，`--ui --impl` 仅覆盖设计稿↔实现一维）；无设计稿降级为 Phase 2-UI 自查（不随 profile 变） |
| 完成验证 | `/code-quality` + `/testing-guide` | 对抗式验证：audit inline 自动 / fast,guarded 延后 drain；`--review` 临时叠加 |
| 完成检查 | `/code-self-describe` | 更新模块自描述（--update） |
| 代码提交 | `/git-safety` | 使用 git mv/rm 处理文件 |
| 提交信息 | `/commit-convention` | 遵循项目提交规范 |
| 依赖解析 | `/dev-tasks` | 读取任务依赖关系和状态 |
| 任务完成 | `/sync` | 后续：更新追溯矩阵（追溯同步） |
| 知识沉淀 | `/compound` | 推荐：sync 后提取经验模式（批量模式默认执行） |
| 全量测试 | `/test-run` | 批量完成后 `--trace`（全量+追溯）；单任务完成后 `--affected`（受变更影响测试），affected 无匹配时回退 `--trace` |
| 外部对抗审查（契约复用） | `/adversarial-review` | **dev-workflow S9 Phase 4 仅复用其 [`references/external-reviewer-integration.md`](../adversarial-review/references/external-reviewer-integration.md) 底层 T1/T2 双通道 + 熔断协议**（不使用 T3 Task 子 Agent 兜底），不直接调用整个 multi-turn skill（避免 AskUserQuestion 阻塞）。Phase 4 调度器以 embedded-headless 模式运行；`/adversarial-review` 仍可被用户独立调用做交互式审查 |

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

无论档位高低,5 条不变量永远 inline 生效(定义见 [../shared/constraints.md](../shared/constraints.md)):绿验 `skipped/todo=0` / 测试冻结 / 声称vs实际 diff 一致 / 行为型 AC 至少 1 条独立证据 / 受影响测试后置。

> **三类机制区分(关键,勿混)**:
> 1. **质量地板**(上述 5 条)——所有档 inline。
> 2. **前置验证 `/verify --impl`**(AC↔实现语义一致)——属"前置验证门",Blocker inline 阻塞提交;guarded/audit 跑,fast 不跑。
> 3. **独立对抗审查**(Phase 1~3 + Phase 4)——**唯一可延后**的部分,fast/guarded 延后到 drain,audit inline。
>
> "review_profile 只改独立审查时机"成立:地板与前置验证永远 inline,不在延后范围。

## 对抗式验证（可选）

> 以不同角色视角审查代码，模拟 "开发 → 审查 → 测试" 的多人协作模式。

> **与 review_profile 的关系（重要）**：本节描述的是独立审查的**机制**（Phase 1~3/4、INT/EXT 状态），其**触发时机**由 `review_profile` 决定——档位表见上文「分层 TDD 模式」，本节不重复。

**设计原则**：

- 前置验证按 review_profile 最小必做：guarded/audit 必有独立前置验证者（`/verify --impl`）；fast 仅质量地板。
- Phase 1~3（内置角色演绎）与 Phase 4（外部独立审查）**独立判定**：各自维护 `INT_*` / `EXT_*` canonical state；`--review` 控 Phase 1~3，`--external-review` 控 Phase 4；**audit inline / fast,guarded defer** 到 `/verify --review-drain`。
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
- [ ] 提交后更新状态：**audit → 已完成**；**fast/guarded → `review_pending`**（经 `/verify --review-drain` 通过才转已完成）
- [ ] **`mode` 不是 `inline` 时展开为 N+1 仓提交**：Commit 1 拆成每个有变更的代码根一个 commit，Commit 2 是外壳仓一次 commit（文档 + 所有变更子模块的指针 bump；`linked` 下无指针，仅文档）。协议见 [workspace-topology/references/protocol.md § N+1 仓提交协议](../workspace-topology/references/protocol.md)。代码根取自握手 `workspace_context.code_roots`（`inline` 时为单项，`path` = 仓库根绝对路径，退化为今天的 Commit 1 + Commit 2）。`mode` 为 `linked` 时代码根不归本仓所有，各仓各自提交、⛔ 不 bump 指针，见 [protocol.md §6.5](../workspace-topology/references/protocol.md#65-linked-下无-n1无指针)。
- [ ] **提交前必过 detached HEAD 门**：每个变更的子模块代码根 `git -C <path> symbolic-ref -q HEAD` 失败即 ⛔ 阻塞，处置见 [workspace-topology/references/migration.md § detached HEAD 处置](../workspace-topology/references/migration.md#detached-head-处置)
- [ ] **`mode` 不是 `inline` 时 `--single-commit` 不可用**：跨仓无法合并为单 commit，⚠️ 忽略该 flag 并提示

### 断点续做约束

- [ ] **每个任务开始前执行状态检测**（6 步流水线：Step 1 / 1.5 证据复核 / 2~5）
- [ ] **不相关变更必须警告用户**（AskUserQuestion：stash/忽略/终止）
- [ ] **存在完成痕迹的任务必须通过 Step 1.5 五项证据复核才允许跳过**：[A] AC 表可复核 / [B] 测试无 skip/todo / [C] trace 矩阵按需维护的索引——缺失记 `trace_pending` 增量补齐，不作为放行硬门 / [D1] Phase 1~3 内置对抗式验证证据（audit 任务必查）/ [D2] Phase 4 外部对抗审查证据（audit 任务必查，`ext_review_state=EXT_REVIEWED` 且 L2 yaml 可读）/ [E] 后置测试证据（`skip_trace_reason` 不得作为放行）
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
- [ ] 若 AGENTS.md 不存在、或「当前状态」节只有台账/状态文档链接（无任务编号与进度字段）则跳过；⛔ 不新增进度快照

### 编排隔离约束

- [ ] **Test Agent 禁读 src/ 已有实现；Impl Agent 禁读 03-test-\*.md、01-requirements.md**
- [ ] **编排器在 Impl Agent 完成后 diff 测试文件，有变更即为 ⛔ Blocker**
- [ ] **主 Agent 只做编排和决策，不直接执行 TDD**

### 全量测试验证约束

- [ ] **批量模式完成后建议调用 `/test-run --trace`**（全量验证 + 追溯校验）；trace 追溯校验可增量/惰性，不阻塞提交；trace 缺口记 `trace_pending` 而非阻断；测试本身（affected/绿验 skipped/todo=0）仍为质量地板不可降
- [ ] **单任务模式完成后必须调用 `/test-run --affected`**（受变更影响的测试，基于 git diff，见 `/test-run` SKILL）
   - `--affected` 无匹配时（test-run 返回"建议运行全量"）→ 回退 `/test-run --trace`
   - 单任务不得完全跳过该校验，除非显式 `--skip-trace="<原因>"` 并登记
- [ ] **`--skip-trace` 收紧**：理由必须写入任务台账 `skip_trace_reason`，批量交付报告单列（便于事后补跑）
- [ ] **使用 `--skip-trace` 的任务自动标 `postcheck_pending`**，不得进入"已完成可跳过"态（恢复方式：补跑 `/test-run --affected` 或 `--trace`，Step 1.5 [E] 才放行）
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

⛔ **commit 里不写任何 keel 编号与流程状态。** 判据：每条信息，一个不知道
keel 存在的维护者都能读懂并用上。任务编号、AC 编号、审查批次、降档理由这些
对他是纯噪音——它们的主体是**任务**，归任务台账（见下）。

```
<type>(<scope>): <描述可观察结果的一句话>

Why: <只写代码和 diff 表达不了的决策、约束、取舍>
Tests: <实际执行过的精确命令>
```

| 规则 | 强制 | 怎么查 |
|---|:---:|---|
| 标题描述可观察结果，⛔ 不带 `T-`/`F-`/`AC-`/`UT-` 编号 | ⛔ | 词法 |
| `Tests` 由**实际执行记录生成**精确命令 | ⛔ | 机器生成，⛔ 不允许手填「已测试」 |
| ⛔ 禁占位文本：模板原文、`TODO`、`N/A`、「相关修改」、「测试通过」 | ⛔ | **词法检查，不是语义校验** |
| `Why` 只写取舍；机械变更 ⛔ 不强迫编造 | 软 | 不判 |
| ⛔ 不复述 diff | — | git 已经存了 |
| commit 保持原子 | 软 | 小而单一的 diff 比四段空泛说明更容易恢复上下文 |

**禁占位文本是防填空的主力**：它拿到了大部分收益，却仍只是词法检查。⛔ 用纯格式
规则**保证不了** `Why` 有价值——策略是把必须手写的主观内容压到一个字段，其余证据
自动产生，⛔ 不假装格式校验等于内容质量。

**type 类型**：feat | fix | refactor | test | docs | chore

## 任务台账（流程状态的唯一载体）

原先挂在 Commit 1 尾注的 7 个流程字段全部迁到 `04-dev-tasks.md` 的任务条目。
它们的语义本来就是「**T-07 这个任务**的外审还欠着」——主体是任务不是 commit。

| 字段 | 何时填 | 语义 |
|---|---|---|
| `commits` | Commit 1 落盘后由 Commit 2 写入 | `<repository>@<full-sha>` + `patch_id` + 一句话描述，可多条。**与追溯矩阵 `changed_by` 同形状**，共用 §2.4 三级降级链 |
| `review_state` | fast/guarded 延后时 | `pending` / `done` |
| `batch` / `due` | 同上 | 批次 ID / `sprint:<id>` 或 `YYYY-MM-DD` |
| `pending_reason` | 同上 | `deferred-fast` / `deferred-guarded` |
| `ext_review_state` | audit Phase 4 | `EXT_REVIEWED` / `EXT_UNRESOLVED` / `EXT_BLOCKED` |
| `profile_downgrade_reason` | 显式降档时 | 降档理由（升档不需要）|
| `skip_trace_reason` | `--skip-trace` 时 | 跳过后置 trace 校验的原因 |
| `exploration_mode` | 探索模式 | `true` + 证据/豁免原因 |

⛔ **绑任务编号，不绑 commit hash。** squash / rebase 改 hash 时，`commits` 字段
的考古索引会失效，但**门控状态（`review_state` / `batch` / `due`）不受影响**——
这是分开绑的理由。

**`commits` 失效时的降级链**（与追溯矩阵同一套，见 sync `trace-mode.md`）：

| 情形 | drain 怎么做 |
|---|---|
| sha 可解析 | 取该 commit 的 diff 送外审 |
| sha 不可解析 + 有 `patch_id` | 在当前历史中找等价提交，找到则更新 `commits` 并继续 |
| 都找不到 | ⚠️ 报 `drain.commit_not_found`，保持 `review_pending`；**Recovery**：人工按描述定位提交后回填 `commits`，或显式改用当前代码状态重审（须在报告单列）|

⛔ **不得因为定位不到就判 `EXT_REVIEWED`**——无审查即无证据。但也 ⛔ 不得让任务
永久卡死：上表第三行的 Recovery 是明确出路，必须给出，不能只报错。

**合法 `ext_review_state` 枚举**：`EXT_REVIEWED` / `EXT_UNRESOLVED` / `EXT_BLOCKED`。
禁用 `CONVERGED` / `DEGRADED` / `SKIPPED` 等非 canonical 词汇。

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，envelope 遵循共享约束 §2 `yaml-summary-v1`；私有字段仅放 `summary.details`：

| details 字段 | 含义 |
|---|---|
| `task` | 任务编号 `T-XX` |
| `commits.code` / `commits.docs` | Commit 1 代码提交、Commit 2 文档提交 |
| `test_summary` | passed/failed/coverage |
| `blockers_resolved` / `suggestions_skipped` | 本任务处理结果 |
| `ac_verified` | 已验证 AC 列表 |
| `decision_log` | Contract 审核、重试、Blocker 修复等关键决策事件 |
| `current_milestone` / `milestones_pending` | 仅分段执行：当前段、等待人工验证的段。**必须随信封上传**——编排层不读产出文档，只消费摘要；漏传会让上层把「等人验证」当成开发阶段完成而继续收尾 |

`next_recommended` 常用 `/sync`；若已完成 Commit 2，可推荐 `/compound` 或为空。

## 参考资料

- [skeleton-examples.md](references/skeleton-examples.md) - 接口/测试骨架示例
- [execution-flow.md](references/execution-flow.md) - 任务执行流程详解
- [verification-flow.md](references/verification-flow.md) - 对抗式验证流程详解
- [task-orchestration.md](references/task-orchestration.md) - 多任务编排（批量/依赖/断点续做）
- [auto-mode.md](references/auto-mode.md) - 无人值守模式详解
- [realign.md](references/realign.md) - dev-workflow spec_version 回扫
