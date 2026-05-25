# AI Agent Skills

面向**个人开发者**的 AI Agent Skills 模板项目。

包含 21 个 ms- 流程 skill（覆盖 PRD → 需求 → 设计 → 测试 → 开发 → 验证全链路，含 1 个 internal-only 横切 skill）和 10 个独立工具 skill。

> ℹ️ 本 README 中提及的 `@satisfies` / `@verifies` 代码注释属于 **layout.v1 legacy**（layout.v2 起改读 `traceability.yml`；详见 [skills/pipeline/references/layout/docs-layout-migration.md § 执行接口落地状态](skills/pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)）。

兼容 **Claude Code**、**Codex CLI**、**OpenCode** 等遵循 [Agent Skills](https://agentskills.io) 开放标准的 AI 编码工具。

## 安装

### Claude Plugin Marketplace（推荐）

```
/plugin marketplace add ab300819/skills
```

### npx（跨工具通用）

```bash
npx skills add ab300819/skills --list      # 列出所有 skill
npx skills add ab300819/skills@code-quality # 安装单个
```

### 本地部署

```bash
git clone https://github.com/ab300819/skills.git
bash skills/scripts/deploy-skills.sh
```

---

## 快速开始

**不确定用哪个？** 运行 `/ms-pipeline`，2-3 个问题自动路由到合适的流程。

### 常见场景速查

| 你的情况 | 命令 |
|----------|------|
| 有个模糊想法，想探索需求 | `/ms-prd` |
| 有明确需求，全新项目 | `/ms-pipeline init` |
| 已有项目，加新功能 | `/ms-pipeline feature` |
| 修 Bug | `/ms-pipeline bugfix` |
| 写完代码，文档没跟上 | `/ms-sync` |
| 接手项目，快速了解 | `/ms-onboard --read` |
| 已有项目，想规范化 | `/ms-retrofit` |
| 检查质量 | `/ms-verify` |
| 周期收尾 | `/ms-pipeline close` |

---

## 工作流详解

### PRD 流程（需求发现）

适用于**模糊想法**或**已有 PRD 文档**，独立于 DevDocs，通过 `--from-prd` 桥接。

#### 常用命令

| 命令 | 用途 |
|------|------|
| `/ms-prd` | 自动检测输入（短想法 → 头脑风暴，大文档 → 结构化解析） |
| `/ms-prd --revise FR-03` | 修改单个需求，重新进入 brainstorm |
| `/ms-prd list` | 查看所有 PRD 及其状态 |
| `/ms-prd status <prd_id>` | 查看指定 PRD 详情 |
| `/ms-prd archive <prd_id>` | 归档已完成的 PRD |

#### 你会经历的流程

**路径 A：从想法开始**（输入 < 200 字）

```
"我想做一个 XX 系统" → /ms-prd
    │
    ├── 5W1H 探索（系统引导你回答核心问题）
    ├── 识别用户角色 + 用户旅程
    ├── 发散所有可能功能 → MoSCoW 收敛优先级
    ├── 输出 FR-XX / NFR-XX 需求文件
    └── 成熟度评估：idea → draft → ready
```

**路径 B：从已有 PRD 文档开始**（输入 > 2000 字）

```
提供 PRD 文档（md/PDF/截图）→ /ms-prd
    │
    ├── 自动按主题分片，保留原文
    ├── 为每个分片生成指纹（用于后续变更追踪）
    ├── 逐块 brainstorm 澄清（深度自适应）
    ├── 跨块综合：提取术语表、共享约束、冲突检测
    └── 成熟度评估 + 就绪检查（6 项门控）
```

> 200~2000 字之间的输入，系统会主动询问你走哪条路径。

#### PRD 文档更新

当原始需求文档有变更时，直接用更新后的文档重新运行 `/ms-prd`，系统**自动增量处理**：

| 检测结果 | 处理方式 |
|----------|----------|
| 整个文档指纹相同 | 跳过，无变化 |
| 某块内容未变 | 保留（`clarified`），不重新处理 |
| 某块内容变了 | 标记 `outdated`，触发重新 brainstorm |
| 新增章节 | 标记 `pending`，作为新块处理 |
| 删除章节 | 标记 `removed`，保留记录但不删除文件 |

如果只想修改单个需求：`/ms-prd --revise FR-03`，定位后单独重新 brainstorm。

#### 产出与衔接

- 产出文件：`docs/prd/<prd_id>/requirements/FR-XX-*.md` + `index.md`
- 成熟度达到 `ready` 后，运行 `/ms-requirements --from-prd` 进入 DevDocs

---

### Dev 流程（任务拆分 + 开发执行）

将设计文档拆为可执行任务，以骨架优先 + 分层 TDD 方式逐个实现。

#### 常用命令

**任务拆分：**

| 命令 | 用途 |
|------|------|
| `/ms-dev-tasks` | 标准任务拆分（逐步确认） |
| `/ms-dev-tasks --fast` | 跳过确认，直接生成 |

**开发执行：**

| 命令 | 用途 |
|------|------|
| `/ms-dev-workflow T-03` | 执行单个任务 |
| `/ms-dev-workflow T-01~T-05` | 执行任务范围 |
| `/ms-dev-workflow T-01,T-03,T-07` | 执行指定任务列表 |
| `/ms-dev-workflow F-001` | 执行某功能的所有任务 |
| `/ms-dev-workflow --all` | 执行所有未完成任务 |
| `/ms-dev-workflow --headless` | 无人值守批量执行，自动决策 |
| `/ms-dev-workflow --auto-commit` | 测试通过自动提交（遇 Blocker 停止） |

#### 任务拆分：你会经历的流程

```
需求 + 设计 + 测试用例（前置文档准备好）→ /ms-dev-tasks
    │
    ├── 从设计模块映射为可执行任务
    ├── 按层分类：🔴 核心逻辑 / 🟡 API / 🟢 UI / ⚪ 基础设施
    ├── 构建任务依赖图
    ├── 每个任务控制在 ≤4h
    └── 输出 04-dev-tasks.md
```

#### 开发执行：你会经历的流程

每个任务的执行过程（自动处理，你可以观察或在关键点干预）：

```
/ms-dev-workflow T-03
    │
    ├── 1. 检查依赖任务是否已完成（缺失自动前置）
    ├── 2. 生成接口骨架 + 测试骨架
    ├── 3. Red：运行测试 → 确认新测试失败（预期）
    ├── 4. Green：编写实现直到测试通过
    ├── 5. Refactor：重构优化
    ├── 6. 对抗验证（🔴 任务自动执行，其他用 --review 触发）
    │       ├── 代码质量审计
    │       ├── 测试完整性审计
    │       └── 🟢 UI 任务额外 UI 质量自检
    ├── 7. 原子提交（代码一个 commit，文档一个 commit）
    └── 8. 更新任务状态为 completed
```

**中断恢复**：任务中断后再次运行同一命令，系统检测断点精确恢复到中断的步骤。

#### 产出

- 代码提交（带任务/AC/测试引用）
- `04-dev-tasks*.md` 任务状态更新
- 批量模式结束后自动调用 `/ms-test-run --trace`

---

### Test 流程（测试设计 + 测试执行）

从验收标准设计测试用例，执行并验证全链路追溯。

#### 常用命令

**测试设计：**

| 命令 | 用途 |
|------|------|
| `/ms-test-cases` | 标准测试用例设计 |
| `/ms-test-cases --fast` | 跳过确认，自动选择测试类型 |

**测试执行：**

| 命令 | 用途 |
|------|------|
| `/ms-test-run` | 运行全部测试（UT → IT → E2E） |
| `/ms-test-run --ut` | 仅运行单元测试 |
| `/ms-test-run --it` | 仅运行集成测试 |
| `/ms-test-run --e2e` | 仅运行端到端测试 |
| `/ms-test-run F-001` | 运行某功能的所有测试 |
| `/ms-test-run --trace` | 运行全部 + 追溯性验证 |
| `/ms-test-run --affected` | 仅运行 git diff 影响的测试 |

#### 测试设计：你会经历的流程

```
需求 + 设计文档准备好 → /ms-test-cases
    │
    ├── 解析所有 AC（验收标准）
    ├── 按 AC 性质自动选择测试类型：
    │     输入校验规则 → UT
    │     业务逻辑     → UT + IT
    │     用户交互流程 → E2E
    │     跨功能流程   → Journey
    ├── 按功能批量设计（首批作为质量锚）
    ├── 生成追溯矩阵：AC → UT/IT/E2E 映射
    └── 输出 03-test-cases.md（含子文件）
```

#### 测试执行：你会经历的流程

```
/ms-test-run --trace
    │
    ├── 1. 检测测试框架（Jest/Vitest/pytest 等，不确定会问你）
    ├── 2. 分层执行：UT → IT → E2E
    │       └── UT 全部失败时会确认是否继续
    ├── 3. 收集结果：通过/失败/跳过 + 覆盖率
    ├── 4. 追溯验证（--trace）：
    │       ├── 扫描代码中的 @verifies 注解
    │       ├── 检查每个 AC 是否被通过的测试覆盖
    │       └── 标记未覆盖的 AC
    └── 5. 输出 05-test-report.md
```

#### 产出

- `03-test-cases.md`（及 `03-test-unit.md`、`03-test-integration.md`、`03-test-e2e.md`）
- `05-test-report.md`（含通过率、覆盖率、失败详情、追溯矩阵）

---

### UI/UX 设计稿与组件库

设计资产不是必须的，但提供后会贯穿整个流程，提升 UI 相关需求、任务和验证的质量。

#### 何时提供

系统会在两个节点**主动询问**你：

1. **`/ms-prd`（Step 0）** — 需求探索阶段
2. **`/ms-requirements`（Step 0.5）** — 需求编码阶段

询问内容：

> **问题 1：是否有 UI/UX 设计稿？**
> - MasterGo（提供短链接或文件 ID）
> - Figma（提供链接或截图）
> - Pencil .pen 文件（提供文件路径）
> - 截图/标注图（提供图片路径）
> - 暂无
>
> **问题 2：是否有 UI 组件库？**
> - 代码包（提供包名，如 `@company/ui-kit`）
> - 本地组件目录（提供路径，如 `src/components/ui/`）
> - 有在线文档/Storybook（提供 URL）
> - 暂无

回答后，系统将设计信息写入 `01-requirements.md` 的 `## 设计资产` 章节，后续所有 skill 自动消费。

#### 支持的设计源及能力差异

| 能力 | MasterGo | Pencil .pen | Figma | 截图 |
|------|----------|-------------|-------|------|
| 组件层级、属性、样式 | ✅ 自动提取 | ✅ 自动提取 | ⚠️ 手动描述 | ⚠️ AI 视觉识别 |
| 交互状态清单 | ✅ 自动提取 | ✅ 自动提取 | ⚠️ 手动描述 | ⚠️ AI 视觉识别 |
| 设计→代码组件映射 | ✅ 自动 | ⚠️ 手动 | ⚠️ 手动 | ❌ |
| 样式 token（颜色、字号、间距） | ✅ 自动 | ✅ 自动 | ⚠️ 手动 | ❌ |

> MasterGo 和 Pencil 能自动提取结构化信息；Figma 和截图需要你手动补充或依赖 AI 视觉分析。

#### 设计信息如何影响各阶段

| 阶段 | 影响 |
|------|------|
| **需求编码** `/ms-requirements` | UI 相关用户故事自动补充交互状态 AC（hover/disabled/error/loading/empty） |
| **系统设计** `/ms-system-design` | 设计稿页面字段 → API 响应结构；用户操作 → API 端点；交互状态 → 错误码 |
| **任务拆分** `/ms-dev-tasks` | 🟢 UI 任务标注 `design_ref`（如 `D-01:登录页`）+ 组件库映射 |
| **开发执行** `/ms-dev-workflow` | 🟢 UI 任务根据设计源自动读取设计信息，实现时优先复用组件库已有组件 |
| **验证** `/ms-verify --ui` | 对比设计稿与实际实现截图，检查布局/样式/交互一致性 |

#### 设计稿晚到怎么办

设计稿可以在**任意阶段补充**，不需要从头重走流程。系统按你当前所处的阶段自动回填：

| 当前阶段 | 你要做的 | 系统自动处理 |
|----------|----------|-------------|
| 需求编码之前 | 下次运行 `/ms-requirements` 时回答询问 | 写入设计资产章节 |
| 系统设计之前 | 手动补充到 `01-requirements.md` | 设计驱动 API 结构调整 |
| 任务已拆分 | 手动补充到 `01-requirements.md` | 🟢 UI 任务补充 `design_ref` 和组件映射 |
| 开发进行中 | 手动补充到 `01-requirements.md` | 运行 `/ms-verify --ui` 生成差异报告 |

> 设计稿**更新**时需你主动声明（系统不做自动检测），声明后按当前阶段执行对应回填。

---

### 完整路径：从想法到上线

```
/ms-prd                 想法/文档 → FR-XX/NFR-XX（成熟度 ready）
    ↓
/ms-requirements        --from-prd 导入 → F/US/AC 编码
    ↓
/ms-system-design       技术架构设计
    ↓
/ms-test-cases          AC → UT/IT/E2E 测试用例
    ↓
/ms-dev-tasks           设计 → T-XX 任务（≤4h，依赖图）
    ↓
/ms-verify --readiness  就绪检查（⛔ P1 必须修复）
    ↓
/ms-dev-workflow        骨架优先 + 分层 TDD → 代码提交
    ↓                   批量模式自动调用 /ms-test-run --trace
/ms-verify --impl       实现验证
    ↓
/ms-sync                文档同步（trace + audit）
    ↓
/ms-compound            知识沉淀（提取经验模式）
```

---

## DevDocs 文档治理体系

> DevDocs 不仅是流程模板，还自带一套**文档生命周期治理框架**，防止文档随项目演进而腐化（编号自造、单文件膨胀、追溯断裂、代码注释污染、命名形式主义等）。
>
> 治理框架完整 spec 位于 [`skills/pipeline/references/layout/`](skills/pipeline/references/layout/) 目录。

### 根本问题：DevDocs 的三职责困境

治理框架的起点是识别出一个本质矛盾：**DevDocs 被迫同时承担三种性质截然不同的职责**，导致用 Markdown 单文件累积大表难以为继。

| 职责 | 性质 | 累积期的表现 |
|------|------|------------|
| **数据库**（编号 + 索引 + 引用关系）| 结构化数据 | 单文件累积 → 越来越难查找/更新 |
| **版本边界**（layout / id / trace 演进）| 治理规则 | 规则与产物混在一起 → skill 升级带不动文档体系 |
| **代码追溯**（AC ↔ 测试 ↔ 实现）| 跨载体映射 | 代码内 `@satisfies` 注释 → 公共项目场景下污染代码 |

**治理核心**：把这三件事**拆开**，分别用合适的工具治理：

```
数据库职责    → layout.v2 一文件一编号 + index.md 索引化 + SSOT lint
版本边界职责  → 三层版本号（docs_layout / id_scheme / traceability）+ realign 命令
代码追溯职责  → traceability.yml 外置追溯（代码保持干净）
```

### 实战痛点（治理框架的具体依据）

治理框架不是凭空设计，而是来自一个真实项目（`mic-en`，跨 17 sprint / 半年研发期 / 80+ 文档）暴露的具体问题：

| 问题域 | 实际状况 | 暴露的本质矛盾 | 治理回应 |
|--------|---------|-------------|---------|
| **单文件膨胀** | `04-dev-tasks.md` 累计到 700 行，含 17 sprint 累积摘要 | DevDocs 当作数据库用，但 Markdown 无法承载结构化查询 | #2 一文件一编号 + sprint 分组折叠 + index.md 索引化 |
| **编号自造** | `INS-XXX` 混合 3 种语义（决策 + 经验沉淀 + 一次性观察）；`BUG-XXX` 非社区主流 | 编号语义不收敛，难以工具化解析 | #1 BUG → ISSUE / INS 拆 ADR/PATTERN/NOTE |
| **代码污染** | 636 处 `@satisfies` / `@verifies` 注释嵌入代码 | DevDocs 元信息侵入代码（公共项目场景不可接受）| #4 trace.v1 外置追溯 + legacy 注释保留窗口 |
| **追溯断裂** | INS-018 / T-145 / BUG-045+046：DTO 新字段未传播到 controller-service-mapper 全链 | 缺少机器可检测的 AC ↔ 实现映射 | `/ms-verify --impl` 盲区 7（SPI DTO 透传完备性）+ #4 traceability.yml（提供机器可检测的映射）|
| **测试断言弱化** | V0.9.x P15 / T-157：IT 测试 setup 完整但断言只验状态码不验载荷 | 测试用例与 AC 失耦 | `/ms-verify --impl` 盲区 6（IT 断言完备性）|
| **版本占位** | **0 release tag + 未上线 production**，但文档累积 ~2,000 处 V<x.y.z> 引用，演化出 V0.9.x 占位、V1.0 候选冻结大重构、P 编号跨多 V 累计 | 无 git tag → 文档被迫承担版本边界 | `/ms-iteration-policy` 横切：研发阶段命名策略 |
| **追溯不可逆** | 文档大量出现 `V0.9.x P17` 字面占位 + Sprint 节奏与 V 节奏脱钩 | 命名约定回潮难防 | iteration-policy baseline + AGENTS.md 项目阶段约定段 |

每个问题对应一个或多个治理产物，6 大原则 + 6 阶段 spec + 横切 skill 的设计都是对这些实战痛点的系统化回应（**先有问题，后有方案**）。

### 6 大治理原则（用户驱动）

| # | 原则 | 落地 |
|---|------|------|
| 1 | **编号体系标准化** — 避免自造（BUG → ISSUE 等社区主流） | id.v2 双轨 |
| 2 | **主文件只记索引** — 按编号一文件一文件夹 | layout.v2 目录树 |
| 3 | **单一事实源（SSOT）** — 按归属放置，其他引用 | SSOT lint（12 规则）|
| 4 | **不污染代码注释** — DevDocs 元信息走 `traceability.yml`，代码保持干净（主仓 + 子仓策略）| trace.v1 外置追溯 |
| 5 | **每次迭代蒸馏** — 代码是唯一事实源，DevDocs 是辅助 | 13 类蒸馏动作 |
| 6 | **Skill 升级带文档体系升级** — 避免新 skill 跑在旧文档体系 | 三层版本号 + spec_version |

### 三层版本号体系

DevDocs 用三层独立版本号治理（解耦演进，强依赖联动）：

| 层 | 字段 | 治理对象 | 当前可选 |
|---|------|---------|---------|
| **目录结构** | `docs_layout_version` | 顶层目录树 + SSOT 强约束 | `layout.v1` / `layout.v2` |
| **编号体系** | `id_scheme` | 编号前缀清单 + alias 兼容 | `id.v1` / `id.v2` |
| **代码追溯** | `traceability_version` | trace.yml schema + 漂移检测 | `trace.v0` / `trace.v1` |

声明位置：项目 `AGENTS.md` 的 `devdocs:` frontmatter 段。

```yaml
---
devdocs:
  docs_layout_version: layout.v2
  id_scheme: id.v2
  traceability_version: trace.v1
  initialized_at: "2026-05-15"
---
```

**强依赖**：`layout.v2` 要求 `id.v2` + `trace.v1`；违反 → skill 阻塞 + 推荐 `/ms-pipeline realign --docs-layout` 升级。

#### 用哪个版本？

| 你的项目状态 | 推荐版本 | 原因 |
|------------|---------|------|
| 既有项目（已有 DevDocs 文档）| **保持 `layout.v1`** | 等 `realign` runtime 落地后再迁移；现在迁移需手动维护，成本高 |
| 全新项目，普通规模 | **使用 `layout.v1`** | runtime 完整可用；spec 已就绪但 v2 工具链待完善 |
| 全新实验项目 + 用户明确接受手动治理 | 可声明 `layout.v2` | 享受目录结构清晰 / SSOT 强约束，但 lint/distill 等自动工具暂不可依赖（命令处于 [FUTURE]），需手动按 spec 维护 |
| `mic-en` 等历史大项目 | **维持 `layout.v1` 不迁移** | 数千处 `@satisfies/@verifies` legacy 注释，等 `extract-trace` runtime + 用户主动调用 `realign` 才迁移 |

### 6 阶段治理 Spec

治理框架按 6 阶段组织（spec 已成文，runtime 仍按 [FUTURE] 状态逐步落地）：

| 阶段 | spec | 内容 |
|------|------|------|
| **#6 治理框架（仲裁层宪法）**| [layout-versioning-policy.md](skills/pipeline/references/layout/layout-versioning-policy.md) | 三层版本号语义 + 升级规则 + 兼容性矩阵 |
| **#1 编号体系（id.v2 双轨）**| [id-scheme-implementation.md](skills/pipeline/references/layout/id-scheme-implementation.md) | F→FEAT / T→TASK / BUG→ISSUE 等；INS 拆 ADR/PATTERN/NOTE |
| **#2 文件夹组织**| [folder-organization-implementation.md](skills/pipeline/references/layout/folder-organization-implementation.md) | 目录树 + 一文件一编号 + sprint 分组 + modules 拆分 |
| **#3 SSOT lint**| [ssot-lint-implementation.md](skills/pipeline/references/layout/ssot-lint-implementation.md) | 12 lint 规则 + baseline 防篡改 + CI 集成 |
| **#4 代码解耦**| [code-decoupling-implementation.md](skills/pipeline/references/layout/code-decoupling-implementation.md) | trace.v1 写入 API + legacy 注释保留窗口 + 多仓聚合 |
| **#5 迭代蒸馏**| [distillation-implementation.md](skills/pipeline/references/layout/distillation-implementation.md) | 13 类蒸馏动作 + 4 级安全门 + rollback + git hook 反循环 |

### 治理盲区主动审查（scope=health）

6 阶段 spec 治理"如何升级文档体系"，health scope 治理"已有文档体系是否健康"。两者正交：

| 维度 | 检查内容 | 实装 rule |
|------|----------|----------|
| a 结构正确性 | frontmatter + spec_version + 设计文档 ADR ↔ 正文同期修订 | schema-drift + `design/adr-only-revision` |
| b 索引/链接正确性 | 编号引用文件存在性 + 追溯矩阵完整性 | ms-sync trace + `health/dead-link` |
| c 过大文档识别 | devdocs-state.md byte 阈值 / 单行长度 / 内嵌禁用模式 | `state/total-size-cap` + `state/line-length-cap` + `state/forbidden-content` |
| d SSOT 遵从（layout.v2 only）| 占位/索引不复制权威源内容 | `ssot/no-restatement` [FUTURE] |
| e 三层分离 [FUTURE] | 决策/执行/数据章节关键词混杂 | 待 keyword baseline 定义 |

**关键设计**：
- health-lint 5 条 [新增] rule 与 layout.v2 的 ssot-lint 12 条 rule **独立**，layout.v1 项目（mic-en）可直接使用
- `devdocs-state.md` 模板硬化（forbidden 6 类内嵌模式 + 200/500/40K 三档阈值）+ `agent-memory --update` 健康度自检（双重保险）
- `design/adr-only-revision` 把 system-design 既有 ⛔ 硬约束（仅追加 ADR 不改正文）从人工自检升级为 git 历史自动扫描

详见 [realign-scope-health.md](skills/pipeline/references/realign-scope-health.md) + [health-lint-implementation.md](skills/pipeline/references/health-lint-implementation.md)。

### PRD 流程治理 Spec（轻量同类，已显性化）

PRD 流程（ms-prd / ms-prd-brainstorm / ms-prd-parser）承担**部分相同**的耦合（数据库 + 修订边界），但**不直接面对代码追溯**（通过 DevDocs 间接）。治理机制已齐备但散落在 4 个文件，需收纳显性化而非重建 6 阶段框架。

| spec | 内容 | 状态 |
|------|------|------|
| [prd-index-ssot.md](skills/prd/references/governance/prd-index-ssot.md) | FR/NFR 全局 SSOT + 最大值续编 + 冲突检测 + 跨 PRD 引用边界 | [现状] |
| [prd-revision-policy.md](skills/prd/references/governance/prd-revision-policy.md) | 4 类变更边界统一规则（PRD 生命周期 / 单 FR / chunk / 模板）| [现状] |
| [prd-devdocs-mapping.md](skills/prd/references/governance/prd-devdocs-mapping.md) | mapping 状态机（active/outdated/remapped/removed）+ 回扫责任分界 | [现状] |

> **与 DevDocs 6 阶段的差异**：PRD 治理 ~85% 是收纳已有机制（chunk 指纹 / `--revise` / `--back-propagate-prd` / mapping_status），~15% 是必要边界补齐；总行数 413（vs DevDocs 治理 ~2700），保持轻量定位。

### 治理工具命令

#### 统一升级入口（综合方案落地）

所有文档体系升级 + 健康度审查动作统一通过单一入口，不再以散落 flag 形式暴露：

```bash
/ms-pipeline realign [--scope=<spec|layout|prd-mapping|health>] [--target=<path>] [--dry-run|--apply]
```

| scope | 用途 | 状态 |
|-------|------|------|
| `spec`（默认）| 产物 `spec_version` drift（schema 维度）| ✅ 部分可用 |
| `layout` | layout.v1 → v2 迁移（含编号/目录/追溯重组）| ✅ **执行接口已落地**（详见 [realign-scope-layout.md](skills/pipeline/references/realign-scope-layout.md)）|
| `prd-mapping` | PRD mapping_status 扫描 + 报告 | [FUTURE] |
| `health` | 文档健康度主动审查（5 维度 / health-lint 5 条 rule）| ✅ **执行接口已落地**（详见 [realign-scope-health.md](skills/pipeline/references/realign-scope-health.md)）|

**Apply 6 Phase**：checkpoint → file_ops → id_map → trace → frontmatter → post-validation；每 Phase 单独 commit；失败 ⛔ + `git reset --hard <checkpoint_commit>` 回滚；plan_hash 校验中断恢复一致性。

**deprecated alias**：`--docs-layout` 等价于 `--scope=layout`，保留 1 版本后移除。

#### 验证工具

| 命令 | 用途 | 状态 |
|------|------|------|
| `/ms-verify --impl` | 实现验证（含盲区 6: IT 断言完备性 + 盲区 7: SPI DTO 透传完备性）| ✅ 可用 |
| `/ms-verify --docs` | 文档层间对齐验证 | ✅ 可用 |
| `/ms-verify --ui` | UI 与设计稿对齐 | ✅ 可用 |
| `/ms-verify --readiness` | 开发前就绪检查 | ✅ 可用 |
| `/ms-verify --schema-drift` | drift 三态报告（schema + layout 两段呈现）| ✅ 可用 |
| `/ms-verify --ssot-lint` | 跑 12 条 SSOT lint 规则（layout.v2 专属，v1 报 not_applicable）| [FUTURE] |
| `/ms-pipeline realign --scope=health` | 健康度主动审查（5 条 [新增] rule，layout.v1+v2 通用）| ✅ 可用 |

#### 已收敛 / internal-only（不再用户面暴露）

| 命令 | 处理 |
|------|------|
| `/ms-pipeline realign --docs-layout` | → `--scope=layout`（deprecated alias 1 版本）|
| `/ms-pipeline realign --classify-ins/--rename-id/--archive-v1` | → 由 `--scope=layout` Phase 自动处理 |
| `/ms-verify --layout-drift` | → 合并到 `--schema-drift`（报告含 layout drift 段）|
| `/ms-sync --extract-trace/--refresh-traceability` | → 由 `realign --scope=layout` Phase 4 编排，不暴露 |
| `/ms-sync --schema-drift` | → 迁移到 `/ms-verify --schema-drift`，统一 drift 报告 |
| `/ms-sync --check/--absorb` | → 合入 `/ms-sync` 默认流程 |
| `/ms-iteration-policy` | → internal-only，由 `/ms-pipeline realign --scope=layout` 编排调度 |

> ℹ️ `/ms-pipeline distill`（迭代蒸馏，13 类动作）是独立的治疗型治理命令，**不属于 realign 入口**；当前状态 [FUTURE]。

### 综合方案落地（单一入口 + flag 收敛）

针对"已膨胀 DevDocs 项目（如 mic-en）需要规范化升级 + skill 子命令膨胀给用户/作者带来认知成本"两个痛点，综合方案落地 5 步：

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | `/ms-pipeline realign --scope=layout` 执行接口（6 Phase + plan_hash + git reset 回滚）| ✅ |
| 2 | SKILL.md 移除 deprecated flag | ✅ |
| 3 | 各 skill SKILL.md 收敛 ≤5 外露 flag | ✅ |
| 4 | `shared-constraints.md § 8` 新增 single-entry 规则族 | ✅ |
| 5 | `ms-iteration-policy` 标 internal-only | ✅ |
| 6 | `--scope=health` 健康度主动审查（health-lint 5 条 rule + devdocs-state 模板硬化 + ADR↔正文同期修订检测）| ✅ |

**用户面 flag 总收敛 49 → 20（-59%）**：

| Skill | 原 | 新 |
|-------|---:|---:|
| ms-pipeline | 19+ | 8 入口 |
| ms-verify | 14 | 5 |
| ms-sync | 8 | 3 |
| ms-requirements | 8 | 4 |
| ms-iteration-policy | 10 | 0（internal-only）|

### 共享约束 SSOT

[`skills/_shared/constraints.md`](skills/_shared/constraints.md) 是跨 skill 协议层共性的单一权威源（274 行 / 99 rule_id），覆盖：

- § 1 门控标记 SSOT（⛔/⚠️/ℹ️ 语义 + 恢复方式格式）
- § 2 yaml-summary-v1 envelope（4 status 值域 + 保留字段）
- § 3 Task 委托规则（最小握手协议）
- § 4 FUTURE 状态三态（[现状]/[新增]/[FUTURE]）
- § 5 用户确认 / AskUserQuestion
- § 6 只读 / dry-run 命名
- § 7 Recovery 格式（4 字段模板）
- § 8 realign / spec_version + **single-entry 规则族**

各 ms- skill 顶部通过聚合声明引用，不复制规则，避免散落 drift。

### 治理设计的关键选择

1. **诚实声明**：参与 DevDocs 治理并声明 `writes_*` 字段的 A/B 类写入 skill（9 个）当前保持 `layout.v1` / `id.v1` / `trace.v0`（"声明 = 行为"对齐；独立工具 skill 和只读 skill 不在此列）。spec 起草完成 **≠** runtime 就绪 — 4 条件全满足（spec + template + runtime + 至少 1 个 v2 项目验证）才升 v2，避免"声明先行陷阱"。

2. **核心目录树 vs 执行层扩展**：layout.v2 强制目录树（requirements/design/tests/tasks/issues/patterns/notes）受 foundation 治理；衍生派生项（`_archived/` / `design/modules/` / `tests/index.md`）属执行层扩展，不污染 foundation。

3. **蒸馏 ≠ 归档**：蒸馏（distillation）= 知识压缩 + 结构优化（产物仍在主目录）；归档（archive）= 已完成项目搬移到 `_archived/`。两者明确分离。

4. **预防型 vs 治疗型**：`ms-iteration-policy` 是 **预防型**（源头治理 V<x.y.z> 形式主义），`ms-pipeline distill` 是 **治疗型**（已成型文档的压缩）。`init` 阶段先用 iteration-policy 立约 → 累积期用 distill 周期蒸馏。

5. **历史项目兼容**：`mic-en` 等 layout.v1 项目维持现状，**不主动迁移**。任何升级必须用户显式调用 `/ms-pipeline realign --docs-layout`。

6. **PRD 治理走轻量同类，不复制 6 阶段**：PRD 不直接追代码（通过 DevDocs 间接），且核心机制已存在；治理目标是显性化已有规则而非发明新体系。具体落地见上文「PRD 流程治理 Spec」。

---

## 全部 Skill

### 编排层（用户主入口）

| Skill | 命令 | 用途 |
|-------|------|------|
| 工作流编排器 | `/ms-pipeline` | 顶层入口，6 个模式（init/feature/bugfix/verify/close/insights） |
| 产品需求编排 | `/ms-prd` | 模糊想法/大型 PRD → 结构化需求 |
| 新功能 | `/ms-feature` | 已有项目追加新功能（含 lite/full 模式） |
| Bug 修复 | `/ms-bugfix` | 测试先行的 Bug 修复 |

### PRD 流程 Skill

| Skill | 命令 | 用途 |
|-------|------|------|
| 需求探索 | `/ms-prd-brainstorm` | 5W1H → 用户旅程 → MoSCoW 收敛 |
| 文档解析 | `/ms-prd-parser` | 大型 PDF/md/截图 → 结构化分片 |

### DevDocs 流程 Skill

| Skill | 命令 | 用途 | 输出 |
|-------|------|------|------|
| 需求编码 | `/ms-requirements` | 功能点/用户故事/验收标准 | `01-requirements.md` |
| 系统设计 | `/ms-system-design` | 技术架构、API、数据模型 | `02-system-design*.md` |
| 测试设计 | `/ms-test-cases` | UT/IT/E2E/Journey 测试用例 | `03-test-*.md` |
| 任务拆分 | `/ms-dev-tasks` | 可执行的开发任务 | `04-dev-tasks*.md` |
| 开发执行 | `/ms-dev-workflow` | 骨架优先 + 分层 TDD + 双 Agent 隔离 | 代码 |
| 测试执行 | `/ms-test-run` | 运行测试 + 追溯验证 | `05-test-report.md` |
| 统一验证 | `/ms-verify` | --docs / --impl / --ui / --readiness | 验证报告 |
| 文档同步 | `/ms-sync` | trace + audit + archive | 更新追溯矩阵 |
| 洞察收集 | `/ms-insights` | 审查/调研结果 → 需求 | `05-insights.md` |
| 知识沉淀 | `/ms-compound` | 提取经验模式 | `patterns/*.md` |
| 暂缓任务池 | `/ms-backlog` | dev-tasks / verify / insights / prd 产生的"暂缓不阻塞"项集中索引 | `docs/devdocs/backlog.md` |
| 项目上下文 | `/ms-onboard` | AI 工具切换时的上下文传递 | `00-context.md` |
| 项目改造 | `/ms-retrofit` | 已有项目适配 DevDocs | 逆向生成文档 |
| 代码盘点 | `/ms-codebase-insight` | 只读分析现有代码库 | `codebase-insight.md` |

### 独立工具 Skill

| Skill | 命令 | 用途 |
|-------|------|------|
| 代码质量 | `/code-quality` | MTE 原则、重构指导、Review 清单 |
| 测试指导 | `/testing-guide` | 断言质量、Mock 规范、变异测试 |
| 重构 | `/refactor` | 系统化重构，测试驱动 |
| 提交规范 | `/commit-convention` | 提交信息格式化 |
| Git 安全 | `/git-safety` | 强制 git mv/rm 规范操作 |
| UI 调度器 | `/ui-orchestrator` | 路由到专业 UI/UX skill |
| 工作报告 | `/work-report` | 周报/月报/季报/年终总结 |
| 代码自描述 | `/code-self-describe` | 模块级 CLAUDE.md + 文件头注释 |
| 记忆管理 | `/agent-memory` | AI agent 记忆文件管理 |

---

## 开发路径选择

| 场景 | 路径 | 说明 |
|------|------|------|
| 需求明确 | `/ms-pipeline init` | requirements → design → tests → tasks → dev |
| 有模糊想法 | `/ms-prd` → `/ms-pipeline init` | 先探索需求，再走标准流程 |
| 已有项目加功能 | `/ms-pipeline feature` | 增量更新全套文档 |
| 已有代码无文档 | `/ms-retrofit` | 从代码逆向生成 DevDocs |
| 探索性原型 | 先写代码 → `/ms-retrofit` | 代码稳定后补文档 |
| Bug 修复 | `/ms-pipeline bugfix` | 写失败测试 → 修复 → 通过 |
| 小改动 | 直接提交 | 遵循 `/commit-convention` |

---

## 编号体系

DevDocs 使用统一编号实现需求到代码的全链路追溯：

```
F-001 (功能点)
  └── US-001 (用户故事)
        └── AC-001 (验收标准)
              ├── UT-001 → @verifies AC-001（代码标注）
              ├── IT-001
              └── E2E-001
                    └── T-01 (开发任务) → @satisfies AC-001（代码标注）
```

| 前缀 | 含义 | 来源 |
|------|------|------|
| FR-XX / NFR-XX | PRD 阶段需求 | `/ms-prd` |
| F-XXX | 功能点 | `/ms-requirements` |
| US-XXX | 用户故事 | `/ms-requirements` |
| AC-XXX | 验收标准 | `/ms-requirements` |
| UT/IT/E2E/Journey | 测试用例 | `/ms-test-cases` |
| T-XX | 开发任务 | `/ms-dev-tasks` |
| INS-XXX | 洞察建议 | `/ms-insights` |
| BUG-XXX | Bug 记录 | `/ms-bugfix` |

> ℹ️ **`ms-backlog` 复用现有编号，不新增 B-XXX**。暂缓条目在 `docs/devdocs/backlog.md` 中用 `source_id + entry_no` 作局部锚点（如 `F-01#1`），状态机仅 `parked → reactivated|closed|superseded`。详见 [ms-backlog SKILL.md](skills/backlog/SKILL.md)。

---

## 文件结构

```
docs/
├── prd/                          # PRD 流程产出
│   ├── requirements/index.md     # 需求总纲
│   ├── requirements/FR-XX-*.md   # 各功能需求
│   └── chunks/                   # PRD 原文分片
│
├── devdocs/                      # DevDocs 流程产出
│   ├── 00-context.md             # 项目上下文（/ms-onboard）
│   ├── 01-requirements.md        # 需求文档
│   ├── 02-system-design*.md      # 系统设计
│   ├── 03-test-*.md              # 测试用例
│   ├── 04-dev-tasks*.md          # 开发任务
│   ├── 05-test-report.md         # 测试报告
│   ├── 05-insights.md            # 洞察日志
│   ├── 05-bugfix-log.md          # Bug 修复日志
│   └── patterns/                 # 经验模式库（/ms-compound）
│
└── codebase-insight.md           # 代码盘点（/ms-codebase-insight）
```

---

## 大型需求最佳实践

基于 [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) 的 Generator-Evaluator 分离、Sprint Contract、最小可行 Harness 等设计模式，结合 ms- 流程的推荐使用方式：

### 1. 需求阶段拉长，开发阶段提速

用 `/ms-prd` 充分探索需求（对应文章的 Planner Agent 角色），需求清晰后一次性走完 requirements → system-design → test-cases → dev-tasks，开发用 `--headless` 或 `--auto-commit` 批量执行。

### 2. 善用 --readiness 门控

不要跳过 `/ms-verify --readiness`，它相当于文章中的 Sprint Contract 验证——在编码前确认交付规格可测试、依赖无环、路径具体。P1 问题一定修复后再开工，返工成本远大于修复成本。

### 3. 批量执行 + 断点续做

大需求拆成 10-20 个任务后，按依赖顺序用 `F-001` 或范围（`T-01~T-10`）批量执行。中断后直接续做，检查点机制会精确恢复到中断的 Agent 和步骤。每完成一个 Feature 的所有任务后运行 `/ms-sync` + `/ms-verify --impl`。

### 4. 迭代而非一步到位

文章核心经验：**多轮 QA 比一次完美实现更有效**。第一轮 dev-workflow 完成后，运行 `/ms-verify --impl` 找差距，将差距转为 bugfix 或 insight 再次进入开发循环，最后运行 `/ms-compound` 沉淀经验。

### 5. 对抗式验证不要跳过

`--review` 对抗验证对应文章中的独立 Evaluator——外部视角发现自己看不到的问题。文章指出 LLM 对自身输出有正面偏见，分离评估是最有效的质量保障手段。

---

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成文档

## 详细文档

每个 skill 的完整规范见 `skills/<dir>/SKILL.md`。架构决策和约定见 `AGENTS.md`。
