# 执行者模式（被派来做指定卡）

本会话被另一个会话（派单方）派来做指定卡时，按本文件执行：测试和实现自己写，⛔ 不派测试/实现/同步/全量子代理。步骤与质量地板不变，只改「谁写测试和实现、怎么防迁就」，⛔ 不改审查时机。

工作目录是 brief 给的 worktree，brief 该带什么、合并与共享资源的规则见 [constraints.md § 并行工作区](../../shared/constraints.md#并行工作区git-worktree)。

## 判定

- **是**：派单 brief 写明「你是 T-xxx 的执行者」或等价意思；用 hcom 时就是 hcom 派单。任务的 `assignee` 即执行者名。
- **不是**：用户在主会话里说「做 T-xxx」「把 T-01~T-05 做了」——这是普通单任务/批量，照 SKILL.md 编排规范派子 Agent。
- 只从 brief 识别，⛔ 不新增用户要敲的参数。

## 步骤

1. **读卡、读相关代码**，自己写 Sprint Contract 和测试，不派子代理。
2. **测试提交（Commit T）**：只含测试文件（和必要的骨架）。行为卡此时测试应红；`move` 档或表征测试应全绿（见 [execution-flow.md](execution-flow.md) S5 例外）。
3. **注错一次**（每个 Commit T 一次）：对被测代码临时注入一处错误，确认至少一条测试变红，还原。记下注错位置与变红的测试名。复用前一张卡已冻结且已注错的测试集时不重复。
4. **写实现，提交 Commit 1**（代码）。
5. **机器检查**（全部确定性）：
   - 顺序与冻结：按 [constraints.md §完成门](../../shared/constraints.md#完成门工具检查) 的前两项在本分支自查（台账由派单方登记，门在派单方那边才触发）；测试被改即 ⛔ Blocker，与「测试不可变」同一条地板。
   - build + 全量测试一次：输出写文件，只读失败摘要和退出码。
   - `move` 档另跑 `keel move-check`，按 [verification-flow.md § move 档](verification-flow.md#move-档) 自判，不合规自己升 `guarded`。
6. **交卡**：一条消息发回派单方，字段见下。
7. **不写台账、不写 `docs/devdocs/`**：执行者分支上只有产品代码和测试（Commit T、Commit 1）。Sprint Contract、注错记录、跳过记录随交卡消息发回，由派单方落进 `audit/<id>/` 并登记台账。

### 交卡消息字段

| 字段 | 内容 |
|---|---|
| 提交 | Commit T、Commit 1 的 sha（复用已有测试集时注明无 Commit T 及复用来源） |
| Sprint Contract | 摘要 |
| 注错记录 | 注错位置、变红的测试名 |
| 全量结果 | 通过/失败摘要与退出码 |
| S8 / S10 / UI | 完成检查结果、自描述更新、UI 卡的 `/verify --ui` 结论 |
| 审查 | audit 档的 Phase 1–4 结论；guarded 有风险触发时的 Phase 1–3 结论 |
| `move` 档 | 判定摘要与胶水清单 |
| 跳过记录 | 跳过了什么、为什么 |

⛔ 不贴逐文件哈希。

## 档位与步骤

| 档位 / 步骤 | 执行者怎么做 |
|---|---|
| audit | 照旧 inline 做 Phase 1–4（Phase 4 调外部审查器），过了才 Commit 1；卡由派单方直接标「已完成」并写 `ext_review_state` |
| guarded 有风险触发 | 照旧 inline 做 Phase 1–3 |
| fast / guarded 无触发 | 照旧延后：派单方标 review_pending，按批 drain |
| S8 完成检查、S10 自描述 | 执行者自己做，结果进交卡消息 |
| `/verify --ui` | UI 卡执行者自己做 |
| `/sync`、`/compound` | 派单方按批做 |

## 子代理与等待

- 子代理只用于「读得多、回得少」的事：大日志、大快照、全量测试原始输出。
- 等待用一次长阻塞（带超时的命令或事件等待），⛔ 不定时轮询。

## 断点续做

- 有 Commit T、无 Commit 1 → 从写实现续做。
- 两者都有 → 从机器检查续做。
