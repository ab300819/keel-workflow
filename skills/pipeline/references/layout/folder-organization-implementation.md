# Folder Organization Implementation（#2 文件夹组织实施规范）

> 把 [layout-versioning-policy.md § layout.v2 完整目标态](layout-versioning-policy.md#layoutv2-完整目标态) 的目录树从"宪法层"落实到"执行层"。定义每种编号文件的内容模板、index.md 格式、主文件索引化规则、SSOT 强约束落地点，以及 9 个 A/B skill 在 v1 / v2 双轨下的输出行为。
>
> 与 [id-scheme-implementation.md](id-scheme-implementation.md) 同级：前者治理编号前缀双轨；本文件治理**编号文件的物理组织 + 内容契约**。

## ⚠️ 执行接口当前状态

本文件描述的目录写入 / index.md 自动维护 / 主文件索引化 / SSOT lint 均依赖 [FUTURE] 接口，详见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。

当前阶段（#2 spec 起草）**只产出规范**，runtime 落地由后续阶段实施。所有 skill 的 `writes_layout` 字段保持 `layout.v1`，正文 v1 行为不变；v2 行为已在 spec 中**声明**，但实际切换待 [FUTURE]。

## 定位

| 治理对象 | 文件 |
|---------|------|
| layout.v2 整体目录树宣告 | [layout-versioning-policy.md § layout.v2](layout-versioning-policy.md#layoutv2-完整目标态) |
| 编号前缀双轨（F→FEAT 等）| [id-scheme-implementation.md](id-scheme-implementation.md) |
| **本文件**：编号文件内容 schema + 目录写入规则 + 主文件索引化 | folder-organization-implementation.md |
| 单文件大表 → 多文件迁移路径 | [docs-layout-migration.md](docs-layout-migration.md) |
| SSOT lint 强约束具体规则 | #3 阶段（待起草）|

## layout.v2 目录结构（执行层）

### Core tree（与 foundation 一致）

本节 core tree 与 [layout-versioning-policy.md § layout.v2 完整目标态](layout-versioning-policy.md#layoutv2-完整目标态) 的强制目录树**逐项一致**：顶层 4 文件（`index.md` / `context.md` / `aliases.yml` / `traceability.yml`）+ 7 类编号目录（requirements / design / tests / tasks / issues / patterns / notes）+ 各 owner 文件命名规则。

```text
docs/devdocs/                          # ===== Core tree（layout-versioning-policy.md 强制 =====
  ├── index.md                         # 全局编号索引（type/status/summary/file 汇总）
  ├── context.md                       # 项目稳定上下文（少变；非编号文件，无 frontmatter id 字段）
  ├── aliases.yml                      # 编号别名映射（必须存在，含 frontmatter version: alias.v1）
  ├── traceability.yml                 # 代码-文档追溯（必须存在，含 frontmatter version: trace.v1）
  ├── requirements/
  │   ├── index.md                     # FEAT/STORY/AC 汇总表（按 type 分组）
  │   ├── FEAT-001.md
  │   ├── STORY-001.md
  │   └── AC-001.md
  ├── design/
  │   ├── index.md                     # ADR 索引（含 status 流转）
  │   ├── current.md                   # 全量当前态快照
  │   └── decisions/
  │       └── ADR-001.md
  ├── tests/
  │   ├── UT/
  │   │   ├── index.md
  │   │   └── UT-001.md
  │   ├── IT/
  │   │   ├── index.md
  │   │   └── IT-001.md
  │   └── E2E/
  │       ├── index.md
  │       └── E2E-001.md
  ├── tasks/
  │   ├── index.md
  │   └── TASK-001.md
  ├── issues/
  │   ├── index.md
  │   └── ISSUE-001.md
  ├── patterns/
  │   ├── index.md
  │   └── PATTERN-001.md
  └── notes/
      ├── index.md
      └── NOTE-001.md
```

### 执行层扩展（派生目录，不属 core layout.v2 tree）

下列目录/文件**不在** foundation core tree 中，由本执行层规范派生引入，专门解决运维和拆分场景。**不**触发 foundation `docs_layout_version` bump（属本文件 spec 范围）。

| 派生项 | 用途 | 触发条件 |
|--------|------|---------|
| `_archived/` | 迁移日志 + 归档原文件留痕（如 v1→v2 拆分后保留单文件大表）| `realign --scope=layout` 自动创建；任何归档操作时使用 |
| `design/modules/` 子目录 + `modules/<name>.md` | `current.md` ≥ 1500 行时的拆分载体 | `current.md` 行数触发，见 § design/modules 拆分规则 |
| `tests/index.md` | 三类（UT/IT/E2E）汇总（数量 + 覆盖率快照）| 可选；若存在则由 ms-test-cases 维护 |

### 元目录治理

| 目录 | 用途 | lint 范围 |
|------|------|----------|
| `_archived/` | 迁移日志 + 旧文件原文留痕 | ⛔ 排除（不参与 SSOT lint）|
| `_drafts/` | **禁止使用**（任何临时草稿应直接命名 `<type>/<ID>.md` 配 `status: draft`）| ⛔ 禁止存在；若发现，lint 报错（rule `ssot/no-drafts-dir`）|

## 一文件一编号原则

### 核心规则

**每个 v2 编号必须有唯一 owner 文件**（H1 唯一性）。owner 文件名 = 编号本身（`FEAT-001.md` / `TASK-007.md` 等）。owner 文件落点详见 [layout-metadata-schema.md § 编号清单](layout-metadata-schema.md#3-编号清单idv2) 的"文件落点"列。

### owner vs 引用

| 角色 | 出现形式 | 允许行为 |
|------|---------|---------|
| owner 文件 | `# FEAT-001: <名称>` H1 | 完整内容（描述、AC、追溯）|
| 非 owner 引用 | `[[FEAT-001]]` 或 `[FEAT-001](../requirements/FEAT-001.md)` | 仅链接 / 不重述内容 |

**禁止**：在非 owner 文件中复制 FEAT-001 的描述/AC/追溯内容。

## 编号文件内容契约

### 通用 frontmatter（所有编号文件必填）

> 字段定义对齐权威 schema [layout-metadata-schema.md § 编号 frontmatter](layout-metadata-schema.md#编号-frontmatter每个编号文件的-h1-必须配-frontmatter)。本文件不重复定义字段语义，只示例 v2 落地形态。

```yaml
---
id: FEAT-001
type: feature | story | ac | task | issue | adr | pattern | note | ut | it | e2e
status: draft | active | done | deprecated
summary: "一句话核心诉求（≤ 120 字符）"
owner_section: "## FEAT-001 — 详细需求"     # 本文件中作为 H1 owner 的章节标题
created_at: "2026-05-18"
updated_at: "2026-05-18"
links:
  parents: [STORY-001]                       # 上层关联（裸 ID）
  children: [AC-001, AC-002]                 # 下层关联（裸 ID）
  related: [PATTERN-005]                     # 平级关联（裸 ID）
---
```

### YAML 引用 vs 正文引用

| 位置 | 形式 | 示例 |
|------|------|------|
| frontmatter `links.{parents,children,related}` | 裸 ID 数组 | `parents: [STORY-001]` |
| Markdown 正文跨编号引用 | `[[ID]]` 或 markdown 链接 | `[[STORY-001]]` 或 `[STORY-001](STORY-001.md)` |
| 正文文本中提及（非引用）| 反引号 | `` `FEAT-001` `` |

⛔ **禁止**：正文中以纯文本形式（如 `STORY-001`）出现编号 — SSOT lint 会要求改为 `[[STORY-001]]` 或反引号包裹。

### 各类型 body schema

#### FEAT-NNN.md

```markdown
# FEAT-001: <功能名称>

## 描述
<功能描述，1-3 段>

## 优先级
P0 | P1 | P2

## 关联用户故事
- [[STORY-001]]
- [[STORY-002]]

## 设计参考（可选）
- design_context.D-01
```

#### STORY-NNN.md

```markdown
# STORY-001: <故事标题>

## 用户故事
作为 <角色>，我希望 <功能>，以便 <价值>

## 关联功能点
- [[FEAT-001]]

## 关联验收标准
- [[AC-001]]
- [[AC-002]]
```

#### AC-NNN.md

```markdown
# AC-001: <验收标准简述>

## GWT 格式
- **Given**: <前置条件>
- **When**: <触发动作>
- **Then**: <预期结果>

## 关联
- 故事：[[STORY-001]]
- 测试：[[UT-001]], [[IT-001]]
```

#### TASK-NNN.md

```markdown
# TASK-001: <任务名>

## 任务概览
| 字段 | 值 |
|------|---|
| 状态 | 待开发 / 进行中 / 已完成 |
| 优先级 | P0 |
| 依赖 | [[TASK-002]] |
| TDD 模式 | 🔴 强制 / 🟡 推荐 / 🟢 可选 / ⚪ 不适用 |
| 关联需求 | [[FEAT-001]], [[AC-001]] |
| 涉及文件 | `src/services/xxx.ts` |

## 执行步骤
1. [ ] ...

## 验收标准
- [ ] ...

## Review 要点
- [ ] ...
```

#### ISSUE-NNN.md

```markdown
# ISSUE-001: <问题简述>

## 复现步骤
1. ...

## 期望 vs 实际
- **期望**：...
- **实际**：...

## 影响范围
- 模块：...
- 严重程度：P0 / P1 / P2

## 关联
- 修复任务：[[TASK-XXX]]
- 回归测试：[[UT-XXX]]
```

#### ADR-NNN.md

```markdown
# ADR-001: <决策标题>

## 状态
已采纳 | 已废弃 | 已取代

## 背景
<决策上下文>

## 决策
<选择的方案>

## 替代方案
- 方案 A：<...>，被拒原因
- 方案 B：<...>，被拒原因

## 下游影响
<对其他模块/未来工作的影响>

## 关联
- 触发需求：[[FEAT-XXX]]
- 替代关系：[[ADR-XXX]]（被取代）
```

#### PATTERN-NNN.md

```markdown
# PATTERN-001: <模式名称>

## 适用场景
<何时应用此模式>

## 解决方案
<模式描述 + 关键代码片段>

## 反模式
<不要这么做的对照>

## 引用度
- 被 [[FEAT-XXX]] 应用
- 被 [[FEAT-YYY]] 应用
```

#### NOTE-NNN.md

```markdown
# NOTE-001: <观察简述>

## 现象
<观察内容>

## 上下文
<时间 / 场景>

## 后续动作
- [ ] 升级为 PATTERN（如多次重现）
- [ ] 升级为 ADR（如触发决策）
- [ ] 关闭（一次性）
```

#### UT/IT/E2E-NNN.md

```markdown
# UT-001: <测试场景>

## 关联
- AC：[[AC-001]]
- 函数：`src/services/user.ts::validateEmail`

## 输入 / 预期输出
| 场景 | 输入 | 预期 |
|------|-----|-----|
| ... | ... | ... |

## 状态
✅ 通过 / ❌ 失败 / ⏳ 未运行
```

## index.md 格式规范

每个类型目录下必须有 `index.md`，作为该类型编号的**索引表**（非内容副本）。

### 通用格式

```markdown
---
type: index
scope: requirements | design | tests/UT | tasks | issues | patterns | notes
generated_by: ms-<owner-skill>
last_updated: 2026-05-18T10:00:00+08:00
---

# <类型> 索引

| 编号 | 标题 | 状态 | 优先级 | 关联 | 链接 |
|------|------|------|--------|------|------|
| FEAT-001 | 登录功能 | active | P0 | [[STORY-001]], [[STORY-002]] | [文件](FEAT-001.md) |

## 统计
- 总数：N
- 活跃：N
- 已归档：N
```

### 强约束

- ⛔ index.md **不得包含**编号文件的描述/AC/追溯内容（只能有 summary ≤ 120 字）
- ⛔ index.md 必须由 skill 自动维护，禁止手编（除非应急）
- ⛔ summary 列字数 > 120 字 → SSOT lint 报错

### tests/ 二级嵌套

`tests/` 下有 UT/IT/E2E 三个子目录，每个子目录有独立 index.md。`tests/index.md` 必须存在（聚合三类统计：总数 / pass / fail / 覆盖率快照）。

### tasks/index.md sprint 分组格式（特殊）

`tasks/index.md` 在通用索引格式之上**附加 sprint 分组段**：

```markdown
---
type: index
scope: tasks
generated_by: ms-dev-tasks
last_updated: 2026-05-18T10:00:00+08:00
sprint_grouping: enabled
current_sprint: sprint-12
---

# 任务索引

## 当前 Sprint（sprint-12）
| 编号 | 标题 | 状态 | TDD | 优先级 | 关联 | 链接 |
|------|------|------|-----|--------|------|------|
| TASK-187 | ... | 进行中 | 🔴 | P0 | [[FEAT-042]] | [文件](TASK-187.md) |

## 历史 Sprint（折叠）

<details><summary>sprint-11（5 个任务）</summary>

| 编号 | 标题 | 状态 | ... |
| TASK-180 | ... | done | ... |

</details>

## 跨 Sprint 累计统计
- 总任务：N
- 已完成：N
- 进行中：N
```

**强约束**：
- ⛔ 当前 sprint 段必须全展开（非折叠）
- ⛔ 历史 sprint 必须用 `<details>` 折叠（控制阅读长度）
- ⛔ `current_sprint` frontmatter 字段必须与"当前 Sprint"段标题一致

### design/modules/ 拆分规则

当 `design/current.md` ≥ 1500 行时强制拆分到 `design/modules/<module-name>.md`：

| 文件 | 角色 | frontmatter |
|------|------|------------|
| `design/current.md` | 拆分后变成模块导航 + 跨模块上下文 | `type: design-current`，无 `id` 字段 |
| `design/modules/index.md` | 模块清单（名称 + 行数 + 最近修改）| `type: index, scope: design/modules` |
| `design/modules/<name>.md` | 单模块当前态 | `type: design-module`，`module: <name>`，无 `id` 字段 |

**强约束**：
- ⛔ 单 `modules/<name>.md` ≤ 800 行（超出二次拆分）
- ⛔ `modules/` 文件不是编号 owner（无 H1 `# FEAT-XX`），不参与 `links` 反向追溯
- ✅ `current.md` 引用 modules 用 `[模块名](modules/<name>.md)` 形式

## 主文件索引化规则

### docs/devdocs/index.md（全局根）

```markdown
---
type: global-index
generated_by: ms-pipeline
last_updated: 2026-05-18T10:00:00+08:00
---

# DevDocs 全局索引

## 类型导航
- [需求](requirements/index.md) - FEAT / STORY / AC
- [设计](design/index.md) - ADR + current.md
- [测试](tests/) - UT / IT / E2E
- [任务](tasks/index.md) - TASK
- [问题](issues/index.md) - ISSUE
- [模式](patterns/index.md) - PATTERN
- [观察](notes/index.md) - NOTE

## 编号注册表
| 类型 | 已分配最大编号 | 总数 |
|------|--------------|------|
| FEAT | FEAT-042 | 42 |
| TASK | TASK-187 | 187 |
| ...

## 跨类型搜索入口
- 搜索关联：`grep -r "[[FEAT-001]]" docs/devdocs/`
- 搜索 traceability：见 `traceability.yml`
```

### design/current.md（系统设计全量快照）

`design/current.md` 是**例外**：它是全量当前态而非索引（因为系统设计需要整体可读）。但**仍受 SSOT 约束**：

- ⛔ 引用 FEAT/AC 时只能用 `[[ID]]`，不得复制需求描述
- ⛔ ADR 决策只能在 `design/decisions/ADR-NNN.md` 中描述完整，current.md 只 summary
- ⛔ current.md 内容 ≤ 1500 行（触发拆分到 modules/ 子目录）

## v1 → v2 迁移规则

### 单文件大表 → 多文件分散

| layout.v1 | layout.v2 |
|----------|----------|
| `01-requirements.md`（700 行含全部 F/US/AC）| `requirements/{FEAT,STORY,AC}-NNN.md` 多文件 + `index.md` |
| `02-system-design.md`（含全部 ADR）| `design/current.md` + `design/decisions/ADR-NNN.md` |
| `03-test-unit.md`（含全部 UT）| `tests/UT/UT-NNN.md` 多文件 + `index.md` |
| `04-dev-tasks.md`（700 行含 17 sprint 累积）| `tasks/TASK-NNN.md` 多文件 + `index.md`（按 sprint 分组）|
| `BUG-XX.md` 散落各处 | `issues/ISSUE-NNN.md` |
| `patterns/<descriptive>.md` 命名 | `patterns/PATTERN-NNN.md` 编号化 + alias 保留旧名 |

### 迁移命令（[FUTURE]）

```bash
/ms-pipeline realign --scope=layout
```

该命令必须：

1. dry-run：列出所有待拆分文件 + 目标路径 + 预计编号
2. AskUserQuestion 用户确认整体迁移方案
3. apply：执行物理拆分 + 自动生成 `aliases.yml` 条目 + 自动更新 `index.md`
4. 写入 `<迁移日志>.md` 到 `_archived/` 留痕
5. 不可逆操作清单见 [docs-layout-migration.md](docs-layout-migration.md)

### 不强制立即迁移

mic-en 等历史项目维持 layout.v1 不动；任何时候用户主动调用 `realign --scope=layout` 才触发。本阶段（#2）**只产出 spec**，不执行任何项目的迁移。

## 9 个 skill 输出迁移矩阵

各 skill 在 layout.v2 项目下的输出物路径变化：

### A 类 skill

| Skill | v1 输出 | v2 输出 | 章节改造范围 |
|-------|--------|--------|------------|
| `ms-requirements` | `01-requirements.md` 单文件 | `requirements/{FEAT,STORY,AC}-NNN.md` 多文件 + `index.md` | 输出路径切换 + index 维护 |
| `ms-system-design` | `02-system-design.md` 单文件 | `design/current.md` + `design/decisions/ADR-NNN.md` | current.md 拆分 + ADR 独立文件 |
| `ms-test-cases` | `03-test-{unit,integration,e2e}.md` | `tests/{UT,IT,E2E}/<ID>.md` 多文件 + `index.md` | 三类各自分文件 |
| `ms-dev-tasks` | `04-dev-tasks.md` 单文件 | `tasks/TASK-NNN.md` 多文件 + `index.md`（按 sprint 分组）| 任务独立文件 + sprint 索引 |
| `ms-dev-workflow` | 读 `04-dev-tasks.md` | 读 `tasks/<ID>.md` + 写状态回该文件 | 路径切换 |

### B 类 skill

| Skill | v1 输出 | v2 输出 | 章节改造范围 |
|-------|--------|--------|------------|
| `ms-prd-parser` | `docs/prd/<slug>/chunks/` | 不变（PRD 层级不属 DevDocs 内部）| 无路径改动 |
| `ms-prd-brainstorm` | `docs/prd/<slug>/requirements/` | 不变 | 无路径改动 |
| `ms-insights` | `docs/devdocs/05-insights.md` 单文件 | 按 AskUserQuestion 归类后分流：决策类 → `design/decisions/ADR-NNN.md`；经验类 → `patterns/PATTERN-NNN.md`；一次性 → `notes/NOTE-NNN.md` | 拆 3 类后路径分流 + 各自 index 维护 |
| `ms-onboard` | 读 `01~05` 单文件 | 读 `{requirements,design,tests,tasks,...}/index.md` | 路径切换 |

### 编排层 skill

| Skill | 改造点 |
|-------|--------|
| `ms-pipeline` | `init` 模式下创建 v2 目录树骨架；`realign --scope=layout` 执行迁移 |
| `ms-feature` | 增量功能时调用 v2 路径写 FEAT/STORY/AC 文件 |
| `ms-bugfix` | 写 `issues/ISSUE-NNN.md`（v1 写 `BUG-NNN.md`）|

## SSOT 强约束清单（落地到 #3 SSOT lint）

本节列出 layout.v2 必须满足的强约束。每条规则按 lint rule 标准格式描述：`rule_id` / 检测对象 / 算法 / 触发条件 / 严重度。`#3 SSOT lint` 阶段直接据此实现 `/ms-verify --ssot-lint` [FUTURE]。

| rule_id | 检测对象 | 算法 | 触发条件 | 严重度 |
|---------|---------|------|---------|-------|
| `ssot/index-body-clean` | 各 `index.md` body | 解析 H2/H3 + 表格；判定除表格 + 统计段外是否有 ≥ 1 段叙述性内容 | 任意 `index.md` 含非表格非统计的内容段 | P0 |
| `ssot/owner-uniqueness` | 全 repo `*.md` H1 | 提取 H1 `# FEAT-NNN` / `# TASK-NNN` 等编号；按 ID 聚合 | 同一 ID 出现 ≥ 2 个 H1 owner | P0 |
| `ssot/no-restatement` | 非 owner 文件 | 对每编号 owner，取 description+AC 段；与其他文件做 80 字以上 n-gram 相似度（≥ 0.85）| 相似度命中且不是 `[[ID]]` / 链接 | P0 |
| `ssot/aliases-exists` | `docs/devdocs/aliases.yml` | 文件存在 + frontmatter `version: alias.v1` 校验 | 文件缺失或 version 不匹配 | P0 |
| `ssot/traceability-exists` | `docs/devdocs/traceability.yml` | 文件存在 + frontmatter `version: trace.v1` 校验 | 文件缺失或 version 不匹配 | P0 |
| `ssot/agents-frontmatter` | `AGENTS.md` | YAML frontmatter 解析；检查 `devdocs.{id_scheme,docs_layout_version,traceability_version}` | 任一字段缺失或值不在合法枚举 | P0 |
| `ssot/index-summary-length` | 各 `index.md` 表格 summary 列 | 字符计数 | summary 列字数 > 120 字 | P1 |
| `ssot/current-md-size` | `design/current.md` | 行数计数 | 行数 > 1500 | P1 |
| `ssot/legacy-annotation-additions` | 全 repo 代码文件 | diff 模式：对比 baseline commit（layout.v2 升级时间点）vs 当前；提取新增 `@satisfies` / `@verifies` 注释 | baseline 后新增任意一条（legacy 保留行不报）| P1 |
| `ssot/file-size-cap` | 全 repo `*.md`（排除 `_archived/`）| 行数计数 | 单文件行数 ≥ 3000 | P1 |
| `ssot/no-drafts-dir` | 全 repo 目录 | 路径匹配 `_drafts/` | 任意路径含 `_drafts/` 段 | P1 |
| `ssot/modules-size-cap` | `design/modules/*.md` | 行数计数 | 单文件行数 > 800 | P1 |

### baseline 机制（用于 `legacy-annotation-additions`）

- `layout.v2` 升级时，`/ms-pipeline realign --scope=layout` 写入 `_archived/layout-v2-baseline-<commit>.yml`：记录升级时刻的 `git rev-parse HEAD`
- lint 算法：`git diff <baseline-commit>..HEAD --unified=0 -- '*.{ts,tsx,js,jsx,py,go,java}'` 提取新增 `+` 行，grep `@satisfies` / `@verifies`
- 删除 legacy 注释**不报**（diff 中的 `-` 行）；新增**报错**（diff 中的 `+` 行）

## frontmatter 升级规则（条件性）

各 skill `writes_layout` 字段保持 `layout.v1`（当前 transitional state）。**升级到 layout.v2 的触发条件（必须 1+2+3+4 全满足）**：

1. SKILL.md 正文已加入 v2 路径双轨说明 ⏳（本阶段 #2 起草后补）
2. SKILL.md 模板已加入 v2 文件 schema 样例 ⏳（本阶段 #2 起草后补）
3. Runtime 路径切换 + index.md 维护 [FUTURE] 已实现 ⏳
4. 至少 1 个 v2 项目已成功跑过该 skill ⏳

> ⛔ **禁止仅凭 1+2 升级**：满足 1+2 仅代表 spec 准备完成，runtime 行为仍是 v1 单文件输出。提前升级会触发"声明先行陷阱"（frontmatter 声称 v2 但实际输出 v1）。必须 1+2+3+4 全满足才可改：
>
> ```yaml
> writes_layout: layout.v1   # 当前
> writes_layout: layout.v2   # 仅当 1+2+3+4 全满足后升级
> ```
>
> 恢复方式：发现提前升级时，立即回退到 `layout.v1` 并补齐 3/4 条件。

升级 `writes_layout: layout.v2` 时必须同步升级 `writes_id_scheme: id.v2`（按 [layout-versioning-policy.md § 版本号依赖关系](layout-versioning-policy.md#版本号依赖关系) 的强依赖）。

## 历史项目兼容（mic-en 等）

- **mic-en 等 layout.v1 项目**：维持 v1 单文件累积大表，**不动**现有 `01~05` 文件
- 任何时候用户主动调用 `/ms-pipeline realign --scope=layout` [FUTURE] 才触发迁移
- 本阶段（#2）**不执行** mic-en 迁移；仅完成 skill spec 改造

## 与其他阶段的接口

| 阶段 | 接口点 |
|------|-------|
| #1 编号体系 | 已在本文件 § 一文件一编号 / § 编号文件内容契约 中消费 FEAT/STORY/TASK/ISSUE/ADR/PATTERN/NOTE 全部 8 类前缀 |
| #3 SSOT lint | 本文件 § SSOT 强约束清单 直接作为 #3 lint 规则源（12 条 rule_id + baseline 机制）|
| #4 代码解耦 | **本文件定义 traceability.yml 文件存在性约束 + `ssot/legacy-annotation-additions` 禁止新增**；#4 阶段负责：(a) 设计 `traceability.yml` 写入 API（sync/dev-workflow 调用入口）；(b) 从 layout.v1 代码注释批量抽取生成首版 traceability.yml；(c) 定义 legacy `@satisfies` 注释在 layout.v2 项目的保留窗口（默认到 layout.v3）；(d) 多仓库聚合策略。本文件**不**定义抽取算法和写入 API |
| #5 迭代蒸馏 | 本文件 § design/current.md ≤ 1500 行 + § modules/ 拆分规则提供蒸馏触发点；#5 阶段负责定义"蒸馏"的具体动作（current.md → modules 拆分？patterns 引用度合并？sprint 摘要写入 tasks/index.md？）|

## 引用关系

| 引用本文件的位置 | 引用目的 |
|------------|---------|
| 9 个 A/B skill SKILL.md § 输出路径 | v1/v2 路径双轨说明 |
| `skills/insights/SKILL.md` § INS 拆分目录 | ADR/PATTERN/NOTE 各自目录 |
| `skills/pipeline/SKILL.md` § realign | 迁移执行入口 |
| `#3 SSOT lint`（待起草）| 强约束规则源 |

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-18 | 初始版本（#2 文件夹组织实施规范）|
