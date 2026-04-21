# 对抗式验证流程详解

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

## Phase 2-UI: UI 质量自查（仅 🟢 UI 层）

> 在 Phase 2 完成后、Phase 3 综合报告之前执行。仅 🟢 UI 层任务触发。
> 详细审查清单见 [ui-quality-checklist.md](ui-quality-checklist.md)。

**审查输入**：S3 阶段 Test Agent 产出的 UI 验收清单
**审查角色**：UI 审查员（基于 ui-quality-checklist 静态代理指标）
**输出格式**：与 Phase 1/2 一致，Blocker / Suggestion 分级

Phase 3 综合报告汇总 Phase 1 + Phase 2 + Phase 2-UI（如有）的全部结果。

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

## 对抗式审查强化

### 声称 vs 实际验证

> **已前移到 S8（全层级必做）**，不再是 --review 触发的增强项。S9 对抗式验证**复用** S8 产出的"AC 完备性表 + 声称 vs 实际对比表"，不再单独生成。
>
> 详见 [execution-flow.md](execution-flow.md) S8 步骤和 [SKILL.md](../SKILL.md#完成检查约束) AC 完备性表模板。

机制原文（保留以便 S9 复用格式）：

1. **读取任务 AC**：从 `04-dev-tasks*.md` 获取当前任务声明的 AC 列表
2. **读取实际变更**：通过 `git diff` 获取本任务所有代码变更
3. **交叉验证**：
   - AC 声称已满足但 diff 中无相关变更 → 🚫 遗漏实现
   - diff 中有大量变更但未关联任何 AC → ⚠️ 多余改动（可能是附带重构）
4. **输出**：声称 vs 实际对比表（由 S8 产出，S9 直接引用）

```markdown
| AC | 声称状态 | 实际变更 | 判定 |
|----|---------|---------|------|
| AC-001 | ✅ 已满足 | src/user.ts +45 行 | ✅ 一致 |
| AC-002 | ✅ 已满足 | 无相关变更 | 🚫 遗漏 |
| — | — | src/utils.ts +20 行 | ⚠️ 未关联 AC |
```

### 最低发现数门槛

对抗式审查**至少报告 3 个发现**（问题或确认项），防止走过场式审查：

- 如实际问题不足 3 个，用 ✅ 确认项补齐（如"依赖注入使用正确"、"命名清晰"）
- 若审查后发现数 < 3，审查员必须说明为什么代码质量高到只有不足 3 个发现点
- 目的不是凑数，而是**确保审查过程认真执行**

### 三种解决路径分类

每个发现必须归入以下三种路径之一：

| 路径 | 标记 | 含义 | 处理方式 |
|------|------|------|----------|
| 自动修复 | 🔧 | Agent 可直接修复 | 立即修复，修复后重新验证 |
| 行动项 | 📋 | 需记录待修，不阻塞当前任务 | 记录到 insights 或后续任务 |
| 详细解释 | 💬 | 非问题，但需说明理由 | 在报告中补充解释 |

**分类规则**：

- Blocker 只能是 🔧（必须当场修复）
- Suggestion 可以是 🔧、📋 或 💬
- ✅ 确认项固定为 💬

### 强化后的 Phase 3 报告模板

Phase 3 综合报告额外追加以下章节：

```markdown
## 声称 vs 实际验证

| AC | 声称状态 | 实际变更 | 判定 |
|----|---------|---------|------|
| ... | ... | ... | ... |

## 发现汇总（≥ 3 项）

| # | 发现 | 分级 | 路径 | 说明 |
|---|------|------|------|------|
| 1 | AC-002 无实际变更 | 🚫 Blocker | 🔧 自动修复 | 需补充实现 |
| 2 | utils.ts 未关联 AC | 💡 Suggestion | 📋 行动项 | 记录为技术债 |
| 3 | 依赖注入使用正确 | ✅ 确认 | 💬 解释 | 构造函数注入，符合 MTE |
```

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
│  4. T3 Task 子 Agent（T1/T2 全失败时兜底）                 │
│     └── 起独立 prompt（无 AskUserQuestion 权限）           │
│         警告：T3 不是真外部，自动标 EXT_UNRESOLVED         │
│                                                            │
│  5. 收敛循环（自动，无 AskUserQuestion）                   │
│     ├── blocker=[] → 收敛，导出 L1/L2/L3 artifact          │
│     ├── blocker!=[] 且 round < max_rounds → 自动构建下一轮 │
│     │      brief（嵌入修复指引 + 前轮 findings），继续     │
│     ├── blocker!=[] 且 round==max_rounds → breaker_reason  │
│     │      =safety_limit，状态 EXT_BLOCKED                 │
│     └── 任何步骤 status=failed / 降级链全挂 → 状态         │
│             EXT_UNRESOLVED                                  │
│                                                            │
│  6. 产出                                                    │
│     ├── L1: Commit 1 尾注（External-Review-Verdict 等）   │
│     ├── L2: docs/devdocs/audit/<T-XX>-external-review.yaml │
│     └── L3: docs/devdocs/audit/<T-XX>-external-review-raw/ │
│           <round-N>.txt（原样 pass-through，每轮一个文件） │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**默认轮次**：`max_rounds=3`（dev-workflow 嵌入收紧值）。`--external-rounds N` 覆盖上限 5（对齐 /adversarial-review 自身默认）。

### 三级通道 `external_review_channel_used`（非状态字段）

| 通道 | 触发调用 | 语义 | 默认对应状态 |
|-----|---------|------|-------------|
| `T1` | codex CLI | 真正外部独立审查（不同进程/不同模型） | `EXT_REVIEWED`（当 status=success ∧ blockers=[] ∧ 证据完备） |
| `T2` | codex-mcp | 真正外部独立审查 | 同上 |
| `T3` | Task 子 Agent | **同进程独立上下文**，非真外部，仅兜底 | 自动 `EXT_UNRESOLVED`（覆盖其他判定，除非 Emergency-Mode 接受） |

🔴 任务 Phase 4 **必须落到 T1 或 T2 通道并达成 `EXT_REVIEWED`** 才能放行。

### Canonical state enum `EXT_*`

**所有文档、约束、续做信号表、Step 1.5 [D2] 校验失败分支、Commit 1 尾注字段、场景回放描述必须仅使用下表常量**，禁用 `external_reviewed` / `external_review_pending` / `CONVERGED` / `DEGRADED` / `SKIPPED` / 单独的 `reviewed` 等非 canonical 词汇。

| 状态 ID | 触发条件 | 优先级 | 唯一恢复动作 | 放行 |
|---------|---------|--------|-------------|------|
| `EXT_REVIEWED` | T1/T2 + status=success + blockers=[] + 证据完备 | 4（终态） | —（无需恢复） | ✅ |
| `EXT_PENDING` | `--skip-external-review-reason` 登记主动跳过；或 T3 经 Emergency-Mode 接受 | 3 | 事后补跑 Phase 4，产出 L1/L2/L3 完整证据 | ❌ |
| `EXT_UNRESOLVED` | 通道降级到 T3 / T1 T2 T3 全部 status!=success / 证据协议 L1/L2/L3 任缺一 | 2 | 交互模式 AskUserQuestion 接受降级（需 Emergency）或手动补跑；headless fail-fast | ❌ |
| `EXT_BLOCKED` | `breaker_reason=safety_limit`（达 max_rounds 未收敛）或 Emergency 超时（`rollback_by_expired=true`） | 1（最高） | 交互模式用户可解除 max_rounds += 3 重跑；headless fail-fast；超时终态须重新启动完整 Phase 4 | ❌ |

### 非状态字段（派生输入）

本身不是状态枚举，但作为 `EXT_*` 判定的派生输入参与计算：
- `external_review_channel_used: T1 | T2 | T3 | none`——实际生效的调用通道
- `degraded_to_t3: bool`——是否从 T1/T2 降级到 T3
- `emergency_accepted: bool`——T3 是否经 Emergency-Mode 合法授权接受
- `rollback_by_expired: bool`——`Emergency-Rollback-By` 时间戳是否已过

同时写入 L1 尾注（非状态字段区）和 L2 yaml 摘要的 `summary.details`。

### 状态判定真值表

**按优先级从高到低执行，命中即返回，下游规则不再评估**：

| 优先级 | 输入组合 | → `ext_review_state` | 说明 |
|-------|---------|----------------------|------|
| 1 | `breaker_reason=safety_limit` | `EXT_BLOCKED` | 熔断终态，Emergency 授权不能绕过 |
| 2 | `rollback_by_expired=true` | `EXT_BLOCKED` | Emergency 超时终态，**同时清除 `INT_PENDING` / `EXT_PENDING`**，Step 1.5 [D2] 识别为硬阻塞 |
| 3 | 证据协议 L1/L2/L3 任缺一或不一致（Phase 4 运行时产出缺失 / Step 1.5 [D2] 续做校验失败） | `EXT_UNRESOLVED` | **必须优先于 `EXT_REVIEWED` 判定**——无可复核证据不得放行 |
| 4 | `--skip-external-review-reason="..."` 登记 | `EXT_PENDING` | 主动跳过，待补跑 |
| 5 | `channel=T3 ∧ emergency_accepted=true` | `EXT_PENDING` | **覆盖** 规则 6/8——Emergency 合法接受 T3 时不看 status/blockers |
| 6 | `channel=T3 ∧ emergency_accepted=false` | `EXT_UNRESOLVED` | T3 默认不放行 |
| 7 | `channel∈{T1,T2} ∧ status=success ∧ blockers=[]`（且规则 3 未命中） | `EXT_REVIEWED` | 外审通过，**唯一**放行分支 |
| 8 | `channel∈{T1,T2} ∧ (status!=success ∨ blockers!=[])` | `EXT_UNRESOLVED` | Phase 4 单轮未通过（已达 max_rounds 由规则 1 捕获） |
| fallback | 以上均不命中（应不可达） | `EXT_UNRESOLVED` | 安全阀，同时产生诊断日志 |

**互斥性保证**：规则按优先级**唯一命中**一条（高优先级短路低优先级），任一输入组合有且仅有一个 `EXT_*` 映射。

**优先级冲突澄清**：
- 规则 5（T3 + Emergency 接受）优先于规则 6/8，覆盖 "T3 默认 UNRESOLVED" 和 "status!=success → UNRESOLVED"
- 规则 1（safety_limit）和规则 2（超时）是硬终态，优先于 Emergency 授权——Emergency 不能绕过熔断或超时
- 规则 3（证据缺失）优先于规则 7（EXT_REVIEWED）——防止"通道 T1/T2 + status=success + blockers=[] + 证据缺失"被误判为 `EXT_REVIEWED`

### 证据三级协议

| 层级 | 存储位置 | 内容 | 权威性 |
|------|---------|------|-------|
| L1 尾注 | Commit 1 message trailer | `External-Review-Verdict: EXT_*` + rounds + health_scores + method | 快速扫描，不含证据 |
| L2 摘要 | `docs/devdocs/audit/<T-XX>-external-review.yaml` | yaml-summary-v1 完整摘要（blockers, findings, rounds, fallback_events, primary_method, effective_method） | 结构化证据，Step 1.5 [D2] 主要消费源 |
| L3 原始 | `docs/devdocs/audit/<T-XX>-external-review-raw/<round-N>.txt` | 每轮 codex 原始 stdout/json 输出 | **原样保留强制要求**：Phase 4 调度器必须在每轮结束时 pass-through 到主编排器可访问的 artifact，不得仅存调度器本地日志 |

### T3 状态迁移链（Emergency-Mode 衔接）

```
T3 触发
  └── 初始状态：EXT_UNRESOLVED
      ├── --headless：直接 fail-fast（不走 Emergency 通道）
      └── 交互模式
          ├── 用户不接受降级 → 保持 EXT_UNRESOLVED（手动补跑 T1/T2 或终止）
          └── 用户经 Emergency-Mode 合法授权接受（满足下方锚定三选一）
              └── 状态覆盖为 EXT_PENDING + 同时标 INT_PENDING + EXT_PENDING（双 pending 挂起）
                  └── 在 Emergency-Rollback-By 时间戳前补跑 T1/T2
                      ├── 补跑成功 → EXT_REVIEWED（清除 pending）
                      ├── 补跑失败 → EXT_BLOCKED
                      └── 超时未补跑 → rollback_by_expired=true → EXT_BLOCKED（规则 2）
```

### Emergency-Mode 授权协议（双 skip 例外通道）

**默认禁令**：`--skip-review-reason` + `--skip-external-review-reason` 同时使用 → ⛔ 非法参数组合。

**例外条件**（全部满足缺一即禁令生效）：

| 条件 | 要求 |
|------|------|
| 触发模式 | **仅交互模式**（`--headless` 禁止自启用） |
| 授权来源锚定（三选一） | (a) **当轮用户 AskUserQuestion 确认**：原始问答 + UTC 时间戳写入 artifact 的 `user_confirmation:` 字段；或 (b) **外部既有工单**：`Emergency-Authorized-By: ticket://<url>`，Step 1.5 [D2] 校验工单创建时间 < 任务 S1 起始时间；或 (c) **签名工件**：detached signature（sigstore/GPG），签名者+时间可离线校验 |
| 证据 artifact | `docs/devdocs/audit/<T-XX>-emergency-auth.md` 必须存在且包含：理由、影响范围、风险评估、补跑计划、上方锚定证据 |
| Commit 尾注 | `Emergency-Mode: true` + `Emergency-Authorized-By` + `Emergency-Anchor-Type` + `Emergency-Rollback-By`（UTC 绝对时间） |
| 状态门禁 | 同时标 `INT_PENDING + EXT_PENDING`，不得进入"已完成可跳过"态 |
| 超时行为 | `rollback_by_expired=true` → 真值表规则 2 转 `EXT_BLOCKED` + 清 pending；Step 1.5 [D2] 硬阻塞 |
| 自写防护 | Phase 4 调度器/编排器**同轮禁止创建或修改** `Emergency-Authorized-By` 来源记录，只能引用既有记录 |
