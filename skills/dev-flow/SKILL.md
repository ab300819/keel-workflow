---
name: dev-flow
description: Execute general development tasks from a plan document, task prompt, or issue text — no DevDocs required. Five-stage flow with three hard gates (Contract / Red-Green / Verify with fresh-context contract review), quality floor, and atomic commit. Use for standalone or lightweight projects, superpowers/CE/BMAD style plans, or any dev task outside DevDocs. Triggers on "dev-flow", "通用开发流程", "按计划开发", "执行计划", "轻量开发", "独立开发", "standalone dev". NOT for DevDocs T-XX task execution with traceability (use ms-dev-workflow), task breakdown (use ms-dev-tasks), or bug fixes in DevDocs projects (use ms-bugfix).
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, Task, AskUserQuestion, TodoWrite
---

# Dev Flow

不依赖 DevDocs 的通用开发执行器：**契约先行 + 测试红绿 + 质量地板 + 证据交付**。输入一个计划文档、任务描述或 issue 文本即可启动。复杂治理（编号体系、追溯矩阵、文档同步、review_profile 分档）留给 `ms-*` 流程。

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese

## 触发条件

- 用户给出计划文档（如 superpowers writing-plans 产出的 Markdown checklist）要求逐项实施
- 用户给出任务描述 / issue 文本要求直接开发，且项目无 DevDocs 文档体系
- 用户要求"轻量/通用/独立的开发流程"

**路由判定**：项目存在 `docs/devdocs/` 且任务有 T-XX 编号 → 用 `/ms-dev-workflow`；否则用本 skill。

## 输入形态

| 输入 | 处理方式 |
|------|----------|
| 计划文档路径 | 读取 Markdown checklist，选择当前项或用户指定项 |
| 任务 prompt | 直接转为执行契约，必要时扫描代码补足上下文 |
| issue 文本 | 提取问题、期望行为、约束、验收信号 |
| 代码上下文提示 | 仅作 scope hint，不替代验收契约 |

只识别 Markdown checklist 和自然语言任务，不解析任何框架专有计划语法。**不引入新编号体系**：契约只用本轮局部 checklist，不生成 DF-XX / AC-XX。

## 五阶段流程

| 阶段 | 目的 | 输出 / 门控 |
|------|------|------------|
| 1. 输入定位 | 读输入，扫代码上下文 | 目标、范围、风险、候选测试命令 |
| 2. 执行契约 | 协商 Execution Contract | 契约 yaml；**Contract Gate** |
| 3. 测试先行 | 写最小测试，确认红验 | 红验记录 + 测试冻结点；**Red-Green Gate** |
| 4. 实现与重构 | 只实现契约内行为，跑到绿验 | 代码变更、绿验结果 |
| 5. 证据与交付 | 质量地板 + fresh-context 契约审查 + 可选提交 | 交付报告；**Verify Gate** |

## 三硬门控

### Gate 1: Contract Gate（唯一默认人工批准点）

进入实现前必须形成可执行验收契约（模板见下）。**交互模式**：契约以一次 AskUserQuestion 请用户确认（确认 / 修改范围 / 终止）；**headless 或任务明确**：自动通过并在交付报告记录理由。

后续仍可临时询问（疑似测试缺陷、范围冲突、危险操作），但**禁止逐阶段批准**——人工控制集中在契约这一个高杠杆时刻。

### Gate 2: Red-Green Gate

- 行为变更且自动测试可行时，**必须先红后绿**：新测试先全部失败（且不破坏既有测试基线），实现后全部通过
- 红验通过即**测试冻结**：实现阶段不得修改测试文件（完成时 diff 机械校验，有变更 → ⛔ Blocker）；疑似测试缺陷 → 停止实现并请求确认，不得静默改测试
- 自动测试不可行（无测试框架 / 纯配置 / 探索任务）：**不伪造 TDD**——必须在契约 `evidence_plan` 中声明降级证据（命令 / 截图 / 手动验证）及不可行原因

### Gate 3: Verify Gate（一个门、两个独立 verdict，均必过）

**3a. Evidence Check（质量地板，不可降；通用化自 [_shared/constraints.md 质量地板 5 条](../_shared/constraints.md)，"契约行为"对应原"行为型 AC"）**：

- [ ] 绿验通过且 `skipped/todo = 0`
- [ ] 测试冻结 diff 校验通过
- [ ] 声称 vs 实际 diff 一致（契约行为逐条对照 `git diff`，无未解释大块变更）
- [ ] 每个契约行为至少 1 条独立证据（测试断言 / 命令输出 / 截图 / 已声明的手动验证）
- [ ] 受影响测试后置运行通过

> 自动测试不可行（已在契约声明降级）时，绿验/冻结/后置测试三项记 N/A，由 `evidence_plan` 的降级证据 + 原因替代；其余两项不可豁免。

**3b. Fresh-Context Contract Review**：派一个**新上下文子 Agent**（Task tool），只校验 `diff ↔ Execution Contract ↔ evidence` 合规——契约行为是否都实现、有无契约外变更、证据是否真实支撑。spec 合规优先于代码质量；不扩展为完整代码质量审查。contract-critical 发现 → ⛔ 阻断修复后重审。

> 这是去掉默认物理双 Agent 后"写码者不自评"的最低保障，不可跳过；完整对抗审查用 `--audit`。

**审查即分诊**：审查发现分两类——①契约内（含通用不变量：不破坏既有测试、测试冻结、无未解释大 diff、安全底线）critical → 阻断修复；②契约外发现（顺手发现的 bug / 坏味道）→ **不阻断、不顺手改**，列入交付报告 `deferred` 清单。

## Execution Contract

```yaml
execution_contract:
  source: "<plan path | prompt | issue text>"
  goal: "<一句话目标>"
  in_scope: ["<本次会做什么>"]
  out_of_scope: ["<明确不做什么>"]
  expected_behavior: ["<用户或系统可观察结果>"]
  evidence_plan:
    - kind: "test | command | screenshot | manual"
      command_or_path: "<验证方式；非 test 时附自动测试不可行原因>"
  risk_flags: ["<public-api | schema | auth | data-loss | ui | low-risk>"]
  stop_conditions: ["<遇到什么必须暂停确认>"]
```

**模糊任务处理**：

| 情形 | 处理 |
|------|------|
| 可推导单一可验证目标 | 写明"推导契约"，继续执行 |
| 多个合理方向 | ⚠️ 必须确认，用户选目标/范围 |
| 完全无验收标准（"优化一下"） | 不进实现，降级为契约澄清 |
| 显式 `--explore` | 允许 spike / 方案 / 可回滚实验；**不得声称"已完成"** |

## 执行模型

默认**单 Agent 两 Pass**（语义屏障）：

1. **Test Pass**：基于契约写接口骨架 + 测试断言（断言值来自契约 `expected_behavior`，不参考实现细节）→ 红验
2. **Impl Pass**：只实现契约内行为 → 绿验 → 重构（保持绿）

`--strict-tdd` 或 `risk_flags` 含 `auth/data-loss/schema/public-api` 时，升级为**物理双子 Agent**（Task tool）：Test Agent 不读已有实现，Impl Agent 不读契约推导过程、不可改测试——同 ms-dev-workflow 信息屏障语义。

**编码纪律**（两种模式恒定）：遵循 [`/code-quality`](../code-quality/SKILL.md) 核心阈值表 / [命名规范](../code-quality/SKILL.md#命名规范) / [注释规范](../code-quality/SKILL.md#注释规范)（禁止变更日志式、来源记录式、对审查者说话的注释，含修复循环）/ [日志规范](../code-quality/SKILL.md#日志规范)（级别纪律 + 最小上下文 + 安全红线 + 禁 log-and-throw）；测试断言质量遵循 `/testing-guide`。

## 批量模式（计划文档多项）

- 仅**可独立执行、可验收**的 checklist 项进入批量；叙事型条目先转任务队列（与用户确认）
- 逐项执行，**每项 fresh context**（独立子 Agent 或清空上下文重启，对抗 context rot）
- **每项独立走完三硬门控**（形成契约 → 红绿 → Verify Gate 通过），不做批末统一审查
- 每项完成：勾选计划文档对应项 + 原子提交（`--no-commit` 时仅勾选不提交）
- **断点恢复**：无检查点文件、无状态机——每项启动前重读计划文档勾选状态，未勾选即未完成
- 单任务 prompt 输入无批量逻辑

## Flags

| flag | 作用 |
|------|------|
| `--strict-tdd` | 强制物理双子 Agent + 信息屏障（核心逻辑 / 高风险） |
| `--audit` | Verify Gate 后追加完整独立审查（调用 `/adversarial-review`） |
| `--no-commit` | 只改代码 + 输出证据，不提交 |
| `--explore` | 模糊/调研任务：spike 模式，产出方案或可回滚实验 |

## 提交规范

- 用户要求提交或批量模式逐项提交时：**原子提交**，一项一 commit，遵循 `/commit-convention`
- 文件移动/删除遵循 `/git-safety`（git mv/rm）
- 绝不推送远程；Verify Gate 未过不提交

## 交付报告

```markdown
## dev-flow 交付报告

**任务**: <goal> ｜ **来源**: <source> ｜ **结果**: 完成 / 部分完成 / 阻塞
**契约批准**: 用户确认 / 自动通过（理由）

### 证据
| 契约行为 | 证据 | 位置 |
|---|---|---|

### Verify
- Evidence Check: ✅/❌ ｜ Fresh-Context Review: ✅/❌（轮次 N）

### Deferred（契约外发现，未处理）
- <发现 + 位置>

### 建议沉淀项（可选，仅确有可复用惯例/踩坑时输出）
- <一行；用户可自行 /agent-memory 或忽略>
```

## 约束清单

- [ ] **三硬门控不可跳过**：Contract / Red-Green（测试可行时）/ Verify（两 verdict 均必过）
- [ ] **测试冻结**：实现阶段改测试文件 → ⛔ Blocker
- [ ] **Fresh-Context Review 必须是新上下文子 Agent**，不得由实现者自评
- [ ] **契约外发现不顺手改**，进 deferred 清单
- [ ] **无自动测试不伪造 TDD**，降级证据须声明原因
- [ ] **不生成编号体系**、不写 traceability、不做文档同步
- [ ] **提交前排除构建/缓存生成物**（`__pycache__`/dist 等确保不进入提交——.gitignore / 本地 exclude / 不 add 均可；生成物入 diff 视为未解释变更）
- [ ] **绝不推送远程**

## 生态边界

| 场景 | 用谁 |
|------|------|
| DevDocs 项目 T-XX 任务执行 / 追溯 / 04-dev-tasks 状态推进 / review-drain | `/ms-dev-workflow` |
| 计划文档 / 普通 issue / CE·superpowers·BMAD 松散计划驱动的开发 | **本 skill** |
| 任务拆分 | superpowers writing-plans 或 `/ms-dev-tasks`（DevDocs） |
| 项目转文档驱动 | `/ms-retrofit` 反向生成 DevDocs（本 skill 交付报告可作辅助输入，非追溯矩阵） |

**superpowers 衔接**：writing-plans 产出可直接作输入；executing-plans 可作上层计划执行器，单项开发由本 skill 接管门控。

## Skill 协作

| 阶段 | 协作 Skill | 说明 |
|------|-----------|------|
| 写业务代码 | `/code-quality` | 核心阈值表、命名/注释规范、设计原则（代码级） |
| 写测试 | `/testing-guide` | 断言质量、弱断言检查 |
| 完整审查 | `/adversarial-review` | 仅 `--audit` 或用户显式要求 |
| 提交 | `/commit-convention` + `/git-safety` | 提交信息 + git 原生操作 |
| UI 任务 | `/ui-orchestrator` | 可选协作，非硬依赖 |
