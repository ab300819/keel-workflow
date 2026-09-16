---
title: 工作区拓扑协议（inline / shell / linked）
status: 三种拓扑，跨 skill 强制
scope: 文档仓与代码仓的拓扑关系
related:
  - skills/shared/constraints.md（§10 指针）
  - skills/workspace-topology/SKILL.md（入口与声明 schema）
  - skills/workspace-topology/references/migration.md（操作手册）
generated_at: 2026-08-05
spec_version: workspace-topology.v2
---

# 工作区拓扑协议（inline / shell / linked）

本文是工作区拓扑维度的协议正文。该维度描述**文档仓与代码仓的拓扑关系**——docs 内部结构不因模式而变。

本文不覆盖：入口、声明 schema、校验的交互形态（见 [../SKILL.md](../SKILL.md)），也不覆盖探测步骤、迁移流程、故障修复手册（见 [migration.md](migration.md)）。

## 目录

- 1. 模式枚举与缺省
- 2. `code_roots` 与真源
- 3. 校验规则（fail-closed）
- 4. 归属判定
- 5. 零污染写入范围
- 6. N+1 仓提交协议
- 7. 工作区洁净检查（gitlink 排除）

## 1. 模式枚举与缺省

外壳仓根下依然是 `docs/devdocs/`，仓内 310 处 `docs/devdocs` 硬编码引用原样成立。**文档根在三种模式下恒为 `<仓库根>/docs/`，是固定不变量，不设配置字段。** 真正改变的只有两件事：

1. **代码根 ≠ 仓库根** —— 碰代码的 skill 现在假设代码在 cwd 根
2. **多个 git 仓** —— 文档提交进本仓，代码提交进各代码根自身的仓。`shell` 下本仓额外跟子模块指针；`linked` 下无 gitlink、无指针（见 §6.5）

声明在项目根 `AGENTS.md` frontmatter 的**独立 `workspace:` 块**——这是仓库级事实，不是 keel 事实：

```yaml
---
workspace:
  mode: shell                  # 枚举 inline|shell|linked；无此块时问用户，不缺省
  code_roots: [web, api]       # shell / linked 时必填，≥1 项；shell 元素为 submodule name，linked 须给 path
devdocs:                       # keel 项目才有；非 keel 项目只有 workspace: 块
  initialized_at: "2026-08-05"
---
```

- `workspace/mode-enum`：`mode` 是三值枚举 `inline` | `shell` | `linked`，声明在项目根 `AGENTS.md` 的独立 `workspace:` frontmatter 块。**无此块时不缺省、不自动判定**——问用户定出 `mode` 与代码根后落声明（见 [../SKILL.md § 无声明时：问，不猜](../SKILL.md#无声明时问不猜)）。已落声明的项目行为完全不变。
- `workspace/docs-root`：文档根恒为 `<仓库根>/docs/`，三种模式无差别，**不设字段、不可配置**。
- `workspace/legacy-location`：旧版本把字段放在 `devdocs.workspace_mode` / `devdocs.code_roots`，**只读兼容**；迁移与冲突处置见 [../SKILL.md § legacy 兼容](../SKILL.md)。

### 1.1 三种拓扑与所有权

| mode | 代码根在哪 | 归本仓所有吗 |
|------|------------|--------------|
| `inline` | 仓库根 | 是 |
| `shell` | 本仓的 git 子模块 | 是（gitlink 锁 commit） |
| `linked` | 本机的目录引用，仓内仓外皆可 | **否**，本仓只持有引用 |

`inline` / `shell` 的共同前提是「本仓拥有代码」。`linked` 打破的正是这一条——所有权变了，校验规则随之分家（§3）。

## 2. `code_roots` 与真源

以下关于 `.gitmodules` 真源的论述**仅适用 `shell`**；`linked` 见 `workspace/code-roots-source`。

**`code_roots` 记 submodule name 而非路径。** `.gitmodules` 是路径与 URL 的唯一真源，运行时用 `git config -f .gitmodules submodule.<name>.path` 解析。这样：

- 子模块换路径只改 `.gitmodules`，frontmatter 不用跟，不会漂
- 「name 不在 `.gitmodules`」能区分「被改名/删了」与「路径临时不存在（未 submodule update）」，两种情形提示不同
- 「必须是 git 子模块」这条校验由构造保证，不用单独判

- `workspace/code-roots-source`：真源按 mode 分。`shell` 下 `code_roots` 元素为 `.gitmodules` 的 submodule **name**，路径经 `git config -f .gitmodules submodule.<name>.path` 解析；`linked` 下无 `.gitmodules` 兜底，元素必须给 `path`，声明本身即真源。`code_roots` 同时接受字符串项与对象项，字符串 `foo` 等价于 `{name: foo}`——`shell` 现有声明零改动。
- `workspace/no-nested-submodules`：**嵌套子模块（vendor / 依赖项）不在 `code_roots` 语义内，`workspace-topology.v2` 不处理。** `code_roots` 只认外壳仓自身 `.gitmodules` 里的一层；code_root 内部再嵌套的子模块属依赖项、不在工作面上，其 gitlink 条目在 code_root 层扫描中按普通「不相关变更」呈现（即 §7.2 判据不认它是 gitlink，§7.3 的 stash 禁令不覆盖它）。这是**有意缺位而非缺口**：依赖项的正确答案本就是「忽略」，三选一里有一项（stash）对它是空操作，属可接受的表面瑕疵。不扩展 §7.2 判据、不做嵌套深度遍历、不为此新增 health rule。

## 3. 校验规则（fail-closed）

**无 `workspace:` 块时不进本表** —— 先问用户定出 `mode` 与代码根（见 [../SKILL.md § 无声明时：问，不猜](../SKILL.md)），⛔ 不再无条件视为 `inline`。定出 mode 后再按下表校验。

| 情形 | inline | shell | linked |
|------|--------|-------|--------|
| `mode` 需要 `code_roots` 但缺失 / 为空 | — | ⛔ | ⛔ |
| 声明的代码根解析不到实体 | — | ⚠️ 归入 `missing_code_roots`，报告里给恢复线索 | ⚠️ 同左 |
| `code_roots` 有重复 name | ⛔ | ⛔ | ⛔ |
| 解析出的两个 path 互为前缀 | — | ⛔ | — |
| 某 path 为 `.` 或等于 `docs` | — | ⛔ | ⛔ |
| 某 path 含 `..` 或为绝对路径 | — | ⛔（子模块不可能在仓外） | ✅ 合法 |
| 跟踪了 mode 160000 但 `.gitmodules` 无对应条目（裸 gitlink） | ⛔ | ⛔ | ⛔ |
| 解析后路径逃逸出已授权工作范围 | ⛔ | ⛔ | ⛔ |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略 | — | — |

「声明的代码根解析不到实体」在 health 只读扫描中对应 `submodule/pointer-drift` rule，见 [health-lint-implementation.md § submodule/pointer-drift](../../pipeline/references/health-lint-implementation.md#submodulepointer-drift)（该 rule 仅 `shell` 适用；`linked` 无 gitlink，无等价 rule）。

- `workspace/fail-closed`：见上表，校验按 mode 分家。两处相对 v1 的实质变化：（1）「声明的代码根解析不到」从 ⛔ 降为 ⚠️ 另列——流程不碰的代码根没 init 不该挡死整条流程，且那是一条命令可恢复的状态，不是损坏；（2）`path` 含 `..` 或为绝对路径在 `linked` 下合法。`linked` 下不检查 path 互为前缀 —— spec 明确「多个引用指向同一目标可能是有意的，只认不评判」；该检查在 `shell` 下成立是因为嵌套子模块属依赖项、不该进 `code_roots`。
- `workspace/bare-gitlink`：跟踪了 mode 160000 的条目但 `.gitmodules` 无对应 submodule 条目 → ⛔ 全 mode 阻塞。这是客观损坏：clone 下来是空目录且无法 `git submodule update` 恢复，git 自身只输出 hint 不拦截。
- `workspace/path-not-authorization`：`AGENTS.md` 是版本控制里的普通文件，可能来自不可信来源（clone 他人的仓、合并他人的分支），而 `path` 允许绝对路径、`..` 与符号链接。**解析出的路径不得自动扩大 agent 的可写范围**：逃逸出已授权工作范围 ⛔ 拒绝并报告；符号链接按**解析后的真实目标**判定，不按链接自身位置；绝对路径是本机绑定事实，报告时如实标注，⛔ 不得呈现为「可移植的仓库事实」。允许写下某个路径，不等于允许往那里写文件。

## 4. 归属判定

某文件属于哪个代码根，用**解析后路径的前缀匹配**。此判定同时是第 6 节提交分组的依据。

落在仓库根下、不属任何 `code_roots` 且不在 `docs/` 里的**已跟踪文件** → ℹ️ 列清单交用户判断。

⛔ **不猜哪个算源码。** 上游仓目录约定各异，静态白名单会误伤——这与 §5「不做静态白名单猜测『什么算源码』」是同一条纪律，此前两节互相矛盾，现统一为「列出来，让人看」。

- `workspace/root-attribution`：文件归属代码根按解析后路径的前缀匹配判定，该判定同时是第 6 节提交分组的依据。
- `workspace/root-residue`：仓库根下不属任何 `code_roots` 且不在 `docs/` 内的已跟踪文件 → ℹ️ 列清单交用户判断，**不预判类别**。

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
| `@satisfies` / `@verifies` 代码注释 | — | shell 下**禁用**——子模块是开源上游，keel 元信息不得进入 |
| `.claude/settings.local.json`、`.remember/` | 外壳仓 | 参考仓既有实践 |

**违约检测**：dev-workflow / bugfix 提交前，对每个变更子模块跑 `git status --porcelain`，**列出全部变更路径清单**交用户判断（⚠️ AskUserQuestion：提交 / 排除 / 终止）。**不预先判定哪条是「非源码」** —— 上游仓目录约定各异，静态白名单会误伤。裁法与 §4 `workspace/root-residue` 一致。

- `workspace/no-pollution`：LLM 不主动往 `code_roots` 写任何非代码文件；已存在的 `AGENTS.md`/`CLAUDE.md` 照读照尊重，写入范围见上表。提交前对每个变更子模块跑 `git status --porcelain` 做违约检测，**列出全部变更路径**并 AskUserQuestion（提交 / 排除 / 终止），⛔ 不预判类别、不做静态白名单猜测。

## 6. N+1 仓提交协议

> **本节按 mode 分层适用。** `inline` 退化为单仓的 Commit 1 + Commit 2。
>
> `shell` 与 `linked` **共用**：Commit 1 按代码根拆成 N 个 commit、drain 侧逐 code_root 定位、工作区遍历 N+1 个仓、`--single-commit` 不可用——判据是 **`mode` 不是 `inline`**，即代码不在本仓。⛔ 不要用「`code_roots` 有几项」判——单代码根的外壳仓（维护一个 fork）只有一项，与 `inline` 分不开。
>
> **仅 `shell` 适用**：Commit 2 的子模块指针 bump、§6.3 的追溯枢纽（外壳仓 commit 记录各子模块 SHA）、§6.4 的指针漂移 Recovery、断点续做的「Git 历史」维收紧与第五维「指针一致性」——这些依赖 gitlink。`linked` 下无 SHA 可比、无指针可 bump，⛔ 不得把这几项套上去（套上去会让任务永远判不成已完成、每次续做都回炉），见 [§6.5](#65-linked-下无-n1无指针)。
>
> **§6.2 的 detached HEAD 前置门是 `mode` 不是 `inline` 时全适用**，不限 `shell`：游离 commit 被 `git gc` 回收、push 不上去，这两样危害与 gitlink 无关；`linked` 的代码根若是 `git worktree add --detach` 或手动 detached checkout 同样中招。只有「指针 bump 后代码看似都在、实际无分支引用」这半句解释是 `shell` 特有的。

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
| 子模块 | 沿用**该仓自身**的提交历史风格（`/commit-convention` 的「优先沿用已有风格」正好适用） | **不带** T-XX / F-XX —— keel 编号对上游是噪声，也是零污染的一部分 |
| 外壳仓 | 本仓 Conventional Commits | 带 T-XX，body 列 `web@a1b2c3d` / `api@e4f5g6h` |

**追溯枢纽 = 外壳仓 commit。** 正向：T-XX → 外壳仓 commit → 各子模块 SHA。反向：子模块 SHA → 外壳仓 `git log -S<sha>` → T-XX。子模块自身干净得像没有 keel 存在过。

**`--single-commit` 在 `mode` 不是 `inline` 时不可用** —— 跨仓无法合并为单 commit，⚠️ 忽略该 flag 并提示。

### 6.4 跨仓 Recovery

跨仓无真原子性。按失败点分三类，均按共享约束 §7 Recovery 格式输出：

| 失败点 | 残留状态 | 恢复方式 |
|--------|---------|---------|
| 第 k 个子模块提交失败（k>1） | 前 k−1 仓已提交，追溯链未建立 | 报告已提交 SHA 列表 + 剩余 root，AskUserQuestion（续提 / 人工回滚 / 终止）。**不自动回滚已提交的代码** |
| 全部子模块已提交，外壳仓提交失败 | 代码在，文档与指针没跟 | 最轻。给出精确命令重跑外壳仓提交 |
| 外壳仓已提交但漏 bump 某指针 | 指针滞后 | `git submodule status` 可检出，由 `verify` / `realign --scope=health` 捕获并提示补 bump |

- `workspace/commit-protocol`：Commit 1 = 每个有变更的代码根各一个 commit；Commit 2 = 外壳仓一次提交（文档变更 + 各变更子模块指针 bump）。提交前逐个变更子模块跑 `git -C <path> symbolic-ref -q HEAD` 检查具名分支，detached HEAD ⛔ 阻塞并提示 `git -C <path> checkout <branch>`。子模块提交沿用自身仓风格、不带 T-XX/F-XX；外壳仓提交用 Conventional Commits + T-XX，body 列各子模块 SHA；追溯枢纽 = 外壳仓 commit。`--single-commit` 在 `mode` 不是 `inline` 时不可用，⚠️ 忽略并提示。
- `workspace/recovery`：跨仓无真原子性，按失败点分三类（见上表：子模块提交失败 / 全部子模块已提交但外壳仓提交失败 / 外壳仓已提交但漏 bump 指针），均按共享约束 §7 Recovery 格式输出；不自动回滚已提交的代码。

### 6.5 `linked` 下：无 N+1，无指针

`linked` 的代码根是独立仓库，**不由本仓通过 gitlink 跟踪**。因此：

- 文档仓提交只含文档，⛔ **不做指针 bump**——没有 gitlink 可 bump
- 代码提交进各代码根自身的仓，沿用该仓风格
- **追溯链不由本 skill 保证**。`shell` 的追溯枢纽是「外壳仓 commit 记录各子模块 SHA」，该机制依赖 gitlink；`linked` 下不存在等价物

这是「只认，不造」的直接后果：本仓不拥有那些代码根，无权也无法为它们建立指针。需要追溯的项目应选 `shell`。

- `workspace/linked-commit`：`linked` 下各仓各自提交，⛔ 不做指针 bump，追溯链不由本 skill 保证。

## 7. 工作区洁净检查（gitlink 排除）

> **§7.2 / §7.3 的 gitlink 排除规则仅适用 `shell`。** `linked` 的代码根不是 gitlink，不会以 gitlink 条目形式出现，无需排除。
>
> ⚠️ 但**仓内**的 `linked` 代码根若未被 `.gitignore` 忽略，会以 `??` 出现在洁净扫描里。此时 §7.3 的 `workspace/no-stash-gitlink` **同样适用**——那是个嵌套 git 仓，`git stash` 对它没有「暂存掉这个条目」的语义。⛔ 不得对它提供 stash 选项，只能引导用户进该目录自行处理。

`dev-workflow` 的 N+1 工作区遍历（外壳仓 + 各 `code_roots` 各跑一次 `git status --porcelain`，检出「不相关变更」后 AskUserQuestion：stash / 忽略 / 终止，见 [task-orchestration.md § 断点续做状态机](../../dev-workflow/references/task-orchestration.md)）在外壳仓这一层必须排除 gitlink 条目，否则同一件事会被双重报告，且 gitlink 条目不适用 stash。

### 7.1 现象：gitlink 条目与普通文件条目在 porcelain v1 里同形

子模块工作区脏时（含子模块内部再嵌套子模块的 untracked 内容层层冒泡），外壳仓 `git status --porcelain` 会显示一条形如 ` M <code_root_path>` 的 gitlink 条目——格式上与普通文件的 `M`/`??` 条目**完全相同**，无法仅凭这一行文本区分「指针漂移待 bump」还是「子模块工作区脏污染冒泡」（这两者的判据只存在于 `git submodule status` 的首字符：空格=SHA 一致=非漂移，`+`=漂移，见 §3 表「声明的代码根解析不到实体」行下方的 `pointer-drift` health rule 指引）。

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

- `workspace/gitlink-exclusion`：外壳仓层面的工作区洁净扫描跳过匹配 code_root 路径的条目（判据见 §7.2）。该条目代表的信号分别交给：指针是否漂移 → `submodule/pointer-drift` health rule（[migration.md § 指针漂移修复](migration.md#指针漂移修复)）；子模块内部是否有不相关变更 → 该 code_root 自身那一轮 `git -C <path> status --porcelain` 扫描。**不得**在外壳仓扫描与 code_root 扫描里对同一件事各报一次。
- `workspace/no-stash-gitlink`：gitlink 条目**不适用**「stash / 忽略 / 终止」三选一，尤其**绝不提供 stash 选项**。理由：`git stash` 对未提交的子模块指针状态与普通文件的处理方式不同——不存在"把 gitlink 这个条目本身暂存掉"的语义，实际效果是暂存子模块内已 `git add` 的变更（若有），子模块工作区本身未 `add` 的脏内容不受影响；用户会误以为"暂存"消除了这件事，但状态原样存在。gitlink 条目只能引导用户去对应 code_root 内部处理（`git -C <path> ...`）。
