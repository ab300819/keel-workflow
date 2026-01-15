# Skills 模板集合

Claude Code Agent Skills 模板项目，包含 DevDocs 全流程和通用工具 skills。

## 语言规则

所有 skill 统一遵循：
- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

---

## Skills 概览

| Skill | 命令 | 用途 | 输出文件 |
|-------|------|------|----------|
| [需求扩写](#1-devdocs-requirements-需求扩写) | `/devdocs-requirements` | 将需求扩展为详细文档 | `01-requirements.md` |
| [系统设计](#2-devdocs-system-design-系统设计) | `/devdocs-system-design` | 技术架构和 API 设计 | `02-system-design*.md` |
| [测试方案](#3-devdocs-test-plan-测试方案) | `/devdocs-test-plan` | 单元/E2E/手动测试用例 | `03-test-*.md` |
| [开发任务](#4-devdocs-dev-tasks-开发任务) | `/devdocs-dev-tasks` | 可执行的开发任务拆分 | `04-dev-tasks*.md` |
| [项目改造](#5-devdocs-retrofit-项目改造) | `/devdocs-retrofit` | 已有项目适配 DevDocs 流程 | `00-retrofit-report.md` |
| [代码质量](#6-code-quality-代码质量) | `/code-quality` | MTE 原则、重构指导、Review 清单 | - |
| [测试指导](#12-testing-guide-测试指导) | `/testing-guide` | 测试质量约束（断言、Mock、变异测试） | - |
| [重构](#10-refactor-重构) | `/refactor` | 系统化重构，测试驱动，安全可追溯 | `05-refactor-*.md` |
| [提交规范](#7-commit-convention-提交规范) | - | 提交信息格式化与历史风格同步 | - |
| [Git 安全](#11-git-safety-git-安全) | - | 强制使用 git mv/rm 规范操作 | - |
| [UI 规范](#9-ui-skills-ui-规范) | `/ui-skills` | 构建更好界面的意见约束 | - |
| [工作报告](#8-work-report-工作报告) | `/work-report` | 生成周报、月报、季报、年终总结 | `*.md` |

## DevDocs 工作流

### 新项目

```
/devdocs-requirements → /devdocs-system-design → /devdocs-test-plan → /devdocs-dev-tasks
       │                        │                        │                    │
       ▼                        ▼                        ▼                    ▼
  需求文档                  系统设计                  测试方案              开发任务
                                                                              │
                                                                              ▼
                                                                           开发实现
                                                                    ┌────────┼────────┐
                                                                    ▼        ▼        ▼
                                                              /code-quality /testing-guide /ui-skills
                                                              (代码质量)    (测试质量)      (UI 约束)
```

### 已有项目改造

```
/devdocs-retrofit
       │
       ├── 自动识别已有文档
       ├── 用户确认/手动指定
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

围绕需求设计详细技术方案，考虑可维护性、可测试性和适度扩展性。

## 元数据

```yaml
name: devdocs-system-design
description: Create system design documents based on requirements
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
```

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 如不存在，建议先运行 `/devdocs-requirements`

## 设计前必问

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

## 下一步

完成后建议运行 `/devdocs-test-plan`

---

# 3. devdocs-test-plan (测试方案)

创建完整的测试方案，包含单元测试、UI 自动化、手动测试和上线回归。

## 元数据

```yaml
name: devdocs-test-plan
description: Create comprehensive test plans including unit tests, UI automation, and manual test cases
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
```

## 前置条件

- 需求文档：`docs/devdocs/01-requirements.md`
- 系统设计：`docs/devdocs/02-system-design.md`

## 测试策略

| 测试类型 | 覆盖范围 | 覆盖要求 |
|----------|----------|----------|
| 单元测试 | 核心业务逻辑 | 行覆盖率 ≥ 80%，分支覆盖率 ≥ 80% |
| UI 自动化 | 核心用户场景 | 覆盖所有 P0 场景 |
| 手动测试 | 全部场景 | 覆盖所有验收标准 |

## 输出文件

```
docs/devdocs/
├── 03-test-plan.md          # 测试策略概览和覆盖矩阵
├── 03-test-unit.md          # 单元测试用例和 Mock 策略
├── 03-test-e2e.md           # UI 自动化测试用例
├── 03-test-manual.md        # 手动测试用例
└── 03-test-regression.md    # 上线前回归检查清单
```

## 单元测试方案

### 覆盖率要求
- **行覆盖率**：≥ 80%
- **分支覆盖率**：≥ 80%

### 用例格式

| 用例ID | 测试函数 | 场景 | 输入 | 预期输出 |
|--------|----------|------|------|----------|
| UT-001 | `functionName()` | 正常情况 | `{input}` | `{output}` |

### Mock 策略

| 依赖 | Mock 方式 | 说明 |
|------|-----------|------|
| 数据库 | Mock | 使用内存 Mock |
| 外部 API | Stub | 返回预定义响应 |

## UI 自动化测试方案

### 核心场景覆盖

| 用例ID | 场景名称 | 操作步骤 | 断言点 | 优先级 |
|--------|----------|----------|--------|--------|
| E2E-001 | <场景> | 1. xxx<br>2. xxx | <断言> | P0 |

## 手动测试用例

### 分类

| 分类 | 用例ID前缀 | 说明 |
|------|------------|------|
| 正向测试 | TC-P-XXX | 正常业务流程 |
| 反向测试 | TC-N-XXX | 异常输入和错误处理 |
| 边界测试 | TC-B-XXX | 边界值和极限情况 |
| 兼容性测试 | TC-C-XXX | 跨浏览器/设备 |
| 安全测试 | TC-S-XXX | 基础安全验证 |

## 上线前回归步骤

### 回归检查清单

| # | 检查项 | 执行方式 | 通过标准 | 责任人 |
|---|--------|----------|----------|--------|
| 1 | 代码合并 | 手动 | PR 已合并，无冲突 | 开发 |
| 2 | 单元测试 | CI 自动 | 全部通过，覆盖率达标 | 开发 |
| 3 | UI 自动化 | CI 自动 | 全部 P0 用例通过 | QA |
| 4 | 核心功能验证 | 手动 | P0 用例全部通过 | QA |
| 5 | 兼容性验证 | 手动 | 主流环境无异常 | QA |
| 6 | 性能验证 | 自动/手动 | 达到性能指标 | 开发 |
| 7 | 安全检查 | 自动 | 无高危漏洞 | 开发 |

### 回滚条件

| 级别 | 触发条件 | 回滚策略 |
|------|----------|----------|
| P0 | 核心功能不可用 | 立即回滚 |
| P1 | 严重影响用户体验 | 评估后决定 |
| P2 | 轻微问题 | 热修复 |

### 上线后验证

- [ ] 冒烟测试通过
- [ ] 核心监控指标正常
- [ ] 错误日志无异常增长
- [ ] 用户反馈渠道监控

## 约束

- [ ] **单元测试必须覆盖核心业务逻辑，行覆盖率 ≥ 80%，分支覆盖率 ≥ 80%**
- [ ] **UI 自动化测试必须覆盖所有 P0 场景**
- [ ] 手动测试用例覆盖所有验收标准
- [ ] 每个核心功能点至少 1 个正向用例
- [ ] 每个用户输入至少 1 个反向用例
- [ ] 必须提供验收标准覆盖矩阵
- [ ] 优先级标注：P0（阻塞）、P1（重要）、P2（一般）
- [ ] 用例步骤必须可执行，不得含糊
- [ ] 单元测试必须说明 Mock 策略
- [ ] **必须包含上线前回归检查清单**
- [ ] **必须定义回滚条件和上线后验证项**

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
- 测试方案：`docs/devdocs/03-test-plan.md`

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
| **涉及文件** | `src/db/schema.ts` |

**测试方法**：
- [ ] 运行数据库迁移脚本
- [ ] 验证表结构创建成功

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
2. 编写代码
   │
   ▼
3. 执行测试方法
   ├── 通过 ──────────────────┐
   └── 失败 → 修复 → 重新测试 │
                              ▼
4. 检查验收标准
   ├── 全部满足 ─────────────┐
   └── 未满足 → 补充 → 重检  │
                             ▼
5. 自查 Review 要点
   │
   ▼
6. 询问用户：是否提交代码？
   ├── 是 → git add & commit
   └── 否 → 继续修改
```

## Commit 格式

```
feat(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

测试: <测试结果>
验收: <验收状态>
```

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

将已有工程按 DevDocs 流程改造，自动识别或手动指定各阶段文档。

## 元数据

```yaml
name: devdocs-retrofit
description: Retrofit existing projects to DevDocs workflow
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash
```

## 触发条件

- 用户希望将现有项目适配 DevDocs 流程
- 用户需要标准化项目文档
- 用户要迁移或整理已有文档

## 工作流程

```
1. 扫描项目结构
   │
   ▼
2. 自动识别已有文档
   │
   ▼
3. 用户确认/手动指定
   │
   ▼
4. 分析文档覆盖情况
   │
   ▼
5. 生成改造计划
   │
   ▼
6. 逐阶段执行改造
   │
   ▼
7. 生成改造报告
```

## 文档识别规则

| DevDocs 阶段 | 识别关键词 | 常见文件名 |
|----------|------------|------------|
| 需求文档 | requirement, PRD, 需求, spec | `*requirement*.md`, `*prd*.md` |
| 系统设计 | design, architecture, 设计 | `*design*.md`, `*architecture*.md` |
| 测试方案 | test, QA, 测试 | `*test*.md`, `*qa*.md` |
| 开发任务 | task, todo, 任务 | `*task*.md`, `*todo*.md` |

## 改造模式

| 模式 | 说明 |
|------|------|
| **完整改造** | 按 DevDocs 模板重新生成所有文档 |
| **增量补充** | 保留原有内容，仅补充缺失部分 |
| **仅标准化** | 保留内容，调整格式和结构 |

## 输出文件

```
docs/devdocs/
├── 00-retrofit-report.md    # 改造报告
├── 01-requirements.md       # 需求文档（新建或补充）
├── 02-system-design.md      # 系统设计（新建或补充）
├── 03-test-plan.md          # 测试方案（新建或补充）
└── 04-dev-tasks.md          # 开发任务（新建或补充）
```

## 约束

- [ ] 必须扫描常见文档目录
- [ ] 识别结果必须让用户确认
- [ ] 支持用户手动指定/修正
- [ ] **不得删除原有文档的有效内容**
- [ ] 缺失内容标注 `[待补充]`
- [ ] 必须生成改造报告

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
/devdocs-test-plan  →  生成测试计划文档（what to test）
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

# 项目结构

```
skills/
├── README.md                           # 本文档
├── agent-skill.md                      # Skill 规范参考
├── devdocs-requirements/
│   └── SKILL.md
├── devdocs-system-design/
│   ├── SKILL.md
│   └── templates/
│       └── design-template.md
├── devdocs-test-plan/
│   ├── SKILL.md
│   └── templates/
│       ├── unit-test-template.md
│       ├── e2e-test-template.md
│       ├── manual-test-template.md
│       └── regression-template.md
├── devdocs-dev-tasks/
│   └── SKILL.md
├── devdocs-retrofit/
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
/devdocs-test-plan
/devdocs-dev-tasks
/devdocs-retrofit
/code-quality
/testing-guide
/refactor
/commit-convention
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
帮我重构这段代码
重构 UserService
Review 一下这个 PR
提交代码
帮我生成本周的周报
```
