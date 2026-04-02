---
name: ms-prd
description: Product requirements orchestrator. Routes ideas and PRDs through brainstorm and parsing workflows, producing structured requirements for DevDocs consumption. Use for fuzzy ideas, large PRD documents, or when users say "产品需求", "PRD", "需求探索", "头脑风暴", "brainstorm", "产品流程". NOT for already-structured requirements (use ms-requirements) or direct skill invocation.
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

**最常见用法**: `/ms-prd`（自动检测新建/修订/继续）

**不适合?** 需求已明确→`/ms-requirements`

## 语言规则

- 支持中英文提问
- 统一中文回复

## 定位

```
用户 → /ms-prd → 自动检测输入类型 → 路由到对应流程
                         ↓
              ms-prd-brainstorm（想法澄清）
              ms-prd-parser（文档拆分）
                         ↓
              结构化需求包 → DevDocs 衔接
```

**核心价值**：弥补 DevDocs 对模糊想法和大型 PRD 的处理不足，提供需求探索到结构化输出的完整路径。

## 运行模式

```bash
/ms-prd              → 自动检测输入类型（默认感知已有系统）
/ms-prd brainstorm   → 强制头脑风暴模式
/ms-prd prd          → 强制 PRD 解析模式
/ms-prd --revise FR-03  → 单个 FR 重新 brainstorm
/ms-prd list         → 列出所有 PRD 及状态
/ms-prd archive <prd_id> → 归档指定 PRD
/ms-prd status <prd_id>  → 查看单个 PRD 状态详情
```

## 多 PRD 模式判定

启动时自动检测目录结构，确定运行模式：

**三级判定**（优先级从高到低）：
1. 存在 `docs/prd/index.md` 且含 PRD 清单表 → **multi-PRD 模式**
2. 仅存在顶层 `docs/prd/chunks/` 或 `docs/prd/requirements/` 且无全局 index → **legacy 单 PRD 模式**，回退扁平行为
3. 两者同时存在 → **⚠️ 必须确认**，提示用户执行 `/ms-prd migrate` 或手动清理

**路径解析**：统一使用 `prd_id → 路径` 间接定位：
- 先查 `docs/prd/<prd_id>/`，再查 `docs/prd/_archived/<prd_id>/`（仅限只读操作）

**新建 PRD**：生成 `YYYYMMDD-<slug>` 目录名（同日冲突追加 `-2`、`-3`），读取全局 index 编号注册表获取 FR/NFR 最大编号，将起始值（`fr_start`, `nfr_start`）作为参数传给 parser。

**编号分配职责**：ms-prd 编排层从全局注册表获取起始编号 → 传给 ms-prd-parser → parser 从该值续编 → brainstorm 块澄清沿用 chunk 编号。

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

## Step 0: 上下文感知（自动，所有场景前置）

启动时自动检测是否存在已有系统，无需用户指定：

```text
/ms-prd 启动
    |
    v
Step 0: 上下文感知
    |
    +-- 检测项目是否有代码（检查 git ls-files 是否有非文档文件，或检测常见代码文件模式）
    |   ├── 有代码 → 委托 ms-codebase-insight（由其缓存机制决定是否重扫）
    |   │            读取返回的 docs/codebase-insight.md 作为已有上下文
    |   └── 无代码 → 绿地模式，跳过
    |
    +-- 检测 docs/devdocs/01-requirements.md
    |   ├── 存在 → 提取已有 F/US 列表作为补充上下文
    |   └── 不存在 → 跳过
    |
    +-- 设计资产探测 → 按 references/design-context.md 探测协议执行
    |
    v
Step 1+: 正常编排流程（brainstorm / prd-parse）
```

携带已有上下文后，brainstorm 探索时标注每个 FR-XX 与已有系统的关系：
- FR-XX YAML 增加 `relation` 字段：`new`（全新功能）| `extend`（扩展已有）| `modify`（修改已有）
- `extend` / `modify` 时增加 `related_module` 字段标注关联的已有模块

## --revise 模式

允许用户对单个 FR 重新进入 brainstorm 澄清，无需重新提交整个 PRD：

```text
/ms-prd --revise FR-03
    |
    v
1. 定位 FR-03 文件：
   multi-PRD 模式：glob docs/prd/*/requirements/FR-03-*.md 定位所属 PRD
   legacy 模式：查 docs/prd/requirements/FR-03-*.md
   ⛔ 若文件位于 _archived/ 下 → 禁止 revise（提示：已归档 PRD 不可修改，需创建新版 PRD）
   记录实际路径（source_fr_path），后续回写使用同一路径
    |
    v
2. 提取 FR-03 的功能描述和验收意图，作为 brainstorm 上下文
    |
    v
3. Task: ms-prd-brainstorm（完整模式）
    |  传入上下文：FR-03 现有功能描述 + 验收意图 + 用户修正说明
    |  约束：brainstorm 产出必须保持 FR-03 的 id 和编号不变
    |  输出：更新后的 FR-03 内容（不分配新编号）
    |
    v
4. 用 brainstorm 产出**原地覆盖** source_fr_path（保持 id: FR-03）+ 更新同目录下的 index.md
    |
    v
5. 如果 FR-03 已有 DevDocs 映射 → 将 mapping_status 置为 outdated
    |  提示：「FR-03 已映射为 F-XXX，建议重新运行 /ms-requirements --from-prd 更新」
```

### mapping_status 规范

> 详细规范见 `references/prd-mapping-status.md`（列定义、状态枚举、authoritative row 规则）

## 编排流程

### 场景 1：头脑风暴（idea → requirements）

```text
用户输入（一句话/简短想法）
    |
    v
Task: ms-prd-brainstorm（完整模式）
    |  ← 5W1H → 用户旅程 → MoSCoW 收敛
    v
生成 requirements/ 小文档 + index.md
    |
    v
成熟度评估 → DevDocs 衔接建议
```

### 场景 2：PRD 解析（大文档 → chunks → requirements）

```text
用户提供 PRD 文档
    |
    v
Step 1: Task: ms-prd-parser
    |  ← 转换 + 拆分 → chunks/FR-XX.md + NFR-XX.md
    v
Step 2: 逐块 Task: ms-prd-brainstorm --chunk <chunk文件路径>
    |  ← 自适应深度：成熟块快速确认，模糊块深入探索
    |  ← 终判分类：复核 parser 的 FR/NFR 初判
    |  ← 入参示例：/ms-prd-brainstorm --chunk docs/prd/<prd_id>/chunks/FR-09-用户认证.md
    v
Step 3: 跨块合成
    |  ← 全局术语、共享假设、横切 NFR、冲突/重复解决
    v
Step 4: 生成/更新 requirements/index.md 总纲
    |
    v
Step 5: 成熟度评估 → DevDocs 衔接建议
```

### 场景 3：PRD 更新（增量处理）

```text
用户提供更新后的 PRD
    |
    v
Step 0: 留存原始文档（仅 multi-PRD 模式）
    |  将 source/ 全量复制到 _snapshots/<YYYYMMDD-HHMMSS>/source/
    |  _snapshots/ 不入库，与 source/ 同忽略策略
    v
Step 1: Task: ms-prd-parser（重新拆分）
    |  ← 计算新 document_fingerprint
    v
Step 2: 指纹对比
    |  ← 通过 chunk_key 匹配新旧块
    |  ← 对比 source_fingerprint
    |
    +-- 不变 → 保持 clarified，跳过
    +-- 变化 → 标记 outdated，重新 brainstorm
    +-- 新增 → 创建新文件，status=pending
    +-- 删除 → 标记 removed，对应 requirement 标记失效
    |
    v
Step 3: 仅对 outdated/pending 块调用 ms-prd-brainstorm
    |
    v
Step 4: 更新 index.md + 成熟度重评估
```

## 跨块合成（Step 3 详解）

PRD 场景中，所有块澄清完成后执行跨块合成：

### 全局术语表

扫描所有 requirements 文件，提取重复出现的领域术语，统一定义写入 index.md。

### 共享假设与约束

识别不属于单个块但影响多个需求的全局假设和约束条件。

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

### ready 门槛检查（6 项，建议性）

- [ ] 至少 1 个主要用户角色已明确
- [ ] 范围边界已定义（包含/排除）
- [ ] 每个 FR-XX 有至少 1 条验收意图
- [ ] 开放问题数 <= 总需求项的 20%
- [ ] 无 status=pending 的块（全部至少 clarified）
- [ ] 假设挑战已执行，且无未解决的「需修正假设」

未满足时在 index.md 标注缺失项，用户可选择仍然进入 DevDocs。

## DevDocs 桥接

### 衔接时机

当整体 maturity=ready 时，主动推荐：

```
需求包已就绪（maturity: ready），建议运行：
/ms-requirements --from-prd <实际 index.md 路径>
```

> 路径使用当前 pipeline 实际写入的 index.md 路径（multi-PRD: `docs/prd/<prd_id>/requirements/index.md`；legacy: `docs/prd/requirements/index.md`）。archived PRD 允许只读 `--from-prd`。

maturity 为 draft 时也可衔接，但需提示用户开放问题可能影响后续质量。

### 衔接原则

- 需求文件**不分配 F/US/AC 编号**，编号权属于 DevDocs
- FR-XX/NFR-XX 为 product 阶段唯一标识，进入 DevDocs 后映射为 F-XXX
- 需求文件存放于 `docs/prd/<prd_id>/`（legacy 兼容 `docs/prd/`），不写入 `docs/devdocs/`
- 以小文档形式传入 DevDocs：index.md 提供全局视图，各 FR-XX 对应独立功能领域

## 编排规范（子 Agent 调度）

### 调度原则

pipeline 调用其他技能时，**必须通过 Task tool 启动子 Agent**：

```text
ms-prd（编排层）
    |
    +-- Task: ms-prd-parser → YAML 摘要
    +-- Task: ms-prd-brainstorm（逐块）→ YAML 摘要
    +-- 跨块合成（pipeline 自身执行）
    +-- 生成 index.md（pipeline 自身执行）
```

### 摘要传递

阶段间只传递 YAML 摘要 + 文件路径。编排 Agent **不读取**子技能的完整输出文档内容来做编排决策。

### 异常回退

子 Agent 返回 `status: failed` + `blockers` 时：
1. 展示阻塞项给用户
2. 询问用户处理方式（修复/跳过/终止）
3. **不自行读取文档排障**

### 上下文隔离

每个子 Agent 自行读取所需的前置文件（从 `docs/prd/` 文件系统），不依赖编排 Agent 传递全文。

## 文件产出路径

### multi-PRD 模式

```
docs/prd/
+-- index.md                        <- 全局 PRD 索引（source of truth）
+-- <prd_id>/                       <- YYYYMMDD-slug 格式
|   +-- chunks/                     <- PRD 原文完整文本化副本
|   |   +-- FR-XX-<topic>.md
|   |   +-- NFR-XX-<topic>.md
|   +-- requirements/               <- brainstorm 澄清后的结构化需求
|   |   +-- index.md               <- 本 PRD 总纲
|   |   +-- FR-XX-<topic>.md
|   |   +-- NFR-XX-<topic>.md
|   +-- source/                     <- 原始文件来源记录（.gitignore 排除）
|   |   +-- manifest.md
|   |   +-- original-prd.md
|   +-- _snapshots/                    <- 重解析前的原始文档留存（与 source/ 同忽略策略）
|       +-- <YYYYMMDD-HHMMSS>/source/
+-- synthesis/                      <- 跨 PRD 综合产物
|   +-- terminology.md
|   +-- shared-constraints.md
|   +-- conflict-resolution.md
+-- _archived/                      <- 归档目录（保留完整结构）
    +-- <prd_id>/
```

### legacy 单 PRD 模式（向后兼容）

```
docs/prd/
+-- chunks/
+-- requirements/
+-- source/
```

**模板**：
- 全局索引模板：`templates/global-index-template.md`
- 总纲模板：`templates/requirements-index-template.md`
- 需求分文件模板：`templates/requirements-item-template.md`

## 归档流程

```text
/ms-prd archive <prd_id>
    |
    v
1. 读取全局 index，确认 prd_id 存在且状态为 active 或 superseded
   ⛔ 已归档 → 报错退出
    |
    v
2. AskUserQuestion 确认归档意图
    |
    v
3. 移动 docs/prd/<prd_id>/ → docs/prd/_archived/<prd_id>/
4. 更新全局 index：状态→archived，填写归档日期
5. 更新 per-PRD index：prd_status→archived
```

**归档后操作边界**：archived PRD 禁止 `--revise`，允许只读 `--from-prd` 和 `status` 查看。

## 权威模型

| 字段 | Source of Truth | 说明 |
|------|----------------|------|
| PRD 清单/生命周期状态/编号注册表 | 全局 index | 注册入口，parser 分配前查询 |
| supersedes / superseded_by | 全局 index | 迭代关系双向维护 |
| 需求清单 / DevDocs mapping / 假设挑战 | per-PRD index | 本 PRD 范围内 |

**写入顺序**：先写全局 index → 再更新 per-PRD index。全局写入成功即生效。

### supersedes 链不变式

- 禁止自指和环
- 每个 PRD 最多一个 `supersedes` 目标
- 写入时同步回填旧 PRD 的 `superseded_by`
- 仅 `active` 状态的 PRD 允许被 supersede

## 约束

### 编排约束

- [ ] **pipeline 仅负责路由、衔接和跨块合成，不复制原子 skill 的探索/解析逻辑**
- [ ] **brainstorm 和 prd-parser 阶段必须委托给对应 skill 执行**
- [ ] **阶段间传递的信息仅限：YAML 摘要、文件路径、新增编号列表**
- [ ] 用户可在任意阶段退出 pipeline

### 自动检测约束

- [ ] **优先使用输入长度 + 结构特征自动判断，无法判断时才提问**
- [ ] **AskUserQuestion 最多 1 次确认路由，不开放式提问**
- [ ] 用户明确指定模式时直接路由，不二次确认

### 子 Agent 约束

- [ ] **调用其他技能时必须通过 Task tool 启动子 Agent**
- [ ] **阶段间只传递 YAML 摘要 + 文件路径**
- [ ] **子 Agent 失败时展示阻塞项询问用户，不自行排障**
- [ ] **每个子 Agent 自行读取前置文档，编排层不传递全文**

### 成熟度约束

- [ ] **成熟度标记为建议性，不硬阻塞流程**
- [ ] **ready 门槛未满足时标注缺失项，由用户决定是否继续**
- [ ] **maturity=idea 时不主动推荐 DevDocs 衔接**

### 编号约束

- [ ] **FR-XX/NFR-XX 为 product 阶段唯一 ID，不分配 F/US/AC 编号**
- [ ] **编号权属于 DevDocs，ms-prd 不越界**

## Skill 协作

| 场景 | 编排的 Skill 链 |
|------|----------------|
| 头脑风暴 | 查全局注册表取编号起始 → ms-prd-brainstorm → index 生成 → ready 检查 |
| PRD 解析 | 查全局注册表取编号起始 → ms-prd-parser → 逐块 ms-prd-brainstorm → 跨块合成 → index 生成 → ready 检查 |
| PRD 更新 | ms-prd-parser（重拆）→ 指纹对比 → 仅 outdated 块 brainstorm → index 更新 |
| PRD 管理 | list（列出所有 PRD）/ status（查看详情）/ archive（归档） |
| DevDocs 衔接 | ready 时推荐 ms-requirements --from-prd |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-prd
status: success | partial | failed
summary:
  headline: "需求处理完成，成熟度 ready，含 6 个功能 + 2 个非功能"
  details:
    prd_id: 20260330-用户认证
    prd_status: active
    index_path: docs/prd/20260330-用户认证/requirements/index.md
    mode: brainstorm | prd-parse
    maturity: idea | draft | ready
    functional_count: 6
    nonfunctional_count: 2
    clarified_count: 8
    open_questions: 2
    ready_checks_passed: 6
    ready_checks_total: 6
blockers: []
output_files:
  - docs/prd/20260330-用户认证/requirements/index.md
  - docs/prd/20260330-用户认证/requirements/FR-09-登录.md
new_ids:
  requirements: [FR-09~FR-14, NFR-04~NFR-05]
next_recommended:
  skill: ms-requirements
  args: "--from-prd docs/prd/20260330-用户认证/requirements/index.md"
```

**status 值域**：
- `success`：所有块处理完成，index.md 已生成
- `partial`：部分块处理完成（用户中断或部分块失败）
- `failed`：关键步骤失败（如 PRD 无法解析）

## 下一步

pipeline 完成后，根据成熟度给出建议：

- `ready` → 推荐 `/ms-requirements --from-prd <实际 index.md 路径>`
- `draft` → 提示开放问题清单，建议补充后再衔接，或用户选择直接进入 DevDocs
- `idea` → 建议继续 `/ms-prd brainstorm` 深化探索
