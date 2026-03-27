---
name: ms-dev-workflow
description: Execute development tasks with skeleton-first approach and layered TDD. Supports single task, batch execution (by range, feature, user story), dependency resolution, and breakpoint resume. Includes optional adversarial verification and --headless unattended mode (无人值守). Triggers on "execute task", "start T-XX", "batch", "resume", "开发任务", "执行任务", "批量开发", "继续开发", "开始写代码", "开始开发", "--review", "--headless", "无人值守". NOT for task breakdown (use ms-dev-tasks) or bug fixes (use ms-bugfix).
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion, TodoWrite, Task
metadata:
  patterns: [pipeline, reviewer]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 开发工作流

> 视角：资深开发者 — 务实优先，不过度设计，测试先行，提交原子化。

执行开发任务的工作流指导，支持单任务和批量执行，采用自顶向下开发模式和分层 TDD。

## 语言规则

- 支持中英文提问
- 统一中文回复

## 模式选择

入口处根据任务规模选择合适的开发模式：

| 模式 | 适用场景 | 流程 |
|------|---------|------|
| **轻量** | Bug fix、小改动、配置变更 | → `/ms-bugfix`（已有） |
| **标准** | 新功能、需求变更 | → 完整 Requirements→Design→Tests→Tasks→Dev |
| **探索** | 原型、技术调研 | → 允许跳过部分验证，事后 `/ms-retrofit` 补文档 |

### 模式判断指引

- 若任务来自 `ms-dev-tasks`（已有完整文档链）→ **标准模式**
- 若用户描述为 bug/hotfix/配置变更 → **轻量模式**，路由到 `/ms-bugfix`
- 若用户描述为原型/调研/探索/spike → **探索模式**，跳过对抗式验证和追溯标注强制，开发完成后提示运行 `/ms-retrofit`

> 以下流程为**标准模式**。轻量模式和探索模式见上述路由。

## 触发条件

- 用户开始执行某个任务（如 T-01）
- 用户批量执行任务（如 T-01~T-05、F-001、--all）
- 用户需要继续开发（断点续做）
- 用户需要开发指导
- 用户从 ms-dev-tasks 进入开发阶段
- 关键词："开发任务"、"执行任务"、"开始 T-XX"、"批量开发"、"继续开发"

## 运行模式

### 语法

| 指定符 | 示例 | 说明 |
|--------|------|------|
| 单任务 | `T-03` | 执行单个任务（现有行为） |
| 范围 | `T-01~T-05` | 执行范围内所有任务 |
| 枚举 | `T-01,T-03,T-07` | 执行指定任务列表 |
| 功能点 | `F-001` | 通过 `关联需求` 字段反查所有关联任务 |
| 用户故事 | `US-001` | 同上 |
| 全部 | `--all` | 所有 `状态≠已完成` 的任务 |
| 无人值守 | `--headless` | 批量模式 + 全自动决策（fail-fast） |
| 自动提交 | `--auto-commit` | 测试通过自动提交，仅 Blocker 时暂停（与 `--headless` 互斥） |
| 上下文重置 | `--context-reset N` | 每 N 个任务后编排器重置上下文（默认 3，仅批量模式） |

### 模式对比

| 特性 | 单任务模式 | 批量模式（交互） | `--auto-commit` | `--headless` |
|------|-----------|----------------|----------------|--------------|
| 依赖解析 | 自动补充前置依赖 | 拓扑排序全部任务 | 拓扑排序全部任务 | 拓扑排序 + 前置校验 |
| 断点检测 | 编排器轻量执行 | 编排器轻量执行 | 编排器轻量执行 | 编排器轻量执行 |
| 提交方式 | 子 Agent 内交互确认 | 子 Agent 内交互确认 | 测试通过自动提交 | 自动提交（安全不变量保证） |
| 中断处理 | 子 Agent 内交互 | 子 Agent 内交互 | Blocker 时暂停询问 | fail-fast 终止 + 续做命令 |
| 完成汇总 | 任务完成摘要 | 批量执行报告 | 批量执行报告 | 交付报告 + 检查点文件 |
| 执行模式 | 编排器 + 子 Agent | 编排器 + 子 Agent | 编排器 + 子 Agent | 编排器 + 子 Agent |
| 上下文隔离 | 任务执行隔离 | 每任务独立上下文 | 每任务独立上下文 | 每任务独立上下文 |

### 统一编排流程

所有模式均采用**编排器 + 子 Agent** 架构，主 Agent 只做编排和决策，不直接执行 TDD 循环：

```text
解析任务指定符 → 依赖解析
  ├── 扩展后仅 1 任务 → 启动子 Agent 执行完整流程 → 接收摘要 → 后续步骤
  └── 扩展后 >1 任务 → 拓扑排序 → 逐任务循环（断点检测 → 子 Agent 执行 → 原子提交）→ 汇总
```

**编排器（主 Agent）职责**：解析指定符、依赖解析、断点检测、启动子 Agent、接收摘要、展示结果、调度后续子 Agent（sync/compound/test-run）

**任务子 Agent 职责**：执行开发流程（步骤 1→5），包括 TDD 循环、对抗式验证、Blocker 修复闭环、code-self-describe、Commit 1（代码提交）。Commit 2（文档同步）由编排器调度 /ms-sync 子 Agent 完成。

> 详见 [task-orchestration.md](references/task-orchestration.md)

## 前置条件

- 任务文档：`docs/devdocs/04-dev-tasks.md`
- 任务已定义并包含：关联需求、验收标准、测试方法

## 工作流程

```text
1. 读取任务定义
   ├── 从 04-dev-tasks.md 获取任务详情
   ├── 确认关联的 F-XXX、AC-XXX
   └── 确认关联的测试用例 UT/IT/E2E-XXX
           │
           ▼
1.5 Sprint Contract（验收契约协商）
   ├── Test Agent 基于 AC + 当前代码上下文，生成可执行的验收契约
   │   └── 具体到：函数签名、返回值类型、边界条件、异常场景
   ├── 编排器审核契约合理性（过度 vs 不足）
   │   ├── 过度：契约超出 AC 范围 → 裁剪
   │   └── 不足：契约未覆盖 AC 关键行为 → 补充
   └── 契约确认后作为 Test Agent 写测试的输入约束
           │
           ▼
2. 生成骨架代码（自顶向下）
   ├── 接口骨架 + @requirement/@satisfies 标注
   └── 测试骨架 + @verifies/@testcase 标注（基于 Sprint Contract）
           │
           ▼
3. 执行开发（统一流程，分级强制）
   ├── 所有层级遵循统一 11 步流程
   ├── 层级标记（🔴🟡🟢⚪）决定各步骤强制程度
   └── 详见 [execution-flow.md](references/execution-flow.md) 强制程度矩阵
           │
           ▼
4. 完成检查
   ├── 基础检查（始终执行）
   │   ├── 验收标准全部满足
   │   ├── 测试通过
   │   └── Review 要点自查
   │
   ├── 前置验证（--review 触发时，对抗式验证之前）
   │   ├── /ms-verify --impl：AC 满足度 + 设计一致性（若存在 DevDocs 文档）
   │   └── /ms-verify --ui：设计稿↔实现对齐（仅 UI 任务 + 有设计稿）
   │
   └── 对抗式验证（🔴自动触发 / 其他层级 --review 手动触发）
       ├── 🔍 代码质量审查（/code-quality 视角）
       ├── 🧪 测试完备性审查（/testing-guide 视角）
       └── 📋 综合审查报告
           │
           ▼
4.5 更新自描述（/code-self-describe --update）
           │
           ▼
5. 提交代码（Commit 1: 代码，遵循 /commit-convention）
           │
           ▼
6. 更新追溯 + 文档提交（/ms-sync → Commit 2: 文档）
        │
        ▼
6.5 更新 AGENTS.md "当前状态"（若存在）
    ├── 更新活跃任务编号 (T-XX)
    └── 更新进度统计 (X/Y)
        │
        ▼
7. [推荐] 知识沉淀（/ms-compound）
    ├── 批量模式完成后默认执行（用户可跳过）
    └── 单任务模式：提示用户是否运行 /ms-compound
```

### 步骤状态追踪

11 步执行流程中，每步完成后记录状态标记（S1~S11），用于断点恢复时精确定位。比原有 5 步检查点更精确，减少重复工作。

> 详见 [execution-flow.md](references/execution-flow.md) 步骤状态追踪表

## 代码追溯标注规范

> 实现文档↔代码的双向追溯，AI 在生成代码时自动添加标注。

### 标注类型

| 标注 | 用途 | 位置 |
|------|------|------|
| `@requirement F-XXX` | 关联功能点 | 接口/类/模块 |
| `@satisfies AC-XXX` | 满足的验收标准 | 接口/方法 |
| `@verifies AC-XXX` | 验证的验收标准 | 测试用例 |
| `@testcase UT/IT/E2E-XXX` | 测试编号 | 测试用例 |

### 标注规则

| 层级 | 标注位置 | 强制性 |
|------|----------|--------|
| 公共接口 | Service/API 入口方法 | **必须** |
| 测试文件 | 每个测试用例 | **必须** |
| 内部实现 | 复杂逻辑 | 可选 |

## 自顶向下开发模式

> 先定义骨架，后填充细节。确保追溯链在代码生成时就建立。

### 开发流程（双 Agent 模型）

```text
Step 0.5: Sprint Contract（Test Agent 生成，编排器审核）
        ├── 输入：AC 列表 + 当前代码上下文 + 系统设计
        ├── 产出：验收契约（函数签名、返回值、边界条件、异常场景）
        └── 编排器审核：过度→裁剪，不足→补充
                │
                ▼
Step 1: Test Agent（独立子 Agent）
        ├── 输入：系统设计（接口+行为契约）+ 测试用例 + 需求 + Sprint Contract
        ├── 生成接口骨架（签名 + @requirement/@satisfies + throw Error）
        ├── 生成测试代码（@verifies/@testcase + 完整断言，约束于 Contract）
        └── 产出：骨架文件 + 测试文件
                │
                ▼
Step 2: 红色验证（编排器执行）
        ├── 运行测试 → 确认新增测试全部失败 + 已有测试无基线外新增失败
        └── 若新测试意外通过 → ⛔ 检查测试有效性
                │
                ▼
Step 3: Impl Agent（独立子 Agent）
        ├── 输入：系统设计（接口+行为契约）+ 测试文件 + 骨架文件
        ├── 实现代码使测试通过（遵循 /code-quality）
        ├── 重构优化（保持测试通过）
        └── 退出条件：所有测试通过
                │
                ▼
Step 4: 完成检查 + 提交（编排器）
        ├── 测试文件不可变校验（diff 检查）
        ├── AC 满足度验证
        ├── 对抗式验证（按层级）
        ├── /code-self-describe --update
        └── Commit 1
```

### 骨架生成约束

- [ ] **接口骨架必须包含完整签名**（参数、返回值、泛型）
- [ ] **接口骨架必须添加追溯标注**
- [ ] **未实现方法必须抛出 Error 并注明任务编号**
- [ ] **测试骨架必须使用 skip/todo 标记**
- [ ] **测试骨架必须添加 @verifies 和 @testcase 标注**

详见 [skeleton-examples.md](references/skeleton-examples.md)

## 分层 TDD 模式

所有层级遵循统一 11 步执行流程，层级标记仅决定各步骤的**强制程度**：

| 层级 | 标记 | 强制步骤 | 推荐步骤 | 可选步骤 |
|------|------|----------|----------|----------|
| **核心逻辑** (Service/Domain) | 🔴 | 全部 11 步 | — | — |
| **接口层** (Controller/API) | 🟡 | 骨架/实现/绿/AC/自描述/提交 | 测试断言/红/重构/验证 | — |
| **UI 层** (Component/View) | 🟢 | 骨架/实现/绿/AC/自描述/提交 | 测试断言/验证 | 红/重构 |
| **基础设施** (DB/Config) | ⚪ | 骨架/实现/绿/AC/自描述/提交 | 测试骨架 | 测试断言/红/重构/验证 |

### TDD 循环（双 Agent 模型）

```text
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Test Agent│ →  │ 红色验证  │ →  │ Impl Agent│
│ 写骨架+  │     │ 编排器确认│     │ 写实现+  │
│ 写测试   │     │ 测试失败  │     │ 重构     │
└──────────┘     └──────────┘     └──────────┘
```

> **⛔ 信息屏障：Test Agent 不得看到实现代码；Impl Agent 不得看到 03-test-\*.md（只看测试代码文件）**（恢复方式：检查子 Agent prompt 中的文件访问列表）。

> **⛔ 测试不可变：Impl Agent 严禁修改 Test Agent 产出的测试代码。测试失败只能修改实现。疑似测试缺陷须 AskUserQuestion 确认后回退 Test Agent 修复。**

> 详见 [execution-flow.md](references/execution-flow.md) 统一任务执行流程 + 强制程度矩阵

## 编排规范（子 Agent 调度）

**所有模式（含单任务）的开发执行和技能调用，必须通过 Task tool 启动子 Agent**：

| 阶段 | 被调度内容 | 调度方式 |
|------|-----------|----------|
| **验收契约** | Test Agent：Sprint Contract 生成 → 编排器审核 | Test Agent 产出 + 编排器轻量审核 |
| **测试编写** | Test Agent：骨架 + 测试代码（约束于 Contract） | Task tool 子 Agent |
| **红色验证** | 运行测试确认失败 | 编排器轻量执行 |
| **实现编写** | Impl Agent：实现 + 重构 | Task tool 子 Agent |
| 前置验证 | `/ms-verify --impl` | Task tool 子 Agent |
| UI 对齐 | `/ms-verify --ui` | Task tool 子 Agent |
| 追溯同步 | `/ms-sync` | Task tool 子 Agent |
| 知识沉淀 | `/ms-compound` | Task tool 子 Agent |
| 全量测试 | `/ms-test-run` | Task tool 子 Agent |

### 调度原则

1. **上下文隔离 + 信息屏障**：子 Agent 自行读取文档；Test Agent 和 Impl Agent 可读范围严格隔离（详见编排隔离约束）
2. **摘要传递**：只接收 YAML 摘要，`test_defects` 非空时触发用户确认
3. **测试不可变**：Impl Agent 完成后 diff 测试文件，有变更即为 Blocker
4. **主 Agent 禁止直接执行 TDD**：编排器不写代码——红色验证和断点检测的轻量文件扫描除外

## Skill 协作

| 阶段 | 协作 Skill | 说明 |
|------|-----------|------|
| 写业务代码 | `/code-quality` | MTE 原则、依赖注入、避免过度设计 |
| 写测试代码 | `/testing-guide` | 断言质量、变异测试、覆盖率 |
| UI 实现 | `/ui-orchestrator` | 无障碍、动画、布局约束 |
| 实现审查 | `/ms-verify --impl` | 前置验证：AC 满足度 + 设计一致性（DevDocs 功能开发任务） |
| UI 对齐 | `/ms-verify --ui` | 前置验证：设计稿↔实现对齐（仅 UI 任务 + 有设计稿时） |
| 完成验证 | `/code-quality` + `/testing-guide` | 对抗式验证：多视角审查 |
| 完成检查 | `/code-self-describe` | 更新模块自描述（--update） |
| 代码提交 | `/git-safety` | 使用 git mv/rm 处理文件 |
| 提交信息 | `/commit-convention` | 遵循项目提交规范 |
| 依赖解析 | `/ms-dev-tasks` | 读取任务依赖关系和状态 |
| 任务完成 | `/ms-sync` | 后续：更新追溯矩阵（追溯同步） |
| 知识沉淀 | `/ms-compound` | 推荐：sync 后提取经验模式（批量模式默认执行） |
| 全量测试 | `/ms-test-run` | 批量完成后：全量测试 + 追溯验证（--trace） |

## 约束

### 分层 TDD 约束

- [ ] **所有层级遵循统一执行流程（S1~S12 + S1.5 Contract）**（层级标记仅决定强制程度）
- [ ] **核心逻辑任务必须标记 🔴 强制 TDD**（全部步骤 ■ 必须）
- [ ] **Test Agent 先写测试，Impl Agent 后写实现**（物理隔离）
- [ ] **核心逻辑任务禁止在测试通过前提交**
- [ ] 接口层任务标记 🟡 推荐 TDD
- [ ] UI 层任务标记 🟢 可选 TDD
- [ ] 基础设施任务标记 ⚪ 推荐测试骨架
- [ ] **Test Agent 断言来自行为契约 + 03-test-\*.md，Impl Agent 禁止读取 03-test-\*.md**
- [ ] **Impl Agent 严禁修改 Test Agent 产出的测试代码**（疑似缺陷须 AskUserQuestion 确认）
- [ ] TDD 任务必须包含红-绿-重构三步骤（跨越 Test Agent → 编排器 → Impl Agent）
- [ ] □/○ 步骤跳过时必须在提交信息中记录原因

### 完成检查约束

- [ ] **验收标准 (AC-XXX) 全部满足**
- [ ] **关联测试全部通过**
- [ ] **Review 要点自查完成**
- [ ] 代码追溯标注完整
- [ ] 代码分支覆盖分析完成（可选，**补充性质**，使用 `/testing-guide` 分支分析；业务逻辑分支应回溯为 AC 对应的正式测试）

## 对抗式验证（可选）

> 以不同角色视角审查代码，模拟 "开发 → 审查 → 测试" 的多人协作模式。

### 触发条件

> **层级判定**：任务层级标记（🔴🟡🟢⚪）来自 `04-dev-tasks.md` 中的任务定义，由 `/ms-dev-tasks` 在任务拆分时根据任务分层规则分配。

| 任务层级 | 默认行为 | 手动控制 |
|---------|---------|---------|
| 🔴 核心逻辑 | **自动触发** | `--skip-review` 跳过 |
| 🟡 接口层 | 不触发 | `--review` 启用 |
| 🟢 UI 层 | 不触发 | `--review` 启用 |
| ⚪ 基础设施 | 不触发 | `--review` 启用 |

### 验证流程概要

基础完成检查（AC + 测试 + 标注）→ Phase 1: 代码质量审查（/code-quality 视角）→ Phase 2: 测试完备性审查（/testing-guide 视角）→ Phase 3: 综合报告（Blocker 必须修复 / Suggestion 可跳过）

> **执行对抗式验证时，必须读取 [verification-flow.md](references/verification-flow.md) 获取 AC↔diff 交叉验证规则、发现数量下限、发现分类标准和 --headless 下 Blocker/Suggestion 处理细则。**

### 对抗式验证约束

- [ ] **Blocker 问题必须修复后才能提交**
- [ ] **每个 Phase 必须明确声明当前审查角色**
- [ ] **审查结果必须分级（Blocker/Suggestion）**
- [ ] 核心逻辑任务（🔴）默认触发
- [ ] 修复 Blocker 后必须重新运行验证

### 依赖解析约束

- [ ] **执行前必须完成依赖解析**
- [ ] **循环依赖必须报错终止**（列出循环路径）
- [ ] **已完成依赖跳过**，不重复执行
- [ ] 自动补充未完成的前置依赖到执行队列
- [ ] "进行中"依赖通过 AskUserQuestion 询问用户

### 原子提交约束

- [ ] **每个任务独立提交**，不跨任务合并
- [ ] **代码提交和文档提交分离**（Commit 1: 代码，Commit 2: 文档状态 + trace 同步结果）
- [ ] **提交前必须通过完成检查**
- [ ] 提交后更新 04-dev-tasks*.md 任务状态为 `已完成`
- [ ] `--single-commit` 可将代码+文档合并为单次提交

### 断点续做约束

- [ ] **每个任务开始前执行状态检测**（5 步流水线）
- [ ] **不相关变更必须警告用户**（AskUserQuestion：stash/忽略/终止）
- [ ] **已完成任务自动跳过**
- [ ] 进行中任务分析续做起点（精确定位：S1~S12 + S1.5，含续做 Agent 判定）
- [ ] 文档状态 + Git 历史 + 工作区三重验证

> 详见 [task-orchestration.md](references/task-orchestration.md)

### `--auto-commit` 约束

- [ ] **交互模式（非 headless），用户仍可观察过程**
- [ ] **测试全部通过且无 Blocker 时自动提交，不询问**
- [ ] **出现 Blocker 或测试失败时暂停询问**
- [ ] 与 `--headless` 互斥（`--headless` 已包含自动提交语义）
- [ ] 安全不变量同 `--headless`：测试未通过不提交、Blocker 未解决不提交

### 记忆文件同步约束

- [ ] **任务完成后检查项目根目录是否存在 AGENTS.md**
- [ ] **仅允许更新 `## 当前状态` 章节**（活跃任务编号、进度统计）
- [ ] **禁止修改结构性章节**（Project Overview、Skill Architecture、Conventions 等由 /agent-memory 管理）
- [ ] CLAUDE.md 通过 @AGENTS.md 自动导入，无需同步
- [ ] 仅做文本替换，不调用 /agent-memory
- [ ] 格式须与 `/agent-memory` 模板保持一致
- [ ] 若 AGENTS.md 不存在则跳过

### 编排隔离约束

- [ ] **每任务双 Agent：Test Agent（骨架+测试）→ 红色验证 → Impl Agent（实现+重构）**
- [ ] **Test Agent 禁读 src/ 已有实现；Impl Agent 禁读 03-test-\*.md、01-requirements.md**
- [ ] **编排器在 Impl Agent 完成后 diff 测试文件，有变更即为 ⛔ Blocker**
- [ ] **主 Agent 只做编排和决策，不直接执行 TDD**
- [ ] **依赖扩展后 >1 任务时，自动升级为批量编排**

### 全量测试验证约束

- [ ] **批量模式完成后必须调用 /ms-test-run --trace**
- [ ] 单任务模式不触发全量测试（已在开发中运行自身测试）
- [ ] 全量测试失败不回滚已提交任务
- [ ] 交互模式：AskUserQuestion 询问是否修复失败测试
- [ ] --headless / --auto-commit 模式：记录警告到交付报告，不中断

### 无人值守约束（--headless）

- [ ] **工作区必须洁净**（启动前 + 每任务 Commit 2 后校验）
- [ ] **前置依赖不得处于"进行中"状态**（否则 fail-fast）
- [ ] **fail-fast 后输出续做命令**
- [ ] **修复过程中标注不得删减**
- [ ] **修复过程中断言数量不得减少**
- [ ] **Suggestion 自动跳过**（除非 `--fix-suggestions`）
- [ ] **绝不推送远程**

> 详见 [auto-mode.md](references/auto-mode.md)

## 任务完成流程

Impl Agent 完成后，编排器执行：测试文件不可变校验（diff）→ AC 验证 → 对抗式验证 → 自描述更新 → 提交决策 → 原子提交（Commit 1 代码 + Commit 2 文档）

> 详见 [execution-flow.md](references/execution-flow.md) 完整步骤和强制矩阵
## 提交信息格式

遵循 `/commit-convention` 规范，格式如下：

```markdown
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
```

**type 类型**：feat | fix | refactor | test | docs | chore

## 子 Agent 摘要格式

当本 Skill 作为子 Agent 运行时，返回以下结构化摘要：

```yaml
skill: ms-dev-workflow
status: success | failed
summary:
  headline: "T-03 开发完成，测试全部通过"
  details:
    task: T-XX
    commits:
      code: "abc1234"
      docs: "def5678"
    test_summary:
      passed: X
      failed: 0
      coverage: "XX%"
    blockers_resolved: 0
    suggestions_skipped: 0
    ac_verified: [AC-001, AC-002]
    decision_log: []  # 关键决策事件（Contract 审核、重试、Blocker 修复等）
blockers: []
output_files: []
new_ids: {}
next_recommended:
  skill: ms-sync
```

## 参考资料

- [skeleton-examples.md](references/skeleton-examples.md) - 接口/测试骨架示例
- [execution-flow.md](references/execution-flow.md) - 任务执行流程详解
- [verification-flow.md](references/verification-flow.md) - 对抗式验证流程详解
- [task-orchestration.md](references/task-orchestration.md) - 多任务编排（批量/依赖/断点续做）
- [auto-mode.md](references/auto-mode.md) - 无人值守模式详解
