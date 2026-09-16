---
name: prd
description: 将模糊产品想法或大型 PRD 整理为可供 DevDocs 消费的需求，选择探索或解析路径。已明确需求编码用 requirements。
metadata:
  patterns: [pipeline]
  interaction: multi-turn
  handoff: yaml-summary-v1
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Task
user-invocable: true
---

# 产品需求编排器

编排产品需求处理流程，自动路由到 brainstorm 或 PRD 解析，产出结构化需求包供 DevDocs 消费。

## 快速开始

**一句话**: 处理模糊想法或大型 PRD 文档，产出结构化 FR-XX/NFR-XX 需求。

**最常见用法**: `/prd`（自动检测新建/修订/继续）

**不适合?** 需求已明确→`/requirements`

## 详细文档

- PRD 修订边界：[references/governance/prd-revision-policy.md](references/governance/prd-revision-policy.md)
- PRD ↔ DevDocs Mapping：[references/governance/prd-devdocs-mapping.md](references/governance/prd-devdocs-mapping.md)
- 共享约束 SSOT：[../shared/constraints.md](../shared/constraints.md)

> 本 skill 遵循共享约束 SSOT：门控标记、yaml-summary-v1、Task 委托、用户确认、Recovery 格式、只读 / dry-run、FUTURE 三态、realign / spec_version 见 [skills/shared/constraints.md](../shared/constraints.md)。本文件只描述 PRD 私有规则。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 定位

```
用户 → /prd → 自动检测输入类型 → 路由到对应流程
                         ↓
              prd-brainstorm（想法澄清）
              prd-parser（文档拆分）
                         ↓
              结构化需求包 → DevDocs 衔接
```

**核心价值**：弥补 DevDocs 对模糊想法和大型 PRD 的处理不足，提供需求探索到结构化输出的完整路径。

## 单需求脚手架原则

`docs/prd/` 是**当前需求的一次性脚手架**，扁平结构，任一时刻只服务一个在飞需求：

- 不维护跨需求的全局索引、编号注册表、归档或迭代链 —— 多需求并行经实践证伪，已移除。
- 需求生命周期：`brainstorm/解析 → requirements → 设计 → 开发 → close(上线)`。被 `/requirements --from-prd` 吸收只是**进入开发流程**，不是终点；开发期间需求仍可 `--revise` 修订。
- **close（上线）后**需求才结束，`docs/prd/` 可由 `/prd clear`（或 `/pipeline close` 末步）清理。唯一事实源是代码 + 已吸收进 `docs/devdocs/` 的 why 记忆；历史靠 git，不靠 `docs/prd/` 留存。

## 运行模式

```bash
/prd                 → 自动检测输入类型（默认感知已有系统）
/prd brainstorm      → 强制头脑风暴模式
/prd prd             → 强制 PRD 解析模式
/prd --revise FR-03  → 单个 FR 重新 brainstorm
/prd clear [--dry-run|--apply]  → 清理当前需求脚手架（close 收尾用）
```

## 新建需求门禁（强约束）

`/prd` 进入**新建路径**（brainstorm / prd-parse）前，先检测当前脚手架，确保"只存当前需求"：

1. 检测 `docs/prd/requirements/index.md` 是否已存在。
2. **不存在** → 绿地，直接新建，FR/NFR 从 `FR-01` / `NFR-01` 起。
3. **已存在** → ⚠️ 必须确认，AskUserQuestion 三选一：
   - **继续当前需求**：在现有脚手架上追加 / 修订（FR 续编，不重起编号）；
   - **close 清理后新建**：跳转 `/prd clear` 流程，清空后再从头新建；
   - **显式 discard / reset**：用户明确丢弃当前脚手架（清空 `docs/prd/`）后从头新建。
4. 未确认前 ⛔ 禁止直接覆盖新建 —— 防止旧需求被静默吞掉、新旧编号串台（旧 mapping row 会被误当成新 FR 的映射）。

## 自动检测逻辑

无参数或未指定模式时，分析用户输入自动路由：

```text
分析用户输入
    |
    +-- 输入 < 200 字 + 无结构化标记 → brainstorm 完整模式
    |
    +-- 输入 > 2000 字 或引用大文件 → prd-parser + 逐块 brainstorm
    |
    +-- 用户明确指定模式 → 直接路由
    |
    +-- 模糊（200~2000 字，无法确定）→ AskUserQuestion 确认
```

**判断标准**：
- "无结构化标记"指无标题层级、无编号列表、无 YAML 头等
- "引用大文件"指用户提供文件路径且文件 > 2000 字，或为 PDF/图片等二进制格式
- 模糊区间时询问：「输入内容介于想法和文档之间，请确认：(1) 作为想法进行头脑风暴 (2) 作为文档进行结构化解析」

## PRD 私有门控

**门控标记**：见 [skills/shared/constraints.md § 1](../shared/constraints.md#1-门控标记-ssot)

| 触发点 | 门控 | 恢复 / 继续 |
|---|---|---|
| 新建需求时 `docs/prd/requirements/index.md` 已存在 | ⚠️ 必须确认 | 三选一：继续当前需求 / `/prd clear` 清理后新建 / 显式 discard 后新建 |
| 输入 200~2000 字且无法判断是想法还是文档 | ⚠️ 必须确认 | 用户选择「作为想法进行头脑风暴」或「作为文档进行结构化解析」 |
| `--revise` 目标 FR 文件不存在 | ⛔ 禁止继续 | 报错退出；检查编号或先创建该 FR |
| `clear` 检测到孤儿 / 未同步需求 | ⚠️ 必须确认 | 显式确认后才删（见 [清理脚手架](#清理脚手架close-收尾)） |

## Step 0: 上下文感知（自动，所有场景前置）

启动时自动检测是否存在已有系统，无需用户指定：

| 项 | 规则 | 输出 |
|---|---|---|
| 代码检测 | 检查 `git ls-files` 是否有非文档文件，或检测常见代码文件模式 | 有代码 → 委托 codebase-insight（由其缓存机制决定是否重扫），读取返回的 `docs/codebase-insight.md`；无代码 → 绿地模式，跳过 |
| DevDocs 检测 | 检测 `docs/devdocs/01-requirements.md` | 存在 → 提取已有 F/US 列表作为补充上下文；不存在 → 跳过 |
| 设计资产探测 | 按 [`references/design-context.md`](references/design-context.md) 探测协议执行 | 进入 Step 1+ 正常编排流程（brainstorm / prd-parse） |

携带已有上下文后，brainstorm 探索时标注每个 FR-XX 与已有系统的关系：
- FR-XX YAML 增加 `relation` 字段：`new`（全新功能）| `extend`（扩展已有）| `modify`（修改已有）
- `extend` / `modify` 时增加 `related_module` 字段标注关联的已有模块

## --revise 模式

允许用户对单个 FR 重新进入 brainstorm 澄清，无需重新提交整个需求：

```text
/prd --revise FR-03
    |
    v
1. 定位 FR-03 文件：glob docs/prd/requirements/FR-03-*.md
   ⛔ 若文件不存在 → 报错退出（检查编号或先创建）
   记录实际路径（source_fr_path），后续回写使用同一路径
    |
    v
2. 提取 FR-03 的功能描述和验收意图，作为 brainstorm 上下文
    |
    v
3. Task: prd-brainstorm（完整模式）
    |  传入上下文：FR-03 现有功能描述 + 验收意图 + 用户修正说明
    |  约束：brainstorm 产出必须保持 FR-03 的 id 和编号不变
    |  输出：更新后的 FR-03 内容（不分配新编号）
    |
    v
4. 用 brainstorm 产出**原地覆盖** source_fr_path（保持 id: FR-03）+ 更新 requirements/index.md
    |
    v
5. 如果 FR-03 已有 DevDocs 映射 → 将 mapping_status 置为 outdated
    |  提示：「FR-03 已映射为 F-XXX，建议重新运行 /requirements --from-prd 更新」
```

### mapping_status 规范

> 详细规范见 [`references/prd-mapping-status.md`](references/prd-mapping-status.md)（列定义、状态枚举、authoritative row 规则）

## 清理脚手架（close 收尾）

`/prd clear` 在需求 close（上线）后清理 `docs/prd/` 一次性脚手架。通常由 `/pipeline close` 末步委托（在 sync/compound/onboard 把 why 记忆抽干净后执行），也可独立调用。

**dry-run → 确认 → 实施**（默认 `--dry-run`，`--apply` 才物理删除）：

1. **清理范围**：列出 `docs/prd/` 下将删除的文件/目录树。
2. **影响分析**（"已安全吸收"判定，三条件全满足才算可清理）：
   - **枚举实际文件**：扫 `requirements/FR-*.md` / `NFR-*.md` 实际存在的 `product_id`，不只信 mapping 表；
   - **取 authoritative row**：对每个 `product_id`，取 `requirements/index.md` 的 `## DevDocs 映射` 表中**最后一行**为权威状态（不能因历史行是 active 就忽略后续 outdated/removed，见 [prd-mapping-status.md](references/prd-mapping-status.md)）；
   - **校验 DevDocs 实存**：权威行 `devdocs_id` 必须在 `docs/devdocs/01-requirements.md` 当前 F 列表中实际存在；
   - 仅当「最新状态 ∈ {active, remapped} **且** 目标 F 在 DevDocs 存在」→ 标记**可安全清理**；其余（无映射 / outdated / removed / 目标缺失）→ ⚠️ **孤儿 / 未同步高亮**，默认不删。
3. **⚠️ 必须确认** → `--apply` 删除 `docs/prd/`；存在孤儿 / 未同步项时，确认文案显式列出它们。
4. 无 `docs/prd/` 时静默跳过（已清理）。

## 编排流程

| 场景 | 输入 | 步骤 | 输出 / 门控 |
|---|---|---|---|
| 头脑风暴（idea → requirements） | 用户输入（一句话/简短想法） | Task: prd-brainstorm（完整模式），按 5W1H → 用户旅程 → MoSCoW 收敛 | 生成 requirements/ 小文档 + index.md；成熟度评估 → DevDocs 衔接建议 |
| PRD 解析（大文档 → chunks → requirements） | 用户提供 PRD 文档 | 1. Task: prd-parser（转换 + 拆分 → chunks/FR-XX.md + NFR-XX.md）<br>2. 逐块 Task: prd-brainstorm --chunk `<chunk文件路径>`；自适应深度：成熟块快速确认，模糊块深入探索；终判分类：复核 parser 的 FR/NFR 初判；入参示例：`/prd-brainstorm --chunk docs/prd/chunks/FR-09-用户认证.md`<br>3. 跨块合成：全局术语、共享假设、横切 NFR、冲突/重复解决<br>4. 生成/更新 requirements/index.md 总纲<br>5. 成熟度评估 | DevDocs 衔接建议 |
| PRD 更新（增量处理） | 用户提供更新后的 PRD | 1. Task: prd-parser（重新拆分），计算新 document_fingerprint<br>2. 指纹对比：通过 chunk_key 匹配新旧块，对比 source_fingerprint<br>3. 仅对 outdated/pending 块调用 prd-brainstorm<br>4. 更新 index.md + 成熟度重评估 | 不变 → 保持 clarified，跳过；变化 → 标记 outdated，重新 brainstorm；新增 → 创建新文件，status=pending；删除 → 标记 removed，对应 requirement 标记失效 |

## 跨块合成（Step 3 详解）

PRD 场景中，所有块澄清完成后执行跨块合成（单需求内部多 chunk 的综合，写入 `requirements/index.md`）：

### 全局术语表

扫描所有 requirements 文件，提取重复出现的领域术语，统一定义写入 index.md。

### 共享假设与约束

识别不属于单个块但影响多个需求的假设和约束条件。

### 横切 NFR

识别跨多个 FR 的非功能需求（如全局性能指标、安全策略、兼容性要求），汇总到 index.md 的横切 NFR 章节。

### 冲突与重复解决

- **内容冲突**：不同块对同一功能的描述不一致 → 记录冲突项，标注来源块，建议决议
- **重复检测**：多个块描述相同功能 → 合并或标注主从关系
- **分类冲突**：brainstorm 终判与 parser 初判不一致 → 以 brainstorm 终判为准，index.md 标注 `来源: FR-01 (复判为 NFR)`

## 成熟度标记

轻量三级标记，**建议性不硬阻塞**：

| 级别 | 含义 | 特征 |
|------|------|------|
| `idea` | 功能范围未收敛 | 刚完成初步头脑风暴，MoSCoW 未确定 |
| `draft` | 基本明确但有开放问题 | 主要功能已识别，部分细节待澄清 |
| `ready` | 可进入 DevDocs | 通过 ready 门槛检查 |

### 假设挑战（产品层，ready 评估前必须执行）

所有进入 ready 评估的产品输出均须执行（PRD 路径和 idea→brainstorm 路径均触发）。对全局需求进行假设有效性审查：

| # | 挑战问题 |
|---|---------|
| 1 | 识别的用户角色是否真实存在于目标用户群？ |
| 2 | 每个 FR 解决的是根本问题还是表面症状？ |
| 3 | 我们决定不做的是什么？排除/包含它会改变价值主张吗？ |
| 4 | 哪些功能是真正独立的，哪些只有作为整体才有价值？ |

将挑战结论记入 index.md 的「假设挑战」节（确认的假设 / 需修正的假设 / 范围调整）。

### ready 门槛检查（建议性）

- [ ] 至少 1 个主要用户角色已明确
- [ ] 范围边界已定义（包含/排除）
- [ ] 每个 FR-XX 有至少 1 条验收意图
- [ ] 无 status=pending 的块（全部至少 clarified）
- [ ] 假设挑战已执行，且无未解决的「需修正假设」

未满足时在 index.md 标注缺失项，用户可选择仍然进入 DevDocs。

## DevDocs 桥接

### 衔接时机

当整体 maturity=ready 时，主动推荐：

```
需求包已就绪（maturity: ready），建议运行：
/requirements --from-prd docs/prd/requirements/index.md
```

maturity 为 draft 时也可衔接，但需提示用户开放问题可能影响后续质量。

### 衔接原则

- 需求文件**不分配 F/US/AC 编号**，编号权属于 DevDocs
- FR-XX/NFR-XX 为 product 阶段唯一标识，进入 DevDocs 后映射为 F-XXX
- 需求文件存放于 `docs/prd/`，不写入 `docs/devdocs/`
- 以小文档形式传入 DevDocs：index.md 提供全局视图，各 FR-XX 对应独立功能领域

## 编排规范（子 Agent 调度）

**Task tool / 子 Agent 委托规则**：见 [skills/shared/constraints.md § 3](../shared/constraints.md#3-task-tool--子-agent-委托规则)

| 分工 | PRD 私有约束 |
|---|---|
| 委托 | prd 通过 Task 启动 prd-parser 和 prd-brainstorm（逐块），并接收 YAML 摘要 |
| 自执行 | 跨块合成、index.md 生成、clear 清理由 prd 自身执行 |
| 摘要传递 | 阶段间只传递 YAML 摘要 + 文件路径 + 新增编号列表；编排 Agent **不读取**子技能的完整输出文档内容来做编排决策 |
| 异常回退 | 子 Agent 返回 `status: failed` + `blockers` 时，展示阻塞项并询问用户修复/跳过/终止；**不自行读取文档排障** |
| 上下文隔离 | 每个子 Agent 自行读取所需的前置文件（从 `docs/prd/` 文件系统），不依赖编排 Agent 传递全文 |

## 文件产出路径

```
docs/prd/
+-- chunks/                     <- PRD 原文完整文本化副本（仅 prd-parse 路径产生）
|   +-- FR-XX-<topic>.md
|   +-- NFR-XX-<topic>.md
+-- requirements/               <- brainstorm 澄清后的结构化需求
|   +-- index.md                <- 本需求总纲（含跨块合成结果 + DevDocs 映射表）
|   +-- FR-XX-<topic>.md
|   +-- NFR-XX-<topic>.md
+-- source/                     <- 原始文件来源记录（.gitignore 排除）
    +-- manifest.md
    +-- original-prd.md
```

**模板**：
- 总纲模板：`templates/requirements-index-template.md`
- 需求分文件模板：`templates/requirements-item-template.md`

## 权威模型

`docs/prd/requirements/index.md` 是当前需求以下信息的唯一权威源：需求清单、跨块合成结果（术语/假设/横切 NFR/冲突）、假设挑战、DevDocs 映射。各 FR-XX/NFR-XX 分文件为对应需求项的内容权威。

- FR/NFR 在当前需求内续编、两位数字（`FR-XX`），一旦分配在本需求内不复用。
- 新需求从 `FR-01` 重起 —— 产品阶段编号是映射进 DevDocs 后即作废的临时标识，无需跨需求全局唯一（依赖[新建需求门禁](#新建需求门禁强约束)确保旧脚手架已清理）。
- mapping 状态机（active/outdated/remapped/removed、authoritative row）见 [prd-mapping-status.md](references/prd-mapping-status.md)。

## 约束

### 编排约束

- [ ] **pipeline 仅负责路由、衔接和跨块合成，不复制原子 skill 的探索/解析逻辑**
- [ ] **brainstorm 和 prd-parser 阶段必须委托给对应 skill 执行**
- [ ] **阶段间传递的信息仅限：YAML 摘要、文件路径、新增编号列表**

### 单需求脚手架约束

- [ ] **新建需求前必须执行门禁检测**（已有 index.md 时 ⚠️ 三选一，未确认 ⛔ 不覆盖）
- [ ] **不维护跨需求的全局索引 / 编号注册表 / 归档 / 迭代链**
- [ ] **clear 删除前必须输出范围 + 影响 dry-run，孤儿/未同步项默认不删**

### 自动检测约束

- [ ] **优先使用输入长度 + 结构特征自动判断，无法判断时才提问**
- [ ] **AskUserQuestion 最多 1 次确认路由，不开放式提问**

### 成熟度约束

- [ ] **成熟度标记为建议性，不硬阻塞流程**
- [ ] **maturity=idea 时不主动推荐 DevDocs 衔接**

### 编号约束

- [ ] **FR-XX/NFR-XX 为 product 阶段唯一 ID，不分配 F/US/AC 编号**

## Skill 协作

| 场景 | 编排的 Skill 链 |
|------|----------------|
| 头脑风暴 | 新建门禁 → prd-brainstorm → index 生成 → ready 检查 |
| PRD 解析 | 新建门禁 → prd-parser → 逐块 prd-brainstorm → 跨块合成 → index 生成 → ready 检查 |
| PRD 更新 | prd-parser（重拆）→ 指纹对比 → 仅 outdated 块 brainstorm → index 更新 |
| 清理收尾 | clear（dry-run → 孤儿拦截 → ⚠️确认 → 删），通常由 pipeline close 末步委托 |
| DevDocs 衔接 | ready 时推荐 requirements --from-prd |

## 子 Agent 摘要格式

**yaml-summary-v1 envelope**：见 [skills/shared/constraints.md § 2](../shared/constraints.md#2-yaml-summary-v1-envelope-ssot)

**summary.details 私有字段**：

| 字段 | 值域 / 示例 |
|---|---|
| `index_path` | `docs/prd/requirements/index.md` |
| `mode` / `maturity` | `brainstorm \| prd-parse \| clear` / `idea \| draft \| ready` |
| `functional_count` / `nonfunctional_count` | 功能 / 非功能数量 |
| `clarified_count` / `open_questions` | 已澄清块数 / 开放问题数 |
| `ready_checks_passed` / `ready_checks_total` | ready 检查通过数 / 总数 |
| `clear_removable` / `clear_orphans` | 仅 clear 模式：可安全清理 / 孤儿未同步项数 |

**PRD status 判定**：`success` = 所有块处理完成且 index.md 已生成（clear 模式：清理完成或 dry-run 报告生成）；`partial` = 部分块处理完成（用户中断或部分块失败）；`failed` = 关键步骤失败（如 PRD 无法解析）。

**产物字段**：`output_files` 列出 index 与 FR/NFR 文件；`new_ids.requirements` 记录 `FR-09~FR-14, NFR-04~NFR-05` 这类新增编号；`next_recommended` 可指向 `requirements --from-prd docs/prd/requirements/index.md`。

## 下一步

pipeline 完成后，根据成熟度给出建议：

- `ready` → 推荐 `/requirements --from-prd docs/prd/requirements/index.md`
- `draft` → 提示开放问题清单，建议补充后再衔接，或用户选择直接进入 DevDocs
- `idea` → 建议继续 `/prd brainstorm` 深化探索
