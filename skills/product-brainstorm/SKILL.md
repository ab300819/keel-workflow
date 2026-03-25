---
name: product-brainstorm
description: Brainstorm and clarify product requirements through structured exploration. Two modes - full brainstorm (idea to requirements via 5W1H/journey/MoSCoW) and chunk-clarify (adaptive depth clarification of PRD segments). Outputs structured requirement files (FR-XX/NFR-XX). Triggers on "brainstorm", "头脑风暴", "需求探索", "澄清需求", "clarify requirements". NOT for PRD parsing (use product-prd-parser) or pipeline orchestration (use product-pipeline).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
metadata:
  patterns: [inversion, generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 需求探索与澄清

将模糊想法或 PRD 分段转化为结构化需求文件，通过渐进式探索确保需求完整性和可追溯性。

## 角色

- 身份：需求探索顾问
- 关注：需求完整性、场景覆盖、用户价值、分类准确性
- 回避：技术实现方案、架构设计、编码细节
- 判断倾向：发散时宁可多探不可遗漏，收敛时严格 MoSCoW 分级

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户提供一句话模糊想法，需要头脑风暴
- 用户想要探索和澄清需求
- 来自 `product-pipeline` 的块澄清委托
- 来自 `product-prd-parser` 的分段需要深入探索

## 运行模式

```bash
/product-brainstorm                → 完整头脑风暴模式（一句话想法）
/product-brainstorm --chunk <path> → 块澄清模式（PRD 分段逐块澄清）
```

| 模式 | 触发条件 | 说明 |
|------|----------|------|
| **完整模式** | 用户直接输入想法或需求描述 | 5W1H → 用户角色 → 旅程 → MoSCoW 全流程 |
| **块澄清模式** | 指定 chunk 文件路径 | 自适应深度，快速确认或深入探索 |

## 工作流程

### 完整模式（一句话想法 → 结构化需求）

```text
1. 记录原始想法
   │
   ├── 记录用户原话
   └── 标记来源和日期
   │
   ▼
2. 5W1H 快速定位
   │
   ├── What — 做什么产品/功能？
   ├── Who — 目标用户是谁？
   ├── Why — 解决什么问题？带来什么价值？
   ├── When — 使用时机和频率？
   ├── Where — 使用场景和环境？
   └── How — 核心交互方式？
   │
   ├── 使用 AskUserQuestion 逐项澄清不明确的维度
   └── 已明确的维度直接记录，不重复追问
   │
   ▼
3. 用户角色探索
   │
   ├── 识别 2-4 个核心角色
   ├── 每个角色的核心任务和痛点
   └── 使用 AskUserQuestion 确认角色划分
   │
   ▼
4. 用户旅程草绘
   │
   ├── 每个核心角色 3-5 步关键旅程
   ├── 标注关键触点和情绪曲线
   └── 识别旅程中的功能需求
   │
   ▼
5. 功能发散 → 收敛
   │
   ├── 发散：列出所有可能功能点
   ├── 收敛前审视：当前功能列表是否在解决正确的问题？（轻提示，正式记录由 product-pipeline 写入 index.md）
   ├── 收敛：MoSCoW 分类
   │   ├── Must have — 核心功能，缺失则产品不成立
   │   ├── Should have — 重要功能，首版应包含
   │   ├── Could have — 锦上添花，资源允许时做
   │   └── Won't have — 明确排除，记录但不做
   └── 使用 AskUserQuestion 确认优先级
   │
   ▼
6. 分类与输出
   │
   ├── 按 FR（功能需求）/ NFR（非功能需求）分类
   ├── 为每项分配 FR-XX 或 NFR-XX 编号
   ├── 生成需求文件到 docs/product/requirements/
   └── 使用 AskUserQuestion 最终确认
```

详细技法指南参见 [references/brainstorm-techniques.md](references/brainstorm-techniques.md)

### 块澄清模式（PRD 分段 → 结构化需求）

```text
1. 读取 chunk 文件
   │
   ├── 解析 YAML 头（id, title, type, source_anchor）
   └── 读取原文内容
   │
   ▼
2. 自适应深度评估
   │
   ├── 执行 6 项深度 rubric 检查
   ├── >= 4 项通过 → 快速确认路径
   └── < 4 项通过 → 深入探索路径
   │
   ▼
3a. 快速确认路径
   │
   ├── 直接提取结构化需求
   ├── 执行终判分类（复核 FR/NFR）
   └── 输出需求文件
   │
   ▼
3b. 深入探索路径
   │
   ├── 针对未通过项使用 AskUserQuestion 澄清
   ├── 最多 3 轮追问
   ├── 3 轮后强制输出（未解决项标记为开放问题）
   ├── 执行终判分类
   └── 输出需求文件
```

## 自适应深度 Rubric

对每个 chunk 执行以下 6 项检查，判断澄清深度：

| # | 检查项 | 通过标准 | 未通过时追问方向 |
|---|--------|----------|-----------------|
| 1 | 用户角色是否明确 | 能识别至少 1 个具体角色 | "谁会使用这个功能？" |
| 2 | 触发场景是否具体 | 有明确的使用时机或前置条件 | "什么情况下会触发？" |
| 3 | 功能边界是否清晰 | 做什么和不做什么可区分 | "这个功能的边界在哪？" |
| 4 | 成功结果是否可描述 | 能描述完成后的状态或效果 | "做完后用户看到什么？" |
| 5 | 约束条件是否已知 | 性能/安全/兼容等限制已提及 | "有什么技术或业务限制？" |
| 6 | 验收意图是否可提取 | 能推导出至少 1 条验收条件 | "怎么判断这个功能做好了？" |

**评估规则**：
- >= 4 项通过：走快速确认路径，直接输出结构化需求
- < 4 项通过：走深入探索路径，针对未通过项逐一追问
- 每轮追问后重新评估，新通过项不再追问
- **最多 3 轮追问**后强制输出，将未解决项记录为开放问题

## 终判分类

brainstorm 对每个需求项执行分类终判，复核 parser 的 FR/NFR 初判。

### 分类标准

| 类型 | 判定依据 |
|------|---------|
| FR（功能需求） | 涉及用户操作、交互流程、业务逻辑、数据处理 |
| NFR（非功能需求） | 涉及性能指标、安全要求、可用性、兼容性、可维护性 |

### 终判规则

- chunk 文件名**不改**（保持原始拆分记录）
- 如终判与初判不同，chunk 文件 YAML 头增加 `reclassified_to: NFR`（或 `FR`）
- requirement 文件按终判类型命名（如 chunk 是 FR-01 但终判为 NFR → requirement 文件为 NFR-XX）
- index.md 需求清单中标注 `来源: FR-01 (复判为 NFR)`
- 内部稳定 ID 以 requirement 文件为准，chunk ID 仅作溯源用

### 终判流程

```text
1. 阅读 chunk 原文内容
2. 根据分类标准独立判断 FR/NFR
3. 对比 parser 初判
   ├── 一致 → 直接采用
   └── 不一致 → 记录理由，按终判结果命名 requirement 文件
4. 在 chunk YAML 头追加 reclassified_to 字段（仅不一致时）
```

## 编号规范

| 类型 | 前缀 | 格式 | 示例 |
|------|------|------|------|
| 功能需求 | FR | FR-XX | FR-01, FR-02 |
| 非功能需求 | NFR | NFR-XX | NFR-01, NFR-02 |

**编号规则**：
- FR-XX / NFR-XX 为产品阶段唯一标识（不使用 D-XXX）
- 编号从 01 开始，两位数字，顺序递增
- 编号一旦分配不可复用
- 完整模式：brainstorm 过程中分配编号
- 块澄清模式：沿用 chunk 编号（终判调整类型前缀时重新分配）

## 输出文件

**输出目录**：`docs/product/requirements/`

每个需求项生成一个独立文件：

```markdown
---
id: FR-01
title: 用户认证
type: FR
source_chunk: FR-01                      # chunk ID，仅块澄清模式
moscow: Must
maturity: draft
status: clarified
open_questions: 1
---

# FR-01: 用户认证

## 来源追溯

- 原始 chunk: `docs/product/chunks/FR-01-用户认证.md`
- 初判分类: FR
- 终判分类: FR

## 用户角色与场景

| 角色 | 使用场景 | 核心需求 |
|------|---------|---------|
| 普通用户 | 首次注册/登录 | 快速安全地进入系统 |

## 功能描述

（结构化的功能描述，澄清后的成品）

## MoSCoW 优先级

**Must have** — 核心功能，无此功能产品不成立。

## 验收意图

- [ ] 用户可通过邮箱注册新账号
- [ ] 用户可通过密码登录系统
- [ ] 登录失败时显示明确错误提示

## 开放问题

1. 是否需要支持第三方登录（微信/Google）？
```

## 上下文管理

### 分批原则

完整模式按探索阶段分批（5W1H → 角色 → 旅程 → MoSCoW），每阶段完成后进入下一阶段。

### 质量锚点

- 完整模式：首个 FR 的描述深度作为后续 FR 的**质量锚点**
- 块澄清模式：首个 chunk 的澄清深度作为后续 chunk 的质量基准
- 后续输出的详细程度不低于锚点

### 忠于原文原则

- 块澄清模式中，不篡改原始 PRD 内容
- 结构化需求基于原文提取和补充，不替代原文
- 开放问题如实记录，不自行假设答案

## 约束

### 阶段边界约束（最高优先级）
- [ ] **禁止继续：不得产出实现代码、架构设计或技术方案**（恢复方式：使用对应 DevDocs skill 执行后续阶段）
- [ ] Write 工具仅用于写入 `docs/product/requirements/` 和 `docs/product/chunks/` 下的 Markdown 文档
- [ ] 对 chunks/ 文件：仅修改 YAML 头（添加 `reclassified_to` 字段），**不得改动原文内容**
- [ ] 对 requirements/ 文件：写入完整的结构化需求文档

### 探索约束
- [ ] 完整模式必须完成 5W1H → 角色 → 旅程 → MoSCoW 全流程
- [ ] 每阶段至少使用 1 次 AskUserQuestion 与用户确认
- [ ] 不得添加用户未提及且未确认的需求
- [ ] 发散阶段鼓励多探索，收敛阶段严格 MoSCoW

### 澄清约束
- [ ] 块澄清模式最多 3 轮追问，超出后强制输出
- [ ] 未解决的疑问标记为开放问题，不自行填补
- [ ] 自适应深度 rubric 6 项检查必须逐项执行并记录结果

### 分类约束
- [ ] 终判分类必须给出判定理由
- [ ] chunk 文件名不可更改
- [ ] requirement 文件按终判类型命名
- [ ] 分类不一致时必须在 chunk YAML 头追加 reclassified_to

### 编号约束
- [ ] FR-XX / NFR-XX 为唯一产品阶段标识
- [ ] 不使用 D-XXX 编号
- [ ] 编号一旦分配不可复用

### Generator 自检（输出前自动执行）

在输出需求文件前自动验证：

- [ ] 每个 FR/NFR 有标题和功能描述
- [ ] 每个 FR/NFR 有至少 1 条验收意图
- [ ] MoSCoW 分级已标注
- [ ] 开放问题已列出（如有）

自检不通过项自动修复后再输出，不增加用户交互步骤。

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| PRD 拆分后逐块澄清 | `product-prd-parser` | 上游：parser 拆分后由 pipeline 委派 |
| 编排调度 | `product-pipeline` | 上游：pipeline 调用本 skill |
| 需求进入 DevDocs | `devdocs-requirements` | 下游：ready 后通过 `--from-product` 消费 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: product-brainstorm
status: success | partial | failed
summary:
  headline: "识别 5 个功能领域，2 个非功能需求"
  details:
    mode: full | chunk-clarify
    chunk_id: FR-01               # 仅 chunk-clarify 模式
    functional_count: 5
    nonfunctional_count: 2
    open_questions: 1
    rubric_score: 5               # 仅 chunk-clarify 模式，6 项中通过数
    clarify_rounds: 2             # 仅 chunk-clarify 模式，实际追问轮数
    reclassified: false           # 是否发生分类调整
blockers: []
output_files:
  - docs/product/requirements/FR-01-用户认证.md
new_ids:
  requirements: [FR-01~FR-03, NFR-01~NFR-02]
next_recommended:
  skill: product-pipeline
```

**status 值域**：
- `success`：所有需求项已澄清并输出
- `partial`：部分需求项有开放问题，已标记但已输出
- `failed`：无法完成澄清（如用户中断、关键信息缺失无法继续）

## 下一步

| 完成模式 | 建议下一步 |
|----------|------------|
| 完整模式 | 返回 `product-pipeline` 生成 index.md |
| 块澄清模式 | 返回 `product-pipeline` 继续下一块或生成 index.md |
| 整体 ready | `devdocs-requirements --from-product` 进入 DevDocs |
