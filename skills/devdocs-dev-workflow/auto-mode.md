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
/devdocs-dev-workflow T-01~T-05 --headless              # 基本用法
/devdocs-dev-workflow F-001 --headless --max-retries 5   # 自定义重试上限
/devdocs-dev-workflow T-03~T-10 --headless --fix-suggestions  # 尝试修复 Suggestion
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--headless` | — | 启用无人值守模式 |
| `--max-retries N` | 3 | 任务内重试上限（测试失败、Blocker 修复） |
| `--fix-suggestions` | false | 尝试修复 Suggestion（默认跳过） |

## 前置条件

| 条件 | 检测方式 | 失败处理 |
|------|----------|----------|
| 工作区洁净 | `git status --porcelain` 为空 | fail-fast |
| 依赖状态 | 无"进行中"的前置依赖 | fail-fast，报告阻塞链 |
| 任务文档存在 | `04-dev-tasks*.md` 可读 | fail-fast |
| 编号完整 | 任务包含关联 F/AC/UT 编号 | fail-fast |

## 编排器-执行器架构

> 此架构为所有批量模式共享。交互批量模式下子 Agent 通过 AskUserQuestion 与用户交互；
> `--headless` 模式下由决策策略表自动决策。详见 [task-orchestration.md](task-orchestration.md) 子 Agent 协议。

### 架构总览

```
编排器（主 Agent，轻量上下文）
  │
  ├── 1. 解析指定符 → 任务列表
  ├── 2. 依赖解析 → 拓扑排序 → 执行队列
  ├── 3. 前置校验（洁净工作区、依赖状态）
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
  │     │     ├── 成功 → 更新任务状态 + sync --trace + commit 2
  │     │     └── 失败 → fail-fast（输出续做命令）
  │     │
  │     ├── 4d. 工作区洁净校验 + 写检查点文件
  │     │
  │     └── 4e. → 下一任务
  │
  └── 5. 生成交付报告
```

### 子 Agent 协议

**输入**（编排器 → 子 Agent）：

```
任务编号: T-XX
任务定义: （从 04-dev-tasks*.md 提取的完整任务块）
关联编号: F-XXX, AC-XXX, UT-XXX
涉及文件: src/xxx.ts, tests/xxx.test.ts
决策模式: --headless（策略自动决策）
max_retries: 3
```

**输出**（子 Agent → 编排器）：

```
status: success | failed
commit_hash: abc1234（成功时）
failure_reason: "测试失败（重试 3/3）"（失败时）
failure_context: "tests/user.test.ts:45"（失败时）
test_summary: "UT-001~003 通过, 覆盖率 85%"
blockers_resolved: 2
suggestions_skipped: 1
```

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

### 标注删减检测

修复前快照所有 `@verifies` 和 `@testcase` 标注集合。修复后重新扫描。若任何标注被移除，视为新增 Blocker：

> "🚫 Blocker: 修复过程中移除了 @verifies AC-003 标注（文件: tests/user.test.ts:20）"

### 断言数量不减检测

修复前统计测试文件中断言调用总数（`expect`/`assert`/`should` 等）。修复后重新统计。若总数减少，视为新增 Blocker：

> "🚫 Blocker: 修复后断言数量从 12 减少到 9（文件: tests/user.test.ts）"

## 工作区洁净协议

| 时机 | 检测 | 失败处理 |
|------|------|----------|
| 批量启动前 | `git status --porcelain` 为空 | fail-fast（不自动 stash） |
| 每任务 Commit 2 后 | `git status --porcelain` 为空 | fail-fast |

## 检查点文件

每任务完成后写入 `docs/devdocs/.batch-checkpoint.json`：

```json
{
  "batch_id": "2024-01-15T10:30:00",
  "total_tasks": 5,
  "completed": [
    {"task": "T-01", "status": "success", "commit1": "abc1234", "commit2": "def5678"},
    {"task": "T-02", "status": "success", "commit1": "111aaaa", "commit2": "222bbbb"}
  ],
  "current": "T-03",
  "remaining": ["T-03", "T-04", "T-05"],
  "resume_command": "/devdocs-dev-workflow T-03~T-05 --headless"
}
```

用途：
- 上下文压缩后仍可读取检查点恢复批量状态
- fail-fast 后提供精确续做信息
- 批量完成后生成交付报告的数据源

## 交付报告模板

### 成功

```markdown
# 交付报告

## 批量执行结果: ✅ 全部成功

| 任务 | 状态 | Commit 1 | Commit 2 | 测试摘要 |
|------|------|----------|----------|----------|
| T-01 | ✅ | abc1234 | def5678 | UT-001~003 通过, 覆盖率 85% |
| T-02 | ✅ | 111aaaa | 222bbbb | UT-004~006 通过, 覆盖率 82% |

## 统计
- 总任务数: 2
- Blocker 已修复: 3
- Suggestion 已跳过: 5
- 总耗时: 由编排器记录
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

## 续做命令
/devdocs-dev-workflow T-03~T-05 --headless
```

## 失败续做

fail-fast 后输出的续做命令格式：

```
⚠️ 批量执行中断于 T-XX

已完成: T-01, T-02（已 commit）
失败: T-XX — [失败原因]
未执行: T-YY, T-ZZ

续做命令:
/devdocs-dev-workflow T-XX~T-ZZ --headless
```
