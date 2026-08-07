# DevDocs 外壳工作区模式（workspace_mode: shell）设计

> 状态：设计定稿 · 日期：2026-08-05
> 定位：**跨 skill 协议层新增一个正交维度**，与 layout / id / trace 三层版本号并列但互不耦合

## 1. 问题与定位

现状：DevDocs 假设**文档与代码同仓** —— `docs/devdocs/` 与源码共处一个 git 仓库。

两类真实场景不成立：

1. **维护开源项目** —— 项目仓是 fork 的上游仓，DevDocs 的需求/设计/任务/洞察都是私有产物，塞进上游仓即污染
2. **自有项目但计划公开** —— 同上，且需要在公开前就保持代码仓干净

目标布局（参照 `chiaki-apple-dev` / `chiaki-ng-dev`）：

```
<project>-dev/                    # 外壳仓（私有）
├── AGENTS.md / CLAUDE.md         # 治理元数据 + 工作流路由
├── .gitmodules
├── docs/                         # DevDocs 全部产物，路径与同仓模式完全一致
│   ├── devdocs/
│   ├── prd/
│   └── codebase-insight.md
├── web/                          # 子模块 = 代码根之一
└── api/                          # 子模块 = 代码根之二
```

### 关键事实：docs 路径不变

外壳仓根下依然是 `docs/devdocs/`，仓内 280 处 `docs/devdocs` 硬编码引用原样成立。真正改变的只有两件事：

1. **代码根 ≠ 仓库根** —— 碰代码的 skill 现在假设代码在 cwd 根
2. **N+1 个 git 仓** —— 文档提交进外壳仓，代码提交进各子模块仓，外壳仓额外跟子模块指针

### 与 layout 版本的关系（为什么不做成 layout.v1-shell）

layout 版本管的是 **docs 内部结构**；workspace mode 管的是 **docs 与代码的仓库关系**。docs 结构在本方案下一个字节没变。塞进版本矩阵会让 `layout × id × trace` 变四维，且每个 skill 的兼容性 frontmatter 都要改。因此作为**正交维度**独立建模。

## 2. 元数据与探测

### 2.1 frontmatter 字段

外壳仓根 `AGENTS.md` 已有的 `devdocs:` 段新增两字段：

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

**`code_roots` 记 submodule name 而非路径。** `.gitmodules` 是路径与 URL 的唯一真源，运行时用 `git config -f .gitmodules submodule.<name>.path` 解析。这样：

- 子模块换路径只改 `.gitmodules`，frontmatter 不用跟，不会漂
- 「name 不在 `.gitmodules`」能区分「被改名/删了」与「路径临时不存在（未 submodule update）」，两种情形提示不同
- 「必须是 git 子模块」这条校验由构造保证，不用单独判

### 2.2 校验规则（fail-closed）

| 情形 | 行为 |
|------|------|
| 无 `workspace_mode` 字段 | 视为 `inline` —— 现存所有项目零影响 |
| `shell` 但 `code_roots` 缺失 / 为空 | ⛔ 阻塞 |
| 某 name 不在 `.gitmodules` | ⛔ 阻塞，提示修 frontmatter |
| name 在 `.gitmodules` 但工作区目录为空 | ⛔ 阻塞，提示 `git submodule update --init <path>` |
| 解析出的两个 path 互为前缀（嵌套子模块） | ⛔ 阻塞 |
| 某 path 为 `.` / 含 `..` / 等于 `docs` | ⛔ 阻塞 |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略，不阻塞 |

### 2.3 探测

**仅在 init / retrofit / `realign --scope=layout` 执行一次；运行时只认 frontmatter，不重新探测。**

读 `.gitmodules` → 列出全部 submodule name → AskUserQuestion **多选**哪些是代码根（子模块也可能是素材 / vendor，不都算）→ 写入 frontmatter。`.gitmodules` 不存在或无条目 → 默认 `inline`，不追问。

### 2.4 归属判定

某文件属于哪个代码根，用**解析后路径的前缀匹配**。落在仓库根下、不属任何 `code_roots` 且不在 `docs/` 里的源码文件 → ⚠️ 提示（外壳仓不该有代码）。此判定同时是 §4 提交分组的依据。

### 2.5 多代码根是一等场景

`code_roots` 是列表，N=1 是退化情形，不做特判。

多代码根**不同于**已被证伪的「多需求并行」：后者错在把无关的东西塞进一个上下文；这里是**一个上下文天然跨多个有依赖关系的仓**（如 API 契约变更同时落在 `api` 和 `web`）。由此推出四条下游后果，分别在后续章节落地：

1. 一个 T-XX 可横跨多仓 → 任务不绑定单一仓，提交按变更实际落点分组（§4）
2. 跨仓原子性不存在 → 必须给 Recovery（§4.4）
3. codebase-insight 要盘 N 个仓并**显式记录仓间关系**（依赖方向、接口契约面）（§5）
4. 工作区洁净检查扩到 N+1 个仓（§4.5）

## 3. 零污染写入范围

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

## 4. N+1 仓提交协议

### 4.1 映射

现有「Commit 1 代码 + Commit 2 文档」直接展开：

- **Commit 1** → 每个**有变更的**代码根一个 commit
- **Commit 2** → 外壳仓一次 commit，含文档变更 + 所有变更子模块的指针 bump

### 4.2 严格顺序

1. **前置门（逐个变更子模块）**：`git -C <path> symbolic-ref -q HEAD` 检查是否在具名分支上。子模块默认 detached HEAD，此状态下提交产生**游离 commit** —— 指针 bump 后代码看似在、实际无分支引用，且 `git gc` 后可能丢失。detached → ⛔ 阻塞，提示 `git -C <path> checkout <branch>`。**这是本布局最容易踩且最难察觉的坑。**
2. 逐个变更子模块提交
3. 外壳仓 `git add docs/ <各变更 path>` → 一次提交

### 4.3 commit message 契约与追溯枢纽

| 仓 | 风格 | 编号 |
|----|------|------|
| 子模块 | 沿用**该仓自身**的提交历史风格（`/commit-convention` 的「优先沿用已有风格」正好适用） | **不带** T-XX / F-XX —— DevDocs 编号对上游是噪声，也是零污染的一部分 |
| 外壳仓 | 本仓 Conventional Commits | 带 T-XX，body 列 `web@a1b2c3d` / `api@e4f5g6h` |

**追溯枢纽 = 外壳仓 commit。** 正向：T-XX → 外壳仓 commit → 各子模块 SHA。反向：子模块 SHA → 外壳仓 `git log -S<sha>` → T-XX。子模块自身干净得像没有 DevDocs 存在过。

**`--single-commit` 在 shell 下不可用** —— 跨仓无法合并为单 commit，⚠️ 忽略该 flag 并提示。

### 4.4 跨仓 Recovery

跨仓无真原子性。按失败点分三类，均按共享约束 §7 Recovery 格式输出：

| 失败点 | 残留状态 | 恢复方式 |
|--------|---------|---------|
| 第 k 个子模块提交失败（k>1） | 前 k−1 仓已提交，追溯链未建立 | 报告已提交 SHA 列表 + 剩余 root，AskUserQuestion（续提 / 人工回滚 / 终止）。**不自动回滚已提交的代码** |
| 全部子模块已提交，外壳仓提交失败 | 代码在，文档与指针没跟 | 最轻。给出精确命令重跑外壳仓提交 |
| 外壳仓已提交但漏 bump 某指针 | 指针滞后 | `git submodule status` 可检出，由 `verify` / `realign --scope=health` 捕获并提示补 bump |

### 4.5 断点续做扩展

dev-workflow Step 1 状态检测现为四重验证（文档状态 + 证据复核 + Git 历史 + 工作区）。shell 下改两维、加一维，变为**五重**：

- **改**：「工作区不相关变更」遍历 N+1 个仓（现在只看一个）
- **改**：「Git 历史有 code+doc commit」判定收紧为 —— 外壳仓存在带该 T-XX 的 commit，**且**其 body 记录的子模块 SHA 与当前指针一致
- **加**：第五维「指针一致性」—— 外壳仓记录的 SHA vs 各子模块实际 HEAD，不一致 → 进 Step 1.5 证据复核，不直接跳过

「证据复核」维（Step 1.5 的 A/B/C/D1/D2/E 六项）本身不改 —— 它复核的是 AC 表、测试、trace、对抗验证证据，与仓库拓扑无关。

`review_pending` 语义不变（状态写在外壳仓文档里，与代码仓无关）。

## 5. 改动清单

### SSOT 与协议层

| 文件 | 改动 |
|------|------|
| `skills/_shared/workspace-mode.md` | **新建** —— 协议正文 SSOT：字段语义、校验表、归属判定、零污染红线、N+1 提交协议、Recovery 三类 |
| `skills/_shared/constraints.md` | 新增 §10「工作区模式」——**仅指针 + 字段枚举**，约 8 行 |
| `skills/pipeline/references/layout/workspace-shell.md` | **新建** —— 操作手册：探测步骤、inline→shell 迁移（§6）、detached HEAD 处置、指针漂移修复 |
| `skills/pipeline/references/layout/layout-metadata-schema.md` | §1 schema 增两字段 + 校验规则 + 缺失行为表 |

**为什么协议正文不放 constraints.md**：该文件 frontmatter 声明 `status: 现状提取，不引入新规则`，条款 `doc/status-extraction` 明确禁止引入新执行语义（§9 当初即以「不新增运行时强制」声明合规）。塞入一整节新协议正文属违章。其 `doc/reference-over-copy` 条款要求的正是「详细 spec 保留在原位置，本文只声明协议层共性与指针」——故正文落 `_shared/workspace-mode.md`（跨 skill 共享命名空间，与 constraints.md 平级），constraints.md §10 只留指针。此形态同时避开了「跨 skill 协议落在 pipeline 私有目录」的问题。

### 编排与治理层

- `skills/pipeline/SKILL.md` —— init / retrofit 探测步骤
- `skills/pipeline/references/realign-scope-layout.md` —— 探测与修复流程、迁移子流程
- `skills/pipeline/references/realign-scope-health.md` + `health-lint-implementation.md` —— 新增 rule `submodule-pointer-drift`，**仅 shell 模式生效**

### 消费侧指针（每处 1–3 行）

| skill | 要点 |
|-------|------|
| `dev-workflow/SKILL.md` | 提交约束 + 断点续做 + 自描述跳过 |
| `dev-workflow/references/task-orchestration.md` | 状态检测扩 N+1 + 指针一致性维 |
| `bugfix` | 同 dev-workflow 的提交与洁净检查 |
| `dev-flow` | 原子提交扩 N+1 |
| `codebase-insight` | 盘 N 个仓 + **显式记录仓间关系** |
| `test-run` | 测试命令在哪个 code_root 下执行 |
| `verify` | `--impl` 的扫码路径 |
| `e2e-test-flow` | 源码定位路径 |
| `code-self-describe` | shell 默认跳过 + `--force-code-docs` |

### 文档层

本仓 `AGENTS.md` 当前状态 · `docs/architecture.md` 文件结构节加 shell 布局图 · `docs/workflows.md` 用户面「怎么开 shell 模式」

### 版本号处置

`spec_version` 追踪的是 **A/B 类文档产物模板**，常量位于各 skill `references/realign.md` 顶部（`realign/current-constant-location`）。核对结果：

- **不 bump 任何 skill 的 `spec_version`。** 本方案不改任何产物模板的必填章节 / 字段 / 结构，只改流程规则。且 `bugfix` / `codebase-insight` / `verify` / `test-run` 本就没有 `references/realign.md`（不产受 realign 管的模板产物），无从 bump
- **不 bump layout 版本。** `layout-metadata-schema` 只加**可选**字段，无该字段的 layout.v1 项目仍然合法
- **bump `constraints.md` 自身 `spec_version`：`shared-constraints.v1` → `shared-constraints.v2`**（新增 §10 属结构变更），并在 frontmatter `related` 列表补 `skills/_shared/workspace-mode.md`
- **不新增 realign scope**（复用 `layout` + `health`，守 `scope-enum-authority`）

## 6. inline → shell 迁移

要做的是一次**仓库手术**：单仓 R（code + docs 混在一起）→ 外壳仓 W + R 作为 W 的子模块。R 保留全部历史并继续当代码仓，W 是新建的空仓。

### 6.1 入口

复用 `/ms-pipeline realign --scope=layout`，**不新增 scope、不加 flag**。**由用户显式意图触发** —— realign 自身永不主动提议做仓库手术，那是产品决策而非规范差距。用户表达「把这个项目转成外壳模式」，pipeline 路由至此。

### 6.2 七步，dry-run 优先

| 步 | 动作 | 门 |
|----|------|-----|
| 1 | 前置检查：R 工作区干净、有 remote、无未推送提交 | 任一不满足 ⛔ 阻塞 —— 手术前必须有远端兜底 |
| 2 | 输出完整计划（建哪个仓、移哪些文件、产生哪几个 commit），AskUserQuestion 确认 | 未确认不动任何文件 |
| 3 | 在 `../<R名>-dev` 建 W（`git init` + 初始 commit），路径可覆盖 | 目标已存在 ⛔ |
| 4 | `git submodule add <R 的 url> <name>` | |
| 5 | 迁移 DevDocs 产物到 `W/docs/`；R 根 `AGENTS.md` 的 `devdocs:` 治理段迁到 `W/AGENTS.md`；委托 `agent-memory --update` 补工作流路由节 | 见 6.2.1 迁移范围 |
| 6 | R 内 `git rm -r` 已迁走的路径 + 清掉 `devdocs:` frontmatter → commit `chore: 迁出 DevDocs 产物` | **不自动 push**，提示用户自行推送 |
| 7 | W 写 `workspace_mode: shell` / `code_roots: [<name>]`，bump 子模块指针，commit | |

每步失败都给 Recovery（§7 格式）。步序刻意设计成**前 5 步全部可逆**（只新增不删除）；唯一不可逆的删除集中在第 6 步，且此时 W 已完整。

#### 6.2.1 迁移范围：只搬 DevDocs 产物，不搬整个 docs/

`docs/` 里未必只有 DevDocs 产物 —— 用户面文档、API 文档、架构图等属于代码仓，搬走反而是错的。

- **无条件迁移**：`docs/devdocs/`、`docs/prd/`、`docs/codebase-insight.md`
- **留在 R**：`docs/` 下其余内容
- **逐项确认**：第 2 步的 dry-run 计划里列出 `docs/` 下所有未分类条目，AskUserQuestion 让用户决定去留

第 6 步的 `git rm` 只删已确认迁走的路径，不是 `git rm -r docs/`。

### 6.3 明确不做

1. **不重写 R 的历史。** docs 仍留在 R 的历史里。若 R 已公开且历史含私有内容，泄露已发生，迁移救不回来 —— 只提示 `git filter-repo` 这条路存在，**绝不代执行**。
2. **不搬 docs 的 git 历史到 W。** W 的 `docs/` 从一个干净 commit 起步。要考古去 R 的历史查，成本远低于 subtree split 的复杂度与风险。
3. **不自动 push、不删 R 本地目录、不动 R 里除 `docs/` 和 `AGENTS.md` 外的任何文件。**

### 6.4 反向迁移（shell → inline）不提供

无真实动机，YAGNI。

## 7. 不在本方案范围

- **upstream 协作** —— fetch / rebase / 建分支 / 开 PR 全部交给 git 和用户。本方案只解决布局、代码根、提交协议
- **多 workspace_mode 并存** —— 一个外壳仓一种模式
- **子模块的 CI / hooks 适配** —— 上游自身的事

## 8. 影响面与验证

### 对现有项目零影响的论证

所有新增规则的触发条件都是 `workspace_mode: shell`。现存项目 frontmatter 无此字段 → 判为 `inline` → 走原路径。落地后逐条 grep 核对新增规则确实都在 shell 条件下，**无裸露的无条件门**——唯一例外：探测探针本身在 init / retrofit / `realign --scope=layout` 三处对含 `.gitmodules` 的 `inline` 项目可见（如 realign 的 dry-run plan 会多列一条「可选项：未声明工作区模式」），此行为由 §2.3 授权、只在 dry-run 列示不自动改，不影响其余场景。

### 验证策略（规格库，无测试框架）

1. **静态一致性** —— grep 新字段名，确认 SSOT 与 9 个消费点表述一致，无 skill 私自另定规则
2. **真实端到端** —— 拿 `chiaki-ng-dev` 实跑：它已有子模块 + `docs/devdocs/`（散文态），正是 retrofit 的真实样本。跑探测看 frontmatter 是否正确写入，再跑一个最小 T-XX 看 N+1 提交与追溯枢纽是否成型。沿用本仓 board E2E 冒烟 / idea-mcp live 实证的做法
3. **对抗审查** —— `/adversarial-review` 过 codex，重点打：detached HEAD 门、跨仓 Recovery 三类是否穷尽、指针一致性维与现有五项证据复核（Step 1.5 的 A/B/C/D1/D2/E）是否冲突
