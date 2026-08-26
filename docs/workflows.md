# 工作流详解

> 各流程的逐步走查。新人先读 [README 的「我该用哪个」](../README.md#我该用哪个)，需要细节再看本文。

### PRD 流程（需求发现）

适用于**模糊想法**或**已有 PRD 文档**。独立于 DevDocs，成熟后由编排层桥接进去（桥接是内部动作，你不需要触发它）。

#### 怎么用

`/ms-prd`。输入是短想法还是大文档由它自动判断。

想改某一条需求，说「改 FR-03」；需求上线后想清掉脚手架，说「清理 PRD」——它会先给 dry-run 再动手。**不需要记参数。**

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
    └── 成熟度评估 + 就绪检查
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

只想改某一条需求，说「改 FR-03」即可，它会定位后单独重新 brainstorm。

#### 产出与衔接

- 产出文件：`docs/prd/requirements/FR-XX-*.md` + `index.md`（扁平、单需求脚手架）
- 成熟度达到 `ready` 后，说「把 PRD 导进 DevDocs」——编排层会带着 PRD 产物路径调用 `/ms-requirements`
- 需求 close（上线）后，`docs/prd/` 脚手架可由 `/ms-prd clear`（或 `/ms-pipeline close` 末步）清理 —— 代码 + DevDocs 才是事实源

---

### Dev 流程（任务拆分 + 开发执行）

将设计文档拆为可执行任务，以骨架优先 + 分层 TDD 方式逐个实现。

#### 怎么用

**任务拆分**：`/ms-dev-tasks`。想少确认几步就直说。

**开发执行**：`/ms-dev-workflow` 后面跟你要做的范围——

- 单个任务：`T-03`
- 一段范围：`T-01~T-05`
- 挑几个：`T-01,T-03,T-07`
- 某功能的全部任务：`F-001`
- 剩下没做完的：说「把剩下的都跑完」

**授权类的事要你开口。** 无人值守（不再问你、自动决策）和自动提交都不是默认行为，得你明说，比如「这批你自己跑完别问我」。反过来，不可逆的动作（推送、删除、往代码目录写文件）**不看你开头说了什么，一律在动作发生那一刻再确认一次**——因为二十分钟前的一句话，反映不了你看到中间结果后的判断。

#### 任务拆分：你会经历的流程

```
需求 + 设计 + 测试用例（前置文档准备好）→ /ms-dev-tasks
    │
    ├── 从设计模块映射为可执行任务
    ├── 按层分类：🔴 核心逻辑 / 🟡 API / 🟢 UI / ⚪ 基础设施
    ├── 构建任务依赖图
    ├── 每个任务可独立验收
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
    ├── 6. 对抗验证（高风险任务自动执行，其他任务说一声即可触发）
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
- 批量模式结束后自动跑全量测试 + 追溯校验

---

### Test 流程（测试设计 + 测试执行）

从验收标准设计测试用例，执行并验证全链路追溯。

#### 怎么用

**测试设计**：`/ms-test-cases`。

**测试执行**：`/ms-test-run`，默认按 UT → IT → E2E 全跑。想缩范围直接说——「只跑单测」「只跑 E2E」「只跑 F-001 相关的」「只跑这次改动影响到的」；想同时验追溯链，说「顺便查一下追溯」。

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
/ms-test-run  （并说「顺便查追溯」）
    │
    ├── 1. 检测测试框架（Jest/Vitest/pytest 等，不确定会问你）
    ├── 2. 分层执行：UT → IT → E2E
    │       └── UT 全部失败时会确认是否继续
    ├── 3. 收集结果：通过/失败/跳过 + 覆盖率
    ├── 4. 追溯验证（要求查追溯时）：
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
| **验证** `/ms-verify`（说明要比设计稿）| 对比设计稿与实际实现截图，检查布局/样式/交互一致性 |

#### 设计稿晚到怎么办

设计稿可以在**任意阶段补充**，不需要从头重走流程。系统按你当前所处的阶段自动回填：

| 当前阶段 | 你要做的 | 系统自动处理 |
|----------|----------|-------------|
| 需求编码之前 | 下次运行 `/ms-requirements` 时回答询问 | 写入设计资产章节 |
| 系统设计之前 | 手动补充到 `01-requirements.md` | 设计驱动 API 结构调整 |
| 任务已拆分 | 手动补充到 `01-requirements.md` | 🟢 UI 任务补充 `design_ref` 和组件映射 |
| 开发进行中 | 手动补充到 `01-requirements.md` | 运行 `/ms-verify` 并说明要比设计稿，生成差异报告 |

> 设计稿**更新**时需你主动声明（系统不做自动检测），声明后按当前阶段执行对应回填。

---

### 完整路径：从想法到上线

```
/ms-prd                 想法/文档 → FR-XX/NFR-XX（成熟度 ready）
    ↓
/ms-requirements        导入 PRD 产物 → F/US/AC 编码
    ↓
/ms-system-design       技术架构设计
    ↓
/ms-test-cases          AC → UT/IT/E2E 测试用例
    ↓
/ms-dev-tasks           设计 → T-XX 任务（可独立验收，依赖图）
    ↓
/ms-verify             就绪检查（⛔ P1 必须修复）
    ↓
/ms-dev-workflow        骨架优先 + 分层 TDD → 代码提交
    ↓                   批量模式自动调用 /ms-test-run  （并说「顺便查追溯」）
/ms-verify             实现验证
    ↓
/ms-sync                文档同步（trace + audit）
    ↓
/ms-compound            知识沉淀（提取经验模式）
```

---

## 大型需求最佳实践

基于 [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) 的 Generator-Evaluator 分离、Sprint Contract、最小可行 Harness 等设计模式，结合 ms- 流程的推荐使用方式：

### 1. 需求阶段拉长，开发阶段提速

用 `/ms-prd` 充分探索需求（对应文章的 Planner Agent 角色），需求清晰后一次性走完 requirements → system-design → test-cases → dev-tasks，开发阶段可以授权无人值守批量跑（明说一次即可）。

### 2. 善用开发前的就绪门控

不要跳过开发前的就绪检查（`/ms-verify`），它相当于文章中的 Sprint Contract 验证——在编码前确认交付规格可测试、依赖无环、路径具体。P1 问题一定修复后再开工，返工成本远大于修复成本。

### 3. 批量执行 + 断点续做

大需求拆成 10-20 个任务后，按依赖顺序用 `F-001` 或范围（`T-01~T-10`）批量执行。中断后直接续做，检查点机制会精确恢复到中断的 Agent 和步骤。每完成一个 Feature 的所有任务后运行 `/ms-sync` + `/ms-verify`。

### 4. 迭代而非一步到位

文章核心经验：**多轮 QA 比一次完美实现更有效**。第一轮 dev-workflow 完成后，运行 `/ms-verify` 找差距，将差距转为 bugfix 或 insight 再次进入开发循环，最后运行 `/ms-compound` 沉淀经验。

### 5. 对抗式验证不要跳过

独立对抗验证对应文章中的 Evaluator——外部视角发现自己看不到的问题。文章指出 LLM 对自身输出有正面偏见，分离评估是最有效的质量保障手段。

## 与 superpowers 共存

> 设计与审查记录:[specs/2026-07-22-superpowers-coexistence-design.md](superpowers/specs/2026-07-22-superpowers-coexistence-design.md)(codex 3 轮)。原则:**单向兼容**(superpowers 插件零改动)+ **可选增强、单一路径归一化**(ms- 阶段永远执行并产出权威结果)。

### 路由声明(压制误触发)

DevDocs 项目的 AGENTS.md 含「工作流路由」节(由 `/agent-memory` 幂等维护;init/retrofit 自动发货,存量项目由 pipeline 阶段检测 ℹ️ 提示补齐)。依"用户指令 > skill 默认行为"的通用优先级,该节使 superpowers 的 process skill(brainstorming / systematic-debugging / writing-plans / executing-plans / subagent-driven-development / finishing-a-development-branch 等)在 DevDocs 管理的工作上让位于 `ms-*` 入口;它们仍可用于体系外杂项(一次性脚本、非交付实验、文档体系元改造)。

### 两座产物桥

| 场景 | 通道 | 追溯 |
|------|------|------|
| superpowers writing-plans 产出的计划(**非 DevDocs 项目**) | `/dev-flow` 执行(契约先行+红绿+质量地板) | 零追溯 |
| 一句话任务+验收标准(DevDocs 项目内轻量) | `/ms-dev-workflow`（直接描述任务和验收标准） | 有追溯(AC 落 01,guarded 下限) |

注意:DevDocs 项目内不使用 dev-flow(其自身路由判定亦如此);finishing-a-development-branch 的 merge/push 选项与 DevDocs"绝不推送远程"不变量冲突,任何情况下不接入。

### 能力吸收结论(2026-07-22 三方对齐)

逐项映射后:9 项 superpowers 能力 DevDocs 已有等价或更强;唯一内化项 = ms-bugfix 根因纪律门;worktree 并行为架构级 FUTURE(触发 = 真实并行需求,需先设计工作区所有权/文档 SSOT 合并/review-drain 回收);"委托+fallback"机制经评审否决(语义漂移伤追溯,外部 skill 不承诺 yaml-summary 契约)。

## 文档与代码分仓（shell 拓扑）

**什么时候用**：维护 fork 的开源项目，或自有项目计划公开——DevDocs 的需求 / 设计 / 任务 / 洞察都是私有产物，不该进代码仓。

**怎么开**：

- **任何时候**：`/workspace-topology`。独立 skill，**不拉起 DevDocs**，非 DevDocs 项目也能用。没有声明就问你一次：仓库是 `inline` / `shell` / `linked` 哪种，代码根在哪，答案记进 `AGENTS.md`，此后不再问
- **新项目 / 改造已有项目**：`/ms-pipeline init` 与 `/ms-retrofit` 会在生成 `docs/devdocs/` 后自动委托上面那个 skill，不用你单独跑
- **现有单仓要拆开**：`/workspace-topology`（说明要拆成外壳布局），先选手动还是自动模式（分界在谁把代码仓挪进根目录），执行前给完整 dry-run 计划
- **后期要改**：再跑一次 `/workspace-topology` 就行——幂等，状态一致时零改动。增删代码根、新增子模块都在这里

**开了之后有什么不同**：

| | 变了 | 没变 |
|---|------|------|
| 文档路径 | — | `docs/devdocs/` 等全部不变 |
| 提交 | 一个任务产生 N+1 个 commit（每个变更代码根一个 + 外壳仓一个）| 每个任务独立提交、不跨任务合并的原则不变（inline 下本就是 Commit 1 代码 + Commit 2 文档两次提交，shell 只是把 Commit 1 按变更代码根展开）|
| 代码仓 | 只收代码和测试，commit message 沿用该仓风格、不带 DevDocs 编号 | — |
| 自描述 / 代码注释类产物 | 默认跳过（要写进代码目录须你在动作发生时确认） | — |

**追溯**：外壳仓的 commit 是枢纽——它带 T-XX，body 里记各子模块 SHA。代码仓自身干净得像没有 DevDocs 存在过。
