# 对抗式验证流程详解

> ⚠️ **layout.v1 legacy 标注上下文** — 本文件中 `@satisfies` / `@verifies` 检查项属于 layout.v1 机制。**layout.v2 起改读 `traceability.yml`**；legacy retained 检查项在 v1 项目仍生效。v2 接口落地状态见 [skills/pipeline/references/layout/docs-layout-migration.md § 执行接口落地状态](../../pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)。

## 理念

### 为什么需要对抗式验证？

开发者审查自己的代码容易产生盲区——"我写的时候觉得没问题"。对抗式验证通过**两种互补机制**缓解该盲区：

1. **Phase 1~3（内置角色演绎）**：编排器切换到不同视角（/code-quality / /testing-guide / ui-quality-checklist），在**同进程**内审查。成本低、响应快，但本质仍是"同一个 agent 切视角自审"。
2. **Phase 4（外部独立审查）**：调用**不同进程、不同模型**的外部审查者（codex CLI / codex-mcp），对 git diff 做真正的第三方审查。成本较高但独立性强，🔴 任务默认触发。

两类机制并行运行、各自判定：Phase 1~3 产出 `INT_*` canonical state（`INT_REVIEWED` / `INT_PENDING` 等），Phase 4 产出 `EXT_*` canonical state（见下方真值表）。任务进入 Commit 1 需两类 state 同时"放行态"。

### 核心原则

```
1. 角色分离：Phase 1~3 在审查时切换到不同视角，应用不同 Skill 的约束
2. 独立源验证：Phase 4 调用外部不同进程/模型的审查者，不被主编排器解释层污染
3. 问题分级：区分必须修复（Blocker）和建议修复（Suggestion）
4. 闭环验证：修复后重新验证，确保问题真正解决
5. 证据留痕：所有审查产出（角色演绎报告 / 外部 raw findings / yaml 摘要 / Commit trailer）三级协议存储
```

---

## Phase 1: 代码质量审查

### 审查角色

**代码审查员**（依据 `/code-quality` MTE 原则）

### 审查清单

#### M - 可维护性

- [ ] 函数职责单一（一个函数只做一件事）
- [ ] 函数长度 ≤ 50 行
- [ ] 参数数量 ≤ 5 个（超过使用参数对象）
- [ ] 嵌套深度 ≤ 3 层（使用早返回减少嵌套）
- [ ] 命名清晰准确（不使用缩写）
- [ ] 无重复代码（Rule of Three: 3 次以上才提取）

#### T - 可测试性

- [ ] 依赖可注入（不硬编码依赖）
- [ ] 纯函数优先（相同输入相同输出）
- [ ] 业务逻辑与 IO 分离

#### E - 可扩展性

- [ ] 不为假设需求设计（YAGNI）
- [ ] 接口抽象合理（不过度抽象）
- [ ] 只有 1 个实现时不创建接口（除非为了测试）

#### 安全检查

- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险
- [ ] 敏感数据正确处理（不 log 密码、Token 等）
- [ ] 错误信息不泄露内部实现细节

### Phase 1 输出格式

```markdown
## Phase 1: 代码质量审查报告

**审查角色**: 代码审查员 (基于 /code-quality MTE 原则)

### 🚫 Blocker

| # | 文件:行号 | 问题 | 说明 |
|---|----------|------|------|
| 1 | `src/x.ts:45` | 函数过长 (87行) | 拆分为多个职责单一的函数 |

### 💡 Suggestion

| # | 文件:行号 | 问题 | 说明 |
|---|----------|------|------|
| 1 | `src/x.ts:12` | 4个参数 | 建议使用参数对象 |

### ✅ 良好实践

- 依赖注入使用正确
- 命名清晰准确
```

---

## Phase 2: 测试完备性审查

### 审查角色

**测试审查员**（依据 `/testing-guide` 约束）

### 审查清单

#### 覆盖率

- [ ] 行覆盖率 ≥ 80%
- [ ] 分支覆盖率 ≥ 80%

#### 断言质量

- [ ] 每个测试有 ≥1 个具体断言
- [ ] 无弱断言作为唯一断言（toBeDefined, toBeTruthy, not.toBeNull）
- [ ] 测试名称描述预期行为

#### 需求追溯

- [ ] 每个 AC 有对应测试
- [ ] 测试代码有 @verifies 标注
- [ ] 测试代码有 @testcase 标注

#### Mock 质量

- [ ] 只 Mock 外部依赖，不 Mock 内部实现
- [ ] Mock 验证了调用参数
- [ ] 无过度 Mock

#### [可选] 代码分支覆盖分析

- [ ] 代码分支已分析
- [ ] 未覆盖分支已生成 BCA 补充测试

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

### Phase 2-UI（仅 🟢 UI 层任务）

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

S8 AC 完备性表 / 类型×证据矩阵 / 声称-vs-diff 交叉验证已是所有层级强制，见 [SKILL.md §完成检查约束](../SKILL.md)。Phase 1~3 不重复执行 AC 表，只在 Phase 3 综合报告中复用 S8 产出的判定结果。

详细 AC 类型分类、证据矩阵、可复核判据见 [SKILL.md 同章节末尾说明 + AC 完备性表模板](../SKILL.md)。

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

修复前快照所有 `@verifies` 和 `@testcase` 标注集合。
修复后重新扫描。若任何标注被移除，视为新增 Blocker：

> "🚫 Blocker: 修复过程中移除了 @verifies AC-003 标注（文件: tests/user.test.ts:20）"

### 断言数量不减检测

修复前统计测试文件中断言调用总数（`expect`/`assert`/`should` 等）。
修复后重新统计。若总数减少，视为新增 Blocker：

> "🚫 Blocker: 修复后断言数量从 12 减少到 9（文件: tests/user.test.ts）"

---

## Blocker 判定标准

### 代码质量 Blocker

| 问题 | 阈值 | Blocker 判定 | 依据 |
|------|------|-------------|------|
| 函数长度 | > 50 行 | 🚫 Blocker | /code-quality 最大 50 行 |
| 函数长度 | 30-50 行 | 💡 Suggestion | /code-quality 建议 30 行 |
| 嵌套深度 | > 3 层 | 🚫 Blocker | /code-quality 最大 3 层 |
| 嵌套深度 | 2-3 层 | 💡 Suggestion | /code-quality 建议 2 层 |
| 重复代码 | > 3 处相同 | 🚫 Blocker |
| 安全漏洞 | 任何 | 🚫 Blocker |

### 测试完备 Blocker

| 问题 | 阈值 | Blocker 判定 |
|------|------|-------------|
| 弱断言 | 作为唯一断言 | 🚫 Blocker |
| 覆盖率 | < 60% | 🚫 Blocker |
| 覆盖率 | 60-80% | 💡 Suggestion |
| AC 无对应测试 | 任何 | 🚫 Blocker |
| 缺少 @verifies 标注 | 核心逻辑 | 🚫 Blocker |

---

## Phase 4: 外部对抗审查（embedded-headless 模式）

Phase 4 由 dev-workflow 编排器在 S9 自审（Phase 1~3）之后、S10 之前调用。**🔴 任务默认触发**；🟡/🟢/⚪ 通过 `--external-review` 显式启用。

### 为什么不直接调用 /adversarial-review skill？

`/adversarial-review` 本质是 multi-turn 协调器（展示原始发现 → 逐条验证 → AskUserQuestion 接受/驳回循环）。作为子 Agent 被 Task tool 调用时，内部 AskUserQuestion 会阻塞或被吞掉。因此 dev-workflow **不调用整个 skill**，而是自带轻量调度器，**复用 `/adversarial-review` 的 `references/external-reviewer-integration.md` 三级降级链和熔断协议**。

> `/adversarial-review` skill 仍可被用户独立调用（交互式审查场景）。两种使用模式互不冲突。

### Phase 4 调度器契约

```
┌─ Phase 4 调度器（dev-workflow 编排器内置） ─────────────────┐
│                                                            │
│  1. 准备 brief：自动生成，包含任务 AC / Phase 1~3 综合报告 │
│     / 本任务 git diff（注意：不要暴露 Phase 1~3 的结论，   │
│     避免污染外部审查者视角）                                │
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
│             { prompt: "<brief>", uncommitted: true }       │
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

**默认轮次**：`max_rounds=3`（dev-workflow 嵌入收紧值）。`--external-rounds N` 覆盖上限 5（对齐 /adversarial-review 自身默认）。

**无 T3 兜底**：dev-workflow embedded-headless 模式**仅采用 T1/T2**真外部通道，不复用 /adversarial-review skill 的 T3 Task 子 Agent（T3 是同进程独立上下文，不满足"独立审查"承诺）。T1/T2 全失败 → `EXT_UNRESOLVED` → --headless 立即 fail-fast；交互模式由用户选择手动补跑或终止。

### 双通道 `external_review_channel_used`（非状态字段）

| 通道 | 触发调用 | 语义 |
|-----|---------|------|
| `T1` | codex CLI | 真正外部独立审查（不同进程/不同模型），首选 |
| `T2` | codex-mcp | 真正外部独立审查，T1 不可用时降级 |

🔴 任务 Phase 4 **必须落到 T1 或 T2 通道并达成 `EXT_REVIEWED`** 才能放行；T1/T2 全失败 → `EXT_UNRESOLVED`。

### Canonical state enum `EXT_*`

**所有文档、约束、续做信号表、Step 1.5 [D2] 校验失败分支、Commit 1 尾注字段、场景回放描述必须仅使用下表常量**，禁用 `external_reviewed` / `external_review_pending` / `CONVERGED` / `DEGRADED` / `SKIPPED` / 单独的 `reviewed` 等非 canonical 词汇。

| 状态 ID | 触发条件 | 优先级 | 唯一恢复动作 | 放行 |
|---------|---------|--------|-------------|------|
| `EXT_REVIEWED` | T1/T2 + status=success + blockers=[] + L2 yaml 可读 | 4（终态） | —（无需恢复） | ✅ |
| `EXT_PENDING` | `--skip-external-review-reason` 登记主动跳过 | 3 | 事后补跑 Phase 4，产出 L2 yaml | ❌ |
| `EXT_UNRESOLVED` | T1/T2 全失败 / L2 yaml 缺失或不可读 | 2 | 交互模式 AskUserQuestion 手动补跑或终止；headless fail-fast | ❌ |
| `EXT_BLOCKED` | `breaker_reason=safety_limit`（达 max_rounds 未收敛） | 1（最高） | 交互模式用户可解除 max_rounds += 3 重跑；headless fail-fast | ❌ |

### 非状态字段（派生输入）

本身不是状态枚举，但作为 `EXT_*` 判定的派生输入参与计算：
- `external_review_channel_used: T1 | T2 | none`——实际生效的调用通道

此字段同时写入 L1 尾注（非状态字段区）和 L2 yaml 摘要的 `summary.details`。

### 状态判定真值表

**按优先级从高到低执行，命中即返回，下游规则不再评估**：

| 优先级 | 输入组合 | → `ext_review_state` | 说明 |
|-------|---------|----------------------|------|
| 1 | `breaker_reason=safety_limit` | `EXT_BLOCKED` | 熔断终态 |
| 2 | L2 yaml 缺失或不可读（Phase 4 运行时产出失败 / Step 1.5 [D2] 续做校验失败） | `EXT_UNRESOLVED` | **必须优先于 `EXT_REVIEWED` 判定**——无可复核证据不得放行 |
| 3 | `--skip-external-review-reason="..."` 登记 | `EXT_PENDING` | 主动跳过，待补跑 |
| 4 | `channel∈{T1,T2} ∧ status=success ∧ blockers=[]`（且规则 2 未命中） | `EXT_REVIEWED` | 外审通过，**唯一**放行分支 |
| 5 | `channel∈{T1,T2} ∧ (status!=success ∨ blockers!=[])` 或 T1/T2 全失败 | `EXT_UNRESOLVED` | Phase 4 单轮未通过（已达 max_rounds 由规则 1 捕获） |
| fallback | 以上均不命中（应不可达） | `EXT_UNRESOLVED` | 安全阀，同时产生诊断日志 |

**互斥性保证**：规则按优先级**唯一命中**一条（高优先级短路低优先级），任一输入组合有且仅有一个 `EXT_*` 映射。

**优先级冲突澄清**：
- 规则 1（safety_limit）是硬终态，优先于其他规则
- 规则 2（L2 证据缺失）优先于规则 4（EXT_REVIEWED）——防止"T1/T2 + status=success + blockers=[] + L2 缺失"被误判为 `EXT_REVIEWED`

> **P0-A 澄清**：`EXT_PENDING` 在所有放行路径下都为 ⛔ 阻塞 Commit 1，无例外。`--skip-external-review-reason="<原因>"` 仅登记跳过原因 + 自动标 `EXT_PENDING` + 留 `Skip-External-Review-Reason:` 尾注，**不构成 Commit 1 放行**。补跑 Phase 4 达成 `EXT_REVIEWED` 后方可进入 Commit 1。

### 证据协议（L2 为权威源）

| 层级 | 存储位置 | 权威性 | 生成时机 |
|------|---------|-------|---------|
| L2 摘要（**唯一权威**） | `docs/devdocs/audit/<T-XX>-external-review.yaml` | **Step 1.5 [D2] 唯一消费源**，schema 见下方"L2 最小必需 schema" | Phase 4 调度器每轮结束产出 |
| L1 尾注（**派生**） | Commit 1 message trailer | L1 由 L2 自动派生（`External-Review-Verdict` 值直接读自 L2 的 `ext_review_state`，`health_scores` / rounds / channel 等也从 L2 读取），不作为独立校验来源 | Commit 1 生成时读 L2 填充 |
| L3 原始（**可选调试**） | `docs/devdocs/audit/<T-XX>-external-review-raw/<round-N>.txt` | 调度器保存每轮 codex 原始输出以便人工 debug，**不是门禁要求**——缺失或损坏不影响状态判定 | Phase 4 调度器可选产出 |

**L2 最小必需 schema**（Phase 4 调度器必须产出；缺键视为 L2 无效）：

```yaml
ext_review_state: EXT_REVIEWED | EXT_PENDING | EXT_UNRESOLVED | EXT_BLOCKED   # 必需：canonical enum 之一
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
- `ext_review_state` 属于 canonical enum 的 4 个值之一
- `health_scores` 长度等于 `rounds`
- `blockers` 为数组类型
- 任一失败 → `EXT_UNRESOLVED`（真值表规则 2）

不再校验 L1↔L2 一致性（L1 由 L2 派生，结构上同源）或 L3 存在性（L3 已降为可选）。

### 双 skip 禁令

`--skip-review-reason` + `--skip-external-review-reason` 同时使用 → ⛔ 非法参数组合（恢复方式：删除其中一个）。不设例外通道——实际遇到需要跳过 Phase 1~3 和 Phase 4 的场景极少，且任何"例外通道"都会被滥用为常规路径；与其用复杂的 Emergency-Mode 授权链软化禁令，不如让两个 skip 参数互斥，遇到真需要时手动在 diff 上跑一次 T1/T2 外审做证据补跑。
