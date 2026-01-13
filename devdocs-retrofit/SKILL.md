---
name: devdocs-retrofit
description: Retrofit existing projects to DevDocs workflow by identifying documents, specifying them manually, or reverse-engineering from code. Use when users want to adapt existing projects to DevDocs process, migrate legacy documentation, standardize project documents, or generate documentation from code for undocumented projects. Triggers on keywords like "retrofit", "改造", "适配", "迁移文档", "标准化", "逆向", "reverse", "从代码生成文档", "无文档".
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash
---

# DevDocs Retrofit

将已有工程按 DevDocs 流程改造，支持自动识别文档、手动指定文档、或从代码逆向推导生成文档。

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese
- Generate all documents in Chinese

## Trigger Conditions

- 用户希望将现有项目适配 DevDocs 流程
- 用户需要标准化项目文档
- 用户要迁移或整理已有文档
- 项目缺少文档，需要从代码逆向推导生成文档

## Workflow

```
1. 扫描项目结构
   │
   ▼
2. 自动识别已有文档
   │
   ▼
3. 展示识别结果，询问用户确认/修正
   │
   ├─────────────────────────────────────┐
   │                                     │
   ▼                                     ▼
3a. 使用已有文档              3b. 代码逆向推导（无文档时）
   │                                     │
   └─────────────────────────────────────┘
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

## Step 1: 扫描项目结构

扫描常见文档位置：

```bash
# 扫描文档目录
docs/ doc/ documentation/ 文档/

# 扫描根目录文档
README.md CHANGELOG.md CONTRIBUTING.md

# 扫描设计文档
design/ architecture/ 设计/

# 扫描测试文档
tests/ test/ __tests__/ spec/
```

## Step 2: 自动识别文档

### 识别规则

| DevDocs 阶段 | 识别关键词 | 常见文件名 |
|----------|------------|------------|
| 需求文档 | requirement, PRD, 需求, spec, feature | `*requirement*.md`, `*prd*.md`, `*spec*.md` |
| 系统设计 | design, architecture, 设计, 架构, technical | `*design*.md`, `*architecture*.md`, `*tech*.md` |
| 测试方案 | test, QA, 测试, case | `*test*.md`, `*qa*.md`, `test-plan.*` |
| 开发任务 | task, todo, 任务, sprint, backlog | `*task*.md`, `*todo*.md`, `*backlog*.md` |

### 识别逻辑

```
1. 按文件名模式匹配
2. 读取文件内容，按关键词评分
3. 识别文档结构（标题、章节）
4. 综合判断文档类型
```

## Step 3: 用户确认

使用 AskUserQuestion 展示识别结果：

```markdown
## 文档识别结果

| 阶段 | 识别状态 | 识别到的文件 |
|------|----------|--------------|
| 需求文档 | ✅ 已识别 | `docs/requirements.md` |
| 系统设计 | ✅ 已识别 | `docs/architecture.md` |
| 测试方案 | ❌ 未找到 | - |
| 开发任务 | ⚠️ 待确认 | `TODO.md` (相似度 60%) |

请确认或修正以上识别结果。
```

### 用户选项

1. **确认识别结果** - 使用自动识别的映射
2. **手动指定文档** - 用户提供各阶段文档路径
3. **混合模式** - 部分确认，部分手动指定
4. **代码逆向推导** - 从代码分析生成文档（适用于无文档项目）

### 手动指定格式

```markdown
请按以下格式指定各阶段文档（可选，留空表示需要新建）：

- 需求文档: <文件路径>
- 系统设计: <文件路径>
- 测试方案: <文件路径>
- 开发任务: <文件路径>
```

## Step 3b: 代码逆向推导（可选）

当项目缺少文档或用户选择"代码逆向推导"时，通过分析代码生成文档。

### 触发条件

- 文档识别结果为空或大部分缺失
- 用户主动选择"代码逆向推导"选项
- 用户明确表示项目没有文档

### 代码分析范围

```bash
# 项目配置文件
package.json, pyproject.toml, Cargo.toml, go.mod, pom.xml, build.gradle

# 入口文件
src/index.*, src/main.*, src/app.*, main.*, app.*

# 路由/页面结构
src/routes/, src/pages/, src/views/, routes/, pages/

# API 定义
src/api/, src/controllers/, src/handlers/, api/, controllers/

# 数据模型
src/models/, src/entities/, src/schemas/, models/, entities/

# 测试文件
tests/, test/, __tests__/, *_test.*, *.test.*, *.spec.*

# 配置文件
.env.example, config/, settings/
```

### 需求文档逆向推导

从代码中提取需求信息：

| 分析对象 | 推导内容 | 分析方法 |
|----------|----------|----------|
| 路由/页面 | 功能模块清单 | 扫描路由定义，提取页面结构 |
| API 端点 | 业务能力列表 | 分析 REST/GraphQL 端点，提取操作类型 |
| 数据模型 | 业务实体 | 分析 Schema/Model 定义，提取核心实体 |
| 测试描述 | 用户故事 | 提取 describe/it 描述文本 |
| README | 项目背景 | 提取项目简介和功能说明 |
| 权限代码 | 用户角色 | 分析 RBAC/权限相关代码 |

#### 需求推导流程

```
1. 扫描路由/页面文件
   - 提取所有路由路径和组件名
   - 推导：功能模块和页面清单

2. 扫描 API 端点
   - 提取 HTTP 方法 + 路径 + 处理函数
   - 推导：业务操作清单（CRUD + 业务动作）

3. 扫描数据模型
   - 提取实体名称和字段
   - 推导：核心业务对象和属性

4. 扫描测试文件
   - 提取 describe/it/test 的描述文本
   - 推导：用户故事和验收标准

5. 综合生成需求文档
   - 按功能模块组织
   - 标注 [从代码推导] 便于用户审核
```

#### 需求推导示例

```markdown
## 功能清单 [从代码推导]

### 用户模块
- 用户注册 (POST /api/users)
- 用户登录 (POST /api/auth/login)
- 获取用户信息 (GET /api/users/:id)
- 更新用户资料 (PUT /api/users/:id)

### 订单模块
- 创建订单 (POST /api/orders)
- 订单列表 (GET /api/orders)
- 订单详情 (GET /api/orders/:id)
- 取消订单 (DELETE /api/orders/:id)

## 用户故事 [从测试推导]

- 作为用户，我可以注册新账号，以便使用系统功能
  - 来源：`auth.test.ts: "should register new user"`
- 作为用户，我可以查看订单列表，以便了解我的购买记录
  - 来源：`order.test.ts: "should list user orders"`
```

### 系统设计逆向推导

从代码中提取架构信息：

| 分析对象 | 推导内容 | 分析方法 |
|----------|----------|----------|
| package.json | 技术选型 | 分析 dependencies 确定技术栈 |
| 目录结构 | 模块划分 | 分析 src/ 目录结构确定分层 |
| 导入关系 | 模块依赖 | 分析 import/require 确定依赖关系 |
| API 代码 | 接口定义 | 提取路由、参数、响应结构 |
| Model 代码 | 数据模型 | 提取 Schema/Entity 定义 |
| 配置文件 | 外部依赖 | 分析数据库、缓存、消息队列配置 |

#### 系统设计推导流程

```
1. 分析项目配置
   - 读取 package.json/pyproject.toml 等
   - 推导：技术栈（框架、数据库、工具库）

2. 分析目录结构
   - 扫描 src/ 下的目录层级
   - 推导：架构模式（MVC/分层/模块化）

3. 分析代码依赖
   - 扫描 import/require 语句
   - 推导：模块依赖图

4. 提取 API 定义
   - 分析路由和控制器代码
   - 推导：接口清单（路径、方法、参数、响应）

5. 提取数据模型
   - 分析 Model/Schema/Entity 定义
   - 推导：ER 图和字段说明

6. 分析配置依赖
   - 读取配置文件和环境变量
   - 推导：外部服务依赖（DB、Redis、MQ 等）
```

#### 系统设计推导示例

```markdown
## 技术选型 [从代码推导]

| 类别 | 技术 | 来源 |
|------|------|------|
| 框架 | Express.js | package.json: express@4.18.2 |
| 数据库 | PostgreSQL | package.json: pg@8.11.0 |
| ORM | Prisma | package.json: @prisma/client |
| 缓存 | Redis | package.json: ioredis@5.3.0 |
| 认证 | JWT | package.json: jsonwebtoken |

## 模块划分 [从目录推导]

```
src/
├── controllers/    # 控制层 - 处理 HTTP 请求
├── services/       # 服务层 - 业务逻辑
├── models/         # 数据层 - 数据模型
├── middlewares/    # 中间件 - 认证、日志等
├── utils/          # 工具函数
└── config/         # 配置管理
```

## API 接口 [从路由推导]

### 用户接口

| 方法 | 路径 | 描述 | 来源 |
|------|------|------|------|
| POST | /api/users | 创建用户 | routes/user.ts:12 |
| GET | /api/users/:id | 获取用户 | routes/user.ts:18 |
| PUT | /api/users/:id | 更新用户 | routes/user.ts:24 |
```

### 测试方案逆向推导

从测试代码中提取测试策略：

| 分析对象 | 推导内容 | 分析方法 |
|----------|----------|----------|
| 测试文件结构 | 测试覆盖范围 | 分析 tests/ 目录组织 |
| 测试框架 | 测试工具链 | 分析测试依赖和配置 |
| 测试用例 | 具体测试点 | 提取 describe/it 结构 |
| Mock 文件 | 测试数据 | 分析 mock/fixture 数据 |
| CI 配置 | 自动化流程 | 分析 GitHub Actions 等 |

#### 测试推导流程

```
1. 分析测试目录结构
   - 扫描 tests/ 或 __tests__/ 目录
   - 推导：测试分类（unit/integration/e2e）

2. 分析测试框架配置
   - 读取 jest.config/vitest.config 等
   - 推导：测试工具链

3. 提取测试用例
   - 解析 describe/it/test 块
   - 推导：测试用例清单

4. 分析覆盖率配置
   - 读取覆盖率配置
   - 推导：覆盖率要求

5. 分析 CI 流程
   - 读取 .github/workflows 等
   - 推导：自动化测试流程
```

#### 测试推导示例

```markdown
## 测试覆盖 [从代码推导]

### 单元测试
| 模块 | 测试文件 | 用例数 |
|------|----------|--------|
| UserService | user.service.test.ts | 12 |
| OrderService | order.service.test.ts | 8 |
| AuthMiddleware | auth.middleware.test.ts | 5 |

### 测试用例清单 [从测试推导]

#### UserService
- [ ] should create user with valid data
- [ ] should throw error for duplicate email
- [ ] should hash password before saving
- [ ] should return user without password field
```

### 开发任务逆向推导

从代码中提取潜在任务：

| 分析对象 | 推导内容 | 分析方法 |
|----------|----------|----------|
| TODO 注释 | 待办事项 | 搜索 TODO/FIXME/HACK 注释 |
| Issue 链接 | 关联问题 | 搜索 #123 或 issue URL |
| 代码质量 | 技术债务 | 分析复杂度、重复代码 |
| 依赖版本 | 升级任务 | 检查过时依赖 |
| 测试覆盖 | 补充测试 | 分析未覆盖代码 |

#### 任务推导流程

```
1. 搜索代码注释
   - 正则匹配 TODO/FIXME/HACK/XXX
   - 推导：待办任务清单

2. 分析代码质量
   - 识别超长函数、深层嵌套
   - 推导：重构任务

3. 检查依赖状态
   - 分析 package.json 依赖版本
   - 推导：升级任务

4. 分析测试覆盖
   - 对比代码和测试文件
   - 推导：补充测试任务
```

#### 任务推导示例

```markdown
## 开发任务 [从代码推导]

### 待办事项 [从 TODO 注释]
| 优先级 | 任务 | 来源 |
|--------|------|------|
| P1 | 实现密码重置功能 | src/auth.ts:45 `// TODO: implement password reset` |
| P2 | 优化查询性能 | src/order.ts:89 `// FIXME: N+1 query issue` |
| P3 | 添加输入验证 | src/user.ts:23 `// TODO: add validation` |

### 技术债务 [从代码分析]
| 类型 | 描述 | 位置 |
|------|------|------|
| 重构 | 函数过长 (>100行) | src/services/order.ts:processOrder |
| 重构 | 重复代码 | src/controllers/*.ts 错误处理 |
| 升级 | 过时依赖 | lodash@4.17.15 -> 4.17.21 |

### 测试补充 [从覆盖分析]
| 模块 | 当前覆盖率 | 建议 |
|------|------------|------|
| PaymentService | 23% | 补充支付流程测试 |
| EmailService | 0% | 新增邮件发送测试 |
```

### 逆向推导输出标记

所有从代码逆向推导的内容必须明确标记来源：

```markdown
## 标记规范

- `[从代码推导]` - 通过分析代码结构推导
- `[从测试推导]` - 通过分析测试用例推导
- `[从配置推导]` - 通过分析配置文件推导
- `[从注释推导]` - 通过分析代码注释推导
- `[待用户确认]` - 推导结果需要用户验证
- `[置信度: 高/中/低]` - 推导结果的可信程度
```

### 逆向推导结果确认

完成代码分析后，向用户展示推导结果：

```markdown
## 代码逆向推导结果

### 推导概览

| 文档类型 | 推导状态 | 置信度 | 主要来源 |
|----------|----------|--------|----------|
| 需求文档 | ✅ 已生成 | 中 | API + 测试 + README |
| 系统设计 | ✅ 已生成 | 高 | 代码结构 + 配置 |
| 测试方案 | ⚠️ 部分生成 | 中 | 测试目录 |
| 开发任务 | ✅ 已生成 | 高 | TODO 注释 + 依赖分析 |

### 重要提示

以上内容均从代码逆向推导，可能存在以下局限：
1. 无法推导业务背景和产品愿景
2. 无法推导非功能性需求的具体指标
3. 可能遗漏未在代码中体现的计划功能
4. 建议用户审核并补充 [待用户确认] 标记的内容

是否继续使用推导结果生成文档？
```

## Step 4: 分析覆盖情况

对已识别的文档进行内容分析：

### 需求文档检查项

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 需求背景 | ✅/❌ | 是否包含背景说明 |
| 目标用户 | ✅/❌ | 是否定义用户群体 |
| 功能清单 | ✅/❌ | 是否列出功能点 |
| 用户故事 | ✅/❌ | 是否有用户故事 |
| 验收标准 | ✅/❌ | 是否有验收条件 |
| 范围边界 | ✅/❌ | 是否明确范围 |

### 系统设计检查项

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 架构图 | ✅/❌ | 是否有架构描述 |
| 技术选型 | ✅/❌ | 是否说明技术栈 |
| 模块设计 | ✅/❌ | 是否有模块划分 |
| 接口定义 | ✅/❌ | 是否有 API 设计 |
| 数据模型 | ✅/❌ | 是否有数据结构 |

### 测试方案检查项

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 单元测试 | ✅/❌ | 是否有单测方案 |
| 集成测试 | ✅/❌ | 是否有集成测试 |
| E2E 测试 | ✅/❌ | 是否有端到端测试 |
| 测试用例 | ✅/❌ | 是否有具体用例 |

### 开发任务检查项

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 任务列表 | ✅/❌ | 是否有任务清单 |
| 依赖关系 | ✅/❌ | 是否标注依赖 |
| 优先级 | ✅/❌ | 是否有优先级 |
| 完成标准 | ✅/❌ | 是否有验收条件 |

## Step 5: 生成改造计划

```markdown
## 改造计划

### 文档状态总览

| 阶段 | 当前状态 | 改造动作 |
|------|----------|----------|
| 需求文档 | 部分完整 (70%) | 补充验收标准、范围边界 |
| 系统设计 | 缺失 | 新建完整文档 |
| 测试方案 | 部分完整 (40%) | 补充单元测试、回归方案 |
| 开发任务 | 已存在 | 格式标准化 |

### 改造步骤

1. [ ] 补充需求文档缺失章节
2. [ ] 新建系统设计文档
3. [ ] 完善测试方案
4. [ ] 标准化开发任务格式

### 预计产出

docs/devdocs/
├── 01-requirements.md      # 补充自 docs/requirements.md
├── 02-system-design.md     # 新建
├── 03-test-plan.md         # 补充自 tests/README.md
└── 04-dev-tasks.md         # 标准化自 TODO.md
```

## Step 6: 执行改造

### 改造模式

使用 AskUserQuestion 询问改造模式：

1. **完整改造** - 按 DevDocs 模板重新生成所有文档
2. **增量补充** - 保留原有内容，仅补充缺失部分
3. **仅标准化** - 保留内容，调整格式和结构

### 改造原则

- [ ] 保留原有文档的核心内容
- [ ] 不删除用户已有的信息
- [ ] 新增内容标注 `[待补充]` 提醒用户
- [ ] 生成的文档放入 `docs/devdocs/` 目录
- [ ] 原文档保留备份（如需要）

### 各阶段改造

#### 需求文档改造

```
1. 读取原文档内容
2. 提取已有信息（背景、功能等）
3. 按 DevDocs 模板重组
4. 标注缺失部分为 [待补充]
5. 写入 docs/devdocs/01-requirements.md
```

#### 系统设计改造

```
1. 读取原文档（如有）
2. 扫描代码结构推断架构
3. 提取已有设计信息
4. 按模板生成，缺失部分标注
5. 写入 docs/devdocs/02-system-design.md
```

#### 测试方案改造

```
1. 读取测试相关文档
2. 扫描测试代码目录
3. 提取已有测试策略
4. 按模板补充完善
5. 写入 docs/devdocs/03-test-*.md
```

#### 开发任务改造

```
1. 读取任务/TODO 文档
2. 提取任务列表
3. 按 TAR 原则补充
4. 建立依赖关系
5. 写入 docs/devdocs/04-dev-tasks.md
```

## Step 7: 生成改造报告

```markdown
# DevDocs 改造报告

## 改造概览

- **项目名称**：<project>
- **改造时间**：<timestamp>
- **改造模式**：增量补充

## 改造结果

| 阶段 | 原文档 | 新文档 | 改造类型 |
|------|--------|--------|----------|
| 需求 | `docs/req.md` | `docs/devdocs/01-requirements.md` | 补充 |
| 设计 | - | `docs/devdocs/02-system-design.md` | 新建 |
| 测试 | `tests/README.md` | `docs/devdocs/03-test-plan.md` | 补充 |
| 任务 | `TODO.md` | `docs/devdocs/04-dev-tasks.md` | 标准化 |

## 待完善项

以下内容标记为 [待补充]，需要人工完善：

### 需求文档
- [ ] 验收标准 AC-03 至 AC-05
- [ ] 非功能性需求-性能指标

### 系统设计
- [ ] API 响应示例
- [ ] 错误码列表

### 测试方案
- [ ] UI 自动化测试用例
- [ ] 回归测试检查清单

## 下一步建议

1. 完善标记为 [待补充] 的内容
2. 运行 `/devdocs-requirements` 审查需求文档
3. 运行 `/devdocs-system-design` 审查系统设计
4. 运行 `/devdocs-test-plan` 完善测试方案
```

## Output

```
docs/devdocs/
├── 01-requirements.md
├── 02-system-design.md
├── 02-system-design-api.md      # 如需要
├── 03-test-plan.md
├── 03-test-unit.md              # 如需要
├── 03-test-e2e.md               # 如需要
├── 03-test-manual.md            # 如需要
├── 03-test-regression.md        # 如需要
├── 04-dev-tasks.md
└── 00-retrofit-report.md        # 改造报告
```

## Constraints

### 识别约束
- [ ] 必须扫描常见文档目录
- [ ] 识别结果必须让用户确认
- [ ] 支持用户手动指定/修正

### 改造约束
- [ ] **不得删除原有文档的有效内容**
- [ ] 缺失内容标注 `[待补充]`
- [ ] 必须生成改造报告
- [ ] 改造前询问用户确认改造模式

### 输出约束
- [ ] 输出目录统一为 `docs/devdocs/`
- [ ] 文件命名遵循 DevDocs 规范
- [ ] 每个阶段改造后询问用户确认

## Error Handling

### 无法识别文档
```
未能自动识别到相关文档。

请手动指定各阶段文档路径，或选择跳过相应阶段：
- 需求文档: [请输入路径或留空]
- 系统设计: [请输入路径或留空]
- 测试方案: [请输入路径或留空]
- 开发任务: [请输入路径或留空]
```

### 文档格式不兼容
```
检测到文档格式可能不兼容：
- 文件：<path>
- 问题：<issue>

建议：选择"完整改造"模式重新生成文档。
```

### 项目无文档
```
当前项目未检测到任何文档。

可选方案：
1. **代码逆向推导**（推荐）- 从代码分析自动生成文档
2. 使用 /devdocs-requirements 从头创建需求文档
3. 提供外部文档路径进行导入

是否使用代码逆向推导功能？
```

### 逆向推导失败
```
代码逆向推导未能获取足够信息：

| 文档类型 | 状态 | 原因 |
|----------|------|------|
| 需求文档 | ❌ 失败 | 未找到路由/API 定义 |
| 系统设计 | ⚠️ 部分 | 仅识别到技术栈 |
| 测试方案 | ❌ 失败 | 未找到测试文件 |
| 开发任务 | ✅ 成功 | 从 TODO 注释提取 |

建议：
1. 对于失败项，请手动提供信息或使用对应 skill 从头创建
2. 对于部分成功项，请审核并补充缺失内容
```
