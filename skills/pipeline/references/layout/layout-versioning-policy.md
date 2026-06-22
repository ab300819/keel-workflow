# Docs Layout Versioning Policy（DevDocs 治理三层版本号宪法）

> DevDocs 治理体系的最高仲裁文件。定义三层版本号语义、升级规则、兼容性策略，作为 `docs_layout_version` / `id_scheme` / `traceability_version` 的 source of truth。
>
> 本文件被 `skills/pipeline/SKILL.md` 与所有 A/B 类 skill 的 `references/realign.md` 共同引用。
>
> ⚠️ **执行接口当前状态**：本文件提及的所有命令（`/ms-pipeline realign --scope=layout` / `/ms-verify --layout-drift` 等）落地状态见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。当前框架处于"仲裁层就绪 / 执行层待补"阶段。

## 定位

`spec_version` 治理单个产物模板的格式（design.v2 / req.v1 等）— 见 [../realign.md](../realign.md)。
本文件治理**比 spec_version 高一层**的对象：DevDocs 整体目录结构、编号体系、代码追溯机制。

| 治理对象 | docs_layout_version | spec_version |
|---------|---------------------|---------------|
| 粒度 | 项目级（整个 DevDocs）| 产物级（单个 markdown 文件）|
| 触发频率 | 低（年/季度级别）| 高（每次模板小调）|
| 影响面 | 全部 skill | 单个 skill |
| 迁移命令 | `/ms-pipeline realign --scope=layout` | `/ms-pipeline realign` |
| 不兼容时行为 | 强阻塞（block）| 软提醒（一次性提示）|

**两者不能混用**：layout 升级**不会**自动 bump spec_version，反之亦然。

## 三层版本号语义

### 1. `docs_layout_version` — 目录结构 + SSOT 治理

**治理范围**：
- DevDocs 顶层目录组织（requirements/ design/ tests/ ...）
- 单一事实源（SSOT）原则
- 文件命名规则（一编号一文件 vs 累积大表）
- 主文件与编号文件的职责切分

**升级触发**：
- 目录树结构变化（如 `04-dev-tasks.md` 拆为 `tasks/TASK-NNN.md`）
- SSOT 强约束规则变化（lint 规则新增/删除）
- 主文件职责变化（索引化 / 全量态切换）

**当前版本**：`layout.v2`（详见下方"当前版本基线"）

### 2. `id_scheme` — 编号体系治理

**治理范围**：
- 编号前缀清单（FEAT / STORY / AC / TASK / ISSUE / ADR / PATTERN / NOTE / UT / IT / E2E）
- 编号分配规则
- 编号过渡兼容（`aliases.yml`）
- 编号语义拆分规则

**升级触发**：
- 编号前缀新增 / 删除 / 改名（如 BUG → ISSUE）
- 编号语义拆分（如 INS → ADR + PATTERN + NOTE）
- aliases.yml schema 变化

**当前版本**：`id.v2`

### 3. `traceability_version` — 代码追溯治理

**治理范围**：
- `traceability.yml` schema（trace.v1）
- 代码-文档映射机制
- 漂移检测规则（symbol + path + commit 三元组）
- 多仓库聚合策略

**升级触发**：
- traceability.yml schema 字段变化
- 漂移检测算法变化
- 多仓库支持方式调整

**当前版本**：`trace.v1`

## 版本号依赖关系

```text
layout.v2 ─── 强依赖 ──→ id.v2 + trace.v1
       │
       ├── ❌ 不允许 layout.v2 + id.v1（编号体系不匹配）
       └── ❌ 不允许 layout.v2 + trace.v0（追溯机制缺失）

id.v2  ── 弱依赖 ──→ aliases.yml 存在（兼容老编号）
trace.v1 ── 独立演进（不强依赖 layout 或 id）
```

**强依赖**：组合不合法，skill 必须 surface 阻塞 + 推荐 `/ms-pipeline realign --scope=layout`。
**弱依赖**：组合可运行但功能受限，skill 应 surface 警告。

## 当前版本基线

### `layout.v2` 完整目标态

```yaml
# 1. 目录结构（强制）
directory_tree:
  docs/devdocs/
    ├── index.md                         # 全局编号索引（汇总各类型 index.md）
    ├── context.md                       # 项目稳定上下文（少变）
    ├── aliases.yml                      # 编号别名映射（单文件，详见 aliases-yml-schema.md）
    ├── traceability.yml                 # 代码-文档追溯映射（详见 layout-metadata-schema.md）
    ├── requirements/
    │   ├── index.md                     # F/US/AC 索引表
    │   ├── FEAT-001.md
    │   ├── STORY-001.md
    │   └── AC-001.md
    ├── design/
    │   ├── current.md                   # 全量当前态（系统设计快照）
    │   ├── decisions/
    │   │   └── ADR-001.md               # 增量决策记录
    │   └── index.md                     # ADR 索引
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
    │   ├── index.md                     # 任务索引（按 sprint 分组）
    │   └── TASK-001.md
    ├── issues/
    │   ├── index.md
    │   └── ISSUE-001.md
    ├── patterns/
    │   ├── index.md                     # PATTERN 索引（含引用度统计）
    │   └── PATTERN-001.md
    └── notes/                           # 一次性观察载体（取代部分 INS）
        ├── index.md
        └── NOTE-001.md

# 2. 强约束（违反触发 SSOT lint）
constraints:
  - 主文件（index.md / current.md）只允许表格索引（编号 + 状态 + 链接 + ≤120 字 summary）
  - 每个编号唯一 owner 文件（H1 唯一性）
  - 非 owner 文件出现编号时只能是 [[ID]] 引用或路径链接，禁止重述
  - 跨文件连续 80 字以上相似文本判重复
  - aliases.yml 必须存在（即使为空，含 frontmatter version）
  - traceability.yml 必须存在（即使为空，含 frontmatter version）
  - AGENTS.md 顶部必须含 devdocs frontmatter（见 layout-metadata-schema.md）

# 3. 禁止项
forbidden:
  - 代码内 @satisfies / @verifies 注释 — **禁止新增**；**legacy retained** 允许保留直到 layout.v3（追溯走 traceability.yml 为主线）
  - 累积型大文件（单文件 ≥ 3000 行触发 SSOT lint）
  - 同一编号在多文件作为 H1 owner
  - 编号 copy-paste 内容到非 owner 文件
  - "详见 / 权威源 / cross-link" 后未跟链接（必须可点击）
```

### `id.v2` 编号体系定稿

详细清单 + alias 兼容路径 + 编号分配规则见 [layout-metadata-schema.md](layout-metadata-schema.md) §编号清单。

简要：

| 编号 | 用途 | id.v1 兼容 |
|------|-----|-----------|
| `FEAT-NNN` | 功能点 | `F-NNN` |
| `STORY-NNN` | 用户故事 | `US-NNN` |
| `AC-NNN` | 验收标准 | （保留）|
| `TASK-NNN` | 开发任务 | `T-NNN` |
| `ISSUE-NNN` | 缺陷/问题 | `BUG-NNN` |
| `ADR-NNN` | 架构决策 | （保留）+ 接收 `INS-NNN` 决策类 |
| `PATTERN-NNN` | 经验沉淀 | 接收 `INS-NNN` 经验类 + 原 `patterns/*.md` 描述性命名 |
| `NOTE-NNN` | 一次性观察 | 接收 `INS-NNN` 一次性类 |
| `UT/IT/E2E-NNN` | 测试 | （保留）|

### `trace.v1` traceability.yml schema

详见 [layout-metadata-schema.md](layout-metadata-schema.md) §traceability schema。

简要：
- `version: trace.v1`
- `links: [{id, kind, repo, path, symbol, lines, commit, tests}]`
- 校验顺序：`symbol + path` 优先，`lines` 仅展示缓存，`commit` 用于过期检测

## 历史版本

### `layout.v1`（mic-en 起点）

- 累积大表（`04-dev-tasks.md` 单文件 700 行含 17 sprint 累积摘要）
- 编号体系混合（F / US / AC / T / INS / BUG 自造）
- 代码内 `@satisfies` / `@verifies` 追溯（mic-en 现有 636 处）
- 无 aliases.yml / 无 traceability.yml
- 被动归档（archive 是追加摘要而非生命周期管理）

### `id.v1`（mic-en 起点）

- 前缀清单：`F` / `US` / `AC` / `T` / `INS` / `BUG` / `ADR` / `UT` / `IT` / `E2E`
- `INS` 混合三种语义（决策 + 经验沉淀 + 一次性观察）
- `BUG` 自造编号（非社区主流）

### `trace.v0`（mic-en 起点）

- 无显式 traceability 机制
- 依赖代码内 `@satisfies` / `@verifies` 注释
- 公共项目场景下侵入代码（不可接受）

## 升级规则

### 触发升级的条件

| 当前版本 | 触发条件 | 目标版本 |
|---------|--------|---------|
| `layout.v1` | 目录树升级 + SSOT 引入 + 主文件索引化 | `layout.v2` |
| `id.v1` | 编号改名（BUG→ISSUE）+ INS 拆分 + aliases 引入 | `id.v2` |
| `trace.v0` | traceability.yml 引入 + 代码注释去除 | `trace.v1` |

### 升级执行路径

每次升级必须：
1. 更新本文件"当前版本基线"小节
2. 更新 [docs-layout-migration.md](docs-layout-migration.md) 增加 `v(N) → v(N+1)` 迁移矩阵
3. 更新所有 A/B 类 skill 的 `reads_layout` / `writes_layout` 字段
4. 提供 `/ms-pipeline realign --scope=layout` 执行迁移
5. 在 [skill-compatibility-matrix.md](skill-compatibility-matrix.md) 登记新版本对各 skill 的兼容性

### 不可跳跃升级

❌ 不允许跳过中间版本（如 `v1` 直接到 `v3`）。
✅ 必须逐步升级：`v1 → v2 → v3`。

理由：跳跃升级的 migration matrix 维护成本不可控。

## skill 兼容性声明

每个 A/B 类 skill 的 frontmatter 必须声明：

```yaml
reads_layout: [layout.v1, layout.v2]    # 读哪些 layout 版本（向下兼容）
writes_layout: layout.v2                # 写哪个 layout 版本（单一目标）
reads_id_scheme: [id.v1, id.v2]
writes_id_scheme: id.v2
reads_traceability: [trace.v0, trace.v1]
writes_traceability: trace.v1
on_incompatible: block                  # 遇到不兼容项目时的行为
migration: /ms-pipeline realign --scope=layout
```

### `on_incompatible` 行为枚举

| 值 | 行为 | 使用场景 |
|----|------|--------|
| `block` | surface 阻塞 + 强制要求 migration | **推荐默认值** |
| `warn` | surface 警告但继续运行 | 兼容期过渡 |
| `skip` | 静默跳过 | 仅特殊场景（不推荐）|

## 检测时机

| 时机 | 执行者 | 行为 |
|------|------|------|
| skill 首次调用 | 各 skill 自身 | 检查项目 layout 是否在 `reads_layout` 范围 |
| `/ms-pipeline init` | pipeline | 写入 AGENTS.md devdocs frontmatter（layout.v2 初始化）|
| `/ms-pipeline realign --scope=layout` | pipeline | 执行 layout 升级迁移 |
| `/ms-verify --layout-drift` | verify | 只读检测当前 layout 与 skill `writes_layout` 偏差 |
| `/ms-onboard --read` | onboard | 报告项目当前 layout 版本作为 onboarding 信息 |

## 未来版本规划（informational，不承诺时间表）

候选议题：

| 议题 | 触发版本 |
|------|--------|
| 多仓库聚合（主仓 + 子模块 traceability）| `layout.v3` / `trace.v2` |
| 编号子类型（如 `FEAT-001-frontend`）| `id.v3` |
| 自动从 commit 提取 traceability（git hook）| `trace.v2` |
| AGENTS.md 由 `/agent-memory` 自动同步 devdocs frontmatter | `layout.v3` |

## 引用关系

| 引用本文件的位置 | 引用目的 |
|---------|----|
| `skills/pipeline/SKILL.md` § realign | 仲裁层入口 |
| `skills/pipeline/references/realign.md` | spec_version 与 docs_layout_version 边界澄清 |
| 各 A/B 类 skill `references/realign.md` | 三层版本号语义参考 |
| `skills/verify/SKILL.md` § `--layout-drift` | 漂移检测依据 |
| `skills/onboard/SKILL.md` § `--read` | onboarding 报告 layout 版本 |

## 变更日志

| 日期 | 变更 | 触发 |
|------|------|------|
| 2026-05-15 | 初始版本 | DevDocs 治理体系升级（6 大支柱 #6）|
