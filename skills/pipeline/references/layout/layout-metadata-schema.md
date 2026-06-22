# Layout Metadata Schema

> 治理 DevDocs 元数据的 schema 定义。本文件是 [layout-versioning-policy.md](layout-versioning-policy.md) 三层版本号的具体落地形态规范。
>
> 包含 4 个 schema：AGENTS.md devdocs frontmatter / skill frontmatter / 编号清单 (id.v2) / traceability.yml (trace.v1)。
>
> ⚠️ **执行接口当前状态**：本文件提及的所有命令（`/ms-sync --extract-trace` / `/ms-sync --refresh-traceability` / `/ms-verify --layout-drift` 等）落地状态见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。

## 1. AGENTS.md devdocs frontmatter

项目根目录 `AGENTS.md` / `CLAUDE.md` 必须含 `devdocs` 段。

### Schema

```yaml
---
devdocs:
  docs_layout_version: layout.v2          # 必填，枚举 layout.v1 / layout.v2
  id_scheme: id.v2                        # 必填，枚举 id.v1 / id.v2
  traceability_version: trace.v1          # 必填，枚举 trace.v0 / trace.v1
  initialized_at: "2026-05-15"            # 必填，ISO 日期（首次初始化）
  upgraded_at: "2026-05-15"               # 可选，最近一次升级日期
  upgraded_from:                          # 可选，升级来源（首次初始化时空）
    docs_layout_version: layout.v1
    id_scheme: id.v1
    traceability_version: trace.v0
  legacy_annotation_grace_period: null    # 可选，layout.v2 期间 legacy @satisfies/@verifies 注释截止删除日期
                                          # null = 使用默认（layout.v2 升级日 + 6 个月）
                                          # ISO 日期（如 "2026-12-31"）= 显式覆盖默认
                                          # 用途：#4 code-decoupling-implementation.md § legacy 保留窗口
---
```

### 校验规则

- `docs_layout_version` ∈ [`layout.v1`, `layout.v2`]
- 版本号依赖：`layout.v2` 要求 `id.v2` + `trace.v1`（强依赖，违反触发 skill 阻塞）
- `initialized_at` 一旦写入不可修改
- `upgraded_at` 每次执行 `/ms-pipeline realign --scope=layout` 后自动更新
- frontmatter 段必须紧贴文件起始（无 leading 空行 / heading）

### 缺失时的行为

| 场景 | 行为 |
|------|------|
| AGENTS.md 不存在 | skill surface "无 DevDocs 治理标记，建议 `/ms-pipeline init`" |
| AGENTS.md 存在但无 devdocs 段 | skill 视为 `layout.v0`（隐式），按 `on_incompatible` 字段处理 |
| devdocs 段不完整（缺字段）| skill surface 警告 + 建议补全；不阻塞 |

## 2. Skill frontmatter（layout 兼容性声明）

每个 A/B 类 skill 的 `SKILL.md` frontmatter 必须含兼容性字段。

### Schema

```yaml
---
name: ms-<skill-name>
description: ...
allowed-tools: ...
metadata:
  patterns: [...]
  interaction: ...
  handoff: yaml-summary-v1
# === layout 治理字段（新增）===
reads_layout: [layout.v1, layout.v2]      # 必填，可读的 layout 版本列表
writes_layout: layout.v2                   # 必填，产出物使用的 layout 版本
reads_id_scheme: [id.v1, id.v2]
writes_id_scheme: id.v2
reads_traceability: [trace.v0, trace.v1]
writes_traceability: trace.v1
on_incompatible: block                     # 枚举 block / warn / skip
migration: /ms-pipeline realign --scope=layout
---
```

### 字段语义

| 字段 | 类型 | 必填 | 默认值 |
|------|------|----|-------|
| `reads_layout` | list[str] | ✅ | - |
| `writes_layout` | str | ✅ | - |
| `reads_id_scheme` | list[str] | ✅ | - |
| `writes_id_scheme` | str | ✅ | - |
| `reads_traceability` | list[str] | ✅ | - |
| `writes_traceability` | str | ✅ | - |
| `on_incompatible` | enum | ✅ | `block` |
| `migration` | str | ✅ | `/ms-pipeline realign --scope=layout` |

### 校验规则

- `writes_layout` 必须在 `reads_layout` 内（你写的版本你自己得能读）
- `writes_layout = layout.v2` 时强制 `writes_id_scheme = id.v2` + `writes_traceability = trace.v1`
- `on_incompatible` 选 `block` 时必须提供 `migration` 命令
- 不支持 layout 治理的 skill（如 `commit-convention` / `git-safety` 等独立工具 skill）不需要这些字段

### 运行时检查流程

```text
skill 调用 → 读项目 AGENTS.md devdocs frontmatter
  │
  ├─ 项目 layout ∈ skill.reads_layout
  │     → 正常运行
  │
  └─ 项目 layout ∉ skill.reads_layout
        ├─ on_incompatible: block → surface 阻塞 + 推荐 migration
        ├─ on_incompatible: warn  → surface 警告 + 继续运行
        └─ on_incompatible: skip  → 静默跳过
```

## 3. 编号清单（id.v2）

DevDocs 全部编号前缀的权威定义。

### 完整编号清单

| 编号 | 全称 | 用途 | id.v1 兼容 | 文件落点 |
|------|------|------|-----------|--------|
| `FEAT-NNN` | Feature | 功能点（产品视角）| `F-NNN` | `requirements/FEAT-NNN.md` |
| `STORY-NNN` | User Story | 用户故事 | `US-NNN` | `requirements/STORY-NNN.md` |
| `AC-NNN` | Acceptance Criteria | 验收标准 | `AC-NNN` | `requirements/AC-NNN.md` |
| `TASK-NNN` | Task | 开发任务 | `T-NNN` | `tasks/TASK-NNN.md` |
| `ISSUE-NNN` | Issue | 缺陷/问题（GitHub/GitLab 风格）| `BUG-NNN` | `issues/ISSUE-NNN.md` |
| `ADR-NNN` | Architecture Decision Record | 架构决策 | `ADR-NNN` + `INS-NNN`(决策类) | `design/decisions/ADR-NNN.md` |
| `PATTERN-NNN` | Pattern | 经验沉淀 | `INS-NNN`(经验类) + 旧 patterns 描述性命名 | `patterns/PATTERN-NNN.md` |
| `NOTE-NNN` | Note | 一次性观察 | `INS-NNN`(一次性类) | `notes/NOTE-NNN.md` |
| `UT-NNN` | Unit Test | 单元测试 | `UT-NNN` | `tests/UT/UT-NNN.md` |
| `IT-NNN` | Integration Test | 集成测试 | `IT-NNN` | `tests/IT/IT-NNN.md` |
| `E2E-NNN` | End-to-End Test | 端到端测试 | `E2E-NNN` | `tests/E2E/E2E-NNN.md` |

### 编号分配规则

- **格式**：`<前缀>-<数字>`，数字至少 3 位（如 `FEAT-001`、`PATTERN-042`）
- **唯一性**：同前缀内全局唯一，跨项目不复用
- **递增性**：累计递增，不重复使用已删除编号
- **PATTERN 初始分配**：按引用度排序（最高引用的占 PATTERN-001）
- **编号注册表**：每个类型的 `index.md` 是该类型编号的 source of truth（含 status + summary）

### 编号弃用 / 改名 / 拆分

- **弃用**：编号永久 reserved，不复用，在 `<type>/index.md` 标 `status: deprecated`
- **改名**（如 BUG → ISSUE）：写入 `aliases.yml`（详见 [aliases-yml-schema.md](aliases-yml-schema.md)）
- **拆分**（如 INS → ADR + PATTERN + NOTE）：写入 `aliases.yml` 多条 `split` 类型记录

### 编号 frontmatter（每个编号文件的 H1 必须配 frontmatter）

```yaml
---
id: FEAT-001
type: feature
status: draft | active | done | deprecated
summary: "一句话核心诉求（≤120 字符）"
owner_section: "## FEAT-001 — 详细需求"     # 本文件中作为 H1 owner 的章节标题
created_at: "2026-05-15"
updated_at: "2026-05-15"
links:
  parents: [STORY-001]                       # 上层关联
  children: [AC-001, AC-002]                 # 下层关联
  related: [PATTERN-005]                     # 平级关联
---
```

### 编号查找性能（informational）

`docs/devdocs/index.md` 维护全局编号查找索引：

```markdown
# DevDocs 全局编号索引

| ID | Type | Status | Summary | File |
|----|------|--------|---------|------|
| FEAT-001 | feature | active | 用户登录 | requirements/FEAT-001.md |
| ISSUE-042 | issue | done | 密码重置邮件未送达 | issues/ISSUE-042.md |
```

## 4. traceability.yml schema（trace.v1）

代码-文档追溯的外置载体。文件位置：`docs/devdocs/traceability.yml`（必须存在，即使空）。

### Schema

```yaml
---
version: trace.v1
project_layout: layout.v2
generated_at: "2026-05-15T10:00:00Z"
generator: "manual | ms-sync | ms-sync --extract-trace"
---

links:
  - id: AC-001                              # 必填，关联的编号
    kind: implements                         # 必填，枚举 implements / verifies / mentions
    repo: trade-fund-impl                    # 必填，多仓时区分（子模块名或独立 repo）
    path: src/main/java/.../FundService.java # 必填，文件路径（相对 repo 根）
    symbol: FundService#processSlip          # 必填，符号锚点（class#method 或 file:export）
    lines:                                   # 可选，行号范围（仅展示缓存，不参与校验）
      start: 45
      end: 78
    commit: 22cfb53f49                       # 必填，写入时的 commit（用于过期检测）
    tests:                                   # 可选，关联测试编号
      - UT-001
      - IT-005
    confidence: high                         # 可选，枚举 high / medium / low
    notes: "..."                             # 可选，人工备注

  - id: AC-001                              # kind: verifies 示例 —— evidence 仅出现在 verifies link
    kind: verifies
    repo: trade-fund-impl
    path: src/test/java/.../FundServiceTest.java
    symbol: FundServiceTest#rejectsEmptySlip
    commit: 22cfb53f49
    tests: [UT-001]                          # 覆盖关系：哪些用例覆盖该 AC
    evidence:                                # 可选，Evidence Ledger 投影（仅 kind: verifies）；由 ms-sync 在 S8 通过后回填（数据源 ms-verify S8 verdict），禁止手编
      - ac_type: 行为型                       # 行为型|视觉型|结构型 —— 引用 verification-flow S8 AC 类型 canonical（逐字），不复制
        s8_evidence_type: "UT 断言"          # 引用 verification-flow S8 证据矩阵 canonical 枚举（逐字），不复制
        locator: "UT-001"                    # 证据索引：测试编号 / artifact 路径 / CI run / 命令输出指针
        result: pass                         # trace.v1 本地枚举：pass | fail | n/a
        at_commit: 22cfb53f49                # 产出该证据时的 commit
  
  - id: FEAT-001
    kind: implements
    repo: mstatic
    path: src/pages/LoginPage.tsx
    symbol: LoginPage:default
    lines: { start: 1, end: 250 }
    commit: a565c8e
    tests: [E2E-001]
```

### `kind` 枚举语义

| kind | 含义 | 示例 |
|------|------|------|
| `implements` | 代码实现该需求/任务 | FEAT-001 由 `FundService#processSlip` 实现 |
| `verifies` | 测试验证该需求/任务 | AC-001 由 `UT-001` + `IT-005` 验证 |
| `mentions` | 弱引用（注释提及但非主实现）| TODO/FIXME 引用 ISSUE-XXX |

### 校验规则

#### 严格校验（必须通过）

1. `id` 必须存在于 `aliases.yml` 或对应 `<type>/index.md`
2. `repo` 必须是已注册的 repo（独立 repo 或 git submodule path）
3. `path` 必须真实存在于 `repo` 当前 commit
4. `commit` 必须是有效 git commit（短 hash ≥ 7 位）

#### 软校验（warn 不 block）

5. `symbol` 必须能在 `path` 中定位（grep `class\s+ClassName` / `function\s+funcName`）
6. `lines.end > lines.start`
7. `tests` 中的编号必须存在
8. `evidence` 仅允许出现在 `kind: verifies` 的 link（其他 kind 出现 → warn）；`evidence[].locator` 必须可解析（测试编号存在 / artifact 路径存在 / CI run 可定位）；`s8_evidence_type`（UT 断言/IT 断言/E2E 断言/--ui --live 截图等）与 `ac_type`（行为型/视觉型/结构型）取值须命中 verification-flow S8 矩阵枚举（Evidence Ledger 校验复用本软校验，不新增 health-lint rule）

### 过期检测

```text
traceability link 过期判定：
  current_commit_of_path != link.commit
       AND
  abs(git_log_count_between(link.commit, HEAD)) > THRESHOLD
       (默认 THRESHOLD = 30 commits)
  →  link 标 stale，建议重新校准 symbol 位置
```

**过期处理**：
- `ms-verify --layout-drift` 报告 stale links
- `/ms-sync --refresh-traceability` 重新提取 symbol 位置并更新 commit
- 不自动删除 link（除非 symbol 在 path 中完全消失）

### 多仓库聚合（layout.v2）

`layout.v2` 阶段：traceability.yml 单文件放主仓 `docs/devdocs/`，跨子模块 link 通过 `repo` 字段区分。

`layout.v3` 候选：子模块各自有 `<submodule>/.devdocs-trace.yml`，主仓聚合时 merge。

### 生成方式

| 生成方式 | 何时使用 |
|---------|--------|
| 人工编辑 | 少量 link 维护 |
| `/ms-sync --extract-trace` | 从代码 `@satisfies` / `@verifies` 注释（**layout.v1 legacy**）批量提取（迁移 trace.v0 → v1；legacy retained 注释允许保留到 layout.v3）|
| `/ms-sync --refresh-traceability` | 定期刷新过期 link 的 commit + lines |

## Schema 自身的演进

| Schema | 当前版本 | 演进触发 |
|--------|--------|--------|
| AGENTS.md devdocs frontmatter | 同 `docs_layout_version` | layout 升级 |
| Skill frontmatter | 同 `docs_layout_version` | layout 升级 |
| 编号清单 (id.v2) | `id.v2` | 编号体系升级 |
| traceability.yml (trace.v1) | `trace.v1` | 追溯机制升级 |

四个 schema 解耦演进，但 layout 升级时通常带动其他 schema 同步升级（见依赖关系，[layout-versioning-policy.md](layout-versioning-policy.md) §版本号依赖关系）。

## 引用关系

| 引用本文件的位置 | 引用目的 |
|---------|----|
| `skills/pipeline/SKILL.md` § init | 写入 AGENTS.md devdocs frontmatter |
| `skills/pipeline/references/realign.md` | 与 spec_version 边界 |
| 各 A/B 类 skill SKILL.md frontmatter | layout 兼容性声明 schema 参考 |
| `skills/verify/SKILL.md` § `--layout-drift` | traceability 校验依据 |
| `skills/sync/SKILL.md` § `--extract-trace` | trace.v0 → trace.v1 迁移依据 |

## 变更日志

| 日期 | 变更 | 触发 |
|------|------|------|
| 2026-05-15 | 初始版本 | DevDocs 治理体系升级（6 大支柱 #6）|
