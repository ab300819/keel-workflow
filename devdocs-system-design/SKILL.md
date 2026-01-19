---
name: devdocs-system-design
description: Create system design documents based on requirements. Use when users need technical architecture, API design, data models, or system design. Triggers on keywords like "system design", "architecture", "technical design", "API design".
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
---

# DevDocs System Design

Create comprehensive system design documents based on product requirements.

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese
- Generate all documents in Chinese

## Trigger Conditions

- User has completed requirements document
- User asks for system/technical design
- User needs architecture or API design

## Prerequisites

- Requirements document exists at `docs/devdocs/01-requirements.md`
- If not exists, suggest running `/devdocs-requirements` first

## Workflow

1. **Read requirements**: Load `docs/devdocs/01-requirements.md`
2. **Ask user preferences**: Query tech stack, platform, and integration needs
3. **Explore codebase**: Understand existing architecture if applicable
4. **Create design**: Generate system design document
5. **Verify coverage**: Check all F-XXX have corresponding modules/interfaces
6. **Confirm with user**: Get approval before finalizing

## Pre-design Questions

**Must ask user before designing** using AskUserQuestion:

1. **Tech Stack Preference**
   - Do you have a preferred tech stack?
   - Options: Specify stack / No preference (will recommend based on requirements)

2. **Target Platform**
   - What is the target platform?
   - Options: Web / Mobile (iOS/Android) / Desktop / Server / Cross-platform

3. **Deployment Environment**
   - Where will this be deployed?
   - Options: Cloud (AWS/GCP/Azure) / On-premise / Hybrid

4. **Existing System Integration**
   - Does this need to integrate with existing systems?
   - Options: No / Yes (specify systems, APIs, databases)

If user has no preference, design the optimal solution based on requirements.

## Output

**主文件**：`docs/devdocs/02-system-design.md`

### 文档拆分规则

当满足以下条件时，应拆分文档：
- 文档超过 **300 行**
- 模块数量超过 **5 个**
- API 接口超过 **10 个**

**拆分方式**：

```
docs/devdocs/
├── 02-system-design.md          # 主文档：架构概览、技术选型、模块划分
├── 02-system-design-api.md      # API 设计：接口定义、请求响应示例
└── 02-system-design-data.md     # 数据模型：实体定义、ER 图、索引策略
```

**拆分内容分配**：

| 文件 | 包含章节 |
|------|----------|
| 02-system-design.md | 1-7: 平台、架构、技术选型、模块、接口签名、模式、代码结构 |
| 02-system-design-api.md | 9-10: 完整 API 设计、状态流转 |
| 02-system-design-data.md | 8, 11-13: 数据模型、异常处理、扩展性、需求追溯 |

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

根据场景选择合适的设计模式，**只在必要时使用**：

| 场景 | 推荐模式 | 适用情况 |
|------|----------|----------|
| 对象创建 | Factory / Builder | 复杂对象构建、多种类型创建 |
| 行为扩展 | Strategy / Template | 算法可替换、流程固定步骤可变 |
| 结构组织 | Facade / Adapter | 简化复杂接口、适配第三方库 |
| 状态管理 | State / Observer | 状态驱动行为、事件通知 |
| 数据访问 | Repository / DAO | 数据层抽象、查询封装 |

### 设计层次

```
┌─────────────────────────────────────┐
│           Interface Layer           │  ← API/Controller（薄层，无业务逻辑）
├─────────────────────────────────────┤
│           Service Layer             │  ← 业务逻辑（核心，可测试）
├─────────────────────────────────────┤
│           Domain Layer              │  ← 领域模型（实体、值对象）
├─────────────────────────────────────┤
│         Infrastructure Layer        │  ← 数据访问、外部服务（可替换）
└─────────────────────────────────────┘
```

## Document Structure

1. **Target Platform** - Platform, version requirements, deployment environment
2. **Architecture Overview** - High-level architecture diagram (ASCII)
3. **Tech Stack** - Technology choices with rationale
4. **Module Design** - Module responsibilities and dependencies, **标注关联功能点 (F-XXX)**
5. **Core Interfaces** - Key interfaces and method signatures (no implementation), **标注关联 F-XXX**
6. **Design Patterns** - Applied patterns and rationale
7. **Code Structure** - Directory structure design
8. **Data Model** - Entity definitions and relationships
9. **API Design** - Endpoints with request/response examples, **标注关联 F-XXX, AC-XXX**
10. **State Flow** - State machines for key business flows
11. **Error Handling** - Error codes and handling strategies
12. **Extensibility** - Extension points and future considerations
13. **需求追溯** - 功能点与模块/接口的映射关系，**覆盖检查清单**

## 核心接口设计

设计文档中应体现核心接口定义（**只定义签名，不写实现**），并标注关联功能点：

```markdown
### 核心接口

#### IUserService（关联：F-001 用户注册, F-002 用户登录）

| 方法 | 参数 | 返回值 | 关联 | 说明 |
|------|------|--------|------|------|
| `createUser` | `CreateUserDTO` | `User` | F-001, AC-001 | 创建用户 |
| `validateEmail` | `string` | `boolean` | F-001, AC-002 | 验证邮箱 |
| `login` | `LoginDTO` | `AuthToken` | F-002, AC-006 | 用户登录 |

#### IUserRepository

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `save` | `User` | `User` | 保存用户 |
| `findById` | `string` | `User \| null` | 根据ID查询 |
| `findByEmail` | `string` | `User \| null` | 根据邮箱查询 |
```

## 代码结构设计

```markdown
### 目录结构

src/
├── api/                    # 接口层
│   ├── controllers/        # 控制器（路由处理）
│   ├── middlewares/        # 中间件（认证、日志等）
│   └── validators/         # 请求验证
├── services/               # 服务层
│   ├── interfaces/         # 服务接口定义
│   └── impl/               # 服务实现
├── domain/                 # 领域层
│   ├── entities/           # 实体
│   ├── value-objects/      # 值对象
│   └── events/             # 领域事件
├── infrastructure/         # 基础设施层
│   ├── repositories/       # 数据仓储实现
│   ├── external/           # 外部服务适配
│   └── config/             # 配置
└── shared/                 # 共享
    ├── types/              # 类型定义
    ├── utils/              # 工具函数
    └── constants/          # 常量
```

## Constraints

### 基础约束

- [ ] **Must ask user for tech stack preference and target platform first**
- [ ] Tech stack choices must include rationale
- [ ] If user has no preference, select optimal solution for requirements
- [ ] Must specify target platform and minimum version requirements
- [ ] API design must include request/response examples
- [ ] Data model must consider indexes and query patterns
- [ ] Must identify integration points with existing systems
- [ ] Prefer existing project tech stack when applicable

### MTE 原则约束

- [ ] **每个模块职责单一，不超过一个变化原因**
- [ ] **核心业务逻辑必须可单元测试**（无外部依赖或依赖可 Mock，详见 `/testing-guide`）
- [ ] **预留合理扩展点，但不为假设需求设计**
- [ ] 依赖方向：外层依赖内层，内层不依赖外层
- [ ] 接口优于实现：依赖抽象，不依赖具体实现

### 设计模式约束

- [ ] **只在解决实际问题时使用设计模式，不为使用而使用**
- [ ] 使用的设计模式必须说明解决什么问题
- [ ] 优先选择简单方案，复杂方案需要说明理由
- [ ] 相同问题在项目中使用一致的模式

### 避免过度设计

- [ ] **不为"未来可能"的需求设计，只为当前需求设计**
- [ ] 不创建只有一个实现的接口（除非为了可测试性）
- [ ] 不过早抽象，等到有 3 个以上相似场景再抽象
- [ ] 配置优于硬编码，但不为所有内容添加配置

### 安全约束

- [ ] **敏感数据（密码、Token）不明文存储**
- [ ] **需要认证的 API 已标注**
- [ ] **用户输入有验证（防注入）**
- [ ] 敏感操作有日志记录

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 可测试性设计 | `/testing-guide` | 确保核心逻辑可单元测试 |
| 代码质量 | `/code-quality` | MTE 原则指导设计 |
| UI 架构 | `/ui-skills` | UI 组件设计约束 |

## Next Step

After user confirms system design, suggest running `/devdocs-test-cases` for test case design phase.
