# 无人值守模式详解

## 概述

`--headless` 模式在批量模式的编排器-执行器架构之上，叠加无人值守决策策略。

```
批量模式通用架构：编排器 + 子 Agent 执行器 + 检查点
                                ↑
--headless 叠加层：策略驱动决策 + fail-fast + 交付报告
```

核心理念：
- 编排器-执行器架构为所有批量模式共享（上下文隔离）
- `--headless` 的区别仅在于：交互点由预定义策略自动决策
- 任何不可恢复的问题立即终止，输出续做命令

## 调用语法

```
/ms-dev-workflow T-01~T-05 --headless              # 基本用法
/ms-dev-workflow F-001 --headless --max-retries 5   # 自定义重试上限
/ms-dev-workflow T-03~T-10 --headless --fix-suggestions  # 尝试修复 Suggestion
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--headless` | — | 启用无人值守模式 |
| `--max-retries N` | 3 | 任务内重试上限（测试失败、Blocker 修复） |
| `--fix-suggestions` | false | 尝试修复 Suggestion（默认跳过） |

## 前置条件

| 条件 | 检测方式 | 失败处理 |
|------|----------|----------|
| 工作区洁净或续做 | **每个代码根**的 `git status --porcelain` 均为空，**或**变更属于执行队列首个任务（续做豁免） | 不属于首任务的脏工作区 → fail-fast |
| 依赖状态 | 无"进行中"的前置依赖 | fail-fast，报告阻塞链 |
| 任务文档存在 | `04-dev-tasks*.md` 可读 | fail-fast |
| 编号完整 | 任务包含关联 F/AC/UT 编号 | fail-fast |

> **「每个代码根」怎么遍历**：路径取自握手 `workspace_context.code_roots`（[_shared/constraints.md](../../_shared/constraints.md) §3 `task/workspace-context`）。`mode` 为 `inline` 时它是单项、就是仓库根，遍历退化为今天的一次检查，**行为不变**。
>
> `mode` 不是 `inline` 时还须**额外检查本仓（文档仓）自身**，但要排除代码根对应的条目——那些条目代表的是代码根内部的状态，已经在各自那一轮里查过了，重复报告会让用户以为有两处问题（判据与排除规则见 [workspace-topology/references/protocol.md §7](../../workspace-topology/references/protocol.md#7-工作区洁净检查gitlink-排除)）。
>
> ⛔ **只查本仓是无人值守下最危险的一种失败**：本仓（只有文档）干净、代码根里一堆未提交改动时会被判成「洁净」，然后无人值守地一路跑下去。
>
> **续做豁免**：fail-fast 后工作区可能残留失败任务的未提交变更。前置校验检测到非空工作区时，
> 对比变更文件与执行队列首个任务的"涉及文件"字段——若匹配则判定为续做场景，放行至断点检测（Step 4a）处理。

## 编排器-执行器架构

> 此架构为所有批量模式共享。交互批量模式下子 Agent 通过 AskUserQuestion 与用户交互；
> `--headless` 模式下由决策策略表自动决策。详见 [task-orchestration.md](task-orchestration.md) 子 Agent 协议。

### 架构总览

```
编排器（主 Agent，轻量上下文）
  │
  ├── 1. 解析指定符 → 任务列表
  ├── 2. 依赖解析 → 拓扑排序 → 执行队列
  ├── 3. 前置校验（洁净工作区或续做豁免、依赖状态）
  │
  ├── 4. 逐任务循环：
  │     │
  │     ├── 4a. 断点检测（编排器自行执行，轻量）
  │     │
  │     ├── 4b. 启动子 Agent 执行单任务 ← Task tool
  │     │     子 Agent 获得：任务定义、关联编号、涉及文件
  │     │     子 Agent 执行：骨架→TDD→验证→commit 1
  │     │     子 Agent 返回：{status, commit_hash, test_results, blockers}
  │     │
  │     ├── 4c. 编排器处理子 Agent 结果：
  │     │     ├── 成功 → 更新任务状态 + ms-sync + commit 2
  │     │     └── 失败 → fail-fast（输出续做命令）
  │     │
  │     ├── 4d. 工作区洁净校验 + 写检查点文件
  │     │
  │     └── 4e. → 下一任务
  │
  ├── 5. 全量测试验证（/ms-test-run --trace）
  │     ├── 触发条件：至少 1 个任务成功完成
  │     ├── 全部通过 → 记录到交付报告
  │     └── 有失败 → 记录 ⚠️ 警告到交付报告（不 fail-fast）
  │
  └── 6. 生成交付报告
```

### 子 Agent 协议

> 输入/输出字段定义见 [task-orchestration.md](task-orchestration.md) 子 Agent 协议。
>
> `--headless` 的区别：`决策模式` 字段为 `--headless`，子 Agent 内所有交互点由决策策略表自动决策。

## 决策策略表

| # | 交互点 | `--headless` 策略 |
|---|--------|-------------------|
| 1 | 提交确认 | 自动提交（测试通过 + 无 Blocker） |
| 2 | Suggestion 处理 | 跳过（`--fix-suggestions` 时尝试单次修复，不重试） |
| 3 | 不相关变更 | fail-fast（无人值守要求洁净工作区） |
| 4 | 进行中依赖 | fail-fast（报告阻塞链） |
| 5 | 测试失败（批量） | 任务内重试 ≤N 次，耗尽则 fail-fast 终止批量 |
| 6 | 完成检查失败 | 任务内重试 ≤N 次，耗尽则 fail-fast 终止批量 |
| 7 | Blocker 修复循环 | ≤N 次修复-验证循环，耗尽则 fail-fast |
| 8 | 自动补充依赖 | 静默记录（不变） |
| 9 | 全量测试失败 | 记录到交付报告，标记 ⚠️ 警告（不 fail-fast，任务已提交） |
| 10 | Phase 4 外部对抗审查（全场景） | 见下方 Phase 4 状态机指针 |
| 11 | batch 完成 / pending 超阈值 / 台账 `due` 到期 | **自动 `/ms-verify --review-drain`**（不"告警"等人）；drain 失败 → fail-fast 输出续做命令 |
| 12 | **里程碑段末停点** | ⛔ 不等人、⛔ 不自行放行：01 §2.5 验收状态保持 `⏳ 待验证`，**停止后续段**，返回 `partial` + 待确认事项（见下方）|

### Phase 4 在 headless 下的状态机

> Phase 4 状态字段（`ext_review_state` / `EXT_REVIEWED` / `EXT_UNRESOLVED` / `EXT_BLOCKED`）、轮次控制（`max_rounds`）、降级链（T1 → T2）、真值表全部由 [verification-flow.md Phase 4 章节](verification-flow.md#phase-4-外部对抗审查) 权威定义。本文件不再重复转述。Headless 下仅追加：任一 `EXT_UNRESOLVED` / `EXT_BLOCKED` → fail-fast，输出 `resume_command`。

## 安全不变量

1. **测试未通过不提交** — 重试耗尽后 fail-fast，绝不提交失败代码
2. **Blocker 未解决不提交** — 修复循环耗尽后 fail-fast，绝不带 Blocker 提交
3. **不推送远程** — 仅创建本地 commit，push 始终需要人工
4. **原子提交不变** — 每任务独立 commit，不跨任务合并
5. **循环依赖终止** — 报错终止（不变）
6. **用例删减检测** — 修复中若已有测试用例被移除，视为 Blocker
7. **断言数量不减** — 修复后断言总数 ≥ 修复前
8. **工作区洁净校验** — 每任务 Commit 2 后**每个代码根**的 `git status --porcelain` 均须为空，非空则 fail-fast
9. **漂移防护** — 禁止自动猜测补齐缺失内容，统一 fail 并记录
10. **Phase 4 外部对抗审查**（audit profile inline；fast/guarded 延后 drain）— 状态机见上方指针；`--headless` 下任何非 `EXT_REVIEWED` → fail-fast
11. **里程碑未经人工验证不进下一段** — 段末停点是人工验证，headless 无法代替；⛔ 编排器不得以「自己判断没问题」放行，⛔ 不得因重试逻辑跨段

## 里程碑段末在 headless 下的处理

段末停点要求人**实际使用一遍**，`--headless` 下无人可用——这不是失败，是「做完了可执行的部分，剩下需要人」。

按 [constraints.md](../../_shared/constraints.md) `confirm/headless-fail-safe`：返回 `partial`（⛔ 不伪造 `failed`，也 ⛔ 不整体报 `success`），并满足 `confirm/headless-report` 四项：

```yaml
status: partial
summary:
  headline: "M-001 实现完成，等待人工验证；M-002 未开始"
  details:
    current_milestone: M-001
    milestones_pending: [M-001]
    milestone_goal: "用户能注册登录，并看到自己的清单"
    verification_prompt: "请实际走一遍：<入口 / 命令>，然后回答能用还是有问题"
blockers:
  - "M-001 需要人工使用验证后才能进入 M-002（默认阻断）"
next_recommended:
  skill: ms-dev-workflow
  args: "T-06~T-09"        # 下一段的续做命令，⛔ 不用 M-XXX
```

⛔ **这些事实必须随摘要传递，不能只落在检查点文件里**——pipeline 不读完整产出文档，只消费信封。

**段末检出问题时同理**：输出编排器的判断与理由，**保留默认阻断**，返回 `partial`；⛔ 不得把自己的意见当成用户批准。

## 重试规范

### 伪代码

```
for attempt in 1..max_retries:
    run_tests()
    if all_passed:
        break
    analyze_failure()
    apply_fix()
if not all_passed:
    mark_task_failed(reason="测试失败（重试 {max_retries}/{max_retries}）")
    fail_fast(resume_command="T-XX~T-YY --headless")
```

### 规则

- 每次重试前分析失败原因，针对性修复
- 重试计数跨红/绿阶段和验证阶段独立：测试修复和 Blocker 修复各自计数
- 超过上限立即终止，不降级为跳过

## 修复安全网

> 检测规则见 [verification-flow.md](verification-flow.md) 修复安全网。

`--headless` 模式下：安全网检测触发的新增 Blocker 同样计入重试计数，耗尽则 fail-fast。

## 工作区洁净协议

| 时机 | 检测 | 失败处理 |
|------|------|----------|
| 批量启动前 | **每个代码根**的 `git status --porcelain` 均为空，或变更属于首任务（续做豁免） | 不属于首任务 → fail-fast |
| 每任务 Commit 2 后 | **每个代码根**的 `git status --porcelain` 均为空 | fail-fast |

## 检查点文件

> 格式定义见 [task-orchestration.md](task-orchestration.md) 检查点文件。

`--headless` 模式下检查点的额外用途：
- fail-fast 后提供精确续做命令
- 批量完成后作为交付报告的数据源

## 交付报告（批量末尾）

批量结束时输出单一交付报告，字段如下（成功/失败共用 schema）：

| 字段 | 含义 |
|------|------|
| `batch_id` | 本次批量的 Batch-Id 标识（Phase 2 引入后强制；Phase 1 期间为空）|
| `tasks_done` | 已完成任务列表（含 Commit 1 sha）|
| `tasks_pending` | 未完成任务 + 失败原因（中断/Blocker/超时）|
| `phase_4_summary` | Phase 4 外审 verdict 汇总（EXT_REVIEWED / EXT_UNRESOLVED / EXT_BLOCKED）|
| `resume_command` | 续做命令（完整 CLI，可复制执行）|

极简示例：

```yaml
delivery_report:
  batch_id: ""              # Phase 2 引入后填充 B-<timestamp>-<seq>
  tasks_done: [T-01, T-02]
  tasks_pending:
    - id: T-03
      reason: "Phase 4 EXT_UNRESOLVED after 3 rounds"
  resume_command: "/ms-dev-workflow T-03~T-05 --headless"
  review_pending: [T-XX, ...]
  drain_result: {passed, pending, blockers}
  sprint_close_blocked: <bool>
```

> 完整字段语义见 [SKILL.md 子 Agent 摘要格式章节](../SKILL.md#子-agent-摘要格式) + yaml-summary-v1（[shared constraints §2](../../_shared/constraints.md)）。
