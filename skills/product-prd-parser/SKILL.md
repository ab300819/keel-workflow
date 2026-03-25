---
name: product-prd-parser
description: Parse and split large PRD documents (md/PDF/screenshots) into structured chunks with FR/NFR classification, fingerprint-based change tracking, and full text preservation. Use when users provide large product requirement documents that need segmentation before clarification. Triggers on "PRD", "产品需求文档", "大文档拆分", "解析PRD", "parse prd". NOT for requirement clarification (use product-brainstorm) or pipeline orchestration (use product-pipeline).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, WebFetch
metadata:
  patterns: [generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# PRD 文档解析器

将大型产品需求文档拆分为结构化的独立块文件，保留完整转换文本，为后续逐块澄清做预处理。

## 角色

- 身份：文档分析师
- 关注：忠于原文、结构清晰、不遗漏
- 回避：需求解读、方案设计、内容删减改写
- 判断倾向：拆分粒度宁细不粗，分类存疑时标注待复判

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户提供大型 PRD 文档（md/PDF/截图）
- 来自 `/product-pipeline` 的 PRD 解析委托
- 用户需要对已有 PRD 进行变更检测和增量更新

## 输入支持

| 格式 | 支持方式 | 说明 |
|------|----------|------|
| Markdown | **原生支持** | Read 直接读取 |
| PDF | **原生支持** | Read 分页读取，每次 <=20 页 |
| 截图/图片 | **原生支持** | Read 图片识别，OCR 质量依赖图片清晰度 |
| docx | **需用户转换** | 工具限制，无法直接读取 docx 二进制；请用户先转为 md 或粘贴文本 |
| MCP 来源 | **按工具能力** | 依赖具体 MCP 工具获取内容后处理 |

## 工作流程

### 首次解析

```text
1. 接收输入
   |
   +-- 识别文件格式（md/PDF/截图/文本）
   +-- 若为 docx → AskUserQuestion 请求用户转换
   +-- 若为 PDF → 分页读取（每次 <=20 页），拼接全文
   +-- 若为截图 → Read 图片识别，提取文字
   |
   v
2. 记录原始文件来源
   |
   +-- 文本文件（md）→ 复制到 docs/product/source/
   +-- 二进制文件（PDF/图片/docx）→ 记录原始路径到 source/manifest.md，提示用户手动复制
   +-- 计算 document_fingerprint（对转换后的全文计算 sha256）
   |
   v
3. 识别文档结构
   |
   +-- 有目录/标题层级 → 提取 TOC 作为拆分依据
   +-- 无明确结构 → 按逻辑主题识别拆分点
   |
   v
4. 执行拆分
   |
   +-- 按章节/主题切分为独立块
   +-- 检查块大小，过大细分，过小合并
   +-- 为每块分配 chunk_key（稳定锚点）
   |
   v
5. 初判分类
   |
   +-- 每块判定 FR（功能）或 NFR（非功能）
   +-- 分配编号：FR-XX / NFR-XX
   |
   v
6. 输出 chunk 文件
   |
   +-- 写入 docs/product/chunks/，含 YAML 头 + 完整原文
   +-- 每个文件包含双指纹 + parser_version + chunk_key
   |
   v
7. 用户确认拆分结果
   |
   +-- AskUserQuestion 展示拆分摘要
   +-- 用户可要求调整拆分粒度或分类
   |
   v
8. 返回 yaml-summary-v1
```

### 变更检测（PRD 更新场景）

```text
1. 重新读取 + 转换源文档
   |
   v
2. 计算新的 document_fingerprint
   |
   +-- 与现有 chunks 中的 document_fingerprint 对比
   +-- 相同 → 报告"文档无变化"，结束
   +-- 不同 → 继续
   |
   v
3. 重新拆分，为每块生成 chunk_key + source_fingerprint
   |
   v
4. 通过 chunk_key 匹配新旧块（容忍章节重排）
   |
   +-- chunk_key 匹配成功 → 对比 source_fingerprint
   |   +-- 相同 → 保持原 status（clarified 不变）
   |   +-- 不同 → 标记 status: outdated
   +-- 新增章节（无匹配 chunk_key）→ 新建文件，status: pending
   +-- 删除章节（旧 chunk_key 无匹配）→ 标记 status: removed
   |
   v
5. 更新 chunk 文件
   |
   +-- outdated：更新内容 + source_fingerprint，保留原编号
   +-- pending：写入新文件
   +-- removed：在 YAML 头标记 removed
   |
   v
6. 返回变更摘要
```

## 拆分策略

### 拆分依据

- **有目录/标题结构**：按章节标题拆分，每个一级或二级标题对应一个块
- **无明确结构**：识别逻辑主题边界（段落主题切换、列表分组、空行分隔等）

### 块大小控制

| 指标 | 值 | 处理 |
|------|-----|------|
| 目标大小 | 100-200 行/块 | 理想范围 |
| 最小阈值 | 30 行 | 低于此值与相邻块合并 |
| 最大阈值 | 300 行 | 超过此值按子标题或逻辑段细分 |

### 合并/细分规则

- 合并时优先选择**主题相近**的相邻块
- 细分时优先按**子标题**切分；无子标题则按**段落逻辑**切分
- 合并后的块保留所有原始内容，不删减

## 初判分类

### 分类标准

| 类型 | 编号前缀 | 判定依据 |
|------|----------|----------|
| 功能需求 (FR) | FR-XX | 含用户操作、交互流程、业务逻辑、数据处理 |
| 非功能需求 (NFR) | NFR-XX | 含性能指标、安全要求、可用性、兼容性、合规性 |

### 分类规则

- 同一块中 FR 和 NFR 内容混合时，按**主要内容**分类，在 YAML 头 `mixed_content` 字段标注
- 分类存疑时标注 `classification_confidence: low`，由 brainstorm 终判
- 编号从 01 起始，FR 和 NFR 独立计数

## 输出格式

### Chunk 文件

文件路径：`docs/product/chunks/<编号>-<主题>.md`

```markdown
---
id: FR-01
title: 用户认证
type: FR
source_file: /absolute/path/to/original-prd.pdf  # 原始文件路径（二进制文件为原始位置，文本文件为 source/ 副本）
source_anchor: "2.1 用户认证"
source_pages: "5-8"
source_fingerprint: "sha256:abc123..."
document_fingerprint: "sha256:xyz789..."
parser_version: "1.0"
chunk_key: "2.1-用户认证"
status: pending
---

（以下为原文完整转换文本，忠于原始 PRD，不改写、不删减）

2.1 用户认证

系统需要支持多种认证方式...
```

### YAML 头字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | FR-XX 或 NFR-XX |
| `title` | 是 | 块主题名称 |
| `type` | 是 | FR 或 NFR |
| `source_file` | 是 | 原始文件路径（文本文件指向 source/ 副本，二进制文件指向原始位置，详见 source/manifest.md） |
| `source_anchor` | 是 | 原文章节标题或位置描述 |
| `source_pages` | 否 | PDF 页码或行范围 |
| `source_fingerprint` | 是 | 本块内容的 sha256 哈希 |
| `document_fingerprint` | 是 | 整个原始文档的 sha256 哈希 |
| `parser_version` | 是 | 拆分器版本号，版本变化时触发全量重拆 |
| `chunk_key` | 是 | 稳定锚点（标题路径），章节重排时用于匹配 |
| `status` | 是 | pending / clarified / outdated / removed |
| `mixed_content` | 否 | 块中含混合 FR/NFR 内容时标注 |
| `classification_confidence` | 否 | 分类信心不足时标注 low |
| `reclassified_to` | 否 | brainstorm 终判调整分类时由 brainstorm 填入 |

### 原始文件保存

- 路径：`docs/product/source/`
- 此目录在 `.gitignore` 中排除，不提交仓库
- 避免二进制膨胀和敏感信息入库

## 变更追踪机制

### 双级指纹体系

```
document_fingerprint（文档级）
  → 整文档 sha256，快速判断是否有任何变更

source_fingerprint（块级）
  → 单块内容 sha256，精确定位哪些块发生变更

chunk_key（锚点匹配）
  → 标题路径（如 "2.1-用户认证"），容忍章节重排

parser_version（版本控制）
  → 拆分器版本号，版本变化时全量重新拆分
```

### Status 流转

```
pending ──(brainstorm 澄清)──> clarified
clarified ──(PRD 更新，内容变更)──> outdated
clarified ──(PRD 更新，章节删除)──> removed
outdated ──(重新 brainstorm)──> clarified
pending ──(PRD 更新，章节删除)──> removed
```

### 变更处理策略

| 场景 | 检测方式 | 处理 |
|------|----------|------|
| 文档无变化 | document_fingerprint 相同 | 跳过，报告无变更 |
| 块内容不变 | chunk_key 匹配 + source_fingerprint 相同 | 保持原 status |
| 块内容变更 | chunk_key 匹配 + source_fingerprint 不同 | 标记 outdated |
| 新增章节 | chunk_key 无匹配 | 新建文件，status: pending |
| 删除章节 | 旧 chunk_key 无匹配 | 标记 removed |
| 章节重排 | chunk_key 匹配但顺序变化 | **保持原 chunk ID 不变**（通过 chunk_key 锚点匹配，不重新编号） |

## 指纹计算规则

- **document_fingerprint**：对原始文件（或转换后全文）计算 sha256
- **source_fingerprint**：对块的正文内容（不含 YAML 头）计算 sha256
- 计算前统一处理：去除首尾空白、规范化换行符为 `\n`
- 哈希格式：`sha256:<hex 前 16 位>`（截断以提高可读性，冲突概率可忽略）

## 约束

### 阶段边界约束（最高优先级）

- [ ] **禁止继续：不得解读、改写、删减原文内容**（恢复方式：原文完整保留到 chunk，需求解读由 product-brainstorm 负责）
- [ ] Write 工具仅用于写入 `docs/product/chunks/` 和 `docs/product/source/` 下的文件
- [ ] 不分配 F/US/AC 编号（编号权属于 DevDocs 阶段）

### 忠实性约束

- [ ] chunk 正文必须为原文完整转换文本，逐字保留
- [ ] 不得添加分析注释、摘要或解读到正文区域
- [ ] YAML 头的 title 和 source_anchor 从原文标题提取，不自行创造

### 拆分约束

- [ ] 每个块必须有唯一的 chunk_key
- [ ] 块大小控制在 30-300 行范围内
- [ ] FR 和 NFR 独立编号，从 01 起始
- [ ] 拆分不得丢失原文任何段落

### 变更追踪约束

- [ ] 每个 chunk 文件必须包含全部四个指纹/版本字段
- [ ] 变更检测必须先对比 document_fingerprint 再逐块对比
- [ ] outdated 块保留原编号，不重新分配
- [ ] removed 块保留文件但标记状态，不物理删除

### 确认约束

- [ ] 拆分完成后必须展示摘要并等待用户确认
- [ ] 摘要须包含：块数量、FR/NFR 分布、各块标题和行数
- [ ] 用户要求调整时，修改后重新确认

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 编排调度 | `/product-pipeline` | 被调用：pipeline 委托 PRD 解析 |
| 块澄清 | `/product-brainstorm` | 后续：chunks 传入 brainstorm 逐块澄清 |
| 分类终判 | `/product-brainstorm` | 后续：brainstorm 可复判 FR/NFR 分类 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: product-prd-parser
status: success | partial | failed
summary:
  headline: "PRD 拆分为 6 个功能块 + 2 个非功能块"
  details:
    functional_count: 6
    nonfunctional_count: 2
    total_lines: 1200
    avg_chunk_lines: 150
    has_toc: true
    outdated_count: 0
blockers: []
output_files:
  - docs/product/chunks/FR-01-用户认证.md
  - docs/product/chunks/NFR-01-性能要求.md
  - docs/product/source/manifest.md
new_ids:
  chunks: [FR-01~FR-06, NFR-01~NFR-02]
next_recommended:
  skill: product-pipeline
```

## 下一步

| 完成场景 | 建议下一步 |
|----------|------------|
| 首次解析完成 | 返回 `/product-pipeline`，由 pipeline 逐块调用 brainstorm |
| 变更检测完成 | 返回 `/product-pipeline`，仅对 outdated/pending 块调用 brainstorm |
| 独立运行 | `/product-brainstorm` 逐块澄清 |

> **提示**：本 skill 仅负责拆分和保留原文，需求解读和澄清由 `/product-brainstorm` 负责。
