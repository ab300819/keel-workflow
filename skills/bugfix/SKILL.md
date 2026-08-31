---
name: ms-bugfix
description: Test-first bug fixing workflow. Guide users through reproducing bugs, writing failing tests, fixing code, and committing with regression protection. Use when users report bugs or issues. Triggers on "bug", "fix", "issue", "崩溃", "报错", "修复", "出错了", "不工作", "broken", "regression", "error", "异常". NOT for new features (use ms-feature), insight-driven improvements (use ms-insights), or issue fixes in non-DevDocs projects (use dev-flow).
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, Task
metadata:
  patterns: [inversion, pipeline]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# Bug 修复

测试先行的 Bug 修复流程，确保每个修复都有回归测试保护和完整记录。

## 快速开始

**一句话**: 测试先行的 Bug 修复流程，确保回归保护。

**最常见用法**: `/ms-bugfix`（描述 Bug 后自动评估复杂度）

**不适合?** 新功能→`/ms-feature`，代码质量改进→`/ms-insights`

## 运行模式

```bash
/ms-bugfix                    → 标准修复（自动评估复杂度）
/ms-bugfix BUG-XX realign     → 规范升级回扫：按 BUG-XX 过滤调度相关 skill --realign（仅补齐已完成 bug 流程的规范差距，不触发再修复）
```

> **Realign 模式**：已完成的 bug 修复记录（BUG-XX 条目、测试、修复代码）在 DevDocs 规范升级后按新 spec_version 查漏补缺。共享契约见 [../pipeline/references/realign.md](../pipeline/references/realign.md)。调度策略：按 BUG-XX 的 `关联` 字段追溯对应 F-XX 与 T-XX，委托 `/ms-dev-workflow <T-XX> --realign`。推荐用户入口 `/ms-pipeline realign`。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 触发条件

- 用户报告 Bug 或问题
- 用户提到"修复"、"bug"、"issue"、"崩溃"、"报错"
- 用户提供 Issue 编号或链接
- 测试执行失败（UT/IT/E2E）

## 核心理念

```
先证明 Bug 存在（失败测试），再修复代码，最后证明 Bug 已修复（测试通过）。
每个 Bug 都要记录，形成知识沉淀。
```

## Bug 复杂度判断

| 复杂度 | 特征 | 流程 |
|--------|------|------|
| **简单** | 单文件/单函数、原因明确 | 本 Skill 直接修复 |
| **复杂** | 多模块、需拆分步骤、原因不明 | **必须**走 `/ms-dev-tasks` |

## 工作流程

```
1. 理解 Bug + 评估复杂度
   │
   ├── 复杂 Bug → **必须** /ms-dev-tasks 拆分任务
   │              （用户明确选择"继续简单流程"时除外）
   │
   └── 简单 Bug → 继续
   │
   ▼
2. 定位代码 + 根因确认
   │
   ├── 原因明确 → 继续
   └── 原因不明 → 根因诊断门（见下节）
        ├── 根因证实 → 继续
        └── 连续 2 轮假设全部证伪 → ⚠️ 必须确认
            恢复方式:用户选择转 /ms-dev-tasks 拆分诊断任务,或提供新线索后重进诊断门
   │
   ▼
3. 编写失败测试（证明 Bug 存在）
   │
   ├── 测试通过 → ⚠️ Bug 未复现，重新确认
   └── 测试失败 → ✅ 继续
   │
   ▼
4. 修复代码
   │
   ▼
5. 运行测试
   │
   ├── 测试失败 → 返回步骤 4
   └── 测试通过 → ✅ 继续
   │
   ▼
6. 记录 Bug（追加到 05-bugfix-log.md）
   │
   ▼
7. 询问用户：是否提交？
   │
   └── 生成 fix() 提交信息
```

### 根因诊断门（原因不明时必过）

> 目的:禁止"未理解就修"(shotgun debugging)。范围简单但原因不明的 Bug 走此门,不必直接升级 dev-tasks;吸收结论见 [docs/workflows.md § 与 superpowers 共存](../../docs/workflows.md#与-superpowers-共存)。

1. **复现基线**:固定稳定复现条件(输入、环境、步骤);无法稳定复现 → 先解决复现,不进入假设。
2. **假设清单**:列出候选根因,按可能性排序;每条假设写明"若成立,应观察到什么"。
3. **最小仪器化**:对首选假设做最小验证(定点日志/断点/最小实验),**只为证伪或证实,不顺手改逻辑**。
4. **证伪确认**:假设被证实 → 根因成立,进入失败测试(测试断言应指向该根因);被证伪 → 划掉,取下一条;一轮清单耗尽为一轮。

⛔ 禁止继续:根因未经步骤 4 证实即开始修复代码
恢复方式:回到诊断门完成证实,或走 ⚠️ 升级分支(转 /ms-dev-tasks / 用户提供新线索)。

## 输出文件

**Bug 修复日志**：`docs/devdocs/05-bugfix-log.md`

## Bug 编号规则

| 类型 | 前缀 | 格式 | 说明 |
|------|------|------|------|
| Bug 记录 | BUG | BUG-XXX | Bug 修复记录编号 |

编号延续现有文档中的最大编号。

## Step 1: 理解 Bug

收集 Bug 信息：

| 信息 | 来源 | 必要性 |
|------|------|--------|
| Bug 描述 | 用户输入 | **必须** |
| 复现步骤 | 用户输入 | 建议 |
| 预期行为 | 用户输入 | 建议 |
| 实际行为 | 用户输入 | **必须** |
| 发现来源 | 测试编号/手动测试/用户反馈 | **必须** |
| 关联功能 | F-XXX / AC-XXX，或 `baseline` | **必须** |
| Issue 编号 | 用户输入 | 可选 |

如信息不足，使用 AskUserQuestion 询问。

**基线项目的 Bug**：基线项目（有 `00-baseline.md` 且无 `01`~`04`；`05-bugfix-log.md` 等其他产物不影响判定）修的是基线前的存量代码，
它没有 F 编号，也**不该临时编一个**——临时编号是「推导出没人决定过的结论」的老毛病。
此时「关联功能」填 `baseline`，回归测试仍必须写；追溯写进文档侧的 Bug 记录，⛔ 代码内不写编号标注。

`bugfix/SKILL.md` 已近 500 行硬限，本段为等量替换，勿再扩写。

### 复杂度评估

使用 AskUserQuestion 确认：

```
根据 Bug 描述，评估复杂度：

[ ] 涉及多个模块/文件
[ ] 原因不明确，需要深入分析
[ ] 修复可能影响其他功能
[ ] 需要多个步骤完成

⚠️ 如以上任一命中，**必须**走 /ms-dev-tasks 拆分任务。
确定要跳过任务拆分，继续简单流程吗？[使用任务拆分(推荐)/继续简单流程]
```

## Step 2: 定位代码

搜索策略：

1. **关键词搜索**：根据 Bug 描述搜索相关代码
2. **错误信息搜索**：搜索报错信息中的关键字
3. **测试定位**：从失败的测试用例定位
4. **用户指定**：用户直接提供文件路径

向用户确认定位结果。

## Step 3: 编写失败测试

### 测试命名规范

```
should [预期行为] when [触发条件]
```

### 测试结构

```typescript
/**
 */
describe('Bug fix: BUG-XXX <Bug 描述>', () => {
  it('should <预期行为> when <条件>', () => {
    // Arrange - 构造触发 Bug 的条件
    // Act - 执行操作
    // Assert - 验证预期行为
  });
});
```

### 验证测试有效性

运行测试，确认测试失败：

- **测试失败** ✅ → Bug 已复现，继续修复
- **测试通过** ⚠️ → Bug 未复现，需重新确认

## Step 4: 修复代码

### 修复原则

- [ ] **最小改动**：只修改必要的代码
- [ ] **不引入新功能**：修复 Bug，不顺便重构
- [ ] **遵循现有风格**：与周围代码保持一致

### 修复约束

参考 `/code-quality` 约束。

## Step 5: 运行测试

```bash
# 运行新增的 Bug 修复测试
npm test -- --testNamePattern="Bug fix"

# 运行全部测试，确保没有引入回归
npm test
```

- **新测试通过 + 全部测试通过** ✅ → 修复完成
- **新测试失败** → 返回步骤 4 继续修复
- **其他测试失败** → 检查是否引入回归

## Step 6: 记录 Bug

### 记录模板

追加到 `docs/devdocs/05-bugfix-log.md`：

```markdown
## BUG-XXX: <Bug 标题>

| 属性 | 内容 |
|------|------|
| **发现来源** | UT-XXX / IT-XXX / E2E-XXX / 手动测试 / 用户反馈 |
| **关联功能** | F-XXX, AC-XXX（或 `baseline`：涉及基线前代码） |
| **Issue** | #123（如有）|
| **严重程度** | P0 / P1 / P2 |
| **修复日期** | YYYY-MM-DD |
| **状态** | ✅ 已修复 |

### 问题描述

<Bug 现象描述>

### 复现步骤

1. <步骤1>
2. <步骤2>
3. <观察到的错误>

### 根因分析

<为什么会出现这个问题，技术层面的原因>

### 解决方案

<如何修复的，修改了什么>

### 回归测试

- 新增测试：UT-XXX / IT-XXX
- 关联 commit：`<commit-hash>`

### 经验教训（可选）

<避免类似问题的建议，供团队参考>

---
```

### 记录要点

| 字段 | 说明 | 必填 |
|------|------|------|
| 发现来源 | 哪个测试/谁发现的 | **必须** |
| 关联功能 | 涉及哪个功能点（F-XXX / AC-XXX）；基线前的存量代码填 `baseline` | **必须** |
| 根因分析 | 技术层面的原因 | **必须** |
| 解决方案 | 如何修复的 | **必须** |
| 回归测试 | 新增的测试编号 | **必须** |

## Step 7: 提交

> `workspace_context.mode` 不是 `inline` 时（即代码不在本仓）提交走 N+1 仓协议（含 detached HEAD 前置门与跨仓 Recovery），见 [workspace-topology/references/protocol.md § N+1 仓提交协议](../workspace-topology/references/protocol.md)。代码根路径取自 握手 `workspace_context`（[_shared/constraints.md](../_shared/constraints.md) §3 `task/workspace-context`；未传入时按 `inline` 缺省）。修复代码提交进对应子模块（commit message 沿用该仓风格、**不带 BUG-XX 编号**），bugfix 日志提交进外壳仓。`mode` 为 `linked` 时代码根不归本仓所有，各仓各自提交、⛔ 不 bump 指针，见 [protocol.md §6.5](../workspace-topology/references/protocol.md#65-linked-下无-n1无指针)。

### 提交前检查

- [ ] 全部测试通过

### 提交信息格式

遵循 `/commit-convention`：

```
fix(<scope>): <简述问题>

- 根因：<问题原因>
- 修复：<解决方案>
- 测试：<新增测试编号>

BUG-XXX
Fixes #<issue-number>
```

**示例**：

```
fix(auth): handle empty username in login

- 根因：login() 未校验空用户名，直接查询数据库导致异常
- 修复：添加用户名非空校验，返回明确错误信息
- 测试：UT-025

BUG-003
Fixes #123
```

## 与测试用例的闭环

```
测试执行（UT/IT/E2E）
    │
    ├── 通过 → 正常
    │
    └── 失败 → 触发 /ms-bugfix
                    │
                    ├── 记录 BUG-XXX（关联测试编号）
                    │
                    ├── 修复代码
                    │
                    ├── 新增回归测试（更新测试编号）
                    │
                    └── /ms-sync 更新追溯矩阵
```

## 编排规范（子 Agent 调度）

复杂 Bug 路径下，ms-bugfix 调用子技能时**必须通过 Task tool 启动子 Agent**：

| 场景 | 被调度技能 | 调度方式 |
|------|-----------|----------|
| 复杂 Bug 拆分 | `/ms-dev-tasks` | Task tool 子 Agent |
| 复杂 Bug 开发 | `/ms-dev-workflow` | Task tool 子 Agent |
| 文档同步 | `/ms-sync` | Task tool 子 Agent |

### 调度原则

1. **上下文隔离**：每个子 Agent 自行读取所需文档，bugfix 编排层不传递全文
2. **摘要传递**：只接收子 Agent 返回的 YAML 摘要，据此决定下一步
3. **异常回退**：子 Agent 返回 `status: failed` + `blockers` 时，展示阻塞项询问用户
4. **不自行排障**：编排层不读取子技能的完整输出文档来尝试修复

> 简单 Bug 因流程短（单文件修复），直接在 bugfix 上下文内执行，不启动子 Agent。

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 复杂 Bug 拆分 | `/ms-dev-tasks` | 多步骤 Bug 走任务拆分 |
| 回归测试设计 | `/ms-test-cases` | 补充回归测试到测试文档 |
| 需求缺失 | `/ms-requirements` | Bug 暴露需求问题时调用 |
| 测试编写 | `/testing-guide` | 测试代码质量约束 |
| 代码修改 | `/code-quality` | 修复代码质量约束 |
| 文件操作 | `/git-safety` | 使用 git mv/rm |
| 提交信息 | `/commit-convention` | 提交规范 |
| 文档同步 | `/ms-sync` | 修复后更新追溯矩阵 |

## 约束

### 流程约束

- [ ] **必须先编写失败测试，再修复代码**
- [ ] **原因不明时必须过根因诊断门，根因证实后才进入修复**（禁止 shotgun debugging）
- [ ] **⛔ 禁止继续：测试未通过时不得提交**（恢复方式：修复测试失败后重新运行）
- [ ] **复杂 Bug 走 dev-tasks + dev-workflow 时必须通过 Task tool 启动子 Agent**

### 记录约束

- [ ] **每个 Bug 必须记录到 05-bugfix-log.md**
- [ ] **必须记录发现来源**
- [ ] **必须记录根因分析**
- [ ] **必须记录解决方案**
- [ ] **必须关联回归测试编号**

### 追溯同步约束

- [ ] **修复完成后必须执行 `/ms-sync`**
- [ ] 新增的回归测试必须登记到 `03-test-*.md` 追溯矩阵

### 测试约束

- [ ] 禁止弱断言（参考 `/testing-guide`）

### 提交约束

- [ ] 提交信息包含 BUG-XXX 编号

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-bugfix
status: success | failed | partial
summary:
  headline: "BUG-003 已修复，新增回归测试 UT-025"
  details:
    bug_id: BUG-XXX
    complexity: simple | complex
    related: { feature: F-XXX | baseline, ac: AC-XXX | null }
    test_added: [UT-025]
    commit_hash: "abc1234"
blockers: []
output_files:
  - docs/devdocs/05-bugfix-log.md
new_ids:
  bugs: [BUG-XXX]
  unit_tests: [UT-025]
next_recommended:
  skill: ms-sync
```

## 特殊情况

### Bug 无法复现

```
⚠️ 测试通过，Bug 未能复现。

可能原因：
1. 复现条件不完整
2. Bug 已在其他提交中修复
3. 环境差异导致无法复现

建议：
- 确认复现步骤是否完整
- 检查最近的相关提交
- 与报告者确认环境信息
```

### 复杂 Bug

如 Bug 涉及多个模块或原因不明：

```
⚠️ 检测到复杂 Bug，**必须**使用任务拆分：

1. 使用 /ms-dev-tasks 拆分为多个子任务
2. 每个子任务独立修复和测试
3. 最后集成验证

确定要跳过任务拆分吗？[使用任务拆分(推荐)/继续简单流程]
```

> 默认必须走任务拆分，仅当用户明确选择"继续简单流程"时才允许跳过。

### Bug 暴露设计缺陷

如 Bug 暴露了设计问题：

```
1. 先用最小改动修复当前 Bug
2. 记录设计缺陷到"经验教训"
3. 创建改进建议（可选 /ms-insights）
4. 使用 /refactor 进行系统性改进
```
