# workspace-topology：仓库拓扑从 DevDocs 解耦

> 状态：**第 7 稿 · 按原始方案审查结论重写** · 日期：2026-08-24
> **配对 spec**：[shell 模式单仓假设审计](2026-08-21-shell-single-repo-assumptions-audit-design.md)
>
> **本稿的基线是「用户原始方案 + codex 对该方案的独立评估」**，不是前六稿的展开。前六轮审查（`39.5 → 70.75 → 56.5 → 74.5 → 90`，两次熔断 + 一次安全上限）审的是设计者在原方案之上的加戏，其结论只在与本基线一致处被保留。

## 0. 问题（用户原话）

> 1. 触发机制问题，"仓库设定"是绑定 devdocs 在其他流程中会难以触发或误触发 devdocs 流程
> 2. 该"仓库设定"会修改最外层目录名，按正常节奏不应该修改

**0.1 触发耦合**：探测入口只有三个且全属 DevDocs（`ms-pipeline init` / `ms-retrofit` / `realign --scope=layout`），而消费方里有三个自称「与 DevDocs 独立」的（`dev-flow:133`、`e2e-test-flow:48`、`code-self-describe:87`）。外壳形状但不跑 DevDocs 的项目无路声明；想声明就得拉起整套 DevDocs。

**0.2 外层目录**：`workspace-shell.md` 的迁移七步会在 `../<原名>-dev` 建外壳仓并从远端独立 clone 一份代码仓，磁盘上出现两份工作副本、工作根目录改名。

**0.3 §4/§5 自相矛盾**：`_shared/workspace-mode.md` §4 要「仓根下的**源码文件** → ⚠️」，§5 明确拒绝「静态白名单猜测什么算源码」。

## 1. 第一版定义

采纳 codex 对原始方案的评估结论：

> 独立入口 + 独立元数据 + 稳定 `inspect`/`reconcile` 接口 + 可重入 shell 管理 + **有边界的**迁移；不顺手承诺通用反向迁移或 Git 历史优化。

### 1.1 五条要求的判定

| 用户要求 | 判定 | 依据 |
|---|---|---|
| 抽独立 skill | 成立，但**不便宜** —— 21 处消费/治理/文档点 | 现有直接消费者较多，见 §6 |
| docs 目录统一（inline/shell 都在 `docs/`） | 成立，**现状已基本满足**；做成固定不变量而非可配置字段 | `_shared/workspace-mode.md:21`、`docs/workflows.md:343` |
| 可重入 | 部分成立，**中等到高代价** —— 须区分「改声明」与「改真实拓扑」 | §4 |
| 依赖接口而非实现 | 成立，但**不能解释成调用方什么都不知道** —— `mode`/`docs_dir`/`code_roots` 是必要接口语义，可隐藏的是探测、校验、迁移、恢复算法 | §2 |
| commit 归干活的 skill | 成立，且**用在本 skill 自己身上也成立** —— 它提交自己产生的 `.gitmodules` 与元数据变更 | §2.4 |

### 1.2 「docs 目录统一」的边界

统一的是**工作区文档根**（`docs/devdocs/`、`docs/prd/`、`docs/codebase-insight.md`），**不等于**把代码仓自己的 `docs/`（API 文档、README 资料）一并搬走。后者应留在代码仓。现手册对此边界判断正确（`workspace-shell.md:219`）。

### 1.3 第一版明确不做

| 不做 | 理由 |
|---|---|
| **优化代码提交历史**（rebase / filter / squash / force-push） | 对已公开开源仓风险过高，且**不是布局迁移的必要步骤**。用户第一版已同意去掉 |
| 通用 `shell → inline` 自动化 | 多代码根时「合并进哪个仓 / 是否保留外壳历史 / 多远端如何处理」不存在安全默认答案。第一版只给手动规划 |
| 保持原最外层路径不变的「原地换壳」 | 须先把当前 Git 仓移成子目录再在原路径 init，会移动当前 cwd 且常需 workspace 根之外的父目录写权限 |
| 完全无人值守迁移 | 存在 push 边界；沿用现有纪律：不自动 push |
| 单仓算法迁移（25 处） | → 配对 spec |
| 封装跨仓提交编排 | 跨仓提交是有状态分布式事务；前六轮 R2 熔断结论，codex R3 独立确认 |

## 2. 接口

### 2.1 三个入口

```text
/workspace-topology inspect                              # 只读，返回拓扑上下文
/workspace-topology reconcile                            # 交互式维护声明（幂等）
/workspace-topology migrate --to shell --mode manual|auto  # 有边界的迁移
```

`inspect` 稳定摘要（`yaml-summary-v1` 的 `summary.details`）：

```yaml
schema: workspace-context.v1
mode: shell
workspace_root: /abs/path
docs_dir: docs                    # 固定不变量，非可配置字段
code_roots:
  - {name: api, path: services/api}
  - {name: web, path: web}
```

调用方只依赖这些字段，不关心 `.gitmodules` 怎么解析、迁移分几步、配置写在哪。

### 2.2 传播机制：走握手 `inputs`，不做 Task 嵌套

**实测约束**（前六轮 R5 发现）：六个路径类消费方里五个的 `allowed-tools` **没有 `Task`**——

```
retrofit  ⛔   verify  ⛔   test-run  ⛔   codebase-insight  ⛔   code-self-describe  ⛔
e2e-test-flow ✅   dev-workflow ✅   pipeline ✅
```

它们物理上无法派发子 Agent 去调 `inspect`。两条常见解法都不好：给五个只读 skill 加 `Task` 是能力扩张；让 `verify` 这类原子 skill 再派发子 Agent，与 `constraints.md §3` 的「编排层 → 原子 skill」分层相悖。

**采用第三条**：`constraints.md §3` 的最小握手协议本就有 `inputs` 字段。

- **编排层**（`pipeline` / `feature` / `bugfix` / `dev-workflow`，均有 `Task`）在流程开头调一次 `inspect`，把 `workspace_context` 随握手下传
- **原子 skill** 从 `inputs.workspace_context` 读，**不需要 `Task`、不嵌套、不改权限**
- **单跑**（用户直接 `/ms-verify`，无编排层）：无 `workspace_context` → 按 `inline` 缺省 + ℹ️ 提示「shell 项目请经编排层调用」。shell 是少数场景，单跑原子 skill 本就是次要路径

消费方依赖的是**入参形状**，不是声明文件或 `.gitmodules` —— 「依赖接口而非实现」照样成立。

这需要在 `constraints.md §3` 的握手字段表新增一行 `workspace_context`（可选）。

### 2.3 验证契约

**每次写入后重新执行 `inspect`**，核对配置、`.gitmodules`、实际目录、分支状态与子模块指针。⛔ 不得以「命令退出码为 0」代表完成。

### 2.4 commit 所有权

「谁干活谁提交」逐层落实：

| 谁 | 提交什么 |
|---|---|
| `workspace-topology` | **自己产生的**：`.gitmodules`、`workspace:` 元数据块、迁移中的文件搬运 |
| `ms-dev-workflow` | 它产生的代码与 DevDocs 状态 |
| `ms-bugfix` | 修复代码与 bug 文档 |
| `pipeline` / `retrofit` / `realign` | **只编排，不替被委托 skill 提交** |

⛔ 本 skill **不得**变成「所有流程统一调它代提交」——那反而违背「谁干活谁提交」。现有 N+1 提交纪律留在 `references/protocol.md`，由干活的 skill 按条文执行。

## 3. 元数据

### 3.1 独立命名空间

```yaml
---
workspace:
  mode: shell
  code_roots: [web, api]
devdocs:
  docs_layout_version: layout.v1
  initialized_at: "2026-08-05"
---
```

**只抽 skill、不迁出 `devdocs:`，问题没有解决**——那只是把步骤换了位置，误触发依旧。这是本稿相对第 6 稿的核心修正。

### 3.2 兼容与迁移

| 情形 | 行为 |
|---|---|
| 只有 `workspace:` 块 | 正常读取 |
| 只有旧 `devdocs.workspace_mode` / `code_roots` | **只读兼容**；首次 `reconcile` 时迁移到 `workspace:` 并删除旧字段 |
| 两处并存且**一致** | 迁移并删除旧字段 |
| 两处并存且**冲突** | ⛔ 阻塞，由用户裁决以哪处为准 |
| 字段跨两处拆分（如 `mode` 在新、`code_roots` 在旧） | ⛔ 阻塞——拼接两处声明会让「以哪处为准」失去单一答案 |
| 都没有 | `inline`，零影响 |

`code_roots` 比较按**集合**语义，顺序无意义。

### 3.3 所有权

- `workspace-topology` 拥有 `workspace:` 块
- `agent-memory` **停止管理** `workspace_mode` / `code_roots`，改为**原样保留** `workspace:` 块（不得覆写、不得删除）
- `layout-metadata-schema.md` 删除 workspace 字段——它不属于 layout 元数据

### 3.4 校验（fail-closed）

| 情形 | 行为 |
|------|------|
| `shell` 但 `code_roots` 缺失 / 为空 | ⛔ |
| 某 name 不在 `.gitmodules` | ⛔ |
| `code_roots` 有重复 name | ⛔ |
| name 在 `.gitmodules` 但工作区目录为空 | ⛔（运行时）；health 只读扫描降级 ⚠️ |
| 解析出的两个 path 互为前缀 | ⛔ |
| 某 path 为 `.` / 含 `..` / 等于 `docs` | ⛔ |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略 |

### 3.5 §0.3 的裁决

- `workspace/root-residue`：`shell` 下，仓库根不在 `docs/`、不属任何 `code_root` 的**已跟踪文件** → ℹ️ 列清单交用户判断。**不猜是不是源码，也不装作能猜。**

同构矛盾也存在于零污染违约检测（`protocol.md` §5 要求判定「非源码路径」却禁止猜测），裁法一致。

## 4. 可重入（`reconcile`）

**幂等**：重跑后状态一致则 no-op，**不产生空提交**。

**能做到真正幂等的范围**：

| 动作 | 语义 |
|---|---|
| 重新探测 | 扫 `.gitmodules` → 多选代码根（提示语说明「子模块也可能是素材/vendor」）→ 全不选 = `inline` |
| `shell → shell` 调整 `code_roots` | 纯声明变更 |
| 已存在子模块加入管理范围 | 纯声明变更 |
| 新增子模块 | 提供 URL/path 后 `git submodule add` |
| 中断续做 | 从**实际 Git 状态**继续，不依赖「执行到第几步」的脆弱记录 |
| legacy 字段迁移 | §3.2，一次性 |

**两个必须区分的界限**：

1. **「改声明」vs「改真实拓扑」**：`mode` 字段可以改，但 `inline → shell` 的真实拓扑变更是**仓库迁移**（§5），不是改字段。
2. **「从 `code_roots` 移除」vs「删除子模块」**：前者仅表示「不再作为工作代码根」，纯声明；后者会改 `.gitmodules`、gitlink 和本地目录，是**另一项破坏性操作，必须单独确认**，且第一版不自动执行。

**`shell → inline`**：第一版只提供手动规划，不承诺通用自动化（§1.3）。

## 5. 迁移（`migrate`）

### 5.1 两个模式

用户要求：

> 1. 手动模式：保存上下文，建议用户步骤，建一个根仓库，把开源项目放进去，剩余你来整理……
> 2. 自动模式：也是建一个根仓库，把开源项目放进去……

**手动模式不是让用户手工做全部事情，而是让用户处理 Agent 无法安全跨越的工作区边界**（父目录写权限、cwd 迁移）：

1. skill 输出**恢复胶囊**：源路径、分支、`HEAD`、remote、目标结构、文档清单、各项指纹
2. 用户创建或打开目标父级目录，使其成为新的可写 workspace
3. skill 恢复后完成：初始化外壳仓 → 添加子模块 → 迁移受管文档 → 写配置 → 生成代码仓迁出 commit 与外壳仓 commit → **逐项读回验证**
4. push、分支选择、旧 checkout 删除**由用户执行**

**恢复胶囊必须带失效检测**：记录 repo identity/realpath、`HEAD`、baseline、index 指纹、工作树清单、remote ref OID、递归子模块状态。恢复时重新盘点并比较，**任一漂移即让旧胶囊失效**，重新生成并确认受影响步骤。

**自动模式**仅在以下前置**全部满足**时启动：

- 父目录在当前写入范围内
- 源仓干净、处于具名分支、存在 remote/upstream
- 目标路径不存在或为空
- 完整 dry-run 已列出路径、文件、提交并经确认

### 5.2 两模式共同的禁止项

⛔ rebase / filter / squash / force-push　⛔ 自动 push　⛔ 自动删除原 checkout
⛔ 把代码仓自有文档一并迁走（§1.2）　⛔ 在 detached HEAD 上提交　⛔ 把已有脏改动混入迁移 commit

### 5.3 挂子模块（实测确定的唯一正确序列）

被删七步用 `git submodule add <remote URL>`，那是**从远端重新 clone**，本地未推送工作全丢。改用本地路径也不行——现代 git 直接 `fatal: transport 'file' not allowed`（CVE-2022-39253 后默认禁 file 传输）。

**实测通过的序列**（2026-08-24，本机 git）：

```bash
mkdir W && cd W && git init && git commit --allow-empty -m "chore: init shell workspace"
mv ../myproj ./myproj                     # 先物理移动，工作区原样带过去
git submodule add ./myproj myproj         # → "Adding existing repo at 'myproj' to the index"，不 clone
git config -f .gitmodules submodule.myproj.url <子模块自身的 remote URL>
git add .gitmodules myproj && git commit
```

实测结果：未推送提交、staged 文件、untracked 文件**全部保留**，子模块工作区状态原样，子模块保留自己的 `.git` 目录（不走 `.git/modules/`）。

⚠️ **`.gitmodules` 的 url 修正是完成门，不是可选提醒**：`./myproj` 不指向当前磁盘目录，而是**相对外壳仓默认远端解析**，别人 clone 会得到不存在的嵌套 URL（git 官方说同级仓库应用 `../foo.git`）。第一版处置：无可访问 URL 时保留本地 url，但**阻止「迁移完成 / 可分享」状态**，并在报告中明确列出。

⚠️ **挂载只登记 gitlink 指向的 commit**。「保住工作区现状」只对**当前这台机器**成立；别人 clone 只拿得到那个 commit。报告须列出「仅存在本机、尚未进入可达 commit」的成果。

### 5.4 状态盘点取代前置门

旧七步的 Step 1 前置门（`git status --porcelain` 非空 ⛔、`rev-list @{u}..HEAD` 非 0 ⛔）**会把唯一真实场景挡在门外**——clone 开源项目并用 DevDocs 开发过，状态必然二者居其一。

改为盘点后分类处理。但**不是全部放行**，以下默认阻塞（它们会在移动之后才失败，恢复变成手工仓库手术）：

- 未解决的 unmerged index
- 进行中的 merge / rebase / cherry-pick
- linked worktree / separate gitdir

普通脏工作树（有未提交改动 / untracked）在完成 §5.5 快照后允许继续。

### 5.5 备份

⚠️ **`git branch backup/...` 只指向 `HEAD`**，不含 staged、unstaged、untracked、ignored、嵌套子模块脏工作树。目标场景中最重要的未提交成果**不在里面**。

第一版做法：**保留原仓完整物理副本**，直到迁移后逐项读回验证全部通过。⛔ 禁止用 `reset --hard` 恢复脏工作树。

物理迁移采用 **copy → 校验 → 切换 → 延迟删除**，不用直接 `mv`（跨文件系统移动非原子）。§5.3 的实测序列在有完整副本兜底时才可用 `mv` 简写。

### 5.6 失败恢复

失败后必须能通过**重新运行 `reconcile` / `migrate` 从实际状态恢复**，而不是依赖「执行到了第几步」的脆弱记录。

## 6. 影响面

### 6.1 新建 / 搬迁

```
skills/workspace-topology/
  SKILL.md                     三入口 / 幂等规则 / 提交所有权 / 输入输出契约
  references/protocol.md       ← git mv skills/_shared/workspace-mode.md
                                 （保留仍有效的校验、零污染、N+1 仓规则）
  references/migration.md      ← git mv skills/pipeline/references/layout/workspace-shell.md
                                 （重写：双模式、恢复胶囊、§5.3 实测序列；删迁移七步与历史优化）
```

### 6.2 解除 DevDocs 所有权

| 文件 | 动作 |
|---|---|
| `_shared/constraints.md:292–299` | 删除 workspace 协议 SSOT 小节，改为指向新 skill 的一行 |
| `_shared/constraints.md §3` | 握手字段表**新增** `workspace_context`（可选，§2.2） |
| `layout/layout-metadata-schema.md:27–28, 45, 54` | 删除 workspace 字段——不属 layout 元数据 |
| `agent-memory/SKILL.md:180–264` | 停止管理 `workspace_mode`/`code_roots`；改为原样保留 `workspace:` 块 |
| `pipeline/SKILL.md:208` | 改委托 `/workspace-topology reconcile` |
| `retrofit/SKILL.md:177, 179` | 同上 |
| `realign-scope-layout.md:82–85, 156, 229` | 移除 workspace 迁移实现，最多提示转 `/workspace-topology` |

### 6.3 消费方改为读 `inputs.workspace_context`（10 处）

`dev-flow` / `dev-workflow`（+ `task-orchestration.md` / `verification-flow.md`）/ `bugfix` / `test-run` / `verify` / `codebase-insight` / `code-self-describe` / `e2e-test-flow`

⚠️ 本批只改**拓扑事实的获取方式**，不改任何算法。算法层的单仓假设（25 处）归配对 spec。

### 6.4 health 改为委托接口

`realign-scope-health.md:33, 95, 167`、`health-lint-implementation.md:27, 389, 391, 405, 409, 453` —— 不再自行解析 `code_roots` 与 `mode`。

### 6.5 文档

`README.md`（39→40、17→18，增加独立入口）、`AGENTS.md`、`docs/architecture.md`、`docs/workflows.md:333`。

**无需改动**：`.claude-plugin/plugin.json`（按整个 `skills/` 目录发现）、`scripts/deploy-skills.sh`（自动遍历带 `SKILL.md` 的目录）—— 已核。

### 6.6 spec_version bump

`workspace-mode.v1` → `workspace-topology.v1`（搬迁 + 元数据命名空间变更）、`shared-constraints.v4` → `v5`（§3 握手字段 + §10 删除）、`agent-memory`、`layout-metadata-schema`。

## 7. 验证

**本仓**

1. `grep -rn "workspace_mode\|workspace-shell" skills/` —— 现役消费方零命中（历史 spec / 台账不计）
2. `grep -rn "\.gitmodules" skills/ | grep -v workspace-topology` —— 仅 `constraints.md` 的规则条文本身可出现
3. 逐消费方确认显式使用 `inputs.workspace_context`，不读声明文件、不解析 `.gitmodules`
4. `agent-memory` 跑一次，确认 `workspace:` 块**原样保留**
5. 新 SKILL.md ≤ 500 行；`realign --scope=health` 的 `dead-link` rule 全过

**真实项目（挂账）**

6. `chiaki-ng-dev`（legacy 位置声明）跑 `reconcile`：确认迁移到 `workspace:`、旧字段删除、再跑 no-op 且**无空提交**
7. 非 DevDocs 项目跑 `reconcile`：确认只产生 `workspace:` 块、不触发任何 DevDocs 流程 —— **§0.1 的验收**
8. 「clone 开源项目 + 已用 DevDocs 开发（工作区脏 + 有未推送提交）」跑 `migrate` 两模式：不被前置门挡住、未推送工作仍在、`.gitmodules` url 未修正时**阻止「完成」状态**、历史**未被改写**

## 8. 待审查者重点质疑

1. **§2.2 的握手传播是否真闭合** —— 单跑原子 skill 时按 `inline` 缺省 + ℹ️ 提示，shell 项目单跑会静默按错误拓扑工作。这个降级可接受吗？
2. **§3.3 的所有权切换是否会与 `agent-memory` 的现有写入逻辑冲突** —— 它今天按字段白名单管理，改为「原样保留一个它不认识的块」是否需要新机制。
3. **§5.5 的「完整物理副本」在大仓上是否现实** —— 开源项目动辄数 GB，副本 + 延迟删除的磁盘与时间代价。
4. **§5.3 的 url 修正作为完成门** —— 用户没有 fork 时迁移永远停在「未完成」，这个状态会不会成为常态而失去意义。
5. **21 处改动是否仍可一批落地** —— 前六轮 R4 F-307 曾判「不可分批发布」。本稿的消费方改动只涉及获取方式不涉及算法，这个判断是否随之变化。
