---
name: ms-system-design
description: Create or update system design documents. Supports initial design and incremental design (impact analysis + compatibility assessment) modes. Use when users need technical architecture, API design, data models, module design, or design changes. Triggers on "system design", "architecture", "technical design", "API design", "design change", "impact analysis", "模块设计", "技术方案", "接口设计", "设计变更", "影响分析". NOT for UI/UX design (use ui-orchestrator) or requirements definition (use ms-requirements).
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
metadata:
  patterns: [inversion, generator]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 系统设计

基于需求文档创建或更新系统设计文档，支持初始设计和增量设计两种模式。

## 角色

- 身份：系统架构师
- 关注：技术取舍、模块边界、接口契约、可扩展性
- 回避：用户故事细节、产品优先级排序、UI 视觉与交互实现（消费设计稿数据需求驱动 API）
- 判断倾向：优先简单方案，复杂度需有明确理由

## 快速开始

**一句话**: 创建或更新系统设计文档（架构、API、数据模型）。

**最常见用法**: `/ms-system-design`（自动检测初始/增量）

**不适合?** 需求还没写→`/ms-requirements`，UI 设计→`ui-orchestrator`

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 触发条件

### 初始设计模式
- 用户已完成需求文档，项目无系统设计
- 用户要求系统/技术设计
- 用户需要架构或 API 设计

### 增量设计模式
- 新功能加入后需要设计变更（来自 `/ms-feature`）
- 优化建议确认后需要设计调整（来自 `/ms-insights`）
- 技术改进需要架构调整
- 用户要求更新/修改现有设计

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 如不存在，建议先运行 `/ms-requirements`

## 设计模式检测

启动时自动检测：`02-system-design.md` 不存在 → 初始设计模式；存在 → 检查是否有未覆盖的 F-XXX，有则提示增量设计，无则询问用户意图。

## 运行模式

```bash
/ms-system-design              → 自动检测模式（初始/增量）
/ms-system-design --fast       → 跳过偏好询问和方案确认交互，保留已有实现核对和最终汇总确认
```

## 工作流程

### 初始设计流程（自顶向下 L1~L4 分层推进）

```text
1. 读取需求 → 加载 01-requirements.md（含 design_context）
      │
      ▼
2. 询问偏好 → 技术栈、平台、集成需求
      │
      ▼
3. 探索代码 → 针对需求涉及的接口/实体/表确认已有实现
      │
      ▼
3.5 外部研究（按需）→ 详见"设计前外部研究"章节
      │
      ▼
4. 自顶向下分层设计（每层独立 AskUserQuestion 确认）
      ├── L1 架构层：§2 架构概览 + §1 运行平台
      │     聚焦：边界、分层、关键外部依赖
      ├── L2 模块层：§4 模块设计（职责 + 对外/依赖接口引用）
      │     聚焦：模块边界、单一职责、依赖方向面向接口
      │     自查：SRP / LoD / DIP（见 references/solid-principles-guide.md）
      ├── L3 接口行为层：§5 核心接口（签名 + 前置/后置/错误契约）
      │     聚焦：契约可测性、接口行为非代码细节
      │     ⛔ 强制通过"设计边界自查清单"（references/design-boundary-guide.md）
      │     自查：OCP / LSP / ISP / DIP
      └── L4 数据模型层：§8 数据模型（实体/关系/索引）
            聚焦：存储层不可见细节（可观察约束应在 §5 错误契约）
      │
      ▼
5. 对抗性审查（按复杂度分级触发 SOLID+LoD，见 references/design-review.md）
      │
      ▼
6. 生成 docs/devdocs/02-system-design.md 文档（含审查结论 + 原则校验表 + 关键选型 ADR）
      │
      ▼
7. 验证覆盖 → 所有 F-XXX 都有对应模块/接口
      │
      ▼
8. 用户确认 → 获得批准后定稿
```

**关键规则**：
- **每层允许遗留** `⏳` 占位（某些字段/错误码/参数待下一层或实现阶段细化）；L4 完成时强制汇总所有 `⏳` 清单
- **按复杂度裁剪**：简单需求（单模块、≤3 接口）允许自动合并 L2+L3 或 L3+L4 的确认点；L1 必须独立
- **L3 vs L4 判界**：外部调用方**可观察**的行为归 L3；**不可见**的持久化细节归 L4（详见 design-boundary-guide.md）
- **`--fast` 模式**：L1~L4 合并为一次 AskUserQuestion 展示，但**"越界反例自查 + L1~L4 边界校验 + 原则校验表 + 总确认"不得跳过**

### 增量设计流程

```text
1. 读取现有设计 → 加载 02-system-design*.md
      │
      ▼
2. 识别变更来源
      ├── 新功能需求（F-XXX）
      ├── 优化建议（INS-XXX）
      └── 技术改进
      │
      ▼
3. 影响分析
      ├── 识别受影响的模块
      ├── 识别受影响的接口
      └── 识别受影响的数据模型
      │
      ▼
4. 兼容性评估
      ├── 接口变更是否向后兼容？
      ├── 数据模型变更是否需要迁移？
      └── 是否有破坏性变更？
      │
      ▼
5. 呈现变更方案 + 对抗性审查（AskUserQuestion）
      ├── 常规：三视角挑战（用户价值/架构兼容性/可测试性）
      ├── 新增：**修订清单表格**（必填，格式 §章节 | 动作 | 描述，≤10 行）
      │     动作枚举：新增 / 改写 / 局部调整 / 重构
      └── 新增：**原则校验表**（按复杂度触发 SOLID+LoD，三态强制填写）
      │
      ▼
6. 用户确认方案（含修订清单与原则校验）
      │
      ▼
7. 更新 docs/devdocs/02-system-design*.md 文档
      └── 按修订清单逐条执行正文更新（非仅 ADR 追加）
      │
      ▼
8. 追加变更记录（ADR 仅记 WHY，不记 WHAT；详见 incremental-design.md 检查清单）
      │
      ▼
9. 用户确认 → 获得批准后更新文档
```

## 方案确认规范

在分析完成、写入文档前，**展示设计方案草案并使用 AskUserQuestion 等待用户确认**，确认后再生成文档。草案模板见 [references/plan-drafts.md](references/plan-drafts.md)。

| 模式 | 确认时机 | 方案内容 |
|------|----------|-----------|
| 初始设计 | L1~L4 四层分层推进（或 --fast 合并展示）后 | 技术选型、架构、L2 模块、L3 接口、L4 数据、原则校验 |
| 增量设计 | 影响分析 + 兼容性评估后 | 影响范围、变更策略、**修订清单**、原则校验 |

**约束**：
- 用户确认前：只展示方案，不写入任何文件
- 用户确认后：仅生成 `docs/devdocs/` 下的文档，严禁编写实现代码
- `--fast` 模式：跳过分层交互，但保留越界反例自查 + L1~L4 边界校验 + 原则校验表 + 一次性总确认

## 设计前外部研究

当需求涉及不熟悉的技术/框架或复杂集成时，应在方案确认之前进行外部研究（依赖可用的外部检索工具）。

**触发条件**：项目未使用过的技术、复杂第三方集成、存在多种可行方案需对比。

**研究三步骤**：

1. **现有代码模式扫描** — 扫描项目架构和 `docs/devdocs/patterns/` 已有经验，确认兼容性。**必须检索 patterns/ 目录**：扫描标题列表，匹配当前设计需求的关键词，如命中则读取详情作为设计参考（避免重复踩坑、复用已验证方案）
2. **官方文档确认**（若有外部检索工具可用）— 查阅官方文档确认 API 可用性、版本兼容性、已知限制（可用 context7 MCP）
3. **最佳实践摘要**（若有外部检索工具可用）— 搜索社区最佳实践和常见陷阱，对比方案优劣

**研究结论必须写入设计文档**（"技术选型"章节），格式：

```markdown
#### <技术名称>
**研究结论**：
- 官方文档确认：<版本、兼容性、限制>
- 最佳实践：<关键发现>
- 选择理由：<为什么选这个方案>
- 已知风险：<潜在问题和缓解措施>
```

**跳过条件**：使用项目已有技术栈、需求简单方案明确、`--fast` 模式。

## 设计前必问

**必须使用 AskUserQuestion 询问用户**：

1. **技术栈偏好**
   - 是否有偏好的技术栈？
   - 选项：指定技术栈 / 无偏好（将根据需求推荐）

2. **目标平台**
   - 目标平台是什么？
   - 选项：Web / Mobile (iOS/Android) / Desktop / Server / 跨平台

3. **部署环境**
   - 部署在哪里？
   - 选项：云服务 (AWS/GCP/Azure) / 私有化 / 混合

4. **现有系统集成**
   - 是否需要与现有系统集成？
   - 选项：否 / 是（指定系统、API、数据库）

如用户无偏好，则根据需求设计最优方案。

## 增量设计

增量设计遵循三步流程：**变更范围分类 → 影响分析 → 兼容性评估**，然后更新设计文档并生成 ADR 记录。

- 变更范围分为三级：仅内部实现（轻量分析）、涉及模块接口（标准分析）、涉及架构（完整分析 + ADR）
- 影响分析需覆盖受影响的模块、接口、数据模型，并自动扫描关联文档
- 兼容性评估判断向后兼容性，破坏性变更须标注废弃周期和迁移方案
- 每个变更项使用统一的变更对比格式（变更前/变更后/原因/影响范围）

> **进入增量设计模式时，必须读取 [incremental-design.md](references/incremental-design.md) 获取影响分析、兼容性评估、变更对比格式和检查清单。**

## 输出文件

**主文件**：`docs/devdocs/02-system-design.md`

### 文档拆分规则

当满足以下条件时，应拆分文档：
- 文档超过 **300 行**
- 模块数量超过 **5 个**
- API 接口超过 **10 个**

**拆分方式**：

```text
docs/devdocs/
├── 02-system-design.md          # 主文档：架构概览、技术选型、模块划分
├── 02-system-design-api.md      # API 设计：接口定义、请求响应示例
└── 02-system-design-data.md     # 数据模型：实体定义、ER 图、索引策略
```

**拆分内容分配**：

| 文件 | 包含章节 |
|------|----------|
| 02-system-design.md | 1-7, 15-16: 平台、架构、技术选型、模块、接口签名、模式、代码落位原则、设计审查、ADR |
| 02-system-design-api.md | 9-10: 完整 API 设计、状态流转 |
| 02-system-design-data.md | 8, 11-14: 数据模型、异常处理、扩展性、需求追溯 |

详细模板参见 [templates/design-template.md](templates/design-template.md)。

## 设计原则

### MTE 原则

系统设计必须遵循 **MTE 原则**：

| 原则 | 说明 | 检查点 |
|------|------|--------|
| **Maintainability** | 可维护性 | 模块职责单一、依赖清晰、易于理解和修改 |
| **Testability** | 可测试性 | 核心逻辑可单元测试、依赖可 Mock、边界清晰（参考 `/testing-guide`） |
| **Extensibility** | 可扩展性 | 预留扩展点、接口抽象、开闭原则 |

### 设计模式选择

根据场景选择合适的设计模式，**只在必要时使用**。详见 [references/design-patterns.md](references/design-patterns.md)。

### 设计层次

接口层（薄层）→ 服务层（核心业务逻辑）→ 领域层（实体/值对象）→ 基础设施层（数据访问/外部服务）

## 文档结构

1. **目标平台** - 平台、版本要求、部署环境
2. **架构概览** - 高层架构图（**Mermaid**）
3. **技术选型** - 技术选择及理由
4. **模块设计** - 模块职责与依赖，**标注关联功能点 (F-XXX)**
5. **核心接口** - **面向接口 (签名 + 行为契约)**: 方法签名 + 前置条件/后置条件/错误契约（**严禁包含具体实现逻辑**），标注关联 F-XXX
6. **设计模式** - 应用的模式及理由
7. **代码落位原则** - 模块落位/接口-实现分离/命名约束（非完整目录树；详见 `references/code-structure-conventions.md`）
8. **数据模型** - 实体定义与关系
9. **API 设计** - 接口端点及请求/响应示例，**标注关联 F-XXX, AC-XXX**；design_context 存在时页面数据需求驱动响应结构
10. **状态流转** - 关键业务流程的状态机
11. **异常处理** - 错误码与处理策略
12. **日志设计** - 日志级别、关键日志点、追溯 ID
13. **扩展性** - 扩展点与未来考量
14. **需求追溯** - 功能点与模块/接口的映射关系，**覆盖检查清单**
15. **设计审查** - 对抗性审查结论（产品/工程/测试三视角）
16. **设计变更记录（ADR）** - 初始设计记录关键选型，增量设计记录变更

## 详细参考

- 设计文档完整模板 → [templates/design-template.md](templates/design-template.md)
- 日志设计 → [templates/log-design-guide.md](templates/log-design-guide.md)
- 对抗性审查问题清单 → [references/design-review.md](references/design-review.md)
- UI→API 映射 → [references/design-input-guide.md](references/design-input-guide.md)
- 设计边界反例（设计 vs 实现） → [references/design-boundary-guide.md](references/design-boundary-guide.md)
- SOLID+LoD 六原则指南 → [references/solid-principles-guide.md](references/solid-principles-guide.md)
- 代码目录约定（非设计决策） → [references/code-structure-conventions.md](references/code-structure-conventions.md)
- 方案草案模板（初始+增量） → [references/plan-drafts.md](references/plan-drafts.md)
- 增量设计详解 → [references/incremental-design.md](references/incremental-design.md)

## 约束

### 阶段边界约束（最高优先级）
- [ ] **⛔ 禁止继续：文档阶段不得产出实现代码（源代码、脚本、配置变更）**（恢复方式：使用 /ms-dev-workflow 执行编码）
- [ ] Write 工具仅用于写入 `docs/devdocs/` 下的 Markdown 文档
- [ ] "核心接口"章节仅定义签名和行为契约，严禁包含实现逻辑（编码由 `/ms-dev-workflow` 负责）
- [ ] **⛔ 禁止继续：接口契约内出现越界反例**（算法细化/内部状态/控制流/伪代码/字段注释性描述/时序重试策略/依赖耦合到实现，见 `references/design-boundary-guide.md`）（恢复方式：改写为行为契约表述）
- [ ] **⛔ 禁止继续：存在跨模块依赖时，§4 模块表"依赖接口引用"列出现具体实现类名或裸模块名**（恢复方式：改写为 `I*(§章节号)` 引用；接口未定义则回 L3 层补足；单模块或无跨模块依赖填"无"）
- [ ] **⛔ 禁止继续（增量设计）：仅追加 ADR 而正文相关章节未更新**（恢复方式：按修订清单执行正文更新，或在清单内登记"仅追加 ADR 的理由"）

### 基础约束

- [ ] **必须先询问用户技术栈偏好和目标平台**
- [ ] 技术选型必须说明理由
- [ ] 如用户无偏好，根据需求选择最优方案
- [ ] 必须指定目标平台和最低版本要求
- [ ] API 设计必须包含请求/响应示例
- [ ] 数据模型必须考虑索引和查询模式
- [ ] 必须识别与现有系统的集成点，区分已有实现（复用）/扩展/新增，方案草案须含核对证据
- [ ] 优先使用项目现有技术栈

### MTE + SOLID/LoD 原则约束

MTE 为上位目标（Maintainability/Testability/Extensibility，见 [references/mte-rubric.md](references/mte-rubric.md)）；
SOLID + 迪米特六原则为达成上位目标的**设计证据**（见 [references/solid-principles-guide.md](references/solid-principles-guide.md)）。两套不合并，MTE 评估时引用 SOLID 作证据。

- [ ] **每个模块职责单一**（SRP），职责描述不含多职责连接词（和/并且）
- [ ] **核心业务逻辑必须可单元测试**（无外部依赖或依赖可 Mock）
- [ ] **核心接口必须包含行为契约**（前置/后置/错误契约），使测试可独立于实现编写
- [ ] **预留合理扩展点，但不为假设需求设计**（OCP 指导）
- [ ] **设计必须考虑 SOLID + 迪米特六原则**（SRP/OCP/LSP/LoD/ISP/DIP），按项目复杂度分级触发：单模块 3 原则 / 低-中复杂度 4 原则 / 高复杂度 6 原则
- [ ] **审查结论表的原则校验字段必须三态填写**（✅ 适用 / — 不适用 / ⚠️ 违反+理由），不允许空着；⚠️ 违反必须在 ADR 中说明理由
- [ ] **⛔ 适用下限校验**：单模块至少 2 项/中复杂度至少 3 项/高复杂度至少 5 项为 `✅ 适用`；未达下限视为原则未考虑 → 审查"待修正"，不放行（详见 `references/solid-principles-guide.md`）
- [ ] DIP 硬约束见"阶段边界约束"的 §4 依赖接口引用门禁；其余 5 原则为启发式阈值告警（超阈值需理由+ADR，非硬阻断）

### 设计模式约束

- [ ] **只在解决实际问题时使用设计模式，不为使用而使用**
- [ ] 使用的设计模式必须说明解决什么问题
- [ ] 优先选择简单方案，复杂方案需要说明理由
- [ ] 相同问题在项目中使用一致的模式

### 避免过度设计

- [ ] **不为"未来可能"的需求设计，只为当前需求设计**
- [ ] **默认保留依赖倒置**：模块间通过 §5 接口通信；下条"单实现接口"约束仅针对"过度抽象（为纯内部细节创建接口）"，**不削弱"跨模块依赖面向接口"的核心原则**
- [ ] 不创建只有一个实现的接口（除非为了可测试性或跨模块边界）
- [ ] 不过早抽象，等到有 3 个以上相似场景再抽象
- [ ] 配置优于硬编码，但不为所有内容添加配置

### 安全约束

- [ ] **敏感数据（密码、Token）不明文存储**
- [ ] **需要认证的 API 已标注**
- [ ] **用户输入有验证（防注入）**
- [ ] 敏感操作有日志记录

### 外部研究约束

- [ ] **涉及不熟悉技术且有外部检索工具时，应在方案确认前完成外部研究；无外部工具时，基于现有代码模式扫描和用户输入进行研究**
- [ ] **研究结论必须写入设计文档，不仅存在于对话中**
- [ ] 已有技术栈或简单需求可跳过研究
- [ ] `--fast` 模式跳过研究步骤

### 方案确认约束

- [ ] **初始设计：读取需求 + 询问偏好 + 探索代码（+ 外部研究）后，必须展示方案并等待用户确认**
- [ ] **增量设计：影响分析 + 兼容性评估后，必须展示方案并等待用户确认**
- [ ] **方案必须包含技术选型理由（初始）或影响范围（增量）**
- [ ] **用户确认方案后才能写入文档**
- [ ] 用户要求调整时，更新方案后重新确认
- [ ] 对抗性审查在草案生成后、AskUserQuestion 呈现时自动执行，三视角各至少 1 个挑战
- [ ] 审查结果嵌入确认草案一并展示，用户确认后写入最终文档「设计审查」节

### 增量设计约束

- [ ] **增量设计前必须进行影响分析 + 向后兼容性评估 + 变更范围分类**
- [ ] **破坏性变更必须标注处理方式，数据模型变更必须说明迁移方案**
- [ ] **必须生成设计变更记录（ADR 格式）；初始设计对关键选型同样生成 ADR**
- [ ] 新增内容必须标注关联需求（F-XXX / INS-XXX），修改接口必须说明兼容性
- [ ] **涉及模块接口或架构的变更必须使用变更对比格式**
- [ ] **必须自动扫描受影响文档并列出更新清单**

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 新功能设计变更 | `/ms-feature` | 新功能触发增量设计 |
| 优化建议设计变更 | `/ms-insights` | 洞察确认后触发增量设计 |
| 可测试性设计 | `/testing-guide` | 确保核心逻辑可单元测试 |
| 代码质量 | `/code-quality` | MTE 原则指导设计 |
| UI 架构 | `/ui-orchestrator` | 路由到专业的外部 UI/UX Skill |
| 接口自动提取 | `/ms-retrofit` | 从现有代码逆向提取接口定义并同步到设计文档 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-system-design
status: success | failed | partial
summary:
  headline: "初始设计完成，2 模块 2 接口"
  details:
    mode: initial | incremental
    modules_added: [AuthModule, UserModule]
    interfaces_added: ["POST /api/register", "POST /api/login"]
    data_models_added: [User, Session]
    breaking_changes: false
    patterns_referenced: []
blockers: []
output_files:
  - docs/devdocs/02-system-design.md
new_ids: {}
next_recommended:
  skill: ms-test-cases
```

## 下一步

### 初始设计后
用户确认系统设计后，建议运行 `/ms-test-cases` 进入测试用例设计阶段。

### 增量设计后

1. 如有新增功能点 → 运行 `/ms-test-cases` 补充测试用例
2. 如有数据模型变更 → 在设计文档中记录迁移方案，实际脚本由 `/ms-dev-workflow` 执行
3. 如有破坏性变更 → 在设计文档中标注影响范围和迁移策略

> **提示**：文档变更较大时，建议运行 `/agent-memory` 同步记忆文件。
