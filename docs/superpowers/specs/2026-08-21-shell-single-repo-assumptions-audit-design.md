# shell 模式单仓假设审计 + workspace 声明 cutover

> 状态：**第 1 稿 · 待立项** · 日期：2026-08-21
> **配对 spec**：[抽取 workspace-topology（add-only 批）](2026-08-21-workspace-topology-skill-design.md) —— 本稿是它 cutover 的前置条件
> 来源：该 spec 的 codex 审查 R2 F-108 / R3 F-204 / R4 F-302 / R4 F-304，以及审查过程中的自查发现

## 0. 为什么独立立项

`workspace-mode.v1`（2026-08-05 落地）引入了 shell 模式，但**没有系统盘点「哪些既有算法内嵌了单仓假设」**。这些缺陷今天就在仓里，只因本仓与多数项目跑 inline，`scan_targets` 恰好等于 `[.]`，所以从未暴露。

抽取 `workspace-topology` 的设计过程连续四轮 codex 审查，每轮都在这个方向上发现新条目：

| 轮次 | 发现 | 结果 |
|---|---|---|
| R2 F-108 | 举出 3 处（`codebase-insight` 缓存键 / `test-run --affected` / E2E 影响分析） | 写进那份 spec 的 §6.3 |
| R3 F-204 | 判「明显不完整」，补出 `ms-sync` 委托链、`dev-workflow` S8、`dev-flow` Evidence Check、`onboard`、`verify schema-drift` | §6.3 从 3 涨到 12 |
| R4 F-302 | 仍漏 diff 消费者一整类（含 `adversarial-review` 独立调用） | — |
| R4 F-304 | 补出**全新类别**「仓库归属与仓内操作」（`git ls-files` / `git mv` / `commit-convention` 读历史风格） | — |

R4 的熔断根因（codex 原话）：**「仍以命令关键词代替『操作语义 × 消费方』的完整盘点」**。

**结论**：这不是一份能在别人的 spec 里顺手补完的清单。它需要自己的盘点方法、自己的完成判据、自己的立项。

## 1. 本稿要做两件事

| 阶段 | 内容 | 完成判据 |
|---|---|---|
| **P1 审计** | 用「操作语义 × 消费方」矩阵盘点全部单仓假设，产出权威清单 | 矩阵每格有判定 + 证据，无空格 |
| **P2 迁移 + cutover** | 修 P1 清单；完成后原子切换声明位置与 `no-bypass` 等级 | 配对 spec §1 的 add-only 硬约束全部解除 |

⛔ **P1 必须先完成**。R4 F-307：cutover 与算法迁移**不可分两批发布**——若先切换声明并把 `no-bypass` 升 ⛔，未迁移的旧算法会从「耦合但尚能工作」退化成**没有合法输入**。

## 2. P1：盘点方法

### 2.1 为什么不用 grep 关键词

前四轮用的是关键词法（`git rev-parse HEAD` / `git diff --name-only` / `git status --porcelain` / `git log --grep` / `merge-base` / 「扫描代码」），连续两轮漏掉整个类别。原因：

- **同一操作语义有多种表达**：「取 diff」可以写成 `git diff`、`uncommitted: true`、「对比上次提交」、「变更范围识别」、「工作区改动即本任务改动」
- **有些假设不含任何命令**：`task-orchestration.md:410` 的「禁止读取任何 `src/` 下的实现文件」硬编码路径前缀，无 git 命令
- **有些假设藏在委托链里**：`verify` B3 复用 `ms-sync`，改 `verify` 的入口句修不了 `ms-sync` 的扫描

### 2.2 矩阵定义

**行 = 操作语义**（七类，按「与仓库拓扑的耦合方式」划分，不按命令）：

| # | 操作语义 | 在 shell 下的正确形态 |
|---|---|---|
| O1 | 读代码内容（扫描、盘点、标注提取） | 逐 `scan_target` 执行，结果以 label 限定 |
| O2 | 取 diff（工作区 / staged / 指定 commit / merge-base 区间） | 逐 `scan_target` 取并以 label 分隔；外壳仓侧排除 gitlink 条目 |
| O3 | 读 revision / 判新鲜度（缓存键、freshness、schema-drift） | per-target revision map，非单个 HEAD |
| O4 | 判某路径属哪个仓 | 按 `scan_targets` **最长前缀**定 owner |
| O5 | 在仓内执行 git 写操作（`mv` / `rm` / `add`） | 先定 owner，再 `git -C <owner>` |
| O6 | 读工作区状态（洁净门、变更列表） | 遍历 N+1 仓；外壳仓侧排除 gitlink |
| O7 | 读提交历史（编号检索、风格沿用） | 按用途分：编号检索查外壳仓；风格沿用查各代码仓自身 |

**列 = 消费方**：全部 39 个 skill（`skills/*/SKILL.md` 的 `name` 字段）。

**每格判定**：`适用且已正确` / `适用但错误`（→ 进清单）/ `不适用`。⛔ 不得留空格；`不适用` 也要写一句理由。

### 2.3 委托链展开规则

判定某消费方时，若它把操作**委托**给另一个 skill，必须同时判定被委托方。已知的委托链：

- `verify` B3 → `ms-sync`（trace 扫描）
- `dev-workflow` S10 → `code-self-describe`
- `dev-workflow` S9 Phase 4 → `adversarial-review`（embedded-headless）
- `pipeline` / `feature` / `bugfix` → 各原子 skill
- 各 skill 的提交步骤 → `commit-convention` / `git-safety`

**只改上游入口句修不了下游算法**（R3 F-204 对 `verify`/`ms-sync` 的原始判据）。

## 3. P1 已知条目（**起点，非清单**）

⚠️ 以下是四轮审查已识别的条目，按 §2.2 的操作语义分类。**它不是完整清单**——完整清单是 P1 的交付物。列在这里是为了让 P1 有起点、且不丢已付出的审查成本。

### O1 读代码内容

| 位置 | 缺陷 |
|---|---|
| `sync/SKILL.md:96` | 「扫描代码库（工作区状态）」单仓 |
| `sync/SKILL.md:126` + `sync/references/trace-mode.md:5, 14` | trace 扫 `@satisfies`/`@verifies` 标注单仓；**`verify` B3 复用之** |
| `test-run/SKILL.md:111` | 扫 `@verifies`/`@testcase` 标注 |
| `test-cases/SKILL.md:262` | 扫描代码标注 |
| `dev-flow/SKILL.md:29` | 「必要时扫描代码补足上下文」 |
| `onboard/SKILL.md` `--update` | 从仓根采集目录结构、`git status`、`git log`、运行命令 |

### O2 取 diff

| 位置 | 缺陷 |
|---|---|
| `dev-workflow/references/verification-flow.md:344` | **audit 档 inline 外审**用「工作区 diff（`uncommitted: true`）」，理由写着「此时工作区改动即本任务改动」。shell 下外壳仓工作区 diff **只有一行 gitlink** → Phase 4 等同空审。**与 2026-08-06 修掉的 drain 空 diff 是同一类缺陷的未修分支**（那次只修 drain 侧） |
| `dev-workflow/references/verification-flow.md:349–355` | drain 侧「逐 `code_root` 定位并拼接」未说明如何从追溯枢纽解析**不带 T-XX** 的子模块 commit（R4 F-303） |
| `adversarial-review/references/external-reviewer-integration.md:202` | 独立调用默认 `uncommitted: true`，shell 下只见 gitlink |
| `dev-workflow/references/execution-flow.md` S8 | AC 完备性以仓根 diff 为据，「声称 vs 实际」核对失效 |
| `dev-flow/SKILL.md:56, 64–71` | Gate 3 Evidence Check 以仓根 diff 为质量地板 |
| `test-run/SKILL.md:82–83` | `--affected` 单次仓根 `merge-base` + `git diff --name-only` |
| `e2e-test-flow/references/impact-analysis.md` | 影响分析 diff 基线单仓 |
| `code-self-describe/SKILL.md:182` + `templates/update-rules.md:60, 63` | 单仓 diff 基线；`--force-code-docs --update` 会算错，`--audit` 只读也需逐 target |

### O3 读 revision / 判新鲜度

| 位置 | 缺陷 |
|---|---|
| `codebase-insight/SKILL.md:55` | 缓存键 `commit_hash != git rev-parse HEAD`。shell 下那是外壳仓 HEAD，只随指针 bump 变 → 子模块有代码变更但未 bump 时**误命中缓存** |
| `verify/templates/verify-report.md:13` | `verified_commit`「供 pipeline 判断 freshness」，同上 |
| `verify/references/schema-drift.md:23` | 拿 `codebase-insight` 的 `commit_hash` 与 git HEAD 比 |

**O3 的修法须成套**：`codebase-insight` 改存按 `scan_targets` 排序的 `target_revisions` map（**单一 schema，不给「map 或聚合指纹」二选一**），并同步 frontmatter 字段、摘要契约、`schema-drift.md:23` 判据、该 skill 的 `spec_version` bump。

### O4 / O5 仓库归属与仓内 git 写操作

| 位置 | 缺陷 |
|---|---|
| `git-safety/SKILL.md:25–37` | `git mv` / `git rm` 从外壳仓执行会把子模块内受控文件误判未跟踪或直接失败 |
| `dev-flow/SKILL.md:133–136` | 「文件移动/删除遵循 `/git-safety`」，继承上条 |
| 各处 `git ls-files` 用法 | 同上 |

### O6 读工作区状态

| 位置 | 缺陷 |
|---|---|
| `dev-workflow/references/auto-mode.md:38, 120, 156, 157` | `--headless` 无人值守洁净门用仓根 `git status --porcelain` 判空。shell 下**外壳仓干净而子模块脏时误判通过**。无人值守场景下最危险的一处 |
| `dev-workflow/references/task-orchestration.md:237` | 「`git status --porcelain` 非空 → 报错」同上 |

### O7 读提交历史

| 位置 | 缺陷 |
|---|---|
| `commit-convention/SKILL.md:16, 54` | 「优先沿用项目已有提交历史风格」会读**外壳仓**历史，而 `workspace-mode.v1` §6.3 要求子模块提交沿用**该仓自身**风格 —— 规范与实现直接相反 |

### 其他（不属七类操作语义，但同源）

| 位置 | 缺陷 |
|---|---|
| `dev-workflow/references/task-orchestration.md:410` | 信息屏障硬编码 `src/`：「Test Agent 禁止读取任何 `src/` 下的已有实现文件」。shell 下代码在 `web/src/`，禁令按字面**不覆盖** → **信息屏障失效**。这不是路径问题，是隔离失效 |
| `_shared/workspace-mode.md:73–90` §5 | 零污染违约检测要求判定「非源码/测试路径」，同文又禁「静态白名单猜测什么算源码」。与配对 spec §4.3 裁掉的 §4 矛盾同构，裁法应一致（列清单交用户判断，不预判类别） |

**已知条目计数**：O1×6 + O2×8 + O3×3 + O4/O5×3 + O6×2 + O7×1 + 其他×2 = **25 个逻辑条目**。

> ℹ️ 配对 spec 的第 3、4 稿曾写「12 处」「14 个逻辑条目」，均为当轮已知数。数字每轮都涨，这本身就是「关键词法不收敛」的证据，也是本稿改用矩阵法的直接理由。

## 4. P2：迁移 + cutover

### 4.1 算法迁移

按 P1 清单逐条修，修法遵 §2.2 的「在 shell 下的正确形态」列。

### 4.2 cutover（原子，⛔ 不可与 P1 分批发布）

解除配对 spec §1 列的全部 add-only 约束：

| 项 | 动作 |
|---|---|
| legacy 声明位置 | `devdocs.workspace_mode` / `code_roots` 读取路径移除；`declaration_site: legacy` 从 ℹ️ 升 ⚠️ 再移除 |
| `workspace/no-bypass` | ℹ️ 建议 → ⛔ 强制 |
| `_shared/workspace-mode.md` | 瘦身（声明 schema / 校验表 / 归属判定移出，已在 skill 里）；§5 零污染检测按 §3「其他」表裁决 |
| `agent-memory/SKILL.md` | 受管白名单摘掉 `workspace_mode` / `code_roots`，`devdocs_frontmatter` 入参收缩到只剩 `initialized_at` |
| `layout/layout-metadata-schema.md` | 摘掉 workspace 两字段 |
| `verification-flow.md:344, 354` | `workspace_mode: shell` 分支改用 `scan_targets`（R4 F-303） |

### 4.3 P2 的 spec_version bump

`workspace-mode.v1` → `v2`（瘦身 + schema 移出）、`agent-memory`、`layout-metadata-schema`、`codebase-insight`（`target_revisions` schema）、`shared-constraints`（`no-bypass` 升级）。

## 5. 触发条件

本稿**不主张立即开工**。理由：本仓与多数项目跑 inline，这 25 处在 inline 上恰好不出错。

| 触发 | 说明 |
|---|---|
| 真有 shell 项目进入日常开发 | 最强触发。`chiaki-ng-dev` 是已知的 shell 形状项目 |
| 配对 spec 落地后想解除 add-only | cutover 的前置条件就是 P1 |
| 单独提前修的高危项 | O6 的 `--headless` 洁净门误判、「其他」表的信息屏障失效、O2 的 audit 空审 —— 这三处是**安全性/正确性**缺陷而非便利性缺陷，可不等 P1 全量完成就单独修 |

## 6. 明确不做

| 不做 | 理由 |
|---|---|
| 在配对 spec 里顺手补完清单 | §0；四轮审查证明关键词法不收敛 |
| 用 grep 关键词作为 P1 的完成判据 | §2.1 |
| P1 未完成就做 cutover | R4 F-307；旧算法会失去合法输入 |
| 把「引用者 allowlist」做成通用 health-lint rule | R4 F-306：那是面向普通 DevDocs 项目的机制；本仓专用检查用可复制 `rg` 命令即可 |
| 为 shell 模式建独立的跨仓事务执行器 | 配对 spec §5；R2 熔断结论，与本稿的算法迁移无关 |

## 7. 待审查者重点质疑

1. **§2.2 的七类操作语义是否穷尽** —— 划分依据是「与仓库拓扑的耦合方式」。是否存在第八类，或某两类应合并？特别是 O4（判归属）与 O5（仓内写操作）是否该合并。
2. **§2.2 的矩阵规模是否可执行** —— 7 × 39 = 273 格，每格要判定 + 留证。这个规模在本仓的实际投入下现实吗？还是需要先按「是否碰 git / 是否读代码」做一轮粗筛把列砍掉大半？
3. **§5 的「高危三项可提前单独修」是否安全** —— 它们分别属 O6 / 其他 / O2 三类。单独修会不会与 P1 的统一修法冲突，造成返工。
4. **`commit-convention` 那条（O7）是规范矛盾还是实现缺陷** —— `workspace-mode.v1` §6.3 要求子模块沿用自身风格，而 `commit-convention` 会读外壳仓历史。是改 `commit-convention` 让它接受 owner repo 参数，还是改 `workspace-mode.v1` 的要求？
