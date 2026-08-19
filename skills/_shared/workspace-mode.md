---
title: 工作区模式协议 SSOT（inline / shell）
status: 引入新协议，跨 skill 强制
scope: 文档仓与代码仓的拓扑关系
related:
  - skills/_shared/constraints.md（§10 指针）
  - skills/pipeline/references/layout/layout-metadata-schema.md（frontmatter schema）
  - skills/pipeline/references/layout/workspace-shell.md（操作手册）
generated_at: 2026-08-05
spec_version: workspace-mode.v1
---

# 工作区模式协议 SSOT（inline / shell）

本文是 `workspace_mode` 维度的协议正文 SSOT。该维度描述**文档仓与代码仓的拓扑关系**，与 `docs_layout_version` / `id_scheme` / `traceability_version` 三层版本号正交——docs 内部结构不因模式而变，不进 layout 版本矩阵。

本文不覆盖：探测步骤、inline→shell 迁移流程、故障修复手册。这些操作细节归 [layout/workspace-shell.md](../pipeline/references/layout/workspace-shell.md)。

## 1. 模式枚举与缺省

外壳仓根下依然是 `docs/devdocs/`，仓内 280 处 `docs/devdocs` 硬编码引用原样成立。真正改变的只有两件事：

1. **代码根 ≠ 仓库根** —— 碰代码的 skill 现在假设代码在 cwd 根
2. **N+1 个 git 仓** —— 文档提交进外壳仓，代码提交进各子模块仓，外壳仓额外跟子模块指针

项目根 `AGENTS.md` 已有的 `devdocs:` 段新增字段：

```yaml
---
devdocs:
  docs_layout_version: layout.v1
  id_scheme: id.v1
  traceability_version: trace.v0
  workspace_mode: shell        # 可选，枚举 inline|shell，缺省 inline
  code_roots: [web, api]       # shell 时必填，≥1 项，元素为 .gitmodules 的 submodule name
  initialized_at: "2026-08-05"
---
```

- `workspace/mode-enum`：`workspace_mode` 是二值枚举 `inline` | `shell`，声明在项目根 `AGENTS.md` 的 `devdocs:` frontmatter。**缺省 `inline`**——无此字段的存量项目行为完全不变，docs 路径不因模式而变。

## 2. `code_roots` 与真源

**`code_roots` 记 submodule name 而非路径。** `.gitmodules` 是路径与 URL 的唯一真源，运行时用 `git config -f .gitmodules submodule.<name>.path` 解析。这样：

- 子模块换路径只改 `.gitmodules`，frontmatter 不用跟，不会漂
- 「name 不在 `.gitmodules`」能区分「被改名/删了」与「路径临时不存在（未 submodule update）」，两种情形提示不同
- 「必须是 git 子模块」这条校验由构造保证，不用单独判

- `workspace/code-roots-source`：`shell` 模式下 `code_roots` 必填，元素为 `.gitmodules` 的 submodule **name**，不是路径；路径与 URL 的唯一真源是 `.gitmodules`，不在 frontmatter 复制，运行时经 `git config -f .gitmodules submodule.<name>.path` 解析。
- `workspace/no-nested-submodules`：**嵌套子模块（vendor / 依赖项）不在 `code_roots` 语义内，`workspace-mode.v1` 不处理。** `code_roots` 只认外壳仓自身 `.gitmodules` 里的一层；code_root 内部再嵌套的子模块属依赖项、不在工作面上，其 gitlink 条目在 code_root 层扫描中按普通「不相关变更」呈现（即 §7.2 判据不认它是 gitlink，§7.3 的 stash 禁令不覆盖它）。这是**有意缺位而非缺口**：依赖项的正确答案本就是「忽略」，三选一里有一项（stash）对它是空操作，属可接受的表面瑕疵。不扩展 §7.2 判据、不做嵌套深度遍历、不为此新增 health rule。

## 3. 校验规则（fail-closed）

| 情形 | 行为 |
|------|------|
| 无 `workspace_mode` 字段 | 视为 `inline` —— 现存所有项目零影响 |
| `shell` 但 `code_roots` 缺失 / 为空 | ⛔ 阻塞 |
| 某 name 不在 `.gitmodules` | ⛔ 阻塞，提示修 frontmatter |
| name 在 `.gitmodules` 但工作区目录为空 | ⛔ 阻塞（**运行时校验门**场景：要用代码根干活，目录空了就得停），提示 `git submodule update --init <path>`；health 只读扫描同一情形降级为 ⚠️，见 [health-lint-implementation.md § submodule/pointer-drift](../pipeline/references/health-lint-implementation.md#submodulepointer-drift) |
| 解析出的两个 path 互为前缀（嵌套子模块） | ⛔ 阻塞 |
| 某 path 为 `.` / 含 `..` / 等于 `docs` | ⛔ 阻塞 |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略，不阻塞 |

- `workspace/fail-closed`：见上表——`shell` 模式的六类校验失败一律 fail-closed（多数为 ⛔ 阻塞，`inline` 却出现 `code_roots` 降级为 ⚠️ 警告并忽略）；无 `workspace_mode` 字段（即 `inline`）不触发本表任何一条。

## 4. 归属判定

某文件属于哪个代码根，用**解析后路径的前缀匹配**。落在仓库根下、不属任何 `code_roots` 且不在 `docs/` 里的源码文件 → ⚠️ 提示（外壳仓不该有代码）。此判定同时是第 6 节提交分组的依据。

- `workspace/root-attribution`：文件归属代码根按解析后路径的前缀匹配判定；落在仓库根、不属任何 `code_roots` 且不在 `docs/` 内的源码文件 → ⚠️ 提示（外壳仓不该有代码）。该判定同时是第 6 节提交分组的依据。

## 5. 零污染写入范围

**核心红线：LLM 不主动往 `code_roots` 里写任何非代码文件。** 已存在的照读照尊重，用户显式要求可写。

| 产物 | 落点 | 说明 |
|------|------|------|
| `docs/devdocs/*`、`docs/prd/*`、`docs/codebase-insight.md` | 外壳仓 | 路径与同仓模式一致 |
| 源码、测试代码 | 对应 `code_roots/<path>/` | **唯一**允许写入子模块的类别 |
| 外壳仓根 `AGENTS.md` / `CLAUDE.md` | 外壳仓 | 治理 frontmatter、工作流路由节 |
| 子模块内 `AGENTS.md` / `CLAUDE.md` | 子模块 | **不主动创建、不主动改**；已存在则读取并尊重其编码纪律 |
| `code-self-describe` 的模块级 `CLAUDE.md` + 文件头注释 | — | shell 下**默认跳过**，仅 `--force-code-docs` 显式启用 |
| dev-workflow 流程内的「自描述更新」步骤 | — | 同上，跳过时在 yaml 摘要里 ℹ️ 记录跳过原因 |
| layout.v2 的 `@satisfies` / `@verifies` 代码注释 | — | shell 下**禁用**。本仓现役 layout.v1 本就未启用，此条为前瞻约束，防未来升 v2 时污染上游 |
| `.claude/settings.local.json`、`.remember/` | 外壳仓 | 参考仓既有实践 |

**违约检测**：dev-workflow / bugfix 提交前，对每个变更子模块跑 `git status --porcelain`，出现非源码/测试路径的变更 → ⚠️ 列出并 AskUserQuestion（提交 / 排除 / 终止）。**不做静态白名单猜测「什么算源码」** —— 上游仓目录约定各异，猜会误伤。

- `workspace/no-pollution`：LLM 不主动往 `code_roots` 写任何非代码文件；已存在的 `AGENTS.md`/`CLAUDE.md` 照读照尊重，写入范围见上表。提交前对每个变更子模块跑 `git status --porcelain` 做违约检测，出现非源码/测试路径变更 → ⚠️ 列出并 AskUserQuestion（提交 / 排除 / 终止），不做静态白名单猜测。

## 6. N+1 仓提交协议

### 6.1 映射

现有「Commit 1 代码 + Commit 2 文档」直接展开：

- **Commit 1** → 每个**有变更的**代码根一个 commit
- **Commit 2** → 外壳仓一次 commit，含文档变更 + 所有变更子模块的指针 bump

### 6.2 严格顺序

1. **前置门（逐个变更子模块）**：`git -C <path> symbolic-ref -q HEAD` 检查是否在具名分支上。子模块默认 detached HEAD，此状态下提交产生**游离 commit** —— 指针 bump 后代码看似在、实际无分支引用，且 `git gc` 后可能丢失。detached → ⛔ 阻塞，提示 `git -C <path> checkout <branch>`。**这是本布局最容易踩且最难察觉的坑。**
2. 逐个变更子模块提交
3. 外壳仓 `git add docs/ <各变更 path>` → 一次提交

### 6.3 commit message 契约与追溯枢纽

| 仓 | 风格 | 编号 |
|----|------|------|
| 子模块 | 沿用**该仓自身**的提交历史风格（`/commit-convention` 的「优先沿用已有风格」正好适用） | **不带** T-XX / F-XX —— DevDocs 编号对上游是噪声，也是零污染的一部分 |
| 外壳仓 | 本仓 Conventional Commits | 带 T-XX，body 列 `web@a1b2c3d` / `api@e4f5g6h` |

**追溯枢纽 = 外壳仓 commit。** 正向：T-XX → 外壳仓 commit → 各子模块 SHA。反向：子模块 SHA → 外壳仓 `git log -S<sha>` → T-XX。子模块自身干净得像没有 DevDocs 存在过。

**`--single-commit` 在 shell 下不可用** —— 跨仓无法合并为单 commit，⚠️ 忽略该 flag 并提示。

### 6.4 跨仓 Recovery

跨仓无真原子性。按失败点分三类，均按共享约束 §7 Recovery 格式输出：

| 失败点 | 残留状态 | 恢复方式 |
|--------|---------|---------|
| 第 k 个子模块提交失败（k>1） | 前 k−1 仓已提交，追溯链未建立 | 报告已提交 SHA 列表 + 剩余 root，AskUserQuestion（续提 / 人工回滚 / 终止）。**不自动回滚已提交的代码** |
| 全部子模块已提交，外壳仓提交失败 | 代码在，文档与指针没跟 | 最轻。给出精确命令重跑外壳仓提交 |
| 外壳仓已提交但漏 bump 某指针 | 指针滞后 | `git submodule status` 可检出，由 `verify` / `realign --scope=health` 捕获并提示补 bump |

- `workspace/commit-protocol`：Commit 1 = 每个有变更的代码根各一个 commit；Commit 2 = 外壳仓一次提交（文档变更 + 各变更子模块指针 bump）。提交前逐个变更子模块跑 `git -C <path> symbolic-ref -q HEAD` 检查具名分支，detached HEAD ⛔ 阻塞并提示 `git -C <path> checkout <branch>`。子模块提交沿用自身仓风格、不带 T-XX/F-XX；外壳仓提交用 Conventional Commits + T-XX，body 列各子模块 SHA；追溯枢纽 = 外壳仓 commit。`--single-commit` 在 shell 下不可用，⚠️ 忽略并提示。
- `workspace/recovery`：跨仓无真原子性，按失败点分三类（见上表：子模块提交失败 / 全部子模块已提交但外壳仓提交失败 / 外壳仓已提交但漏 bump 指针），均按共享约束 §7 Recovery 格式输出；不自动回滚已提交的代码。

## 7. 工作区洁净检查（gitlink 排除）

`ms-dev-workflow` 的 N+1 工作区遍历（外壳仓 + 各 `code_roots` 各跑一次 `git status --porcelain`，检出「不相关变更」后 AskUserQuestion：stash / 忽略 / 终止，见 [task-orchestration.md § 断点续做状态机](../dev-workflow/references/task-orchestration.md)）在外壳仓这一层必须排除 gitlink 条目，否则同一件事会被双重报告，且 gitlink 条目不适用 stash。

### 7.1 现象：gitlink 条目与普通文件条目在 porcelain v1 里同形

子模块工作区脏时（含子模块内部再嵌套子模块的 untracked 内容层层冒泡），外壳仓 `git status --porcelain` 会显示一条形如 ` M <code_root_path>` 的 gitlink 条目——格式上与普通文件的 `M`/`??` 条目**完全相同**，无法仅凭这一行文本区分「指针漂移待 bump」还是「子模块工作区脏污染冒泡」（这两者的判据只存在于 `git submodule status` 的首字符：空格=SHA 一致=非漂移，`+`=漂移，见 §3 表「name 在 .gitmodules 但工作区目录为空」行相邻的 `pointer-drift` health rule）。

实测（`chiaki-ng-dev`，2026-08-05，子模块内部 `third-party/curl` 有原有未跟踪改动、指针未漂移）：

```
$ git status --porcelain          # 外壳仓
 M chiaki-ng
$ git -C chiaki-ng status --porcelain
 M third-party/curl
$ git status --porcelain=2        # 更细粒度格式能看出区别，但工作区洁净检查用的是 v1
1 .M S..U 160000 160000 160000 <sha> <sha> chiaki-ng   # S..U = submodule/无commit变更/无tracked变更/有untracked内容
```

`--porcelain=2` 的 `S..U` 标志位能区分「指针未变、纯工作区脏」，但工作区洁净检查依赖的 v1 格式不暴露这个区分——这正是排除规则存在的原因。

> ⚠️ **本节所有输出均为 `git status --porcelain`（v1），不可与 `git status --short` 混用。** 同一仓、无 git 别名、无 `status.*` 配置下实测（`od -c` 核过原始字节）：`--short` 得 ` ? chiaki-ng`，`--porcelain` 得 ` M chiaki-ng`。§7.2 判据是状态位无关的，两种格式下都成立，但上文「无法仅凭这一行文本区分指针漂移与工作区脏冒泡」的断言**只对 `--porcelain` 成立**——`--short` 的 ` ?` 会漏出「仅 untracked 内容」这一信号，不可依赖它做判定。复现本节实测块请用 `--porcelain`。

### 7.2 判据：识别 gitlink 条目

外壳仓 `git status --porcelain` 输出中，**条目路径恰好等于某个 code_root 解析出的 path**（`git config -f .gitmodules submodule.<name>.path` 的结果）→ 判定为 gitlink 条目，无论其状态标记是 `M`/`??`/`AM` 等。

判据刻意只认 code_root 一层：code_root **内部**再嵌套的子模块（如 `chiaki-ng/third-party/curl`）不适用本判据，属有意缺位，见 §2 `workspace/no-nested-submodules`。

### 7.3 排除规则

- `workspace/gitlink-exclusion`：外壳仓层面的工作区洁净扫描跳过匹配 code_root 路径的条目（判据见 §7.2）。该条目代表的信号分别交给：指针是否漂移 → `submodule/pointer-drift` health rule（[workspace-shell.md § 指针漂移修复](../pipeline/references/layout/workspace-shell.md#指针漂移修复)）；子模块内部是否有不相关变更 → 该 code_root 自身那一轮 `git -C <path> status --porcelain` 扫描。**不得**在外壳仓扫描与 code_root 扫描里对同一件事各报一次。
- `workspace/no-stash-gitlink`：gitlink 条目**不适用**「stash / 忽略 / 终止」三选一，尤其**绝不提供 stash 选项**。理由：`git stash` 对未提交的子模块指针状态与普通文件的处理方式不同——不存在"把 gitlink 这个条目本身暂存掉"的语义，实际效果是暂存子模块内已 `git add` 的变更（若有），子模块工作区本身未 `add` 的脏内容不受影响；用户会误以为"暂存"消除了这件事，但状态原样存在。gitlink 条目只能引导用户去对应 code_root 内部处理（`git -C <path> ...`）。
