# keel 精简执行路径：被派执行者与纯移动重构卡（设计稿）

> 状态：待用户审阅。方向由用户 2026-11-22 定：方案 B（被派执行者自己做，用顺序与机器检查代替上下文隔离）；「留一部分验收用例不给实现方」先不做。
> 关联：[多 agent 并行设计稿](2026-11-20-keel-parallel-agents-design.md)（PM 侧记账）。本稿管执行者侧怎么做一张卡，两稿共用「被派执行者」身份，见 §4.1。

## 1. 为什么做

EMSPR 第 1 批大重构（约 50 张拆分卡）的只读审计（emspr-pm，2026-11-22）显示一半多的 token 没有推进「行为一致」「体量达标」两个目标。本会话逐条核对后，和 keel 自身有关的部分：

| 现象（审计实测） | keel 源头 |
|---|---|
| codex 队友再派子代理并轮询：子代理会话占 codex token 47%，派单/等待回合占 37% | `dev-workflow/SKILL.md:172`「所有模式（含单任务）必须通过子 Agent」、`:191`「主 Agent 禁止直接执行 TDD」。189 个 codex 会话中 153 个读过 dev-workflow；子代理名前五 tests 107、verify 83、contract 75、impl 72、quality 43，正是 Test Agent / Sprint Contract / Impl Agent / code-quality / verify |
| 纯搬家卡也走注错、20 检查点、独立审查 | review_profile 三档只按风险分，没有「纯移动」 |
| 表征测试在原码上必然绿，项目每卡绕开红验 | `execution-flow.md:136` 把「新测试意外通过」判为测试无效，与 `refactor/references/rewrite-flow.md:59`「重写前先补表征测试」矛盾 |
| 一卡一次台账提交，几十张拆分卡开销大 | `dev-workflow/SKILL.md:284`、`:335` 要求逐任务 Commit 2 |
| 台账越来越大：75 张卡停在 review_pending 不能归档 | `sync/references/archive.md:239` 只归档「已完成」 |

用户补充子代理的两个用途：**控制主线上下文**、**防止测试迁就实现或实现迁就测试**。结论是两者都有更便宜的做法：

- 上下文：会话边界比子代理便宜。被派执行者的会话本身就是隔离，再分包对 PM 主线没有好处；子代理只在「读得多、回得少」时省钱（大日志、全量测试输出、大快照）。
- 测试迁就实现：先单独提交测试再写实现，写测试时实现不存在；提交顺序可由 git 机器核对。
- 实现迁就测试：现在的信息屏障挡不住（实现方要跑测试，看得到测试代码）。真正起作用的是测试冻结 diff 校验（已有）、每套测试注错一次、重构卡的逐字搬判定或新老对拍。

## 2. 目标与非目标

**目标**

- G1 被派执行者做一张卡时不再派子代理写测试、写实现、同步、跑全量；协调回合降到「领卡一次、交卡一次」。
- G2 防迁就由机器检查承担：测试先提交（顺序可核）、冻结 diff、注错一次。
- G3 纯移动重构卡只做确定性检查，直接「已完成」，不进 review_pending。
- G4 表征测试允许在原码上先绿。
- G5 批量时台账按批提交一次。

**非目标**

- 不改用户在自己主会话里直接跑 dev-workflow 时的子代理分工（Test Agent / Impl Agent）：那里编排器就是用户主线，子代理控制上下文仍然划算。等执行者模式用顺手再议。
- 但 §4.2 `move` 档、§4.4 表征测试先绿、§4.5 按批提交台账**两种用法都生效**（用户 2026-11-23 定）：它们管的是卡的类型和记账节奏，与谁来做无关。主会话里的 `move` 卡仍由 Impl Agent 子代理搬，只是不做独立审查。
- 不做「隐藏验收用例」（用户 2026-11-22 定先不做，等抓到硬写案例再加）。
- 不让 keel 依赖 hcom，不做派单通知。
- 不管项目自加的层（三方注错、逐文件贴 SHA、20 检查点、录制器打磨），那是项目裁定。

**反目标**（做了反而坏事）

- 纯移动通道变成后门：行为改动混进「纯移动」跳过复核。判定必须是工具出证据、可复核，见 §4.3。
- 执行者直接写台账：破坏 EMSPR「只有 PM 写」的单一写入者（与并行稿反目标一致）。
- 给用户增加要记的命令或子指令（2026-08-26「用户面零子指令」）。

## 3. 方案比较

| 方案 | 做法 | 取舍 |
|---|---|---|
| A. 只给纯移动卡开路 | 行为卡照旧双 Agent | 最稳，但审计里分包最重的正是行为卡（前端 duma 每卡拆 contract/tests/impl/quality/verify），省得有限 |
| **B. 被派执行者一律自己做（用户选定）** | 测试先提交 + 顺序核对 + 冻结 diff + 注错一次代替上下文隔离；纯移动卡再省审查 | 省得最多；防不住「先想好实现再写测试」，由注错和 PM 复核/按批独立审查兜底 |
| C. 保留子代理，只改等待方式 | 阻塞等待代替轮询 | 只省协调回合，子代理重读上下文的 47% 不动 |

## 4. 设计

### 4.1 被派执行者（执行者模式）

**判定**：本会话是被另一个会话派来做指定卡的（派单 brief 写明「你是 T-xxx 的执行者」或等价意思；用 hcom 时就是 hcom 派单）。dev-workflow 从 brief 识别，⛔ 不新增用户要敲的参数。并行稿落地后，任务的 `assignee` 就是这个执行者的名字。

**做法**（替代 S1.5–S11 中的子 Agent 调度，步骤与质量地板不变）：

1. 读卡、读相关代码，写 Sprint Contract 和测试，自己做，不派子代理。
2. **测试提交（Commit T）**：只含测试文件（和必要的骨架）。行为卡此时测试应红；表征测试卡此时应绿（§4.4）。
3. **注错一次**（每个 Commit T 一次）：对被测代码临时注入一处错误，确认至少一条测试变红，还原。记录注错位置与变红的测试名。复用前一张卡已冻结且已注错的测试集时不重复。
4. 写实现，提交 **Commit 1**（代码）。
5. **机器检查**（全部确定性）：
   - 顺序：`git merge-base --is-ancestor <Commit T> <Commit 1>`。
   - 冻结：`git diff --quiet <Commit T> <Commit 1> -- <Commit T 里的测试文件>`，有改动即 ⛔ Blocker（与现有「测试不可变」同一条地板）。
   - build + 全量测试一次；输出写文件，只读失败摘要和退出码。
   - 纯移动卡另跑 §4.3 的逐字搬判定。
6. **交卡**：一条消息发回派单方，含 Commit T / Commit 1 的 sha、Sprint Contract 摘要、注错记录、全量结果与退出码、纯移动卡的判定摘要与胶水清单。⛔ 不贴逐文件哈希。
7. **不写台账、不写 `docs/devdocs/`**：执行者分支上只有产品代码和测试（Commit T、Commit 1）。Sprint Contract、注错记录、跳过记录随交卡消息发回，由派单方落进 `audit/<id>/` 并登记台账。（我的判断：守住单一写入者，执行者分支不产生文档冲突。）

**子代理只用于**：读大日志、大快照、全量测试原始输出等「读得多、回得少」的事。等待用一次长阻塞（带超时的命令或事件等待），⛔ 不定时轮询。

**其余步骤照旧，只是自己做**（我的判断：执行者模式只改「谁写测试和实现、怎么防迁就」，⛔ 不改审查时机）：

| 档位 / 步骤 | 执行者怎么做 |
|---|---|
| audit | 照旧 inline 做 Phase 1–4（Phase 4 调外部审查器），过了才 Commit 1；卡由派单方直接标「已完成」并写 `ext_review_state` |
| guarded 有风险触发 | 照旧 inline 做 Phase 1–3 |
| fast / guarded 无触发 | 照旧延后：派单方标 review_pending，按批 drain；并行稿「验证者 ≠ 实现者」在 drain 生效 |
| S8 完成检查、S10 自描述 | 执行者自己做，结果进交卡消息 |
| `/verify --ui` | UI 卡执行者自己做 |
| `/sync`、`/compound` | 派单方按批做 |

**断点续做**：有 Commit T 无 Commit 1 → 从写实现续做；两者都有 → 从机器检查续做。

### 4.1.1 登记与合并（派单方）

- 两次提交都用 `task commit` 登记，Commit T 加 `--kind test`（`commits[]` 新增可选字段 `kind`，取值 `test`，缺省为代码提交）。drain 送审的 diff 从「只取 Commit 1」改为**本卡在该仓登记的最早提交的父提交到最晚提交**，范围由 `task get <id> --diff-range` 给出，⛔ 不由 agent 自己算。（我的判断。）
- 执行者分支合进集成分支后**再登记**，登记的是落地后的 sha（rebase 会改 sha）。⛔ 不 squash 合并：squash 会把 Commit T 和 Commit 1 合成一个，顺序证据丢失。落地后派单方重跑一次 §4.1 第 5 步的顺序与冻结检查。（我的判断。）

### 4.2 审查档位新增 `move`

- review_profile 值域从 `fast / guarded / audit` 扩为加 `move`。schema 仍是 `keel.task.v1`（只加枚举值）；旧版 keel 读到 `move` 会报 K5，所以随版本发布，见 §6。
- dev-tasks 风险分类器：任务描述为拆分、搬移且声明「行为不变」时提议 `move`。执行期只升不降规则不变：§4.3 判定不通过 → 升到 `guarded`。
- `move` 档：不做 Phase 1–4 独立审查，Commit 1 后直接 `已完成`，因此可被 sync 正常归档。
- 测试来源（我的判断）：被搬的代码已有冻结且注错过的表征测试集 → 无 Commit T，直接复用；没有 → 本卡先写表征测试作 Commit T（全绿，§4.4），注错一次，再搬。
- 质量地板 5 条照旧。

### 4.3 逐字搬判定：`keel move-check`

新增 keel 子命令（agent 用，非用户入口）：`keel move-check <base>..<head> [-- <路径>…]`。

- 算法：取区间 diff 的删除行与新增行，各自去首尾空白后按多重集合抵消；剩下的新增行、删除行即「胶水」，按文件列出，带行号。
- 输出：搬动行数、胶水行数、胶水清单；退出码 0 表示算完（判定是证据，不是门禁）。
- 判定规则（写进 verification-flow，不写进工具）：胶水只许是声明、签名、调用、import/using、括号、访问修饰符和构造参数透传；出现条件、运算、字面量、返回值改动 → 不是纯移动，升 `guarded`。
- 谁判（我的判断）：执行者交卡前先按规则自判，不合规自己升 `guarded`；合规的胶水清单随交卡发回，派单方按批过目一次（不是逐卡审）。
- 派单方事后否决：不回滚已完成或已归档的卡（状态机没有这条路），另开修复卡，`--derived-from` 指向原卡。

### 4.4 表征测试先绿

`execution-flow.md` S5 红验加一条例外：任务为 `move` 档，或测试属于表征测试（锁现有行为，期望值取自基线）时，Commit T 上测试应**全绿**；「意外通过」判定不适用。其余冻结、不可变、注错规则不变。refactor 的 `rewrite-flow.md` 改为引用这条，不复述。

### 4.5 按批提交台账

- 批量模式或执行者模式下，台账提交（Commit 2）可按批一次：每张卡的代码提交照旧逐卡，`task commit` / 状态改动逐卡由工具写入 `state/`，批末一次 `/sync` + 一次 Commit 2。
- 工作区洁净校验从「每任务 Commit 2 后」改为「每任务 Commit 1 后，`docs/devdocs/` 以外洁净」+「批末 Commit 2 后全洁净」。
- 中途中断：未提交的 `state/` 改动是工具写的，manifest 认得，续做时照常；批末补 Commit 2 即可。

### 4.6 完成门：由 keel 工具检查，不靠文字

与 keel 3.x「规则由工具执行」一致（用户 2026-11-23 提出）。`task set <id> --status 已完成|review_pending` 写入前，keel 对该卡登记的提交做以下检查，任一不过 → 退出码 1、文件不变、提示原因：

| 检查 | 条件 | 判定 |
|---|---|---|
| 测试先于代码 | 登记了 `kind=test` 的提交 | 每个代码提交都以某个测试提交为祖先（`git merge-base --is-ancestor`） |
| 测试冻结 | 同上 | 测试提交里的测试文件，在最早测试提交到最晚代码提交之间没有改动 |
| 纯移动 | `review_profile=move` 且目标状态为 `已完成` | 在登记范围上跑 `move-check`；胶水含控制流关键字（`if/else/for/while/switch/case/return/throw/try/catch`）、比较或逻辑运算符、数字或字符串字面量的改动 → 拒绝「已完成」，提示改 `--profile guarded` 走 review_pending |
| 注错记录 | 登记了 `kind=test` 的提交 | `--record` 指向的 `audit/<id>/` 存在（只查有记录，查不了是否真做） |

- 不压缩合并（squash）由前两项覆盖：测试提交与代码提交是同一个 sha 时「测试先于代码」不成立。**已知漏口**：完成门由 `kind=test` 登记触发，派单方若把压缩后的提交只当代码提交登记，门不会触发；靠派单方按 workflows.md 登记规则和按批审查发现。
- 没有 `kind=test` 提交的卡（如复用已有表征测试集的 `move` 卡、非编码卡）跳过前两项和注错记录检查。
- 提交 sha 在本地仓库解析不到 → 退出码 1，提示先把执行者分支合进来再登记（与 §4.1.1「落地后再登记」一致）。
- 关键字表按常见语言取并集、写在代码常量里；误拦时的出路是升 `guarded`，⛔ 不提供跳过开关。

仍只靠文字、工具管不到的：注错是否真做（有派单方复核和按批独立审查兜底）；执行者是否派子代理（只影响成本，可事后看用量发现）。

### 4.7 文件改动清单

| 文件 | 改动 |
|---|---|
| `skills/dev-workflow/references/executor-mode.md`（新） | §4.1 全文 |
| `skills/dev-workflow/SKILL.md` | 编排规范一节加一句「被派执行者见 executor-mode.md」；逐任务 Commit 2 两处改为引用 §4.5；保持 ≤500 行 |
| `skills/dev-workflow/references/execution-flow.md` | §4.4 例外；S11/Commit 2 节奏 |
| `skills/dev-workflow/references/verification-flow.md` | `move` 档与 §4.3 判定规则 |
| `skills/dev-workflow/references/task-orchestration.md` | 批量 Commit 2 与洁净校验；续做判定认 Commit T、认批末才有 Commit 2 |
| `skills/dev-workflow/references/auto-mode.md` | 无人值守的洁净校验同 §4.5 |
| `skills/verify/SKILL.md` | drain 送审 diff 范围按 §4.1.1 |
| `skills/shared/constraints.md` | review_profile 值域加 `move`（真源） |
| `skills/dev-tasks/SKILL.md` | 风险分类器提议 `move` |
| `skills/refactor/references/rewrite-flow.md` | 表征测试先绿改为引用 |
| `skills/shared/scripts/keellib/schema.py`、`keel.py`、新 `keellib/movecheck.py` | `move` 枚举、`commits[].kind`、`move-check` 子命令、`task get --diff-range` |
| `skills/shared/scripts/keellib/tasks.py`（或新 `keellib/donegate.py`） | §4.6 完成门 |
| `skills/shared/scripts/tests/` | move-check、枚举、`kind`、完成门各检查的正反例（用临时 git 仓） |
| `docs/workflows.md` | PM 派单段：派单 brief 写明执行者身份，交卡一条消息 |
| `docs/superpowers/specs/2026-11-20-keel-parallel-agents-design.md` | §4.1 引用本稿的执行者身份 |

## 5. 验收

- 执行者模式代表性走查：给一张行为卡和一张拆分卡，按 executor-mode.md 执行，不出现测试/实现/同步/全量子代理；交卡一条消息含 §4.1 第 6 步全部字段。
- 完成门（§4.6）：Commit T 之后改测试 → `task set --status` 退出码 1；Commit T 不是代码提交祖先 → 退出码 1；压缩合并后登记 → 退出码 1；`move` 卡胶水含 `if` 或字面量改动 → 拒绝「已完成」、改 `guarded` 后可进 review_pending；sha 解析不到 → 退出码 1；以上每种情况文件不变。
- `move-check`：纯搬（含缩进变化）胶水为 0 或只有签名/调用；夹带一处条件改动时胶水清单列出该行；重命名文件、跨文件搬移都算搬动。
- `move` 枚举：`task set --profile move` 通过 K5；未知值仍拒绝。
- 表征测试卡：Commit T 全绿不被判无效。
- 批量 Commit 2：3 张卡一批只有 1 次台账提交，每张卡 commits 字段齐全；主会话批量与执行者模式各走查一次。
- 主会话 `move` 卡：仍由子代理搬，Commit 1 后直接已完成，不进 review_pending。
- drain 送审 diff 含 Commit T 的测试改动。
- 测试、ruff、mypy --strict、Python 3.9 自测全过；SKILL.md ≤500 行；`git diff --check` 干净。
- 版本升到 3.1.0（与并行稿谁先落地谁占 3.1.0，后者顺延 3.2.0）。

## 6. 风险与留给施工者的

- **升级顺序**：用了 `move` 的项目，所有会话的 keel 都要 ≥3.1.0，否则旧版 K5 拒绝。发布说明写明。
- **move-check 的多重集合抵消**会把「删一行、别处加一行同样内容」算搬动，即便语义位置变了（如挪进另一个分支）。判定规则要求胶水清单人工过目、表征测试全绿兜底；如误判多，再考虑按块匹配。
- **注错怎么注**由施工者按语言选最简单方式（改一个比较符或返回值），只要求可还原、有记录。
- 执行者模式识别依赖 brief 措辞，施工者在 executor-mode.md 给出判定依据和反例（用户在主会话里说「做 T-xxx」不是执行者模式）。
