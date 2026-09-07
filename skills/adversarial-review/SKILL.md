---
name: adversarial-review
description: >
  用户要求对计划、设计或代码进行外部独立审查、对抗审查或 second opinion 时使用。
  内部自检用 ms-verify；代码规范检查用 code-quality。
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - Task
  - mcp__codex-mcp__delegate-task
  - mcp__codex-mcp__check-task
  - mcp__codex-mcp__review-code
  - mcp__codex-mcp__reply-task
  - mcp__codex-mcp__rework-task
  - mcp__codex-mcp__accept-task
  - mcp__codex-mcp__retry-task
metadata:
  patterns: [reviewer, convergence-breaker]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 对抗性审查（Adversarial Review）

调用外部 LLM 对当前工作进行独立审查，然后逐条验证审查结论的真实性，通过审查循环达成共识。

## 角色

- **身份**：对抗审查协调员——你不是审查者本身，而是协调外部审查者与当前工作之间的对话
- **关注**：确保每条审查发现都经过严格验证，真问题得到修复方案，误报被有理有据地驳回
- **回避**：不做橡皮图章式的全盘接受，也不做防御性的全盘否认
- **判断倾向**：对外部审查结论保持审慎怀疑——既尊重外部视角的独立性，也坚持用证据验证每条发现

## 语言

接受中英文输入，统一中文输出。

## 运行模式

```
/adversarial-review                    # 默认：审查工作区全部修改（staged + unstaged）
/adversarial-review --plan <file>      # 审查方案/设计文档
/adversarial-review --code <file>      # 审查指定代码文件
/adversarial-review --content <file>   # 审查任意文件内容
```

审查对象可以是：工作区 diff（默认）、指定文件、方案文本、或当前对话中的方案描述。

## 核心工作流

```
S1 上下文收集 → S2 构建审查 brief → S3 外部审查调度
    → S4 展示审查结论 → S5 逐条验证（含跨轮追踪 + 快照生成）
        → S6 用户确认
            ├── 接受建议 → 输出修复方案 → 重新提交审查（→ S3）
            ├── 全部驳回 → 生成最终报告 → 结束
            ├── ⚠️ 预警（R2: score 未下降；R3+: score 未下降 或 new_issues > 0）→ 展示趋势，不阻塞
            ├── 🔴 收敛熔断（R3+ score 未下降）→ 复盘 → 用户决策
            └── ⛔ 安全上限（默认 5 轮）→ 强制熔断 → 用户可解除继续
```

---

### S1 上下文收集

**目标**：搞清楚审查什么、为什么会有这些修改。

**审查对象确定**（按优先级）：
1. **默认**：无参数时，运行 `git diff` + `git diff --staged` 收集工作区全部修改
2. **参数覆盖**：`--plan`/`--code`/`--content` 指定具体文件
3. **对话上下文**：如果用户刚在对话中讨论了一个方案并说"审查一下"，将对话中的方案作为审查对象
4. **兜底**：工作区无变更且无参数 → 用 AskUserQuestion 询问用户

**必须收集的上下文**：
- 变更的内容（diff / 文件 / 方案文本）
- 变更的原因（WHY）——为什么会产生这些修改？解决什么问题？
- 审查类型——是方案评审、代码审查、还是文档内容审查？
- （可选）用户特别关注的风险领域

收集方式：优先从 git log、PR 描述、对话历史中推断变更原因。推断不出时用 AskUserQuestion 询问。

### S2 构建审查 Brief

将收集到的上下文打包为结构化的审查请求：

```markdown
## 审查请求

**审查类型**：方案评审 / 代码审查 / 文档审查
**变更原因**：<为什么有这些修改>
**审查对象**：
<变更内容：diff / 文件内容 / 方案文本>

**审查维度**：
1. 正确性：逻辑是否成立？实现是否正确？
2. 完整性：是否有遗漏的场景或边界条件？
3. 可行性：方案/实现是否可行？有无技术障碍？
4. 风险：有哪些潜在风险或副作用？

**输出要求**：
对每条发现，提供：
- id：F-001, F-002...
- severity：P1（阻塞）/ P2（应修复）/ P3（建议，可选）。⛔ 只报影响**正确性或已声明需求**的缺口，不凑数——门槛见 [references/finding-verification-rubric.md](references/finding-verification-rubric.md) § 发现门槛
- description：问题描述
- location：具体位置（文件:行号 或 文档段落）
- suggestion：修复建议
```

### S3 外部审查调度

调用外部 LLM 执行审查。详见 [`references/external-reviewer-integration.md`](references/external-reviewer-integration.md)。

**四级降级链**（首次探测确定首选通道，每轮允许临时降级）：

**T1 codex CLI**（优先）：
1. 两步检测：`which codex` + 冒烟调用（**必须含一次真实工具调用**，见集成文档）
2. 代码审查 → `codex exec --sandbox read-only --output-schema <schema> -o <tmpfile> "<adversarial prompt>"`（结构化 JSON 输出）
3. 方案/设计/文档审查 → stdin 输入长 brief（here-doc 或临时文件，见集成文档）
4. 代码审查：读取 tmpfile，解析 JSON，映射 severity，合成 F-XXX ID；方案审查：文本解析
5. **JSON 校验优先级（⛔ 不可颠倒）**：结构化调用**只有完整通过 schema 校验才算审查结果**。
   - JSON 完整且通过校验 → 正常消费
   - JSON **不完整 / 缺 `verdict`** → 判 **截断**（见 § 截断不是审查结果），⛔ **不得回落成文本解析或 F-001**
   - JSON 完整但**格式异常**（非截断，如字段类型错） → 才降级为文本解析；文本也不可解析 → 包装为单条 F-001 展示
   > 原实现是「JSON 失败 → 文本 → F-001」一条路，会把截断产物洗成一条普通 finding，**本节最重要的安全门就此失效**。

**T1b codex CLI · 备用计费后端**（额度耗尽时的首选补救，**优先于 T2/T3**）：同一 CLI、同一模型档次，只换计费后端（`CODEX_HOME=<备用home> codex exec ...`）→ **质量不降级**，这是它排在 T2 前的唯一理由。探测、选取与已知坑见 [external-reviewer-integration.md § T1b](references/external-reviewer-integration.md)。

**T2 codex-mcp**（次选）：
1. 代码审查 → `mcp__codex-mcp__review-code`（传 prompt + uncommitted: true）
2. 方案/设计/文档审查 → `mcp__codex-mcp__delegate-task`（传 goal + `mode: "plan"` + `allowedPaths: ["."]`）
3. 轮询 → `mcp__codex-mcp__check-task` 直到完成

**T3 Task 子 Agent**（兜底）：
- 触发条件：T1 / T1b / T2 均失败
- 子 Agent 使用独立审查员角色 prompt（见 [`references/external-reviewer-integration.md`](references/external-reviewer-integration.md)）
- ⚠️ **必须标注检出率折损**：T3 与被审对象同模型、同盲区。降到 T3 时结论里标明「本轮降级审查」，⛔ 不得让「审过了」掩盖「审得更浅了」

### 失败分类（⛔ 不得一律按"失败"降级）

六类失败走不同路由，**完整判据表见 [external-reviewer-integration.md § 失败分类](references/external-reviewer-integration.md)**。两条必须记住的：

- **额度 / 限流耗尽** → **T1b**。⛔ **不降 T2**——T2 与 T1 共用同一订阅，必然同样失败，白跑一轮
- **工具协议不兼容**（`incompatible payload`）→ 该后端标不可用并**跳过**，⛔ 不重试（实测重连 5 次全败）

### ⛔ 截断不是审查结果

额度可能在审查**进行中**耗尽——审查者已读完全部输入、正要输出结论时被切断。产物有分析、有文件引用、有行号，**唯独没有裁决**。

判据：**代码审查**（结构化）JSON 缺 `verdict` 或不完整 —— `verdict` 已是 schema 必填项，缺失即截断；**方案/文档审查**（文本）输出不以约定尾标记 `=== END OF REVIEW ===` 结束（brief 中强制要求）。

⛔ **不得把截断输出当发现列表消费**，不得据此判 PASS、不得写入 `findings`。标 `truncated: true`。

**截断只证明「完整性未被证明」，⛔ 不证明「发生了额度耗尽」**——缺尾标记也可能是模型漏输出。所以：

| 同时出现额度信号（`usage limit` 等） | 处置 |
|---|---|
| 有 | 按额度类走 T1b |
| **无** | 原通道**重跑一次**；再次缺失 → 判**输出契约失败**，可换通道或报告用户，⛔ **不得伪装成额度类** |

⛔ **不得把「无额度信号的二次缺标记」路由成额度类**——那只是模型漏输标记，却会触发切后端、T1b 不可用时直接停下等用户，属无谓停摆。误判方向仍安全：多跑一轮，⛔ 不产生假 PASS。尾标记须 `rstrip()` 后比对最后一行，⛔ 不得用字节级 `endswith`（输出通常带末尾换行，会把正常完成判成截断）。完整判据表见 [external-reviewer-integration.md](references/external-reviewer-integration.md)。

> **为什么单列这条**：其余失败都表现为「没有结果」，一眼可辨。**截断表现为「有结果但没结论」**，最容易被当成「审查通过、没发现问题」。

### 额度耗尽的默认行为：报告并停下

T1 额度耗尽且 T1b 不可用时，⛔ **不自动降级到 T3，不自行决定"就这样吧"**。必须报三项由用户决定：**已耗尽的通道** / **重置时间**（原文照抄，如 `try again at 7:48 PM`）/ 可选项（等待 · 降 T3 附折损说明 · 换后端）。

理由：降 T3 是**真实的检出率损失**，不应静默发生。

**降级规则**：
- 首选通道（`primary_method`）在首次探测时确定，每轮优先使用
- 单轮失败只是临时降级，下一轮仍先尝试首选通道
- 连续 2 轮失败 → 永久降级，更新 `primary_method`
- ⛔ **额度类失败例外，不计入「连续 2 轮」计数**：额度是时间窗口问题而非通道问题。一次限流若触发永久降级，会把后续全部审查钉死在更弱的通道上

### S4 展示审查结论

> **⛔ 禁止继续：必须先原样展示外部审查者的完整发现列表，不做任何修改、过滤或重排**
> 恢复方式：如果跳过了此步骤，回到 S4 重新展示原始结论

展示格式：

```
## 外部审查结论（原始）

审查方式：codex CLI / codex-mcp / 独立子 Agent
发现数量：X 条

---

> 以下为外部审查者的原始输出，未经修改。

<完整的审查结论>
```

这一步的意义：让用户和当前 Agent 都先完整看到外部视角，避免选择性呈现。

### S5 逐条验证

对每条审查发现进行独立验证。详见 [`references/finding-verification-rubric.md`](references/finding-verification-rubric.md)。

**跨轮问题关联**（第 2 轮起执行）：

在逐条验证之前，先建立本轮 finding 与上轮的关联：

1. **显式继承**：如果本轮 finding 对应上轮同位置、同类问题，继承原 ID（如上轮 F-001 本轮仍为 F-001）
2. **语义兜底**：对未显式继承的 finding，Agent 做语义匹配——如果本质是同一问题，标注 `recurring_from: <原ID>`
3. **新问题标识**：无法关联到任何上轮 finding 的，标注 `origin: new`

每条 finding 的最终标注：`recurring`（跨轮复现，无论来自 ID 继承还是语义匹配，均以 `recurring_from` 记原 ID）/ `new`（本轮新增）。

对每条发现：

1. **事实核查**：读取相关代码/文档，确认审查者描述的事实是否属实
2. **上下文检查**：审查者是否缺少关键上下文导致误判？
3. **判定**：
   - ✅ **确认**（真实问题）→ 分析成因（怎么产生的？）+ 提出修复方案（怎么解决？）
   - ❌ **驳回**（误报）→ 提供具体反驳证据（为什么不是问题？）
   - ⚠️ **部分正确** → 说明哪部分成立、哪部分不适用
4. **标注严重程度**：P1 / P2 / P3

**关键原则**：
- 驳回不能只说"不同意"，必须引用具体代码/文档作为反驳证据
- 确认必须同时给出成因分析和修复方案
- 如果验证过程中发现审查者没提到的新问题，也记录下来（标注为"自查发现"）

**轮次快照生成**：

S5 验证完成后，生成本轮结构化快照并追加到 `round_history`：

```yaml
round: N
health_score: <加权计算，见"审查循环与熔断"节>
confirmed: X
rejected: X
partial: X
new_issues: X          # origin: new 的 finding 数
recurring: X           # 跨轮复现的 finding 数
by_severity:
  P1: X
  P2: X
  P3: X
```

### S6 用户确认

展示验证后的发现列表，向用户确认：

```
## 验证结果摘要

| 指标 | 数量 |
|------|------|
| ✅ 确认（真实问题） | X |
| ❌ 驳回（误报） | X |
| ⚠️ 部分正确 | X |
| P1 | X |
| P2 | X |

### 需要确认的修复方案

1. **F-001**（P1）：<问题> → 建议修复：<方案>
2. **F-003**（P2）：<问题> → 建议修复：<方案>
...
```

### 趋势预警（第 2 轮起展示）

如果 `round_history` 中本轮 health_score >= 上轮：

```
⚠️ 预警：本轮健康分未下降（{上轮分} → {本轮分}）
  - 新增问题：{new_issues} 条
  - 复现问题：{recurring} 条
  - 如果下一轮仍未收敛，将触发熔断复盘
```

如果本轮 health_score 下降但 new_issues > 0（第 3 轮及以后）：

```
ℹ️ 注意：健康分下降（{上轮分} → {本轮分}），但仍有 {new_issues} 条新增问题
```

预警不阻塞流程，用户仍可选择继续。

用 AskUserQuestion 询问用户：
- **接受修复方案**：输出修复建议详情（skill 不直接修改文件），然后重新收集变更、提交审查（→ S3，新一轮）
- **部分接受**：选择性确认，其余驳回
- **全部驳回**：记录驳回理由，生成最终报告，结束
- **结束审查**：不再继续循环，生成最终报告

---

## 审查循环与熔断

### 加权健康分

每轮的健康分综合衡量问题的数量、严重程度和来源：

```
health_score = Σ(finding_score)
finding_score = base_score(severity, verdict) × origin_multiplier
verdict ∈ {confirmed, partial}    # rejected 不计分
```

单条 finding 的 base_score：

| 严重程度 | 基础分（confirmed） | 基础分（partial） |
|---------|---------------------|-------------------|
| P1      | 8                   | 4                 |
| P2      | 3                   | 1.5               |
| P3      | 1                   | 0.5               |

来源乘数（与基础分相乘）：

| 来源 | 乘数 | 理由 |
|------|------|------|
| recurring（跨轮复现） | ×1.5 | 问题跨轮未解决 |
| new（新增） | ×2 | 修复引入新问题是严重信号 |
| 其他 | ×1 | 首轮发现或已有问题 |

示例：1 个 recurring P1 + 1 个 new P2 = 8×1.5 + 3×2 = 18

### 收敛检测

> ⛔ **手动直敲 `codex exec` 做多轮审查，同样计轮次、同样适用本节熔断。** 本节熔断只在走本 skill 时自动生效——本仓实证：一次改造手动跑了 **7 轮**，熔断一次都没触发（机制在，从旁边过去了），其中 4 轮打的是与用户原始诉求无关的既存问题，最终全量缩回。
>
> 故从第 2 轮起须自记 `round_history`（轮次 / 发现数 / 是否出现新形状问题），命中任一熔断条件即停下复盘，⛔ 不得因「这次是手动跑的」豁免。**手动模式专属判据**：连续 2 轮发现的问题形状都与前几轮不同 → 扫描判据一直在追上一轮的发现，覆盖面不收敛 → 🔴 熔断，回头问方向是否错了（见 [constraints.md](../_shared/constraints.md) `confirm/scope-inflation`）。

收敛判定基于 `round_history` 中 health_score 的趋势：

**第 2 轮结束**：
- score 下降 → 收敛中，继续
- score 持平或上升 → ⚠️ 预警（S6 展示，不阻塞）

**第 3 轮及以后**：
- score 下降且 new_issues == 0 → 收敛中，继续
- score 下降但 new_issues > 0 → ⚠️ 预警（问题在变化而非收敛）
- score 持平或上升（`score[n] >= score[n-1]`）→ 🔴 触发熔断

**安全上限**（默认 5 轮）：
- 无论趋势如何 → ⛔ 强制熔断
- 用户可在熔断决策时选择解除：将 `max_rounds` 提升为 `current_round + 3`，给予 3 轮新空间，并在报告中记录新上限值

### 熔断复盘

> **⛔ 禁止继续：收敛检测或安全上限触发时必须执行熔断复盘，不得跳过**
> 恢复方式：用户在复盘后选择继续/接受/回退/升级

触发时执行以下 4 步：

**1. 趋势数据展示**

```
## 审查趋势

| 轮次 | 健康分 | 确认 | 新增 | 复现 | P1 | P2 | 趋势 |
|------|--------|------|------|------|----|----|------|
| R1   | 22     | 4    | -    | -    | 2  | 2  | —    |
| R2   | 18     | 3    | 1    | 2    | 1  | 2  | ⬇️   |
| R3   | 20     | 2    | 2    | 1    | 1  | 3  | ⬆️   |

熔断原因：<convergence — score 未下降 / safety_limit — 达到 N 轮上限>
```

**2. 根因分析**（基于 round_history 和各轮验证记录判断）

- new_issues 占比高 → "修复引入新问题"
- recurring 占比高 → "修复不到位 / 审查标准模糊"
- 问题位置频繁变化 → "根本性设计分歧"
- 同一 finding 反复驳回又确认 → "上下文差异"

可同时存在多个根因。

**3. 改动合理性评估**

```
## 改动合理性评估

**评估结论**：合理 / 部分合理 / 不合理

**论据**：
- 合理：<哪些改动确实解决了真实问题，引用 finding ID>
- 不合理：<哪些改动引入了更多问题或偏离了原始目标，引用证据>

**建议**：
- 如果不合理 → 建议回退到第 N 轮状态，附反驳理由
- 如果部分合理 → 建议保留 <X>，回退 <Y>
```

**4. 用户决策**

用 AskUserQuestion 让用户选择：
- **继续审查**：解除安全上限（如适用，将 max_rounds 提升为 current_round + 3），带上根因分析的补充上下文进入下一轮
- **接受当前状态**：生成最终报告，记录遗留项
- **回退到指定轮次**：如果评估认为某轮之后的改动不合理，建议回退
- **升级处理**：建议人工介入或重新设计方案

---

## 约束

### 上下文约束
- [ ] 必须先理解变更原因（WHY），再开始审查
- [ ] 审查对象必须明确（diff / 文件路径 / 方案文本）

### 审查调度约束
- [ ] 首选探测按 **T1→T2→T3**；⛔ **T1b 不参与首选探测**（它只是 T1 的另一个计费出口，由「额度耗尽」这一类失败在运行期触发）
- [ ] 首选通道探测仅做一次（首次调用时）；记录 primary_method 和 review_method
- [ ] **冒烟调用必须含一次真实工具调用**（纯问答通过不算可用——实测存在"纯问答通、工具调用全败"的后端）
- [ ] T1 代码审查使用 `--output-schema` 获取结构化 JSON；JSON 解析失败时降级为文本解析
- [ ] **失败必须先分类再决定路由**（见 § 失败分类）；⛔ 额度类不得降 T2（共用订阅）
- [ ] **⛔ 有输出但无裁决 = 截断，不得当审查结果消费**；标 `truncated: true`
- [ ] 额度耗尽且 T1b 不可用 → **报告并停下等用户决定**，⛔ 不自动降 T3
- [ ] 降到 T3 时结论必须标注检出率折损
- [ ] 连续 2 轮 primary_method 失败时永久降级；**额度类失败不计入该计数**

### 结论展示约束
- [ ] ⛔ 必须先原样展示外部审查结论，再进行验证分析

### 验证约束
- [ ] 每条发现必须独立验证，引用具体代码/文档作为证据
- [ ] 驳回必须提供具体反驳（不可仅说"不同意"）
- [ ] 确认必须说明成因和修复方案

### 循环约束
- [ ] 用户确认修复方案后才输出修复建议
- [ ] 每轮（含第 1 轮）必须生成轮次快照并追加到 round_history
- [ ] 第 2 轮起基于快照做趋势判断；score 未下降时必须在 S6 展示 ⚠️ 预警
- [ ] ⛔ 第 3 轮起 score 未下降时必须触发熔断复盘
- [ ] ⛔ 安全上限（默认 5 轮）触发时必须强制熔断，用户可在决策时解除
- [ ] 熔断复盘必须包含趋势数据、根因分析和改动合理性评估

### 只读约束
- [ ] 不修改任何被审查文件——只生成报告和修复建议

---

## 审查报告

审查结束时（用户选择结束或熔断后接受），按 `templates/review-report.md` 模板生成最终报告。

报告输出位置：展示在对话中。如果用户需要保存，告知用户文件路径建议。

---

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 系统设计审查 | `/ms-system-design` | 设计完成后调用对抗审查验证方案可行性 |
| 开发后代码审查 | `/ms-dev-workflow` | 开发完成后调用进行独立代码审查 |
| dev-workflow 内嵌契约复用 | `/ms-dev-workflow` S9 Phase 4 | **底层 [`references/external-reviewer-integration.md`](references/external-reviewer-integration.md) 契约被 dev-workflow 编排器以 `embedded-headless` 模式复用**（仅调用 T1/T2 双通道 + 熔断协议；**不使用 T3 Task 子 Agent 兜底**——T3 是同进程独立上下文，不满足 dev-workflow "外部独立审查" 承诺；不走本 skill 的 multi-turn S4/S5/S6 协调流程，避免子 Agent 中 AskUserQuestion 阻塞）。两种模式并存：本 skill 仍可被用户独立调用做交互式审查 |
| 功能评审 | `/ms-feature` | 功能迭代中对设计方案进行外部挑战 |
| 验证互补 | `/ms-verify` | ms-verify 检查对齐，adversarial-review 挑战正确性 |
| 质量标准参考 | `/code-quality` | 代码审查时参考 MTE 原则 |
| 经验沉淀 | `/ms-compound` | 反复出现的审查发现沉淀为模式 |

---

## 子 Agent 摘要格式（yaml-summary-v1）

```yaml
skill: adversarial-review
status: success | failed | partial | interrupted
summary:
  headline: "审查完成，2 条 P1 确认，1 条误报驳回"
  details:
    review_target: "工作区 diff / 文件路径 / 方案描述"
    review_type: "代码审查 / 方案评审 / 文档审查"
    review_method: codex-cli | codex-cli-alt | codex-mcp | task-subagent  # 最后一轮实际生效的通道
    primary_method: codex-cli | codex-mcp | task-subagent  # 首次探测锁定；⛔ 不含 codex-cli-alt（T1b 不参与首选探测）
    fallback_events: []          # 降级事件列表，如 ["R2: codex-cli→codex-cli-alt (quota)"]
    truncated: false             # ⛔ true = 本轮有输出但无裁决，findings 不可信
    quota_exhausted: false       # 本轮是否遇到额度/限流耗尽
    reset_hint: null             # 额度重置时间（原文照抄，如 "7:48 PM"）；无则 null
    degraded_detection: false    # true = 实际走了 T3，检出率低于外部审查
    rounds: 1
    health_scores: [22]          # 各轮健康分
    breaker_reason: null         # convergence | safety_limit | null
    total_findings: 5
    confirmed: 3
    rejected: 1
    partial: 1
    p1_count: 2
    p2_count: 1
    p3_count: 0
blockers:
  - "P1: <发现描述>"
output_files: []
new_ids: {}
next_recommended:
  skill: <根据上下文>
  args: ""
```
