---
name: devdocs-feature
description: Add new features to existing DevDocs projects. Orchestrates requirements → design → test-cases → dev-tasks for incremental functionality. Use when users need to add, extend, or iterate on features. Triggers on "add feature", "new feature", "新功能", "迭代", "新增功能", "追加需求", "扩展功能", "feature request", "增量功能". NOT for pipeline init (use devdocs-pipeline) or bug fixes (use devdocs-bugfix).
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, Task
---

# 新功能

在已有 DevDocs 项目中追加新功能，确保编号延续、文档一致。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 触发条件

- 用户要在已有项目中添加新功能
- 用户提到"增量"、"迭代"、"新增功能"、"追加需求"
- 用户要求扩展现有功能

## 前置条件

- 已存在 DevDocs 文档目录：`docs/devdocs/`
- 至少存在 `01-requirements.md`

如不存在，建议：
- 新项目 → `/devdocs-requirements`
- 已有代码无文档 → `/devdocs-retrofit`

## 运行模式

### 模式选择

```bash
/devdocs-feature "功能描述"             → 自动检测模式
/devdocs-feature --lite "功能描述"      → 强制轻量模式
/devdocs-feature --fast "功能描述"      → 连续执行 Step 1-5，仅最终汇总确认
/devdocs-feature --lite --fast "功能描述" → 轻量 + 快速组合
```

### 模式对比

| 模式 | 适用场景 | 更新文档 | 上下文负载 |
|------|----------|----------|------------|
| 轻量模式 | 配置修改、UI 微调、简单字段 | 01 + 04 | 低 |
| 完整模式 | 新模块、新接口、架构变更 | 01 + 02 + 03 + 04 | 高（分步） |

### 自动模式检测

分析需求描述，检测是否涉及：

```text
[ ] 新增 API 接口
[ ] 数据模型变更
[ ] 组件间依赖变化
[ ] 第三方服务集成
[ ] 新增独立模块
```

- **以上均无** → 轻量模式
- **任一命中** → 完整模式（提示用户确认）

```markdown
检测到可能涉及架构变更：
- 新增接口: UserPreferenceAPI

建议使用完整模式。是否继续轻量模式？[是/否]
```

## 核心理念

```text
新功能开发 = 延续编号 + 追加文档 + 影响分析 + 回归保护
```

## 轻量模式流程 (--lite)

```text
1. 扫描编号
   │
   ├── 读取 01-requirements.md → 获取 AC 最大编号
   └── 读取 04-dev-tasks*.md → 获取 T 最大编号
   │
   ▼
2. 收集需求（简化）
   │
   └── 验收标准（AC 级别）
   │
   ▼
3. 追加文档（仅两份）
   │
   ├── 01-requirements.md → 追加 AC（挂载到现有 F/US）
   └── 04-dev-tasks*.md → 追加 1-3 个任务
   │
   ▼
4. 用户确认
```

### 轻量模式约束

- 不新建 F-XXX（功能点），仅追加 AC 到现有功能
- 不更新 02-system-design（无架构变更）
- 不更新 03-test-cases（追加任务中直接内联测试用例编号和验收标准；
  建议进入 dev-workflow 前确认 03-test-cases 中已有对应条目，
  dev-workflow 启动时会自动检测并提示补齐）
- 任务数量限制 1-3 个（可直接追加，无需调用 devdocs-dev-tasks）
- 任务必须遵循 TAR 原则格式

### ⚠️ 轻量模式追溯警告

轻量模式跳过 02（系统设计）和 03（测试用例）文档更新，**追溯链不完整**（F → US → AC → UT/IT/E2E 的链路在设计层和测试层断裂）。在 Step 4 用户确认时必须显示以下警告：

```
⚠️ 轻量模式跳过了设计文档和测试用例更新，追溯链不完整。
建议在开发前补齐：
  - /devdocs-system-design（补充设计）
  - /devdocs-test-cases（补充测试用例）
或切换到完整模式：/devdocs-feature "功能描述"
```

## 完整模式流程（分步编排）

> **核心变更**：不再一次性更新 4 份文档，而是分步执行，每步确认后再进入下一步。

```text
┌─────────────────────────────────────────────────────────────┐
│  Step 0: 扫描现有文档，获取编号和架构摘要                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 需求追加                                           │
│  ├── 收集新功能描述                                         │
│  ├── 追加 01-requirements.md（F/US/AC）                     │
│  └── ✅ 用户确认                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 设计追加                                           │
│  ├── 影响分析（模块/接口/数据）                             │
│  ├── 追加 02-system-design*.md                              │
│  └── ✅ 用户确认                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 测试追加                                           │
│  ├── 根据新增 AC 设计测试用例                               │
│  ├── 追加 03-test-cases*.md + 更新追溯矩阵                  │
│  └── ✅ 用户确认                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: 任务追加                                           │
│  ├── 根据设计和测试拆分开发任务                             │
│  ├── 追加 04-dev-tasks*.md                                  │
│  └── ✅ 用户确认                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: 生成功能日志                                       │
│  └── 更新 00-feature-log.md                                 │
└─────────────────────────────────────────────────────────────┘
```

### 分步执行优势

| 问题 | 传统方式 | 分步编排 |
|------|----------|----------|
| 编号重复 | 一次维护 4 份编号，易出错 | 每步只关注当前文档编号 |
| 漏更新 | 上下文过长，易遗漏 | 每步确认，不遗漏 |
| 追溯不完整 | 难以保证 AC→测试 完整性 | Step 3 专注追溯矩阵 |
| 回滚困难 | 全量修改难回滚 | 可在任意步骤终止 |

## Step 0: 扫描现有文档

### 编号提取

从现有文档中提取最大编号：

```markdown
## 当前状态

| 类型 | 当前最大编号 | 下一编号 |
|------|-------------|----------|
| 功能点 (F) | F-003 | F-004 |
| 用户故事 (US) | US-008 | US-009 |
| 验收标准 (AC) | AC-015 | AC-016 |
| 单元测试 (UT) | UT-012 | UT-013 |
| 集成测试 (IT) | IT-003 | IT-004 |
| E2E 测试 (E2E) | E2E-002 | E2E-003 |
| 开发任务 (T) | T-10 | T-11 |
```

### 架构摘要（完整模式）

从 `02-system-design*.md` 提取：
- 现有模块列表
- 核心接口
- 数据实体

## Step 1: 需求追加

> **委托执行**：本步骤必须委托给 `/devdocs-requirements --incremental`，由其负责增量需求。

### 委托输入

传递给 `/devdocs-requirements` 的上下文：
- 用户的新功能描述
- Step 0 扫描到的现有编号状态

### 委托输出

从 `/devdocs-requirements` 获取：
- 新增的 F-XXX、US-XXX、AC-XXX 编号列表
- 更新后的追溯矩阵

### ✅ 确认点（默认模式）

展示步骤摘要块（编号 + 关键变更），等待用户确认。`--fast` 模式跳过此确认。

## Step 2: 设计追加（完整模式）

> **委托执行**：本步骤必须委托给 `/devdocs-system-design`，由其负责增量设计。

### 委托输入

传递给 `/devdocs-system-design` 的上下文：
- Step 1 新增的 F-XXX、US-XXX、AC-XXX 编号
- 现有架构摘要（来自 Step 0）
- 影响分析问题清单

### 委托输出

从 `/devdocs-system-design` 获取：
- 新增/变更的模块和接口
- 影响摘要
- 回归风险点

### ✅ 确认点（默认模式）

展示步骤摘要块（影响范围 + 兼容性结论），等待用户确认。`--fast` 模式跳过此确认。

## Step 3: 测试追加（完整模式）

> **委托执行**：本步骤必须委托给 `/devdocs-test-cases`，由其负责增量测试设计。

### 委托输入

传递给 `/devdocs-test-cases` 的上下文：
- Step 1 新增的 AC-XXX 编号
- Step 2 新增的接口和模块（来自 system-design）

### 委托输出

从 `/devdocs-test-cases` 获取：
- 新增的 UT/IT/E2E-XXX 编号
- 更新后的追溯矩阵

### ✅ 确认点（默认模式）

展示步骤摘要块（新增测试编号 + 矩阵更新状态），等待用户确认。`--fast` 模式跳过此确认。

## Step 4: 任务追加

### 调用 devdocs-dev-tasks

> **重要**：完整模式下，任务拆分由 `/devdocs-dev-tasks` 负责，确保 TAR 原则和分层 TDD 标记的一致性。

**传递给 devdocs-dev-tasks 的上下文**：
- 新增的 F-XXX、AC-XXX 编号
- 新增的 UT/IT/E2E-XXX 编号
- 影响的模块和接口

```text
调用 /devdocs-dev-tasks：
- 输入：Step 1-3 产生的新增编号
- 输出：追加到 04-dev-tasks*.md
- 遵循：TAR 原则、分层 TDD
```

### ✅ 确认点（默认模式）

展示步骤摘要块（新增任务范围 + TDD 分层标注），等待用户确认。`--fast` 模式跳过此确认。

## Step 4.5: 就绪检查（完整模式）

> **委托执行**：本步骤必须委托给 `/devdocs-verify --readiness`，作为进入开发前的质量关卡。

### 委托输入

传递给 `/devdocs-verify --readiness` 的上下文：
- Step 1-4 新增的编号列表

### 委托输出

从 `/devdocs-verify --readiness` 获取：
- readiness 检查结果（P1/P2/P3 问题列表）
- 就绪状态（pass / fail）

### 关卡规则

- **P1 问题存在** → 阻塞进入 Step 6，展示问题清单并建议修复后重试
- **仅 P2/P3** → 展示警告，询问用户是否继续
- **全部通过** → 自动进入 Step 5

## Step 5: 生成功能日志

### 输出文件

```text
docs/devdocs/
└── 00-feature-log.md    # 功能日志（追加）
```

详细模板参见 [templates/feature-log-template.md](templates/feature-log-template.md)

## Step 6: 衔接开发执行（可选）

完整模式下，任务分解完成后，询问用户是否继续执行开发：

```
任务分解已完成，新增 N 个开发任务（T-XX ~ T-YY）。

是否继续执行开发？[是(默认)/否]
- 是 → 自动衔接 /devdocs-dev-workflow T-XX~T-YY
- 否 → 结束 feature 流程，用户后续手动调用 dev-workflow
```

**默认行为**：是（继续执行）。用户选择"否"时，输出任务编号范围供后续手动调用。

> 轻量模式同样支持 Step 6，直接衔接 1-3 个任务的开发。

## 编排规范（子 Agent 调度）

完整模式下，devdocs-feature 调用子技能时**必须通过 Task tool 启动子 Agent**：

| Step | 被调度技能 | 调度方式 |
|------|-----------|----------|
| Step 1 | `/devdocs-requirements --incremental` | Task tool 子 Agent |
| Step 2 | `/devdocs-system-design` | Task tool 子 Agent |
| Step 3 | `/devdocs-test-cases` | Task tool 子 Agent |
| Step 4 | `/devdocs-dev-tasks` | Task tool 子 Agent |
| Step 4.5 | `/devdocs-verify --readiness` | Task tool 子 Agent |
| Step 6 | `/devdocs-dev-workflow` | Task tool 子 Agent |

### 调度原则

1. **上下文隔离**：每个子 Agent 自行读取所需文档，feature 编排层不传递全文
2. **摘要传递**：步骤间只传递 YAML 摘要 + 新增编号列表
3. **异常回退**：子 Agent 返回 `status: failed` + `blockers` 时，展示阻塞项询问用户
4. **不自行排障**：编排层不读取子技能的完整输出文档来尝试修复

> 轻量模式因任务简单（1-3 个任务），直接在 feature 上下文内执行，不启动子 Agent。

## Skill 协作

| 阶段 | 协作 Skill | 说明 |
|------|-----------|------|
| 需求追加 | `/devdocs-requirements` | **完整模式必须委托**（增量更新） |
| 设计追加 | `/devdocs-system-design` | **完整模式必须委托**（增量更新） |
| 测试追加 | `/devdocs-test-cases` | **完整模式必须委托**（增量更新 + 矩阵） |
| 任务追加 | `/devdocs-dev-tasks` | **完整模式必须委托** |
| 就绪检查 | `/devdocs-verify --readiness` | **完整模式必须委托**（Step 4.5 质量关卡） |
| 开发实现 | `/devdocs-dev-workflow` | Step 6 自动衔接（用户可跳过） |
| 编码约束 | `/code-quality`, `/testing-guide` | 编码阶段 |

> **编排器边界**：`devdocs-feature` 是纯编排器，负责步骤编排、确认流程、功能日志。
> 具体的需求、设计、测试、任务内容全部由对应的专项 Skill 负责，本 Skill 不复制其逻辑。

## 约束

### 编号约束

- [ ] **必须延续现有编号，不得重复**
- [ ] **必须先扫描现有文档获取最大编号**
- [ ] 编号格式保持一致（F-XXX, US-XXX, AC-XXX）

### 文档约束

- [ ] **追加内容必须标注功能版本和日期**
- [ ] **不得删除或覆盖现有内容**
- [ ] 追加位置必须正确（章节末尾）
- [ ] 格式必须与现有文档一致

### 分步编排约束（完整模式）

- [ ] **默认每步完成后等待用户确认**
- [ ] **`--fast` 模式：Step 0 扫描照常，Step 1-4 连续执行不逐步确认，Step 5 生成功能日志后展示汇总做 1 次确认**
- [ ] **不得跳过步骤（除非用户明确要求）**
- [ ] 用户可在任意步骤选择"终止"（`--fast` 下可 Ctrl+C）
- [ ] 每步只关注当前文档的编号和格式
- [ ] 步骤间传递的信息仅限：新增编号列表
- [ ] **完整模式 Step 1-4、Step 4.5、Step 6 必须通过 Task tool 启动子 Agent**
- [ ] **步骤间只传递 YAML 摘要 + 编号列表，不传递文档全文**

### 轻量模式约束

- [ ] **仅更新 01-requirements.md 和 04-dev-tasks.md**
- [ ] **不新建 F-XXX，仅追加 AC 到现有功能**
- [ ] 任务数量限制 1-3 个
- [ ] 检测到架构影响时必须提示用户

### 影响分析约束

- [ ] **修改现有接口必须说明向后兼容性**
- [ ] **必须列出回归风险点**
- [ ] 高影响变更需用户确认

### 追溯约束（完整模式）

- [ ] **新增 F-XXX 必须有对应 US-XXX 和 AC-XXX**
- [ ] **新增 AC-XXX 必须有对应测试用例**
- [ ] 必须更新追溯矩阵

## 特殊情况

### 文档结构不完整

如果只有部分文档存在：

```text
1. 提示用户缺失的文档
2. 建议先补全文档（使用 /devdocs-retrofit）
3. 或仅追加到已有文档
```

### 大规模功能

如果新功能需求较大（超过 3 个功能点）：

```text
建议拆分为多次迭代：
1. 按功能模块拆分
2. 每次迭代独立完成
3. 分别提交和验证
```

### 需求变更（非新增）

如果是修改现有需求而非新增：

```text
⚠️ 这是需求变更，不是新功能需求。

建议：
1. 在原 F-XXX 下标注变更
2. 更新相关 US/AC
3. 更新受影响的测试用例
4. 记录变更原因
```

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: devdocs-feature
mode: lite | full
new_ids:
  features: [F-004]
  stories: [US-009, US-010]
  acceptance: [AC-016~AC-020]
  tests: [UT-013~UT-015, IT-004]
  tasks: [T-11~T-13]
status: completed | interrupted
step_reached: 1~6
dev_workflow_triggered: true | false
output_files:
  - docs/devdocs/01-requirements.md
  - docs/devdocs/00-feature-log.md
```

## 输出

- 更新 `01-requirements.md`（追加）
- 更新 `02-system-design*.md`（追加/修改）
- 更新 `03-test-*.md`（追加）
- 更新 `04-dev-tasks*.md`（追加）
- 更新/创建 `00-feature-log.md`（追加）
