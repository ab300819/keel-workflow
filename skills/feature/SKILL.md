---
name: ms-feature
description: Add new features to existing DevDocs projects. Orchestrates requirements → design → test-cases → dev-tasks for incremental functionality. Use when users need to add, extend, or iterate on features. Triggers on "add feature", "new feature", "新功能", "迭代", "新增功能", "追加需求", "扩展功能", "feature request", "增量功能". NOT for pipeline init (use ms-pipeline) or bug fixes (use ms-bugfix).
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, Task
metadata:
  patterns: [pipeline, inversion]
  interaction: multi-turn
  handoff: yaml-summary-v1
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
- 存在 `01-requirements.md` **或** `00-baseline.md`

**有 `00-baseline.md` 且无 `01-requirements.md`（基线项目）时**：本 skill 创建 `01-requirements.md`，`F-001` 从这个新需求起。
存量代码不编号——基线项目的历史实现不进编号体系，只有基线之后的真实变更才有 F/US/AC。

如两者都不存在，建议：

- 新项目 → `/ms-requirements`
- 已有代码无文档 → `/ms-retrofit`（建立项目基线）

> ⛔ 这条前置条件曾写死「至少存在 `01-requirements.md`」，与 `/ms-retrofit` 的「基线已建，无需改造」
> 终态构成死循环：想加新功能 → feature 说去跑 retrofit → retrofit 说基线已建 → 回到 feature。
> 基线项目必须能从这里进入。

## 快速开始

**一句话**: 在已有 DevDocs 项目中追加新功能，自动编排需求/设计/测试/任务。

**最常见用法**: `/ms-feature "功能描述"`（自动选档位）、`/ms-feature --fast "功能描述"`

**不适合?** 新项目→`/ms-pipeline init`，修 Bug→`/ms-bugfix`，已有代码无文档→`/ms-retrofit`

## 运行模式

### 模式选择

```bash
/ms-feature "功能描述"             → 自动检测模式（Lite/Standard/Deep）
/ms-feature --lite "功能描述"      → 强制轻量模式
/ms-feature --deep "功能描述"      → 强制深度模式（强制 review + docs 验证）
/ms-feature --fast "功能描述"      → 连续执行 Step 1-5，仅最终汇总确认
/ms-feature --lite --fast "功能描述" → 轻量 + 快速组合
/ms-feature F-XX realign           → 只对齐 F-XX 关联产物（调度 system-design/test-cases/dev-tasks/dev-workflow --realign=F-XX）；共享契约见 [../pipeline/references/realign.md](../pipeline/references/realign.md)
```

### 模式对比

| 模式 | 适用场景 | 更新文档 | 上下文负载 | 验证强度 |
|------|----------|----------|------------|----------|
| 轻量模式 | 配置修改、UI 微调、简单字段 | 01 + 04 | 低 | 基础 |
| 完整模式 | 新模块、新接口 | 01 + 02 + 03 + 04 | 高（分步） | 标准 |
| 深度模式 | 跨模块架构变更、安全相关、核心数据模型 | 01 + 02 + 03 + 04 | 高（分步） | 强制 review + docs 对齐 |

### 自动模式检测（三档）

分析需求描述，按影响面推荐档位：

```text
Deep 信号（任一命中 → 深度模式）：
[ ] 跨模块依赖变更（影响 ≥2 个现有模块的边界）
[ ] 安全相关变更（认证、授权、加密、敏感数据）
[ ] 核心数据模型/表结构变更
[ ] 架构模式变更（如新增中间件层、消息队列）

Standard 信号（任一命中 → 完整模式）：
[ ] 新增 API 接口
[ ] 数据模型变更（非核心表）
[ ] 组件间依赖变化
[ ] 第三方服务集成
[ ] 新增独立模块

Lite（以上均无）→ 轻量模式
```

```markdown
# Deep 示例
检测到高影响变更：
- 跨模块：AuthModule ↔ UserModule 边界变更
- 安全相关：认证流程修改

建议使用深度模式（强制 review + docs 验证）。[深度/完整/轻量]

# Standard 示例
检测到架构变更：
- 新增接口: UserPreferenceAPI

建议使用完整模式。[完整/轻量]
```

⛔ **基线项目的首个需求强制走完整/标准档**：`docs/devdocs/00-baseline.md` 存在且无 `01-requirements.md` 时，
自动档位检测结果一律提升至标准档。轻量模式 Step 1 要读 `01-requirements.md` 取 AC 最大编号、
且约束「不新建 F-XXX 仅追加到现有功能」——基线项目两者都不成立。Lite 从第二个需求起可用。

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

- **Step 1-4 为文档阶段，仅产出 `docs/devdocs/` 下的 Markdown 文档，不编写实现代码；需要编码时必须通过 Step 6 衔接 `/ms-dev-workflow`**
- 不新建 F-XXX（功能点），仅追加 AC 到现有功能
- 不更新 02-system-design（无架构变更）
- 不更新 03-test-cases（追加任务中直接内联测试用例编号和验收标准；
  建议进入 dev-workflow 前确认 03-test-cases 中已有对应条目，
  dev-workflow 启动时会自动检测并提示补齐）
- 任务数量限制 1-3 个（可直接追加，无需调用 ms-dev-tasks）
- 任务必须遵循 TAR 原则格式

### ⚠️ 轻量模式追溯警告

轻量模式跳过 02（系统设计）和 03（测试用例）文档更新，**追溯链不完整**（F → US → AC → UT/IT/E2E 的链路在设计层和测试层断裂）。在 Step 4 用户确认时必须显示以下警告：

```
⚠️ 轻量模式跳过了设计文档和测试用例更新，追溯链不完整。
建议在开发前补齐：
  - /ms-system-design（补充设计）
  - /ms-test-cases（补充测试用例）
或切换到完整模式：/ms-feature "功能描述"
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

## 完整模式步骤详解

完整模式 Step 0-6 详细委托规范（输入/输出/确认点/子 Agent 调度）见 [references/full-mode-steps.md](references/full-mode-steps.md)。

要点摘要：
- Step 0 扫描编号 + 架构摘要
- Step 1-4 分别委托 `/ms-requirements` / `/ms-system-design` / `/ms-test-cases` / `/ms-dev-tasks`（必须 Task tool 子 Agent）
- Step 4.5 委托 `/ms-verify --readiness` 作为开发前质量关卡
- Step 5 生成 `00-feature-log.md`（模板见 [templates/feature-log-template.md](templates/feature-log-template.md)）
- Step 6 可选衔接 `/ms-dev-workflow`（深度模式自动 `--review` + 完成后 `--docs` 校验）

**编排原则**：上下文隔离 + 摘要传递 + 异常回退 + 不自行排障。

## Skill 协作

| 阶段 | 协作 Skill | 说明 |
|------|-----------|------|
| 需求追加 | `/ms-requirements` | **完整模式必须委托**（增量更新） |
| 设计追加 | `/ms-system-design` | **完整模式必须委托**（增量更新） |
| 测试追加 | `/ms-test-cases` | **完整模式必须委托**（增量更新 + 矩阵） |
| 任务追加 | `/ms-dev-tasks` | **完整模式必须委托** |
| 就绪检查 | `/ms-verify --readiness` | **完整模式必须委托**（Step 4.5 质量关卡） |
| 开发实现 | `/ms-dev-workflow` | Step 6 自动衔接（用户可跳过） |
| 编码约束 | `/code-quality`, `/testing-guide` | 编码阶段 |

> **编排器边界**：`ms-feature` 是纯编排器，负责步骤编排、确认流程、功能日志。
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
- [ ] **⛔ 禁止继续：文档阶段（Step 0-5）不得产出实现代码**（恢复方式：将代码产出移至 Step 6 dev-workflow 委托）
- [ ] **编码仅在 Step 6（dev-workflow 委托）中发生**

### 轻量模式约束

- [ ] **仅更新 01-requirements.md 和 04-dev-tasks.md**
- [ ] **不新建 F-XXX，仅追加 AC 到现有功能**
- [ ] 任务数量限制 1-3 个
- [ ] 检测到架构影响时必须提示用户
- [ ] **⛔ 禁止继续：轻量模式 Step 1-4 为文档阶段，不得编写实现代码**（恢复方式：衔接 /ms-dev-workflow）
- [ ] Write 操作仅限 `docs/devdocs/` 下的 Markdown 文档
- [ ] 需要编码时必须衔接 `/ms-dev-workflow`

### 深度模式约束（--deep）

- [ ] **dev-workflow 衔接时自动附加 `--review`**（所有任务强制对抗式验证）
- [ ] **开发完成后自动执行 `/ms-verify --docs`**（文档层间对齐）
- [ ] 检测到 Deep 信号时必须提示用户确认模式选择
- [ ] Deep 信号：跨模块边界变更、安全相关、核心数据模型、架构模式变更

### 影响分析约束

- [ ] **修改现有接口必须说明向后兼容性**
- [ ] **必须列出回归风险点**
- [ ] 高影响变更需用户确认

### 追溯约束（完整模式）

- [ ] **新增 F-XXX 必须有对应 US-XXX 和 AC-XXX**
- [ ] **新增 AC-XXX 必须有对应测试用例**
- [ ] 必须更新追溯矩阵

## 特殊情况

| 情况 | 处理 |
|------|------|
| 文档结构不完整 | 提示缺失文档，建议 `/ms-retrofit` 补全 |
| 大规模功能（>3 功能点） | 建议按模块拆分为多次迭代 |
| 需求变更（非新增） | 在原 F-XXX 下标注变更，更新 US/AC/测试，记录原因 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-feature
status: success | failed | interrupted | partial
summary:
  headline: "完整模式 Step 4 完成，新增 F-004"
  details:
    mode: lite | full
    step_reached: 1~6
    dev_workflow_triggered: true | false
blockers: []
output_files:
  - docs/devdocs/01-requirements.md
  - docs/devdocs/00-feature-log.md
new_ids:
  features: [F-004]
  stories: [US-009, US-010]
  acceptance: [AC-016~AC-020]
  tests: [UT-013~UT-015, IT-004]
  tasks: [T-11~T-13]
next_recommended:
  skill: ms-dev-workflow
  args: "T-11~T-13"
```

## 输出

更新 `01-requirements.md`、`02-system-design*.md`、`03-test-*.md`、`04-dev-tasks*.md`、`00-feature-log.md`。
