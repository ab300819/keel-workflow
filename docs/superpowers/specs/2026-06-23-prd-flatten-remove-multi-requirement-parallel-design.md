# PRD 扁平化：移除多需求并行 + close 清理脚手架

> 设计文档。状态：待 Codex 审查。
> 触发：mic-en 项目实践验证「多需求并行」为伪需求。

## 背景与动机

PRD 流程当前内置一整套「多需求并行」机器（multi-PRD 模式）：

- `docs/prd/index.md` 全局索引：PRD 清单 + 生命周期状态 + **跨 PRD 全局 FR/NFR 编号注册表**
- `docs/prd/<YYYYMMDD-slug>/` 每需求一个隔离子目录
- supersedes 迭代链、`_archived/` 归档、顶层 `synthesis/` 跨 PRD 综合
- 跨 PRD 引用规则、跨 PRD 编号冲突检测
- `list` / `status` / `archive` / `migrate` 管理子命令
- 配套 governance：`prd-index-ssot.md`（整篇讲跨 PRD 编号 SSOT）

**mic-en 实践结论**：该流程根本无法支撑多需求真正并行推进，「多需求并行」是伪需求。

这与本仓「封存 FUTURE」的判据相反 —— 封存（trace.v1 / layout.v2 / health 维度 d）针对「暂不需要、将来真实痛点会触发」；多需求并行是**已实践、已证伪**的反向证据，应**直接删除**，不进 FUTURE 登记册（逻辑同上一轮废弃 health 维度 e）。

## 决策

### D1 目录模型

`docs/prd/` = **扁平 + 只存当前需求 + 一次性脚手架**。任一时刻只有一个在飞的当前需求。

```
docs/prd/
├── chunks/                 ← 大文档解析后的文本化副本（仅 prd-parse 路径产生）
│   ├── FR-XX-<topic>.md
│   └── NFR-XX-<topic>.md
├── requirements/           ← brainstorm 澄清后的结构化需求
│   ├── index.md            ← 本需求总纲（含跨 chunk 合成结果 + DevDocs 映射表）
│   ├── FR-XX-<topic>.md
│   └── NFR-XX-<topic>.md
└── source/                 ← 原始文件来源记录（.gitignore 排除）
```

无 `index.md` 全局索引、无 `<prd_id>/` 子目录、无 `_archived/`、无顶层 `synthesis/`。

### D2 生命周期

需求生命周期：`brainstorm/解析 → requirements → 设计 → 开发 → close（明确上线）`。

- 被 `/ms-requirements --from-prd` 吸收 = **进入开发流程**，不是需求终点。
- 开发期间需求可变更/优化 → `--revise FR-XX` 原地修订、重跑 `--from-prd` 同步。`docs/prd/` 在整个开发周期内是**活的当前需求脚手架**。
- **close（上线）后需求才真正结束**，此时 `docs/prd/` 可清除。
- 唯一事实源：代码 + 已吸收进 `docs/devdocs/` 的 why 记忆。`docs/prd/` 不承担任何历史/归档职责；历史靠 git。

### D3 删除 / 保留清单

| 删除 | 保留 |
|---|---|
| 三级 multi-PRD 模式判定 | idea→brainstorm（5W1H / MoSCoW 收敛） |
| 全局 `index.md` + 跨 PRD 编号注册表 | 大文档→`chunks/`→逐块 brainstorm |
| `<prd_id>/` 子目录隔离 + 路径间接定位 | **跨块合成**（单需求内 chunk 间术语/约束/横切 NFR/冲突，写 `requirements/index.md`） |
| supersedes 链 + 不变式 | 成熟度三级 + 假设挑战 + ready 门槛 |
| `_archived/` 归档 + 顶层 `synthesis/` | DevDocs 桥接（`--from-prd` / mapping_status / `--back-propagate-prd`） |
| 跨 PRD 引用规则 + 跨 PRD 冲突检测 | `--revise FR-XX`（简化：直查 `requirements/FR-XX-*.md`） |
| `list` / `status` / `archive` / `migrate` 子命令 | PRD 更新（chunk 指纹重解析，单需求内仍有效） |

> **区分**：跨块合成（保留）是单需求内部多 chunk 的综合，写入 `requirements/index.md`；顶层 `synthesis/`（删除）是跨多个 PRD 的综合。二者不同名同实。

### D4 编号与路径

- FR/NFR 在**当前需求内续编**，新需求从头重起。**沿用既有 `FR-XX` 位宽（2 位），不引入 `FR-001` 等新格式**，避免 `--revise` glob / 用户输入变脆。产品阶段编号是映射进 DevDocs 后即作废的临时标识，无需跨需求全局唯一。
- `--from-prd` 路径固定为 `docs/prd/requirements/index.md`（取消 multi/legacy 双路径）。
- mapping 桥接（`mapping_status` / `--from-prd` / `--back-propagate-prd`）**与并行无关，保留**；仅去掉其中的 multi-PRD 分支（如「自动只选 active PRD」「archived/superseded 只读消费」门控）。
- **编号复用前提**：新需求从头重起 FR 编号，依赖 D7 新建门禁确保旧需求脚手架已清理 —— 否则旧 mapping row 会被误当成新 FR 的映射。两者绑定，不可只做其一。

### D5 close 清理（新增）

**入口**：沿用 `/ms-pipeline close`（现编排 `ms-sync → ms-compound → ms-onboard --update`）。**清理为最后一步**——先让 compound 沉淀经验、onboard 固化上下文，把 why 记忆抽干净，再清脚手架，避免信息丢失。

**归属**：清理逻辑由 **ms-prd** 实现（它是 `docs/prd/` 的 owner）；pipeline 仅委托，不自己删文件，守住「pipeline 只路由」约束。

**dry-run → 确认 → 实施**（套用既有 `--dry-run`/`--apply` + ⚠️必须确认 惯例）：

1. **清理范围**：列出 `docs/prd/` 下将删除的文件/目录树。
2. **影响分析**（"已安全吸收"判定，三条件全满足才算可清理）：
   - **枚举实际文件**：扫 `requirements/FR-*.md` / `NFR-*.md` 实际存在的 `product_id`，不只信 mapping 表；
   - **取 authoritative row**：对每个 `product_id`，按既有规范取 `## DevDocs 映射` 表中**最后一行**为权威状态（不能因历史行是 active 就忽略后续 outdated/removed，见 `prd-mapping-status.md` / `prd-devdocs-mapping.md`）；
   - **校验 DevDocs 实际存在**：权威行 `devdocs_id` 必须在 `docs/devdocs/01-requirements.md` 当前 F 列表中实际存在（`--back-propagate-prd` 是显式模式、不保证跑过，光看 mapping 表不足以证明目标还在）；
   - 仅当「最新状态 ∈ {active, remapped} **且** 目标 F 在 DevDocs 存在」→ 标记**可安全清理**；其余（无映射 / outdated / removed / 目标缺失）→ ⚠️ **孤儿/未同步高亮**，默认不删，需用户逐项显式确认；
   - 提示：可安全清理项的 why 记忆已在 `docs/devdocs/` + git 历史，清除安全。
3. **⚠️ 必须确认** → 删除 `docs/prd/`（存在孤儿/未同步项时，确认文案显式列出它们）。

**约束**：清理是 close 的可选末步，不是强制 —— 用户可跳过（保留脚手架供参考）。pipeline close 在无 `docs/prd/` 时静默跳过该步。

### D6 迁移

无迁移机器。`docs/prd/` 既是一次性脚手架，旧的 multi-PRD 布局（若某仓存在）本身可弃，由用户在 close 或手动清理。`AGENTS.md`「当前状态」记一笔变更。

### D7 新建需求门禁（强约束，与 D4 编号复用绑定）

「只存当前需求」必须在 `/ms-prd` 新建需求入口落成**强门禁**，否则旧脚手架残留 + 新需求从头编号会导致旧 mapping row 被误当成新 FR 的映射，`--from-prd` / `--back-propagate-prd` 回写错对象。

`/ms-prd`（brainstorm / prd-parse 新建路径）启动时：

1. 检测 `docs/prd/requirements/index.md` 是否已存在（即已有当前需求脚手架）。
2. 若存在 → **⚠️ 必须确认**，AskUserQuestion 三选一：
   - **继续当前需求**：在现有脚手架上追加/修订（FR 续编，不重起）；
   - **close 清理后新建**：跳转 close 清理（D5）流程，清空后再从头新建；
   - **显式 discard/reset**：用户明确丢弃当前脚手架（清空 `docs/prd/`）后从头新建。
3. 未确认前 **⛔ 禁止**直接从头新建覆盖 —— 防止旧需求被静默吞掉、新旧编号串台。

> 该门禁同时写入 `ms-prd/SKILL.md` 门控表与 `pipeline/SKILL.md` 阶段检测（检测到 flat index 存在且用户意图为「新需求」时触发）。

## 波及面（按文件）

> 核心机制文件 + 下游引用。layout/backlog 中的 archive/supersede 属非 PRD 语境，不在范围内。

### 核心：必改 / 必删

| 文件 | 动作 |
|---|---|
| `skills/prd/SKILL.md` | 大改：删 multi-PRD 判定 / 路径间接定位 / 归档流程 / 权威模型 / supersedes 不变式 / `list`·`status`·`archive`·`migrate`；门控表保留「idea vs 文档」歧义项 + **新增 D7 新建门禁**；产出路径改扁平；`--revise` 简化；`--from-prd` 路径固定；**新增 close 清理能力（D5）** |
| `skills/prd/references/governance/prd-index-ssot.md` | **删除**（整篇为跨 PRD 编号 SSOT，失去存在意义） |
| `skills/prd/templates/global-index-template.md` | **删除** |
| `skills/prd/templates/requirements-index-template.md` | 删 `prd_id`/`prd_status`/`supersedes` 元信息行 + legacy 路径括注 |
| `skills/prd-parser/SKILL.md` | 删 `fr_start/nfr_start` 跨 PRD 续编入参 / multi-PRD 续编分支；FR/NFR 从 01 起；产出路径扁平 |
| `skills/prd-brainstorm/SKILL.md` | 删「multi-PRD 起始值来自全局注册表」；FR/NFR 编号规则改单需求内 |
| `skills/prd/references/governance/prd-revision-policy.md` | 删「PRD 整体生命周期」行 + 状态机 supersede/archive 分支；保留单 FR revise / chunk 指纹 / 模板结构 |
| `skills/prd/references/governance/prd-devdocs-mapping.md` | 外科式去 multi 分支（回扫算法「只选 active PRD」「archived/superseded 只读」门控）；mapping 状态机保留 |
| `skills/prd/templates/requirements-item-template.md` | 检查并去 multi-PRD 残留引用（1 处） |

### 下游：跟改

| 文件 | 动作 |
|---|---|
| `skills/pipeline/SKILL.md` | 阶段检测去「读 `docs/prd/index.md` active 清单 / per-PRD index」分支，改为直接检测 `docs/prd/requirements/index.md`；检测到 flat index 已存在 + 用户意图「新需求」时触发 D7 门禁；close 入口编排末步加 ms-prd 清理委托 |
| `skills/requirements/SKILL.md` | `--from-prd` 路径固定 `docs/prd/requirements/index.md`，去 multi/legacy 双路径 |
| `skills/sync/SKILL.md` | `--back-propagate-prd` 去 multi-PRD 定位分支 |
| `skills/verify/references/schema-drift.md` | 去 global-index / multi-PRD 相关 schema 项（1 处） |
| `skills/prd-brainstorm/references/realign.md`、`skills/prd-parser/references/realign.md` | 去 multi-PRD 残留（如有） |
| `docs/architecture.md` | 更新 PRD 流程描述（去多目录隔离表述） |
| `docs/workflows.md` | 更新 PRD 走查（去 multi-PRD） |
| `AGENTS.md` | 领域术语「PRD 流程」去「支持多目录隔离」；当前状态记一笔变更 |
| `docs/superpowers/specs/2026-06-08-...-design.md` | 1 处引用，加后续变更注记 |

### 需复核（疑似非 PRD 语境，默认不动）

`skills/backlog/*`、`skills/iteration-policy/SKILL.md`、`skills/pipeline/references/layout/*`、`skills/pipeline/references/health-lint-implementation.md`、`realign-scope-*.md` —— 这些 archive/supersede/prd_id 命中多为 layout 版本治理或 backlog 语境，实施时逐一确认，命中 PRD 并行才改。

## 风险与失败模式

1. **遗漏下游引用**：multi-PRD 关键词散落 30+ 文件，部分是非 PRD 语境误命中。实施时须区分，避免误删 layout/backlog 的 archive 语义。缓解：实施后全仓 grep 复核 `multi-PRD`/`全局 index`/`<prd_id>`/`supersede` 零残留（PRD 语境）。
2. **mapping 桥接误伤**：`--from-prd`/`--back-propagate-prd`/mapping_status 大部分与并行无关，须只动 multi 分支，保留单需求桥接链路完整。
3. **close 清理误删未吸收需求**：孤儿拦截（D5.2）依赖 mapping 表完整性；若用户从未跑 `--from-prd`，mapping 表为空 → 全部判为孤儿 → 默认不删并警示，安全侧偏保守。
4. **既有仓库残留 multi-PRD 布局**：无迁移机器，旧布局靠用户清理；过渡期文档应说明「旧多目录布局可直接弃」。

## 验证

- grep 复核：PRD 语境下 `multi-PRD`/`全局 index`/`编号注册表`/`<prd_id>`/`supersedes`/`_archived`/顶层 `synthesis/`/`/ms-prd list|status|archive|migrate` 零残留。
- 链路自洽：`ms-prd`（扁平产出）→ `ms-requirements --from-prd docs/prd/requirements/index.md` → mapping 桥接 → close 清理，路径与字段一致。
- SKILL.md 行数：`ms-prd/SKILL.md` 删减后应显著低于 500 行硬约束。
- close 清理：dry-run 输出范围 + 影响（枚举实际文件 + authoritative row + DevDocs 存在性校验）+ 孤儿/未同步警示三段；`--apply` 才物理删除；无 `docs/prd/` 时静默跳过。
- D7 门禁：已有 `docs/prd/requirements/index.md` 时新建需求触发 ⚠️ 三选一，未确认 ⛔ 不覆盖。
- 编号位宽：全流程统一 `FR-XX` / `NFR-XX`（2 位），无 `FR-001` 残留。
