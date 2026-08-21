# 抽取 workspace-topology：仓库拓扑从 DevDocs 解耦为独立 skill

> 状态：**第 2 稿 · codex R1 已过（7 条全确认并修正）· 待 R2** · 日期：2026-08-21
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
| e | skill 保持**只读**：把调用方的逻辑提交单元映射成物理步骤、跑只读门，不执行 `git commit` | 提交由干活的 skill 做；逻辑提交数与编号策略归调用方，skill 不吃 DevDocs 编号语义 |
| f | 删除 inline→shell 迁移手术（七步、约 170 行） | 0.2 |
| g | docs 根恒为 `<仓库根>/docs/`，不设字段、不可配置 | 310 处 `docs/devdocs` 硬编码的正确性建立在这条常量上 |
| h | 可重入四动作，幂等 | 用户需求：后期改 mode、加子模块 |

## 2. 接口契约

### 2.1 「依赖接口，而不是实现」

本稿的核心约束。第 1 稿曾把 10 处消费方指向 `_shared/workspace-mode.md` 的**具体章节**（§ N+1 仓提交协议、§ 校验规则、§7.2 gitlink 判据），被否决：协议一改，10 处跟着改，接口等于没抽。

**修正后**：委托方不知道字段叫 `workspace.mode`、不知道真源是 `.gitmodules`、不知道任何章节号，只知道调入口拿答案。

这条原则有一个可执行形式，写进 `_shared/constraints.md §10`：

- `workspace/no-bypass`：任何需要代码根路径、docs 根、提交分组或提交状态的 skill 一律委托 `/workspace-topology`，**⛔ 不得自行读取声明文件或解析 `.gitmodules`**。

没有这条禁令，下一个 skill 又会去 grep `AGENTS.md`。

### 2.2 入口：一个交互式 + 两个只读查询

| 入口 | 回答的问题 | 被问的时点 |
|---|---|---|
| `/workspace-topology` | （交互式维护声明，见 §5） | 用户显式 / init / retrofit |
| `--check [--id <ID>]` | 代码扫哪、docs 在哪、本 skill 该开还是该关、工作区什么状态；带 `--id` 时附该编号的提交证据 | 流程开头 / 断点续做判定 |
| `--plan-commits` | 把调用方的逻辑提交单元映射成有序物理步骤 | 提交前 |

**声明失配前置**：§3.3 的 ⛔ 行在两个查询上一律前置阻塞——拿不到可信拓扑，后面的答案都无意义。

**为什么 `--plan-commits` 不能并进 `--check`**：`--plan-commits` 带提交前置门（detached HEAD 等）。`test-run` 在流程开头问「代码在哪」，不该被一个提交时才相关的门挡住。**问题不同、失败语义不同，就不共用入口。**

**为什么提交状态查询并进了 `--check` 而非独立成第三个 flag**：它与 `--check` 的失败语义完全相同（只有声明失配才 ⛔），只多一个 ID 输入。第 1 稿曾把它独立为 `--commit-status`，被判缺乏独立的失败语义（codex R1 F-003）。

### 2.3 摘要信封

作为子 Agent 被委托，返回 `yaml-summary-v1`（`constraints.md §2`），`skill: workspace-topology`。私有字段按 `yaml-summary/details-only-private` 一律落 `summary.details`。

### 2.4 `--check`：输出能力，不输出模式

第 1 稿直接返回 `mode: inline|shell`，被判**语义泄漏**（codex R1 F-002）：`code-self-describe` 要靠它决定跳不跳、`verify` 要靠它决定扫哪，调用方必然写 `if mode == shell`。`workspace/no-bypass` 只禁止读声明文件，没禁住这种分支。

**修正：输出能力与事实，不输出模式。**

```yaml
summary:
  details:
    docs_root: docs
    scan_targets:                       # 代码扫描 / 测试执行 / 洞察盘点的目标目录
      - {label: web, path: web}
      - {label: api, path: api}         # inline 时为单项 {label: ".", path: "."}
    capabilities:
      code_docs_policy: skip_by_default # allow | skip_by_default —— code-self-describe 直接读这个字段
      single_logical_commit: false      # true 时调用方可把多个逻辑单元合并为一次提交
    root_residue: []                    # 仓根下不在 docs/、不属任何 scan_target 的已跟踪文件（ℹ️，见 §4.3）
    undeclared_submodules: []           # 仓内有 .gitmodules 条目但未进声明 → ℹ️
    worktree_changes:                   # 按仓分组，gitlink 条目已在出口前滤掉
      - {label: web, path: web, changes: [src/a.ts]}
      - {label: ".", path: ".", changes: [docs/devdocs/00-context.md]}
    mode: shell                         # ⚠️ 仅供人读；机器消费者不得以此分支
```

三条契约要点：

1. **`mode` 标注为仅供人读**。它留在输出里是为了让人看报告时知道自己在哪种拓扑下，但任何 skill 以 `mode` 做分支即违反 `workspace/no-bypass`。§9 的验证项因此不能只 grep `.gitmodules`，必须同时查 mode-derived 分支。
2. **`worktree_changes` 在出口前已排除 gitlink 条目**，且覆盖**任务开始时**的断点续做检查（`task-orchestration.md` Step 3–5），不是只覆盖提交前。第 1 稿把这个快照只挂在 `--plan-commits` 上，导致任务开始时的扫描无接口可用（codex R1 F-007）。「变更是否属于当前任务」的判定仍归调用方——它知道任务涉及哪些文件，topology 不知道。
3. **`root_residue` / `undeclared_submodules` 是 ℹ️ 级事实**，不阻塞。后者补住 `realign-scope-layout.md:83` 那条「未声明工作区模式」提示——改成委托后若不返这个字段，该提示会静默失效。

`--id` 附加段见 §2.6。

### 2.5 `--plan-commits`：逻辑单元 → 物理步骤

第 1 稿让 topology 输出 `commit_grouping`（长度恒为「代码根数 + 1」），被判 P1 阻塞（codex R1 F-004）：只有 `dev-workflow` 默认路径是 Commit 1+2，`bugfix` inline 下是**一个** fix commit 带 `BUG-XXX`，`dev-flow` 是**一项一 commit**，`--single-commit` 要求合成一次。topology 无权决定逻辑提交数，`carries_id` 更是三套互不相同的编号策略。

**修正：调用方给逻辑单元，topology 只做「逻辑 → 物理」映射。**

**输入**（调用方提供，topology 不发明）：

```yaml
logical_units:
  - kind: code                          # 语义类别，非仓库概念
    paths: [src/a.ts, src/b.ts]
    message: |
      feat(T-07): 实现 X

      Review-Batch-Id: rb-3
  - kind: docs
    paths: [docs/devdocs/00-context.md]
    message: "docs(T-07): 同步任务状态"
```

`bugfix` 传 1 个 `kind: code` 单元（message 含 `BUG-XXX`）；`dev-flow` 每个 checklist 项传 1 个；`dev-workflow --single-commit` 传 1 个合并单元。**message 全文由调用方写定**，编号体系不进 topology。

**输出**（有序物理步骤）：

```yaml
summary:
  details:
    steps:
      - step: 0
        cwd: web                        # inline 恒为 "."
        add: [src/a.ts]
        message: "feat: 实现 X"          # 见下方 message 改写规则
        gate: ok                        # ok | blocked
        gate_recovery: null
      - step: 1
        cwd: .
        add: [docs/devdocs/00-context.md, web]
        message: |
          docs(T-07): 同步任务状态

          web@{{steps[0].sha}}
        gate: ok
    unmapped_paths: []                  # 不属任何 scan_target 且不在 docs/ 的路径 → ⚠️ 调用方确认
    pollution_findings: []              # 落进 scan_target 的非源码/测试路径 → ⚠️ AskUserQuestion
```

调用方跑一个与拓扑无关的统一循环：`for s in steps: commit(s)`，并对 `{{steps[N].sha}}` 做**通用占位替换**（用前序步骤的实际 SHA）。占位替换是个泛型机制——调用方不知道 `web` 是子模块、不知道那行叫「指针 bump」。

四条契约要点：

1. **inline 是恒等映射**。1 个逻辑单元出 1 步、2 个出 2 步，`cwd` 恒为 `.`，无占位符。**三个消费方今天各自的提交形态原样保留**，零回归。
2. **占位符消解了两阶段调用**。外壳提交正文要的 `web@<sha>` 只在子仓提交后才存在（codex R1 F-001）。第 1 稿的一次性快照装不下它；用模板占位而非 `plan → finalize` 两次调用，是因为占位替换对调用方是泛型操作，不引入拓扑知识。
3. **message 改写规则**：shell 下落进子模块的步骤，topology 按 `message_style: inherit` **剥掉调用方 message 的首行 scope 编号与编号型 trailer**（`T-XX` / `BUG-XX` / `Review-Batch-Id`），实现「子模块干净得像没有 DevDocs 存在过」；落进外壳仓的步骤原文保留。inline 下不改写。⚠️ 这条是 topology 唯一触碰 message 文本的地方，剥离规则须在 skill 内列白名单，不做正则猜测。
4. **门在算步骤时就跑掉**，`gate: blocked` → `status: failed` + `blockers`，调用方连循环都进不去。每项的 `gate_recovery` 按 `constraints.md §7` 四字段完整模板预置，调用方失败时照着走，不回头再问 skill。

### 2.6 `--check --id <ID>`：返证据，不返结论

第 1 稿返 `committed: true|false|drifted`，被判 P1 阻塞（codex R1 F-005）：`task-orchestration.md` Step 2 今天分四态——无提交 / 有码无档（`docs_only_pending`）/ 有码有档（进 Step 1.5）/ 指针不一致——三值枚举压掉了 `docs_only_pending`，`shell_commit` 单数也装不下 N 个代码提交。

**修正：返 topology-neutral 的提交证据，业务结论留给调用方。**

```yaml
summary:
  details:
    id: T-07
    implementation_refs:                # N 个代码提交；inline 时 0 或 1 项
      - {label: web, commit: a1b2c3d}
      - {label: api, commit: b2c3d4e}
    documentation_ref: c3d4e5f          # 文档提交；无则 null
    logical_shape: split                # split | combined | none
    consistency: consistent             # consistent | pointer_drift | not_applicable
    review_diff_sources:                # 延后外审的稳定 diff 源（见要点 2）
      - {label: web, range: a1b2c3d}
      - {label: api, range: b2c3d4e}
```

三条契约要点：

1. **`docs_only_pending` 与 Step 1.5 的 A–F 判定仍归 `dev-workflow`**。它读 `implementation_refs` 非空 + `documentation_ref` 为 null 自己得出 `docs_only_pending`。topology 不压缩业务结论。
2. **`review_diff_sources` 是延后外审的唯一合法 diff 源**。第 1 稿说 drain「按 `commit_grouping` 逐项取」——那是**提交前**的工作区计划，落盘后 `worktree_changes` 已为空，[2026-08-06 修掉的空 diff 缺陷](2026-08-06-review-unit-task-to-batch-design.md)会原地复活（codex R1 F-006）。此字段从追溯枢纽（外壳仓 commit 正文记录的子模块 SHA）重建，**排除纯文档提交**。⛔ drain 只能消费此字段，不得消费 `--plan-commits` 的产出。
3. **`logical_shape: combined` 的外审语义**：代码与文档在同一 commit 时，`review_diff_sources` 返回该 commit 并附 `docs_paths_excluded`，由调用方在取 diff 时排除文档路径。

> ℹ️ codex R1 F-006 同时指出 `--single-commit` + drain 在**今天**就与「只审 Commit 1、排除纯文档 Commit 2」冲突。核过了，这是既存缺陷、非本稿引入，归 [空 diff 修复的验证债台账](../../audits/2026-08-20-complexity-audit-backlog.md)。本稿只负责让新接口能表达 combined 形态（要点 3），不负责修那个既存缺陷。

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

### 4.1 方案 B（协议正文进 skill）

第 1 稿定的是方案 A（协议留 `_shared`，skill 只做执行器），立论是「消费方要读 `_shared` 拿约束条文」。§2.1 的原则落实后消费方不再读它，那 163 行只剩一个读者——**单读者的 SSOT 该和读者住在一起**。原则把方案 A 推成了 B。

```
skills/workspace-topology/
  SKILL.md                          定位 / 四入口 / 四动作 / 声明 schema / 校验表 / 分组契约
  references/topology-protocol.md   协议正文（原 _shared/workspace-mode.md 存活部分）
  references/probe-and-repair.md    探测步骤 / detached HEAD 处置 / 指针漂移修复
```

**删除**：`skills/_shared/workspace-mode.md`（163 行）、`skills/pipeline/references/layout/workspace-shell.md`（252 行）。

后者存活约 80 行（探测步骤、detached HEAD 处置、指针漂移三成因表），净删约 170 行。它住在 `pipeline/references/layout/` 下本身就是 0.1 的病灶之一——DevDocs 命名空间承载仓库级操作手册。

### 4.2 `_shared/constraints.md §10` 只剩三条

```
- workspace/single-entry：工作区拓扑（inline/shell）唯一入口 /workspace-topology
- workspace/default-inline：缺省 inline；无声明的项目行为完全不变
- workspace/no-bypass：需要代码根路径、docs 根、提交分组或提交状态的 skill 一律委托
  该入口，⛔ 不得自行读取声明文件或解析 .gitmodules
```

原 §10 的 `workspace/mode-enum`（含字段路径）、`workspace/code-roots-source`（含 `.gitmodules` 真源）、`workspace/orthogonal-to-layout`、`workspace/pointer` 四条**全部下沉进 skill**——它们描述实现，不该留在跨 skill 准则层。

**规则归属总表**：除上述三条留 `constraints.md §10` 外，全部 `workspace/*` 规则住 `skills/workspace-topology/references/topology-protocol.md`。其中两条因接口化而**降级为内部实现笔记**，不再是对外规则：

| 原规则 | 处置 |
|---|---|
| `workspace/gitlink-exclusion` | 降级——`worktree_changes` 出口前已排除，调用方无从见到 gitlink 条目 |
| `workspace/no-stash-gitlink` | 降级——同上，条目不出现即无从误提供 stash 选项 |

### 4.3 §4 / §5 矛盾的裁决

裁掉「源码文件」判定。改为：

- `workspace/root-residue`（住 `topology-protocol.md`）：`shell` 模式下，仓库根下不在 `docs/`、不属任何 `code_roots` 的**已跟踪文件** → ℹ️ 列清单，由用户判断。**不猜是不是源码，也不装作能猜。**

依据：§5 明确拒绝「静态白名单猜测什么算源码」，而 §4 的 ⚠️ 恰恰需要那个猜测。保留提示的价值（外壳仓不该有代码是真实约束），删掉它无法兑现的精确性。降 ⚠️→ℹ️ 是因为无法判定性质就不该要求确认。

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

## 6. 影响面（22 处）

### 6.1 消费方（10 处 · 全部收缩成同一句）

替换文本统一为：

> 代码根 / docs 根路径、提交分组与提交状态一律委托 `/workspace-topology`，本 skill 不读取声明文件、不解析 `.gitmodules`（`workspace/no-bypass`）。

| 文件 | 行 | 现状 | 处置 |
|---|---|---|---|
| `dev-flow/SKILL.md` | 133 | 指 `_shared` § N+1 | 换委托句 |
| `verify/SKILL.md` | 136 | 扫描范围 + 仓根源码 ⚠️ | 换委托句；⚠️→ℹ️（§4.3） |
| `e2e-test-flow/SKILL.md` | 48 | 指 `_shared` | 换委托句 |
| `codebase-insight/SKILL.md` | 152, 154 | 多代码根 | 换委托句 |
| `test-run/SKILL.md` | 72 | 测试执行目录 | 换委托句 |
| `code-self-describe/SKILL.md` | 87, 89, 93 | shell 下跳过 | 保留「跳过」决策（本 skill 私有），路径解析换委托句 |
| `bugfix/SKILL.md` | 288 | 指 `_shared` § N+1 | 换委托句 |
| `dev-workflow/SKILL.md` | 113, 300, 301, 313 | **复述** N+1 拆分规则、detached HEAD 门、五重状态检测 | **复述全删**；113 改读 `capabilities.code_docs_policy`；提交改为传 `logical_units` 消费 `steps`；断点续做改消费 `--check --id` 的证据字段 |
| `dev-workflow/references/task-orchestration.md` | 136, 145 | **复述**五重检测 + gitlink 判据 | **复述全删**，换委托句 |
| `dev-workflow/references/verification-flow.md` | 354 | **复述**逐 `code_root` 拼接 | **复述全删**；drain 侧 diff 源改为消费 `--check --id` 的 `review_diff_sources`（⛔ 不得消费 `--plan-commits` 产出，见 §2.6 要点 2） |

`verification-flow.md:354` 需特别注意：它是 [2026-08-06 空 diff 修复](2026-08-06-review-unit-task-to-batch-design.md) 的产物，且该修复**尚未在真实项目验证**（见 [复杂度审计遗留台账](../../audits/2026-08-20-complexity-audit-backlog.md)）。本稿改它的 diff 源表达方式，不改语义；验证债照旧挂账，不因本稿而解除。

### 6.2 操作方（3 文件 · 改成委托）

- `pipeline/SKILL.md:208` —— 整段探测说明替换为 `Task: /workspace-topology`；删 `devdocs_frontmatter` 传参管道
- `retrofit/SKILL.md:177, 179` —— 同上；179 的「若上一步探测到工作区模式，一并写入」子句删除
- `realign-scope-layout.md:82–85 / 156 / 229` —— 82–85 改委托 `--check`；**156 迁移路由整行删除**；229 修复项指针改新 skill

### 6.3 schema 与治理（4 处）

- `layout/layout-metadata-schema.md:27, 28, 45, 54` —— workspace 两字段从 `devdocs:` schema **摘出**，留一句「该维度已独立，见 `/workspace-topology`」
- `agent-memory/SKILL.md:180–264`（11 处）—— 白名单摘两字段、示例更新、入参说明收缩到只剩 `initialized_at`
- `_shared/constraints.md:9, 292–299` —— §10 按 §4.2 重写；顶部 `related` 摘掉已删文件
- `_shared/workspace-mode.md` —— 删除

### 6.4 health（2 文件）

- `health-lint-implementation.md:27, 389, 391, 405, 409, 453` —— `submodule/pointer-drift` 的适用性门改为「委托 `--check` 拿 `mode`」；389 的「读 `AGENTS.md` 的 `code_roots` 解析」改为消费 `--check` 输出；405 修复路径指针改新 skill references
- `realign-scope-health.md:33, 95, 167` —— 同向改字段表达

### 6.5 文档（3 处）

`docs/architecture.md:283–296`、`docs/workflows.md`、本仓 `AGENTS.md` 当前状态节。

**不改**：`docs/superpowers/specs/2026-08-05-*`、`docs/audits/*`——历史 spec 与台账按本仓惯例不追改。

### 6.6 spec_version bump

| 文件 | 变更性质 | bump |
|---|---|---|
| `_shared/constraints.md` | §10 结构重写 | `shared-constraints.v4` → `v5` |
| `agent-memory` | 受管白名单（硬校验规则）变更 | 按其 `references/realign.md` 规则 bump |
| `layout-metadata-schema.md` | 必填字段集变更 | bump |
| 新 skill | 新建 | `workspace-topology.v1` |
| `workspace-mode.v1` | 退休 | 文件删除，无迁移矩阵（声明位置迁移由 §7 的可重入动作承载） |

按 `realign/bump-sync-three-places`，每处 bump 同步更新 `references/realign.md` 当前常量、Migration Matrix、模板 frontmatter 示例。

## 7. 存量迁移

旧项目字段在 `devdocs.workspace_mode`（`chiaki-ng-dev` 已实测跑过，可能真实存在）。

探测时发现旧位置 → ⚠️ 列出并 AskUserQuestion 是否迁到 `workspace:` 块。一次性，之后幂等。

**不建独立迁移机器**：可重入入口已经覆盖这件事。这与 0.2 删掉的迁移手术性质不同——那是搬文件、造目录；这是同一文件内挪一个 yaml 键。

## 8. 复杂度账

| 项 | 增 | 减 |
|---|---|---|
| `skills/workspace-topology/`（SKILL + 2 references） | +约 450 行 | |
| `_shared/workspace-mode.md` | | −163 行 |
| `workspace-shell.md` | | −252 行 |
| 10 处消费方的复述内容 | | −约 60 行 |
| `agent-memory` 白名单 + 示例 | | −约 15 行 |
| `pipeline` / `retrofit` 传参管道 | | −约 8 行 |
| `constraints.md §10` | | −约 5 行 |
| **净** | | **约 −50 行** |

第 2 稿比第 1 稿多约 70 行（+380 → +450）：`logical_units` 输入契约、message 编号剥离白名单、`review_diff_sources` 重建规则都是 R1 修正引入的。净删从 −120 收窄到 −50。

新增的不是行数而是**一个 skill 边界**。换来的是：非 DevDocs 项目可用、拓扑知识单点收敛、10 处消费方对协议变更免疫。

## 9. 验证

本仓是规格库，无可跑的 drain。验证分两级：

**本仓（可立即做）**

1. `grep -rn "workspace_mode\|workspace-mode\|workspace-shell" skills/ docs/` —— 除历史 spec / 台账外零命中
2. `grep -rn "\.gitmodules" skills/ | grep -v workspace-topology` —— 零命中
3. **mode-derived 分支检查**：`grep -rn "mode.*shell\|shell.*mode" skills/ | grep -v workspace-topology` 逐条人工判读，确认无 skill 以 `mode` 做行为分支（codex R1 F-002：只 grep `.gitmodules` 兜不住语义泄漏，`workspace/no-bypass` 禁的是读声明，不禁 `if mode == shell`）
4. 新 SKILL.md ≤ 500 行（硬约束）
5. 死链检查：`workspace-shell.md` / `_shared/workspace-mode.md` 无残留引用
6. `realign --scope=health` 的 `dead-link` rule 全过

**真实项目（挂账，不阻塞本稿实施）**

7. 在 `chiaki-ng-dev`（已有 shell 声明）跑 `--check`，确认存量迁移提示与幂等
8. 在一个 inline 项目分别跑 `bugfix`（1 逻辑单元）与 `dev-workflow` 默认路径（2 逻辑单元），确认 `steps` 为恒等映射、提交形态与今天逐字节一致
9. 在 shell 项目跑一次完整 `dev-workflow` 提交，确认物理展开、`gate` 生效、占位符替换正确、子模块 message 编号已剥离

第 7–9 项与 [空 diff 修复的验证债](../../audits/2026-08-20-complexity-audit-backlog.md) 合并挂账。

## 10. 明确不做

| 不做 | 理由 |
|---|---|
| inline→shell 仓库手术（建外壳仓、搬文件、造 `<R>-dev` 目录） | 0.2；skill 只管当前文件夹内部 |
| `workspace-topology` 执行 `git commit` | 提交是干活 skill 的职责；让它执行意味着吃进 T-XX 编号与 Commit 1/2 语义，把刚拆开的 DevDocs 耦合从另一头接回去，且成为所有 inline 项目提交的必经之路 |
| 只在 shell 下委托提交（`if shell → 委托 / else → 自己提交`） | 那个 `if` 本身就是接口泄漏 |
| `docs_root` 做成可配置字段 | §3.1 |
| 把 `--plan-commits` 并进 `--check` | §2.2；`--plan-commits` 带提交前置门，会让流程开头的路径查询被提交时才相关的门阻塞 |
| topology 决定逻辑提交数 / 编号策略 | codex R1 F-004；三个消费方的提交形态与编号体系各不相同，调用方传 `logical_units`，topology 只做物理映射 |
| topology 输出 `mode` 供机器分支 | codex R1 F-002；输出能力（`capabilities`）而非模式，否则调用方必然写 `if mode == shell` |
| topology 压缩业务结论（`committed` / `docs_only_pending`） | codex R1 F-005；只返证据，判定归 `dev-workflow` |
| 嵌套子模块（vendor / 依赖项）进 `code_roots` 语义 | 沿用 `workspace-mode.v1` `workspace/no-nested-submodules`：依赖项的正确答案本就是「忽略」 |
| 「什么算源码」的静态白名单 | §4.3 |
| 移除代码根时 `git submodule deinit` / `git rm` | 破坏性动作交用户 |
| 为存量声明位置迁移建独立机器 | §7；可重入入口已覆盖 |

## 11. 待审查者重点质疑（R2）

R1 的 7 条（P1×4 / P2×2 / partial×1）全部确认并已修正，修正点见 §2.4–§2.6 各节开头的「第 1 稿…被判…」说明。R2 请集中攻击修正本身：

1. **占位符 `{{steps[N].sha}}` 是否真是泛型操作**（§2.5 要点 2）—— 它替掉了 `plan → finalize` 两阶段调用。调用方做替换时会不会仍需理解「为什么这一步的 message 里要塞前一步的 SHA」？如果会，泄漏没消除，只是换了形式。
2. **message 改写规则的安全性**（§2.5 要点 3）—— topology 剥掉子模块 message 里的编号型 trailer 是它唯一触碰文本的地方。白名单（`T-XX` / `BUG-XX` / `Review-Batch-Id`）是否够、会不会误剥调用方的业务 trailer。
3. **`review_diff_sources` 能否真从追溯枢纽重建**（§2.6 要点 2）—— 子模块 commit 刻意不带编号，重建完全依赖外壳仓 commit 正文里的 `web@<sha>` 行。这个正文由**调用方**写（topology 只提供占位符），那 topology 反过来解析它时，是否在依赖一个自己不控制的格式？
4. **`capabilities` 的封闭性**（§2.4）—— 当前只有 `code_docs_policy` 与 `single_logical_commit` 两项。是否存在第三个消费方需要、但两项都表达不了的能力，导致它退回 `mode` 分支。
5. **`worktree_changes` 同时服务任务开始扫描与提交前检查**（§2.4 要点 2）—— 两个时点对「不相关变更」的定义是否真的一致。
