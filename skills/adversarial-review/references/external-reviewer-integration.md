# 外部审查者集成与降级策略

## 两种使用模式

本文档的三级降级链（codex CLI → codex-mcp → Task 子 Agent）、yaml-summary-v1 契约、熔断/收敛评分协议被以下**两种模式**复用：

1. **Skill multi-turn 模式**（adversarial-review skill 自身）
   - 通过 S1~S6 完整协调流程运行（展示原始发现 → 逐条验证 → AskUserQuestion 接受/驳回循环）
   - 对外部审查输出做二次加工（解析、映射、F-XXX 合成、收敛评分）
   - 适用场景：用户直接调用 `/adversarial-review` 做交互式审查

2. **dev-workflow embedded-headless 模式**（`/ms-dev-workflow` S9 Phase 4）
   - 由 dev-workflow 编排器自带的 Phase 4 调度器复用本文档 **T1/T2 双通道** + 熔断协议
   - **不使用 T3 Task 子 Agent 兜底**——T3 是同进程独立上下文，不满足 dev-workflow "外部独立审查" 承诺；T1/T2 全失败直接 fail-fast
   - **禁用** AskUserQuestion（避免子 Agent 阻塞），自动收敛循环（blocker!=[] 且 round < max_rounds → 自动构建下一轮 brief）
   - 状态名遵循 dev-workflow 的 canonical enum `EXT_REVIEWED / EXT_UNRESOLVED / EXT_BLOCKED`（非本 skill 的 verdict/rounds 结构）
   - 默认 max_rounds=3（dev-workflow 嵌入收紧值），可由 `--external-rounds N` 覆盖到 5
   - 详见 `skills/dev-workflow/references/verification-flow.md` Phase 4 章节

两种模式共享本文档的 T1/T2 调用契约和 yaml-summary-v1 字段语义（skill multi-turn 模式还另外使用 T3 作为兜底），**协调层互不依赖**：embedded-headless 模式不经过 skill S4/S5/S6 流程，直接消费外部审查的底层结果。

## 概述

对抗审查使用外部 LLM 作为独立审查者。三级降级链：codex CLI → codex-mcp → Task 子 Agent。

> **适用范围限定**：以下三级链仅适用于 adversarial-review skill 的 **multi-turn 模式**。`ms-dev-workflow` S9 Phase 4 embedded-headless 模式**只消费 T1/T2 子集，不执行 T3 分支**——T3 Task 子 Agent 是同进程独立上下文，不满足 dev-workflow "外部独立审查" 承诺。本文档"降级探测流程"和"T3"相关段落仅在 skill multi-turn 模式下生效。

> **设计说明**：T1 直接使用 codex CLI（非 companion 脚本），因为 `CLAUDE_PLUGIN_ROOT` 在 skill 上下文中不可用。
> adversarial-review skill 对外部审查输出做二次加工（解析、映射、F-XXX 合成、收敛评分），是 skill 层面的有意架构选择；dev-workflow embedded-headless 模式下则由 Phase 4 调度器自行生成摘要和状态，不经过本 skill 的二次加工层。

---

## 降级探测流程（skill multi-turn 模式专用）

> dev-workflow embedded-headless 模式不走本章 T3 分支，T1/T2 全失败直接 fail-fast。

### 首选通道探测（首次调用时执行）

```
T1 检测 codex CLI（两步验证）→ 成功则 T1 为首选
  ↓ codex 不在 PATH / 未认证 / 冒烟调用失败
T2 尝试 codex-mcp 首次调用 → 成功则 T2 为首选
  ↓ 连接错误 / 工具不存在 / 超时
T3 使用 Task 子 Agent 为首选（无条件可用）
```

### 每轮执行规则

- `primary_method` 只在首次探测时确定
- 每轮优先使用 `primary_method`；当轮失败则临时降级到下一级
- 单轮失败只影响 `effective_method`，下一轮默认仍先尝试 `primary_method`
- 连续 2 轮失败 → 永久降级，更新 `primary_method` 为下一级
- 报告记录 `primary_method`、`effective_method`、`fallback_events`（如有）

---

## T1：codex CLI

### 检测（两步验证）

**Step 1** — 版本检查：

```bash
which codex && codex --version
```

**Step 2** — 冒烟调用（仅首次）：

```bash
echo "Reply with exactly: OK" | codex exec --sandbox read-only --ephemeral -o /tmp/codex-smoke.txt -
```

- 两步都成功 → T1 可用，锁定为 `primary_method`
- 任一步失败（非零退出、panic、无最终消息、超时） → T1 不可用，尝试 T2

> **非交互前提**：所有 `codex exec` 调用使用 `--sandbox read-only`（无危险操作，不触发审批）。
> 如果用户环境配置了交互审批策略，可能需要额外传递 `--full-auto` 或确保 profile 为非交互模式。

### 代码审查（结构化输出）

```bash
SCHEMA_PATH="skills/adversarial-review/references/review-output.schema.json"
codex exec --sandbox read-only \
  --output-schema "$SCHEMA_PATH" \
  --ephemeral \
  -o /tmp/codex-review-output.txt \
  "<adversarial prompt + 用户关注点>"
```

- 使用 `codex exec`（非 `codex review`），因为只有 `exec` 支持 `--output-schema`
- `--output-schema` 指向 `skills/adversarial-review/references/review-output.schema.json`（从仓库根目录起算的完整相对路径），强制结构化 JSON 输出
- ⚠️ 路径依赖工作目录为仓库根。如果 skill 运行环境不同，需先解析为绝对路径
- `-o <tmpfile>` 将最终消息写入文件，避免 stdout banner/日志污染
- `--sandbox read-only` 确保只读；`--ephemeral` 不持久化会话
- codex 在 repo sandbox 内运行，可自行执行 `git diff` 读取变更
- 输出文件内容为结构化 JSON：`{ verdict, summary, findings: [...], next_steps }`

### Adversarial Prompt 模板

按审查对象类型拆分两版，共享 adversarial 指示。

**workspace diff 版**（默认，用于 `git diff` 审查）：

```
Adversarial software review. Break confidence in the uncommitted changes, don't validate them.
Run `git diff` and `git diff --staged` to collect the changes, then review them.

<共通 adversarial 指示>

User focus: <用户关注点>
```

**explicit file/content 版**（用于 `--code <file>` 场景）：

```
Adversarial software review. Break confidence in the provided code, don't validate it.
Review the file(s) specified below directly; do not run git diff.

<共通 adversarial 指示>

Files to review: <文件路径>
User focus: <用户关注点>
```

**共通 adversarial 指示**：

```
Operating stance: Default to skepticism. Assume the change can fail in subtle,
high-cost, or user-visible ways until the evidence says otherwise.

Attack surface priorities:
- auth, permissions, tenant isolation
- data loss, corruption, irreversible state changes
- rollback safety, retries, partial failure, idempotency gaps
- race conditions, ordering, stale state, re-entrancy
- empty-state, null, timeout, degraded dependency behavior
- version skew, schema drift, migration hazards
- observability gaps

Report only material findings. Every finding must include affected file,
line range, confidence score (0-1), and concrete recommendation.
Use needs-attention if any material risk found; approve only if no substantive finding.
```

### 方案/设计/文档审查（stdin 输入）

```bash
# 方式 1：here-doc（推荐，避免 shell 展开）
cat <<'EOF' | codex exec --sandbox read-only --ephemeral -o /tmp/codex-review-output.txt -
<S2 审查 brief 内容>
EOF

```

- 长 brief 通过 **stdin** 传入（`-` 表示从 stdin 读取 prompt），避免 shell quoting 和长度限制
- ⚠️ 使用 `cat <<'EOF'`（单引号 EOF 禁止 shell 展开），不要用 `echo "..."` 双引号包裹长文本
- 短 brief（< 500 字符且不含特殊字符）可直接作为 argv 参数
- brief 中已要求 F-XXX/P1-P3 格式输出
- 无 `--output-schema` 约束，输出为自由文本

### 输出解析

**代码审查**（有 schema 约束 + `-o` 文件输出）：

1. 读取 `-o` 指定的 tmpfile（纯最终消息，无 banner/日志）
2. `JSON.parse` 取 `{ verdict, summary, findings, next_steps }` 顶层字段
3. 映射 severity → P1/P2/P3，分配 F-XXX ID

**严重程度映射**：

| codex severity | 技能 severity |
|---------------|--------------|
| critical      | P1           |
| high          | P1           |
| medium        | P2           |
| low           | P3           |

**F-XXX ID 合成**：按 `findings` 数组顺序分配 F-001、F-002…
字段映射：title→description, body→details, file:line_start-line_end→location, recommendation→suggestion

**方案/文档审查**（无 schema）：与 T3 相同的文本解析路径。

**容错策略**：

- 代码审查 JSON 解析失败 → 将 `-o` 文件内容作为原始文本，走文本解析路径
- 文本解析失败 → 将整段原始文本包装为单条 F-001（P2）展示，交由 S5 人工验证
- stderr 噪音处理：仅取 `-o` 文件或 stdout，忽略 stderr（可能含 telemetry/progress 信息）

### 审查循环（rework）

- 代码审查：直接重新运行 `codex exec --output-schema <schema-path> ...`（codex 在 sandbox 内重新读取最新 diff）
- 方案/文档审查：重新运行 `codex exec`，通过 stdin 传入修复后内容 + 上轮上下文

---

## T2：codex-mcp

### 工具选择

| 审查类型 | 使用工具 | 说明 |
|----------|---------|------|
| 代码审查（**未提交**改动） | `mcp__codex-mcp__review-code` | 传入 prompt（审查 brief）+ `uncommitted: true` |
| 代码审查（**已提交**改动） | `mcp__codex-mcp__review-code` | 传入 prompt（审查 brief）+ **显式 diff 内容或 commit 范围**，⛔ 不得传 `uncommitted: true` |
| 方案 / 设计 / 文档审查 | `mcp__codex-mcp__delegate-task` | 传入 goal（审查 brief）+ mode: "plan" |

> **为什么区分两行**：`uncommitted: true` 在改动已落盘时会得到**空 diff**——审查照常返回"无问题"，但它什么都没看到。本 skill 独立调用时默认审工作区（未提交），故用第一行；`ms-dev-workflow` S9 Phase 4 的 **drain 侧**（Commit 1 已落盘后集中补审）必须用第二行。判定见 [verification-flow.md § diff 源](../../dev-workflow/references/verification-flow.md)。

### allowedPaths 问题

`delegate-task` 的 `allowedPaths` 为必填且不能为空，即使 `mode: "plan"` 也是如此。
**解决方案**：传 `allowedPaths: ["."]` + `mode: "plan"`。`allowedPaths` 仅为满足工具参数约束的最小路径范围，只读保证由 `mode: "plan"` 和调用方工作流提供。

### 工作流程

```
1. 发起审查
   ├── 代码 → review-code（传入 diff + 审查 brief）
   └── 方案/文档 → delegate-task（传入审查 brief + mode: "plan" + allowedPaths: ["."]）

2. 等待完成
   └── check-task 轮询，直到状态为 completed / failed

3. 获取结果 → 返回 S4 展示

4. （如需补充信息）
   └── reply-task 提供额外上下文

5. （审查循环中，需要重新审查）
   └── rework-task 传入修复后的新版本 + 上一轮审查上下文

6. （审查通过，达成共识）
   └── accept-task 关闭任务

7. （调用失败，非降级场景）
   └── retry-task（最多重试 2 次）
```

### 审查 Brief 构建要点

传给 codex-mcp 的审查请求应包含：
- 变更的**原因**（WHY）——不只是 diff，还要说明为什么做这些修改
- 完整的**审查对象**——diff 或文件内容
- 明确的**审查维度**——正确性、完整性、可行性、风险
- **输出格式要求**——结构化发现列表（id/severity/description/location/suggestion）

---

## T3：Task 子 Agent

### 触发条件

T1 和 T2 均失败时使用。

### 子 Agent 审查员 Prompt

通过 Task 工具启动子 Agent 时，使用以下 prompt 模板：

```
你是一位独立的对抗性代码/方案审查员。你的职责是从独立视角审查提供的内容，找出真正的问题。

## 审查维度

1. **正确性**：逻辑是否成立？实现是否符合意图？
2. **完整性**：是否有遗漏的场景、边界条件或错误处理？
3. **可行性**：方案/实现是否可行？有无技术障碍？
4. **风险**：有哪些潜在风险、副作用或安全隐患？

## 审查对象

<插入审查 brief>

## 输出要求

对每条发现，严格按以下格式输出：

- **id**：F-001, F-002...（顺序编号）
- **severity**：P1（阻塞正确性）/ P2（应修复）/ P3（建议改进）
- **description**：问题的具体描述
- **location**：具体位置（文件:行号，或文档中的段落引用）
- **suggestion**：修复建议

如果没有发现问题，明确说明"未发现问题"并简要说明审查覆盖范围。

## 注意事项

- 聚焦真正的问题，避免吹毛求疵
- P1 仅用于阻塞正确性的问题，不要滥用
- 每条发现必须有具体的位置引用，不接受泛泛而谈
```

### 工具映射表

| codex-mcp 工具 | Task 子 Agent 等价操作 |
|---------------|---------------------|
| `delegate-task` / `review-code` | 启动新 Task，传入审查员 prompt + 审查 brief |
| `check-task` | Task 工具同步返回，无需轮询 |
| `reply-task` | 启动新 Task，包含原始审查 + 补充信息 |
| `rework-task` | 启动新 Task，包含修复后内容 + 上一轮审查上下文 |
| `accept-task` | 无需操作，直接继续 |
| `retry-task` | 重新启动 Task（同样的 prompt） |
