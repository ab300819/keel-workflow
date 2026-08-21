# 抽取 workspace-topology：仓库拓扑从 DevDocs 解耦（add-only 批）

> 状态：**第 5 稿 · R4 二次熔断后拆分 · 待 R5** · 日期：2026-08-21
> 审查轨迹：R1 `39.5` → R2 `70.75`（**+79%**，🔴 熔断 → 用户决策「提交侧不做接口」）→ R3 `56.5`（**−20%**，codex 确认「塌缩本身正确」）→ R4 `74.5`（**+32%**，🔴 二次熔断）→ 用户决策「拆两个 spec」→ 本稿
> **配对 spec**：[shell 模式单仓假设审计](2026-08-21-shell-single-repo-assumptions-audit-design.md) —— 本稿刻意不含的那部分，cutover 的前置条件

## 0. 问题

`workspace_mode`（inline/shell 工作区拓扑）落地三个月后，用户在使用中报了两处结构性缺陷。

### 0.1 写者只在 DevDocs，读者却有非 DevDocs 的

字段声明在 `AGENTS.md` 的 **`devdocs:`** frontmatter 块内，探测入口只有三个，全属 DevDocs：`ms-pipeline init`、`ms-retrofit`、`realign --scope=layout`。而消费方里有三个明确声明「与 DevDocs 独立」的：

| 消费方 | 位置 | 原文自述 |
|---|---|---|
| `dev-flow` | `SKILL.md:133` | 非 DevDocs 通用执行器 |
| `e2e-test-flow` | `SKILL.md:48` | 「本 skill 与 DevDocs 独立，仅借该字段定位源码」 |
| `code-self-describe` | `SKILL.md:87` | 独立 skill |

后果双向：**难触发**——外壳形状但不跑 DevDocs 的项目无路声明；**误触发**——想声明就得跑 `init` / `retrofit`，顺带拉起需求编码、`docs/devdocs/` 脚手架、`agent-memory` 更新。

### 0.2 「仓库设定」会造一个新名字的外层目录

`workspace-shell.md` 的 inline→shell 迁移：Step 2 算 `W="${W:-$(dirname "$R")/${R_NAME}-dev"}`，Step 3 `mkdir -p "$W" && git init`，Step 4 从 remote URL **独立 clone** 一份 R 作子模块。结果是同一个仓在磁盘上有两份工作副本，用户此后工作的根目录变成 `<原名>-dev`。

这超出「声明一个仓库设定」该有的动作幅度——它是一次仓库手术，被挂在了规范维度下面。**判定：过度设计，删除。** skill 只管当前文件夹内部。

### 0.3 §4 / §5 自相矛盾（清点时发现）

`_shared/workspace-mode.md` §4 要「仓根下的**源码文件** → ⚠️」，§5 明确拒绝「静态白名单猜测什么算源码」。两条不能同时成立，裁决见 §4.3。

## 1. 本稿的范围边界（读之前先看这一节）

R4 二次熔断的根因（codex 原话）：**「仍以命令关键词代替『操作语义 × 消费方』的完整盘点」**。连续两轮试图补完「单仓算法迁移清单」的结果都是——更长的清单 + 新的类别。

**关键判断**：那 14+ 处单仓假设**今天就存在**于 `workspace-mode.v1`，即使永不抽这个 skill 也一样错。它们不是抽取**造成**的，是抽取**照出来**的。故独立立项。

| | 本稿（Spec A · add-only） | [Spec B · 单仓假设审计](2026-08-21-shell-single-repo-assumptions-audit-design.md) |
|---|---|---|
| 解决 | §0.1 / §0.2 / §0.3 | 14+ 处既存缺陷 |
| 语义 | **add-only**：只新增能力，不移除任何既有合法输入 | cutover：迁字段、`no-bypass` 升 ⛔、退休旧实现 |
| 爆炸半径 | 小，可独立发布 | 大 |

**add-only 的硬约束**（codex R4 F-307）：第一批若同时迁字段并启用 `no-bypass` 为 ⛔，那些旧算法会从「耦合但尚能工作」退化成**没有合法输入**。所以本稿：

- ⛔ **不移除** `devdocs.workspace_mode` / `code_roots` 的读取路径——`--check` 兼容读新旧两处
- ⛔ **不动** `_shared/workspace-mode.md`（提交 / 零污染 / gitlink 三面完全不碰）
- ⛔ **不改**任何消费方的**算法**，只改指针与字段解析入口
- ⛔ `workspace/no-bypass` 落为 **ℹ️ 建议级**，Spec B 完成后才升 ⛔
- ⛔ **不摘** `agent-memory` 受管白名单、**不摘** `layout-metadata-schema` 字段

## 2. 决策摘要

| # | 决策 | 依据 |
|---|------|------|
| a | 抽取独立 skill `workspace-topology`（非 `ms-` 前缀） | §0.1；仓库拓扑是仓库级事实，不是 DevDocs 事实 |
| b | 新增与 `devdocs:` 平级的独立 `workspace:` 块，**旧位置继续可读** | §0.1 的病根一半在「字段住在 `devdocs:` 里」；add-only |
| c | 删除 inline→shell 迁移手术（七步、约 170 行） | §0.2 |
| d | **提交侧不做接口**，`_shared/workspace-mode.md` 原样保留 | R2 熔断（§5）；codex R3 独立确认「塌缩本身是正确的」 |
| e | docs 根恒为 `<仓库根>/docs/`，不设字段、不可配置 | 310 处 `docs/devdocs` 硬编码的正确性建立在这条常量上 |
| f | 可重入四动作，幂等 | 用户需求：后期改 mode、加子模块 |
| g | 单仓算法迁移 → Spec B | §1；R4 F-302 / F-304 证明它不是可穷举清单 |

## 3. 接口契约

### 3.1 「依赖接口，而不是实现」及其边界

委托方不知道字段叫什么、不知道真源是 `.gitmodules`、不知道任何章节号，只知道调入口拿答案。可执行形式写进 `_shared/constraints.md §10`：

- `workspace/single-entry`：拓扑事实（代码根路径 / docs 根 / 能力 / 指针状态 / 工作区快照）入口为 `/workspace-topology --check`
- `workspace/default-inline`：缺省 inline；无声明的项目行为完全不变
- `workspace/no-bypass`（**本批为 ℹ️ 建议**）：不宜自行读取声明文件或解析 `.gitmodules`。Spec B 完成后升 ⛔

> ⚠️ **原则的适用边界（R2 熔断确立）**：这条原则对**查询**成立，对**跨仓提交编排**不成立。把提交侧也接口化需要一个分布式事务协议（持久 execution receipt + 结构化 message 对象 + gitlink tree transition 作 diff SSOT），代价与收益不成比例，账见 §5。提交协议 / 零污染 / gitlink 排除三面仍以规范条文形式留在 `_shared/workspace-mode.md`，消费方引用其条文是合法的。

### 3.2 入口：一个交互式 + 一个只读查询

| 入口 | 回答的问题 |
|---|---|
| `/workspace-topology` | 交互式维护声明（四动作，见 §6） |
| `--check` | 代码扫哪、docs 在哪、本 skill 该开该关、工作区什么状态、指针是否一致 |

**声明失配前置**：§4.4 的 ⛔ 行前置阻塞——拿不到可信拓扑，后面的答案都无意义。

第 2 稿曾有 `--plan-commits` 与 `--check --id`，R2 熔断后整体删除（§5）。第 1 稿曾有独立的 `--commit-status`，R1 F-003 判其缺乏独立失败语义。

### 3.3 摘要信封

作为子 Agent 被委托，返回 `yaml-summary-v1`（`constraints.md §2`），`skill: workspace-topology`。私有字段按 `yaml-summary/details-only-private` 落 `summary.details`。

### 3.4 `--check` 输出

```yaml
summary:
  headline: "shell 模式，2 个代码根（声明位于旧位置，建议迁移）"
  details:
    docs_root: docs
    declaration_site: legacy            # current | legacy | none —— 见要点 5
    scan_targets:
      - {label: web, path: web}
      - {label: api, path: api}         # inline 时为单项 {label: ".", path: "."}
    capabilities:
      code_dir_write_policy: source_and_tests_only   # unrestricted | source_and_tests_only
      code_metadata_write_policy: explicit_opt_in    # unrestricted | explicit_opt_in
    pointer_checks:
      - {label: web, recorded: e4f5g6h, actual: e4f5g6h, state: consistent}
      - {label: api, recorded: a1b2c3d, actual: f7a8b9c, state: drift_ahead}
    root_residue: []                    # 仓根下不在 docs/、不属任何 scan_target 的已跟踪文件（ℹ️）
    undeclared_submodules: []           # .gitmodules 有条目但未进声明 → ℹ️
    worktree_changes:                   # 按仓分组，gitlink 条目已在出口前滤掉
      - {label: web, path: web, changes: [src/a.ts]}
      - {label: ".", path: ".", changes: [docs/devdocs/00-context.md]}
```

六条契约要点：

1. **结构化输出里没有 `mode`**（codex R3 F-203）。第 2、3 稿把它留在 `summary.details` 并注「仅供人读」——那个注释**没有约束力**，字段在机器可读位置就会被拿去分支。它只出现在 `summary.headline` 的人读散文里。

2. **`capabilities` 两项，各管一件事**，映射为唯一真值表（codex R4 F-305）：

   | 拓扑 | `code_dir_write_policy` | `code_metadata_write_policy` |
   |---|---|---|
   | inline | `unrestricted` | `unrestricted` |
   | shell | `source_and_tests_only` | `explicit_opt_in` |

   topology 拥有**映射**，`_shared/workspace-mode.md` 拥有**行为语义**。枚举、映射或语义发生不兼容变化时同步 bump 两边 `spec_version`。

   为什么两项而非一项：`code-self-describe` 的文件头注释**写进源码文件本身**，按 `source_and_tests_only` 字面属「允许写入」，但按零污染红线应默认跳过——单靠写入策略推不出正确结论（codex R3 F-202）。而单项 `code_docs_policy` 又表达不了 `codebase-insight:158` 的「不往任何子模块写文件」：inline 时 `scan_targets = [{".", "."}]`，`docs/` 就在 `.` 里面，「不往 scan_target 写非代码文件」会**禁掉 inline 下写 `docs/`**。

3. **`worktree_changes` 是无状态快照**，不带 `snapshot_id`。R3 F-205 曾要求建 `workspace_baseline` 持久化基线（per-path `patch_fingerprint` + attribution + decision + 提交前硬门比对），**不采纳**——codex R4 复审此决定为「未发现问题」，理由：今天 `task-orchestration.md:136-147` 本就顺序扫 N+1 仓，聚合进 `--check` 并未新增原子快照要求。
   配套硬约束（codex R4 补充）：**每个决策点 / 洁净门必须重新调用 `--check`，⛔ 不得跨阶段缓存快照**。归属判定与忽略决定完全留在调用方，与今天**行为语义一致**（不宣称「逐字节一致」——聚合形态确有变化）。

4. **`pointer_checks` 让 health 不必读 mode**（codex R2 F-106）。`state` 枚举 = `consistent` | `drift_ahead`（子模块较新，漏 bump）| `drift_behind`（未 update）| `diverged`（互不包含）| `not_applicable`（inline）。三种漂移成因的处置命令在 `probe-and-repair.md`。

5. **`declaration_site` 是 add-only 的核心字段**。`current` = 声明在 `workspace:` 块；`legacy` = 声明在旧的 `devdocs.workspace_mode` / `code_roots`（**照读、不报错**，headline 附一句建议迁移）；`none` = 无声明 → inline。两处同时存在且冲突 → ⛔（见 §4.4）。Spec B 的 cutover 才把 `legacy` 升为 ⚠️、最终移除。

6. **`root_residue` / `undeclared_submodules` 是 ℹ️ 级事实**，不阻塞。后者补住 `realign-scope-layout.md:83` 的「未声明工作区模式」提示——改成委托后若不返这个字段，该提示会静默失效。

## 4. 声明 schema

```yaml
---
workspace:                     # 新增，与 devdocs: 平级
  mode: shell                  # 可选，枚举 inline|shell，缺省 inline
  code_roots: [web, api]       # mode=shell 时必填，≥1 项，元素为 .gitmodules 的 submodule name
devdocs:                       # DevDocs 项目才有；非 DevDocs 项目只有 workspace: 块
  docs_layout_version: layout.v1
  workspace_mode: shell        # ⚠️ legacy 位置，本批仍可读（add-only）
  code_roots: [web, api]       # ⚠️ 同上
  initialized_at: "2026-08-05"
---
```

### 4.1 docs 根是常量而非字段

- `workspace/docs-root`：文档根**恒为** `<仓库根>/docs/`，两种模式无差别，**不设字段、不可配置**。

理由：可配置就会漂，而仓内 **310 处**（2026-08-21 实测 `grep -ro "docs/devdocs" skills/ | wc -l`）硬编码引用的正确性正建立在这条常量上。`--check` 仍在 `details.docs_root` 里回答它——调用方拿常量，不是「不用问」。

### 4.2 写者归属：skill 自己写 `workspace:` 块

今天的写入链是「pipeline 探测 → 结果塞进 `devdocs_frontmatter` 入参 → `agent-memory --update` 代写」，两个 skill 才能落一个字段，因为 pipeline 不许写 `AGENTS.md`。

改为 **`workspace-topology` 直接写 `workspace:` 块**。归属划分：`agent-memory` 拥有正文 + `devdocs:` 块，`workspace-topology` 拥有 `workspace:` 块，**块级不相交**。

**add-only**：`agent-memory` 的受管白名单**不摘**旧字段。Spec A 落地后 `pipeline` / `retrofit` 不再传 `devdocs_frontmatter` 的 workspace 字段，该路径自然休眠而非冲突；正式摘除留给 Spec B。

### 4.3 §4 / §5 矛盾的裁决

裁掉「源码文件」判定：

- `workspace/root-residue`：`shell` 模式下，仓库根下不在 `docs/`、不属任何 `scan_target` 的**已跟踪文件** → ℹ️ 列清单，由用户判断。**不猜是不是源码，也不装作能猜。**

保留提示的价值（外壳仓不该有代码是真实约束），删掉它无法兑现的精确性。降 ⚠️→ℹ️ 是因为无法判定性质就不该要求确认。

> ℹ️ `_shared/workspace-mode.md` §5 的零污染违约检测有**同构矛盾**（要求判定「非源码路径」，同时禁止猜测什么算源码）。裁法一致（列清单交用户判断，不预判类别），但**该文件本批不动**（§1 add-only），此项归 Spec B。

### 4.4 校验（fail-closed）

| 情形 | 行为 |
|------|------|
| 无 `workspace:` 块且无 legacy 字段 | 视为 `inline` —— 存量项目零影响 |
| 仅 legacy 字段 | 照读，`declaration_site: legacy` + ℹ️ 建议迁移 |
| 两处同时存在且值不同 | ⛔ 阻塞，提示以哪处为准需用户裁决 |
| 两处同时存在且值相同 | 照读 `workspace:` 块，ℹ️ 提示可删 legacy |
| `shell` 但 `code_roots` 缺失 / 为空 | ⛔ |
| 某 name 不在 `.gitmodules` | ⛔，提示修声明 |
| name 在 `.gitmodules` 但工作区目录为空 | ⛔（运行时校验门）；health 只读扫描降级 ⚠️ |
| 解析出的两个 path 互为前缀（嵌套子模块） | ⛔ |
| 某 path 为 `.` / 含 `..` / 等于 `docs` | ⛔ |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略 |

## 5. 提交侧不做接口（R2 熔断结论）

第 2 稿有 `--plan-commits`（逻辑单元 → 物理步骤 + `{{steps[N].sha}}` 占位）与 `--check --id`（提交证据 + `review_diff_sources`）。**两节整体删除。**

**熔断数据**：R1 `39.5` → R2 `70.75`（**+79%**），8 条发现里 7 条源自这两节，其中 5 条是 R1 未闭合的复现、3 条是修正自身引入的新问题。

**根因**：把「提交编排」当成可封装的服务。跨仓提交本质是**有状态的分布式事务**——严格顺序、部分失败、SHA 依赖、恢复点。任何想用一次只读调用封住它的设计都会被迫长出事务管理器。

codex R3 独立确认该塌缩正确：「提交侧接口不是『第 2 稿实现得不好、换个形状就应继续做』，而是只有在明确愿意建设持久化跨仓事务执行器时才值得做」。本仓有同型先例：`markdown-style` 的自动修复白名单 27→9→4→0 整体放弃。

**塌缩后的分工**：

| 面 | 归属 | 消费方 |
|---|---|---|
| 声明维护、拓扑事实、指针状态 | `workspace-topology` | verify / test-run / codebase-insight / e2e-test-flow / health-lint / realign / pipeline / retrofit |
| N+1 提交协议、零污染红线、gitlink 排除 | `_shared/workspace-mode.md`（**本批不动**） | dev-workflow / bugfix / dev-flow / code-self-describe |

切分判据 + 三层归属（codex R3 F-201）：

| 层 | 归属 | 职责 | 不得做 |
|---|---|---|---|
| 事实层 | `workspace-topology` | 输出拓扑事实与派生能力 | 不解释能力的行为语义 |
| 规范层 | `_shared/workspace-mode.md` | **唯一**解释能力枚举的行为语义与通用红线 | 不写消费方专属决策 |
| 执行层 | 各消费 skill | 消费能力并执行 | 不重复解释策略、不自行推导应否跳过 |

## 6. 可重入四动作

**幂等判据**：读现状 → 若用户选「保持不变」，或调整后 frontmatter 与现状**逐字节相等** → 零文件写入，`details.changed: false`。

| 动作 | 语义 |
|---|---|
| 首次声明 / 重新探测 | 扫 `.gitmodules` → AskUserQuestion 多选代码根（提示语必须说明「子模块也可能是素材 / vendor，不都算代码根」）→ 全不选 = `inline`。无 `.gitmodules` 时静默判 `inline`，不打扰用户 |
| 切 mode（双向） | **声明跟随事实，不制造事实**。`inline→shell` 要求子模块已挂好；`shell→inline` 只删 `code_roots` 声明，子模块文件与 `.gitmodules` 一律不动 |
| 新增子模块 | `git submodule add <url> <path>` + 追加 `code_roots`。属「管文件夹内部」，不越界。也支持「子模块已存在、只补声明」 |
| 移除代码根 | **仅退声明**，绝不 `git submodule deinit` / `git rm` |
| （附）legacy 迁移 | 发现 `declaration_site: legacy` → ℹ️ 提示并可选迁到 `workspace:` 块。一次性，之后幂等。**不建独立迁移机器**——可重入入口已覆盖 |

**写入后自校验**：立即跑 §4.4 全表，任一 ⛔ → 回滚本次写入并报告。

**不自动提交**：只改工作区文件，`output_files` 列出改动 + `details.suggested_commit_message`。

## 7. 影响面

### 7.1 新建

```
skills/workspace-topology/
  SKILL.md                          定位 / 两入口 / 四动作 / 声明 schema / 校验表
  references/probe-and-repair.md    探测步骤 / 指针漂移三成因与处置
```

### 7.2 操作方（3 文件 · 改成委托）

- `pipeline/SKILL.md:208` —— 整段探测说明替换为 `Task: /workspace-topology`；停止传 `devdocs_frontmatter` 的 workspace 字段
- `retrofit/SKILL.md:177, 179` —— 同上；179 的「若上一步探测到工作区模式，一并写入」子句删除
- `realign-scope-layout.md:82–85 / 156 / 229` —— 82–85 改委托 `--check`（消费 `undeclared_submodules`）；**156 迁移路由整行删除**（§0.2）；229 修复项指针改新 skill

### 7.3 路径类消费方（只改指针与解析入口，⛔ 不改算法）

替换文本统一为：

> 代码根路径、docs 根与工作区快照委托 `/workspace-topology --check`。

| 文件 | 行 | 处置 |
|---|---|---|
| `verify/SKILL.md` | 136 | 消费 `scan_targets` + `root_residue`；⚠️→ℹ️（§4.3） |
| `test-run/SKILL.md` | 72 | 消费 `scan_targets`；「按 root 分组」改由 `len(scan_targets) > 1` 派生 |
| `codebase-insight/SKILL.md` | 152, 154 | 「仓间关系小节」同样改由 `len > 1` 派生——**比今天按 `mode` 判更准**（shell 单代码根时今天会错误地要求产出该小节） |
| `e2e-test-flow/SKILL.md` | 48 | 消费 `scan_targets` |
| `code-self-describe/SKILL.md` | 87, 89, 93 | 跳过决策改读 **`capabilities.code_metadata_write_policy`**（不是 `code_dir_write_policy`——codex R4 F-301：文件头注释属源码内元数据，写入策略枚举会错误放行它） |

### 7.4 提交类消费方（本批仅换路径解析入口）

`dev-flow:133` / `bugfix:288` / `dev-workflow:113, 300, 301, 313` / `task-orchestration.md:136, 145` / `verification-flow.md:344, 354` —— 这些位置**保留**对 `_shared/workspace-mode.md` 条文的引用，仅把「读 `AGENTS.md` 拿 `code_roots`」换成委托 `--check`。

> ⚠️ **本批刻意不动 `verification-flow.md:344/354` 的 `workspace_mode: shell` 分支**。codex R4 F-303 指出：若同时移走旧字段并启用 `no-bypass` 为 ⛔，该分支会失去合法触发依据。add-only 语义下 legacy 字段仍可读，故分支仍成立。该分支的正确重写（改用 `scan_targets`，并解释如何从外壳仓追溯枢纽解析不带 T-XX 的子模块 commit）归 Spec B。

### 7.5 health（2 文件）

- `health-lint-implementation.md:389, 391, 405` —— 适用性门与检测对象改为消费 `pointer_checks`；405 修复路径指针改 `probe-and-repair.md`
- `realign-scope-health.md:33, 95, 167` —— `not_applicable` 由 `pointer_checks[].state` 表达

### 7.6 治理与文档

- `_shared/constraints.md:9, 292–299` —— §10 按 §3.1 三条重写（`no-bypass` 为 ℹ️ 级）
- `layout/layout-metadata-schema.md:27, 28` —— **不摘字段**（add-only），只加一句「该维度已独立，新声明位置见 `/workspace-topology`」
- `docs/architecture.md:283–296`、`docs/workflows.md:333`、本仓 `AGENTS.md` 当前状态节

**不改**：`_shared/workspace-mode.md`、`agent-memory/SKILL.md` 白名单、`docs/superpowers/specs/2026-08-05-*`、`docs/audits/*`。

### 7.7 spec_version bump

| 文件 | 变更性质 | bump |
|---|---|---|
| `_shared/constraints.md` | §10 结构重写 | `shared-constraints.v4` → `v5` |
| 新 skill | 新建 | `workspace-topology.v1` |
| `layout-metadata-schema.md` | 仅加一行指针 | **不 bump**（`realign/no-bump-copyedit`） |

按 `realign/bump-sync-three-places`，bump 时同步 `references/realign.md` 当前常量、Migration Matrix、模板 frontmatter 示例。

## 8. 复杂度账

| 项 | 增 | 减 |
|---|---|---|
| `skills/workspace-topology/`（SKILL + 1 reference） | +约 240 行 | |
| `workspace-shell.md` 迁移七步 + 逐步命令 + 迁移失败恢复 | | −约 170 行 |
| ↳ 存活内容改指针指向 `probe-and-repair.md` | +约 10 行 | |
| `realign-scope-layout.md:156` 迁移路由行 | | −1 行 |
| `pipeline` / `retrofit` 传参管道 | | −约 8 行 |
| `constraints.md §10` | | −约 3 行 |
| **净** | **约 +68 行** | |

四稿的账：−120 → −50 → −40 → +2 → **本稿 +68**。

数字变正的原因不是方案膨胀，而是**范围诚实了**：前四稿的负数依赖「删掉 `_shared/workspace-mode.md`」（第 2 稿）或「消费方复述全删」（第 3 稿），而这两项在 add-only 语义下都不成立。本稿实际删的只有迁移手术那 170 行，加的是一个新 skill 的本体——**新增一个 skill 边界就是要花行数的**，换来的是非 DevDocs 项目可用、拓扑事实单点收敛。

## 9. 验证

本仓是规格库，无可跑的 drain。

**本仓（可立即做）**

1. **旧手册零命中**：`grep -rn "workspace-shell" skills/` —— 现役消费方零命中（历史 spec / 台账不计）
2. **`.gitmodules` 引用 allowlist**（codex R4 F-306 修正）：合法出现位置仅 `skills/workspace-topology/**` 与 `_shared/constraints.md` 的 `workspace/no-bypass` 条文本身（**规范提及**）。其余文件出现即为**自行解析**，须逐条判读。⚠️ 不要写成「除 topology 外零命中」——那会把 `no-bypass` 条文自身判为违规
3. **`_shared/workspace-mode.md` 引用者 allowlist**：`dev-workflow` / `bugfix` / `dev-flow` / `code-self-describe` / `_shared/constraints.md`（后者必然引用，第 4 稿的白名单漏了它——codex R4 F-306）
4. **正向能力检查**：逐个路径类消费方确认其文本显式使用 `scan_targets` / `worktree_changes` / `pointer_checks` / `capabilities` 之一。反向 grep `mode` 抓不到「读 `code_roots` 后自己分支」「给 `mode` 起别名」「完全不读声明直接在仓根跑 git」三类绕过（codex R3 F-203）
5. **`capabilities` 真值表一致性**：`code-self-describe` 读 `code_metadata_write_policy`（非 `code_dir_write_policy`）
6. 新 SKILL.md ≤ 500 行（硬约束）
7. `realign --scope=health` 的 `dead-link` rule 全过

**真实项目（挂账，不阻塞本稿实施）**

8. 在 `chiaki-ng-dev`（声明在 legacy 位置）跑 `--check`，确认 `declaration_site: legacy`、照读不报错、迁移提示出现、迁移后幂等
9. 在一个 inline 项目跑 `--check`，确认 `scan_targets` 为单项 `.`、两项 capability 均 `unrestricted`、`docs/` 写入不被误禁
10. `pointer_checks` 与 `git submodule status` 逐条一致

## 10. 明确不做

| 不做 | 理由 |
|---|---|
| inline→shell 仓库手术 | §0.2 |
| 封装提交侧（`--plan-commits` / 提交证据 / `review_diff_sources`） | §5；R2 熔断，需要跨仓事务协议 |
| `workspace-topology` 执行 `git commit` | 提交是干活 skill 的职责 |
| topology 改写 commit message（剥离编号 trailer） | codex R2 F-103/F-105：只删不迁会让 `Review-Batch-Id` 从追溯枢纽消失，7 个 trailer 里 5 个不在白名单会泄漏进上游；文本剥离无安全语法边界 |
| topology 输出 `mode` 供机器分支 | codex R1 F-002 / R2 F-106 / R3 F-203 |
| 建 `workspace_baseline` 持久化基线 | codex R3 F-205 的建议，R4 复审确认不采纳。该缺口今天就存在；本稿只把扫描接口化 |
| 源码 / 测试路径分类器 | §4.3 |
| **单仓算法迁移（14+ 处）** | §1；→ Spec B。它不是可穷举清单，两轮试图补完都产出更长的清单 + 新类别 |
| **移除 legacy 声明位置 / `no-bypass` 升 ⛔ / `_shared` 瘦身 / `agent-memory` 摘白名单** | §1 add-only 硬约束；→ Spec B 的 cutover 批 |
| 把「引用者 allowlist」做成通用 health-lint rule | codex R4 F-306：那是面向普通 DevDocs 项目的机制，本仓专用检查用可复制 `rg` 命令即可；若坚持做 rule，须在不存在 `skills/workspace-topology/` 时返回 `not_applicable` |
| 移除代码根时 `git submodule deinit` / `git rm` | 破坏性动作交用户 |

## 11. 待审查者重点质疑（R5）

R4 的 7 条处置：F-301（`code-self-describe` 改读 `code_metadata_write_policy`，§7.3）、F-302 / F-304（→ Spec B）、F-303（`verification-flow` 分支本批不动，§7.4）、F-305（真值表，§3.4 要点 2）、F-306（allowlist 修正，§9 项 2–3）、F-307（add-only + 原子 cutover 两批，§1）。

R5 请攻击：

1. **add-only 是否真的 add-only** —— 本稿仍删了迁移七步（§0.2）、删了 `realign-scope-layout.md:156`、改了 5 处路径类消费方的解析入口。这些是「新增」吗？有没有哪一处会让某个今天能工作的路径失去合法输入？
2. **两处声明并存期的语义是否完备**（§4.4）—— 值相同 / 值不同 / 只有一处 / 都没有，四种情形是否穷尽。`code_roots` 是列表，「值不同」的判据是集合相等还是顺序相等？
3. **Spec A 单独落地后 shell 项目是否处于比今天更差的中间态** —— 这是 R4 F-307 的原始担忧。本稿用 add-only 回应，请验证这个回应是否充分。
4. **`--check` 的调用频次约束是否可执行**（§3.4 要点 3）—— 「每个决策点 / 洁净门必须重新调用，不得跨阶段缓存」。规范文件里写这句话，实际执行时如何验证没有缓存？
5. **复杂度账转正是否可接受**（§8）—— 净 +68 行换「非 DevDocs 项目可用 + 拓扑事实单点收敛」。这笔账在本仓的复杂度预算下成立吗，还是说 §0.1 有更便宜的解法（例如只把字段从 `devdocs:` 块提到顶层、不抽 skill）？
