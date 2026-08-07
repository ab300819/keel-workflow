# 架构与治理（维护者 / AI 参考）

> 本文是 DevDocs 治理体系、编号规则、文件结构的参考。**用户上手不需要读本文**——上手见 [README](../README.md)。

> DevDocs 不仅是流程模板，还自带一套**文档生命周期治理框架**，防止文档随项目演进而腐化（编号自造、单文件膨胀、追溯断裂、代码注释污染、命名形式主义等）。
>
> 治理框架完整 spec 位于 [`skills/pipeline/references/layout/`](../skills/pipeline/references/layout/) 目录。

### 根本问题：DevDocs 的三职责困境

治理框架的起点是识别出一个本质矛盾：**DevDocs 被迫同时承担三种性质截然不同的职责**，导致用 Markdown 单文件累积大表难以为继。

| 职责 | 性质 | 累积期的表现 |
|------|------|------------|
| **数据库**（编号 + 索引 + 引用关系）| 结构化数据 | 单文件累积 → 越来越难查找/更新 |
| **版本边界**（layout / id / trace 演进）| 治理规则 | 规则与产物混在一起 → skill 升级带不动文档体系 |
| **代码追溯**（AC ↔ 测试 ↔ 实现）| 跨载体映射 | 代码内 `@satisfies` 注释 → 公共项目场景下污染代码 |

**治理核心**：把这三件事**拆开**，分别用合适的工具治理：

```
数据库职责    → layout.v2 一文件一编号 + index.md 索引化 + SSOT lint
版本边界职责  → 三层版本号（docs_layout / id_scheme / traceability）+ realign 命令
代码追溯职责  → traceability.yml 外置追溯（代码保持干净）
```

### 实战痛点（治理框架的具体依据）

治理框架不是凭空设计，而是来自一个真实项目（`mic-en`，跨 17 sprint / 半年研发期 / 80+ 文档）暴露的具体问题：

| 问题域 | 实际状况 | 暴露的本质矛盾 | 治理回应 |
|--------|---------|-------------|---------|
| **单文件膨胀** | `04-dev-tasks.md` 累计到 700 行，含 17 sprint 累积摘要 | DevDocs 当作数据库用，但 Markdown 无法承载结构化查询 | #2 一文件一编号 + sprint 分组折叠 + index.md 索引化 |
| **编号自造** | `INS-XXX` 混合 3 种语义（决策 + 经验沉淀 + 一次性观察）；`BUG-XXX` 非社区主流 | 编号语义不收敛，难以工具化解析 | #1 BUG → ISSUE / INS 拆 ADR/PATTERN/NOTE |
| **代码污染** | 636 处 `@satisfies` / `@verifies` 注释嵌入代码 | DevDocs 元信息侵入代码（公共项目场景不可接受）| #4 trace.v1 外置追溯 + legacy 注释保留窗口 |
| **追溯断裂** | INS-018 / T-145 / BUG-045+046：DTO 新字段未传播到 controller-service-mapper 全链 | 缺少机器可检测的 AC ↔ 实现映射 | `/ms-verify --impl` 盲区 7（SPI DTO 透传完备性）+ #4 traceability.yml（提供机器可检测的映射）|
| **测试断言弱化** | V0.9.x P15 / T-157：IT 测试 setup 完整但断言只验状态码不验载荷 | 测试用例与 AC 失耦 | `/ms-verify --impl` 盲区 6（IT 断言完备性）|
| **版本占位** | **0 release tag + 未上线 production**，但文档累积 ~2,000 处 V<x.y.z> 引用，演化出 V0.9.x 占位、V1.0 候选冻结大重构、P 编号跨多 V 累计 | 无 git tag → 文档被迫承担版本边界 | `/ms-iteration-policy` 横切：研发阶段命名策略 |
| **追溯不可逆** | 文档大量出现 `V0.9.x P17` 字面占位 + Sprint 节奏与 V 节奏脱钩 | 命名约定回潮难防 | iteration-policy baseline + AGENTS.md 项目阶段约定段 |

每个问题对应一个或多个治理产物，6 大原则 + 6 阶段 spec + 横切 skill 的设计都是对这些实战痛点的系统化回应（**先有问题，后有方案**）。

### 6 大治理原则（用户驱动）

| # | 原则 | 落地 |
|---|------|------|
| 1 | **编号体系标准化** — 避免自造（BUG → ISSUE 等社区主流） | id.v2 双轨 |
| 2 | **主文件只记索引** — 按编号一文件一文件夹 | layout.v2 目录树 |
| 3 | **单一事实源（SSOT）** — 按归属放置，其他引用 | SSOT lint（12 规则）|
| 4 | **不污染代码注释** — DevDocs 元信息走 `traceability.yml`，代码保持干净（主仓 + 子仓策略）| trace.v1 外置追溯 |
| 5 | **每次迭代蒸馏** — 代码是唯一事实源，DevDocs 是辅助 | 13 类蒸馏动作 |
| 6 | **Skill 升级带文档体系升级** — 避免新 skill 跑在旧文档体系 | 三层版本号 + spec_version |

### 三层版本号体系

DevDocs 用三层独立版本号治理（解耦演进，强依赖联动）：

| 层 | 字段 | 治理对象 | 当前可选 |
|---|------|---------|---------|
| **目录结构** | `docs_layout_version` | 顶层目录树 + SSOT 强约束 | `layout.v1` / `layout.v2` |
| **编号体系** | `id_scheme` | 编号前缀清单 + alias 兼容 | `id.v1` / `id.v2` |
| **代码追溯** | `traceability_version` | trace.yml schema + 漂移检测 | `trace.v0` / `trace.v1` |

声明位置：项目 `AGENTS.md` 的 `devdocs:` frontmatter 段。

```yaml
---
devdocs:
  docs_layout_version: layout.v2
  id_scheme: id.v2
  traceability_version: trace.v1
  initialized_at: "2026-05-15"
---
```

**强依赖**：`layout.v2` 要求 `id.v2` + `trace.v1`；违反 → skill 阻塞 + 推荐 `/ms-pipeline realign --scope=layout` 升级。

#### 用哪个版本？

| 你的项目状态 | 推荐版本 | 原因 |
|------------|---------|------|
| 既有项目（已有 DevDocs 文档）| **保持 `layout.v1`** | 等 `realign` runtime 落地后再迁移；现在迁移需手动维护，成本高 |
| 全新项目，普通规模 | **使用 `layout.v1`** | runtime 完整可用；spec 已就绪但 v2 工具链待完善 |
| 全新实验项目 + 用户明确接受手动治理 | 可声明 `layout.v2` | 享受目录结构清晰 / SSOT 强约束，但 lint/distill 等自动工具暂不可依赖（命令处于 [FUTURE]），需手动按 spec 维护 |
| `mic-en` 等历史大项目 | **维持 `layout.v1` 不迁移** | 数千处 `@satisfies/@verifies` legacy 注释，等 `extract-trace` runtime + 用户主动调用 `realign` 才迁移 |

### 6 阶段治理 Spec

治理框架按 6 阶段组织（spec 已成文，runtime 仍按 [FUTURE] 状态逐步落地）：

| 阶段 | spec | 内容 |
|------|------|------|
| **#6 治理框架（仲裁层宪法）**| [layout-versioning-policy.md](../skills/pipeline/references/layout/layout-versioning-policy.md) | 三层版本号语义 + 升级规则 + 兼容性矩阵 |
| **#1 编号体系（id.v2 双轨）**| [id-scheme-implementation.md](../skills/pipeline/references/layout/id-scheme-implementation.md) | F→FEAT / T→TASK / BUG→ISSUE 等；INS 拆 ADR/PATTERN/NOTE |
| **#2 文件夹组织**| [folder-organization-implementation.md](../skills/pipeline/references/layout/folder-organization-implementation.md) | 目录树 + 一文件一编号 + sprint 分组 + modules 拆分 |
| **#3 SSOT lint**| [ssot-lint-implementation.md](../skills/pipeline/references/layout/ssot-lint-implementation.md) | 12 lint 规则 + baseline 防篡改 + CI 集成 |
| **#4 代码解耦**| [code-decoupling-implementation.md](../skills/pipeline/references/layout/code-decoupling-implementation.md) | trace.v1 写入 API + legacy 注释保留窗口 + 多仓聚合 |
| **#5 迭代蒸馏**| [distillation-implementation.md](../skills/pipeline/references/layout/distillation-implementation.md) | 13 类蒸馏动作 + 4 级安全门 + rollback + git hook 反循环 |

### 治理盲区主动审查（scope=health）

6 阶段 spec 治理"如何升级文档体系"，health scope 治理"已有文档体系是否健康"。两者正交：

| 维度 | 检查内容 | 实装 rule |
|------|----------|----------|
| a 结构正确性 | frontmatter + spec_version + 设计文档 ADR ↔ 正文同期修订 | schema-drift + `design/adr-only-revision` |
| b 索引/链接正确性 | 编号引用文件存在性 + 追溯矩阵完整性 | ms-sync trace + `health/dead-link` |
| c 过大文档识别 | devdocs-state.md byte 阈值 / 单行长度 / 内嵌禁用模式 | `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content` |
| d SSOT 遵从（layout.v2 only）| 占位/索引不复制权威源内容 | `ssot/no-restatement` [FUTURE] |

> 原维度 e「三层分离自动检测」已废弃。三层分离作为**原则**在 layout.v1 已由编号文件结构 + `state/*` / `design/adr-only-revision` 症状规则承载，审查时作人工尺子用，不再做独立的关键词扫描维度。权威见 [constraints.md §9 分层记忆原则](../skills/_shared/constraints.md#9-分层记忆原则决策--执行--数据三层分离)。

**关键设计**：
- health-lint rule（清单以 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md) Rule 集表为权威）与 layout.v2 的 ssot-lint 12 条 rule **独立**，layout.v1 项目（mic-en）可直接使用
- `devdocs-state.md` 模板硬化（forbidden 6 类内嵌模式 + 200/500/40K 三档阈值）+ `agent-memory --update` 健康度自检（双重保险）
- `design/adr-only-revision` 把 system-design 既有 ⛔ 硬约束（仅追加 ADR 不改正文）从人工自检升级为 git 历史自动扫描

详见 [realign-scope-health.md](../skills/pipeline/references/realign-scope-health.md) + [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md)。

### PRD 流程治理 Spec（轻量同类，已显性化）

PRD 流程（ms-prd / ms-prd-brainstorm / ms-prd-parser）承担**部分相同**的耦合（修订边界），但**不直接面对代码追溯**（通过 DevDocs 间接）。`docs/prd/` 是**单需求一次性脚手架**（扁平、只存当前需求，close 后清理）——多需求并行经实践证伪已移除。治理机制已齐备但散落，收纳显性化而非重建 6 阶段框架。

| spec | 内容 | 状态 |
|------|------|------|
| [prd-revision-policy.md](../skills/prd/references/governance/prd-revision-policy.md) | 3 类变更边界统一规则（单 FR / chunk / 模板）| [现状] |
| [prd-devdocs-mapping.md](../skills/prd/references/governance/prd-devdocs-mapping.md) | mapping 状态机（active/outdated/remapped/removed）+ 回扫责任分界 | [现状] |

> **与 DevDocs 6 阶段的差异**：PRD 治理大部分是收纳已有机制（chunk 指纹 / `--revise` / `--back-propagate-prd` / mapping_status），少量必要边界补齐，保持轻量定位。

### 治理工具命令

#### 统一升级入口（综合方案落地）

所有文档体系升级 + 健康度审查动作统一通过单一入口，不再以散落 flag 形式暴露：

```bash
/ms-pipeline realign [--scope=<spec|layout|prd-mapping|health>] [--target=<path>] [--dry-run|--apply]
```

| scope | 用途 | 状态 |
|-------|------|------|
| `spec`（默认）| 产物 `spec_version` drift（schema 维度）| ✅ 部分可用 |
| `layout` | layout.v1 → v2 迁移（含编号/目录/追溯重组）| ⚠️ **入口与接口规范已落地，迁移执行逻辑分阶段交付**（接口见 [realign-scope-layout.md](../skills/pipeline/references/realign-scope-layout.md)；落地状态权威见 [docs-layout-migration.md §执行接口落地状态](../skills/pipeline/references/layout/docs-layout-migration.md)）|
| `prd-mapping` | PRD mapping_status 扫描 + 报告 | [FUTURE] |
| `health` | 文档健康度主动审查（4 维度 / health-lint rule，清单见 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md) Rule 集表）| ✅ **执行接口已落地**（详见 [realign-scope-health.md](../skills/pipeline/references/realign-scope-health.md)）|

**Apply 6 Phase**：checkpoint → file_ops → id_map → trace → frontmatter → post-validation；每 Phase 单独 commit；失败 ⛔ + `git reset --hard <checkpoint_commit>` 回滚；plan_hash 校验中断恢复一致性。

**deprecated alias**：`--docs-layout` 等价于 `--scope=layout`，保留 1 版本后移除。

#### 验证工具

| 命令 | 用途 | 状态 |
|------|------|------|
| `/ms-verify --impl` | 实现验证（含盲区 6: IT 断言完备性 + 盲区 7: SPI DTO 透传完备性）| ✅ 可用 |
| `/ms-verify --docs` | 文档层间对齐验证 | ✅ 可用 |
| `/ms-verify --ui` | UI 与设计稿对齐 | ✅ 可用 |
| `/ms-verify --readiness` | 开发前就绪检查 | ✅ 可用 |
| `/ms-verify --schema-drift` | drift 三态报告（schema + layout 两段呈现）| ✅ 可用 |
| `/ms-verify --ssot-lint` | 跑 12 条 SSOT lint 规则（layout.v2 专属，v1 报 not_applicable）| [FUTURE] |
| `/ms-pipeline realign --scope=health` | 健康度主动审查（rule 清单见 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md)，layout.v1+v2 通用）| ✅ 可用 |

#### 已收敛 / internal-only（不再用户面暴露）

| 命令 | 处理 |
|------|------|
| `/ms-pipeline realign --docs-layout` | → `--scope=layout`（deprecated alias 1 版本）|
| `/ms-pipeline realign --classify-ins/--rename-id/--archive-v1` | → 由 `--scope=layout` Phase 自动处理 |
| `/ms-verify --layout-drift` | → 合并到 `--schema-drift`（报告含 layout drift 段）|
| `/ms-sync --extract-trace/--refresh-traceability` | → 由 `realign --scope=layout` Phase 4 编排，不暴露 |
| `/ms-sync --schema-drift` | → 迁移到 `/ms-verify --schema-drift`，统一 drift 报告 |
| `/ms-sync --check/--absorb` | → 合入 `/ms-sync` 默认流程 |
| `/ms-iteration-policy` | → internal-only，由 `/ms-pipeline realign --scope=layout` 编排调度 |

> ℹ️ `/ms-pipeline distill`（迭代蒸馏，13 类动作）是独立的治疗型治理命令，**不属于 realign 入口**；当前状态 [FUTURE]。

### 综合方案落地（单一入口 + flag 收敛）

针对"已膨胀 DevDocs 项目（如 mic-en）需要规范化升级 + skill 子命令膨胀给用户/作者带来认知成本"两个痛点，综合方案落地 5 步：

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | `/ms-pipeline realign --scope=layout` 执行接口（6 Phase + plan_hash + git reset 回滚）| ✅ |
| 2 | SKILL.md 移除 deprecated flag | ✅ |
| 3 | 各 skill SKILL.md 收敛 ≤5 外露 flag | ✅ |
| 4 | `shared-constraints.md § 8` 新增 single-entry 规则族 | ✅ |
| 5 | `ms-iteration-policy` 标 internal-only | ✅ |
| 6 | `--scope=health` 健康度主动审查（health-lint rule（清单见 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md)）+ devdocs-state 模板硬化 + ADR↔正文同期修订检测）| ✅ |

**用户面 flag 总收敛 49 → 20（-59%）**：

| Skill | 原 | 新 |
|-------|---:|---:|
| ms-pipeline | 19+ | 8 入口 |
| ms-verify | 14 | 5 |
| ms-sync | 8 | 3 |
| ms-requirements | 8 | 4 |
| ms-iteration-policy | 10 | 0（internal-only）|

### 共享约束 SSOT

[`skills/_shared/constraints.md`](../skills/_shared/constraints.md) 是跨 skill 协议层共性的单一权威源（274 行 / 99 rule_id），覆盖：

- § 1 门控标记 SSOT（⛔/⚠️/ℹ️ 语义 + 恢复方式格式）
- § 2 yaml-summary-v1 envelope（4 status 值域 + 保留字段）
- § 3 Task 委托规则（最小握手协议）
- § 4 FUTURE 状态三态（[现状]/[新增]/[FUTURE]）
- § 5 用户确认 / AskUserQuestion
- § 6 只读 / dry-run 命名
- § 7 Recovery 格式（4 字段模板）
- § 8 realign / spec_version + **single-entry 规则族**

各 ms- skill 顶部通过聚合声明引用，不复制规则，避免散落 drift。

### 治理设计的关键选择

1. **诚实声明**：参与 DevDocs 治理并声明 `writes_*` 字段的 A/B 类写入 skill（9 个）当前保持 `layout.v1` / `id.v1` / `trace.v0`（"声明 = 行为"对齐；独立工具 skill 和只读 skill 不在此列）。spec 起草完成 **≠** runtime 就绪 — 4 条件全满足（spec + template + runtime + 至少 1 个 v2 项目验证）才升 v2，避免"声明先行陷阱"。

2. **核心目录树 vs 执行层扩展**：layout.v2 强制目录树（requirements/design/tests/tasks/issues/patterns/notes）受 foundation 治理；衍生派生项（`_archived/` / `design/modules/` / `tests/index.md`）属执行层扩展，不污染 foundation。

3. **蒸馏 ≠ 归档**：蒸馏（distillation）= 知识压缩 + 结构优化（产物仍在主目录）；归档（archive）= 已完成项目搬移到 `_archived/`。两者明确分离。

4. **预防型 vs 治疗型**：`ms-iteration-policy` 是 **预防型**（源头治理 V<x.y.z> 形式主义），`ms-pipeline distill` 是 **治疗型**（已成型文档的压缩）。`init` 阶段先用 iteration-policy 立约 → 累积期用 distill 周期蒸馏。

5. **历史项目兼容**：`mic-en` 等 layout.v1 项目维持现状，**不主动迁移**。任何升级必须用户显式调用 `/ms-pipeline realign --scope=layout`。

6. **PRD 治理走轻量同类，不复制 6 阶段**：PRD 不直接追代码（通过 DevDocs 间接），且核心机制已存在；治理目标是显性化已有规则而非发明新体系。具体落地见上文「PRD 流程治理 Spec」。

---


## 编号体系

DevDocs 使用统一编号实现需求到代码的全链路追溯：

```
F-001 (功能点)
  └── US-001 (用户故事)
        └── AC-001 (验收标准)
              ├── UT-001 → @verifies AC-001（代码标注）
              ├── IT-001
              └── E2E-001
                    └── T-01 (开发任务) → @satisfies AC-001（代码标注）
```

| 前缀 | 含义 | 来源 |
|------|------|------|
| FR-XX / NFR-XX | PRD 阶段需求 | `/ms-prd` |
| F-XXX | 功能点 | `/ms-requirements` |
| US-XXX | 用户故事 | `/ms-requirements` |
| AC-XXX | 验收标准 | `/ms-requirements` |
| UT/IT/E2E/Journey | 测试用例 | `/ms-test-cases` |
| T-XX | 开发任务 | `/ms-dev-tasks` |
| INS-XXX | 洞察建议 | `/ms-insights` |
| BUG-XXX | Bug 记录 | `/ms-bugfix` |

> ℹ️ **`ms-backlog` 复用现有编号，不新增 B-XXX**。暂缓条目在 `docs/devdocs/backlog.md` 中用 `source_id + entry_no` 作局部锚点（如 `F-01#1`），状态机仅 `parked → reactivated|closed|superseded`。详见 [ms-backlog SKILL.md](../skills/backlog/SKILL.md)。

## 文件结构

```
docs/
├── prd/                          # PRD 流程产出
│   ├── requirements/index.md     # 需求总纲
│   ├── requirements/FR-XX-*.md   # 各功能需求
│   └── chunks/                   # PRD 原文分片
│
├── devdocs/                      # DevDocs 流程产出
│   ├── 00-context.md             # 项目上下文（/ms-onboard）
│   ├── 01-requirements.md        # 需求文档
│   ├── 02-system-design*.md      # 系统设计
│   ├── 03-test-*.md              # 测试用例
│   ├── 04-dev-tasks*.md          # 开发任务
│   ├── 05-test-report.md         # 测试报告
│   ├── 05-insights.md            # 洞察日志
│   ├── 05-bugfix-log.md          # Bug 修复日志
│   └── patterns/                 # 经验模式库（/ms-compound）
│
└── codebase-insight.md           # 代码盘点（/ms-codebase-insight）
```

### workspace_mode: shell 布局

代码与文档分仓时（外壳仓私有、代码仓可公开）：

```
<project>-dev/                    # 外壳仓
├── AGENTS.md                     # devdocs.workspace_mode: shell + code_roots
├── .gitmodules                   # 路径与 URL 唯一真源
├── docs/                         # 结构与上方完全一致，一字节未变
├── web/                          # 子模块 = code_root
└── api/                          # 子模块 = code_root
```

docs 内部结构不因模式而变，故本维度与 layout 版本正交。详见 [_shared/workspace-mode.md](../skills/_shared/workspace-mode.md)。
