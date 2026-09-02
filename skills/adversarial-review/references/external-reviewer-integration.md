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
   - 详见 `skills/ms-dev-workflow/references/verification-flow.md` Phase 4 章节

两种模式共享本文档的 T1/T2 调用契约和 yaml-summary-v1 字段语义（skill multi-turn 模式还另外使用 T3 作为兜底），**协调层互不依赖**：embedded-headless 模式不经过 skill S4/S5/S6 流程，直接消费外部审查的底层结果。

## 概述

对抗审查使用外部 LLM 作为独立审查者。三级降级链：codex CLI → codex-mcp → Task 子 Agent。

> **适用范围限定**：以下三级链仅适用于 adversarial-review skill 的 **multi-turn 模式**。`ms-dev-workflow` S9 Phase 4 embedded-headless 模式**只消费 T1/T2 子集，不执行 T3 分支**——T3 Task 子 Agent 是同进程独立上下文，不满足 dev-workflow "外部独立审查" 承诺。本文档"降级探测流程"和"T3"相关段落仅在 skill multi-turn 模式下生效。

> **设计说明**：T1 直接使用 codex CLI（非 companion 脚本），因为 `CLAUDE_PLUGIN_ROOT` 在 skill 上下文中不可用。
> adversarial-review skill 对外部审查输出做二次加工（解析、映射、F-XXX 合成、收敛评分），是 skill 层面的有意架构选择；dev-workflow embedded-headless 模式下则由 Phase 4 调度器自行生成摘要和状态，不经过本 skill 的二次加工层。

---

## 降级探测流程（skill multi-turn 模式专用）

> dev-workflow embedded-headless 模式不走本章 T3 分支，T1/T2 全失败直接 fail-fast。
>
> ⚠️ **T1b 目前也不属于 embedded-headless 的共享契约**——本次只修 skill multi-turn 模式。
> dev-workflow 侧要获得同样的额度韧性需单独接入（消费方尚未接），⛔ 不要假设它已生效。

### 首选通道探测（首次调用时执行）

```
T1 检测 codex CLI（两步验证，含真实工具调用）→ 成功则 T1 为首选
  ↓ codex 不在 PATH / 未认证 / 冒烟调用失败
T2 尝试 codex-mcp 首次调用 → 成功则 T2 为首选
  ↓ 连接错误 / 工具不存在 / 超时
T3 使用 Task 子 Agent 为首选（无条件可用）
```

> **T1b 不参与首选探测。** 它只在运行期被「额度/限流耗尽」这一类失败触发（见 SKILL.md § 失败分类），
> 因为它与 T1 是同一通道的不同计费后端，正常情况下没有理由用它。

### 每轮执行规则

- `primary_method` 只在首次探测时确定
- 每轮优先使用 `primary_method`；当轮失败则临时降级到下一级
- 单轮失败只影响本轮实际通道（`review_method`），下一轮默认仍先尝试 `primary_method`
- 连续 2 轮失败 → 永久降级，更新 `primary_method` 为下一级
- 报告记录 `primary_method`、`review_method`、`fallback_events`（如有）

---

## T1：codex CLI

### 检测（两步验证）

**Step 1** — 版本检查：

```bash
which codex && codex --version
```

**Step 2** — 冒烟调用（仅首次）：**必须含一次真实工具调用**。

```bash
SENTINEL="codex-smoke-$$"
SMOKE=$(mktemp); OUT=$(mktemp)
echo "$SENTINEL" > "$SMOKE"

codex exec --sandbox read-only --ephemeral --skip-git-repo-check \
  -o "$OUT" "读取文件 $SMOKE 并原样输出其内容，不要解释。"
RC=$?                                    # ⛔ 必须单独保存 codex 自己的退出码

if [ "$RC" -eq 0 ] && [ -s "$OUT" ] && grep -q "$SENTINEL" "$OUT"; then
  SMOKE_OK=1                             # 三条同时成立才算通过
else
  SMOKE_OK=0
fi
rm -f "$SMOKE" "$OUT"
```

**三条判据必须同时成立**：`codex` 退出码为 0 **且** 最终消息文件非空 **且** 内容含哨兵。

- 三条全真 → T1 可用，锁定为 `primary_method`
- 任一条不成立（非零退出、panic、无最终消息、超时、输出不含哨兵） → T1 不可用，尝试 T2

> ⛔ **不得写成 `codex exec ... | grep -q <哨兵>`。** 管道的退出码是 **`grep` 的**，
> codex 自身的非零退出会被完全吞掉——本地实证：`sh -c 'exit 7' | grep -q ""` 整体返回 1，
> 上游的 7 消失。且 `grep -q` 命中即关闭管道，可能给上游送 SIGPIPE。
> **这正是本次改动一度重犯的错误**：初版冒烟就是这个管道写法，而它要防的恰是同一类
> 「靠单一信号反推成功」的误判（见 [笔记 § 两处推断错误](../../../docs/audits/2026-09-01-adversarial-review-quota-resilience-notes.md)）。

> ⛔ **不得用纯问答做冒烟测试**（原实现是 `echo "Reply with exactly: OK" | codex exec`）。
> **实测存在「纯问答通、工具调用全败」的后端**：OpenRouter 后端在错误的模型 id 下纯问答正常返回，
> 工具调用则 100% 报 `tool exec invoked with incompatible payload`（见 § T1b 已知坑）。
> 审查必须读文件与 diff——**纯问答通过不能证明这个通道能做审查**。

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

#### ⛔ brief 末尾必须强制尾标记（截断检测的唯一判据）

文本审查没有 schema 可校验，**尾标记是判断「输出完整」的唯一机械手段**。brief 结尾必须包含：

```text
## 输出收尾（强制）

⛔ 无论结论如何，你的输出**必须**以下面这一行结束，前后不加任何字符：

=== END OF REVIEW ===

如果你因任何原因无法完成审查，也必须先说明原因再输出该行。
```

消费侧判定：

| 输出状态 | 判定 |
|---|---|
| **`rstrip()` 后最后一行等于** `=== END OF REVIEW ===` | 完整，正常解析 |
| 有内容但**无该标记** | **截断** → 标 `truncated: true`，⛔ 不得解析为 findings、⛔ 不得判 PASS |
| 有标记，但标记**之后**还有非空内容 | 同样判异常（标记必须在末尾） |
| 无内容 | 按「通道不可用 / 超时」处理 |

⛔ **不得用字节级 `endswith(marker)` 判定**：模型与 CLI 的输出**通常带末尾换行**，字节级比对会把
正常完成的审查判成截断 → 白重跑一轮。必须先 `rstrip()` 再比对最后一行。

> **为什么必须这样做**：额度可能在审查**进行中**耗尽——审查者已读完全部输入、正要输出结论时被切断，
> 产物有分析、有文件引用、有行号，**唯独没有裁决**。它是唯一「看起来像审查成功」的失败形态
> （实测发生过：读完整个 diff 后在裁决前断掉）。⛔ 不设此判据就必然把它当成「审过了、没发现问题」。

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

## 失败分类（完整判据表）

SKILL.md 只列两条必记项，完整表在此。⛔ **不得一律按"失败"降级**——失败类决定路由。

| 失败类 | 识别信号 | 路由 | 计入「连续 2 轮永久降级」？ |
|---|---|---|---|
| **额度 / 限流耗尽** | `usage limit` / `rate limit` / `quota` / `try again at <时间>` | → **T1b**（⛔ 不降 T2，共用订阅）| ⛔ **不计入**（时间窗口问题，非通道问题）|
| **中途截断（伴额度信号）** | 有输出但无裁决，**且**输出含 `usage limit` / `try again at` 等 | 同额度类 → T1b | ⛔ 不计入 |
| **输出契约失败（无额度信号）** | 有输出但无裁决，**且无任何额度信号** | 原通道**重跑一次**；再次缺失 → 判**输出契约失败**，可换通道或报告用户，⛔ **不得伪装成额度类** | ⛔ 不计入 |
| 工具协议不兼容 | `incompatible payload` + 重连耗尽 | 该后端标**不可用并跳过** | 计入 |
| 通道不可用 | `which codex` 失败 / MCP 连接关闭 / 命令不存在 | → 下一级 | 计入 |
| 超时 | 无输出且超时 | → 下一级 | 计入 |
| 输出格式异常（非截断）| JSON 完整但字段类型错 / 文本不可解析 | 不降级，按 § T1 第 5 步处理 | 不计入 |

**为什么额度类不计入永久降级**：额度会自行恢复。一次限流若触发永久降级，会把后续**全部**审查钉死在更弱的通道上——单次故障造成长期能力损失。

**为什么工具协议不兼容要「跳过」而非「重试」**：实测该错误下 codex 自动重连 5 次全部失败。它是配置层不匹配，重试不会改变结果，只消耗时间。

---

## T1b：codex CLI · 备用计费后端

### 用途与边界

| | |
|---|---|
| 何时用 | **仅**「额度/限流耗尽」类失败触发（见 [SKILL.md § 失败分类](../SKILL.md)）|
| 为什么排在 T2 前 | 同一 CLI、同一模型档次，**只换计费后端 → 审查质量不降级**。而 T2（codex-mcp）与 T1 共用同一订阅额度，额度耗尽时降 T2 必然同样失败，纯属白跑一轮 |
| ⛔ 不参与首选探测 | 它不是独立能力层，只是 T1 的另一个计费出口 |

### 选取规则

⛔ **`model_provider` 不是计费身份**，不得用它判断「是否独立额度」：同一 provider 可对应不同账号 / 项目 / key；不同 provider id 也可能共用同一 key 或预算池。

**候选必须显式声明，⛔ 不靠推断**。约定在主 `CODEX_HOME` 的 `config.toml` 写有序候选表。

> ⚠️ **没有这张表 = T1b 不可用**（走下方流程第 1 步的「不存在」分支）。
> 装好 skill 但没建表时，额度耗尽仍然只能报告并停下——**声明了 T1b ≠ T1b 通了**。
> 首次使用前请按下方格式建表，并跑一次 § T1 Step 2 的冒烟（含真实工具调用）确认。

```toml
# 主通道自己的计费身份 —— ⛔ 必填，否则第 2 步无可比较的左值
[adversarial_review]
billing_group = "openai-subscription"

# [[adversarial_review.alt_backends]] —— 供本 skill T1b 使用的有序候选
# 本表由人维护：谁跟谁共用额度只有你知道，⛔ 不可从 model_provider 推断
[[adversarial_review.alt_backends]]
codex_home    = "~/.codex-openrouter"
billing_group = "openrouter-personal"   # 与主 home 的 billing_group 不同 = 独立额度
quality_tier  = "peer"                  # peer=同档可用于正式审查 / lower=仅应急
auto_use      = true                    # false = 仅在用户明示时使用
```

> ⛔ **主通道的 `billing_group` 必填。** 缺它时「跳过同计费组的候选」这条规则**没有左值可比**——
> 会把同一额度池的后端误当独立额度，冒烟通过、正式审查再次撞额度，白跑一整轮。
> **缺失时 fail-closed：T1b 判不可用，⛔ 不自动使用。**

流程：

1. 读候选表（不存在、或主通道缺 `billing_group` → T1b 不可用，按 [SKILL.md § 额度耗尽的默认行为](../SKILL.md) 处理）
2. **路径归一**：把每个 `codex_home` 解析为**绝对路径**（展开 `~` 与环境变量）。⛔ 从 TOML 读出的是字面字符串，`~` **不会自行展开**——直接赋给 `CODEX_HOME` 会得到 `path does not exist`，且该报错长得像「没配好」而非「没展开」，极易查错方向。解析失败或目录不存在 → 该候选不可用
3. 跳过：`billing_group` **与主通道相同**的、`billing_group` 与本轮已耗尽通道相同的、`auto_use = false` 的，以及**本轮已试过的**（见第 6 步）
4. 按表中顺序（⛔ 不按字典序）逐个跑 § T1 Step 2 冒烟（**含真实工具调用 + 三条判据**）
5. 第一个通过且 `quality_tier = "peer"` 的即为 T1b；只有 `lower` 档通过 → 视同 T1b 不可用，报告时把它列为「可选降级项」交用户决定
6. **T1b 本身也额度耗尽** → ⛔ **不得再路由回 T1b**：把该候选的 `codex_home` **绝对路径**加入本轮「已试集合」（⛔ 按 `codex_home` 去重，不按 `billing_group`——同组可能有多个可用 home），回到第 3 步取下一个；候选耗尽 → 报告并停下
7. 全部不通过 → T1b 不可用

> **「已试集合」的生存期是本次审查会话**，⛔ 不跨会话持久化——额度会自行恢复，持久化会让下次审查错过已恢复的候选。

⛔ 候选表中 **不得出现任何凭证**（key / token）；凭证仍由各 `CODEX_HOME` 自己的 auth 块提供。

> ⚠️ **`quality_tier` 是人工断言，不是冒烟能验证的属性。** 冒烟只证明「该后端能调工具并返回」，
> ⛔ **不证明模型质量与主通道同档**。`peer` 的可信度完全来自维护者，把弱模型标成 `peer` 会让
> 审查质量静默下降且无人察觉。⛔ 不要把「通过冒烟 + 标了 peer」当成系统验证出的质量结论。

调用与 T1 完全一致，只多一个环境变量（**用第 2 步归一后的绝对路径**）：

```bash
CODEX_HOME=<绝对路径> codex exec --sandbox read-only --output-schema <schema> -o <tmpfile> "<prompt>"
```

### ⚠️ 已知坑：OpenRouter 后端的模型 id 决定工具调用能否工作

**症状**：纯问答正常，**任何需要工具的调用 100% 失败**，报 `codex_core::tools::router: Fatal error: tool exec invoked with incompatible payload`，重连 5/5 后放弃。

**机制**（本地矩阵强支持，⛔ 但未用原始请求/响应或源码最终确认）：

> codex 的**本地模型元数据查找结果**决定它注册哪套 `exec` 工具表示。认得的模型 → 该家族原生表示（OpenRouter 的兼容层无法完整往返）；认不出 → 通用 fallback 表示（可往返）。

**决定性证据**——`~openai/gpt-latest` 的 `alias_target` 就是那个直接点名会失败的模型：

```jsonc
// GET https://openrouter.ai/api/v1/model/~openai/gpt-latest
{ "id": "~openai/gpt-latest",
  "alias_target": { "slug": "openai/gpt-5.6-sol" } }   // ← 同一底层模型
```

**同一模型、同一 provider、同一端点，只有 id 字符串不同**，一个通一个全败。所以差异 100% 在 codex 侧的元数据查找，**不在 OpenRouter 对该模型的处理上**（其 `/models` 也显示全部 `gpt-5.6-*` 变体均声明支持 `tools`）。

| 模型 id | codex 元数据 | 工具调用 |
|---|---|---|
| `gpt-5.6-sol` / `openai/gpt-5.6-sol` / `-terra` / `-luna` | ✅ 认得 | ❌ 全败 |
| `~openai/gpt-latest`（**官方 cookbook 值**，解析到 `-sol`）| ❌ `metadata not found → fallback` | ✅ 通 |

⚠️ **相关上游 issue 是线索不是定论**：[#18330](https://github.com/openai/codex/issues/18330) 记录了「不受支持的 tool 类型」，但「CLI 直接转发 / IDE 会过滤」是报告者的 *Analysis suggests*，无维护者确认或修复提交；`Closed as not planned` 也 ⛔ 不等于「永远不会修」。[#37825](https://github.com/openai/codex/issues/37825) 请求为 `exec` 增加 function-backed transport，说明该能力尚未稳定提供。

⛔ **备用 home 的 `config.toml` 必须用 codex 无法解析元数据的 id**（`~` 是 OpenRouter 的别名路由前缀，正好满足）。
参见 [OpenRouter 官方配置](https://openrouter.ai/docs/cookbook/coding-agents/codex-cli)。

> **这个坑正是「冒烟测试必须含真实工具调用」的来源**：错配 id 下纯问答完全正常，
> 只有真调工具才暴露。用纯问答冒烟会把一个做不了审查的后端判为可用。

---

## T2：codex-mcp

### 工具选择

| 审查类型 | 使用工具 | 说明 |
|----------|---------|------|
| 代码审查（**未提交**改动） | `mcp__codex-mcp__review-code` | 传入 prompt（审查 brief）+ `uncommitted: true` |
| 代码审查（**已提交**改动） | `mcp__codex-mcp__review-code` | 传入 prompt（审查 brief）+ **显式 diff 内容或 commit 范围**，⛔ 不得传 `uncommitted: true` |
| 方案 / 设计 / 文档审查 | `mcp__codex-mcp__delegate-task` | 传入 goal（审查 brief）+ mode: "plan" |

> **为什么区分两行**：`uncommitted: true` 在改动已落盘时会得到**空 diff**——审查照常返回"无问题"，但它什么都没看到。本 skill 独立调用时默认审工作区（未提交），故用第一行；`ms-dev-workflow` S9 Phase 4 的 **drain 侧**（Commit 1 已落盘后集中补审）必须用第二行。判定见 [verification-flow.md § diff 源](../../ms-dev-workflow/references/verification-flow.md)。

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
