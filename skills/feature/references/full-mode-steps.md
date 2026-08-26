# ms-feature 完整模式分步详解

> 完整模式 Step 0-6 的详细委托规范，包括每步的输入、输出、确认点和子 Agent 调度细节。
>
> SKILL.md 仅保留流程图总览；本文件提供执行级细节。

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

> **委托执行**：本步骤必须委托给 `/ms-requirements --incremental`，由其负责增量需求。

### 委托输入

传递给 `/ms-requirements` 的上下文：
- 用户的新功能描述
- Step 0 扫描到的现有编号状态

### 委托输出

从 `/ms-requirements` 获取：
- 新增的 F-XXX、US-XXX、AC-XXX 编号列表
- 更新后的追溯矩阵

### ✅ 确认点（默认模式）

展示步骤摘要块（编号 + 关键变更），等待用户确认。快速档跳过此确认。

## Step 2: 设计追加（完整模式）

> **委托执行**：本步骤必须委托给 `/ms-system-design`，由其负责增量设计。

### 委托输入

传递给 `/ms-system-design` 的上下文：
- Step 1 新增的 F-XXX、US-XXX、AC-XXX 编号
- 现有架构摘要（来自 Step 0）
- 影响分析问题清单

### 委托输出

从 `/ms-system-design` 获取：
- 新增/变更的模块和接口
- 影响摘要
- 回归风险点

### ✅ 确认点（默认模式）

展示步骤摘要块（影响范围 + 兼容性结论），等待用户确认。快速档跳过此确认。

## Step 3: 测试追加（完整模式）

> **委托执行**：本步骤必须委托给 `/ms-test-cases`，由其负责增量测试设计。

### 委托输入

传递给 `/ms-test-cases` 的上下文：
- Step 1 新增的 AC-XXX 编号
- Step 2 新增的接口和模块（来自 system-design）

### 委托输出

从 `/ms-test-cases` 获取：
- 新增的 UT/IT/E2E-XXX 编号
- 更新后的追溯矩阵

### ✅ 确认点（默认模式）

展示步骤摘要块（新增测试编号 + 矩阵更新状态），等待用户确认。快速档跳过此确认。

## Step 4: 任务追加

### 调用 ms-dev-tasks

> **重要**：完整模式下，任务拆分由 `/ms-dev-tasks` 负责，确保 TAR 原则和分层 TDD 标记的一致性。

**传递给 ms-dev-tasks 的上下文**：
- 新增的 F-XXX、AC-XXX 编号
- 新增的 UT/IT/E2E-XXX 编号
- 影响的模块和接口

```text
调用 /ms-dev-tasks：
- 输入：Step 1-3 产生的新增编号
- 输出：追加到 04-dev-tasks*.md
- 遵循：TAR 原则、分层 TDD
```

### ✅ 确认点（默认模式）

展示步骤摘要块（新增任务范围 + TDD 分层标注），等待用户确认。快速档跳过此确认。

## Step 4.5: 就绪检查（完整模式）

> **委托执行**：本步骤必须委托给 `/ms-verify --readiness`，作为进入开发前的质量关卡。

### 委托输入

传递给 `/ms-verify --readiness` 的上下文：
- Step 1-4 新增的编号列表

### 委托输出

从 `/ms-verify --readiness` 获取：
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

详细模板参见 [../templates/feature-log-template.md](../templates/feature-log-template.md)

## Step 6: 衔接开发执行（可选）

完整模式下，任务分解完成后，询问用户是否继续执行开发：

```
任务分解已完成，新增 N 个开发任务（T-XX ~ T-YY）。

是否继续执行开发？[是(默认)/否]
- 是 → 自动衔接 /ms-dev-workflow T-XX~T-YY
- 否 → 结束 feature 流程，用户后续手动调用 dev-workflow
```

**默认行为**：是（继续执行）。用户选择"否"时，输出任务编号范围供后续手动调用。

**深度模式附加行为**：
- dev-workflow 自动附加 `--review`（所有任务强制对抗式验证）
- Step 6 完成后自动追加 `/ms-verify --docs`（文档层间对齐检查）

> 轻量模式同样支持 Step 6，通过委托 `/ms-dev-workflow` 衔接少量任务的开发。轻量模式自身不编写实现代码。

## 编排规范（子 Agent 调度）

完整模式下，ms-feature 调用子技能时**必须通过 Task tool 启动子 Agent**：

| Step | 被调度技能 | 调度方式 |
|------|-----------|----------|
| Step 1 | `/ms-requirements --incremental` | Task tool 子 Agent |
| Step 2 | `/ms-system-design` | Task tool 子 Agent |
| Step 3 | `/ms-test-cases` | Task tool 子 Agent |
| Step 4 | `/ms-dev-tasks` | Task tool 子 Agent |
| Step 4.5 | `/ms-verify --readiness` | Task tool 子 Agent |
| Step 6 | `/ms-dev-workflow` | Task tool 子 Agent |

### 调度原则

1. **上下文隔离**：每个子 Agent 自行读取所需文档，feature 编排层不传递全文
2. **摘要传递**：步骤间只传递 YAML 摘要 + 新增编号列表
3. **异常回退**：子 Agent 返回 `status: failed` + `blockers` 时，展示阻塞项询问用户
4. **不自行排障**：编排层不读取子技能的完整输出文档来尝试修复

> 轻量模式因任务简单，**文档步骤**（Step 1-4）直接在 feature 上下文内执行，不启动子 Agent。Step 6 开发衔接仍需委托 `/ms-dev-workflow`。
