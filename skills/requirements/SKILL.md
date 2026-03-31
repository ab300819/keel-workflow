---
name: ms-requirements
description: 将已明确需求编码为 F/US/AC 体系。Supports initial, incremental, context (--context), and --from-prd modes. 模糊需求请先用 /ms-prd 探索。Triggers on "requirements", "feature request", "user story", "需求", "功能点", "验收标准", "项目背景", "补充信息". NOT for fuzzy ideas (use ms-prd), system/technical design (use ms-system-design), or test case design (use ms-test-cases).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, WebFetch
metadata:
  patterns: [inversion, generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 需求扩写

将用户简短需求扩展为结构化的需求文档，建立功能点、用户故事、验收标准的关联体系。

## 角色

- 身份：产品分析师
- 关注：用户价值、场景完备性、验收可测性
- 回避：技术实现、架构决策、性能方案
- 判断倾向：宁可多问不可假设，拒绝模糊需求直接通过

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

- 用户提供功能需求或想法
- 用户要求创建/编写 PRD
- 用户想要澄清或记录需求
- 来自 `/ms-feature` 的增量需求委托
- 用户需要补充项目背景信息（尤其是 retrofit 后）
- 用户提供参考资料、领域知识、技术约束

## 运行模式

```bash
/ms-requirements              → 自动检测模式
/ms-requirements --incremental → 强制增量模式（追加功能点）
/ms-requirements --context     → 背景信息模式（追加/更新背景）
/ms-requirements --fast        → 跳过方案确认，直接生成，仅最终汇总确认
/ms-requirements --from-prd <index路径> → 消费产品需求包
/ms-requirements --update-design              → 设计资产写入/更新（由 pipeline design 委托）
/ms-requirements --update-design --target prd-index → 写入 PRD index（依次尝试 docs/prd/requirements/index.md → docs/product/requirements/index.md）
```

| 模式 | 触发条件 | 说明 |
|------|----------|------|
| **初始模式** | 无 `01-requirements.md` | 从零创建需求文档 |
| **增量模式** | 已有 `01-requirements.md` | 扫描编号 + 追加功能点/用户故事/验收标准 |
| **背景信息模式** | `--context` 或用户要补充背景 | 追加/更新"背景与目标"章节 |
| **产品导入模式** | `--from-prd` + index 路径 | 消费 ms-prd 输出的结构化需求包 |
| **设计资产更新** | `--update-design` 参数 | 由 pipeline design 委托，写入/更新 design_context |

### `--from-prd` 模式

消费 `/ms-prd` 产出的结构化需求包，转化为正式 F/US/AC。

**模式定位**：初始模式的变体。产品流程通常在 DevDocs 之前运行，此时 `01-requirements.md` 尚不存在。如果已存在：
- 检查映射表中 `mapping_status: outdated` 的条目 → **原地更新**对应 F/US/AC（不创建新编号）（mapping_status 规范见 `skills/prd/references/prd-mapping-status.md`）
- 新增的 FR-XX（无映射记录）→ 按增量模式追加新 F/US/AC

**与其他模式的关系**：
- 替代初始模式的"收集原始需求"步骤（需求已由 ms-prd 准备好）
- **跳过方案确认环节**（Inversion gate），因为用户已在 ms-prd 中确认过
- 保留最终文档确认（仅确认 F/US/AC 生成结果）

**消费流程**：
1. 读取用户指定的 `<index路径>`（如未指定，依次尝试 `docs/prd/requirements/index.md` → `docs/product/requirements/index.md`）
   - 记录实际读取的路径（`source_index_path`），后续回写映射时使用同一路径
   - 读取 index.md 中 `## 设计资产` 的 design_context → 写入 01-requirements.md `## 设计资产`
2. 逐个读取 `requirements/FR-XX-<topic>.md` 和 `requirements/NFR-XX-<topic>.md`（通过 Glob 匹配 `FR-*`/`NFR-*` 模式）→ 提取澄清结论中的功能描述和验收意图
   - FR-XX → 生成功能需求（F-XXX/US-XXX/AC-XXX）
   - NFR-XX → 写入 `01-requirements.md` 的非功能需求章节（性能、安全、兼容性等约束）
3. 将 FR-XX/NFR-XX 内容写入 `01-requirements.md` 的 `## 0. 原始需求` 表（来源标注为 "ms-prd"）
4. 按现有流程生成 F-XXX/US-XXX/AC-XXX（跳过方案确认，直接生成）
5. 回写映射到 `source_index_path`（即实际读取的 index.md）：
   - 若 `## DevDocs 映射` 章节已存在 → **更新现有章节**（追加/修改行，不创建新章节）
   - 若不存在 → 在文末创建该章节
   - 重新导入时：旧映射行保留（审计历史），追加新行并标记 `mapping_status: remapped`
6. 返回新增编号列表

**最小输入字段**（每个 FR-XX/NFR-XX 文件必须包含）：
- title（功能名称）
- type（FR/NFR）
- 澄清结论中的功能描述
- 验收意图（至少 1 条）

### `--fast` 模式

`--fast` 可与任意模式组合，行为变更：

- 跳过方案确认步骤（初始模式）
- 使用合理默认值（不询问技术栈偏好等）
- 仅保留最终写入前的 1 次汇总确认
- 默认行为不变，`--fast` 是 opt-in

## 工作流程

### 初始模式

```text
0. 输入检查
   │
   ├── 输入 < 200 字 + 无结构化标记 → 建议先运行 /ms-prd 探索
   │   └── AskUserQuestion：「输入较模糊，建议先用 /ms-prd 进行需求探索。继续还是切换？」
   └── 输入 >= 200 字 或有明确功能点 → 继续
   │
   ▼
0.5 设计资产感知（按 prd/references/design-context.md 探测协议）
   └── AskUserQuestion 询问设计稿和组件库 → 结果写入 01-requirements.md ## 设计资产
   │
   ▼
1. 收集原始需求
   │
   ├── 记录用户原话或关键表述
   ├── 标记来源（口述/邮件/Issue/会议纪要）
   └── 记录日期
   │
   ▼
2. 理解需求 + 探索代码库（如适用）
   │
   ▼
3. 呈现需求拆解方案 + 轻量假设挑战（AskUserQuestion）
   │  拆解确认：功能点划分、边界范围、优先级
   │  轻量假设挑战（仅初始模式 + 非 --from-prd + 非 --fast）：
   │  ① 去掉此功能，用户最大损失？ ② MVP 最小可用集？
   │  ③ 6 个月后还重要吗？
   │  （--from-prd 跳过：prd 层已做 4 题产品视角挑战）
   │  （--fast 跳过：加风险提示「跳过假设挑战，低质量需求可能进入 F/US/AC」）
   ▼
4. 用户确认方案 → 确认拆解方向或调整
   │
   ▼
5. 生成需求文档：识别功能点 (F-XXX)
   │
   ▼
6. 文档编写：用户故事 (US-XXX)
   │
   ▼
7. 文档编写：验收标准 (AC-XXX)
   │  design_context 存在时：UI 相关 US 自动补充交互状态 AC（hover/disabled/error/loading/empty）
   │
   ▼
8. 生成追溯矩阵
   │
   ▼
9. 用户确认
```

### 增量模式

```text
1. 扫描现有编号
   │
   ├── 读取 01-requirements.md
   └── 获取 F/US/AC 最大编号
   │
   ▼
1.5 设计资产感知
   ├── 01-requirements.md 已有 ## 设计资产 → 读取已有 design_context
   └── 无 → AskUserQuestion 询问（按 design-context.md 探测协议）
   │
   ▼
2. 收集新增原始需求
   │
   ├── 记录用户原话，追加到 `## 0. 原始需求` 表格
   └── 若该章节不存在（历史文档），标注"缺失历史原始需求"后继续
   │
   ▼
3. 理解新增需求
   │
   ▼
4. 追加功能点/用户故事/验收标准
   │
   ├── 延续现有编号
   └── 标注增量版本和日期
   │
   ▼
5. 更新追溯矩阵
   │
   ▼
6. 用户确认
   │
   ▼
7. 返回新增编号列表（供调用方使用）
```

### 背景信息模式

> 背景信息模式不涉及功能点生成，跳过设计资产探测（步骤 0.5）。

```text
1. 读取现有文档
   │
   ├── 检查 01-requirements.md 是否存在
   └── 提取现有"背景与目标"章节内容
   │
   ▼
2. 收集背景信息
   │
   ├── 引导用户提供信息（AskUserQuestion）
   ├── 接收用户直接输入
   ├── 从文件路径提取（Read）
   └── 从 URL 提取摘要（WebFetch）
   │
   ▼
3. 整合信息
   │
   ├── 合并到"背景与目标"章节
   ├── 补充到"技术约束"子章节
   └── 补充到"参考资料"子章节
   │
   ▼
4. 更新文档
   │
   ▼
5. 用户确认
```

### 设计资产更新模式

由 `/ms-pipeline design` 委托调用，专门处理 design_context 的写入和更新。

1. 接收 pipeline 传递的 design_context 数据
2. 确定写入目标：`--target prd-index` → prd index.md，默认 → 01-requirements.md
3. 写入/合并：无 `## 设计资产` 则新增章节；已有则按合并规则更新（见 design-context.md § 主动推送协议）
4. AC 联动检查（仅当已有 US/AC）：新增 D-XX 关联 UI 相关 US → 检查是否需补充交互状态 AC

**约束**：不触发需求拆解流程（Step 1-9），仅写入 design_context。AC 联动采用"缺失才补"规则。

## 上下文管理

### 分批原则

按功能点 (F-XXX) 分批扩写，每批完成一个功能点的全部用户故事和验收标准。

### 质量锚点

- 首个功能点的 US/AC 作为**质量锚点**
- 每个新功能点开始前，回顾首批的详细程度（US 的角色/期望/目的具体性、AC 的可量化程度、GWT 格式完整性）
- 若当前批次详细程度明显低于锚点，立即补充

### 一致性自检

每个功能点扩写完成后，对比检查：
- [ ] US 格式是否与首批一致（角色/期望/目的三要素完整）
- [ ] AC 是否可量化可验证（非"系统应正常工作"等模糊描述）
- [ ] 每个 US 是否有 2-3 条 AC（覆盖密度一致）

## 方案确认规范

**仅初始模式**需要方案确认。增量模式和背景信息模式方向明确，无需确认。

### 初始模式方案确认

在理解需求和探索代码后，**展示需求拆解方案并使用 AskUserQuestion 等待用户确认**：

```markdown
## 需求拆解方案

### 功能点划分
| 编号 | 功能点 | 描述 | 优先级 |
|------|--------|------|--------|
| F-001 | ... | ... | P0 |
| F-002 | ... | ... | P1 |

### 范围边界
- 包含：<本次范围内的功能>
- 排除：<明确不做的功能>

### 关键决策
- <需要用户确认的拆解决策>

### 预估规模
- 功能点数量：X 个
- 用户故事数量：约 Y 个
- 验收标准数量：约 Z 个

### 轻量假设挑战

> 仅初始模式 + 非 --from-prd + 非 --fast 时展示。

| # | 问题 | 回答 |
|---|------|------|
| 1 | 去掉此功能，用户最大损失？ | |
| 2 | MVP 最小可用集？ | |
| 3 | 6 个月后还重要吗？ | |

MVP 范围： / 非目标： / 删减理由：

> 以上是需求拆解方案，是否可以开始生成文档？如需调整请说明。
```

### 确认时机

| 模式 | 是否需要确认 | 理由 |
|------|-------------|------|
| 初始模式 | **是** | F 编号一旦确立，下游全部引用，改动成本高 |
| 增量模式 | 否 | 追加方向明确，编号延续现有体系 |
| 背景信息模式 | 否 | 信息整合，无架构决策 |

### 约束
- 用户确认前：只展示方案，不写入任何文件
- 用户确认后：仅生成 `docs/devdocs/` 下的文档，严禁编写实现代码
- `--fast` 模式：跳过方案确认，但保留最终汇总确认

## 编号规范

| 类型 | 前缀 | 格式 | 示例 |
|------|------|------|------|
| 功能点 | F | F-XXX | F-001, F-002 |
| 用户故事 | US | US-XXX | US-001, US-002 |
| 验收标准 | AC | AC-XXX | AC-001, AC-002 |

**编号规则**：
- 全局顺序编号，不嵌套
- 通过追溯矩阵表达关联关系
- 编号一旦分配不可复用

## 输出文件

**主文件**：`docs/devdocs/01-requirements.md`

如文档超过 300 行，可拆分为：
- `01-requirements.md` - 概览和功能点
- `01-requirements-stories.md` - 用户故事详情
- `01-requirements-nfr.md` - 非功能性需求

详细模板参见 [templates/requirements-template.md](templates/requirements-template.md)

## 文档结构

```markdown
# 需求文档：<功能名称>

## 0. 原始需求
## 0.5 设计资产（design_context，可选）
## 1. 背景与目标
## 2. 功能点清单
## 3. 用户故事
## 4. 验收标准
## 5. 追溯矩阵
## 6. 非功能性需求
## 7. 范围边界
## 8. 风险与假设
```

> `## 0. 原始需求` 记录用户原话或关键表述，作为需求精化的基准参照。详见模板。

## 核心概念

- **功能点 (F-XXX)**：用户可感知的独立功能单元，可独立交付和验证
- **用户故事 (US-XXX)**：格式 "作为 \<角色\>，我希望 \<功能\>，以便 \<价值\>"
- **验收标准 (AC-XXX)**：可量化、可验证的完成条件，每个 US 至少 2-3 条
- **追溯矩阵**：展示 F → US → AC 的关联关系

详细格式和示例参见 [templates/requirements-template.md](templates/requirements-template.md)

## 增量模式详解

详见 [references/incremental-mode.md](references/incremental-mode.md)（编号扫描、追加格式、返回值）

## 背景信息模式详解

> **进入 --context 模式时，必须读取 [context-mode.md](context-mode.md) 获取信息收集引导、输入方式和文档结构模板。**

## 约束

### 阶段边界约束（最高优先级）
- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码（源代码、脚本、配置变更）**（恢复方式：使用 /ms-dev-workflow 执行编码）
- [ ] Write 工具仅用于写入 `docs/devdocs/` 下的 Markdown 文档
- [ ] 用户确认方案后，执行文档编写（非代码实现）
- [ ] 编码实现由 `/ms-dev-workflow` 负责，本 Skill 不涉及

### 功能点约束
- [ ] 每个功能点必须有唯一编号 (F-XXX)
- [ ] 功能点必须标注优先级 (P0/P1/P2)
- [ ] 功能点描述应简洁明确

### 用户故事约束
- [ ] 每个用户故事必须关联到功能点
- [ ] 必须遵循"作为...我希望...以便..."格式
- [ ] 每个功能点至少有 1 个用户故事

### 用户故事质量检查 (INVEST) + 验收标准约束

INVEST 标准和 AC 可验证性标准详见 [references/ac-quality-rubric.md](references/ac-quality-rubric.md)，执行时按需加载。

- [ ] 每个验收标准必须有唯一编号 (AC-XXX)
- [ ] 每个用户故事至少有 2 条验收标准
- [ ] 验收标准必须可量化、可验证
- [ ] 必须描述验证方式

### 追溯约束
- [ ] 必须提供追溯矩阵
- [ ] 所有功能点必须有对应的用户故事
- [ ] 所有用户故事必须有对应的验收标准

### 增量模式约束
- [ ] **必须先扫描现有编号，延续编号**
- [ ] **追加内容必须标注增量版本和日期**
- [ ] **不得删除或覆盖现有内容**
- [ ] **完成后必须返回新增编号列表**

### 原始需求约束
- [ ] **初始模式：必须在 F/US/AC 精化前收集原始需求，写入 `## 0. 原始需求`**
- [ ] **增量模式：新增需求必须追加到 `## 0. 原始需求` 表格**
- [ ] **背景信息模式（`--context`）：不写入 `## 0. 原始需求`**——除非用户提供的是需求原话而非背景补充
- [ ] 原始需求应保留原话或最小必要改写
- [ ] 历史文档若无该章节，标注"缺失历史原始需求"后继续

### 背景信息模式约束
- [ ] **必须先读取现有"背景与目标"章节内容**
- [ ] **不得删除或覆盖现有背景信息**
- [ ] **新增内容必须标注更新日期**
- [ ] **URL 引用必须使用 WebFetch 提取摘要，不能仅记录链接**
- [ ] **文件引用必须使用 Read 验证文件存在**
- [ ] 敏感信息（密钥、密码、内部 URL）不得写入文档
- [ ] 参考资料必须注明用途和关联性

### 方案确认约束
- [ ] **初始模式：理解需求 + 探索代码后，必须展示方案并等待用户确认**
- [ ] **方案必须包含功能点划分和范围边界**
- [ ] **用户确认方案后才能开始编号分配和文档写入**
- [ ] 用户要求调整时，更新方案后重新确认
- [ ] 增量模式和背景信息模式无需方案确认
- [ ] 轻量假设挑战（3 题）仅在初始模式 + 非 `--from-prd` + 非 `--fast` 时触发
- [ ] `--from-prd` 跳过假设挑战（prd 层已做 4 题产品视角挑战）
- [ ] `--fast` 跳过假设挑战，加风险提示
- [ ] 输入模糊（< 200 字 + 无结构）时引导用户先运行 `/ms-prd`

### Generator 自检（用户确认前自动执行）

在呈现给用户确认前，加载 [references/ac-quality-rubric.md](references/ac-quality-rubric.md) 并自动验证：

- [ ] 每条 AC 可量化可验证（非模糊描述）
- [ ] 每个 US 有 ≥ 2 条 AC
- [ ] GWT 格式完整（使用 GWT 时 Given/When/Then 三要素均存在）
- [ ] INVEST 六项检查通过

自检不通过项自动修复后再呈现用户，不增加用户交互步骤。

### 确认约束
- [ ] 必须与用户确认功能点是否完整
- [ ] 不得添加用户未提及且未确认的功能

### 上下文管理约束
- [ ] 后批次 US/AC 详细程度不低于首批次（格式完整性、量化程度、覆盖密度）
- [ ] 每个功能点完成后执行一致性自检

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 新功能需求 | `/ms-feature` | 被调用：新功能触发需求追加 |
| 洞察转化 | `/ms-insights` | 被调用：改进建议转化为需求 |
| Bug 暴露需求 | `/ms-bugfix` | 被调用：Bug 修复发现需求缺失 |
| 项目改造 | `/ms-retrofit` | 被调用：逆向推导生成需求 |
| **改造后补充背景** | `/ms-retrofit` | **后续**：逆向完成后用 `--context` 补充背景 |
| 设计阶段 | `/ms-system-design` | 后续：需求确认后进入设计 |
| 上下文生成 | `/ms-onboard` | 后续：背景信息会被提取到上下文摘要 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-requirements
status: success | failed | partial
summary:
  headline: "初始需求完成，3 功能点 15 验收标准"
  details:
    mode: initial | incremental | from-prd | update-design
blockers: []
output_files:
  - docs/devdocs/01-requirements.md
new_ids:
  features: [F-001~F-003]
  stories: [US-001~US-008]
  acceptance: [AC-001~AC-015]
next_recommended:
  skill: ms-system-design
```

## 下一步

| 完成模式 | 建议下一步 |
|----------|------------|
| 初始模式 | `/ms-system-design` 进入系统设计 |
| 增量模式 | `/ms-system-design` 增量设计或 `/ms-test-cases` 补充测试 |
| 背景信息模式 | 继续 `/ms-requirements` 定义功能点，或 `/ms-system-design` 设计 |

> **提示**：文档变更较大时，建议运行 `/agent-memory` 同步记忆文件。
