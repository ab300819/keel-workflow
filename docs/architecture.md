# 架构与治理（维护者 / AI 参考）

> 本文是 keel 治理体系、编号规则、文件结构的参考。**用户上手不需要读本文**——上手见 [README](../README.md)。

> keel 不仅是流程模板，还自带一套**文档生命周期治理框架**，防止文档随项目演进而腐化（编号自造、单文件膨胀、追溯断裂、代码注释污染、命名形式主义等）。
>
> 治理判决与达成路径见 [2026-08-31 达成方案](superpowers/specs/2026-08-31-layout-v2-goal-attainment-design.md)。

### 根本问题：keel 的三职责困境

治理框架的起点是识别出一个本质矛盾：**keel 被迫同时承担三种性质截然不同的职责**，导致用 Markdown 单文件累积大表难以为继。

| 职责 | 性质 | 累积期的表现 |
|------|------|------------|
| **数据库**（编号 + 索引 + 引用关系）| 结构化数据 | 单文件累积 → 越来越难查找/更新 |
| **版本边界**（layout / id / trace 演进）| 治理规则 | 规则与产物混在一起 → skill 升级带不动文档体系 |
| **代码追溯**（AC ↔ 测试 ↔ 实现）| 跨载体映射 | 代码内编号引用 → 对没有 keel 上下文的维护者是纯噪音 |

**治理核心**：把这三件事**拆开**，分别用合适的工具治理：

```
文档膨胀职责  → /sync --archive 分档阈值 + 归档减量（不是拆分摊薄）
版本边界职责  → spec_version + /pipeline realign（单层，不是三层）
代码追溯职责  → 反向依赖：文档记 commit，代码零 keel 编号
```

### 实战痛点（治理框架的具体依据）

治理框架不是凭空设计，而是来自一个真实项目（`mic-en`，跨 17 sprint / 半年研发期 / 80+ 文档）暴露的具体问题：

| 问题域 | 实际状况 | 暴露的本质矛盾 | 治理回应 |
|--------|---------|-------------|---------|
| **单文件膨胀** | `04-dev-tasks.md` 累计到 700 行，含 17 sprint 累积摘要 | keel 当作数据库用，但 Markdown 无法承载结构化查询 | #2 一文件一编号 + sprint 分组折叠 + index.md 索引化 |
| **编号自造** | `INS-XXX` 混合 3 种语义（决策 + 经验沉淀 + 一次性观察）；`BUG-XXX` 非社区主流 | 编号语义不收敛，难以工具化解析 | #1 BUG → ISSUE / INS 拆 ADR/PATTERN/NOTE |
| **代码污染** | `@satisfies` / `@verifies` 注释嵌入代码（636 处，**2026-05 对 mic-en 的统计，未复核**）| keel 元信息侵入代码；keel 丢失后它就是指向虚空的指针 | **反向依赖**：代码零编号，文档记 `<repository>@<sha>`（存量留着不清理，只约束新增）|
| **追溯断裂** | INS-018 / T-145 / BUG-045+046：DTO 新字段未传播到 controller-service-mapper 全链 | 缺少机器可检测的 AC ↔ 实现映射 | `/verify --impl` 盲区 7（SPI DTO 透传完备性）+ #4 traceability.yml（提供机器可检测的映射）|
| **测试断言弱化** | V0.9.x P15 / T-157：IT 测试 setup 完整但断言只验状态码不验载荷 | 测试用例与 AC 失耦 | `/verify --impl` 盲区 6（IT 断言完备性）|
| **版本占位** | **0 release tag + 未上线 production**，但文档累积 ~2,000 处 V<x.y.z> 引用，演化出 V0.9.x 占位、V1.0 候选冻结大重构、P 编号跨多 V 累计 | 无 git tag → 文档被迫承担版本边界 | `00-baseline.md` §2.1 源头治理：未发布项目不套 semver |
| **追溯不可逆** | 文档大量出现 `V0.9.x P17` 字面占位 + Sprint 节奏与 V 节奏脱钩 | 命名约定回潮难防 | `00-baseline.md` §2.1「发布状态与命名约定」建基线时**问一次**（源头治理）|

每个问题对应一个或多个治理产物，6 大原则 + 6 阶段 spec + 横切 skill 的设计都是对这些实战痛点的系统化回应（**先有问题，后有方案**）。

### 6 大治理原则 —— 达成盘点（2026-08-31 复盘）

原方案 layout.v2 **自身达成率 0%**（12 个命令一个没实现、从未在任何项目跑过），
但目标已达成一半，**全部由别的更便宜的现役手段达成**。判决与路径见
[2026-08-31 达成方案](superpowers/specs/2026-08-31-layout-v2-goal-attainment-design.md)。

| # | 原则 | 原打算怎么做 | 达成了吗 | 实际靠什么 |
|---|------|------------|---------|-----------|
| 1 | **编号体系标准化** | id.v2 双轨 + aliases.yml | ⚠️ 部分 | INS 混三语义改由 `insights` **四路分流**（决策→ADR / 经验→patterns / 需求→01 / 一次性→丢）；⛔ 不做 BUG→ISSUE 改名（零外部消费者）|
| 2 | **主文件只记索引** | 一文件一编号目录树 | ✅ **达成，手段不同** | `/sync --archive` 四文件分档阈值 + **归档减量** |
| 3 | **单一事实源（SSOT）** | 12 条 ssot lint | ⚠️ 部分 | health-lint 的 `health/dead-link` + `design/adr-only-revision` 覆盖两类主症状；其余 10 条在单文件形态下**没有检测对象** |
| 4 | **不污染代码注释** | traceability.yml 外置 | ✅ **达成，手段不同** | **反向依赖**：代码与 commit 零 keel 编号，文档记 `<repository>@<sha>` |
| 5 | **每次迭代蒸馏** | 13 类蒸馏动作 | ⚠️ 部分 | 归档 + `state/total-size-cap` 承担减量。⚠️ 原 13 类动作**一条真删除都没有**，`sprint-fold` 甚至让总量变大 |
| 6 | **Skill 升级带文档体系升级** | 三层版本号 | ✅ **达成，手段不同** | `spec_version` + `realign --scope=spec` |

⛔ **不重新设计目录树。** `constraints.md` §9 已承认编号文件结构为决策/执行/数据三层
各自安排了位置；膨胀由 `--archive` 解决。不建 v3。

### 版本治理：只有一层

原三层版本号（`docs_layout_version` / `id_scheme` / `traceability_version`）
已随 layout.v2 一并删除——它们治理的三个对象都没变过，而字段本身在 10 个现役 skill
的 frontmatter 里占了 80 行。

现役只剩 `spec_version`（产物模板格式），声明位置在各产物 frontmatter，
升级入口 `/pipeline realign --scope=spec`。

### 治理盲区主动审查（scope=health）

health scope 治理「已有文档体系是否健康」，与 `spec` scope（产物模板格式升级）正交：

| 维度 | 检查内容 | 实装 rule |
|------|----------|----------|
| a 结构正确性 | frontmatter + spec_version + 设计文档 ADR ↔ 正文同期修订 | schema-drift + `design/adr-only-revision` |
| b 索引/链接正确性 | 编号引用文件存在性 + 追溯矩阵完整性 | sync trace + `health/dead-link` |
| c 过大文档识别 | devdocs-state.md byte 阈值 / 单行长度 / 内嵌禁用模式 / 编号缓存陈旧 | `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content` + `state/max-id-stale` |

> 原维度 d「SSOT 遵从」与维度 e「三层分离自动检测」均已废弃：d 依赖已删除的 layout.v2 ssot-lint，无检测对象。三层分离作为**原则**已由编号文件结构 + `state/*` / `design/adr-only-revision` 症状规则承载，审查时作人工尺子用，不再做独立的关键词扫描维度。权威见 [constraints.md §9 分层记忆原则](../skills/shared/constraints.md#9-分层记忆原则决策--执行--数据三层分离)。

**关键设计**：
- health-lint rule 清单以 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md) Rule 集表为权威，12 条中 10 条可执行，2 条 not_implemented（`design/adr-only-revision` · `submodule/pointer-drift`）
- `devdocs-state.md` 模板硬化（forbidden 6 类内嵌模式 + 200/500/40K 三档阈值）+ `agent-memory --update` 健康度自检（双重保险）
- `design/adr-only-revision` 把 system-design 既有 ⛔ 硬约束（仅追加 ADR 不改正文）从人工自检升级为 git 历史自动扫描

详见 [realign-scope-health.md](../skills/pipeline/references/realign-scope-health.md) + [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md)。

### PRD 流程治理 Spec（轻量同类，已显性化）

PRD 流程（prd / prd-brainstorm / prd-parser）承担**部分相同**的耦合（修订边界），但**不直接面对代码追溯**（通过 keel 间接）。`docs/prd/` 是**单需求一次性脚手架**（扁平、只存当前需求，close 后清理）——多需求并行经实践证伪已移除。治理机制已齐备但散落，收纳显性化而非重建 6 阶段框架。

| spec | 内容 | 状态 |
|------|------|------|
| [prd-revision-policy.md](../skills/prd/references/governance/prd-revision-policy.md) | 3 类变更边界统一规则（单 FR / chunk / 模板）| [现状] |
| [prd-devdocs-mapping.md](../skills/prd/references/governance/prd-devdocs-mapping.md) | mapping 状态机（active/outdated/remapped/removed）+ 回扫责任分界 | [现状] |

> **与 keel 6 阶段的差异**：PRD 治理大部分是收纳已有机制（chunk 指纹 / `--revise` / `--back-propagate-prd` / mapping_status），少量必要边界补齐，保持轻量定位。

### 治理工具命令

#### 统一升级入口（综合方案落地）

所有文档体系升级 + 健康度审查动作统一通过单一入口，不再以散落 flag 形式暴露：

```bash
/pipeline realign [--scope=<spec|layout|prd-mapping|health>] [--target=<path>] [--dry-run|--apply]
```

| scope | 用途 | 状态 |
|-------|------|------|
| `spec`（默认）| 产物 `spec_version` drift（schema 维度）| ✅ 部分可用 |
| `prd-mapping` | PRD mapping_status 扫描 + 报告 | [FUTURE] |
| `health` | 文档健康度主动审查（4 维度 / health-lint rule，清单见 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md) Rule 集表）| ✅ **执行接口已落地**（详见 [realign-scope-health.md](../skills/pipeline/references/realign-scope-health.md)）|

**Apply 6 Phase**：checkpoint → file_ops → id_map → trace → frontmatter → post-validation；每 Phase 单独 commit；失败 ⛔ + `git reset --hard <checkpoint_commit>` 回滚；plan_hash 校验中断恢复一致性。

#### 验证工具

| 命令 | 用途 | 状态 |
|------|------|------|
| `/verify --impl` | 实现验证（含盲区 6: IT 断言完备性 + 盲区 7: SPI DTO 透传完备性）| ✅ 可用 |
| `/verify --docs` | 文档层间对齐验证 | ✅ 可用 |
| `/verify --ui` | UI 与设计稿对齐 | ✅ 可用 |
| `/verify --readiness` | 开发前就绪检查 | ✅ 可用 |
| `/verify --schema-drift` | drift 三态报告（schema + layout 两段呈现）| ✅ 可用 |
| `/pipeline realign --scope=health` | 健康度主动审查（rule 清单见 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md)，layout.v1+v2 通用）| ✅ 可用 |

#### 已收敛 / internal-only（不再用户面暴露）

| 命令 | 处理 |
|------|------|
| `/sync --schema-drift` | → 迁移到 `/verify --schema-drift`，统一 drift 报告 |
| `/sync --check/--absorb` | → 合入 `/sync` 默认流程 |

### 综合方案落地（单一入口 + flag 收敛）

针对"已膨胀 keel 项目（如 mic-en）需要规范化升级 + skill 子命令膨胀给用户/作者带来认知成本"两个痛点，综合方案落地 5 步：

| 步骤 | 内容 | 状态 |
|------|------|------|
| 2 | SKILL.md 移除 deprecated flag | ✅ |
| 3 | 各 skill SKILL.md 收敛 ≤5 外露 flag | ✅ |
| 4 | `shared-constraints.md § 8` 新增 single-entry 规则族 | ✅ |
| 6 | `--scope=health` 健康度主动审查（health-lint rule（清单见 [health-lint-implementation.md](../skills/pipeline/references/health-lint-implementation.md)）+ devdocs-state 模板硬化 + ADR↔正文同期修订检测）| ✅ |

**用户面 flag 总收敛 49 → 20（-59%）**：

| Skill | 原 | 新 |
|-------|---:|---:|
| pipeline | 19+ | 8 入口 |
| verify | 14 | 5 |
| sync | 8 | 3 |
| requirements | 8 | 4 |

### 共享约束 SSOT

[`skills/shared/constraints.md`](../skills/shared/constraints.md) 是跨 skill 协议层共性的单一权威源（274 行 / 99 rule_id），覆盖：

- § 1 门控标记 SSOT（⛔/⚠️/ℹ️ 语义 + 恢复方式格式）
- § 2 yaml-summary-v1 envelope（4 status 值域 + 保留字段）
- § 3 Task 委托规则（最小握手协议）
- § 4 FUTURE 状态三态（[现状]/[新增]/[FUTURE]）
- § 5 用户确认 / AskUserQuestion
- § 6 只读 / dry-run 命名
- § 7 Recovery 格式（4 字段模板）
- § 8 realign / spec_version + **single-entry 规则族**

各 keel 流程 skill 顶部通过聚合声明引用，不复制规则，避免散落 drift。

### 治理设计的关键选择

1. **诚实声明**：skill 的版本声明必须等于其实际行为（"声明 = 行为"对齐；独立工具 skill 和只读 skill 不在此列）。spec 起草完成 **≠** runtime 就绪 — 4 条件全满足（spec + template + runtime + 至少 1 个 v2 项目验证）才升 v2，避免"声明先行陷阱"。

2. **减量而非摊薄**：文档膨胀的解药是**归档**（`/sync --archive` 分档阈值），不是**拆分**。一文件一编号只是把 700 行摊成 200 个文件，总量不减反增，还多出 index 重建、交叉引用校验、别名合并三种纯自造的维护开销。

3. **归档是唯一的减量手段**：`/sync --archive` 把已失效部分移出主文档，正文只留现状。原 layout.v2 的 13 类「蒸馏」动作里**一条真删除都没有**——`sprint-fold` 甚至保留 owner 文件的同时再往 index 写一份摘要，总量反而变大。

4. **预防型优于治疗型**：命名污染在**建基线时问一次**（`00-baseline.md` §2.1）远比事后扫描迁移便宜。原 `ms-iteration-policy`（已删除）自己就写着该走源头，却把自己实现成 7 个事后命令。

5. **存量不清理**：既有项目的代码标注**留着不动**——它们已经在那里了，删除是纯风险且无收益。新规则只约束新增。
   > ⚠️ 上表的 636 是 **2026-05 对 mic-en 的一次统计**，本仓从未复核，今天的实际数量未知。此处及上表引用它只为说明**量级**，⛔ 不作为任何判据的输入。

6. **PRD 治理走轻量同类，不复制 6 阶段**：PRD 不直接追代码（通过 keel 间接），且核心机制已存在；治理目标是显性化已有规则而非发明新体系。具体落地见上文「PRD 流程治理 Spec」。

---

## 编号体系

keel 使用统一编号实现需求到代码的全链路追溯：

```
F-001 (功能点)
  └── US-001 (用户故事)
        └── AC-001 (验收标准)
              ├── UT-001 → 追溯矩阵 AC↔测试编号映射
              ├── IT-001
              └── E2E-001
                    └── T-01 (开发任务) → 追溯矩阵「变更来源」`api@a3f9c21`
```

| 前缀 | 含义 | 来源 |
|------|------|------|
| FR-XX / NFR-XX | PRD 阶段需求 | `/prd` |
| F-XXX | 功能点 | `/requirements` |
| US-XXX | 用户故事 | `/requirements` |
| AC-XXX | 验收标准 | `/requirements` |
| UT/IT/E2E/Journey | 测试用例 | `/test-cases` |
| T-XX | 开发任务 | `/dev-tasks` |
| INS-XXX | 洞察建议 | `/insights` |
| BUG-XXX | Bug 记录 | `/bugfix` |
| M-XXX | 里程碑（可选） | `/requirements` |

> ℹ️ **`M-XXX` 是逻辑组织概念，⛔ 不进上方追溯链示意**。它只把多个 F 分成可交付的段，用于「做完一段停下来让人实际用一遍」；不进追溯矩阵、不进覆盖率、不是执行单元。可选——按需求规模决定用不用。登记与消费边界见 [shared/constraints.md](../skills/shared/constraints.md) `M` 标识登记。

> ℹ️ **`backlog` 复用现有编号，不新增 B-XXX**。暂缓条目在 `docs/devdocs/backlog.md` 中用 `source_id + entry_no` 作局部锚点（如 `F-01#1`），状态机仅 `parked → reactivated|closed|superseded`。`M-XXX` 是唯一允许承接「尚无编号」新想法的 source_id。详见 [backlog SKILL.md](../skills/backlog/SKILL.md)。

## 文件结构

```
docs/
├── prd/                          # PRD 流程产出
│   ├── requirements/index.md     # 需求总纲
│   ├── requirements/FR-XX-*.md   # 各功能需求
│   └── chunks/                   # PRD 原文分片
│
├── devdocs/                      # keel 流程产出
│   ├── 00-context.md             # 项目上下文（/onboard）
│   ├── 00-baseline.md            # 项目基线（接手记录，retrofit 产出）
│   ├── 01-requirements.md        # 需求文档
│   ├── 02-system-design*.md      # 系统设计
│   ├── 03-test-*.md              # 测试用例
│   ├── 04-dev-tasks*.md          # 开发任务
│   ├── 05-test-report.md         # 测试报告
│   ├── 05-insights.md            # 洞察日志
│   ├── 05-bugfix-log.md          # Bug 修复日志
│   └── patterns/                 # 经验模式库（/compound）
│
└── codebase-insight.md           # 代码盘点（/codebase-insight）
```

### shell 拓扑布局

代码与文档分仓时（外壳仓私有、代码仓可公开）：

```
<project>-dev/                    # 外壳仓
├── AGENTS.md                     # workspace: {mode: shell, code_roots: [...]}
├── .gitmodules                   # 路径与 URL 唯一真源
├── docs/                         # 结构与上方完全一致，一字节未变
├── web/                          # 子模块 = code_root
└── api/                          # 子模块 = code_root
```

docs 内部结构不因模式而变，文档根三种模式下恒为 `<仓库根>/docs/`，故本维度与 layout 版本正交，也不属 layout 元数据。它是**仓库级事实**，由独立 skill [/workspace-topology](../skills/workspace-topology/SKILL.md) 拥有。

## 决策记录索引

> 逐字迁自 `AGENTS.md` 的「当前状态」节（2026-09-07）。该节曾占 AGENTS.md 体积的 87%，把变更历史写成了当前状态——正是 [doc-organization](../skills/doc-organization/SKILL.md) 原则一禁止的形状。
>
> 按时间倒序，最新在前。**理由与推导的权威在各条所链的 spec / plan / audit**，本节不是它们的替代。

- **retrofit 逆向推导 → 建立项目基线**：逆向出的 US/AC 是把端点和测试名换个说法重说一遍，且构成**循环论证**（测试断言→AC→同一测试证明覆盖），产出必然 100% 的假追溯率，还会把已有 Bug 的现状行为固化成验收标准。整条推导链（F/US/AC + UT/IT/E2E）**删除**，改为建立 `docs/devdocs/00-baseline.md`。判据是**认知权威四分法**——LLM 极擅长读出「代码实际做了什么」，也极易把它误当成「本该做什么 / 外部要求什么 / 根本不知道什么」；基线只承载后三者，凡重扫代码能重建的一律不装。六节：建立记录（含 `adoption_commit`）/ 项目目的与边界 / 代码外部的硬约束 / 仍在约束未来改动的护栏 / 已知未知+证据冲突 / 权威来源地图。四条纪律：调查先于提问、每条标来源（`用户确认`/`已有文档`/`推导待确认`/`未知`，沉默不升格）、文档不是权威代码是（可验证陈述必须拿代码校验，冲突以代码为准）、每次提问必有「我也不清楚」出口。存量代码不编号，`01` 由首次 `/feature` 创建。同批修 6 处下游断点，其中 `feature` 前置要求 `01` 存在会与「基线已建」形成**死循环**；另修两个既存缺陷（retrofit `allowed-tools` 缺 `Task` 导致其委托指令跑不了、onboard `1.1` 写死从 `01` 提取）。经 codex 两轮独立评审（禁读设计稿），第二轮推翻本方案「已证伪的路必装」的原结论——该结论依据 AGENTS.md 实测词频，但内容多也可能只是没人删（本文件 82 行/20KB 超 60 行硬限）；裁定改为「只装仍在约束未来改动的证伪结论，且须写成护栏形式」。方案见 [specs/2026-08-25-retrofit-baseline-design.md](docs/superpowers/specs/2026-08-25-retrofit-baseline-design.md)
- **PRD 扁平化（移除多需求并行）**：mic-en 实践证伪「多需求并行」，已**删除**整套 multi-PRD 机器（全局 `index.md` + 跨 PRD 编号注册表 / `<prd_id>` 子目录 / supersedes / `_archived` / 顶层 `synthesis/` / 跨 PRD 引用+冲突检测 / `list`·`status`·`archive`·`migrate` / `prd-index-ssot.md` + `global-index-template.md`）。`docs/prd/` 改为**扁平·单需求一次性脚手架**，FR/NFR 当前需求内续编、新需求从 FR-01 重起（受 prd 新建门禁保护）；需求 close（上线）后由 `/prd clear`（`/pipeline close` 末步委托）清理。删除而非封存 FUTURE（已证伪，逻辑同废弃 health 维度 e）。方案见 [specs/2026-06-23-prd-flatten-remove-multi-requirement-parallel-design.md](docs/superpowers/specs/2026-06-23-prd-flatten-remove-multi-requirement-parallel-design.md)
- **工作区拓扑抽为独立 skill**：`shell` 拓扑下文档在外壳仓 `docs/`，代码作 git 子模块挂在同级（服务「维护开源项目」「自有项目待公开」两类零污染场景）。**文档根三种拓扑下恒为 `<仓库根>/docs/`**，是固定不变量不设字段；变的只有代码在哪。原 `workspace_mode` 维度绑死在 keel 触发链上（探测入口只有 init / retrofit / realign 三个，全属 keel），而消费方里有三个自称「与 keel 独立」的——外壳形状但不跑 keel 的项目无路声明，想声明就得拉起整套 keel。现抽为独立 skill [/workspace-topology](skills/workspace-topology/SKILL.md)：三入口 `inspect`（返回拓扑上下文；已有声明时只读）/ `reconcile`（交互式维护声明，幂等可重入）/ `migrate`（单仓→外壳布局，手动/自动双模式）。声明迁到 `AGENTS.md` 的**独立 `workspace:` 块**（旧 `devdocs.workspace_mode` 只读兼容，`reconcile` 时迁移），由该 skill 拥有、`agent-memory` 原样保留不动。**消费方不自己调它**——编排层开头调一次 `inspect`，结果经握手 `workspace_context` 下传（[constraints.md §3](skills/shared/constraints.md) `task/workspace-context`），因为多数原子 skill 的 `allowed-tools` 没有 `Task`。原 inline→shell 迁移七步删除重写：旧版前置门「工作区干净 + 无未推送提交」会把唯一真实场景（clone 开源项目并已开发过）挡在门外，Step 4 用远端 URL `submodule add` 又会重新 clone 丢掉本地未推送工作；新流程先 `mv` 进外壳仓再传远程 URL 登记（实测不 clone、未推送提交/staged/untracked 全保留），顺序为「建壳→mv→登记→复制→校验→才删原件→写声明→推送收尾」，⛔ 不做历史改写。**无 `workspace:` 块**当时按 `inline` 缺省，存量项目零影响（该缺省已被下一条推翻，现为「没声明就问」）。方案见 [specs/2026-08-21-workspace-topology-skill-design.md](docs/superpowers/specs/2026-08-21-workspace-topology-skill-design.md)（经 codex 对原始方案独立评估；前六轮审查的加戏已剥离），配对的 [shell 单仓假设审计](docs/superpowers/specs/2026-08-21-shell-single-repo-assumptions-audit-design.md) 已裁定**只修静默失败的两条**（audit 档外审的工作区 diff、headless 洁净门），全量矩阵盘点（7 类操作 × 39 skill ≈ 270 格）不做——其余 23 个已知条目今天不影响使用，等真踩到再说
- **拓扑探测重写 + 第三种拓扑 `linked`**：原「无声明 → 判 inline」是**兜底默认**，必然在「有事实但没声明」时给错答案；真因是 `git ls-files` 把子模块 gitlink 当普通文件列出，**任何外壳仓都会被误判成 inline**（判据改取 `git ls-files -s` 的 mode ≠ 160000）。现改为三信号探测（自有代码 / 子模块 / 被忽略的嵌套 git 仓），**恰好命中一个才给结论**，信号冲突或零信号一律问一次并落声明（一次性成本：217 个真实仓库实测，仅 12 个触发）。新增 `linked`：代码根**不归本仓所有**，本仓只持有本机目录引用，`path` 允许相对 / `~/` / 绝对三种形式；**只认不造**——不建 worktree、不 clone、不组装工作区，`migrate` 仍只在 `inline` ↔ `shell` 间双向发生。校验按 mode 分家，「声明的代码根解析不到」从 ⛔ 降为 ⚠️ 另列（既存缺陷：流程不碰的代码根没 init 不该挡死整条流程）；新增裸 gitlink ⛔ 与「路径声明不是写权限授权」边界。`workspace-context` 升 v2（`declared_path` / `missing_code_roots`），三种 mode 下元素形状一致、调用方不分支。经 codex 独立评审（一致 12 / 采纳 1 / 不采纳 2，其中 per-code-root 类型标记因 217 仓零样本被实证否决）。方案见 [specs/2026-08-25-workspace-topology-linked-mode-design.md](docs/superpowers/specs/2026-08-25-workspace-topology-linked-mode-design.md)
- 综合方案落地：flag 收敛 49→20、shared-constraints SSOT、realign --scope 四入口
- 治理盲区收敛：scope=health（结构/索引/过大 3 维）+ health-lint rule（state/* + dead-link + adr-only-revision，清单以 [health-lint-implementation.md](skills/pipeline/references/health-lint-implementation.md) Rule 集表为权威），layout.v1+v2 通用
- 新增 skill：backlog（暂缓任务池）
- 新增 skill：idea-mcp-workflow（独立，非 keel）：通过 JetBrains `idea` MCP（`mcp__idea__*` deferred 工具）操作项目的决策/踩坑手册。承载 4 条跨切面纪律（projectPath 必填且须绝对路径 / build 输出防爆=`filesToRebuild` 源头缩范围而非落盘 jq / 依赖未解析 vs 真 bug 强信号 / Maven reload 是 UI 动作 MCP 不暴露）+ 编译主链路，debug·database·refactor 沉 references 按需加载。经 Codex 独立调研（8 条反馈对齐）+ live MCP 实证（纪律 1 报错文案、envo/trade）+ 只读行为抽查。注：skill-creator 触发评测在嵌套 claude -p 环境非判别性（本仓 skill 靠目录发现、非真 Skill 注册），未采纳其分数
- **dev-workflow inline 轻量入口**：`--inline "<任务>" --ac "<AC>"` 无 04 也可进入，物化 stub（AC 落 01 唯一编号源、review_profile 下限 guarded、`grep "来源: inline"` 即回填台账）；协议私有于 [dev-workflow references/inline-entry.md](skills/dev-workflow/references/inline-entry.md)（constraints.md 零改动），spec_version bump devflow.v2，方案见 [specs/2026-07-22-inline-input-satisfaction-design.md](docs/superpowers/specs/2026-07-22-inline-input-satisfaction-design.md)（codex 2 轮审查）
- **superpowers 共存(单向)**：AGENTS.md「工作流路由」节压制外部 process skill 误触发（agent-memory 幂等维护+managed 标记；init/retrofit 实际委托发货、pipeline ℹ️ 兜底）；能力吸收三方对齐结论=9 项已有等价/更强、唯一内化 bugfix 根因门、worktree 并行 FUTURE、"委托+fallback"否决改"可选增强+单一路径"；方案见 [specs/2026-07-22-superpowers-coexistence-design.md](docs/superpowers/specs/2026-07-22-superpowers-coexistence-design.md)（codex 3 轮）+ [workflows.md 共存节](docs/workflows.md#与-superpowers-共存)
- **新增 skill：board（可视化评审面板）**：01/02 → 自包含 HTML 评审页（临时目录不入库），chrome-devtools MCP 双向桥（board_id fail-closed / 读 `window.__review` 写 `agent-*` 白名单），意见经评审修订协议回流（编号不变/新增委托 requirements 增量/删除标废弃/02 走增量设计+ADR），mermaid 渲染须网络 deny-all 沙箱（macOS 配方已实证，含 unix-socket 放行坑）；协议 SSOT 在 [board references/board-protocol.md](skills/board/references/board-protocol.md)，方案见 [specs/2026-07-22-devdocs-review-board-design.md](docs/superpowers/specs/2026-07-22-devdocs-review-board-design.md)（codex 6 轮 R6 PASS）；E2E 冒烟通过（注入转义/状态恢复/导出/沙箱渲染）
- **新增 skill：e2e-test-flow（独立 E2E 实测，非 keel）**：消费已有用例文档（md/html）对**运行中系统**做黑盒 E2E —— 录制真实请求取代猜接口、写型用例只执行一次（含铺数）、DB 只读观测、影响分析仅提升优先级永不缩小范围、只做功能不做视觉断言；单 skill + 4 references 分层，白盒/黑盒由子 Agent 工具集隔离。FUTURE：影响分析可独立抽取（code review 范围评估/回归范围界定），触发=真实跨场景复用需求，参照 worktree 并行 FUTURE 同类封存。方案见 [specs/2026-07-27-ai-e2e-test-flow-design.md](docs/superpowers/specs/2026-07-27-ai-e2e-test-flow-design.md)（codex 7 轮 R7 PASS，R4 熔断后简化重写 568→237 行）
- **新增 skill：markdown-style（Markdown 标记与排版只读审查器，独立，非 keel）**：三组分工 —— M 组 markdownlint（`MD001`–`MD060` 共 **53** 条，7 个编号未定义）由工具判定、T 组中文排版（GB/T 15834 + 排版指北，ID `T1`–`T4`·`T6`·`T7`·`T9`，`T5` 否决 / `T8` 并入 T7）与 L 组 LLM 排版毛病由 AI 通读。**经三轮塌缩为纯只读审查器**：自动修复白名单 27→9→4→0 条整体放弃（`fixable` ≠ **语意安全**，十类破坏模式是核心知识资产）、附带脚本取消（保护区识别 = 实现 CommonMark 子解析器）、W 组文风审查删除（属语意改写，边界原则无例外）。价值内核 = 规则的**出处、冲突与裁决**，非配置本身：GB/T 15834 允许叹号叠用**最多三叠**（推翻排版指北"不重复使用标点"）、省略号以国标六连点 `……` 为准（推翻本地参考项目的 `⋯⋯`）、GB/T 15835 数字用法不纳入（管用字选择非排版）、T2 相对指北 §2 硬规则**主动降级**为只报告。修改走哈希事务，唯一硬不变量 = 落盘与推导逐字节相等（行号子集断言已证伪）。方案见 [specs/2026-07-31-markdown-style-skill-design.md](docs/superpowers/specs/2026-07-31-markdown-style-skill-design.md)（Codex 三轮 + 首次真实运行验证：暴露并回修 8 项缺陷，含 T4 与 `MD060: padded` 表格 padding 互斥、L2 判据 3 因 MD036 尾标点启发式对中文整体沉默而**无处让位**故删除、确认时机判据由整仓改逐文件）
- **新增 skill：doc-organization（文档信息组织指导原则，独立，非 keel）**：五条原则——当前状态与变更历史分离 / 编号先定义再使用 / 引言职责 / 结论单一出处 / 写给缺少你现在上下文的人。**只给原则不做检测**：判据无法机械化（正则会把 `B2B` `HTTP2` `H1` 当编号），修法无法保证语义中立（补定义=猜事实、改引用=丢本地语境）。`system-design` 引用其中两条。
- **新增 skill：prior-art-scan（开工前先例扫描，独立非 keel）**：多角度检索 GitHub/生态找同类项目 → 5 维健康度评估 → 缺口四分类 → 六路径决策（use-as-is / 插件 / 上游贡献 / vendor+patch / 硬 fork / 自建）。三条跨切面纪律：**证据门**（未经工具确认的候选与数字一律不得入报告，幻觉是本 skill 头号风险）、**只读**（allowed-tools 排除全部 GitHub 写工具，fork/issue/PR 只作为行动项交用户批准）、**覆盖门**（6 检索角度全跑留证）。关键判断：star 与 `pushed:` 是假信号（后者匹配任意分支，bot 提交能伪造活跃）；「外部 PR 受纳度」（`author_association` 分布）是独立于健康度的维度，决定"贡献"路径可不可行；默认反对 fork（成本被系统性低估），vendor+patch 为默认优先项。产出 cwd 单文件 md，零污染。github MCP 能力已 live 实测（无 `get_repository`；`minimal_output:true` 不含 license/`pushed_at`；`reason:not-planned` 查询 vs `not_planned` 返回值），坑记录在 `prior-art-scan/references/discovery-matrix.md`（该 skill 已移出本仓，见 skills-local）。方案见 [specs/2026-08-06-prior-art-scan-skill-design.md](docs/superpowers/specs/2026-08-06-prior-art-scan-skill-design.md)
- **作用域匹配准则 + 延后外审修复（第一段）**：新增跨切面准则 [shared/constraints.md §11](skills/shared/constraints.md) `作用域匹配`（评审边界 ≥ 影响边界，与 SSOT 对偶；三条正向规则 + 三条防滥用刹车 `design-time-only`/`not-delivery-granularity`/`no-auto-detection`；适用 keel 流程 skill + dev-flow，人工 review lens 承载不建检测器）+ `doc/project-rule-boundary`（补住 project→skill 方向的提拔缺口，此前只有 skill→shared 设闸）。**发现并修复既存缺陷**：`fast`/`guarded` 的延后外审在 drain 时用工作区 diff，而 Commit 1 已落盘 → **审的是空 diff**；现按 inline（工作区）/ drain（Commit 1 提交 diff）**分离 diff 源**，含 shell 模式逐 `code_root` 拼接。同批删 skip 参数族（2 flag + `INT_PENDING`/`EXT_PENDING` 2 enum 值 + 2 trailer + 双 skip 禁令——它们与 `*_UNRESOLVED` 在阻塞性和恢复动作上等价，唯一效果是把"现在必须做"变成"事后要补的债"）+ 最低发现数门槛（凑数激励）。**第二段（外审输入 task → batch）待第一段真实数据**，触发条件见方案 §3.1，"不做"是合法结局。方案见 [specs/2026-08-06-review-unit-task-to-batch-design.md](docs/superpowers/specs/2026-08-06-review-unit-task-to-batch-design.md)（第 2 稿经 codex + 独立子 Agent 双路审计证伪 6 处，存档于该文 §6）。**⚠️ 空 diff 修复尚未验证**——本仓无可跑的 drain，须在真实项目上验；遗留台账（待执行验证 / 7 项无需数据的删除项 / 5 项封存待数据 / 审计自身的 2 处错误）见 [audits/2026-08-20-complexity-audit-backlog.md](docs/audits/2026-08-20-complexity-audit-backlog.md)
- **单项目污染清理 + 表述去重**：`verify` 曾把 mic-en 的 sprint 实战发现（Java SPI/DTO/PO 字段透传）经"项目 patterns → 项目 AGENTS.md → skill 级默认约束"三级阶梯提拔为跨项目 ⛔ 强制门，而该阶梯第三级在本仓不存在（唯一相近的 `notes-promote` 是项目内部升级）=自我授权；已清 4 文件（含会复制进用户项目的 `verify-report.md` 模板与 P 级评分 SSOT），保留 2 条语言中立项。另确立**镜像边界**（agent 侧 references/SKILL 一律改指针；仅用户侧产物模板允许内联数字——模板复制进项目后 skill 不在场），`verification-flow.md` 572→455、`execution-flow.md` 296→220。审计过程反证：其"层级重申删 20 处"结论按 grep 命中计数、未判用途，实际只有 7 处真重复
- **bugfix 根因诊断门**：原因不明的简单 Bug 必过"复现基线→假设清单→最小仪器化→证伪确认"，根因未证实 ⛔ 不得修复；连续 2 轮证伪 ⚠️ 升级 dev-tasks（吸收自 superpowers systematic-debugging 纪律，内化非委托）
- code-quality 重构为代码质量 SSOT：核心阈值表（统一谓词）+ 命名/注释/日志规范 + 设计原则（代码级），示例拆 references/；日志规范=编码纪律 SSOT（级别纪律/最小上下文/异常纪律/安全红线/事实优先 6 条），system-design log-design-guide 留设计阶段"在哪打点"并指针回此；dev-flow/dev-workflow 编码纪律 + verification-flow 日志卫生审查项已并列接入；deferred：health-lint 镜像一致性 rule（见 [plans/2026-06-12-code-quality-restructure-naming.md](docs/superpowers/plans/2026-06-12-code-quality-restructure-naming.md) §4）
- 新增 skill：dev-flow（非 keel 通用开发执行器：契约先行 + 红绿 + 质量地板 + fresh-context 契约审查；与 dev-workflow 双向 NOT-for，方案见 [plans/2026-06-12-dev-flow-standalone-skill.md](docs/superpowers/plans/2026-06-12-dev-flow-standalone-skill.md)）
- **分层记忆原则（已落地为 SSOT）**：决策/执行/数据三层分离，权威在 [shared/constraints.md §9](skills/shared/constraints.md)。**结构基础已存在**（编号文件提供三层 owner 位置），现役 `state/*`、`adr-only-revision` 只兜**部分**退化症状，**主要靠人工 review lens 承载**（非自动兜底）。
  - **维度 d「SSOT 遵从」与维度 e「三层分离自动检测」均已废弃**：d 依赖已删除的 ssot-lint 无检测对象；e 的关键词扫描复杂度不匹配收益。
