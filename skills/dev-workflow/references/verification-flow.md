# 对抗式验证流程详解

## 理念

### 为什么需要对抗式验证？

开发者审查自己的代码容易产生盲区——"我写的时候觉得没问题"。对抗式验证通过**两种互补机制**缓解该盲区：

1. **Phase 1~3（内置角色演绎）**：编排器切换到不同视角（/code-quality / /testing-guide / ui-quality-checklist），在**同进程**内审查。成本低、响应快，但本质仍是"同一个 agent 切视角自审"。
2. **Phase 4（外部独立审查）**：调用**不同进程、不同模型**的外部审查者（codex CLI / codex-mcp），对 git diff 做真正的第三方审查。成本较高但独立性强，audit 默认 inline 触发；fast/guarded 延后到 `/ms-verify --review-drain`。

两类机制并行运行、各自判定：Phase 1~3 产出 `INT_*` canonical state（`INT_REVIEWED` / `INT_UNRESOLVED`），Phase 4 产出 `EXT_*` canonical state（见下方真值表）。**进入 Commit 1 的放行条件按 review_profile 分**：**audit** 任务需 `INT_*` 与 `EXT_*` 同时为"放行态"才能 Commit 1（独立审查 inline）；**fast/guarded** 任务独立审查延后,Commit 1 不等 INT/EXT 放行,提交后落 `review_pending`,经 `/ms-verify --review-drain` 通过才转 `已完成`（质量地板与 `/ms-verify --impl` 前置验证仍 inline 阻塞,不在延后范围）。

### 核心原则

```
1. 角色分离：Phase 1~3 在审查时切换到不同视角，应用不同 Skill 的约束
2. 独立源验证：Phase 4 调用外部不同进程/模型的审查者，不被主编排器解释层污染
3. 问题分级：区分必须修复（Blocker）和建议修复（Suggestion）——元语义以 /code-quality 反馈分级表为权威
4. 闭环验证：修复后重新验证，确保问题真正解决
5. 证据留痕：所有审查产出（角色演绎报告 / 外部 raw findings / yaml 摘要 / Commit trailer）三级协议存储
```

---

> **延后语义**:Phase 1~3(内置角色演绎)+ Phase 4(外部对抗)是**独立审查**,在 `review_profile=fast/guarded` 时延后到 `/ms-verify --review-drain` 集中执行,任务期间任务标 `review_pending`。`audit` 档 inline fail-fast(同今天 🔴)。质量地板与 `/ms-verify --impl` 前置验证**不延后,始终 inline**。

## Phase 1: 代码质量审查

### 审查角色

**代码审查员**（依据 `/code-quality` MTE 原则）

### 审查清单

> **清单与报告格式的权威在 [`/code-quality` review-rubric](../../code-quality/references/review-rubric.md)**（M/T/E + 设计原则 + 错误处理 + 安全检查 + 输出格式）；数字阈值以 [核心阈值表](../../code-quality/SKILL.md#核心阈值表) 为准；注释 / 命名 / 日志的黑名单以 [`/code-quality`](../../code-quality/SKILL.md) 对应规范节为准。**本文件不再镜像上游条目与数字**（守 `doc/reference-over-copy`；原镜像的同步义务无强制手段，见 AGENTS.md 记录的 health-lint 镜像 rule deferred）。

dev-workflow 私有的执行差异（**仅此三条不在上游**，Phase 1 执行时叠加）：

- `review/diff-only`：注释 / 命名 / 日志 / 错误处理四类**仅审本次 diff 新增或修改**的部分；M/T/E、设计原则、安全检查审全量受影响面。
- `review/legacy-suggestion`：本次未触碰的存量坏注释 / 坏命名 → 降为 Suggestion，不阻塞提交。
- `review/security-no-tier`：日志命中安全红线、注入 / XSS / 越权**不分档**，命中即 Blocker（不套用阈值三档谓词）。

---

## Phase 2: 测试完备性审查

### 审查角色

**测试审查员**（依据 `/testing-guide` 约束）

### 审查清单

> **清单权威在 [`/testing-guide` 单元测试约束](../../testing-guide/SKILL.md#单元测试约束)**（断言质量 / Mock 质量 / 追溯标注 / 分支覆盖分析）；覆盖率与断言阈值以 [核心阈值表](../../testing-guide/SKILL.md#核心阈值表) 为准。**本文件不再镜像**（理由同 Phase 1）。

dev-workflow 私有的执行差异：

- `review/ac-coverage`：每个 AC 必须有对应测试——这是 DevDocs 追溯要求，非 testing-guide 的覆盖率阈值，缺失即 Blocker 且不可用覆盖率达标抵消。

### Phase 2 输出格式

```markdown
## Phase 2: 测试完备性审查报告

**审查角色**: 测试审查员 (基于 /testing-guide 约束)

### 🚫 Blocker

| # | 文件:行号 | 问题 | 说明 |
|---|----------|------|------|
| 1 | `tests/x.test.ts:23` | 弱断言 | `toBeDefined()` 作为唯一断言 |

### 💡 Suggestion

| # | 文件:行号 | 问题 | 说明 |
|---|----------|------|------|
| 1 | `src/x.ts` | 分支覆盖 62% | 建议补充 guard clause 测试 |

### ✅ 良好实践

- AAA 结构使用正确
- 需求追溯标注完整
```

---

## Phase 2-UI（仅 🟢 UI 层任务）

🟢 UI 层在 Phase 2 之后追加的 UI 质量自查（静态代理指标 + 与 `/ms-verify --ui` 边界）由 [ui-quality-checklist.md](ui-quality-checklist.md) 唯一权威定义。本文件不重复转述。

---

## Phase 3: 综合审查报告

### 报告模板

```markdown
# 对抗式验证报告

## 任务信息
- 任务编号: T-XX
- 关联功能: F-XXX
- 验收标准: AC-XXX, AC-YYY
- 任务层级: 🔴 核心逻辑

## 验证结果摘要

| Phase | Blocker | Suggestion | 状态 |
|-------|---------|------------|------|
| 代码质量 | 0 | 2 | ✅ |
| 测试完备 | 1 | 1 | ❌ |
| UI 质量（仅 🟢） | 0 | 0 | ⏭️ 非 UI 任务跳过 |

## 总体结论

❌ 存在 1 个 Blocker，需修复后重新验证。

## 详细问题

### 🚫 Blocker (必须修复)

1. [Phase 2] `tests/x.test.ts:23` 弱断言 `toBeDefined()` 作为唯一断言
   - 建议: 替换为 `toBe('expected_value')` 或 `toEqual({...})`

### 💡 Suggestion (建议修复)

1. [Phase 1] `src/x.ts:12` 4个参数，建议使用参数对象
2. [Phase 2] `src/x.ts` 分支覆盖 62%，建议补充 guard clause 测试
```

> `--headless` 模式下：Suggestion 自动跳过（`--fix-suggestions` 时尝试单次修复，不重试）；
> Blocker 自动修复（最多 N 次），超限则 fail-fast。

---

## AC 完备性（S8 权威定义）

### AC 完备性表模板（S8 必须输出）

```markdown
| AC 编号 | AC 类型 | 证据类型 | 位置 | 判定 |
|---------|---------|---------|------|------|
| AC-001 | 行为型 | UT 断言 | tests/user.spec.ts:42 `it('拒绝空密码')` | ✅ 满足 |
| AC-002 | 行为型 | IT 断言 + 实现代码 | tests/auth.int.ts:15, src/auth.ts:88 | ✅ 满足 |
| AC-003 | 视觉型 | UI 清单 + --ui --live 截图 | ui-checklist §2-UI.2, artifacts/T-03-disabled.png | ✅ 满足 |
| AC-004 | 结构型 | 实现代码 | src/types.ts:42（新增 `UserRole` 枚举）| ✅ 满足 |
```

### AC 类型分类（S8 必须为每条 AC 标注）

| AC 类型 | 定义 | 典型例子 |
|---------|------|---------|
| **行为型** | 描述可观察的运行时行为（输入→输出、状态迁移、副作用）| "点击按钮后 API 返回 200"、"空密码时拒绝登录" |
| **视觉型** | 描述 UI 外观或交互状态 | "disabled 态显示灰色"、"hover 态显示 tooltip" |
| **结构型** | 描述代码/数据结构本身（类型定义、schema、配置项）| "导出 `UserRole` 枚举"、"数据库加 `deleted_at` 列" |

### 证据类型 × AC 类型分级矩阵

| 证据类型 | 行为型 AC | 视觉型 AC | 结构型 AC |
|---------|-----------|-----------|-----------|
| `UT 断言` / `IT 断言` / `E2E 断言` | ✅ 可作唯一证据 | ⚠️ 可作唯一证据（需覆盖状态） | ✅ 可作唯一证据 |
| `--ui --live 截图` / `--ui --live trace` | ❌ 不可作唯一证据 | ✅ 可作唯一证据 | ❌ 不适用 |
| `UI 清单`（未配断言/live） | ❌ 禁止 | ⚠️ 仅作辅助，必须配断言或 live | ❌ 不适用 |
| `实现代码`（无测试） | ❌ **禁止作唯一证据**（至少配一条测试） | ❌ 禁止 | ✅ 可作唯一证据 |
| `显式豁免（附原因）` | ⚠️ 仅限枚举白名单：第三方服务不可测 / 灰度功能关闭 / 平台 API 限制；每条豁免必须登记 artifact 路径或外部票据 | ⚠️ 同左 + **自动化成本过高（感知类视觉项）**（UI 特例，见 [ui-quality-checklist.md](ui-quality-checklist.md#blocker-项证据要求)，**不得**用于交互类 Blocker） | ⚠️ 同左 |

⛔ 违反分级表（例如行为型 AC 仅用"实现代码"做证据）→ S8 直接判失败，不得进入 S9/Commit 1（恢复方式：补一条 UT/IT/E2E 断言或走豁免枚举）。

### Step 1.5 [A] 可复核判据

证据栏引用的路径/行号存在、测试名在测试文件中能定位、artifact 文件可打开、AC 类型与证据类型符合分级表。任一不满足 → AC 表不可复核 → `verification_pending`。

---

## Phase 1~3 与 S8 AC 完备性表的关系

S8 AC 完备性表 / 类型×证据矩阵 / 声称-vs-diff 交叉验证已是所有层级强制，强制性约束见 [SKILL.md §完成检查约束](../SKILL.md#完成检查约束)。Phase 1~3 不重复执行 AC 表，只在 Phase 3 综合报告中复用 S8 产出的判定结果。

详细 AC 类型分类、证据矩阵、可复核判据见 [本文件 §AC 完备性](#ac-完备性s8-权威定义)（S8 权威定义）；强制性约束见 [SKILL.md §完成检查约束](../SKILL.md#完成检查约束)。

### 发现数：无下限

**允许 0 发现**，但须给出一句可复核判据说明为何无发现（例：本次 diff 仅 3 行配置变更，无新增分支与外部调用）。

> 不设最低发现数门槛。门槛本身即凑数激励——凑出的 ✅ 确认项挤占注意力，凑出的 Suggestion 会被修成 accretion（单向增生）。审查是否认真执行由判据可复核性保证，不由发现数量保证。

### 三种解决路径分类

每个发现必须归入以下三种路径之一：

| 路径 | 标记 | 含义 | 处理方式 |
|------|------|------|----------|
| 自动修复 | 🔧 | Agent 可直接修复 | 立即修复，修复后重新验证。**修复动作可以是删除或合并，不限于新增** |
| 行动项 | 📋 | 需记录待修，不阻塞当前任务 | 记录到 insights 或后续任务 |
| 详细解释 | 💬 | 非问题，但需说明理由 | 在报告中补充解释 |

**分类规则**：

- Blocker 只能是 🔧（必须当场修复；用删除消解也算 🔧）
- Suggestion 可以是 🔧、📋 或 💬
- ✅ 确认项固定为 💬

### Phase 3 综合报告补充章节

Phase 3 综合报告在标准章节外追加 "发现汇总"：

```markdown
## 发现汇总

| # | 发现 | 分级 | 路径 | 说明 |
|---|------|------|------|------|
| 1 | AC-002 无实际变更 | 🚫 Blocker | 🔧 自动修复 | 需补充实现 |
| 2 | 重复的入参校验（与 validator.ts 同逻辑） | 🚫 Blocker | 🔧 删除 | 删除本处，改调用既有 validator |
| 3 | utils.ts 未关联 AC | 💡 Suggestion | 📋 行动项 | 记录为技术债 |

<!-- 无发现时：写「本轮无发现」+ 一句可复核判据，不得用 ✅ 确认项凑数 -->
```

> 注：声称 vs 实际验证表已前移到 S8（约束见 [SKILL.md §完成检查约束](../SKILL.md#完成检查约束)，表模板见 [§AC 完备性](#ac-完备性s8-权威定义)），Phase 3 直接引用 S8 产出，不再重复生成。

## Blocker 修复流程

```
发现 Blocker
    │
    ▼
展示问题详情和修复建议
    │
    ▼
修复问题（触发修复安全网检测）
    │
    ▼
重新运行对应 Phase（不需全部重跑）
    │
    ├── 通过 → 继续提交流程
    └── 仍有 Blocker → 再次修复（最多 N 次，默认 3）
        └── 超过重试上限 → 标记任务失败，不提交
            ├── --headless 模式：fail-fast 终止批量
            └── 交互模式：AskUserQuestion 询问用户
```

---

## 修复安全网

修复 Blocker 或 Suggestion 时，以下检测自动执行（交互和 `--headless` 模式均生效）：

### 标注删减检测

修复前快照所有测试用例名集合。
修复后重新扫描。若任何标注被移除，视为新增 Blocker：

> "🚫 Blocker: 修复过程中删除了测试用例 `should reject invalid email`（文件: tests/user.test.ts:20）"

### 断言数量不减检测

修复前统计测试文件中断言调用总数（`expect`/`assert`/`should` 等）。
修复后重新统计。若总数减少，视为新增 Blocker：

> "🚫 Blocker: 修复后断言数量从 12 减少到 9（文件: tests/user.test.ts）"

---

## Blocker 判定标准

> **逐指标判定由上游阈值 + 上游谓词机械推导，本文件不再镜像**：
> - 代码质量 → [`/code-quality` 核心阈值表](../../code-quality/SKILL.md#核心阈值表)，谓词「≤ 建议值合规 / > 建议值且 ≤ 最大值 → Suggestion / > 最大值 → Blocker；无建议值的指标只有合规 / Blocker 两档」
> - 测试完备 → [`/testing-guide` 核心阈值表](../../testing-guide/SKILL.md#核心阈值表)，谓词「≥ 达标值合规 / ≥ 最低值且 < 达标值 → Suggestion / < 最低值 → Blocker」
>
> 两张上游表均自带谓词语义，原本文件的 20 行判定表每一行都可由此推出，无独立信息。**反馈分级元语义**（Blocker/Suggestion/Question/Nice 的含义与处置要求）以 [`/code-quality` 反馈分级表](../../code-quality/SKILL.md) 为权威。

dev-workflow 私有判定（**不可从上游推导**，故保留）：

| 情形 | 判定 | 为什么不能从上游推出 |
|------|------|---------------------|
| 安全漏洞 / 日志命中安全红线 / 注入·XSS·越权 | 🚫 Blocker（**不分档**） | 安全维度不套用阈值三档谓词 |
| 黑名单注释 / 命名，**本次 diff 新增或修改** | 🚫 Blocker | 上游无 diff 范围概念，见 `review/diff-only` |
| 黑名单注释 / 命名，**本次未触碰的存量**；public API 缺契约注释 | 💡 Suggestion | 同上，见 `review/legacy-suggestion` |
| AC 无对应测试 | 🚫 Blocker | DevDocs 追溯要求，非覆盖率阈值，不可用覆盖率达标抵消 |
| 核心逻辑无对应测试 | 🚫 Blocker | 同上 |

---

## Phase 4: 外部对抗审查（embedded-headless 模式）

Phase 4 由 dev-workflow 编排器在 S9 自审（Phase 1~3）之后、S10 之前调用。**audit 默认 inline 触发 Phase 4**；fast/guarded 延后到 `/ms-verify --review-drain`；非 audit 可用 `--review/--external-review` 临时叠加 inline。

### 为什么不直接调用 /adversarial-review skill？

`/adversarial-review` 本质是 multi-turn 协调器（展示原始发现 → 逐条验证 → AskUserQuestion 接受/驳回循环）。作为子 Agent 被 Task tool 调用时，内部 AskUserQuestion 会阻塞或被吞掉。因此 dev-workflow **不调用整个 skill**，而是自带轻量调度器，**复用 `/adversarial-review` 的 `references/external-reviewer-integration.md` 三级降级链和熔断协议**。

> `/adversarial-review` skill 仍可被用户独立调用（交互式审查场景）。两种使用模式互不冲突。

### Phase 4 调度器契约

```
┌─ Phase 4 调度器（dev-workflow 编排器内置） ─────────────────┐
│                                                            │
│  1. 准备 brief：任务 AC / Phase 1~3 综合报告 / 本任务 diff │
│     （diff 源按触发模式分离，见下方「diff 源」小节）        │
│     注意：不要暴露 Phase 1~3 的结论，避免污染外审视角      │
│                                                            │
│  2. T1 codex CLI（首选）                                   │
│     └── codex exec --sandbox read-only \                   │
│             --output-schema <json-schema> \                │
│             -o /tmp/round-<N>.json \                       │
│             "<brief>"                                       │
│         parse JSON → yaml-summary                          │
│                                                            │
│  3. T2 codex-mcp（T1 失败时）                              │
│     └── mcp__codex-mcp__review-code \                      │
│             inline: { prompt, uncommitted: true }          │
│             drain : { prompt } + 显式 diff 内容/commit 范围│
│         retry 轮询 → yaml-summary                          │
│                                                            │
│  4. 收敛循环（自动，无 AskUserQuestion）                   │
│     ├── blocker=[] → 收敛，导出 L2 yaml，可选落 L3          │
│     ├── blocker!=[] 且 round < max_rounds → 自动构建下一轮 │
│     │      brief（嵌入修复指引 + 前轮 findings），继续     │
│     ├── blocker!=[] 且 round==max_rounds → breaker_reason  │
│     │      =safety_limit，状态 EXT_BLOCKED                 │
│     └── 任何步骤 status=failed / T1/T2 全失败 → 状态       │
│             EXT_UNRESOLVED（headless 立即 fail-fast）      │
│                                                            │
│  5. 产出（L1 由 L2 派生生成）                               │
│     ├── L1 尾注：写 Commit 1 时从 L2 读取派生              │
│     ├── L2 权威：docs/devdocs/audit/<T-XX>-external-review │
│     │            .yaml（Step 1.5 [D2] 唯一消费源）         │
│     └── L3 可选调试：audit/<T-XX>-external-review-raw/     │
│           <round-N>.txt（不参与门禁）                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### diff 源（按触发模式分离）

Phase 4 有两条触发路径，**工作区 diff 只对其中一条有效**：

> ⚠️ 下表第一列的 `inline` 是**触发模式**的名字（audit 档在 Commit 1 之前触发），与拓扑 `workspace_context.mode` 的 `inline` **同名但无关**。本节提到拓扑时一律写全 `mode` 为 `inline`。

| 触发模式 | 发生时点 | diff 源 |
|---------|---------|--------|
| **inline**（audit） | Commit 1 **之前** | 工作区 diff（`uncommitted: true`）——此时工作区改动即本任务改动 |
| **drain**（fast/guarded，经 `/ms-verify --review-drain`） | Commit 1 **之后** | **该任务 Commit 1 的提交 diff** |

> ⛔ **drain 路径禁止使用工作区 diff**。Commit 1 已落盘时工作区为空，沿用 `uncommitted: true` 会让外审收到**空 diff**（即"审了但什么都没看到"）。
>
> ⛔ **`mode` 不是 `inline` 时，audit 档的工作区 diff 须逐 `code_root` 取并拼接**：`for root in code_roots: git -C <root> diff`。此时代码改动全在各代码根自身的仓里，本仓（外壳仓）的工作区 diff **只有一行子模块指针变化**（`linked` 下连这行都没有）——直接用它同样是空审，与上一条 drain 的失效形态相同、成因不同。

drain 侧定位规则（读任务台账，⛔ 不 grep git log）：

1. 从 `04-dev-tasks.md` 任务条目的 `commits` 字段取该任务 Commit 1 的 `<repository>@<sha>`。
2. 外审输入 = 该 Commit 1 的 diff。**Commit 2 是纯文档提交，不入外审输入。**
3. T2 通道 drain 侧须传入显式 diff 内容或 commit 范围（契约见 [external-reviewer-integration.md](../../adversarial-review/references/external-reviewer-integration.md)）。
4. **`mode` 不是 `inline` 时**：Commit 1 按代码根拆成 N 个 commit（见 [protocol.md N+1 仓提交协议](../../workspace-topology/references/protocol.md)）。drain 侧须**逐 code_root 定位并拼接**；外壳仓 Commit 2（文档 + 指针 bump）不参与。
5. diff 为空（任务确无代码变更）→ 记 `drain.empty_diff`，跳过 Phase 4 但**不判 `EXT_REVIEWED`**——无审查即无证据。

**默认轮次**：`max_rounds=3`（dev-workflow 嵌入收紧值）。`--external-rounds N` 覆盖上限 5（对齐 /adversarial-review 自身默认）。

**无 T3 兜底**：dev-workflow embedded-headless 模式**仅采用 T1/T2**真外部通道，不复用 /adversarial-review skill 的 T3 Task 子 Agent（T3 是同进程独立上下文，不满足"独立审查"承诺）。T1/T2 全失败 → `EXT_UNRESOLVED` → --headless 立即 fail-fast；交互模式由用户选择手动补跑或终止。

### 双通道 `external_review_channel_used`（非状态字段）

| 通道 | 触发调用 | 语义 |
|-----|---------|------|
| `T1` | codex CLI | 真正外部独立审查（不同进程/不同模型），首选 |
| `T2` | codex-mcp | 真正外部独立审查，T1 不可用时降级 |

audit 任务必须 `EXT_REVIEWED` 才能 Commit 1；fast/guarded 提交后标 `review_pending`，drain 达 `EXT_REVIEWED` 才转已完成。T1/T2 全失败 → `EXT_UNRESOLVED`。

### `EXT_*` 状态执行判定表

**值域与放行语义权威见 [_shared/constraints.md §独立审查状态机枚举](../../_shared/constraints.md)，本表为执行判定摘要**。所有文档、约束、续做信号表、Step 1.5 [D2] 校验失败分支、Commit 1 尾注字段、场景回放描述必须仅使用该值域常量，禁用 `external_reviewed` / `external_review_pending` / `CONVERGED` / `DEGRADED` / `SKIPPED` / 单独的 `reviewed` 等非 canonical 词汇。

| 状态 ID | 触发条件 | 优先级 | 唯一恢复动作 | 放行 |
|---------|---------|--------|-------------|------|
| `EXT_REVIEWED` | T1/T2 + status=success + blockers=[] + L2 yaml 可读 | 3（终态） | —（无需恢复） | ✅ |
| `EXT_UNRESOLVED` | T1/T2 全失败 / L2 yaml 缺失或不可读 | 2 | 交互模式 AskUserQuestion 手动补跑或终止；headless fail-fast | ❌ |
| `EXT_BLOCKED` | `breaker_reason=safety_limit`（达 max_rounds 未收敛） | 1（最高） | 交互模式用户可解除 max_rounds += 3 重跑；headless fail-fast | ❌ |

### 非状态字段（派生输入）

本身不是状态枚举，但作为 `EXT_*` 判定的派生输入参与计算：
- `external_review_channel_used: T1 | T2 | none`——实际生效的调用通道

此字段同时写入 L1 尾注（非状态字段区）和 L2 yaml 摘要的 `summary.details`。

### 状态判定真值表

> 枚举值域与放行态语义（canonical）权威见 [_shared/constraints.md §独立审查状态机枚举](../../_shared/constraints.md)；本表为**判定规则执行细节**的权威，两层不互相覆盖。

**按优先级从高到低执行，命中即返回，下游规则不再评估**：

| 优先级 | 输入组合 | → `ext_review_state` | 说明 |
|-------|---------|----------------------|------|
| 1 | `breaker_reason=safety_limit` | `EXT_BLOCKED` | 熔断终态 |
| 2 | L2 yaml 缺失或不可读（Phase 4 运行时产出失败 / Step 1.5 [D2] 续做校验失败） | `EXT_UNRESOLVED` | **必须优先于 `EXT_REVIEWED` 判定**——无可复核证据不得放行 |
| 3 | `channel∈{T1,T2} ∧ status=success ∧ blockers=[]`（且规则 2 未命中） | `EXT_REVIEWED` | 外审通过，**唯一**放行分支 |
| 4 | `channel∈{T1,T2} ∧ (status!=success ∨ blockers!=[])` 或 T1/T2 全失败 | `EXT_UNRESOLVED` | Phase 4 单轮未通过（已达 max_rounds 由规则 1 捕获） |
| fallback | 以上均不命中（应不可达） | `EXT_UNRESOLVED` | 安全阀，同时产生诊断日志 |

**互斥性保证**：规则按优先级**唯一命中**一条（高优先级短路低优先级），任一输入组合有且仅有一个 `EXT_*` 映射。

**优先级冲突澄清**：
- 规则 1（safety_limit）是硬终态，优先于其他规则
- 规则 2（L2 证据缺失）优先于规则 3（EXT_REVIEWED）——防止"T1/T2 + status=success + blockers=[] + L2 缺失"被误判为 `EXT_REVIEWED`

### 证据协议（L2 为权威源）

| 层级 | 存储位置 | 权威性 | 生成时机 |
|------|---------|-------|---------|
| L2 摘要（**唯一权威**） | `docs/devdocs/audit/<T-XX>-external-review.yaml` | **Step 1.5 [D2] 唯一消费源**，schema 见下方"L2 最小必需 schema" | Phase 4 调度器每轮结束产出 |
| L1 台账（**派生**） | 任务条目 `ext_review_state` | L1 由 L2 自动派生（值直接读自 L2 的 `ext_review_state`，`health_scores` / rounds / channel 等也从 L2 读取），不作为独立校验来源 | Commit 2 写文档时读 L2 填充 |
| L3 原始（**可选调试**） | `docs/devdocs/audit/<T-XX>-external-review-raw/<round-N>.txt` | 调度器保存每轮 codex 原始输出以便人工 debug，**不是门禁要求**——缺失或损坏不影响状态判定 | Phase 4 调度器可选产出 |

**L2 最小必需 schema**（Phase 4 调度器必须产出；缺键视为 L2 无效）：

```yaml
ext_review_state: EXT_REVIEWED | EXT_UNRESOLVED | EXT_BLOCKED   # 必需：canonical enum 之一
status: success | failed | partial | interrupted                              # 必需
blockers: []                                                                  # 必需（数组，可空）
rounds: N                                                                     # 必需（整数 ≥ 1）
health_scores: [N, N, ...]                                                    # 必需（长度 == rounds）
external_review_channel_used: T1 | T2 | none                                  # 必需
breaker_reason: safety_limit | null                                           # 必需（可为 null）
findings: []                                                                  # 可选
fallback_events: []                                                           # 可选
```

**Step 1.5 [D2] 一致性校验**（对齐上表 schema）：
- L2 yaml 文件存在且可被 YAML 解析
- 所有**必需键**均存在（`ext_review_state` / `status` / `blockers` / `rounds` / `health_scores` / `external_review_channel_used` / `breaker_reason`）
- `ext_review_state` 属于 canonical enum 的 3 个值之一（`EXT_REVIEWED` / `EXT_UNRESOLVED` / `EXT_BLOCKED`）
- `health_scores` 长度等于 `rounds`
- `blockers` 为数组类型
- 任一失败 → `EXT_UNRESOLVED`（真值表规则 2）

不再校验 L1↔L2 一致性（L1 由 L2 派生，结构上同源）或 L3 存在性（L3 已降为可选）。

---

## 延后审查与 review_pending(fast/guarded)

### review_pending 状态
- fast/guarded 任务 Commit 1 落盘后,独立审查(Phase 1~3 + Phase 4)未做 → 任务标 `review_pending`(**独立状态**——含义是"已提交待集中审",区别于 `EXT_UNRESOLVED` 的"审过但未通过")。
- 任务台账字段:`batch` / `due`(格式 `sprint:<id>` 或 `YYYY-MM-DD`,默认落盘日+3 工作会话)/ `pending_reason: deferred-fast|deferred-guarded`。⛔ 不写 commit 尾注。
- 转移:`review_pending` --(drain 无 Blocker)--> `已完成`;有 Blocker → fix-forward(见下)。

### `/ms-verify --review-drain` 集中清审
收集所有 `review_pending` 任务,按延后档位补跑 Phase 1~3 + Phase 4(复用 embedded-headless T1→T2 通道),逐任务出 verdict。

**外审输入**:drain 侧**必须**用该任务 Commit 1 的提交 diff,不得用工作区 diff——见上方 [§diff 源](#diff-源按触发模式分离)。

**drain 失败矩阵:**

| 场景 | 任务状态 | 退出 | 报告字段 |
|------|---------|:---:|---------|
| 单任务 Blocker | 保持 `review_pending` + fix-forward 入队 | 非0 | `drain.blockers[]` |
| 部分通过 | 过的转 `已完成`,未过保持 `review_pending` | 非0 | `drain.passed`/`drain.pending` |
| T1/T2 全失败 | 保持 `review_pending`(EXT_UNRESOLVED) | 非0 | `drain.channel_failure` |
| L2 yaml 无效 | 保持 `review_pending` | 非0 | `drain.invalid_evidence` |
| **Commit 1 diff 为空** | 保持 `review_pending`,**不判 `EXT_REVIEWED`** | 非0 | `drain.empty_diff` |
| **台账无 `commits` 记录，或 sha 解析不到** | 保持 `review_pending` | 非0 | `drain.commit_not_found` |
| 用户中断 | 已处理落定,余下保持 `review_pending` | 130 | `drain.interrupted_at` |
| headless fail-fast | 保持 `review_pending` | 非0 | `drain.headless_halt` |

> 共性:**任何非全通过 → 阻断 sprint close**。

### post-commit Blocker 恢复
- 默认 **fix-forward**:开修复任务追加新 commit,不 revert(原子提交已落盘)。
- revert 仅限"已落盘代码主动有害且 fix-forward 无法快速处理",罕见,须 AskUserQuestion 确认。
- 全部 fix-forward + 重新 drain 通过前,阻断 sprint close。
