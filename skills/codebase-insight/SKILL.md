---
name: ms-codebase-insight
description: 只读分析现有代码库，输出系统边界、核心模块、公开接口、关键数据对象和技术约束。供 prd 和 dev/test 流程委托调用，了解已有系统现状。触发词：代码分析、系统现状、codebase analysis、existing system、代码盘点。NOT for 需求定义（use ms-requirements）、项目基线（use ms-retrofit）、项目上下文（use ms-onboard）。
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion, Write
metadata:
  patterns: [generator]
  interaction: single-turn
  handoff: yaml-summary-v1
user-invocable: true
---

# 代码盘点

只读分析现有代码库，输出结构化的系统现状盘点。不做需求推导、不做设计判断、不分配编号。

> 视角：代码考古学家——忠实记录发现的事实，不加解释或推荐。

## 快速开始

**一句话**: 只读分析代码库，输出系统边界、核心模块和技术约束。

**最常见用法**: `/ms-codebase-insight`

**不适合?** 需求定义→`/ms-requirements`，项目基线→`/ms-retrofit`，项目交接→`/ms-onboard`

## 与其他 skill 的边界

| skill | 职责 | codebase-insight 不做的 |
|-------|------|------------------------|
| ms-retrofit | 建立项目基线（`00-baseline.md`：目的边界 / 外部硬约束 / 护栏 / 已知未知） | 问人、判断意图、给不确定性定安全默认动作 |
| ms-onboard | 项目上下文 + 进度 + 待办 | 进度追踪、待办汇总 |
| code-self-describe | 模块级 CLAUDE.md + 依赖图 | 文件级描述、依赖图生成 |
| ms-verify `--schema-drift` | 扫描 A/B 类 DevDocs 产物的 `spec_version` 元数据 | 本 skill 的 `schema_version + commit_hash` 独立机制**被 `--schema-drift` 读取并在主报告独立章节呈现**（不并入 A/B 类主统计，不纳入 realign 编排；失效后由本 skill 自身 `--force` 处理，见 [../pipeline/references/realign.md](../pipeline/references/realign.md) § 与 ms-codebase-insight 的关系） |

## 运行模式

```bash
/ms-codebase-insight            → 智能检测（缓存命中则跳过）
/ms-codebase-insight --force    → 强制全量重新扫描
```

## 缓存机制

通过 commit hash 避免重复扫描，三个失效条件任一触发即重新扫描：

```text
Step 0: 缓存检查
    |
    +-- --force？→ 直接全量扫描
    |
    +-- docs/codebase-insight.md 不存在？→ 全量扫描
    |
    +-- 读取 frontmatter：
        ├── schema_version 不匹配 → 全量重新扫描
        ├── commit_hash != git rev-parse HEAD → 全量重新扫描
        └── 全部匹配 → 缓存命中（status: success, cache_hit: true）
```

**缓存设计原则**：只检查已提交变更（commit hash）和 schema 版本。未提交变更属于临时状态，需要时用 `--force` 强制重扫。

## 工作流程

### 全量扫描

```text
Step 1: 项目结构扫描
    |
    ├── 检测语言/框架（package.json, go.mod, Cargo.toml, pyproject.toml 等）
    ├── 目录结构分析（识别模块边界）
    └── 入口文件定位（main, app, index, routes）
    |
    ▼
Step 2: 接口提取
    |
    ├── 扫描路由注册（Express routes, FastAPI decorators, Go handlers 等）
    ├── 提取 HTTP 方法 + 路径 + handler 函数
    └── 按模块归类
    |
    ▼
Step 3: 数据对象提取
    |
    ├── 扫描 ORM 模型 / Schema 定义
    ├── 提取字段和关联关系
    └── 按业务域归类
    |
    ▼
Step 4: 约束识别
    |
    ├── 配置文件（env, config）
    ├── 环境依赖（Docker, CI）
    └── 版本约束（引擎版本、依赖版本）
    |
    ▼
Step 5: 输出 docs/codebase-insight.md
    |
    └── 更新 frontmatter: commit_hash, scan_scope, schema_version, generated_at
```

## 输出规范

文件路径：`docs/codebase-insight.md`

### frontmatter（必须字段）

```yaml
---
generated_at: 2026-03-26T10:00:00+08:00
commit_hash: "a1b2c3d"
scan_scope: "src/"                 # 扫描根目录
tech_stack: "Node.js + Express + PostgreSQL"
schema_version: "1.0"
---
```

### 章节结构（标题和顺序固定，消费方按标题定位解析）

```markdown
# 代码盘点

## 系统边界
- 入口点：...
- 外部依赖/集成：...

## 核心模块
| 模块 | 路径 | 职责摘要 |
|------|------|---------|

## 公开接口
| 方法 | 路径/签名 | 所属模块 |
|------|----------|---------|

## 关键数据对象
| 对象 | 关键字段 | 关联 |
|------|---------|------|

## 技术栈与约束
- 语言/框架：...
- 数据库：...
- 已知约束/限制：...

## 未确定项
- [ ] 项目描述（每项为 checkbox 格式）
```

### schema 约束

- 章节标题和顺序固定，不可增删或重排
- frontmatter 必须包含 `generated_at`、`commit_hash`、`scan_scope`、`schema_version`
- 未确定项使用 `- [ ]` checkbox 格式
- 表格列数固定，可为空但不可省略列

### 多代码根

盘点范围是 `workspace_context.code_roots` 各路径（`inline` 时为单项，`path` = 仓库根绝对路径，**本 skill 不按拓扑分支**）。代码根取自 握手 `workspace_context`（[_shared/constraints.md](../_shared/constraints.md) §3 `task/workspace-context`；未传入时按 `inline` 缺省）。**代码根多于一项时**：

- **逐个代码根盘点**，产出的模块 / 接口 / 数据对象一律带 `<label>/` 前缀限定，避免跨仓重名混淆
- **必须额外产出「仓间关系」小节**：依赖方向（谁调谁）、接口契约面（跨仓的 API / 消息 / 共享数据结构）、版本耦合点（改一边必须同改另一边的地方）。多代码根场景的价值主要在此——单仓时这节不存在
- 产物恒写 `<workspace_context.docs_dir>/codebase-insight.md`，**不往任何代码根写文件**（判据见 `capabilities.code_dir_write_policy`）

## 摘要契约

```yaml
skill: ms-codebase-insight
status: success | partial | failed
summary:
  headline: "5 个模块、23 个接口、8 个数据对象"
  details:
    cache_hit: true | false
    prev_commit: "a1b2c3d"
    curr_commit: "e4f5g6h"
    schema_version: "1.0"
    module_count: 5
    interface_count: 23
    data_object_count: 8
    tech_stack: "Node.js + Express + PostgreSQL"
blockers: []
output_files:
  - docs/codebase-insight.md
new_ids: {}
next_recommended:           # 不硬编码，由调用方决定下一步
  skill: ""
  args: ""
```

缓存命中时：

```yaml
skill: ms-codebase-insight
status: success
summary:
  headline: "缓存命中，代码无变更"
  details:
    cache_hit: true
    prev_commit: "a1b2c3d"
    curr_commit: "a1b2c3d"
    schema_version: "1.0"
blockers: []
output_files: []            # 缓存命中时未创建/修改任何文件
new_ids: {}
next_recommended:
  skill: ""
  args: ""
```

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档
