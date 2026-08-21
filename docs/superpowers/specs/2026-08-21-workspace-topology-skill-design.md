# 抽取 workspace-topology：仓库拓扑从 DevDocs 解耦为独立 skill

> 状态：**第 3 稿 · R2 熔断后塌缩 · 待 R3** · 日期：2026-08-21
> 审查轨迹：R1 `health_score=39.5`（7 条全确认并修正）→ R2 `70.75`（**上升 79%**，5 条复现 + 3 条自引入）→ 🔴 熔断复盘 → 用户决策「塌缩：提交侧不做接口」→ 本稿
> 前置：`workspace-mode.v1`（[2026-08-05 设计](2026-08-05-devdocs-shell-workspace-mode-design.md)）已落地并在 `chiaki-ng-dev` 实测过
> 本稿**退休** `workspace-mode.v1` 的文件布局与声明位置，协议内核（inline/shell 语义、`.gitmodules` 真源、零污染红线、N+1 提交）保留

## 0. 问题

`workspace_mode` 维度落地三个月后，两处结构性缺陷在使用中暴露。

### 0.1 写者只在 DevDocs，读者却有非 DevDocs 的

字段声明在 `AGENTS.md` 的 **`devdocs:`** frontmatter 块内，探测入口只有三个，全属 DevDocs：`ms-pipeline init`、`ms-retrofit`、`realign --scope=layout`。而消费方里有三个明确声明「与 DevDocs 独立」的：

| 消费方 | 位置 | 原文自述 |
|---|---|---|
| `dev-flow` | `SKILL.md:133` | 非 DevDocs 通用执行器 |
| `e2e-test-flow` | `SKILL.md:48` | 「本 skill 与 DevDocs 独立，仅借该字段定位源码」 |
| `code-self-describe` | `SKILL.md:87` | 独立 skill |

后果双向：

- **难触发**：外壳形状但不跑 DevDocs 的项目，没有任何合法途径声明自己是 shell
- **误触发**：想声明就得跑 `init` / `retrofit`，顺带拉起需求编码、`docs/devdocs/` 脚手架、`agent-memory` 更新

### 0.2 「仓库设定」会造一个新名字的外层目录

`workspace-shell.md` 的 inline→shell 迁移：Step 2 算 `W="${W:-$(dirname "$R")/${R_NAME}-dev"}`，Step 3 `mkdir -p "$W" && git init`，Step 4 从 remote URL **独立 clone** 一份 R 作子模块。结果是同一个仓在磁盘上有两份工作副本，用户此后工作的根目录变成 `<原名>-dev`。

这超出「声明一个仓库设定」该有的动作幅度——它是一次仓库手术，被挂在了规范维度下面。**判定：过度设计，删除。** skill 只管当前文件夹内部。

### 0.3 第三处缺陷（清点时发现）

`_shared/workspace-mode.md` §4 与 §5 互相矛盾：

- §4：「落在仓库根、不属任何 `code_roots` 且不在 `docs/` 里的**源码文件** → ⚠️」
- §5：「**不做静态白名单猜测「什么算源码」** —— 上游仓目录约定各异，猜会误伤」

两条不能同时成立。裁决见 §4.3。

## 1. 决策摘要

| # | 决策 | 依据 |
|---|------|------|
| a | 抽取独立 skill `workspace-topology`（非 `ms-` 前缀） | 0.1；仓库拓扑是仓库级事实，不是 DevDocs 事实 |
| b | 声明移到与 `devdocs:` 平级的独立 `workspace:` 块 | 0.1 的病根一半在「字段住在 `devdocs:` 里」 |
| c | 协议正文搬进 skill，`_shared/workspace-mode.md` 删除 | §4.1「依赖接口而非实现」的连带后果 |
| d | 消费方一律委托入口，⛔ 不得自读声明文件 | 新增 `workspace/no-bypass` 禁令 |
| e | **提交侧不做接口**：N+1 提交协议留 `_shared/workspace-mode.md`，skill 只管声明与拓扑查询 | R2 熔断（§2.5）；封装跨仓提交需要一个分布式事务协议，与本仓复杂度预算不成比例 |
| f | 删除 inline→shell 迁移手术（七步、约 170 行） | 0.2 |
| g | docs 根恒为 `<仓库根>/docs/`，不设字段、不可配置 | 310 处 `docs/devdocs` 硬编码的正确性建立在这条常量上 |
| h | 可重入四动作，幂等 | 用户需求：后期改 mode、加子模块 |
| i | 消费方的**单仓算法**需随迁移一并修 | codex R2 F-108；`codebase-insight` 缓存键、`test-run --affected`、E2E 影响分析今天都只跑一次仓根 |

## 2. 接口契约

### 2.1 「依赖接口，而不是实现」

本稿的核心约束。第 1 稿曾把 10 处消费方指向 `_shared/workspace-mode.md` 的**具体章节**（§ N+1 仓提交协议、§ 校验规则、§7.2 gitlink 判据），被否决：协议一改，10 处跟着改，接口等于没抽。

**修正后**：委托方不知道字段叫 `workspace.mode`、不知道真源是 `.gitmodules`、不知道任何章节号，只知道调入口拿答案。

这条原则有一个可执行形式，写进 `_shared/constraints.md §10`（收窄后的最终形态见 §4.2）：

- `workspace/no-bypass`：**⛔ 不得自行读取声明文件或解析 `.gitmodules`** —— 拿代码根路径 / docs 根 / 工作区快照必须走 `--check`。

> ⚠️ **原则的适用边界（R2 熔断后确立）**：这条原则对**查询**成立，对**跨仓提交编排**不成立。把提交侧也接口化需要一个分布式事务协议，代价与收益不成比例，账见 §2.5。因此提交协议、零污染、gitlink 排除三面仍以规范条文形式留在 `_shared/workspace-mode.md`，消费方引用其条文是合法的。切分判据见 §4.1。

没有这条禁令，下一个 skill 又会去 grep `AGENTS.md`。

### 2.2 入口：一个交互式 + 一个只读查询

| 入口 | 回答的问题 |
|---|---|
| `/workspace-topology` | （交互式维护声明，见 §5） |
| `--check` | 代码扫哪、docs 在哪、本 skill 该开还是该关、工作区什么状态、指针是否一致 |

**声明失配前置**：§3.3 的 ⛔ 行前置阻塞——拿不到可信拓扑，后面的答案都无意义。

**第 2 稿的 `--plan-commits` / `--check --id` 已删除**。理由见 §2.5。

### 2.3 摘要信封

作为子 Agent 被委托，返回 `yaml-summary-v1`（`constraints.md §2`），`skill: workspace-topology`。私有字段按 `yaml-summary/details-only-private` 一律落 `summary.details`。

### 2.4 `--check`：输出能力与事实，不输出模式

第 1 稿直接返回 `mode: inline|shell`，被判**语义泄漏**（codex R1 F-002）：`code-self-describe` 要靠它决定跳不跳、`verify` 要靠它决定扫哪，调用方必然写 `if mode == shell`。`workspace/no-bypass` 只禁止读声明文件，没禁住这种分支。

```yaml
summary:
  details:
    docs_root: docs
    scan_targets:                       # 代码扫描 / 测试执行 / 洞察盘点 / diff 基线的目标
      - {label: web, path: web}
      - {label: api, path: api}         # inline 时为单项 {label: ".", path: "."}
    capabilities:
      code_dir_write_policy: source_and_tests_only   # unrestricted | source_and_tests_only
    pointer_checks:                     # health-lint 的 submodule/pointer-drift 直接消费
      - {label: web, recorded: e4f5g6h, actual: e4f5g6h, state: consistent}
      - {label: api, recorded: a1b2c3d, actual: f7a8b9c, state: drift_ahead}
    root_residue: []                    # 仓根下不在 docs/、不属任何 scan_target 的已跟踪文件（ℹ️，§4.3）
    undeclared_submodules: []           # .gitmodules 有条目但未进声明 → ℹ️
    snapshot_id: ws-7f2548c-1           # 见要点 3
    worktree_changes:                   # 按仓分组，gitlink 条目已在出口前滤掉
      - {label: web, path: web, changes: [src/a.ts]}
      - {label: ".", path: ".", changes: [docs/devdocs/00-context.md]}
    mode: shell                         # ⚠️ 仅供人读；机器消费者不得以此分支
```

五条契约要点：

1. **`mode` 仅供人读**。留它是为了让人看报告时知道自己在哪种拓扑下，任何 skill 以 `mode` 做分支即违反 `workspace/no-bypass`。§9 的验证项因此不能只 grep `.gitmodules`，必须同时人工判读 mode-derived 分支。

2. **`capabilities` 只有一项，且是泛化后的**。第 2 稿的 `code_docs_policy: allow|skip_by_default` 表达不了 `codebase-insight:158` 的「不往任何子模块写文件」——inline 时 `scan_targets = [{".", "."}]`，而 `docs/` 就在 `.` 里面，「不往 scan_target 写非代码文件」会**禁掉 inline 下写 `docs/`**，零污染红线在 inline 退化时自相矛盾。改为 `code_dir_write_policy: unrestricted | source_and_tests_only`（inline 前者、shell 后者），`code-self-describe` 的跳过决策由它派生。
   其余三个消费方核过无需新 capability：`test-run` 的「按 root 分组」与 `codebase-insight` 的「仓间关系小节」都能由 `len(scan_targets) > 1` 派生——**而且比今天按 `mode` 判更准**（shell 单代码根时今天会错误地要求产出仓间关系小节）。

3. **`worktree_changes` 与 `snapshot_id`：明确调用两次，归属判定归调用方**（codex R2 F-107）。任务开始时与提交前是两个时点，必须各取一次快照——`snapshot_id` 让调用方能断言新鲜度。两处的归属基准不同：任务开始时按任务的「涉及文件」字段判，提交前按实际变更路径判。**「变更是否属于当前任务」与「用户选了忽略继续」这两件事都归调用方持久化**，topology 不记忆决定。gitlink 条目在出口前已滤掉，覆盖 `task-orchestration.md` Step 3–5（codex R1 F-007）。

4. **`pointer_checks` 让 health 不必读 `mode`**（codex R2 F-106）。第 2 稿自己还写着 health-lint「委托 `--check` 拿 `mode`」，直接违反自己定的规则。现在 health-lint 的 `submodule/pointer-drift` 直接消费 `pointer_checks`，`state` 枚举 = `consistent` | `drift_ahead`（子模块较新，漏 bump）| `drift_behind`（未 update）| `diverged`（互不包含）| `not_applicable`（inline）。三种漂移成因的处置命令在 `probe-and-repair.md`。

5. **`root_residue` / `undeclared_submodules` 是 ℹ️ 级事实**，不阻塞。后者补住 `realign-scope-layout.md:83` 的「未声明工作区模式」提示——改成委托后若不返这个字段，该提示会静默失效。

### 2.5 提交侧不做接口（R2 熔断结论）

第 2 稿有 `--plan-commits`（逻辑单元 → 物理步骤 + `{{steps[N].sha}}` 占位）与 `--check --id`（提交证据 + `review_diff_sources`）两个入口。**两节整体删除。**

**熔断数据**：R1 `health_score=39.5`（P1×4 / P2×2 / partial×1），R2 `health_score=70.75`（P1×4 / P2×3 / partial×1），**上升 79%**，其中 5 条是 R1 未闭合的复现、3 条是修正自身引入的新问题。8 条发现里 7 条源自这两节。

**根因（一条）**：把「提交编排」当成了可以封装的服务。跨仓提交本质是**有状态的分布式事务**——严格顺序、部分失败、SHA 依赖、恢复点。任何想用一次只读调用封住它的设计都会被迫长出事务管理器。codex R2 的三条修法（持久 execution receipt + 结构化 message 对象 + gitlink tree transition 作 diff SSOT）加起来正是一个跨仓事务协议。

对一个纯 Markdown 规格库、为了服务少数 shell 模式项目，这个复杂度与要解的问题不成比例。本仓有同型先例：`markdown-style` 的自动修复白名单 27→9→4→0 整体放弃。

**塌缩后的分工**：

| 面 | 归属 | 消费方 |
|---|---|---|
| 声明维护、拓扑事实、指针状态 | `workspace-topology` | verify / test-run / codebase-insight / e2e-test-flow / health-lint / realign / pipeline / retrofit |
| N+1 提交协议、零污染红线、gitlink 排除 | `_shared/workspace-mode.md`（保留） | dev-workflow / bugfix / dev-flow / code-self-describe |

**这是对「依赖接口而非实现」的局部让步，账要记明**：封住提交侧的代价是一个跨仓事务协议，受益者只有 shell 模式；不封的代价是 3 处消费方在提交这一面仍引用规范文件条文。用户在 R2 熔断决策时选择了后者。

codex R1 F-007 的原文本就给了这个选项：「或者保留当前调用方逻辑并**承认接口没有封装这部分**」。


## 3. 声明 schema 与写者归属

```yaml
---
workspace:                     # 与 devdocs: 平级的独立块
  mode: shell                  # 可选，枚举 inline|shell，缺省 inline
  code_roots: [web, api]       # mode=shell 时必填，≥1 项，元素为 .gitmodules 的 submodule name
devdocs:                       # DevDocs 项目才有；非 DevDocs 项目只有 workspace: 块
  docs_layout_version: layout.v1
  id_scheme: id.v1
  traceability_version: trace.v0
  initialized_at: "2026-08-05"
---
```

### 3.1 docs 根是常量而非字段

- `workspace/docs-root`：文档根**恒为** `<仓库根>/docs/`，两种模式无差别，**不设字段、不可配置**。

理由：可配置就会漂，而仓内 **310 处**（2026-08-21 实测 `grep -ro "docs/devdocs" skills/ | wc -l`）`docs/devdocs` 硬编码引用的正确性正建立在这条常量上。`--check` 仍在 `details.docs_root` 里回答它——调用方拿常量，不是「不用问」。

### 3.2 写者归属：skill 自己写，不经 agent-memory

今天的写入链是「pipeline 探测 → 结果塞进 `devdocs_frontmatter` 入参 → `agent-memory --update` 代写」，两个 skill 才能落一个字段，因为 pipeline 不许写 `AGENTS.md`。

改为 **`workspace-topology` 直接写 `workspace:` 块**，并从 `agent-memory` 的受管字段白名单里摘掉 `workspace_mode` / `code_roots`（`initialized_at` 留给它）。

| 收益 | 说明 |
|---|---|
| 少一层委托、少一个入参契约 | `pipeline` / `retrofit` 退化成一句 `Task: /workspace-topology` |
| 归属无重叠 | `agent-memory` 拥有正文 + `devdocs:` 块，`workspace-topology` 拥有 `workspace:` 块 |

两个写者共存 `AGENTS.md` 的安全性由**块级不相交**保证，比今天两个 skill 抢同一批字段更安全。

### 3.3 校验（fail-closed）

沿用 `workspace-mode.v1` §3 全表，仅字段路径改名：

| 情形 | 行为 |
|---|---|
| 无 `workspace:` 块 / 无 `mode` 字段 | 视为 `inline`——存量项目零影响 |
| `shell` 但 `code_roots` 缺失 / 为空 | ⛔ |
| 某 name 不在 `.gitmodules` | ⛔，提示修声明 |
| name 在 `.gitmodules` 但工作区目录为空 | ⛔（运行时校验门）；health 只读扫描降级 ⚠️ |
| 解析出的两个 path 互为前缀（嵌套子模块） | ⛔ |
| 某 path 为 `.` / 含 `..` / 等于 `docs` | ⛔ |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略 |

## 4. 文件布局

### 4.1 混合归属（R2 塌缩后）

第 1 稿定方案 A（协议全留 `_shared`），第 2 稿按「依赖接口」推成方案 B（协议全进 skill）。R2 熔断后落在**按面切分**：

```
skills/_shared/workspace-mode.md          保留并瘦身（跨 skill 行为约束）
  ├ 零污染写入范围
  ├ N+1 仓提交协议（严格顺序 / detached HEAD 门 / message 契约与追溯枢纽
  │                 / --single-commit 不可用 / 跨仓 Recovery 三类）
  └ gitlink 排除（工作区洁净检查）
  ⚠️ 本文不再复制声明 schema 与路径解析——需要代码根路径时委托 `--check`

skills/workspace-topology/
  SKILL.md                          定位 / 两入口 / 四动作 / 声明 schema / 校验表
  references/probe-and-repair.md    探测步骤 / 指针漂移三成因与处置
```

**删除**：`skills/pipeline/references/layout/workspace-shell.md`（252 行）。存活内容分流——探测步骤与指针漂移修复进 `probe-and-repair.md`（约 50 行），detached HEAD 处置随它的门一起并入 `_shared/workspace-mode.md`（约 20 行），净删约 180 行。

它住在 `pipeline/references/layout/` 下本身就是 §0.1 的病灶之一——DevDocs 命名空间承载仓库级操作手册。

切分判据：**一件事若有 ≥2 个 skill 需要按它的条文行动（而非只需要一个答案），它是跨 skill 行为约束，留 `_shared`；若消费方只需要一个答案，它是查询，进 skill。**

### 4.2 `_shared/constraints.md §10`

```
- workspace/single-entry：拓扑事实（代码根路径 / docs 根 / 能力 / 指针状态 /
  工作区快照）唯一入口 /workspace-topology --check
- workspace/default-inline：缺省 inline；无声明的项目行为完全不变
- workspace/no-bypass：⛔ 不得自行读取声明文件或解析 .gitmodules——拿路径必须走
  --check。提交协议 / 零污染 / gitlink 排除等行为约束仍由 workspace-mode.md 承载，
  引用其条文是合法的：本条只禁「自己读声明」，不禁「引用行为约束」。
```

第 2 稿的 `no-bypass` 是无限定的「一律委托入口」，R2 熔断后收窄为上述形态。原 §10 的 `workspace/mode-enum`（含字段路径）、`workspace/code-roots-source`（含 `.gitmodules` 真源）、`workspace/orthogonal-to-layout`、`workspace/pointer` 四条下沉进 skill——它们描述声明的实现，不该留在跨 skill 准则层。

`workspace/no-pollution`、`workspace/commit-protocol`、`workspace/recovery`、`workspace/gitlink-exclusion`、`workspace/no-stash-gitlink`、`workspace/no-nested-submodules` 留在 `workspace-mode.md`。其中 `no-stash-gitlink` 保留为对外规则——第 2 稿曾说它「在接口层自然消失」，那个论断依赖 `worktree_changes` 出口过滤，而提交侧塌缩后 dev-workflow 仍会直接看到外壳仓 porcelain 输出（codex R2 F-107 指出的生命周期缺口的另一面）。

### 4.3 §4 / §5 矛盾的裁决

原 `workspace-mode.md` §4 与 §5 互相矛盾：§4 要「仓根下的**源码文件** → ⚠️」，§5 明确拒绝「静态白名单猜测什么算源码」。裁掉「源码文件」判定：

- `workspace/root-residue`（住 skill）：`shell` 模式下，仓库根下不在 `docs/`、不属任何 `scan_target` 的**已跟踪文件** → ℹ️ 列清单，由用户判断。**不猜是不是源码，也不装作能猜。**

保留提示的价值（外壳仓不该有代码是真实约束），删掉它无法兑现的精确性。降 ⚠️→ℹ️ 是因为无法判定性质就不该要求确认。


## 5. 可重入四动作

**幂等判据**：读现状 → 若用户选「保持不变」，或调整后 frontmatter 与现状**逐字节相等** → 零文件写入，`details.changed: false`。

| 动作 | 语义 |
|---|---|
| 首次声明 / 重新探测 | 扫 `.gitmodules` → AskUserQuestion 多选代码根（提示语必须说明「子模块也可能是素材 / vendor，不都算代码根」）→ 全不选 = `inline`。无 `.gitmodules` 时静默判 `inline`，不打扰用户 |
| 切 mode（双向） | **声明跟随事实，不制造事实**。`inline→shell` 要求子模块已挂好；`shell→inline` 只删 `code_roots` 声明，子模块文件与 `.gitmodules` 一律不动 |
| 新增子模块 | `git submodule add <url> <path>` + 追加 `code_roots`。属「管文件夹内部」，不越界。也支持「子模块已存在、只补声明」 |
| 移除代码根 | **仅退声明**，绝不 `git submodule deinit` / `git rm`——破坏性动作交用户 |

**写入后自校验**：立即跑 §3.3 全表，任一 ⛔ → 回滚本次写入并报告（沿用 `workspace-mode.v1` 探测第 6 步）。

**不自动提交**：只改工作区文件，`output_files` 列出改动 + `details.suggested_commit_message`。独立 skill 不自造 commit；DevDocs 链里由 pipeline 既有提交步骤覆盖。

## 6. 影响面

塌缩后消费方分**两类**，改动方式不同。

### 6.1 路径类消费方（改委托 `--check`）

替换文本统一为：

> 代码根路径、docs 根与工作区快照委托 `/workspace-topology --check`，本 skill 不读取声明文件、不解析 `.gitmodules`（`workspace/no-bypass`）。

| 文件 | 行 | 处置 |
|---|---|---|
| `verify/SKILL.md` | 136 | 换委托句，消费 `scan_targets` + `root_residue`；⚠️→ℹ️（§4.3） |
| `test-run/SKILL.md` | 72 | 换委托句，消费 `scan_targets`；「按 root 分组」改由 `len(scan_targets) > 1` 派生 |
| `codebase-insight/SKILL.md` | 152, 154 | 换委托句；「仓间关系小节」同样改由 `len > 1` 派生 |
| `e2e-test-flow/SKILL.md` | 48 | 换委托句，消费 `scan_targets` |
| `code-self-describe/SKILL.md` | 87, 89, 93 | 跳过决策改读 `capabilities.code_dir_write_policy`，不读 `mode` |

### 6.2 提交类消费方（继续引用 `_shared`，仅修指针目标）

这三处**不换委托句**——它们需要按条文行动，不是要一个答案（§4.1 切分判据）。改动仅限：`workspace_mode` → 委托 `--check` 拿路径，其余条文引用保持。

| 文件 | 行 | 处置 |
|---|---|---|
| `dev-flow/SKILL.md` | 133 | 保留指向 `_shared` § N+1 的引用；路径解析改委托 |
| `bugfix/SKILL.md` | 288 | 同上 |
| `dev-workflow/SKILL.md` | 113, 300, 301, 313 | 113 改读 `capabilities`；300/313 的**复述**删除、改为指向 `_shared` 条文；301 的 detached HEAD 指针改指 `_shared`（处置手册已并入该文，§4.1） |
| `dev-workflow/references/task-orchestration.md` | 136, 145 | 复述删除、改指 `_shared`；工作区遍历改消费 `--check` 的 `worktree_changes` + `snapshot_id`（§2.4 要点 3） |
| `dev-workflow/references/verification-flow.md` | 354 | **不动**——drain 侧逐 `code_root` 拼接仍按 `_shared` 提交协议执行。第 2 稿曾改它，R2 F-106 证明那个改法会让空 diff 缺陷复活 |

### 6.3 单仓算法迁移（codex R2 F-108 · 新增，与提交无关）

「换一句委托」不够——三处消费方的算法本身假设单仓：

| 文件 | 缺陷 | 修法 |
|---|---|---|
| `codebase-insight/SKILL.md:55` | 缓存键是单个 `git rev-parse HEAD`。shell 下那是外壳仓 HEAD，只在指针 bump 时变——子模块内有代码变更但未 bump 时会**误命中缓存** | 改存按 `scan_targets` 排序的 per-target revision map（或其聚合指纹） |
| `test-run/SKILL.md:83` | `--affected` 只跑一次仓根 `git diff --name-only <base>`。shell 下只得到 gitlink 条目，**拿不到子仓文件级 diff** | 逐 `scan_target` 算 merge-base 与文件 diff，结果带 label 合并 |
| `e2e-test-flow/references/impact-analysis.md` | 同上，影响分析的 diff 基线是单仓 | 同上 |

### 6.4 操作方（3 文件 · 改成委托）

- `pipeline/SKILL.md:208` —— 整段探测说明替换为 `Task: /workspace-topology`；删 `devdocs_frontmatter` 传参管道
- `retrofit/SKILL.md:177, 179` —— 同上；179 的「若上一步探测到工作区模式，一并写入」子句删除
- `realign-scope-layout.md:82–85 / 156 / 229` —— 82–85 改委托 `--check`（消费 `undeclared_submodules`）；**156 迁移路由整行删除**；229 修复项指针改新 skill

### 6.5 schema 与治理（4 处）

- `layout/layout-metadata-schema.md:27, 28, 45, 54` —— workspace 两字段从 `devdocs:` schema **摘出**，留一句「该维度已独立，见 `/workspace-topology`」
- `agent-memory/SKILL.md:180–264`（11 处）—— 白名单摘两字段、示例更新、入参说明收缩到只剩 `initialized_at`
- `_shared/constraints.md:9, 292–299` —— §10 按 §4.2 重写
- `_shared/workspace-mode.md` —— 瘦身（§4.1），非删除

### 6.6 health（2 文件）

- `health-lint-implementation.md:27, 389, 391, 405, 409, 453` —— 适用性门与检测对象**全部改为消费 `pointer_checks`**，不读 `mode`、不自己解析 `code_roots`（codex R2 F-106）；405 修复路径指针改 `probe-and-repair.md`
- `realign-scope-health.md:33, 95, 167` —— 同向；`not_applicable` 由 `pointer_checks[].state` 表达

### 6.7 文档（3 处）

`docs/architecture.md:283–296`、`docs/workflows.md:333`、本仓 `AGENTS.md` 当前状态节。

**不改**：`docs/superpowers/specs/2026-08-05-*`、`docs/audits/*`——历史 spec 与台账按本仓惯例不追改。

### 6.8 spec_version bump

| 文件 | 变更性质 | bump |
|---|---|---|
| `_shared/constraints.md` | §10 结构重写 | `shared-constraints.v4` → `v5` |
| `_shared/workspace-mode.md` | 瘦身 + 声明 schema 移出 | `workspace-mode.v1` → `v2` |
| `agent-memory` | 受管白名单（硬校验规则）变更 | 按其 `references/realign.md` 规则 bump |
| `layout-metadata-schema.md` | 必填字段集变更 | bump |
| 新 skill | 新建 | `workspace-topology.v1` |

按 `realign/bump-sync-three-places`，每处 bump 同步更新 `references/realign.md` 当前常量、Migration Matrix、模板 frontmatter 示例。

## 7. 存量迁移

旧项目字段在 `devdocs.workspace_mode`（`chiaki-ng-dev` 已实测跑过，可能真实存在）。

探测时发现旧位置 → ⚠️ 列出并 AskUserQuestion 是否迁到 `workspace:` 块。一次性，之后幂等。

**不建独立迁移机器**：可重入入口已经覆盖这件事。这与 0.2 删掉的迁移手术性质不同——那是搬文件、造目录；这是同一文件内挪一个 yaml 键。

## 8. 复杂度账

| 项 | 增 | 减 |
|---|---|---|
| `skills/workspace-topology/`（SKILL + 1 reference） | +约 260 行 | |
| `workspace-shell.md` 删除 | | −252 行 |
| ↳ 存活分流（`probe-and-repair.md` 约 50 + `_shared` 约 20） | +70 行 | |
| `_shared/workspace-mode.md` 瘦身（声明 schema / 校验表 / 归属判定移出） | | −约 70 行 |
| 消费方复述内容（`dev-workflow` × 3 文件） | | −约 40 行 |
| `agent-memory` 白名单 + 示例 | | −约 15 行 |
| `pipeline` / `retrofit` 传参管道 | | −约 8 行 |
| `constraints.md §10` | | −约 3 行 |
| §6.3 单仓算法迁移（3 处，净增） | +约 20 行 | |
| **净** | | **约 −40 行** |

三稿的账：第 1 稿 −120，第 2 稿 −50（R1 修正引入 70 行契约），第 3 稿 −40（塌缩省下事务协议，但 §6.3 的算法迁移是净增且不可省）。

新增的不是行数而是**一个 skill 边界**。换来的是：非 DevDocs 项目可用、拓扑事实单点收敛、5 处路径类消费方对声明格式变更免疫。提交侧不在收益范围内——那是这次明确放弃的（§2.5）。

## 9. 验证

本仓是规格库，无可跑的 drain。验证分两级：

**本仓（可立即做）**

1. `grep -rn "workspace_mode\|workspace-mode\|workspace-shell" skills/ docs/` —— 除历史 spec / 台账外零命中
2. `grep -rn "\.gitmodules" skills/ | grep -v workspace-topology` —— 零命中
3. **mode-derived 分支检查**：`grep -rn "mode.*shell\|shell.*mode" skills/ | grep -v workspace-topology` 逐条人工判读，确认无 skill 以 `mode` 做行为分支（codex R1 F-002：只 grep `.gitmodules` 兜不住语义泄漏，`workspace/no-bypass` 禁的是读声明，不禁 `if mode == shell`）
4. 新 SKILL.md ≤ 500 行（硬约束）
5. 死链检查：`workspace-shell.md` 无残留引用（`_shared/workspace-mode.md` **保留**，其引用应仍可解析）
6. `realign --scope=health` 的 `dead-link` rule 全过

**真实项目（挂账，不阻塞本稿实施）**

7. 在 `chiaki-ng-dev`（已有 shell 声明）跑 `--check`，确认存量迁移提示、幂等、`pointer_checks` 与 `git submodule status` 一致
8. 在一个 inline 项目跑 `--check`，确认 `scan_targets` 为单项 `.`、`code_dir_write_policy: unrestricted`、`docs/` 写入不被零污染规则误禁（§2.4 要点 2 的自相矛盾场景）
9. **提交路径零回归验证**：inline 项目分别跑 `bugfix` 与 `dev-workflow` 默认路径，确认提交形态与今天逐字节一致——本稿不改提交协议，此项是回归兜底而非新行为验证
10. `codebase-insight` 缓存键与 `test-run --affected` 在 shell 项目上的迁移正确性（§6.3）

第 7–10 项与 [空 diff 修复的验证债](../../audits/2026-08-20-complexity-audit-backlog.md) 合并挂账。

## 10. 明确不做

| 不做 | 理由 |
|---|---|
| inline→shell 仓库手术（建外壳仓、搬文件、造 `<R>-dev` 目录） | §0.2；skill 只管当前文件夹内部 |
| **封装提交侧（`--plan-commits` / 提交证据查询 / `review_diff_sources`）** | §2.5；R2 熔断，需要持久 execution receipt + 结构化 message 对象 + gitlink tree transition，即一个跨仓事务协议 |
| `workspace-topology` 执行 `git commit` | 提交是干活 skill 的职责 |
| topology 改写 commit message（剥离编号 trailer） | codex R2 F-103/F-105：只删不迁会让 `Review-Batch-Id` 从追溯枢纽消失，且 7 个 trailer 里 5 个不在白名单会泄漏进上游；文本剥离无安全语法边界 |
| topology 输出 `mode` 供机器分支 | codex R1 F-002 / R2 F-106；输出 `capabilities` 与 `pointer_checks` |
| topology 记忆「变更归属」与「忽略继续」决定 | codex R2 F-107；那是调用方的会话状态，topology 只给快照 + `snapshot_id` |
| `docs_root` 做成可配置字段 | §3.1 |
| 把 `--check` 拆成多个只读 flag | R1 F-003 判 `--commit-status` 缺独立失败语义；R2 熔断后提交侧整体移出，剩余面只需一个查询 |
| 嵌套子模块（vendor / 依赖项）进 `code_roots` 语义 | 沿用 `workspace/no-nested-submodules`：依赖项的正确答案本就是「忽略」 |
| 「什么算源码」的静态白名单 | §4.3 |
| 移除代码根时 `git submodule deinit` / `git rm` | 破坏性动作交用户 |
| 为存量声明位置迁移建独立机器 | §7；可重入入口已覆盖 |

## 11. 待审查者重点质疑（R3）

R2 的 8 条中，7 条源自已删除的两节（提交侧接口），随塌缩一并消失。剩余需要 R3 验证的：

1. **§4.1 的切分判据是否可操作** —— 「≥2 个 skill 需按条文行动 → 留 `_shared`；只需一个答案 → 进 skill」。请找出这个判据判不了、或判出反直觉结果的条目。特别是 `workspace/no-pollution`（`code-self-describe` 只需一个答案 `code_dir_write_policy`，但 `dev-workflow` 提交前的违约检测需要按条文行动——同一条规则跨两类）。
2. **`no-bypass` 收窄后是否还有约束力**（§4.2）—— 「禁自己读声明，不禁引用行为约束」这个边界，会不会被下一个 skill 解释成「我这是引用行为约束」从而绕过 `--check`。
3. **`capabilities` 只剩一项是否够**（§2.4 要点 2）—— `code_dir_write_policy` 泛化后覆盖了 `codebase-insight:158` 与 `code-self-describe:87`。请核对 `dev-workflow` 提交前的零污染违约检测能否只靠这一项表达。
4. **§6.3 的单仓算法迁移是否完整** —— 除 `codebase-insight` 缓存键、`test-run --affected`、E2E 影响分析这三处，是否还有别的 skill 内嵌了单仓假设（尤其 `verify` 的追溯扫描与 `ms-sync`）。
5. **`snapshot_id` 是否解决了 R2 F-107** —— 调用方持久化归属与忽略决定，topology 只给快照。这个分工是否真闭合，还是把生命周期缺口从 topology 挪到了调用方而没有消除。
