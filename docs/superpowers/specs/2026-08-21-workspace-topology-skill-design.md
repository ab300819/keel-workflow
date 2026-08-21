# 抽取 workspace-topology：仓库拓扑从 DevDocs 解耦为独立 skill

> 状态：**第 1 稿 · 待 codex 审查** · 日期：2026-08-21
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
| e | skill 保持**只读**：算分组、跑只读门，不执行 `git commit` | 提交由干活的 skill 做；skill 不吃 DevDocs 编号语义 |
| f | 删除 inline→shell 迁移手术（七步、约 170 行） | 0.2 |
| g | docs 根恒为 `<仓库根>/docs/`，不设字段、不可配置 | 280 处 `docs/devdocs` 硬编码的正确性建立在这条常量上 |
| h | 可重入四动作，幂等 | 用户需求：后期改 mode、加子模块 |

## 2. 接口契约

### 2.1 「依赖接口，而不是实现」

本稿的核心约束。第 1 稿曾把 10 处消费方指向 `_shared/workspace-mode.md` 的**具体章节**（§ N+1 仓提交协议、§ 校验规则、§7.2 gitlink 判据），被否决：协议一改，10 处跟着改，接口等于没抽。

**修正后**：委托方不知道字段叫 `workspace.mode`、不知道真源是 `.gitmodules`、不知道任何章节号，只知道调入口拿答案。

这条原则有一个可执行形式，写进 `_shared/constraints.md §10`：

- `workspace/no-bypass`：任何需要代码根路径、docs 根、提交分组或提交状态的 skill 一律委托 `/workspace-topology`，**⛔ 不得自行读取声明文件或解析 `.gitmodules`**。

没有这条禁令，下一个 skill 又会去 grep `AGENTS.md`。

### 2.2 入口

一个交互式入口 + 三个只读查询。三个查询**不合并**，因为它们回答不同的问题、在不同时点被问、失败语义不同。

| 入口 | 回答的问题 | 被问的时点 | ⛔ 条件 |
|---|---|---|---|
| `/workspace-topology` | （交互式维护声明，见 §5） | 用户显式 / init / retrofit | 写入后自校验失败 |
| `--check` | 代码在哪、docs 在哪、当前什么 mode | 流程开头 | 仅声明失配 |
| `--commit-status --id <ID>` | 这个编号的提交是否完整落地 | 断点续做判定 | 无（返回状态而非阻塞） |
| `--plan-commits` | 这批变更该怎么分组提交 | 提交前 | 提交前置门失败 |

**三个查询共有的前置**：声明失配（§3.3 的 ⛔ 行）在三个查询上**一律前置阻塞**——拿不到可信的拓扑，后面的答案都无意义。表中「⛔ 条件」列指的是该查询**额外**引入的阻塞条件。

**为什么 `--check` 不能吃下 `--plan-commits`**：`test-run` 在流程开头问「代码在哪」，不该被一个提交时才相关的 detached HEAD 门挡住。**问题不同、失败语义不同，就不共用入口。**

> ⚠️ 三个 flag 是本稿最可能被判过度的地方（本仓刚把 flag 从 49 收到 20）。合并任意两个都会导致失败语义混淆或调用方分支，见 §10 的取舍记录。请审查者重点质疑此处。

### 2.3 摘要信封

作为子 Agent 被委托，返回 `yaml-summary-v1`（`constraints.md §2`），`skill: workspace-topology`。私有字段按 `yaml-summary/details-only-private` 一律落 `summary.details`：

```yaml
skill: workspace-topology
status: success
summary:
  headline: "shell 模式，2 个代码根"
  details:
    mode: shell
    docs_root: docs
    code_roots:
      - {name: web, path: web}
      - {name: api, path: api}
    changed: false
blockers: []
output_files: []
```

`--check` 在 `inline` 项目上的返回：`mode: inline` / `docs_root: docs` / `code_roots: [{name: ".", path: "."}]`。**调用方不分支**——inline 也是一个代码根，路径为 `.`。

### 2.4 `commit_grouping` 契约

`--plan-commits` 的核心产出。分组长度 = 代码根数 + 1；**inline 项目拿到 2 项**（代码 + 文档，路径均为 `.`），与今天的「Commit 1 代码 + Commit 2 文档」逐字节等价。

```yaml
summary:
  details:
    single_commit_allowed: false      # inline: true（可合并两项）；shell: false（跨仓无法合并）
    commit_grouping:
      - repo: web
        path: web
        role: code
        gate: ok                      # ok | blocked
        message_style: inherit        # 沿用该仓自身提交历史风格
        carries_id: false             # 编号对上游是噪声
        worktree_changes: [src/a.ts]  # 已排除 gitlink 条目
        pollution_findings: []        # 非源码/测试路径的变更
      - repo: api
        path: api
        role: code
        gate: blocked
        gate_recovery: |
          ⛔ 禁止继续：子模块 api 处于 detached HEAD，此状态下提交会产生游离 commit
          恢复方式：
          - 动作：git -C api checkout <branch>（若已误提交，先 git -C api branch <tmp> <sha> 保住 commit 再切）
          - 执行者：用户
          - 验证：git -C api symbolic-ref -q HEAD 输出 refs/heads/<branch>
          - 下一步：重跑 /workspace-topology --plan-commits
        ...
      - repo: .
        path: .
        role: shell
        gate: ok
        message_style: conventional
        carries_id: true
        bump_pointers: [web, api]     # inline 时为 []
        worktree_changes: [docs/devdocs/00-context.md]
```

调用方跑一个**与模式无关**的统一循环：`for g in commit_grouping: commit(g)`。没有 `if shell`，没有章节引用。

三条设计要点：

1. **门在算分组时就跑掉**，结果落 `gate` 字段。门不合格 → `status: failed` + `blockers`，调用方连循环都进不去。调用方不需要知道 detached HEAD 是什么概念，只看 `gate` 和一句现成的恢复指令。
2. **Recovery 预置在每一项里**（按 `constraints.md §7` 四字段完整模板，运行时输出禁用简写）。调用方失败时照着走，不回头再问 skill——skill 保持无状态只读。
3. **`worktree_changes` 已排除 gitlink 条目**。这使 `workspace-mode.v1` 的 `workspace/no-stash-gitlink`（「绝不给 gitlink 条目提供 stash 选项」）**在接口层自然消失**——条目根本不出现在调用方视野里，无从误提供。原协议 §7.1 那 30 行「porcelain v1 与 --short 的字节级差异」实测记录降级为 skill 内部实现笔记。

`single_commit_allowed` 让调用方的 `--single-commit` flag 无需知道模式：`false` 时忽略该 flag 并 ℹ️ 提示。

### 2.5 `--commit-status` 契约

`dev-workflow` 断点续做需判定「T-XX 是否已提交」。shell 下这个判定比 inline 复杂（外壳仓存在带该编号的 commit **且** body 记录的子模块 SHA 与当前指针一致），该复杂度不得泄漏给调用方。

```yaml
summary:
  details:
    id: T-07
    committed: true | false | drifted
    shell_commit: a1b2c3d           # inline 时即仓库自身的 commit
    pointer_check: [{name: web, recorded: e4f5g6h, actual: e4f5g6h, match: true}]
```

`drifted` = 外壳仓有该编号的 commit 但指针不一致。调用方对 `drifted` 的动作：进证据复核，不直接跳过（沿用今天 `dev-workflow` 的第五维语义，只是判定搬进了 skill）。inline 项目永不返回 `drifted`。

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

理由：可配置就会漂，而仓内 280 处 `docs/devdocs` 硬编码引用的正确性正建立在这条常量上。`--check` 仍在 `details.docs_root` 里回答它——调用方拿常量，不是「不用问」。

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
| `dev-workflow/SKILL.md` | 113, 300, 301, 313 | **复述** N+1 拆分规则、detached HEAD 门、五重状态检测 | **复述全删**，换委托句 + 消费 `commit_grouping` / `--commit-status` |
| `dev-workflow/references/task-orchestration.md` | 136, 145 | **复述**五重检测 + gitlink 判据 | **复述全删**，换委托句 |
| `dev-workflow/references/verification-flow.md` | 354 | **复述**逐 `code_root` 拼接 | **复述全删**；drain 侧 diff 源改为按 `commit_grouping` 逐项取 |

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
| `skills/workspace-topology/`（SKILL + 2 references） | +约 380 行 | |
| `_shared/workspace-mode.md` | | −163 行 |
| `workspace-shell.md` | | −252 行 |
| 10 处消费方的复述内容 | | −约 60 行 |
| `agent-memory` 白名单 + 示例 | | −约 15 行 |
| `pipeline` / `retrofit` 传参管道 | | −约 8 行 |
| `constraints.md §10` | | −约 5 行 |
| **净** | | **约 −120 行** |

新增的不是行数而是**一个 skill 边界**。换来的是：非 DevDocs 项目可用、拓扑知识单点收敛、10 处消费方对协议变更免疫。

## 9. 验证

本仓是规格库，无可跑的 drain。验证分两级：

**本仓（可立即做）**

1. `grep -rn "workspace_mode\|workspace-mode\|workspace-shell" skills/ docs/` —— 除历史 spec / 台账外零命中
2. `grep -rn "\.gitmodules" skills/ | grep -v workspace-topology` —— 零命中（`workspace/no-bypass` 的机械可查形式）
3. 新 SKILL.md ≤ 500 行（硬约束）
4. 死链检查：`workspace-shell.md` / `_shared/workspace-mode.md` 无残留引用
5. `realign --scope=health` 的 `dead-link` rule 全过

**真实项目（挂账，不阻塞本稿实施）**

6. 在 `chiaki-ng-dev`（已有 shell 声明）跑 `--check`，确认存量迁移提示与幂等
7. 在一个 inline 项目跑 `--plan-commits`，确认分组 2 项、行为与今天逐字节一致
8. 在 shell 项目跑一次完整 `dev-workflow` 提交，确认 N+1 展开与 `gate` 生效

第 6–8 项与 [空 diff 修复的验证债](../../audits/2026-08-20-complexity-audit-backlog.md) 合并挂账。

## 10. 明确不做

| 不做 | 理由 |
|---|---|
| inline→shell 仓库手术（建外壳仓、搬文件、造 `<R>-dev` 目录） | 0.2；skill 只管当前文件夹内部 |
| `workspace-topology` 执行 `git commit` | 提交是干活 skill 的职责；让它执行意味着吃进 T-XX 编号与 Commit 1/2 语义，把刚拆开的 DevDocs 耦合从另一头接回去，且成为所有 inline 项目提交的必经之路 |
| 只在 shell 下委托提交（`if shell → 委托 / else → 自己提交`） | 那个 `if` 本身就是接口泄漏 |
| `docs_root` 做成可配置字段 | §3.1 |
| 合并三个只读 flag | §2.2；合并会导致失败语义混淆（`--check` 被提交门阻塞）或调用方分支 |
| 嵌套子模块（vendor / 依赖项）进 `code_roots` 语义 | 沿用 `workspace-mode.v1` `workspace/no-nested-submodules`：依赖项的正确答案本就是「忽略」 |
| 「什么算源码」的静态白名单 | §4.3 |
| 移除代码根时 `git submodule deinit` / `git rm` | 破坏性动作交用户 |
| 为存量声明位置迁移建独立机器 | §7；可重入入口已覆盖 |

## 11. 待审查者重点质疑

1. **三个只读 flag 是否过度**（§2.2）—— 本仓刚把 flag 从 49 收到 20，这是最可能被判过度的地方
2. **`--commit-status` 的 `drifted` 状态是否该由 skill 判定** —— 它接近「业务判定」而非「拓扑判定」
3. **两个写者共存 `AGENTS.md`**（§3.2）—— 块级不相交是否足够，还是该保留单写者
4. **inline 项目拿到 2 项分组** 是否真与今天逐字节一致（§2.4），有无遗漏的今日行为
5. **`workspace/no-bypass` 的可执行性** —— §9 第 2 项的 grep 是否足以兜住，还是需要 health-lint rule
