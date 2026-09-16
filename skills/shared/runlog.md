---
title: 运行日志（runlog）
scope: 跨 skill 编排层共性
spec_version: runlog.v1
verdict_due: 2026-11-30
generated_at: 2026-08-26
related:
  - docs/superpowers/specs/2026-08-26-devdocs-rule-triage-and-runlog-design.md（判据与判决点）
  - skills/shared/constraints.md § 2（yaml-summary-v1 信封）
---

# 运行日志（runlog）

**目的**：把每次子 Agent 返回的 `yaml-summary-v1` 留在磁盘上，供后续判断**哪些规则该删**。

现状是这些摘要在编排器上下文里过一遍即蒸发。本文的全部内容就是「别扔掉它」——不新增字段、不新增 status、不改信封。

⚠️ **本文自带死期。** 见文末「判决点」。

## 位置与格式

- **路径**：`<workspace_context.docs_dir>/devdocs/.runlog.yaml`
- **格式**：多文档 YAML 流，每条记录以 `---` 分隔
- **提交**：随 Commit 2（文档提交）入库，不新增提交机制

> 选 YAML 多文档流而非 JSONL：写入方是负载下的 LLM，它本就在产出这段 YAML，零转换、零转义风险。聚合端的便利让位于写入端的可靠。

消费项目建议在 `.gitattributes` 加一行，使 append-only 冲突按并集解决：

```gitattributes
**/.runlog.yaml merge=union
```

## 谁写，何时写

编排层（`pipeline` / `feature` / `bugfix` / `dev-workflow` 等任何通过 Task tool 委托的 skill）在**收到子 Agent 的 yaml-summary 之后**追加一条。

**子 Agent 不写 runlog。** 它只负责返回摘要；落盘是编排层的事。子 Agent 自行追加会造成重复记录与嵌套委托下的顺序错乱。

## 记录形状

### 首条：形态指纹

文件创建时写一次。

```yaml
type: shape
lang: <取自 codebase-insight.md frontmatter 的 tech_stack；读不到写 null>
mode: <取自 workspace_context 的拓扑 mode>
scale: <"<5k" | "5k-50k" | ">50k"，一次性计算>
created_at: <ISO 8601>
verdict_due: 2026-11-30
```

**不得为写 runlog 而发起扫描。** 形态字段只从已有产物读取，读不到就写 `null`。

### 后续：事件记录

`yaml-summary-v1` 信封**逐字原样**，追加两个键：

```yaml
ts: <ISO 8601>
entry: <用户的原始措辞，逐字保存>
skill: xxx            # 以下为信封原有字段，不改
status: success | failed | interrupted | partial
summary: {...}
blockers: []
output_files: []
new_ids: {}
```

**`entry` 必须是用户原话，不是归一化后的命令。** 它是授权推断的审计线索——事后要能复核「模型当时凭什么认为被授权了」。这是 runlog 里唯一承担安全职责的字段。

## 硬纪律

> 本节**刻意不使用 `⛔` 标记**。runlog 按设计不设门禁（规则 1），既没有门控（无阻塞态），这些条目也不是面向执行者的禁令，而是**对本机制自身设计的约束**。`⛔` 的两种合法语义见 [constraints.md](constraints.md) `gate/two-senses`。

| # | 规则 |
|---|---|
| 1 | **不设门禁。** 写失败即静默跳过，**不得**因 runlog 未写成而阻断任何流程 |
| 2 | **不新增字段、不新增 status 值、不改信封。** skill 私有统计一律走既有的 `summary.details` |
| 3 | **不采集自报合规。** 不得新增「本次是否遵守了 X」「跳过了哪些步骤」「这道门是否有用」一类字段 |
| 4 | **不为它新建检查器 / lint rule / health 维度** |
| 5 | 产物只写 `docs_dir`，三种拓扑一致，不触碰任何代码根 |

规则 3 的判据与已废弃的 retrofit 逆向推导同源：**被测者书写测量记录**。一个无视了 `⛔` 的模型同样不会记录「我无视了 `⛔`」——该失败模式在构造上即静默，采集结果会系统性偏向「遵守良好」。拿这种数据做删除决策**比没有数据更糟**。

## 判决点

> **累计 60 条 task 级记录，或 2026-11-30，孰先到。**
> 到期读一次，然后二选一：**依据它删规则**，或**删它自己**。
> 到期未读，本文自动作废，`.runlog.yaml` 应被删除。

### 读的时候先做交叉校验

⚠️ runlog 无门禁，漏写是**静默**的。判决点第一步不是读内容，是**用 `git log` 的任务数交叉校验 runlog 条数**——缺口本身即一项发现（说明编排层没有稳定执行追加）。

### 能问与不能问

| 问题 | 答得了吗 |
|---|---|
| 哪些门被规律性绕过 | ✅ 主要在 `git log` 的 commit trailer 里，runlog 提供形态维度 |
| 门触发后是否真的改了东西 | ✅ blocker 记录 → 后续 diff 是否触及该处 |
| 哪些门从未触发 | ⚠️ 能测频次，**推不出无用**——可能是废的，也可能因为写在那儿所以没人违反。进观察名单，不进删除名单 |
| 模型是否遵守了规则 | ❌ 不可测，见硬纪律 3 |

## 已有埋点：先读再埋

**最高价值的记录已经在任务台账里，且从未被读过。** 以下字段在语义上就是「我绕过了这道门，理由如下」：

| 字段 | 记录 |
|---|---|
| `profile_downgrade_reason` | 风险分档被人为降档 |
| `skip_trace_reason` | 追溯校验被关闭 |
| `pending_reason` | 审查被延后 |
| `exploration_mode` | 整套文档强制被豁免 |

一条被规律性绕过的门，就是一条设计错了的门。此项零新增成本。

⚠️ **本仓（skill 规格库）自身不跑 keel**，304 个提交中零个真 trailer。上述统计只能在**消费 keel 的项目**里做；判决点的计数同理，在本仓不会推进。
