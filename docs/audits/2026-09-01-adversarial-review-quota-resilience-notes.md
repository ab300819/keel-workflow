# adversarial-review 额度耗尽韧性 —— 待确认笔记

> 2026-09-01。**已实施**（skill 改动 + openrouter config 修复），本文降级为**故障档案**：留实测事实、推断错误留档、以及被否决的候选。
> 现役规则以 [SKILL.md](../../skills/adversarial-review/SKILL.md) 与 [external-reviewer-integration.md](../../skills/adversarial-review/references/external-reviewer-integration.md) 为准，⛔ 本文不再是规则来源。
>
> 起因：CON-XXX 实施 diff 的第 6 轮审查，Codex 订阅额度耗尽（重置 4 小时后），切 OpenRouter 后端又撞到另一类失败。
>
> 经 Codex 独立审查（2 P1 + 5 P2 + 2 P3 全部采纳），其中一条尤其值得记：**本次修复一度重犯了它要防的那个错**——初版冒烟写成 `codex exec ... | grep -q <哨兵>`，而管道退出码是 `grep` 的，codex 自身非零退出被完全吞掉（实证 `sh -c 'exit 7' | grep -q ""` 整体返回 1）。要防的正是同一类「靠单一信号反推成功」。

## 1. 实测到的失败形态（4 类，全部真实发生过）

| # | 形态 | 原始信号 | 危险度 |
|---|---|---|---|
| 1 | **订阅额度耗尽（调用前）** | `ERROR: You've hit your usage limit ... try again at 2:48 PM` | 低——一眼可辨，无输出 |
| 2 | **订阅额度耗尽（审查中途）** | 读完全部输入、输出了大段分析，**在出裁决前被切断** | ⚠️ **最高** |
| 3 | 备用后端工具协议不兼容 | `Fatal error: tool exec invoked with incompatible payload` ×20 + `Reconnecting... 1/5` | 中 |
| 4 | 备用后端上游限流 | `openai/gpt-5.6-sol is temporarily rate-limited upstream` | 低 |

### 形态 2 是核心风险

其余三类都表现为「没有结果」，一眼可辨。**形态 2 表现为「有结果但没结论」**——产物里有分析、有文件引用、有行号，看起来像一次完整审查，极易被当成「审过了、没发现阻塞问题」。

本次它就真的发生了：R6 第一次跑读完了整个 diff（输出里能看到它已读到当轮新加的 `archive.md`），然后在裁决前断掉。**如果不是特意去数「有没有裁决段」，这份输出会被当成 PASS。**

## 2. 实测：备用后端能力边界

`~/.codex-openrouter`（`model_provider = "openrouter"`，`model = "gpt-5.6-sol"`）：

**已用最小用例隔离验证**（两次独立调用）：

| 场景 | 结果 |
|---|---|
| 纯问答（无工具） | ✅ 成功，19453 tokens 正常返回 |
| 需要工具调用（读 hostname） | ❌ `tool exec invoked with incompatible payload`，重连 5/5 后放弃 |

**这不是限流**（纯问答同时段是通的），是工具协议不兼容。

### 根因已定位并修复

上游 [openai/codex#18330](https://github.com/openai/codex/issues/18330)（**Closed as not planned，不会修**）：

> Codex CLI 发送的 `tools` 数组含 OpenRouter 不接受的 tool 类型；OpenRouter 只接受 `"function"` 类型或 `"openrouter:*"` 前缀。**Codex IDE 发送前会过滤/规范化，CLI 不会。**

**模型 id 是开关**（本地逐个实测）：

| 模型 id | codex 能否解析元数据 | 工具调用 |
|---|---|---|
| `gpt-5.6-sol`（原配置） | ✅ 认得 | ❌ |
| `openai/gpt-5.6-sol`（加前缀，同变体） | ✅ 认得 | ❌ |
| `openai/gpt-5.6-terra` / `-luna` | ✅ 认得 | ❌ |
| `~openai/gpt-latest`（**OpenRouter 官方 cookbook 值**） | ❌ `metadata not found → fallback` | ✅ **通**（实测返回真实 hostname） |

codex 认出模型家族 → 注册该家族**原生全量工具集**（含非 `function` 类型）→ OpenRouter 拒收；认不出 → 落回**通用 fallback 工具集**（只含可接受类型）→ 正常。`~` 是 OpenRouter 别名路由前缀，正好让 codex 解析不到元数据。

**已修**：`~/.codex-openrouter/config.toml` 的 `model` 改为官方推荐值 `~openai/gpt-latest`（原值备份为 `config.toml.bak-*`），并在文件内写明为何不能改回具体 id。**T1b 因此从空壳变为真实可用。**

⚠️ 代价：走的是 codex 自己标记为 `this can degrade performance and cause issues` 的 fallback 元数据路径。这是上游不修的前提下唯一可用路径。

### 两处推断错误（留档）

1. 曾判 `shell_snapshot=false` 修好了 —— **错**。过滤输出时漏看了后续错误行，实际仍失败。
2. 曾判 `google/gemini-3-pro` 可用（"0 次 incompatible"）—— **错**。它是 `400 not a valid model ID`，根本没走到工具调用；只 grep `incompatible` 把 400 当成了成功。

**教训：判「通过」必须看正向证据（真实工具结果），不能靠「没出现某个错误」反推。**

> **一个有用的观察**：该失败下模型**主动声明了自己的无能力**——「工具调用异常并被中止，未能实际读取主机名，因此无法可靠告诉你结果」，没有编造。
> 这与形态 2（截断）正相反：**工具失败是自陈的，截断是静默的**。所以截断才需要机械判据（§3.3），这一类不需要。

三个 CODEX_HOME 的实际分布：

| 目录 | provider | 独立计费 |
|---|---|---|
| `~/.codex` | 默认（订阅） | ❌ 与 T1/T2 共用 |
| `~/.codex-review` | 默认（订阅） | ❌ 同上 |
| `~/.codex-openrouter` | openrouter | ✅ **已修通**（见下「根因已定位并修复」）|

## 3. 候选修法 —— 实施结果

> 下列各条均已落地，措辞与判据的**权威版本在 skill 侧**（本节保留当时的推理过程）。
> Codex 审查后的修正见 §5。

### 3.1 新增 T1b 层：同 CLI 换计费后端

现有降级链 `T1 codex CLI → T2 codex-mcp → T3 Task 子 Agent` 有一处结构性错误：

> **T2 与 T1 共用同一订阅额度。** 额度耗尽时降 T2 必然同样失败，白跑一轮，然后才降到 T3（检出率明显更低）。

候选：在 T1 与 T2 之间插 **T1b = `CODEX_HOME=<备用home> codex exec ...`**，同 CLI 同模型档次，**只换计费后端 → 审查质量不降级**。这是它必须排在 T2 前面的唯一理由。

⚠️ **但按 §2 实测，现有备用后端工具调用不通**——T1b 目前是空壳。要么先修通 openrouter 工具协议，要么 T1b 的探测规则必须包含「冒烟测试须含一次真实工具调用」，否则会把不可用后端当可用。

### 3.2 失败分类表：不同失败走不同路径

| 失败类 | 识别 | 候选路由 |
|---|---|---|
| 额度/限流耗尽 | `usage limit` / `rate limit` / `quota` / `try again at <时间>` | → T1b。⛔ **不降 T2**（共用订阅） |
| 通道不可用 | `which codex` 失败 / MCP 连接关闭 | → 下一级 |
| 超时 | 无输出且超时 | → 下一级 |
| 输出不可解析 | 有输出但 JSON/文本均解析失败 | 不降级，按现有第 5 步包装展示 |
| **中途截断** | 有大段输出但**无裁决段** | 标 `truncated: true`，按额度类重跑 |
| **工具协议不兼容** | `incompatible payload` + 重连耗尽 | 该后端标不可用，跳过（⛔ 不重试，重试无效——实测 5 次全败） |

### 3.3 截断检测的判据（需要定）

「有没有裁决」怎么机械判定？候选：审查 prompt 强制要求输出以固定标记结尾（如 `=== VERDICT ===` 或 schema 里的必填 `verdict` 字段），**缺该标记即判截断**。

- 代码审查已用 `--output-schema`，JSON 缺 `verdict` 字段即可判定 —— 这条成本最低
- 方案/文档审查走文本解析，需要约定尾标记
- ⚠️ 待确认：是否值得为此改动现有 `review-output.schema.json`

### 3.4 额度类失败不计入永久降级

现有规则「连续 2 轮失败 → 永久降级 `primary_method`」。额度是**时间窗口问题而非通道问题**——一次限流会把后续全部审查永久钉死在更弱通道上。

候选：额度类失败 ⛔ 不计入「连续 2 轮」计数。

### 3.5 向用户报告的最小信息集

额度耗尽且备用不可用时，应报：**已耗尽的通道 + 输出里给出的重置时间 + 当前可选项（等待 / 降级 T3 / 换后端）**，由用户决定。
⛔ 不自行决定「就这样吧」，也 ⛔ 不静默降级到 T3 后宣称审查完成。

### 3.6 T3 必须标注检出率折损

T3（Task 子 Agent）与被审对象**同模型、同盲区**。本次 6 轮的实证：每一批「消费方漏项」都是 Codex 先指出的（R1 漏 4 处、R2 漏 8 处、R4 漏 2 处、R5 漏 1 处），自审只能在拿到它的方法后复用。

候选：降到 T3 时结论里必须标注，⛔ 不得让「审过了」掩盖「审得更浅了」。

## 4. 已拍板的四点

| # | 决定 |
|---|---|
| 1 | **先修 openrouter 工具协议，再做 T1b** —— 已修通，T1b 有实体 |
| 2 | 截断检测 **schema 必填 `verdict` + 文本尾标记**双轨 |
| 3 | ⛔ **不改** `review-output.schema.json` —— `verdict` 本已是必填字段，无需改动 |
| 4 | 额度耗尽默认 **报告并停下等用户决定**，⛔ 不自动降 T3 |

## 5. Codex 审查后的修正（2 P1 + 5 P2 + 2 P3，全部采纳）

| 级别 | 问题 | 修法 |
|---|---|---|
| **P1** | 新冒烟仍假阳性：`\| grep -q` 只返回 grep 状态 | 改为单独保存 `RC=$?` + `-o` 存最终消息 + **三条判据同时成立** |
| **P1** | 截断门与旧容错路径冲突：`JSON 失败 → 文本 → F-001` 会把截断洗成普通 finding | 写死优先级：不完整 JSON ⛔ 不得回落文本 / F-001 |
| P2 | 根因写得过于确定（#18330 的因果链是报告者 *Analysis suggests*，无维护者确认；`Closed as not planned` ≠ 永不修） | 降级为「本地矩阵强支持的机制推断」，并补上更强的 `alias_target` 证据 |
| P2 | 截断被无条件当额度类，但缺标记 ⛔ 不证明 quota | 分流：伴额度信号 → T1b；无信号 → 原通道重跑一次 |
| P2 | T1b 自己额度耗尽会再路由回 T1b（死循环） | 取候选表下一个；候选耗尽 → 报告并停下 |
| P2 | `model_provider` 不是计费身份（同 provider 可不同账号；不同 provider 可共用 key） | 改为**显式有序候选表** + `billing_group` / `quality_tier` / `auto_use`，⛔ 不从 provider 推断 |
| P2 | embedded-headless 未接入 T1b，却未声明边界 | 集成文档显式写明 T1b 不属其共享契约 |
| P3 | SKILL.md:401 说 T1b 参与首选探测，与集成文档矛盾；`primary_method: codex-cli-alt` 不可达 | 统一为 ⛔ 不参与首选探测；yaml 的 `primary_method` 枚举去掉该值 |
| P3 | 为压行合并长句致可读性受损，且只剩 12 行余量 | 失败分类完整表移入 references，正文只留两条必记项 + 指针 |

### Codex 论据中未能证实的两条（留档）

| 它的说法 | 我的核查 |
|---|---|
| `~openai/gpt-latest` 解析到 `openai/gpt-5.6-sol` | ✅ **证实**，`alias_target.slug` 确为该值——且这条比我原来的证据更强 |
| gemini 正确 slug 是 `google/gemini-3-pro-preview` | ❌ **不成立**，`/models` 里无此 id（只有 `google/gemini-3-pro-image` 系与 `google/gemini-3.1-pro-preview`）。细节，不影响结论 |
4. 额度耗尽时默认行为：报告并停下等用户决定，还是自动降 T3 并标注
