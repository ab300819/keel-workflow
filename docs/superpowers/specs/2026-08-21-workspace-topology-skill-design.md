# 抽取 workspace-topology：仓库拓扑从 DevDocs 解耦为独立 skill

> 状态：**第 4 稿 · 待 R4** · 日期：2026-08-21
> 审查轨迹：R1 `39.5`（7 条全确认）→ R2 `70.75`（**+79%**，5 复现 + 3 自引入）→ 🔴 熔断 → 用户决策「塌缩：提交侧不做接口」→ R3 `56.5`（**−20%**，6 条确认 0 驳回；codex 单独确认「塌缩本身是正确的」）→ 本稿
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
| c | **按面切分**：声明 / 校验 / 查询协议搬进 skill；提交 / 零污染 / gitlink 三面的**行为协议留 `_shared/workspace-mode.md` 并瘦身** | §4.1；第 1 稿曾定「全留 `_shared`」、第 2 稿曾定「全进 skill 并删除该文件」，两者都被推翻 |
| d | 拓扑**事实**一律委托 `--check`，⛔ 不得自读声明文件 / 解析 `.gitmodules`；引用 `_shared` 的**行为条文**合法 | `workspace/no-bypass`（收窄形态见 §4.2） |
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
      code_metadata_write_policy: explicit_opt_in    # unrestricted | explicit_opt_in
    pointer_checks:                     # health-lint 的 submodule/pointer-drift 直接消费
      - {label: web, recorded: e4f5g6h, actual: e4f5g6h, state: consistent}
      - {label: api, recorded: a1b2c3d, actual: f7a8b9c, state: drift_ahead}
    root_residue: []                    # 仓根下不在 docs/、不属任何 scan_target 的已跟踪文件（ℹ️，§4.3）
    undeclared_submodules: []           # .gitmodules 有条目但未进声明 → ℹ️
    worktree_changes:                   # 按仓分组，gitlink 条目已在出口前滤掉
      - {label: web, path: web, changes: [src/a.ts]}
      - {label: ".", path: ".", changes: [docs/devdocs/00-context.md]}
```

五条契约要点：

1. **结构化输出里没有 `mode`**（codex R3 F-203）。第 2、3 稿把它留在 `summary.details` 并注「仅供人读」——那个注释**没有约束力**，字段在机器可读位置就会被拿去分支。现在它只出现在 `summary.headline` 的人读散文里（如「shell 模式，2 个代码根」）。§9 的验证项相应改为**逐消费方正向检查**是否显式使用 `scan_targets` / `worktree_changes` / `pointer_checks`，而不是反向 grep `mode`。

2. **`capabilities` 两项，各管一件事**。第 2 稿的 `code_docs_policy: allow|skip_by_default` 表达不了 `codebase-insight:158` 的「不往任何子模块写文件」——inline 时 `scan_targets = [{".", "."}]`，而 `docs/` 就在 `.` 里面，「不往 scan_target 写非代码文件」会**禁掉 inline 下写 `docs/`**，零污染红线在 inline 退化时自相矛盾。
   第 3 稿泛化为单项 `code_dir_write_policy` 又不够（codex R3 F-202）：`code-self-describe` 的文件头注释**写进源码文件本身**，按枚举字面属「允许写入」，但按零污染红线应默认跳过——单靠写入策略推不出正确结论。故拆两项：
   - `code_dir_write_policy: unrestricted | source_and_tests_only` —— 管**往代码目录写什么类别**
   - `code_metadata_write_policy: unrestricted | explicit_opt_in` —— 管**私有代码元数据**（自描述注释、模块级 `CLAUDE.md`、未来 layout.v2 的 `@satisfies` 注释）。`explicit_opt_in` 即 `code-self-describe` 默认跳过、`--force-code-docs` 才执行
   
   其余消费方核过无需新 capability：`test-run` 的「按 root 分组」与 `codebase-insight` 的「仓间关系小节」都能由 `len(scan_targets) > 1` 派生——**而且比今天按 `mode` 判更准**（shell 单代码根时今天会错误地要求产出仓间关系小节）。`codebase-insight` 的产物落点只需 `docs_root`，不靠 capability。

3. **`worktree_changes` 是无状态快照，不带 `snapshot_id`**（codex R3 F-205 的塌缩式处置）。第 3 稿加了 `snapshot_id`，codex 指出它没定义生成方式、相等性、失效语义，且调用方无处持久化归属与忽略决定——要闭合就得建一套 `workspace_baseline`（per-path `patch_fingerprint` + attribution + decision + 提交前硬门比对）。
   **不建**。理由：那个生命周期缺口**今天就存在**且从未被抱怨——今天 `task-orchestration.md` Step 3 扫一次、Step 4 按任务「涉及文件」归属、Step 5 问用户，忽略决定只活在会话里，重启就重问；`git status` 也从来只给路径 + 状态位，分不出「同一路径里用户的改动」与「Agent 的改动」。本稿的职责是把**扫描**接口化，不是顺手补一个今天没有的持久化基线。加它就是又一次「修复引入新问题」。
   所以：`--check` 每次给当次的真实快照（gitlink 条目在出口前已滤掉，覆盖 `task-orchestration.md` Step 3–5），**归属判定与忽略决定完全留在调用方，与今天逐字节一致**。写进 §10 明确不做。

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

切分判据（第 3 稿只有下面第一句，codex R3 F-201 指出它处理不了混合情形——`no-pollution` 既由 `_shared` 定义行为、又由 topology 派生 `code_dir_write_policy`，两者的权威关系与漂移检查未定义。补为三层归属）：

**判据**：一件事若有 ≥2 个 skill 需要按它的条文行动（而非只需要一个答案），它是跨 skill 行为约束，留 `_shared`；若消费方只需要一个答案，它是查询，进 skill。

**混合情形按三层归属定权威，消除双源**：

| 层 | 归属 | 职责 | 不得做 |
|---|---|---|---|
| 事实层 | `workspace-topology` | 输出拓扑事实与**派生能力**（`capabilities`） | 不解释能力的行为语义 |
| 规范层 | `_shared/workspace-mode.md` | **唯一**解释能力枚举的行为语义与通用红线 | 不写消费方专属决策（如「`code-self-describe` 默认跳过」） |
| 执行层 | 各消费 skill | 消费能力并执行 | 不重复解释策略、不自行推导应否跳过 |

据此从 `_shared` 的零污染写入范围表里**删掉消费方专属行**（`code-self-describe` 的模块级 `CLAUDE.md`、dev-workflow 的「自描述更新」步骤），只留通用红线；这两条的决策改由 `code_metadata_write_policy` 派生。这同时消掉了「同一条规则跨两类」的双源问题。

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

**同一裁决须扩展到零污染违约检测**（codex R3 F-202）。原 §5 有同构矛盾：要求「提交前对每个变更子模块跑 `git status --porcelain`，出现**非源码/测试路径**的变更 → ⚠️」，同时又声明「不做静态白名单猜测什么算源码」。裁法一致：

- `workspace/pollution-check`（住 `_shared`）：`shell` 模式提交前，对每个变更 code_root 跑 `git status --porcelain`，**列出全部变更路径清单**交用户判断（⚠️ AskUserQuestion：提交 / 排除 / 终止），**不预先判定哪条是「非源码」**。

这是既存矛盾，非本稿引入，但本稿动这一节就得一并裁掉——留着它会让实施者以为需要一个源码分类器。


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
| `dev-workflow/references/task-orchestration.md` | 136, 145 | 复述删除、改指 `_shared`；工作区遍历改消费 `--check` 的 `worktree_changes`（§2.4 要点 3；归属判定与忽略决定留在本 skill，与今天一致） |
| `dev-workflow/references/verification-flow.md` | 354 | **不动**——drain 侧逐 `code_root` 拼接仍按 `_shared` 提交协议执行。第 2 稿曾改它，R2 F-106 证明那个改法会让空 diff 缺陷复活 |

### 6.3 单仓算法迁移（codex R2 F-108 / R3 F-204）

「换一句委托」不够——多处 skill 的**算法本身**假设单仓。第 3 稿只列了三处，codex R3 判为「明显不完整」，要求建**权威清单**而非举例。以下按缺陷类别分组，来源是全仓 grep（`git rev-parse HEAD` / `git diff --name-only` / `git status --porcelain` / `git log --grep` / `merge-base` / 「扫描代码」）逐条判读。

**A 类 · 代码扫描基线**（需逐 `scan_target` 执行并以 label 限定结果，防跨仓重名混淆）

| 位置 | 缺陷 |
|---|---|
| `sync/SKILL.md:96` | 「扫描代码库（工作区状态）」单仓 |
| `sync/SKILL.md:126` + `sync/references/trace-mode.md:5, 14` | trace 阶段扫描 `@satisfies`/`@verifies` 标注，单仓；**`verify` B3 复用 `ms-sync`，只改 verify 入口句修不了委托链** |
| `test-run/SKILL.md:111` | 扫描 `@verifies`/`@testcase` 标注 |
| `test-cases/SKILL.md:262` | 扫描代码标注 |
| `dev-flow/SKILL.md:29` | 「必要时扫描代码补足上下文」 |
| `onboard/SKILL.md` `--update` | 从仓根采集目录结构、`git status`、`git log`、运行命令 |

**B 类 · revision / freshness 判据**（单个仓根 HEAD 在 shell 下只随指针 bump 变动 → 子模块有代码变更但未 bump 时**误判新鲜**）

| 位置 | 缺陷 |
|---|---|
| `codebase-insight/SKILL.md:55` | 缓存键 `commit_hash != git rev-parse HEAD` |
| `verify/templates/verify-report.md:13` | `verified_commit`「供 pipeline 判断 freshness」 |
| `verify/references/schema-drift.md:23` | 拿 `codebase-insight` 的 `commit_hash` 与 git HEAD 比 |

**B 类修法须成套**：`codebase-insight` 改存按 `scan_targets` 排序的 `target_revisions` map（**单一 schema，不给「map 或聚合指纹」二选一**），并同步 frontmatter 字段、摘要契约、`schema-drift.md:23` 的判据、以及该 skill 的 `spec_version` bump。第 3 稿只说了 `codebase-insight` 一侧，漏了下游三处。

**C 类 · diff 基线**

| 位置 | 缺陷 |
|---|---|
| `test-run/SKILL.md:82–83` | `--affected` 单次仓根 `merge-base` + `git diff --name-only`；shell 下只得到 gitlink 条目 |
| `e2e-test-flow/references/impact-analysis.md` | 影响分析基线同上 |
| `code-self-describe/SKILL.md:182` + `templates/update-rules.md:60, 63` | 单仓 diff 基线。该 skill 在 shell 下默认跳过，但 `--force-code-docs --update` 时会跑且算错；**`--audit` 模式不应跳过**（只读盘点，不写代码目录），也需逐 target |

**D 类 · 工作区洁净门**（⚠️ **codex 未发现，本轮自查补入**）

| 位置 | 缺陷 |
|---|---|
| `dev-workflow/references/auto-mode.md:38, 120, 156, 157` | `--headless` 无人值守的洁净门用仓根 `git status --porcelain` 判空。shell 下**外壳仓干净而子模块脏时会误判通过**，无人值守场景下这是最危险的一处 |
| `dev-workflow/references/task-orchestration.md:237` | 「`git status --porcelain` 非空 → 报错」同上 |

D 类改为消费 `--check` 的 `worktree_changes`（已按仓分组、已滤 gitlink），洁净判据 = 所有仓的 `changes` 均为空。

**E 类 · Git 历史**：`task-orchestration.md:114` 的 `git log --grep="(T-XX)"` 属提交面，按 §6.2 留 `_shared` 条文，不在本节。

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
| §6.3 单仓算法迁移（**12 处**，净增） | +约 75 行 | |
| §4.1 三层归属表 + §4.3 裁决扩展 | +约 15 行 | |
| **净** | **约 +2 行** | |

四稿的账：第 1 稿 −120 → 第 2 稿 −50（R1 修正引入 70 行契约）→ 第 3 稿 −40 → 第 4 稿 **+2**。

净删归零的原因是 §6.3 从 3 处涨到 12 处（codex R3 F-204 判第 3 稿的三处清单「明显不完整」，要求建权威清单）。**这不是方案在膨胀** —— 那 12 处单仓假设**今天就是错的**，只是在 inline 项目上恰好不出错，所以从未暴露。抽 skill 这件事把它们从「隐性缺陷」变成了「必须一并修的显性工作」。

由此产生一个实施顺序问题（§11 第 5 问）：这 12 处是否必须与 skill 抽取同批落地。

新增的不是行数而是**一个 skill 边界**。换来的是：非 DevDocs 项目可用、拓扑事实单点收敛、5 处路径类消费方对声明格式变更免疫。提交侧不在收益范围内——那是这次明确放弃的（§2.5）。

## 9. 验证

本仓是规格库，无可跑的 drain。验证分两级：

**本仓（可立即做）**

1. **旧字段与旧手册零命中**：`grep -rn "workspace_mode\|workspace-shell" skills/` —— 现役消费方零命中（历史 spec / 台账不计）。⚠️ **不要**把 `workspace-mode` 一并纳入本项——`_shared/workspace-mode.md` 保留，合法消费方必须继续引用它，纳入必然假失败（codex R3 F-206）
2. **`_shared/workspace-mode.md` 的引用者白名单**：只允许提交 / 零污染 / gitlink 三面的消费方（`dev-workflow` / `bugfix` / `dev-flow`）引用；其余 skill 引用它即为归属错误
3. `grep -rn "\.gitmodules" skills/ | grep -v workspace-topology` —— 零命中
4. **正向能力检查**（取代第 3 稿的反向 grep `mode`）：逐个路径类消费方确认其文本**显式使用** `scan_targets` / `worktree_changes` / `pointer_checks` / `capabilities` 之一。反向 grep 抓不到「读 `code_roots` 后自己分支」「给 `mode` 起别名」「完全不读声明直接在仓根跑 `git status`」三类绕过（codex R3 F-203）
5. §6.3 的 A–D 四类清单逐条闭环，B 类须成套（`codebase-insight` 的 `target_revisions` + frontmatter + 摘要契约 + `schema-drift.md:23` + `spec_version`）
6. 新 SKILL.md ≤ 500 行（硬约束）
7. 死链检查：`workspace-shell.md` 无残留引用（`_shared/workspace-mode.md` **保留**，其引用应仍可解析）
8. `realign --scope=health` 的 `dead-link` rule 全过

**真实项目（挂账，不阻塞本稿实施）**

9. 在 `chiaki-ng-dev`（已有 shell 声明）跑 `--check`，确认存量迁移提示、幂等、`pointer_checks` 与 `git submodule status` 一致
10. 在一个 inline 项目跑 `--check`，确认 `scan_targets` 为单项 `.`、`code_dir_write_policy: unrestricted`、`docs/` 写入不被零污染规则误禁（§2.4 要点 2 的自相矛盾场景）
11. **提交路径零回归验证**：inline 项目分别跑 `bugfix` 与 `dev-workflow` 默认路径，确认提交形态与今天逐字节一致——本稿不改提交协议，此项是回归兜底而非新行为验证
12. §6.3 的 B / C / D 三类在 shell 项目上的迁移正确性——特别是 D 类：构造「外壳仓干净、子模块脏」状态，确认 `--headless` 洁净门**不再**误判通过

第 9–12 项与 [空 diff 修复的验证债](../../audits/2026-08-20-complexity-audit-backlog.md) 合并挂账。

## 10. 明确不做

| 不做 | 理由 |
|---|---|
| inline→shell 仓库手术（建外壳仓、搬文件、造 `<R>-dev` 目录） | §0.2；skill 只管当前文件夹内部 |
| **封装提交侧（`--plan-commits` / 提交证据查询 / `review_diff_sources`）** | §2.5；R2 熔断，需要持久 execution receipt + 结构化 message 对象 + gitlink tree transition，即一个跨仓事务协议 |
| `workspace-topology` 执行 `git commit` | 提交是干活 skill 的职责 |
| topology 改写 commit message（剥离编号 trailer） | codex R2 F-103/F-105：只删不迁会让 `Review-Batch-Id` 从追溯枢纽消失，且 7 个 trailer 里 5 个不在白名单会泄漏进上游；文本剥离无安全语法边界 |
| topology 输出 `mode` 供机器分支 | codex R1 F-002 / R2 F-106；输出 `capabilities` 与 `pointer_checks` |
| topology 记忆「变更归属」与「忽略继续」决定 | codex R2 F-107；那是调用方的会话状态，topology 只给快照 |
| **建 `workspace_baseline` 持久化基线**（`snapshot_id` + per-path `patch_fingerprint` + attribution + decision + 提交前硬门比对） | codex R3 F-205 的建议，**不采纳**。该生命周期缺口今天就存在且从未被抱怨：今天忽略决定只活在会话里、重启重问，`git status` 也从来只给路径 + 状态位。本稿职责是把**扫描**接口化，不是顺手补一个今天没有的持久化基线——加它就是又一次「修复引入新问题」 |
| 源码 / 测试路径分类器 | §4.3；`root_residue` 与 `pollution-check` 一律列清单交用户判断 |
| `docs_root` 做成可配置字段 | §3.1 |
| 把 `--check` 拆成多个只读 flag | R1 F-003 判 `--commit-status` 缺独立失败语义；R2 熔断后提交侧整体移出，剩余面只需一个查询 |
| 嵌套子模块（vendor / 依赖项）进 `code_roots` 语义 | 沿用 `workspace/no-nested-submodules`：依赖项的正确答案本就是「忽略」 |
| 「什么算源码」的静态白名单 | §4.3 |
| 移除代码根时 `git submodule deinit` / `git rm` | 破坏性动作交用户 |
| 为存量声明位置迁移建独立机器 | §7；可重入入口已覆盖 |

## 11. 待审查者重点质疑（R4）

R3 的 6 条全部确认、0 驳回，处置如下（其中 1 条不采纳并给了理由）：

| R3 id | 处置 |
|---|---|
| F-201 P2 | §4.1 补三层归属（事实 / 规范 / 执行），并从 `_shared` 删掉消费方专属决策行，消除双源 |
| F-202 P1 | §2.4 要点 2 拆 `code_metadata_write_policy`；§4.3 把「不猜源码」裁决扩展到零污染违约检测 |
| F-203 P2 | §2.4 要点 1 从 `summary.details` **删除 `mode`**；§9 验证项 4 改正向能力检查 |
| F-204 P1 | §6.3 重写为 A–D 四类权威清单（12 处），B 类改为成套修法 |
| F-205 P1 | **部分不采纳**：删 `snapshot_id`，但不建 `workspace_baseline`，理由见 §10 与 §2.4 要点 3 |
| F-206 P2 | 决策 c / d 改写；§9 验证项 1 拆分并排除 `workspace-mode` |

**本轮自查另补一条 codex 未发现的 P1**：`dev-workflow/references/auto-mode.md:38, 120, 156, 157` —— `--headless` 洁净门用仓根 `git status --porcelain`，shell 下外壳仓干净而子模块脏时误判通过（§6.3 D 类）。

R4 请攻击：

1. **F-205 的不采纳是否成立** —— 我的论据是「该缺口今天就存在、本稿只负责把扫描接口化」。请判断这个论据是否在偷换问题：把单仓 `git status` 换成多仓聚合快照，是否**本身**就提高了对基线一致性的要求，从而使「与今天等价」不成立。
2. **三层归属是否真消除了双源**（§4.1）—— `capabilities` 由 topology 派生、行为语义由 `_shared` 解释。当 `_shared` 的红线改变时，topology 派生的枚举值语义随之改变而 topology 文本不变。这是解耦还是隐式耦合？
3. **§6.3 的 A–D 清单是否仍有遗漏** —— 清单来自全仓 grep（`git rev-parse HEAD` / `git diff --name-only` / `git status --porcelain` / `git log --grep` / `merge-base` / 「扫描代码」）。请判断这组 grep 关键词是否覆盖了「内嵌单仓假设」的全部表达形式。
4. **§9 验证项 2 的白名单是否可执行** —— 「只允许提交 / 零污染 / gitlink 三面的消费方引用 `_shared/workspace-mode.md`」。这个白名单靠人工判读维持，会不会在下次有人新增引用时静默失效；是否该做成 health-lint rule。
5. **实施顺序** —— §6.3 的 12 处算法迁移与 skill 抽取是否必须同批落地，还是可以分两批（先抽 skill + 路径类委托，再补算法迁移）。如可分批，第一批落地后 shell 项目会不会处于比今天更差的中间态。
