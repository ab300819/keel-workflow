---
name: product-pipeline
description: Product requirements orchestrator. Routes ideas and PRDs through brainstorm and parsing workflows, producing structured requirements for DevDocs consumption. Use for fuzzy ideas, large PRD documents, or when users say "产品需求", "PRD", "需求探索", "头脑风暴", "brainstorm", "产品流程". NOT for already-structured DevDocs requirements or direct skill invocation.
metadata:
  patterns: [pipeline]
  interaction: multi-turn
  handoff: yaml-summary-v1
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Task
user-invocable: true
---

# 产品需求编排器

编排产品需求处理流程，自动路由到 brainstorm 或 PRD 解析，产出结构化需求包供 DevDocs 消费。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 定位

```
用户 → /product-pipeline → 自动检测输入类型 → 路由到对应流程
                         ↓
              product-brainstorm（想法澄清）
              product-prd-parser（文档拆分）
                         ↓
              结构化需求包 → DevDocs 衔接
```

**核心价值**：弥补 DevDocs 对模糊想法和大型 PRD 的处理不足，提供需求探索到结构化输出的完整路径。

## 运行模式

```bash
/product-pipeline              → 自动检测输入类型
/product-pipeline brainstorm   → 强制头脑风暴模式
/product-pipeline prd          → 强制 PRD 解析模式
```

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

## 编排流程

### 场景 1：头脑风暴（idea → requirements）

```text
用户输入（一句话/简短想法）
    |
    v
Task: product-brainstorm（完整模式）
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
Step 1: Task: product-prd-parser
    |  ← 转换 + 拆分 → chunks/FR-XX.md + NFR-XX.md
    v
Step 2: 逐块 Task: product-brainstorm --chunk <chunk文件路径>
    |  ← 自适应深度：成熟块快速确认，模糊块深入探索
    |  ← 终判分类：复核 parser 的 FR/NFR 初判
    |  ← 入参示例：/product-brainstorm --chunk docs/product/chunks/FR-01-用户认证.md
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
Step 1: Task: product-prd-parser（重新拆分）
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
Step 3: 仅对 outdated/pending 块调用 product-brainstorm
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
/devdocs-requirements --from-product docs/product/requirements/index.md
```

maturity 为 draft 时也可衔接，但需提示用户开放问题可能影响后续质量。

### 衔接原则

- 需求文件**不分配 F/US/AC 编号**，编号权属于 DevDocs
- FR-XX/NFR-XX 为 product 阶段唯一标识，进入 DevDocs 后映射为 F-XXX
- 需求文件存放于 `docs/product/`，不写入 `docs/devdocs/`
- 以小文档形式传入 DevDocs：index.md 提供全局视图，各 FR-XX 对应独立功能领域

## 编排规范（子 Agent 调度）

### 调度原则

pipeline 调用其他技能时，**必须通过 Task tool 启动子 Agent**：

```text
product-pipeline（编排层）
    |
    +-- Task: product-prd-parser → YAML 摘要
    +-- Task: product-brainstorm（逐块）→ YAML 摘要
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

每个子 Agent 自行读取所需的前置文件（从 `docs/product/` 文件系统），不依赖编排 Agent 传递全文。

## 文件产出路径

```
docs/product/
+-- chunks/                     <- PRD 原文完整文本化副本
|   +-- FR-01-<topic>.md
|   +-- NFR-01-<topic>.md
+-- requirements/               <- brainstorm 澄清后的结构化需求
|   +-- index.md               <- 总纲
|   +-- FR-01-<topic>.md
|   +-- NFR-01-<topic>.md
+-- source/                     <- 原始文件来源记录（.gitignore 排除）
    +-- manifest.md              <- 记录原始文件路径、哈希、类型
    +-- original-prd.md          <- 文本文件自动复制；二进制文件需用户手动复制
```

**模板**：
- 总纲模板：`templates/requirements-index-template.md`
- 需求分文件模板：`templates/requirements-item-template.md`

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
- [ ] **编号权属于 DevDocs，product-pipeline 不越界**

## Skill 协作

| 场景 | 编排的 Skill 链 |
|------|----------------|
| 头脑风暴 | product-brainstorm → index 生成 → ready 检查 |
| PRD 解析 | product-prd-parser → 逐块 product-brainstorm → 跨块合成 → index 生成 → ready 检查 |
| PRD 更新 | product-prd-parser（重拆）→ 指纹对比 → 仅 outdated 块 brainstorm → index 更新 |
| DevDocs 衔接 | ready 时推荐 devdocs-requirements --from-product |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: product-pipeline
status: success | partial | failed
summary:
  headline: "需求处理完成，成熟度 ready，含 6 个功能 + 2 个非功能"
  details:
    mode: brainstorm | prd-parse
    maturity: idea | draft | ready
    functional_count: 6
    nonfunctional_count: 2
    clarified_count: 8
    open_questions: 2
    ready_checks_passed: 5
    ready_checks_total: 5
blockers: []
output_files:
  - docs/product/requirements/index.md
  - docs/product/requirements/FR-01-用户认证.md
new_ids:
  requirements: [FR-01~FR-06, NFR-01~NFR-02]
next_recommended:
  skill: devdocs-requirements
  args: "--from-product docs/product/requirements/index.md"
```

**status 值域**：
- `success`：所有块处理完成，index.md 已生成
- `partial`：部分块处理完成（用户中断或部分块失败）
- `failed`：关键步骤失败（如 PRD 无法解析）

## 下一步

pipeline 完成后，根据成熟度给出建议：

- `ready` → 推荐 `/devdocs-requirements --from-product docs/product/requirements/index.md`
- `draft` → 提示开放问题清单，建议补充后再衔接，或用户选择直接进入 DevDocs
- `idea` → 建议继续 `/product-pipeline brainstorm` 深化探索
