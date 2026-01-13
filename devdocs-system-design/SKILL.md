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
2. **Ask user preferences**: Query tech stack and platform preferences
3. **Explore codebase**: Understand existing architecture if applicable
4. **Create design**: Generate system design document
5. **Confirm with user**: Get approval before finalizing

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

If user has no preference, design the optimal solution based on requirements.

## Output

**File**: `docs/devdocs/02-system-design.md`

If the document exceeds 300 lines, split into:
- `docs/devdocs/02-system-design.md` - Architecture overview and tech stack
- `docs/devdocs/02-system-design-api.md` - Detailed API design
- `docs/devdocs/02-system-design-data.md` - Data models and database design

For detailed template, see [templates/design-template.md](templates/design-template.md).

## 设计原则

### MTE 原则

系统设计必须遵循 **MTE 原则**：

| 原则 | 说明 | 检查点 |
|------|------|--------|
| **Maintainability** | 可维护性 | 模块职责单一、依赖清晰、易于理解和修改 |
| **Testability** | 可测试性 | 核心逻辑可单元测试、依赖可 Mock、边界清晰 |
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
4. **Module Design** - Module responsibilities and dependencies
5. **Core Interfaces** - Key interfaces and method signatures (no implementation)
6. **Design Patterns** - Applied patterns and rationale
7. **Data Model** - Entity definitions and relationships
8. **API Design** - Endpoints with request/response examples
9. **State Flow** - State machines for key business flows
10. **Error Handling** - Error codes and handling strategies
11. **Extensibility** - Extension points and future considerations

## 核心接口设计

设计文档中应体现核心接口定义（**只定义签名，不写实现**）：

```markdown
### 核心接口

#### IUserService

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `createUser` | `CreateUserDTO` | `User` | 创建用户 |
| `getUserById` | `string` | `User \| null` | 根据ID查询 |
| `updateUser` | `string, UpdateUserDTO` | `User` | 更新用户信息 |

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
- [ ] **核心业务逻辑必须可单元测试（无外部依赖或依赖可 Mock）**
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

## Next Step

After user confirms system design, suggest running `/devdocs-test-plan` for test planning phase.
