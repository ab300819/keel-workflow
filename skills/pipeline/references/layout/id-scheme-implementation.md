# id.v2 编号体系实施规范（双轨）

> DevDocs 编号体系 v1 → v2 的实际落地规范。本文件定义 9 个 A/B skill 在 layout.v1 / layout.v2 双轨环境下的编号输出行为。
>
> 与 [layout-versioning-policy.md](layout-versioning-policy.md) 和 [layout-metadata-schema.md § 3 编号清单](layout-metadata-schema.md#3-编号清单idv2) 配套：前者定义版本治理框架，后者定义编号 schema，**本文件定义如何在 skill 中落地**。

## ⚠️ 执行接口当前状态

本文件描述的 layout 检测 + 双轨切换逻辑依赖 [FUTURE] 接口，详见 [docs-layout-migration.md § 执行接口落地状态](docs-layout-migration.md#-执行接口落地状态future)。当前 v1 行为是各 skill 的实际默认输出；v2 行为已在 SKILL.md 中**声明**，但实际切换 runtime 待 [FUTURE] 落地。

## 定位

| 治理对象 | 文件 |
|---------|------|
| 版本号语义 / 升级规则 | [layout-versioning-policy.md](layout-versioning-policy.md) |
| 编号清单 (id.v2 包含哪些前缀) | [layout-metadata-schema.md § 3](layout-metadata-schema.md#3-编号清单idv2) |
| 别名兼容机制 (aliases.yml) | [aliases-yml-schema.md](aliases-yml-schema.md) |
| **本文件**：skill 如何输出 v2 编号 | id-scheme-implementation.md |

## 双轨输出规则

### 核心原则

**单一 skill 必须能在 layout.v1 和 layout.v2 项目下都正确运行**。skill 通过检测 `AGENTS.md devdocs frontmatter` 的 `id_scheme` 字段决定输出形态：

```yaml
# AGENTS.md
devdocs:
  id_scheme: id.v1    # → skill 输出 F/US/AC/T/INS/BUG（v1 路径）
  id_scheme: id.v2    # → skill 输出 FEAT/STORY/AC/TASK/ADR-or-PATTERN-or-NOTE/ISSUE（v2 路径）
```

### 编号映射表

| v1 前缀 | v2 前缀 | 行为差异 |
|--------|--------|---------|
| `F-NNN` | `FEAT-NNN` | 仅前缀改名 |
| `US-NNN` | `STORY-NNN` | 仅前缀改名 |
| `AC-NNN` | `AC-NNN` | 不变 |
| `T-NNN` | `TASK-NNN` | 仅前缀改名 |
| `BUG-NNN` | `ISSUE-NNN` | 仅前缀改名 |
| `INS-NNN` | `ADR-NNN` / `PATTERN-NNN` / `NOTE-NNN` | **需人工归类 3 选 1** |
| `ADR-NNN` | `ADR-NNN` | 不变 |
| `UT/IT/E2E-NNN` | `UT/IT/E2E-NNN` | 不变 |

### Runtime 切换逻辑（[FUTURE] — 当前仅规范定义）

```text
skill 调用 →
  1. 读取 AGENTS.md devdocs.id_scheme
  2. 若 id.v1 → 走 v1 路径（默认）
       └─ 输出 F-NNN / US-NNN / T-NNN / BUG-NNN / INS-NNN
  3. 若 id.v2 → 走 v2 路径
       ├─ 输出 FEAT-NNN / STORY-NNN / TASK-NNN / ISSUE-NNN
       └─ 新增 INS 类候选时 AskUserQuestion 让用户选 ADR / PATTERN / NOTE
  4. 若 AGENTS.md 缺 devdocs frontmatter
       └─ 视为 id.v1（隐式默认）
```

## INS 拆 3 类人工归类机制

### 触发时机

- skill 在 layout.v2 项目下**新增** INS 候选时
- 用户通过 `/ms-pipeline realign --classify-ins INS-NNN` [FUTURE] 历史迁移时

### 归类引导（AskUserQuestion 强制）

```yaml
question: "请为 <候选条目> 选择编号类型："
options:
  - label: "ADR (决策记录)"
    description: "含技术选型、trade-off、架构权衡 → design/decisions/ADR-NNN.md"
  - label: "PATTERN (经验沉淀)"
    description: "可复用的模式、套路、最佳实践 → patterns/PATTERN-NNN.md"
  - label: "NOTE (一次性观察)"
    description: "现象记录、临时观察、不构成可复用知识 → notes/NOTE-NNN.md"
```

### 归类辅助建议（不强制）

skill 可基于内容关键词提示推荐分类，但**最终决策必须由用户**：

| 关键词 | 推荐 |
|--------|------|
| "决定" / "选择" / "trade-off" / "权衡" / "原因" | ADR |
| "模式" / "复用" / "套路" / "经验" / "best practice" | PATTERN |
| "观察" / "现象" / "一次性" / "临时" | NOTE |

## 各 skill 升级范围矩阵

### A 类 skill（DevDocs 主链路）

| Skill | v1 输出 | v2 输出 | 章节改造范围 |
|-------|--------|--------|------------|
| `ms-requirements` | F-NNN / US-NNN / AC-NNN | FEAT-NNN / STORY-NNN / AC-NNN | 编号规范 / 文档结构 / 模板 |
| `ms-system-design` | F-NNN / ADR-NNN | FEAT-NNN / ADR-NNN | 引用 F 改为 FEAT 双轨 |
| `ms-test-cases` | AC-NNN / UT-NNN / IT-NNN / E2E-NNN | AC-NNN / UT-NNN / IT-NNN / E2E-NNN | **无前缀改动**（id.v2 保留这些）；仅引用其他 v2 编号 |
| `ms-dev-tasks` | T-NNN（关联 F-NNN / US-NNN）| TASK-NNN（关联 FEAT-NNN / STORY-NNN）| 编号规范 / 任务模板 / 依赖关系 |
| `ms-dev-workflow` | T-NNN / @satisfies AC-NNN | TASK-NNN / @satisfies AC-NNN（注释 layout.v1 legacy）| 任务编号引用双轨 |

### B 类 skill（辅助产物）

| Skill | v1 输出 | v2 输出 | 章节改造范围 |
|-------|--------|--------|------------|
| `ms-prd-parser` | FR-NN / NFR-NN（PRD 层级，不变）| FR-NN / NFR-NN | **无编号改动**（PRD 层级与 DevDocs id 解耦）|
| `ms-prd-brainstorm` | FR-NN / NFR-NN | FR-NN / NFR-NN | 同上 |
| `ms-insights` | INS-NNN（混合）| 新增时 AskUserQuestion → ADR/PATTERN/NOTE | **核心改造**：拆 3 类归类机制 |
| `ms-onboard` | 引用 F / T / INS 等 | 引用 FEAT / TASK / ADR-PATTERN-NOTE | 上下文摘要的编号引用双轨 |

### 编排层 skill（不直接输出编号，仅调度）

| Skill | 改造点 |
|-------|--------|
| `ms-pipeline` | 阶段检测 / 文档检测使用编号时双轨匹配 |
| `ms-feature` | 接收 F-NN 或 FEAT-NN 都能正确路由 |
| `ms-bugfix` | 接收 BUG-NN 或 ISSUE-NN 都能正确路由 |

## SKILL.md 双轨表述模板

各 skill 在涉及编号的章节统一采用此模板：

```markdown
## 编号规范

- **layout.v1 项目**（默认）：使用 `F-NNN` / `US-NNN` / `T-NNN` 等 id.v1 前缀
- **layout.v2 项目** [FUTURE]：使用 `FEAT-NNN` / `STORY-NNN` / `TASK-NNN` 等 id.v2 前缀；INS 类候选必须 AskUserQuestion 归类为 ADR / PATTERN / NOTE
- 历史 v1 编号在 v2 项目通过 `aliases.yml` 自动解析（详见 [layout/aliases-yml-schema.md](path)）
```

## frontmatter 升级规则（条件性）

各 skill `writes_id_scheme` 字段保持 v1（当前 transitional state）。**升级到 id.v2 的触发条件（必须 1+2+3+4 全满足）**：

1. SKILL.md 正文已加入 v2 双轨说明 ✅（本阶段 #1 完成）
2. SKILL.md 模板（templates/）已加入 v2 编号样例 ✅（本阶段 #1 完成）
3. Runtime 检测层 [FUTURE] 已实现 ⏳
4. 至少 1 个 v2 项目已成功跑过该 skill ⏳

> ⛔ **禁止仅凭 1+2 升级**：满足 1+2 仅代表 spec 准备完成，runtime 行为仍是 v1。提前升级 `writes_id_scheme: id.v2` 会触发"声明先行陷阱"（frontmatter 声称 v2 但实际输出 v1）。必须 1+2+3+4 全满足才可改：
>
> ```yaml
> writes_id_scheme: id.v1   # 当前（1+2 完成，3+4 未达）
> writes_id_scheme: id.v2   # 仅当 1+2+3+4 全满足后升级
> ```
>
> 恢复方式：发现提前升级时，立即回退到 `id.v1` 并补齐 3/4 条件。

满足 3+4 时同步升级 `writes_layout: layout.v2`（按 codex 单一升级原则联动）。

## 模板文件双轨规则

各 skill 的 `templates/<name>.md` 内涉及编号样例时统一处理：

```markdown
> ℹ️ **编号双轨**：本模板下方示例使用 v1 前缀（如 F-001 / T-001）；layout.v2 项目应替换为 v2 前缀（FEAT-001 / TASK-001）。详见 [id-scheme-implementation.md](../../pipeline/references/layout/id-scheme-implementation.md)。

[原 v1 模板内容]
```

模板正文**不**做硬替换（保留 F-001 等 v1 样例可读），仅头部加双轨提示。

## 验证规则

`ms-verify --layout-drift` [FUTURE] 应检测：

1. AGENTS.md `id_scheme` vs skill `writes_id_scheme` 一致性
2. docs/ 中实际编号前缀 vs id_scheme 声明的一致性（v1 项目不应出现 FEAT-NNN 等 v2 前缀；v2 项目反之）
3. INS-NNN 出现在 v2 项目时报 warning（应已拆为 ADR/PATTERN/NOTE）

## 历史项目兼容（mic-en 等）

- **mic-en 等 layout.v1 项目**：维持 v1 行为，**不动**现有 F/US/AC/T/INS/BUG 编号
- 任何时候若用户主动调用 `/ms-pipeline realign --docs-layout` [FUTURE] 才触发迁移
- 本阶段（#1）**不执行** mic-en 迁移；仅完成 skill spec 改造

## 与 #2 文件夹组织的接口预留

`#2 文件夹组织` 阶段将基于本规范实施：
- v2 项目下编号文件按目录组织（requirements/FEAT-NNN.md 等）
- v2 项目下 INS 归类后直接写入对应目录（ADR-NNN.md → design/decisions/ 等）
- 本阶段 (#1) **不**强制目录结构，仅保证编号前缀双轨

## 引用关系

| 引用本文件的位置 | 引用目的 |
|------------|---------|
| 9 个 A/B skill SKILL.md § 编号规范 | 双轨表述参考 |
| `skills/insights/SKILL.md` § INS 拆分 | 人工归类机制 |
| `layout-versioning-policy.md` § id.v2 | 编号体系实施细节 |
| `docs-layout-migration.md` | mic-en 迁移路径 |

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-18 | 初始版本（id.v2 双轨实施规范）|
