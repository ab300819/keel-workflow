---
name: workspace-topology
description: 维护仓库的工作区拓扑声明——代码与文档同仓（inline）还是文档在外壳仓、代码作 git 子模块（shell）。三个入口：inspect 返回稳定的拓扑上下文供其他流程消费，reconcile 交互式维护声明（幂等、可重入、支持增删代码根与新增子模块），migrate 把单仓改造成外壳布局（手动/自动双模式）。独立于 DevDocs，非 DevDocs 项目也可单跑。Triggers on "/workspace-topology", "工作区模式", "外壳仓", "shell 模式", "inline 模式", "代码根", "code_roots", "把项目转成子模块", "文档和代码分仓", "workspace mode", "submodule 布局". NOT for DevDocs 文档结构升级（用 /ms-pipeline realign --scope=layout）、记忆文件维护（用 agent-memory）、代码盘点（用 ms-codebase-insight）。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
metadata:
  spec_version: workspace-topology.v1
  interaction: multi-turn
user-invocable: true
---

# Workspace Topology

**管仓库的形状：代码在哪、文档在哪。不管代码内容，不管文档内容。**

两种形状：

| 形状 | 代码 | 文档 |
|---|---|---|
| `inline`（缺省） | 仓库根 | `<仓库根>/docs/` |
| `shell` | 各 git 子模块下 | `<仓库根>/docs/` |

**文档根两种形状下都是 `docs/`**，这是固定不变量，不设配置字段。变的只有代码在哪。

`shell` 服务两类零污染场景：维护开源项目（自己的文档不能进上游仓）、自有项目待公开。

## 三个入口

| 入口 | 做什么 | 写文件吗 |
|---|---|---|
| `inspect` | 返回拓扑上下文，供其他流程消费 | 否 |
| `reconcile` | 交互式维护声明（幂等，可重入） | 是 |
| `migrate --to shell --mode manual\|auto` | 单仓 → 外壳布局的仓库改造 | 是 |

无参数调用等同 `reconcile`。

## inspect

只读。返回 `yaml-summary-v1`，拓扑上下文落 `summary.details`：

```yaml
schema: workspace-context.v1
mode: inline | shell
workspace_root: /abs/path
docs_dir: docs
code_roots:
  - {name: api, path: services/api}
  - {name: web, path: web}
```

`inline` 时 `code_roots` 为单项 `{name: ".", path: "."}`——**调用方不分支**，inline 也是一个代码根。

### 消费方怎么拿到它

⛔ **不要求消费方自己调本 skill**。多数原子 skill 的 `allowed-tools` 没有 `Task`，无法派发子 Agent；让它们自己读声明文件又会把实现细节泄漏出去。

走 [constraints.md §3](../_shared/constraints.md) 的最小握手协议：

- **编排层**（`ms-pipeline` / `ms-feature` / `ms-bugfix` / `ms-dev-workflow`）在流程开头调一次 `inspect`，把 `workspace_context` 随握手的 `inputs` 下传
- **原子 skill** 从 `inputs.workspace_context` 读，不需要 `Task`
- **单跑**（用户直接调某个原子 skill，无编排层）：无 `workspace_context` → 按 `inline` 缺省 + ℹ️ 提示「shell 项目请经编排层调用」

消费方依赖的是**入参形状**，不是声明文件、不是 `.gitmodules`。

## reconcile

交互式维护声明。**幂等：状态一致则 no-op，不产生空提交。**

| 动作 | 语义 |
|---|---|
| 重新探测 | 扫 `.gitmodules` → AskUserQuestion 多选哪些是代码根（提示语必须说明「子模块也可能是素材 / vendor，不都算代码根」）→ 全不选 = `inline`。无 `.gitmodules` 时静默判 `inline`，不打扰用户 |
| 调整 `code_roots` | 纯声明变更 |
| 已存在子模块加入管理范围 | 纯声明变更 |
| 新增子模块 | 用户给 URL 与路径 → `git submodule add` → 追加 `code_roots` |
| 退出 `code_roots` | **仅退声明**，表示「不再作为工作代码根」。⛔ 不动 `.gitmodules`、不动本地目录 |
| legacy 字段迁移 | 见下方「元数据」，一次性 |
| 中断续做 | 从**实际 git 状态**继续，不依赖「执行到第几步」的记录 |

**两个必须区分的界限**：

1. **改声明 ≠ 改真实拓扑**。`mode` 字段可以随便改，但 `inline → shell` 的真实拓扑变更是仓库改造，走 `migrate`。
2. **退出 `code_roots` ≠ 删子模块**。后者会改 `.gitmodules`、gitlink 和本地目录，是破坏性操作，本 skill **不做**，交用户自行执行。

**写入后自校验**：立即重跑校验全表，任一 ⛔ → 回滚本次写入并报告。⛔ 不得以「命令退出码为 0」代表完成。

**`shell → inline`**：只给手动规划，不承诺自动化——多代码根时「合并进哪个仓 / 是否保留外壳历史 / 多远端怎么处理」没有安全默认答案。

## migrate

见 [references/migration.md](references/migration.md)。要点：

- **仅由用户显式意图触发**，本 skill 永不主动提议——那是产品决策，不是规范差距
- 两个模式的分界在**谁把代码仓挪进根目录**：手动模式下用户处理这个跨工作区边界的动作（父目录写权限、cwd 迁移），其余仍由本 skill 完成
- 顺序是硬约束：建壳 → 整仓 `mv` 进去 → `submodule add` 登记 → 复制文档 → **校验复制到位** → 才删原件 → 写声明 → 推送收尾
- ⛔ 不做 rebase / filter / squash / force-push；⛔ 不静默 push；⛔ 不自动删除原 checkout；⛔ 不把代码仓自有文档（API 文档、README 资料）一并迁走

## 元数据

声明在项目根 `AGENTS.md` frontmatter 的**独立 `workspace:` 块**：

```yaml
---
workspace:
  mode: shell
  code_roots: [web, api]      # mode=shell 时必填，元素为 .gitmodules 的 submodule name
devdocs:                      # DevDocs 项目才有；非 DevDocs 项目只有 workspace: 块
  docs_layout_version: layout.v1
---
```

**为什么独立成块**：这是仓库级事实，不是 DevDocs 事实。挂在 `devdocs:` 下会让「声明一个仓库设定」必须经过 DevDocs 流程。

**路径真源是 `.gitmodules`**，`code_roots` 只记 submodule name，运行时经 `git config -f .gitmodules submodule.<name>.path` 解析。子模块换路径只改 `.gitmodules`，声明不用跟。

### 所有权

| 谁 | 拥有什么 |
|---|---|
| `workspace-topology` | `workspace:` 块 |
| `agent-memory` | 正文 + `devdocs:` 块；⛔ 对 `workspace:` 块**原样保留**，不覆写不删除 |

### legacy 兼容

旧版本把字段放在 `devdocs.workspace_mode` / `devdocs.code_roots`。

| 情形 | 行为 |
|---|---|
| 只有 `workspace:` 块 | 正常读取 |
| 只有 legacy 字段 | **只读兼容**；`reconcile` 时迁移到 `workspace:` 并删除旧字段 |
| 两处并存且**一致** | 迁移并删除旧字段 |
| 两处并存且**冲突** | ⛔ 阻塞，由用户裁决以哪处为准 |
| 字段跨两处拆分（`mode` 在新、`code_roots` 在旧） | ⛔ 阻塞——拼接两处声明会让「以哪处为准」失去单一答案 |
| 都没有 | `inline`，零影响 |

`code_roots` 比较按**集合**语义，顺序无意义。

## 校验（fail-closed）

| 情形 | 行为 | 恢复方式 |
|---|---|---|
| `shell` 但 `code_roots` 缺失 / 为空 | ⛔ | 跑 `reconcile` 补声明 |
| 某 name 不在 `.gitmodules` | ⛔ | 该子模块被改名或删除 → 跑 `reconcile` 修正声明 |
| `code_roots` 有重复 name | ⛔ | 跑 `reconcile` 去重 |
| name 在 `.gitmodules` 但工作区目录为空 | ⛔（运行时）/ ⚠️（health 只读扫描） | `git submodule update --init <path>` |
| 解析出的两个 path 互为前缀（嵌套子模块） | ⛔ | 嵌套子模块属依赖项，不该进 `code_roots`；跑 `reconcile` 移除内层 |
| 某 path 为 `.` / 含 `..` / 等于 `docs` | ⛔ | 路径非法，修 `.gitmodules` |
| `inline` 却出现 `code_roots` | ⚠️ 警告并忽略 | 跑 `reconcile` 清理 |

## 仓根残留文件

`shell` 下，仓库根不在 `docs/`、不属任何 `code_root` 的**已跟踪文件** → ℹ️ 列清单交用户判断。

⛔ **不猜哪个算源码**。上游仓目录约定各异，静态白名单会误伤。列出来，让人看。

## 提交

**谁干活谁提交**：本 skill 提交自己产生的东西（`.gitmodules`、`workspace:` 块、迁移中的文件搬运），不替别的 skill 提交，也不被别的 skill 用来代提交。

跨仓提交协议（`shell` 下 Commit 1 展开为 N+1 仓）见 [references/protocol.md](references/protocol.md)，由干活的 skill 按条文执行。

## 详细协议

- 校验全表、零污染写入范围、N+1 仓提交协议、gitlink 排除：[references/protocol.md](references/protocol.md)
- 迁移双模式、探测步骤、detached HEAD 处置、指针漂移修复：[references/migration.md](references/migration.md)
