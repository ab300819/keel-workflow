# 无人值守模式详解

> ℹ️ 本文件提及的 `@satisfies` / `@verifies` 等标注属于 **layout.v1 legacy**（v2 起改读 traceability.yml，[FUTURE 状态](../../pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)）。

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
| 工作区洁净或续做 | `git status --porcelain` 为空，**或**变更属于执行队列首个任务（续做豁免） | 不属于首任务的脏工作区 → fail-fast |
| 依赖状态 | 无"进行中"的前置依赖 | fail-fast，报告阻塞链 |
| 任务文档存在 | `04-dev-tasks*.md` 可读 | fail-fast |
| 编号完整 | 任务包含关联 F/AC/UT 编号 | fail-fast |

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
| 10 | Phase 4 外部对抗审查 Blocker | 任务内重试 ≤`max_rounds`（默认 3）次，耗尽则 `EXT_BLOCKED` → fail-fast 终止批量 |
| 11 | Phase 4 T1/T2 全失败（codex CLI / codex-mcp 均不可用或 status=failed） | `EXT_UNRESOLVED` → fail-fast，交付报告提示"检查 codex 环境（codex CLI / codex-mcp 可用性）" |
| 12 | Phase 4 breaker_reason=safety_limit | `EXT_BLOCKED` → fail-fast |
| 14 | 🔴 `--skip-external-review-reason` 登记 | **--headless 下禁止使用**（`--skip-external-review-reason` 只作用于交互模式；--headless 下传入该参数视为非法并 fail-fast）。交互模式：`EXT_PENDING` + 记录到交付报告"待补跑 Phase 4"清单 |

## 安全不变量

1. **测试未通过不提交** — 重试耗尽后 fail-fast，绝不提交失败代码
2. **Blocker 未解决不提交** — 修复循环耗尽后 fail-fast，绝不带 Blocker 提交
3. **不推送远程** — 仅创建本地 commit，push 始终需要人工
4. **原子提交不变** — 每任务独立 commit，不跨任务合并
5. **循环依赖终止** — 报错终止（不变）
6. **标注删减检测** — 修复中若 `@verifies`/`@testcase` 被移除，视为 Blocker
7. **断言数量不减** — 修复后断言总数 ≥ 修复前
8. **工作区洁净校验** — 每任务 Commit 2 后 `git status --porcelain` 必须为空，非空则 fail-fast
9. **漂移防护** — 禁止自动猜测补齐缺失内容，统一 fail 并记录
10. **Phase 4 外部对抗审查**（🔴 任务必须）— `ext_review_state` ≠ `EXT_REVIEWED` → fail-fast 不提交；`--headless` 下任何 `EXT_PENDING`/`EXT_UNRESOLVED`/`EXT_BLOCKED` 均触发 fail-fast
11. **Phase 4 证据（L2 权威）** — Phase 4 必须产出 L2 yaml（`docs/devdocs/audit/<T-XX>-external-review.yaml`）；L2 缺失或不可读 → `EXT_UNRESOLVED` → fail-fast。L1 尾注由 L2 派生（Commit 1 生成时读 L2 填充），L3 原始输出为可选调试 artifact 不参与门禁

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
| 批量启动前 | `git status --porcelain` 为空，或变更属于首任务（续做豁免） | 不属于首任务 → fail-fast |
| 每任务 Commit 2 后 | `git status --porcelain` 为空 | fail-fast |

## 检查点文件

> 格式定义见 [task-orchestration.md](task-orchestration.md) 检查点文件。

`--headless` 模式下检查点的额外用途：
- fail-fast 后提供精确续做命令
- 批量完成后作为交付报告的数据源

## 交付报告模板

### 成功

```markdown
# 交付报告

## 批量执行结果: ✅ 全部成功

| 任务 | 状态 | Commit 1 | Commit 2 | int_review_state | ext_review_state | 通道 | 测试摘要 |
|------|------|----------|----------|------------------|------------------|------|----------|
| T-01 | ✅ | abc1234 | def5678 | INT_REVIEWED | EXT_REVIEWED | T1 | UT-001~003 通过, 覆盖率 85% |
| T-02 | ✅ | 111aaaa | 222bbbb | INT_REVIEWED | EXT_REVIEWED | T2 | UT-004~006 通过, 覆盖率 82% |

## 统计
- 总任务数: 2
- Blocker 已修复: 3
- Suggestion 已跳过: 5
- Phase 4 外部对抗调用次数: 2（T1: 1, T2: 1）
- EXT_PENDING 待补跑: 0（`--skip-external-review-reason` 单列统计）
- EXT_UNRESOLVED: 0 | EXT_BLOCKED: 0
- 总耗时: 由编排器记录

## 决策日志

> 记录关键决策点，便于 /ms-compound 消费和执行 Trace 分析。

```yaml
decision_log:
  - task: T-01
    events:
      - step: S1.5_contract
        action: "Contract 审核通过，裁剪 1 个过度断言"
      - step: S5_red
        action: "红色验证通过，3 个新测试全部失败"
      - step: S9_review
        action: "对抗式验证：1 Blocker 已修复（缺失边界检查）"
  - task: T-02
    events:
      - step: S4_red_assertions
        action: "Test Agent 重试 1 次（首次断言不完整）"
      - step: S6_green
        action: "Impl Agent 一次通过"
```

## 全量测试结果

> 由 /ms-test-run --trace 生成

| 类型 | 通过 | 失败 | 跳过 | 通过率 |
|------|------|------|------|--------|
| UT | X | 0 | 0 | 100% |
| IT | X | 0 | 0 | 100% |
| E2E | X | 0 | 0 | 100% |

### 追溯验证
- AC 总数: X
- 已覆盖（测试通过）: X
- 未覆盖: 0
- AC 覆盖率: 100%

> 详细报告见 docs/devdocs/05-test-report.md
```

### 失败

```markdown
# 交付报告

## 批量执行结果: ❌ 中断于 T-03

| 任务 | 状态 | Commit 1 | Commit 2 | 说明 |
|------|------|----------|----------|------|
| T-01 | ✅ | abc1234 | def5678 | 正常完成 |
| T-02 | ✅ | 111aaaa | 222bbbb | 正常完成 |
| T-03 | ❌ | — | — | 测试失败（重试 3/3） |

## 失败详情
- 失败原因: tests/user.test.ts:45 断言失败
- 已重试: 3 次

## 决策日志

```yaml
decision_log:
  - task: T-01
    events:
      - step: S6_green
        action: "Impl Agent 一次通过"
  - task: T-03
    events:
      - step: S6_green
        action: "测试失败，重试 3/3 后终止"
        failure: "tests/user.test.ts:45 断言失败"
```

## 全量测试结果: ⚠️ 未执行（批量中断）

> 批量中断时全量测试不执行，仅在所有任务完成后触发。

## 续做命令
/ms-dev-workflow T-03~T-05 --headless
```

## 失败续做

fail-fast 后输出的续做命令格式：

```
⚠️ 批量执行中断于 T-XX

已完成: T-01, T-02（已 commit）
失败: T-XX — [失败原因]
未执行: T-YY, T-ZZ

续做命令:
/ms-dev-workflow T-XX~T-ZZ --headless
```
