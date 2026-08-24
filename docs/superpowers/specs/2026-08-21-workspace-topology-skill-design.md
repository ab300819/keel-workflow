# 抽取 workspace-topology：把工作区声明维护从 DevDocs 触发链上摘下来

> 状态：**第 6 稿（最小可行）· 待 R6** · 日期：2026-08-21（第 6 稿 08-24）
> **配对 spec**：[shell 模式单仓假设审计 + 拓扑查询接口](2026-08-21-shell-single-repo-assumptions-audit-design.md)
> 审查轨迹：R1 `39.5` → R2 `70.75`（🔴 熔断，提交侧不做接口）→ R3 `56.5`（codex 确认塌缩正确）→ R4 `74.5`（🔴 二次熔断，拆两 spec）→ R5 `90`（🔴 安全上限；F-404 机械证明 `--check` 委托在当前工具权限下不成立）→ 用户决策「最小可行方案」→ 本稿

## 0. 问题

`workspace_mode`（inline/shell 工作区拓扑，2026-08-05 落地）在使用中暴露三处缺陷。

### 0.1 声明动作绑死在 DevDocs 触发链上

用户原话：

> 「『仓库设定』是绑定 devdocs，在其他流程中会难以触发或误触发 devdocs 流程」

探测入口只有三个，全属 DevDocs：`ms-pipeline init`（`ms-requirements` 之后）、`ms-retrofit`（改造成功后）、`realign --scope=layout`。而消费方里有三个明确声明「与 DevDocs 独立」的：`dev-flow:133`、`e2e-test-flow:48`（原文「本 skill 与 DevDocs 独立，仅借该字段定位源码」）、`code-self-describe:87`。

后果双向：**难触发**——外壳形状但不跑 DevDocs 的项目无路声明；**误触发**——想声明就得跑 `init` / `retrofit`，顺带拉起需求编码、`docs/devdocs/` 脚手架、`agent-memory` 更新。

> ⚠️ **本稿刻意不动字段的 YAML 位置。** 第 1–5 稿把「字段住在 `devdocs:` 块里」当成本问题的「病根一半」，那是**设计者加的诊断，不是用户的诉求**。这条加戏引出新声明位置 → legacy 兼容 → current-only 回归（R5 F-403）→ `no-bypass` → 撞上 Task 权限（R5 F-404），是五轮复杂度的主要来源之一。用户抱怨的是**触发**，不是嵌套。

### 0.2 「仓库设定」会造一个新名字的外层目录

`workspace-shell.md` 的 inline→shell 迁移：Step 2 算 `W="${W:-$(dirname "$R")/${R_NAME}-dev"}`，Step 3 `mkdir -p "$W" && git init`，Step 4 从 remote URL **独立 clone** 一份 R 作子模块。结果是同一个仓在磁盘上有两份工作副本，用户此后工作的根目录变成 `<原名>-dev`。

用户原话：「该『仓库设定』会修改最外层目录名，按正常节奏不应该修改」。

**判定：不是「迁移不该存在」，而是「迁移不该是声明设定的隐藏副作用，且不该由 skill 擅自决定外层目录路径」。** 修法：迁移改为**显式的、双模式的、路径由用户定**的独立操作（§5）。原七步删除重写。

### 0.3 §4 / §5 自相矛盾

`_shared/workspace-mode.md` §4 要「仓根下的**源码文件** → ⚠️」，§5 明确拒绝「静态白名单猜测什么算源码」。两条不能同时成立。

## 1. 范围：五件事，消费方零改动

| # | 动作 | 解决 |
|---|---|---|
| 1 | 新建 `workspace-topology` skill = **交互式声明维护**（四动作、幂等、校验、`.gitmodules` 探测），写**现有字段位置** | §0.1 |
| 2 | 删除 inline→shell 迁移七步及其 realign 路由 | §0.2 |
| 3 | `pipeline` / `retrofit` / `realign --scope=layout` 的探测改委托该 skill | §0.1 反向 |
| 4 | 裁掉「什么算源码」的猜测 | §0.3 |
| 5 | inline→shell 迁移重写为**双模式显式操作**（§5） | §0.2 |

**⛔ 明确不在本稿范围**（→ 配对 spec）：`--check` 拓扑查询接口、`workspace/no-bypass`、字段位置迁移、任何消费方改动、25 处单仓假设、`_shared/workspace-mode.md` 的任何改动。

### 1.1 为什么消费方零改动 —— R5 的机械证据

第 5 稿要求路径类消费方委托 `/workspace-topology --check`。实测 `allowed-tools`：

```
retrofit             ⛔ 无 Task        e2e-test-flow    有 Task
verify               ⛔ 无 Task        dev-workflow     有 Task
test-run             ⛔ 无 Task        pipeline         有 Task
codebase-insight     ⛔ 无 Task
code-self-describe   ⛔ 无 Task
```

**六个路径类消费方里五个物理上无法派发子 Agent**，而自己读声明又是 `no-bypass` 禁止的。整个委托架构在当前工具权限模型下不成立，除非同时给五个只读 skill 开子 Agent 派发权——那是个比本方案本身更大的治理变更（R5 F-404）。

本稿要委托的三个入口（`pipeline` / `retrofit` / `realign` 由 pipeline 承载）**都有 Task**，已验证。

**连带消失的 R5 阻塞项**：F-403（current-only 回归）随「字段位置不变」消失；F-404 随「消费方零改动」消失；F-405 / F-406 / F-407 全是 `--check` 输出契约的问题，随之消失。

### 1.2 breaking change 的边界

本稿不用「add-only」为自己背书——第 5 稿那么做过，被判名不副实（R5 F-401）。诚实说明：

- **迁移七步删除重写**（§5）。旧实现的两个致命缺陷（前置门挡住唯一真实场景、Step 4 从远端重 clone 丢工作）意味着它对目标场景本就不可用，重写不是回退。
- `workspace-shell.md` **文件删除**。存活内容（探测步骤、detached HEAD 处置、指针漂移三成因）搬进 `references/probe-and-repair.md`，引用者改指针。
- 其余一切不变：字段位置、消费方、`_shared/workspace-mode.md` 正文、`agent-memory`。

## 2. skill 定位与接口

**定位**：独立 skill（非 `ms-` 前缀），职责单一——维护工作区拓扑声明。不读 `docs/devdocs/`，不碰任何业务文档，**不对外提供查询接口**（那是配对 spec 的事）。

**入口**：`/workspace-topology`，无 flag。交互式：读现状 → 展示 → AskUserQuestion 选动作。

**输出**：`yaml-summary-v1`（`constraints.md §2`），`skill: workspace-topology`，私有字段落 `summary.details`：

```yaml
summary:
  headline: "shell 模式，2 个代码根（无改动）"
  details:
    mode: shell
    code_roots: [{name: web, path: web}, {name: api, path: api}]
    changed: false
    validation: []            # §3.2 校验表的 findings
    root_residue: []          # §3.3
    pointer_checks: []        # 指针一致性，供人读与 health 提示
blockers: []
output_files: []
```

调用方（`pipeline` / `retrofit`）只需要知道「跑完了、有没有 blocker」，不消费 `details` 做分支——**本稿不建立任何机器消费契约**。

## 3. 声明与校验

### 3.1 字段位置不变

```yaml
---
devdocs:
  docs_layout_version: layout.v1
  workspace_mode: shell        # 位置不变
  code_roots: [web, api]       # 位置不变，元素为 .gitmodules 的 submodule name
  initialized_at: "2026-08-05"
---
```

非 DevDocs 项目会得到一个**只含这两字段的部分 `devdocs:` 块**。这不是本稿发明的——`workspace-shell.md` 探测第 5 步今天就明文规定了这个形态，并说明它「是合法的既知状态，不是意外」，消费方不得当 ⛔ 处理。

**写者**：`workspace-topology` 直接写。今天的链路是「pipeline 探测 → 塞进 `devdocs_frontmatter` 入参 → `agent-memory --update` 代写」，两个 skill 才落一个字段，因为 pipeline 不许写 `AGENTS.md`。新 skill 自己有写权限，链路缩短一环。

**`agent-memory` 的受管白名单不动**——`pipeline` / `retrofit` 不再传 workspace 字段后该路径自然休眠，不冲突。移除留给配对 spec。

- `workspace/docs-root`：文档根**恒为** `<仓库根>/docs/`，两种模式无差别，不设字段、不可配置。理由：可配置就会漂，而仓内 **310 处**（2026-08-21 实测）`docs/devdocs` 硬编码引用的正确性建立在这条常量上。

### 3.2 校验（fail-closed，沿用现有全表）

| 情形 | 行为 |
|------|------|
| 无 `workspace_mode` 字段 | 视为 `inline` —— 存量项目零影响 |
| `shell` 但 `code_roots` 缺失 / 为空 | ⛔ |
| 某 name 不在 `.gitmodules` | ⛔，提示修声明 |
| `code_roots` 有重复 name | ⛔（第 5 稿 R5 F-406 补入） |
| name 在 `.gitmodules` 但工作区目录为空（未 `submodule update --init`） | ⛔（运行时校验门）；health 只读扫描降级 ⚠️ |
| 解析出的两个 path 互为前缀（嵌套子模块） | ⛔ |
| 某 path 为 `.` / 含 `..` / 等于 `docs` | ⛔ |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略 |

`code_roots` 比较一律按**集合**语义，顺序无意义（R5 F-406）。

### 3.3 §0.3 的裁决

- `workspace/root-residue`：`shell` 模式下，仓库根下不在 `docs/`、不属任何 `code_roots` 的**已跟踪文件** → ℹ️ 列清单，由用户判断。**不猜是不是源码，也不装作能猜。**

保留提示的价值（外壳仓不该有代码是真实约束），删掉它无法兑现的精确性。降 ⚠️→ℹ️ 是因为无法判定性质就不该要求确认。

> ℹ️ `_shared/workspace-mode.md` §5 的零污染违约检测有**同构矛盾**（要求判定「非源码路径」，同时禁止猜测什么算源码）。裁法应一致，但**本稿不动该文件**，此项归配对 spec。

## 4. 可重入四动作（声明维护）

**幂等判据**：读现状 → 若用户选「保持不变」，或调整后 frontmatter 与现状**逐字节相等** → 零文件写入，`details.changed: false`。

| 动作 | 语义 |
|---|---|
| 首次声明 / 重新探测 | 扫 `.gitmodules` → AskUserQuestion 多选代码根（提示语必须说明「子模块也可能是素材 / vendor，不都算代码根」）→ 全不选 = `inline`。无 `.gitmodules` 时静默判 `inline`，不打扰用户 |
| 切 mode（双向） | **声明跟随事实，不制造事实**。`inline→shell` 要求子模块已挂好；`shell→inline` 只删 `code_roots` 声明，子模块文件与 `.gitmodules` 一律不动 |
| 新增子模块 | `git submodule add <url> <path>` + 追加 `code_roots`。属「管文件夹内部」，不越界。也支持「子模块已存在、只补声明」 |
| 移除代码根 | **仅退声明**，绝不 `git submodule deinit` / `git rm` |

**写入后自校验**：立即跑 §3.2 全表，任一 ⛔ → 回滚本次写入并报告。

**不自动提交**：只改工作区文件，`output_files` 列出改动 + `details.suggested_commit_message`。

## 5. inline→shell 迁移（双模式）

### 5.1 触发与两个模式

**仅由用户显式意图触发**（如「把这个项目转成外壳模式」），从交互式入口选择。skill **永不主动提议**——那是产品决策，不是规范差距。

进入后第一件事是 AskUserQuestion 选模式，分界在**谁把代码仓挪进根目录**这个物理动作：

| 步骤 | 手动模式 | 自动模式 |
|---|---|---|
| 状态盘点（§5.2） | skill | skill |
| 建根目录、把代码仓挪进去 | **用户**（skill 给出精确命令 + 保存迁移计划文件） | **skill** |
| `git init` 根仓库 + 首次 commit | skill | skill |
| 挂子模块 | skill | skill |
| 提取 DevDocs 文档到根仓库 | skill | skill |
| 从代码仓清掉 DevDocs 产物 | skill | skill |
| 优化代码提交历史（§5.3） | skill | skill |
| 写 `workspace_mode` 声明 | skill | skill |
| 子模块切具名分支 | skill | skill |

**手动模式的上下文保存**：skill 输出一份**迁移计划文件**（盘点结果 + 待办步骤 + 已确认项），落在用户指定路径或系统临时目录，**不进任何仓**。用户建好目录后重新调 skill 并指向该文件即可续做。

### 5.2 状态盘点取代前置门

被删的七步有一道 Step 1 前置门：`git status --porcelain` 非空 ⛔、`rev-list @{u}..HEAD` 非 0 ⛔。**这道门会把唯一真实场景挡在门外**——clone 开源项目并用 DevDocs 开发过，状态必然是「工作区有未提交改动」或「有未推送提交」二选一。

改为**盘点后分支处理**，不阻塞：

```bash
git -C <R> status --porcelain              # DevDocs 产物在工作区？
git -C <R> log --oneline <base>..HEAD      # 已提交？
git -C <R> remote -v                       # remote 是上游还是自己的 fork？
```

三种形态分别对应 §5.3 的不同处置。**唯一保留的 ⛔**：目标根目录已存在且非空。

### 5.3 优化代码提交历史

范围含两件事：**摘掉 DevDocs 痕迹** + **把散乱开发提交整理成可提 PR 的序列**。

#### 三条硬安全线

1. **改写范围 = 只有你自己的提交**：`git merge-base <upstream>/<default-branch> HEAD`..HEAD。**上游历史零改动**。无 upstream remote（纯本地）时由用户指定基线 commit。
2. **改写前强制备份**：`git branch backup/pre-migrate-<timestamp>`，并在报告里给出回滚命令。⛔ 备份失败不得继续。
3. **改写后内容断言**：`git diff <backup> HEAD -- . ':!docs/devdocs' ':!docs/prd' ':!docs/codebase-insight.md' ':!AGENTS.md'` **必须为空**——即代码文件树末态逐字节相同，只有历史结构变了。⛔ 非空即回滚。

#### 推送状态的三分处置

| 范围内提交的推送状态 | 处置 |
|---|---|
| 未推送 | 直接改写 |
| 已推送到**你自己的 fork** | ⚠️ 告知改写后需 `--force-with-lease`，确认后继续 |
| 已推送到**上游** | ⛔ 该部分不得改写。只能用「不改历史」方式处理（补一个迁出 commit） |

#### 两步执行

**第一步 · 摘 DevDocs 痕迹**（机械，无判断）

列出范围内所有触碰 `docs/devdocs` / `docs/prd` / `docs/codebase-insight.md` / `AGENTS.md` 的提交，分两类：

- **纯 DevDocs 提交** → 整个 drop
- **混合提交**（同时改了代码和 DevDocs 产物）→ 只摘那些路径，保留代码改动

**第二步 · 整理成可提 PR 的序列**（判断题，⚠️ 逐组确认）

把剩余代码提交按**逻辑变更**分组，一组 squash 成一个 commit，message 沿用该仓自身历史风格（委托 `/commit-convention`）。

⛔ **分组不得自动决定**。每一组 AskUserQuestion 展示 before/after 让用户确认：

```
第 2 组 / 共 4 组
  before:  a3 fix typo
           a4 真正的实现
           a5 忘了加测试
  after:   feat: 支持 X（含单元测试）
[确认 / 调整分组 / 拆开不合 / 跳过整理只摘痕迹]
```

「跳过整理只摘痕迹」是随时可退的出口——退出后仍拿到干净的历史，只是没整理。

### 5.4 挂子模块：绝不用远端 URL

被删的七步 Step 4 用 `git submodule add <R 的 remote URL>`，那是**从远端重新 clone 一份干净的**，本地未推送的工作全不在里面。

改为挂**本地路径**：

```bash
git submodule add ./<R 目录名> <name>
```

保住工作区现状。后续推送与 URL 修正由用户在需要时自行处理（`git config -f .gitmodules submodule.<name>.url <url>`）。

### 5.5 可逆性

除 §5.3 的历史改写（有备份分支兜底）与「从代码仓清掉 DevDocs 产物」外，**其余步骤只新增不删除**。清理步骤放在最后，此时根仓库已完整。

详细命令与分场景处置见 `references/inline-to-shell.md`。

## 6. 影响面

### 6.1 新建

```
skills/workspace-topology/
  SKILL.md                          定位 / 单入口 / 四动作 / 声明 schema / 校验表
  references/probe-and-repair.md    探测步骤 / detached HEAD 处置 / 指针漂移三成因
  references/inline-to-shell.md     迁移双模式流程 / 分场景命令 / 历史改写安全线
```

### 6.2 改动（3 文件）

- `pipeline/SKILL.md:208` —— 整段探测说明替换为 `Task: /workspace-topology`；停止传 `devdocs_frontmatter` 的 workspace 字段
- `retrofit/SKILL.md:177, 179` —— 同上；179 的「若上一步探测到工作区模式，一并写入」子句删除
- `realign-scope-layout.md:82–85 / 156 / 229` —— 82–85 改委托；**156 迁移路由整行删除**（§0.2）；229 修复项指针改新 skill

### 6.3 删除 + 指针改指（1 文件 + 其引用者）

`pipeline/references/layout/workspace-shell.md` 删除。引用它的位置改指 `skills/workspace-topology/references/probe-and-repair.md`：

| 引用者 | 行 |
|---|---|
| `_shared/workspace-mode.md` | frontmatter `related`、正文 §17、§3 表、§7.3 |
| `_shared/constraints.md` | 299（`workspace/pointer`） |
| `dev-workflow/SKILL.md` | 301（detached HEAD 处置） |
| `health-lint-implementation.md` | 405（指针漂移修复路径） |
| `realign-scope-layout.md` | 156（**整行删除**，不改指针） |
| `pipeline/SKILL.md` / `retrofit/SKILL.md` | 208 / 177（随 5.2 一并改） |

⚠️ 这是**纯指针替换**，不改任何条文语义。`_shared/workspace-mode.md` 的内容一字不动。

### 6.4 文档

`docs/architecture.md:283–296`、`docs/workflows.md:333`、本仓 `AGENTS.md` 当前状态节。

**不改**：`_shared/workspace-mode.md` 正文、`agent-memory/SKILL.md`、`layout-metadata-schema.md`、全部消费方 skill、`docs/superpowers/specs/2026-08-05-*`、`docs/audits/*`。

### 6.5 spec_version bump

| 文件 | 变更 | bump |
|---|---|---|
| 新 skill | 新建 | `workspace-topology.v1` |
| `_shared/constraints.md` §10 `workspace/pointer` | 仅改指针目标 | **不 bump**（`realign/no-bump-copyedit`） |
| `_shared/workspace-mode.md` | 仅改 `related` 与指针 | **不 bump**（同上） |

## 7. 复杂度账

| 项 | 增 | 减 |
|---|---|---|
| `skills/workspace-topology/`（SKILL + 2 references） | +约 220 行 | |
| `workspace-shell.md` 删除（含旧迁移七步 170 行） | | −252 行 |
| ↳ 存活内容已计入上方 +220 | | |
| `realign-scope-layout.md:156` 迁移路由行 | | −1 行 |
| `pipeline` / `retrofit` 传参管道 | | −约 8 行 |
| **净** | | **约 −41 行** |

六稿的账：−120 → −50 → −40 → +2 → +68 → **本稿 −41**。

比第 6 稿初版（−131）多出的约 90 行全在 `inline-to-shell.md`：双模式分工、状态盘点分支、历史改写的三条安全线与两步执行。**这部分是净新增能力**——旧七步虽有 170 行，但对目标场景不可用（§1.2）。

不建查询接口就不用写输出契约、不迁字段就不用写兼容层、不改消费方就不用写委托句 —— 负数仍然成立。

## 8. 验证

**本仓（可立即做）**

1. `grep -rn "workspace-shell" skills/ docs/` —— 除历史 spec / 台账外零命中（指针已全部改指 `probe-and-repair.md`）
2. `realign --scope=health` 的 `dead-link` rule 全过
3. `git diff` 确认 `_shared/workspace-mode.md` 的改动**仅限** frontmatter `related` 与四处指针，正文零改动
4. 新 SKILL.md ≤ 500 行（硬约束）
5. 消费方零改动：`git diff --name-only` 不含 `verify` / `test-run` / `codebase-insight` / `e2e-test-flow` / `code-self-describe` / `dev-flow` / `bugfix` / `dev-workflow`（`dev-workflow/SKILL.md:301` 的纯指针替换是唯一例外，须在 diff 中肉眼确认只有一行）

**真实项目（挂账）**

6. 在 `chiaki-ng-dev`（已有 shell 声明）跑一次，确认展示现状、选「保持不变」时零写入、`pointer_checks` 与 `git submodule status` 一致
7. 在一个无 `.gitmodules` 的 inline 项目跑一次，确认静默判 `inline`、不打扰、零写入
8. 在一个非 DevDocs 项目（无 `docs/devdocs/`）跑一次，确认能创建只含两字段的部分 `devdocs:` 块且不触发任何 DevDocs 流程 —— **这是 §0.1 的验收**
9. **迁移双模式验收（§0.2）**：造一个「clone 开源项目 + 已用 DevDocs 开发（工作区有改动 + 有未推送提交）」的仓，两种模式各跑一次：
   - 确认**不被前置门挡住**（旧七步在此必 ⛔）
   - 确认子模块挂的是本地路径、**未推送工作仍在**
   - 确认历史改写前打了备份分支，改写后 §5.3 的内容断言为空
   - 确认上游已推送的提交**未被改写**
   - 手动模式：确认迁移计划文件落在仓外、用户建好目录后能续做

## 9. 明确不做

| 不做 | 理由 |
|---|---|
| skill 擅自决定外层目录路径 / 迁移作为声明设定的副作用发生 | §0.2；迁移改为显式双模式操作，路径由用户定（§5.1） |
| 自动决定 squash 分组 | §5.3；「哪些该合」是判断题，逐组 AskUserQuestion，且随时可退到「只摘痕迹」 |
| 改写上游已有的历史 | §5.3 安全线 1；改写范围恒为 `merge-base(upstream, HEAD)..HEAD` |
| 用远端 URL `git submodule add` | §5.4；会丢本地未推送工作 |
| `--check` 拓扑查询接口 | R5 F-404：五个路径类消费方无 `Task` 权限，委托架构不成立；→ 配对 spec |
| `workspace/no-bypass` 禁令 | 同上——没有可用的委托入口就无从要求「必须委托」 |
| 字段位置迁移到顶层 `workspace:` 块 | §0.1 附注；那是设计者加的诊断，非用户诉求，且引出 R5 F-403 回归 |
| 任何消费方算法改动 | §1；→ 配对 spec 的 25 处 |
| 封装提交侧（`--plan-commits` / 提交证据 / `review_diff_sources`） | R2 熔断；跨仓提交是有状态分布式事务，codex R3 独立确认该塌缩正确 |
| `workspace-topology` 执行 `git commit` | 提交是干活 skill 的职责 |
| 建 `workspace_baseline` 持久化基线 | R3 F-205 建议，R4 复审确认不采纳；该缺口今天就存在 |
| 源码 / 测试路径分类器 | §3.3 |
| 用「add-only」为本批背书 | §1.2；删迁移是有意的 breaking removal，R5 F-401 判第 5 稿的 add-only 定性名不副实 |

## 10. 待审查者重点质疑（R6）

前五轮共 36 条发现，其中 28 条源自本稿已删除的三个面（提交侧接口 / `--check` 查询接口 / 字段位置迁移）。§5 的迁移是**本稿新增、从未被审过**的面，请优先攻击它（第 6–8 问）。其余：

1. **`pipeline` / `retrofit` 的委托改造是否真的零回归** —— 今天探测结果经 `devdocs_frontmatter` 传给 `agent-memory` 代写，改为新 skill 自写后，`agent-memory` 那一步的其余职责（工作流路由节、`initialized_at`）是否受影响；两者写同一个 `devdocs:` 块的时序是否会互相覆盖。
2. **§5.3 的指针替换是否真是纯替换** —— `workspace-shell.md` 里除探测 / detached HEAD / 指针漂移三节外，是否还有别的内容被现有引用者依赖，删除后会丢。
3. **§7 验证项 5 的「消费方零改动」是否可执行** —— `dev-workflow/SKILL.md:301` 是唯一例外。这个例外会不会在实施时扩散。
4. **非 DevDocs 项目创建部分 `devdocs:` 块是否有副作用** —— 该块存在会不会让别的 skill（尤其 `pipeline` 的阶段检测、`health-lint` 的 `state/*` rule）误判该项目为 DevDocs 项目。
5. **本稿是否仍有「设计者加的诊断」** —— §0.1 的附注承认了一处。请找出是否还有第二处：某个约束或字段的存在理由追溯不到用户诉求或既有缺陷。
6. **§5.3 的内容断言是否真能兜住历史改写** —— `git diff <backup> HEAD -- . ':!docs/devdocs' …` 为空即通过。这个断言在「混合提交只摘部分路径」「squash 跨越文件重命名」「有 merge commit」三种情形下是否仍成立？
7. **手动模式的续做是否真闭合** —— 迁移计划文件落在仓外，用户建好目录后重新调 skill 指向它。用户在这期间改了别的东西（比如又提交了几个 commit），计划文件里的盘点结果失效怎么办？
8. **§5.2 删掉前置门后，有没有新的不安全输入能进来** —— 旧门虽然挡错了场景，但它确实拦住了「工作区脏时做仓库手术」。改为盘点分支后，哪些脏状态组合会导致中途失败且难以恢复？
