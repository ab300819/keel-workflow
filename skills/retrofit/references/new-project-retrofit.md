# ms-retrofit 新项目改造流程详解

> 当项目没有 DevDocs 文档时执行的完整 Step 1-5 详细规范（含文档识别、代码逆向推导、推导示例）。
>
> SKILL.md 仅保留触发判定 + 总览；本文件提供执行细节。

## Step 1: 扫描项目结构

扫描常见文档位置：

```bash
# 文档目录
docs/ doc/ documentation/

# 根目录文档
README.md CHANGELOG.md

# 设计文档
design/ architecture/

# 测试文档
tests/ test/ __tests__/
```

## Step 2: 自动识别文档

### 识别规则

| DevDocs 阶段 | 识别关键词 | 常见文件名 |
|--------------|------------|------------|
| 需求文档 | requirement, PRD, 需求, spec | `*requirement*.md`, `*prd*.md` |
| 系统设计 | design, architecture, 设计, 架构 | `*design*.md`, `*architecture*.md` |
| 测试用例 | test, QA, 测试, case | `*test*.md`, `*qa*.md` |
| 开发任务 | task, todo, 任务, backlog | `*task*.md`, `*todo*.md` |

## Step 3: 用户确认

```markdown
## 文档识别结果

| 阶段 | 识别状态 | 识别到的文件 |
|------|----------|--------------|
| 需求文档 | ✅ 已识别 | `docs/requirements.md` |
| 系统设计 | ✅ 已识别 | `docs/architecture.md` |
| 测试用例 | ❌ 未找到 | - |
| 开发任务 | ⚠️ 待确认 | `TODO.md` (相似度 60%) |

### 选项

1. **确认识别结果** - 使用自动识别的映射
2. **手动指定文档** - 提供各阶段文档路径
3. **代码逆向推导** - 从代码分析生成文档（适用于无文档项目）
```

## Step 4: 代码逆向推导（可选）

当项目缺少文档时，从代码分析生成文档。

### 需求推导

| 分析对象 | 推导内容 | 编号分配 |
|----------|----------|----------|
| 路由/页面 | 功能模块 → F-XXX | 按模块顺序 |
| API 端点 | 业务操作 | 归属到 F-XXX |
| 测试描述 | 用户故事 → US-XXX | 按 F-XXX 分组 |
| 测试断言 | 验收标准 → AC-XXX | 按 US-XXX 分组 |

### 推导示例

```markdown
## 功能清单 [从代码推导]

### F-001: 用户模块

**用户故事**：
- **US-001**: 作为用户，我可以注册新账号
  - 来源：`POST /api/users` + `auth.test.ts`
- **US-002**: 作为用户，我可以登录系统
  - 来源：`POST /api/auth/login`

**验收标准**：
- **AC-001**: 邮箱格式正确时注册成功
  - 来源：`auth.test.ts: "should register with valid email"`
- **AC-002**: 密码少于 6 位时提示错误
  - 来源：`auth.test.ts: "should reject short password"`
```

### 测试用例推导

| 分析对象 | 推导内容 | 编号分配 |
|----------|----------|----------|
| 单元测试文件 | UT-XXX | 按文件顺序 |
| 集成测试文件 | IT-XXX | 按文件顺序 |
| E2E 测试文件 | E2E-XXX | 按文件顺序 |

```markdown
## 测试用例 [从代码推导]

### 单元测试

| 编号 | 关联 AC | 测试描述 | 来源 |
|------|---------|----------|------|
| UT-001 | AC-001 | should register with valid email | auth.test.ts:12 |
| UT-002 | AC-002 | should reject short password | auth.test.ts:24 |
```

## Step 5: 生成 DevDocs 文档

按 DevDocs 规范生成完整文档：

```
docs/devdocs/
├── 01-requirements.md      # 含 F/US/AC 编号
├── 02-system-design.md     # 含模块-功能点映射
├── 03-test-cases.md        # 含追溯矩阵
├── 03-test-unit.md         # 含 UT-XXX 编号
├── 03-test-integration.md  # 含 IT-XXX 编号
├── 03-test-e2e.md          # 含 E2E-XXX 编号
├── 04-dev-tasks.md         # 含 T-XX 编号
└── 00-retrofit-report.md   # 改造报告
```
