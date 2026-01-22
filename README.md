# Skills 模板集合

面向**个人开发者**的 Claude Code Agent Skills 模板项目，包含 DevDocs 全流程和通用工具 skills。

## 语言规则

所有 skill 统一遵循：
- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

---

## 编号规范

DevDocs 流程使用统一的编号体系实现需求到测试的追溯：

| 类型 | 前缀 | 格式 | 说明 |
|------|------|------|------|
| 功能点 | F | F-XXX | 用户可感知的独立功能 |
| 用户故事 | US | US-XXX | 用户使用场景 |
| 验收标准 | AC | AC-XXX | 可量化的完成条件 |
| 单元测试 | UT | UT-XXX | 验证内部逻辑 |
| 集成测试 | IT | IT-XXX | 验证组件协作 |
| E2E 测试 | E2E | E2E-XXX | 验证用户场景 |

**追溯关系**：
```
F-001 (功能点)
  └── US-001 (用户故事)
        └── AC-001 (验收标准)
              ├── UT-001 (单元测试)
              ├── IT-001 (集成测试)
              └── E2E-001 (E2E 测试)
```

---

## 文档拆分规范

当文档过大时，按以下规则拆分：

| 文档类型 | 拆分阈值 | 拆分方式 |
|----------|----------|----------|
| 需求文档 | 300 行 或 5+ 功能点 | 主文档 + 用户故事 + NFR |
| 系统设计 | 300 行 或 10+ API | 主文档 + API 设计 + 数据模型 |
| 测试用例 | 300 行 或 30+ 用例 | 概览 + UT + IT + E2E |
| 开发任务 | 300 行 或 20+ 任务 | 概览 + 按层级拆分 |

**拆分后文件结构**：

```
docs/devdocs/
├── 01-requirements.md           # 需求主文档
├── 01-requirements-stories.md   # 用户故事详情（可选）
├── 01-requirements-nfr.md       # 非功能性需求（可选）
├── 02-system-design.md          # 设计主文档
├── 02-system-design-api.md      # API 设计详情（可选）
├── 02-system-design-data.md     # 数据模型详情（可选）
├── 03-test-cases.md             # 测试用例概览 + 追溯矩阵
├── 03-test-unit.md              # 单元测试详情（可选）
├── 03-test-integration.md       # 集成测试详情（可选）
├── 03-test-e2e.md               # E2E 测试详情（可选）
├── 04-dev-tasks.md              # 任务主文档
├── 04-dev-tasks-infra.md        # 基础设施任务（可选）
├── 04-dev-tasks-core.md         # 核心逻辑任务（可选）
├── 04-dev-tasks-api.md          # 接口层任务（可选）
└── 04-dev-tasks-test.md         # 测试任务（可选）
```

**小型项目**：如内容较少，可保持单一文件，无需拆分。

---

## Skills 概览

| Skill | 命令 | 用途 | 输出文件 |
|-------|------|------|----------|
| [需求扩写](#1-devdocs-requirements-需求扩写) | `/devdocs-requirements` | 功能点、用户故事、验收标准 | `01-requirements.md` |
| [系统设计](#2-devdocs-system-design-系统设计) | `/devdocs-system-design` | 技术架构和 API 设计（支持增量） | `02-system-design*.md` |
| [测试用例](#3-devdocs-test-cases-测试用例) | `/devdocs-test-cases` | 单元/集成/E2E 测试用例 | `03-test-*.md` |
| [开发任务](#4-devdocs-dev-tasks-开发任务) | `/devdocs-dev-tasks` | 可执行的开发任务拆分 | `04-dev-tasks*.md` |
| [项目改造](#5-devdocs-retrofit-项目改造) | `/devdocs-retrofit` | 已有项目适配 DevDocs 流程 | `00-retrofit-report.md` |
| [新功能](#14-devdocs-feature-新功能) | `/devdocs-feature` | 在已有项目中追加新功能 | `00-feature-log.md` |
| [文档同步](#15-devdocs-sync-文档同步) | `/devdocs-sync` | 同步文档与实现进度 | `progress-report.md` |
| [项目上下文](#16-devdocs-onboard-项目上下文) | `/devdocs-onboard` | AI 工具切换时的上下文传递 | `00-context.md` |
| [洞察收集](#17-devdocs-insights-洞察收集) | `/devdocs-insights` | 收集改进建议转化为需求 | `05-insights.md` |
| [Bug 修复](#13-devdocs-bugfix-bug-修复) | `/devdocs-bugfix` | 测试先行的 Bug 修复流程 | - |
| [代码质量](#6-code-quality-代码质量) | `/code-quality` | MTE 原则、重构指导、Review 清单 | - |
| [测试指导](#12-testing-guide-测试指导) | `/testing-guide` | 测试质量约束（断言、Mock、变异测试） | - |
| [重构](#10-refactor-重构) | `/refactor` | 系统化重构，测试驱动，安全可追溯 | `05-refactor-*.md` |
| [提交规范](#7-commit-convention-提交规范) | - | 提交信息格式化与历史风格同步 | - |
| [Git 安全](#11-git-safety-git-安全) | - | 强制使用 git mv/rm 规范操作 | - |
| [UI 规范](#9-ui-skills-ui-规范) | `/ui-skills` | 构建更好界面的意见约束 | - |
| [工作报告](#8-work-report-工作报告) | `/work-report` | 生成周报、月报、季报、年终总结 | `*.md` |

## DevDocs 工作流

### 路径选择

根据项目状态选择合适的开发路径：

| 场景 | 推荐路径 | 说明 |
|------|----------|------|
| 新功能开发（需求明确） | **路径 A：正向开发** | 从需求开始，逐步细化 |
| 新功能 / 功能迭代 | **`/devdocs-feature`** | 延续编号，追加文档 |
| 探索性开发 / 原型验证 | **路径 B：探索后补** | 先写代码，后补文档 |
| 已有项目规范化 | **路径 B：探索后补** | 从代码逆向生成文档 |
| Bug 修复 | **`/devdocs-bugfix`** | 测试先行，编写失败测试后修复 |
| 小型配置变更 | **直接提交** | 无需流程，遵循 commit 规范 |

---

### 路径 A：正向开发（需求驱动）

适用于需求明确的新功能开发：

```
/devdocs-requirements → /devdocs-system-design → /devdocs-test-cases → /devdocs-dev-tasks
       │                        │                        │                    │
       ▼                        ▼                        ▼                    ▼
  需求文档                  系统设计                  测试用例              开发任务
  (F/US/AC)                                         (UT/IT/E2E)
                                                                              │
                                                                              ▼
                                                                           开发实现
                                                                    ┌────────┼────────┐
                                                                    ▼        ▼        ▼
                                                              /code-quality /testing-guide /ui-skills
                                                              (代码质量)    (测试质量)      (UI 约束)
                                                                              │
                                                                              ▼
                                                                        /devdocs-sync
                                                                        (文档同步)
```

---

### 路径 B：探索后补（代码驱动）

适用于探索性开发或已有项目规范化：

```
1. 编写核心代码/原型
       │
       ▼
2. /devdocs-retrofit（逆向生成文档）
       │
       ├── 从代码提取：功能清单、API、数据模型
       ├── 从测试提取：用户故事、验收标准
       └── 生成标准化 DevDocs 文档
       │
       ▼
3. 审核补充文档
       │
       ▼
4. 补充测试用例（参考 /testing-guide）
```

**优势**：
- 避免过早设计导致的返工
- 文档基于实际代码，更准确
- 适合快速验证想法

**注意**：
- 逆向生成的文档需要人工审核
- 标记为 `[从代码推导]` 的内容需确认
- 建议在代码稳定后尽早补充文档

---

### 已有项目改造

```
/devdocs-retrofit
       │
       ├── 自动识别已有文档
       ├── 用户确认/手动指定
       ├── 代码逆向推导（无文档时）
       ├── 分析覆盖情况
       └── 生成标准化 DevDocs 文档
```

### 代码重构

```
/refactor
       │
       ├── 1. 确定范围（用户指定或系统审查）
       │
       ├── 2. 评估测试状态
       │       ├── 覆盖率 ≥80% → 直接重构
       │       ├── 覆盖率 <80% → 补充测试
       │       └── 不可测试 → 重写流程
       │
       ├── 3. 执行重构
       │       ├── 普通代码 → /code-quality
       │       └── UI 代码 → /ui-skills
       │
       └── 4. 重写流程（如需要）
               └── /devdocs-retrofit → 逆向分析 → 重新实现
```

---

## Skill 协作关系

DevDocs 流程中各 Skill 的协作关系：

| 阶段 | 主 Skill | 协作 Skill | 说明 |
|------|----------|-----------|------|
| 需求分析 | `/devdocs-requirements` | - | 定义 F/US/AC 编号 |
| 洞察收集 | `/devdocs-insights` | `/ui-skills` | 审查/调研结果转需求 |
| 系统设计 | `/devdocs-system-design` | `/code-quality` | MTE 原则指导设计 |
| 测试用例 | `/devdocs-test-cases` | `/testing-guide` | 测试质量约束 |
| 开发任务 | `/devdocs-dev-tasks` | 多个 | 见下表 |
| 文档同步 | `/devdocs-sync` | - | 保持文档与实现一致 |
| 代码重构 | `/refactor` | `/code-quality`, `/testing-guide` | 测试先行 |

### 开发阶段 Skill 协作

```
/devdocs-dev-tasks 执行任务
         │
         ├── 编码实现 ────────── /code-quality (MTE 原则)
         │
         ├── UI 实现 ─────────── /ui-skills (无障碍、动画约束)
         │
         ├── 测试编写 ────────── /testing-guide (断言质量、变异测试)
         │
         ├── 代码提交 ────────── /git-safety + /commit-convention
         │
         └── 进度同步 ────────── /devdocs-sync (文档与实现一致性)
```

### 约束执行时机

| Skill | 何时执行 | 检查内容 |
|-------|---------|----------|
| `/code-quality` | 编写/重构代码时 | 函数长度、参数数量、依赖注入 |
| `/testing-guide` | 编写测试时 | 断言质量、覆盖率、变异得分 |
| `/ui-skills` | 实现 UI 时 | 无障碍、动画性能、布局规范 |
| `/git-safety` | 文件操作时 | 使用 git mv/rm |
| `/commit-convention` | 提交代码时 | 提交信息格式 |
| `/devdocs-sync` | 任务完成后/Sprint 结束 | 文档与实现一致性 |

---

# 1. devdocs-requirements (需求扩写)

将用户简短需求扩展为详细的产品需求文档。

## 元数据

```yaml
name: devdocs-requirements
description: Expand user requirements into detailed DevDocs documents
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
```

## 触发条件

- 用户提供功能需求或想法
- 用户要求创建/编写 PRD
- 用户想要澄清或记录需求

## 工作流程

1. **理解需求**：读取用户输入
2. **探索代码库**：了解现有架构（如适用）
3. **起草需求**：创建完整需求文档
4. **用户确认**：获得用户批准

## 输出文件

```
docs/devdocs/
├── 01-requirements.md           # 主文档
├── 01-requirements-stories.md   # 用户故事（如超长）
└── 01-requirements-nfr.md       # 非功能性需求（如超长）
```

## 文档模板

```markdown
# 需求文档：<功能名称>

## 1. 需求背景
<为什么需要这个功能，解决什么问题>

## 2. 目标用户
<谁会使用这个功能，用户画像>

## 3. 核心功能点
- [ ] 功能点 1：<描述>
- [ ] 功能点 2：<描述>

## 4. 用户故事

| 编号 | 角色 | 期望 | 目的 |
|------|------|------|------|
| US-01 | 作为<角色> | 我希望<功能> | 以便于<价值> |

## 5. 验收标准
- [ ] AC-01：<可量化的标准>
- [ ] AC-02：<可量化的标准>
- [ ] AC-03：<可量化的标准>

## 6. 非功能性需求
- **性能**：<要求>
- **安全**：<要求>
- **兼容性**：<要求>

## 7. 范围边界

### 本次包含
- <内容>

### 本次不包含
- <内容>

## 8. 假设与依赖
- <前提条件>
```

## 约束

- [ ] 必须与用户确认核心功能点是否完整
- [ ] 必须定义至少 3 条验收标准
- [ ] 必须列出范围边界，避免需求蔓延
- [ ] 不得添加用户未提及且未确认的大功能
- [ ] 用户故事必须遵循 "作为...我希望...以便于..." 格式
- [ ] 验收标准必须可量化、可验证

## 下一步

完成后建议运行 `/devdocs-system-design`

---

# 2. devdocs-system-design (系统设计)

围绕需求设计详细技术方案，支持初始设计和增量设计两种模式。

## 元数据

```yaml
name: devdocs-system-design
description: Create or update system design documents (supports incremental design)
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
```

## 设计模式

| 模式 | 触发条件 | 说明 |
|------|----------|------|
| **初始设计** | 无 `02-system-design.md` | 从零创建系统设计 |
| **增量设计** | 已有设计 + 新需求/优化 | 影响分析 + 设计变更 |

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 如不存在，建议先运行 `/devdocs-requirements`

## 设计前必问（初始设计）

**必须使用 AskUserQuestion 询问用户**：

1. **技术栈偏好** - 指定技术栈 / 无偏好
2. **目标平台** - Web / Mobile / Desktop / Server / 跨平台
3. **部署环境** - 云服务 / 私有化 / 混合

如用户无偏好，则根据需求设计最优方案。

## MTE 设计原则

| 原则 | 说明 | 检查点 |
|------|------|--------|
| **Maintainability** | 可维护性 | 模块职责单一、依赖清晰 |
| **Testability** | 可测试性 | 核心逻辑可单元测试、依赖可 Mock |
| **Extensibility** | 可扩展性 | 预留扩展点、接口抽象 |

## 设计模式选择

根据场景选择合适的设计模式，**只在必要时使用**：

| 场景 | 推荐模式 | 适用情况 |
|------|----------|----------|
| 对象创建 | Factory / Builder | 复杂对象构建 |
| 行为扩展 | Strategy / Template | 算法可替换 |
| 结构组织 | Facade / Adapter | 简化接口、适配第三方 |
| 数据访问 | Repository / DAO | 数据层抽象 |

## 分层架构

```
┌─────────────────────────────────────┐
│           Interface Layer           │  ← API/Controller（薄层）
├─────────────────────────────────────┤
│           Service Layer             │  ← 业务逻辑（核心，可测试）
├─────────────────────────────────────┤
│           Domain Layer              │  ← 领域模型
├─────────────────────────────────────┤
│         Infrastructure Layer        │  ← 数据访问、外部服务（可替换）
└─────────────────────────────────────┘
```

## 输出文件

```
docs/devdocs/
├── 02-system-design.md          # 架构、技术选型、模块、接口、模式
├── 02-system-design-api.md      # API 设计（如超长）
└── 02-system-design-data.md     # 数据模型（如超长）
```

## 文档结构

1. **运行平台** - 平台、版本要求、部署环境
2. **架构概览** - 高层架构图（ASCII）
3. **技术选型** - 技术选择及理由
4. **模块划分** - 模块职责和依赖
5. **核心接口** - 关键接口和方法签名（只定义，不实现）
6. **设计模式** - 使用的模式及解决的问题
7. **代码结构** - 目录结构设计
8. **数据模型** - 实体定义和关系
9. **API 设计** - 接口定义含请求/响应示例
10. **状态流转** - 关键业务状态机
11. **异常处理** - 错误码和处理策略
12. **扩展性设计** - 扩展点和不做的设计

## 核心接口示例

> 只定义签名，不写实现代码

```markdown
#### IUserService

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `createUser` | `CreateUserDTO` | `User` | 创建用户 |
| `getUserById` | `string` | `User \| null` | 根据ID查询 |
```

## 约束

### 基础约束
- [ ] **必须先询问用户技术栈偏好和目标平台**
- [ ] 技术选型必须说明理由
- [ ] API 设计必须包含请求/响应示例
- [ ] 数据模型必须考虑索引和查询场景

### MTE 原则约束
- [ ] **每个模块职责单一**
- [ ] **核心业务逻辑必须可单元测试**
- [ ] **预留合理扩展点，但不为假设需求设计**
- [ ] 依赖方向：外层依赖内层

### 避免过度设计
- [ ] **不为"未来可能"的需求设计**
- [ ] 不创建只有一个实现的接口（除非为可测试性）
- [ ] 不过早抽象，等到有 3 个以上相似场景再抽象

### 增量设计约束
- [ ] **增量设计前必须进行影响分析**
- [ ] **必须评估向后兼容性**
- [ ] **破坏性变更必须标注处理方式**
- [ ] **必须生成设计变更记录**

## 增量设计流程

```
1. 读取现有设计
   │
   ▼
2. 识别变更来源（F-XXX / INS-XXX / 技术改进）
   │
   ▼
3. 影响分析（模块、接口、数据模型）
   │
   ▼
4. 兼容性评估
   │
   ▼
5. 设计变更 + 生成变更记录
   │
   ▼
6. 用户确认
```

## 下一步

完成后建议运行 `/devdocs-test-cases`

---

# 3. devdocs-test-cases (测试用例)

基于需求文档设计测试用例，建立验收标准与测试用例的追溯关系。

## 元数据

```yaml
name: devdocs-test-cases
description: Design test cases based on requirements
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
```

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 如不存在，建议先运行 `/devdocs-requirements`

## 核心理念

测试用例从需求推导，不是从代码推导：

```
验收标准 (AC-XXX)
    │
    ├── 单元测试 (UT-XXX)  ← 验证内部逻辑
    │
    ├── 集成测试 (IT-XXX)  ← 验证组件协作
    │
    └── E2E 测试 (E2E-XXX) ← 验证用户场景
```

## 测试类型选择

| 验收标准类型 | 推荐测试类型 | 示例 |
|--------------|--------------|------|
| 输入验证规则 | 单元测试 | "邮箱格式校验" → UT |
| 业务逻辑规则 | 单元测试 + 集成测试 | "密码加密存储" → UT + IT |
| 用户交互流程 | E2E 测试 | "完成注册流程" → E2E |
| 组件间协作 | 集成测试 | "发送验证邮件" → IT |

## 输出文件

```
docs/devdocs/
├── 03-test-cases.md           # 测试用例概览 + 追溯矩阵
├── 03-test-unit.md            # 单元测试用例
├── 03-test-integration.md     # 集成测试用例
└── 03-test-e2e.md             # E2E 测试用例
```

## 追溯矩阵

| 功能点 | 用户故事 | 验收标准 | 单元测试 | 集成测试 | E2E测试 | 状态 |
|--------|----------|----------|----------|----------|---------|------|
| F-001 | US-001 | AC-001 | UT-001 | - | E2E-001 | ✅ |
| F-001 | US-001 | AC-002 | UT-002 | - | E2E-001 | ✅ |
| F-001 | US-002 | AC-004 | UT-003, UT-004 | IT-001 | - | ✅ |

## 覆盖率要求

| 测试类型 | 覆盖目标 | 覆盖要求 |
|----------|----------|----------|
| 单元测试 | 核心业务逻辑 | 行覆盖率 ≥ 80%，分支覆盖率 ≥ 80% |
| 集成测试 | 组件协作场景 | 每个功能点至少 1 个 IT |
| E2E 测试 | 用户故事 | 每个 P0 用户故事至少 1 个 E2E |

## 约束

- [ ] **每个验收标准至少有 1 个测试用例覆盖**
- [ ] **必须生成追溯矩阵**
- [ ] 测试用例必须关联验收标准编号
- [ ] P0 验收标准必须 100% 测试覆盖
- [ ] 测试名称必须描述预期行为
- [ ] 禁止弱断言（toBeDefined, toBeTruthy 不能作为唯一断言）

## 下一步

完成后建议运行 `/devdocs-dev-tasks`

---

# 4. devdocs-dev-tasks (开发任务)

将系统设计拆解为可执行的开发任务。

## 元数据

```yaml
name: devdocs-dev-tasks
description: Break down system design into executable development tasks
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, TodoWrite, Bash
```

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 系统设计：`docs/devdocs/02-system-design.md`
- 测试用例：`docs/devdocs/03-test-cases.md`（及 `03-test-unit.md`, `03-test-integration.md`, `03-test-e2e.md`）

## TAR 原则

每个任务必须满足：

| 原则 | 说明 | 必填内容 |
|------|------|----------|
| **Testable** | 可测试 | 测试方法和预期结果 |
| **Acceptable** | 可验收 | 可量化的完成标准 |
| **Reviewable** | 可审查 | Review 检查要点 |

## 输出文件

```
docs/devdocs/
├── 04-dev-tasks.md              # 概览和依赖图
├── 04-dev-tasks-infra.md        # 基础设施任务（如超长）
├── 04-dev-tasks-core.md         # 核心逻辑任务（如超长）
├── 04-dev-tasks-api.md          # 接口层任务（如超长）
└── 04-dev-tasks-test.md         # 测试任务（如超长）
```

## 文档模板

```markdown
# 开发任务：<功能名称>

## 任务概览

- **总任务数**：X 个
- **执行顺序**：按依赖关系

## 任务设计原则

每个任务必须满足 **TAR 原则**：
- **可测试 (Testable)**：有明确的测试方法
- **可验收 (Acceptable)**：有可量化的完成标准
- **可审查 (Reviewable)**：有独立的代码审查点

## 依赖关系图

T-01 ─┬─> T-03 ─> T-05
T-02 ─┘           │
                  ▼
            T-06 ─> T-07

## 任务列表

### T-01: <任务名称>

| 属性 | 内容 |
|------|------|
| **描述** | <任务描述> |
| **依赖** | 无 |
| **优先级** | P0 |
| **关联需求** | F-001, AC-001 |
| **涉及文件** | `src/db/schema.ts` |

**编码约束**（参考 `/code-quality`）：
- [ ] 遵循 MTE 原则

**测试用例**（来自 `03-test-*.md`）：
- [ ] UT-001: AC-001 - <测试场景>

**验收标准**：
- [ ] 迁移脚本执行无错误
- [ ] 数据库表结构与设计文档一致

**Review 要点**：
- [ ] 字段类型是否正确
- [ ] 索引设计是否合理
- [ ] 是否有安全隐患

---

## 执行检查清单

| 任务 | 测试 | 验收 | Review | 提交 |
|------|------|------|--------|------|
| T-01 | [ ] | [ ] | [ ] | [ ] |
| T-02 | [ ] | [ ] | [ ] | [ ] |

## 风险项

| 任务 | 风险 | 缓解措施 |
|------|------|----------|
| T-XX | <风险> | <措施> |
```

## 任务执行流程

```
1. 开始任务
   │
   ▼
2. 编写代码（遵循 /code-quality, /ui-skills 约束）
   │
   ▼
3. 编写测试（遵循 /testing-guide 约束）
   │
   ▼
4. 执行测试用例（UT/IT/E2E-XXX）
   ├── 通过 ──────────────────┐
   └── 失败 → 修复 → 重新测试 │
                              ▼
5. 检查验收标准（AC-XXX）
   ├── 全部满足 ─────────────┐
   └── 未满足 → 补充 → 重检  │
                             ▼
6. 自查 Review 要点
   │
   ▼
7. 询问用户：是否提交代码？
   ├── 是 → 提交（遵循 /git-safety, /commit-convention）
   └── 否 → 继续修改
```

## Commit 格式

遵循 `/commit-convention` 规范：

```
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
```

**type 类型**：feat | fix | refactor | test | docs | chore

## 约束

- [ ] **单个任务必须在 4 小时内可完成**
- [ ] **必须标注任务依赖关系**
- [ ] **必须按依赖顺序排列，无循环依赖**
- [ ] **文件路径必须具体，不得写"相关文件"**
- [ ] **必须提供依赖关系图**
- [ ] 优先级：P0（阻塞）、P1（重要）、P2（一般）
- [ ] 任务 ID 格式：T-XX（顺序编号）
- [ ] **每个任务必须包含测试方法**
- [ ] **每个任务必须包含验收标准**
- [ ] **每个任务必须包含 Review 要点**
- [ ] 测试方法必须可执行
- [ ] 验收标准必须可量化
- [ ] Review 要点必须针对任务类型

---

# 5. devdocs-retrofit (项目改造)

将已有工程改造为 DevDocs 流程，或将旧版 DevDocs 迁移到新规范。

## 元数据

```yaml
name: devdocs-retrofit
description: Retrofit existing projects or migrate old DevDocs to new standards
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash
```

## 触发条件

- 用户希望将现有项目适配 DevDocs 流程
- 用户需要标准化项目文档
- 用户要迁移或升级已有 DevDocs 文档
- 项目缺少文档，需要从代码逆向生成

## 工作流程

```
1. 扫描项目结构
   │
   ▼
2. 检测项目状态
   │
   ├── 无 DevDocs → 新项目改造流程
   │
   ├── 有 DevDocs（旧版）→ 版本迁移流程
   │
   └── 有 DevDocs（符合规范）→ 无需改造
```

## 版本迁移流程

当检测到旧版 DevDocs 文档时：

```
1. 规范符合性检查
   │
   ▼
2. 生成迁移差异清单
   │
   ▼
3. 用户确认迁移计划
   │
   ▼
4. 执行迁移（编号、重命名、追溯矩阵）
```

### 规范检查清单

| 检查项 | 规范要求 |
|--------|----------|
| 编号体系 | F-XXX, US-XXX, AC-XXX |
| 测试编号 | UT-XXX, IT-XXX, E2E-XXX |
| 追溯矩阵 | F → US → AC → 测试 |
| 文件命名 | 03-test-cases.md（非 test-plan） |

## 新项目改造流程

当项目没有 DevDocs 文档时：

```
1. 自动识别已有文档
   │
   ▼
2. 用户确认/手动指定/代码逆向推导
   │
   ▼
3. 生成 DevDocs 文档（含编号）
   │
   ▼
4. 生成改造报告
```

## 输出文件

```
docs/devdocs/
├── 00-retrofit-report.md    # 改造报告
├── 01-requirements.md       # 需求文档（含 F/US/AC 编号）
├── 02-system-design.md      # 系统设计
├── 03-test-cases.md         # 测试用例概览 + 追溯矩阵
├── 03-test-unit.md          # 单元测试（含 UT-XXX）
├── 03-test-integration.md   # 集成测试（含 IT-XXX）
├── 03-test-e2e.md           # E2E 测试（含 E2E-XXX）
└── 04-dev-tasks.md          # 开发任务（含 T-XX）
```

## 约束

- [ ] **必须先检测项目状态（无 DevDocs / 旧版 / 符合规范）**
- [ ] **迁移前必须生成差异清单并用户确认**
- [ ] **必须为所有内容分配编号（F/US/AC/UT/IT/E2E）**
- [ ] 文件重命名必须使用 `git mv`
- [ ] 不得删除原有文档的有效内容
- [ ] 必须生成改造报告

详见 [devdocs-retrofit/SKILL.md](devdocs-retrofit/SKILL.md)。

---

# 6. code-quality (代码质量)

编码和重构时的质量约束，确保代码可维护、可测试、适度扩展。

## 元数据

```yaml
name: code-quality
description: Opinionated constraints for writing maintainable, testable code
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
```

## 触发条件

- 用户正在编写新代码
- 用户需要重构现有代码
- 用户需要 Code Review 检查清单
- 用户提到 MTE 原则、代码质量、避免过度设计

## 核心原则：MTE

| 原则 | 说明 | 检查点 |
|------|------|--------|
| **Maintainability** | 可维护性 | 职责单一、依赖清晰、易于理解 |
| **Testability** | 可测试性 | 核心逻辑可单元测试、依赖可 Mock |
| **Extensibility** | 可扩展性 | 预留合理扩展点、接口抽象 |

## 应用场景

### 编码约束

- 函数不超过 50 行
- 参数不超过 5 个
- 嵌套不超过 3 层
- 依赖通过注入
- 核心逻辑可测试

### 重构指导

- 重构前必须有测试
- 每步重构后运行测试
- 不在重构中添加功能
- 识别 Code Smells 并修复

### Code Review 清单

- MTE 原则检查
- 代码规范检查
- 错误处理检查
- 安全检查

## 约束

- [ ] **函数不超过 50 行**
- [ ] **参数不超过 5 个**
- [ ] **嵌套不超过 3 层**
- [ ] **每个模块职责单一**
- [ ] **不为假设需求设计**
- [ ] **重构前必须有测试**

---

# 7. commit-convention (提交规范)

提供提交信息的格式化标准。优先学习并沿用项目已有的提交历史风格，若无明显风格或为新项目，则遵循 Conventional Commits 规范。

## 元数据

```yaml
name: commit-convention
description: Git 提交信息规范。优先学习并沿用项目已有的提交历史风格。
user-invocable: false
```

## 核心策略

1. **风格学习**：生成信息前先执行 `git log -n 5 --oneline` 观察习惯。
2. **规范回退**：无规律时遵循 Conventional Commits (`type(scope): subject`)。
3. **决策指导**：该 Skill 不执行 `git commit`，仅为 Agent 提供信息生成的建议。

## 约束

- [ ] 必须先观察 `git log`
- [ ] 优先匹配历史记录的语言和前缀风格
- [ ] 仅提供建议，不直接执行提交命令

---

# 8. work-report (工作报告)

生成周报、月报、季度报和年终总结。

## 元数据

```yaml
name: work-report
description: 生成周报、月报、季度报和年终总结
allowed-tools: Read, Bash, Write, Glob, Grep, AskUserQuestion
```

## 触发条件

- 用户提到"周报"、"月报"、"季报"、"年终总结"
- 用户需要生成工作报告

## 报告类型

| 类型 | 时间范围 | 输入来源 | 主要内容 |
|------|---------|---------|---------|
| 周报 | 本周 | 每日工作记录/口述 | 本周工作、下周计划 |
| 月报 | 当月 | 周报汇总 | 主要工作、进度跟踪 |
| 季报 | 当季 | 周报汇总 | 季度总结、阶段成果 |
| 年终总结 | 全年 | 周报汇总 | 业绩达成、个人成长、成长计划 |

## 工作流程

```
1. 确定报告类型和时间范围
   │
   ▼
2. 收集必要信息（周报文件、规划文档等）
   │
   ▼
3. 读取并解析文件
   │
   ▼
4. 分析周报内容，提取关键工作
   │
   ▼
5. 根据报告类型生成内容
   │
   ▼
6. 输出 Markdown 文件
```

## 输出模板

- **周报**：固定格式，包含本周重点工作和下周计划
- **月报/季报**：灵活格式，突出重点工作和进度
- **年终总结**：固定格式，包含业绩达成（1500-3000字）、个人成长（400-700字）、成长计划（400-700字）

## 约束

- [ ] 必须确认报告类型和时间范围
- [ ] 必须向用户确认信息来源
- [ ] 客观呈现，用事实和数据说话
- [ ] 根据用户指引调整重点和弱化内容

---

# 9. ui-skills (UI 规范)

构建更好界面的意见约束。在 DevDocs 流程开发阶段实现 UI 相关任务时应用此 skill。

## 元数据

```yaml
name: ui-skills
description: Opinionated constraints for building better interfaces with agents
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
```

## 触发条件

- DevDocs 开发阶段涉及 UI 实现
- 用户要求优化 UI/UX
- 用户要求构建新界面
- 涉及 CSS、布局、动画等前端开发任务

## 在 DevDocs 流程中的位置

```
/devdocs-dev-tasks → 开发实现 → /ui-skills (UI 相关任务)
                             → /code-quality (代码质量)
```

## 核心规范

详见 [ui-skills/SKILL.md](ui-skills/SKILL.md)。

---

# 10. refactor (重构)

系统化重构 skill，确保重构过程安全、可追溯、符合质量标准。

## 元数据

```yaml
name: refactor
description: Systematic refactoring with test coverage requirements
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, TodoWrite
```

## 触发条件

- 用户需要重构现有代码
- 用户要求优化代码质量
- 用户提到技术债、代码改造

## 核心流程

```
1. 确定范围 → 2. 评估测试 → 3. 补充测试 → 4. 执行重构 → 5. 验证报告
                   │
                   └── 不可测试 → /devdocs-retrofit → 重写
```

## 重构原则

- **测试先行**：覆盖率 ≥80% 才能开始重构
- **小步迭代**：每步重构后运行测试
- **不加功能**：重构过程中不添加新功能
- **可追溯**：生成重构报告

## 与其他 Skills 协作

| 场景 | 协作 Skill |
|------|------------|
| 代码不可测试 | `/devdocs-retrofit` |
| UI 重构 | `/ui-skills` |
| 代码质量检查 | `/code-quality` |

## 输出文件

```
docs/devdocs/
├── 05-refactor-audit.md     # 代码审查报告
├── 05-refactor-plan.md      # 重构计划
└── 05-refactor-report.md    # 重构报告
```

## 约束

- [ ] **重构前测试覆盖率必须 ≥80%**
- [ ] **每步重构后运行测试**
- [ ] **重构后所有测试必须通过**
- [ ] **不得在重构中添加新功能**
- [ ] UI 重构必须应用 `/ui-skills`
- [ ] 代码重构必须应用 `/code-quality`

详见 [refactor/SKILL.md](refactor/SKILL.md)。

---

# 11. git-safety (Git 安全)

强制要求在 Git 仓库中使用原生命令进行文件操作，确保历史完整性。

## 元数据

```yaml
name: git-safety
description: 强制使用 git mv/rm 规范操作。
```

## 核心准则

1. **移动/重命名**：必须使用 `git mv`。
2. **删除**：必须使用 `git rm`。
3. **自检**：操作前通过 `git ls-files` 确认文件是否受控。

---

# 12. testing-guide (测试指导)

编写高质量测试的约束规范，确保测试真正验证行为而非仅仅覆盖代码。

## 元数据

```yaml
name: testing-guide
description: Opinionated constraints for writing effective tests
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
```

## 触发条件

- 用户正在编写测试代码
- 用户需要测试策略指导
- 用户提到测试覆盖率、断言、变异测试
- Code Review 中涉及测试代码

## 核心理念

### 测试质量金字塔

```
Level 3: 测试有效性（最高标准）
  - 变异得分 ≥ 80%
  - 需求-测试追溯 100%

Level 2: 断言质量（核心要求）
  - 禁止弱断言
  - 测试名称描述预期行为

Level 1: 代码覆盖（基础门槛）
  - 行/分支覆盖率 ≥ 80%
  - ⚠️ 必要但不充分
```

### 关键约束

| 约束 | 说明 |
|------|------|
| **测试依据来自需求** | 从需求推导测试，不是从代码推导 |
| **禁止弱断言** | `toBeDefined()`, `toBeTruthy()` 不能作为唯一断言 |
| **测试命名规范** | `[方法] 应该 [行为] 当 [条件]` |
| **Mock 只用于外部依赖** | 不 Mock 内部实现 |
| **变异测试验证** | 推荐使用 Stryker/mutmut 验证测试有效性 |

## 与其他 Skills 的关系

```
/devdocs-test-cases →  设计测试用例文档（what to test）
/testing-guide      →  指导如何写测试（how to test）
/code-quality       →  确保代码可测试性（testability）
/refactor           →  重构前验证测试覆盖
```

## 输出文件

```
testing-guide/
├── SKILL.md                              # 主文件（核心规范）
└── templates/
    ├── mutation-testing.md               # 变异测试配置（JS/TS/Python/Java/Go/C#/Rust）
    └── traceability-matrix.md            # 需求追溯矩阵模板
```

详见 [testing-guide/SKILL.md](testing-guide/SKILL.md)。

---

# 13. devdocs-bugfix (Bug 修复)

测试先行的 Bug 修复流程，确保每个修复都有回归测试保护。

## 元数据

```yaml
name: devdocs-bugfix
description: Test-first bug fixing workflow
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
```

## 触发条件

- 用户报告 Bug 或问题
- 用户提到"修复"、"bug"、"崩溃"、"报错"
- 用户提供 Issue 编号

## 核心流程

```
1. 理解 Bug
   │
   ▼
2. 定位代码
   │
   ▼
3. 编写失败测试（证明 Bug 存在）
   │
   ├── 测试通过 → ⚠️ Bug 未复现
   └── 测试失败 → ✅ 继续
   │
   ▼
4. 修复代码
   │
   ▼
5. 运行测试（测试通过 = 修复完成）
   │
   ▼
6. 提交 fix(<scope>): <description>
```

## 核心原则

```
先证明 Bug 存在（失败测试），再修复代码，最后证明 Bug 已修复（测试通过）。
```

## 约束

- [ ] **必须先编写失败测试，再修复代码**
- [ ] 测试名称描述 Bug 场景
- [ ] 提交信息使用 `fix(<scope>):` 前缀
- [ ] 关联 Issue 编号（如有）

## 与其他 Skills 协作

| 场景 | 协作 Skill |
|------|-----------|
| 测试编写 | `/testing-guide` |
| 代码修改 | `/code-quality` |
| 提交信息 | `/commit-convention` |

详见 [devdocs-bugfix/SKILL.md](devdocs-bugfix/SKILL.md)。

---

# 14. devdocs-feature (新功能)

在已有 DevDocs 项目中追加新功能，确保编号延续、文档一致。

## 元数据

```yaml
name: devdocs-feature
description: Add new features to existing DevDocs projects
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
```

## 触发条件

- 用户要在已有项目中添加新功能
- 用户提到"新功能"、"迭代"、"新增功能"
- 用户要求扩展现有功能

## 核心流程

```
1. 扫描现有文档（获取最大编号）
   │
   ▼
2. 收集增量需求
   │
   ▼
3. 影响分析（是否修改现有设计）
   │
   ▼
4. 追加文档（延续编号）
   │
   ├── 01-requirements.md → 追加 F/US/AC
   ├── 02-system-design*.md → 追加/修改设计
   ├── 03-test-*.md → 追加测试用例
   └── 04-dev-tasks*.md → 追加任务
   │
   ▼
5. 生成增量日志
```

## 核心原则

```
新功能开发 = 延续编号 + 追加文档 + 影响分析 + 回归保护
```

## 约束

- [ ] **必须延续现有编号，不得重复**
- [ ] **追加内容必须标注增量版本和日期**
- [ ] **不得删除或覆盖现有内容**
- [ ] 修改现有接口必须说明向后兼容性

## 输出文件

- 更新 `01-requirements.md`（追加）
- 更新 `02-system-design*.md`（追加/修改）
- 更新 `03-test-*.md`（追加）
- 更新 `04-dev-tasks*.md`（追加）
- 更新/创建 `00-feature-log.md`（功能日志）

详见 [devdocs-feature/SKILL.md](devdocs-feature/SKILL.md)。

---

# 15. devdocs-sync (文档同步)

保持 DevDocs 文档与实际实现进度一致，检测偏差并更新状态。

## 元数据

```yaml
name: devdocs-sync
description: Sync documentation with implementation progress
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
```

## 触发条件

- 用户完成一个或多个开发任务后
- 用户要求检查文档与代码一致性
- 用户需要更新文档进度
- Sprint 结束时定期同步

## 核心流程

```
1. 读取 DevDocs 文档
   │
   ▼
2. 扫描代码库（文件、测试、git 提交）
   │
   ▼
3. 对比分析
   │
   ▼
4. 生成偏差报告
   │
   ▼
5. 用户确认更新
   │
   ▼
6. 更新文档
```

## 偏差类型

| 类型 | 说明 | 处理建议 |
|------|------|----------|
| 文档有，代码无 | 任务定义但未实现 | 继续开发 或 移除任务 |
| 代码有，文档无 | 实现未记录 | 补充文档 |
| 实现与设计不一致 | 接口签名变更等 | 更新文档 或 修改实现 |

## 输出文件

```
docs/devdocs/
└── progress-report.md    # 进度报告
```

## 同步命令

```bash
# 快速检查（不更新文档）
/devdocs-sync check

# 完整同步（检查 + 更新文档）
/devdocs-sync

# 强制归档已完成任务
/devdocs-sync --archive
```

## 任务归档

同步时自动检测：
- 已完成任务超过 15 个 → 建议归档
- 归档按功能点 (F-XXX) 分组
- 主文档保留最近完成的 5 个任务

## 约束

- [ ] **必须读取所有 DevDocs 文档后再进行检查**
- [ ] **必须生成偏差报告**
- [ ] **更新文档前必须询问用户确认**
- [ ] 不自动删除文档内容，只标记状态
- [ ] 不自动修改代码，只更新文档

## 与其他 Skills 协作

| 场景 | 协作 Skill |
|------|-----------|
| 任务完成后 | `/devdocs-dev-tasks` |
| 需求变更 | `/devdocs-feature` |
| Bug 修复 | `/devdocs-bugfix` |
| 项目改造 | `/devdocs-retrofit` |

详见 [devdocs-sync/SKILL.md](devdocs-sync/SKILL.md)。

---

# 16. devdocs-onboard (项目上下文)

生成项目上下文摘要，帮助 AI 工具或团队成员快速了解项目并接手工作。

## 元数据

```yaml
name: devdocs-onboard
description: Generate project context summary for AI tool handover
allowed-tools: Read, Glob, Grep, Write, AskUserQuestion
```

## 触发条件

- 用户切换 AI 工具，需要传递上下文
- 用户开始新的对话会话
- 团队成员需要了解项目
- 用户要求生成项目简报

## 核心流程

```
1. 扫描 DevDocs 文档
   │
   ▼
2. 提取关键信息
   ├── 项目概述
   ├── 技术架构
   ├── 当前进度
   └── 待办任务
   │
   ▼
3. 扫描代码库结构
   │
   ▼
4. 生成上下文摘要
```

## 输出文件

```
docs/devdocs/
└── 00-context.md    # 项目上下文（可直接传递给新 AI）
```

## 上下文内容

| 章节 | 内容 | 来源 |
|------|------|------|
| 项目概述 | 目标、核心功能、技术栈 | `01-requirements.md`, `02-system-design.md` |
| 系统架构 | 架构图、核心模块、关键接口 | `02-system-design.md` |
| 代码结构 | 目录结构、关键文件 | 代码库扫描 |
| 当前进度 | 完成率、进行中任务、未提交变更 | `04-dev-tasks.md`, `git status` |
| 待办任务 | 下一步任务、阻塞项 | `04-dev-tasks.md` |
| 快速开始 | 环境准备、运行命令 | `package.json`, `Makefile` |

## 使用场景

```bash
# 标准模式：生成上下文文件
/devdocs-onboard

# 快速模式：仅显示摘要
/devdocs-onboard --quick

# 完整模式：包含更多细节
/devdocs-onboard --full
```

## 约束

- [ ] **必须扫描所有 DevDocs 文档**
- [ ] **必须检查当前代码库状态**
- [ ] **输出文件必须自包含**（新 AI 读取后能立即工作）
- [ ] 敏感信息不得包含
- [ ] 必须列出下一步可执行的任务

## 与其他 Skills 协作

| 场景 | 协作 Skill |
|------|-----------|
| DevDocs 不存在 | `/devdocs-retrofit` |
| 进度信息过时 | `/devdocs-sync` |

详见 [devdocs-onboard/SKILL.md](devdocs-onboard/SKILL.md)。

---

# 17. devdocs-insights (洞察收集)

收集来自 UI/UX 审查、文档调研、外部参考等来源的改进建议，经用户确认后转化为开发需求。

## 元数据

```yaml
name: devdocs-insights
description: Collect improvement insights from UI/UX reviews, document research, or external references
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, WebFetch
```

## 触发条件

- 用户完成 UI/UX 审查，有优化建议
- 用户调研了文档/方案，发现可借鉴点
- 用户发现外部参考（竞品、最佳实践）可借鉴
- 用户有改进想法需要转化为需求

## 洞察来源

| 来源 | 说明 | 示例 |
|------|------|------|
| 🎨 UI/UX 审查 | 界面问题、交互优化 | 按钮对比度不足、缺少加载状态 |
| 📄 文档调研 | 技术方案、设计模式 | 采用 React Query、引入乐观更新 |
| 🔍 外部参考 | 竞品分析、最佳实践 | 参考 Notion 的拖拽交互 |
| 💡 内部反馈 | 用户反馈、团队建议 | 列表加载慢需要虚拟滚动 |

## 核心流程

```
1. 识别洞察来源
   │
   ▼
2. 收集/整理建议（INS-XXX）
   │
   ▼
3. 用户确认（AskUserQuestion）
   │
   ▼
4. 转化为需求（追加到 01-requirements.md）
   │
   ▼
5. 建议后续流程
```

## 建议格式

```markdown
### INS-001: <建议标题>

| 属性 | 内容 |
|------|------|
| **来源** | 🎨 UI/UX 审查 |
| **参考** | <来源链接或描述> |
| **现状** | <当前问题> |
| **建议** | <改进建议> |
| **优先级** | P1 |
| **状态** | ⏳ 待确认 |
```

## 输出文件

```
docs/devdocs/
├── 05-insights.md       # 洞察记录（可选）
└── 01-requirements.md   # 确认后追加需求
```

## 使用示例

```bash
# 标准模式：交互式收集和确认
/devdocs-insights

# 从 URL 提取建议
/devdocs-insights --url <url>

# 快速模式：直接输入建议列表
/devdocs-insights --quick
```

## 约束

- [ ] **所有建议必须经过用户确认才能转化**
- [ ] **必须标明建议来源**
- [ ] **转化后的需求必须可追溯到原始建议**
- [ ] 拒绝的建议必须记录原因
- [ ] 单次收集建议不超过 10 条

## 与其他 Skills 协作

| 场景 | 协作 Skill |
|------|-----------|
| UI/UX 审查来源 | `/ui-skills` |
| 确认后设计 | `/devdocs-system-design` |
| 确认后开发 | `/devdocs-dev-tasks` |
| Bug 类建议 | `/devdocs-bugfix` |

详见 [devdocs-insights/SKILL.md](devdocs-insights/SKILL.md)。

---

# 项目结构

```
skills/
├── README.md                           # 本文档
├── agent-skill.md                      # Skill 规范参考
├── devdocs-requirements/
│   ├── SKILL.md
│   └── templates/
│       └── requirements-template.md
├── devdocs-system-design/
│   ├── SKILL.md
│   └── templates/
│       └── design-template.md
├── devdocs-test-cases/
│   ├── SKILL.md
│   └── templates/
│       ├── test-cases-template.md
│       ├── unit-test-template.md
│       ├── integration-test-template.md
│       └── e2e-test-template.md
├── devdocs-dev-tasks/
│   └── SKILL.md
├── devdocs-retrofit/
│   └── SKILL.md
├── devdocs-bugfix/
│   └── SKILL.md
├── devdocs-feature/
│   └── SKILL.md
├── devdocs-sync/
│   └── SKILL.md
├── devdocs-onboard/
│   └── SKILL.md
├── devdocs-insights/
│   └── SKILL.md
├── code-quality/
│   └── SKILL.md
├── testing-guide/
│   ├── SKILL.md
│   └── templates/
│       ├── mutation-testing.md
│       └── traceability-matrix.md
├── refactor/
│   └── SKILL.md
├── git-safety/
│   └── SKILL.md
├── commit-convention/
│   └── SKILL.md
├── ui-skills/
│   └── SKILL.md
└── work-report/
    ├── SKILL.md
    └── templates/
        ├── weekly-report.md
        └── year-end.md
```

---

# 使用方式

## 安装

将 skill 目录复制到：
- 个人使用：`~/.claude/skills/`
- 项目使用：`.claude/skills/`

## 调用

直接输入命令或使用触发词：

```
/devdocs-requirements 我需要一个用户登录功能
/devdocs-system-design
/devdocs-test-cases
/devdocs-dev-tasks
/devdocs-retrofit
/devdocs-feature
/devdocs-sync
/devdocs-onboard
/devdocs-insights
/devdocs-bugfix
/code-quality
/testing-guide
/refactor
/ui-skills
/work-report
```

或自然语言触发：

```
帮我写一个用户注册的需求文档
设计一下系统架构
写测试用例
拆分开发任务
把这个项目按 DevDocs 流程改造一下
添加一个新功能
同步一下文档进度
检查文档和代码是否一致
生成项目上下文
帮我了解这个项目
我审查了界面，有一些优化建议
这篇文章有些可以借鉴的地方
帮我重构这段代码
重构 UserService
Review 一下这个 PR
提交代码
帮我生成本周的周报
```
