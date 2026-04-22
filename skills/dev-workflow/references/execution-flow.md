# 任务执行流程详解

各层级任务的详细执行流程。**所有模式（含单任务）均通过双 Agent 模型执行：Test Agent 写骨架+测试 → 编排器红色验证 → Impl Agent 写实现+重构 → 编排器完成检查+提交**。文档同步（/ms-sync + Commit 2）由编排器调度。

## 步骤状态追踪

执行流程中，每步完成后记录状态标记（含 S1.5 Sprint Contract），用于断点恢复时精确定位：

| 步骤 | 对应流程 | 执行者 | 状态标记 |
|------|----------|--------|----------|
| S1 | 读取任务定义 | 编排器 | `task_loaded` |
| S1.5 | Sprint Contract 协商 | Test Agent + 编排器审核 | `contract_agreed` |
| S2 | 生成接口骨架 | Test Agent | `skeleton_interface` |
| S3 | 生成测试骨架 | Test Agent | `skeleton_test` |
| S4 | 编写测试断言（约束于 Contract） | Test Agent | `red_assertions` |
| S5 | 红色验证（确认测试全部失败） | 编排器 | `red_verified` |
| S6 | 实现代码 | Impl Agent | `green_impl` |
| S7 | 重构优化 | Impl Agent | `refactored` |
| S8 | 验证 AC 满足度（逐条完备性 + 声称 vs 实际 diff） | 编排器 | `ac_verified` |
| S9 / Phase 1~3 | 对抗式验证（内置角色演绎） | 编排器 | `int_review_state` ∈ {INT_REVIEWED, INT_PENDING, INT_UNRESOLVED} |
| S9 / Phase 4 | 外部对抗审查（🔴 默认；其他 `--external-review`） | 编排器（embedded-headless 调度器） | `ext_review_state` ∈ {EXT_REVIEWED, EXT_PENDING, EXT_UNRESOLVED, EXT_BLOCKED} |
| S10 | 更新自描述 | 编排器 | `self_describe_done` |
| S11 | 提交代码 | 编排器 | `committed` |
| S12 | 追溯同步 + 知识沉淀 | 编排器 | `synced` |

**断点恢复**：检测到中断时，根据状态标记判定续做 Agent（Test Agent / 编排器 / Impl Agent），从上一个已完成步骤的下一步继续。详见 [task-orchestration.md](task-orchestration.md) 续做模式信号表。

**记录方式**：通过 TodoWrite 跟踪当前步骤状态。批量模式下，编排器维护每个任务的步骤状态。

## 批量编排流程

批量模式（含依赖扩展后 >1 任务的单任务请求）的外层编排流程。纯单任务（队列长度=1）跳过拓扑排序和检查点文件，但**不跳过后置测试校验**——单任务末尾运行 `/ms-test-run --affected`（受变更影响的测试），若 affected 无匹配则回退 `/ms-test-run --trace`：

```
┌─ 外层编排（编排器，轻量上下文）─────────────────────┐
│                                                    │
│  1. 批量指定符解析                                  │
│     └── T-XX~T-YY / F-XXX / US-XXX / --all        │
│                    │                                │
│                    ▼                                │
│  2. 依赖解析 + 拓扑排序                             │
│     └── 递归收集依赖 → 已完成跳过 → DAG → 排序     │
│                    │                                │
│                    ▼                                │
│  3. 逐任务循环                                      │
│     ┌──────────────────────────────────────┐       │
│     │  a. 断点检测（编排器轻量执行）        │       │
│     │  b. Test Agent（Task）：骨架+测试    │       │
│     │  c. 红色验证（编排器确认测试全失败） │       │
│     │  d. Impl Agent（Task）：实现+重构    │       │
│     │  e. 完成检查+对抗验证+Commit 1       │       │
│     │  f. 更新任务状态 + /ms-sync     │       │
│     │  g. Commit 2: 文档+追踪提交          │       │
│     │  h. 写检查点文件                     │       │
│     └──────────────────────────────────────┘       │
│                    │                                │
│                    ▼                                │
│  4. 后置测试校验（至少 1 个任务成功完成时触发）     │
│     ├── 批量模式：/ms-test-run --trace（全量+追溯）  │
│     ├── 单任务模式：/ms-test-run --affected         │
│     │    └── --affected 无匹配 → 回退 /ms-test-run --trace │
│     └── --skip-trace="<原因>" → 跳过并登记尾注      │
│                    │                                │
│                    ▼                                │
│  5. 批量执行报告                                    │
│                                                    │
└────────────────────────────────────────────────────┘
```

> 详见 [task-orchestration.md](task-orchestration.md)

## 统一任务执行流程

所有任务遵循相同步骤，层级标记决定各步骤的强制程度：

| 符号 | 含义 |
|------|------|
| ■ | 必须执行 |
| ■* | 条件必须：满足条件时升级为 ■（不得跳过） |
| □ | 推荐执行（跳过时记录原因） |
| ○ | 可选 |

**■\* 条件升级规则**：当任务**存在测试骨架或测试文件**（S3 已产出）时，S4「编写测试断言」和 S5「红验」自动升级为 ■。只有在明确决定不产出测试（S3 为 ○ 或跳过）时才允许退化为 □/○。

### 强制程度矩阵

| 步骤 | 执行者 | 🔴 核心逻辑 | 🟡 接口层 | 🟢 UI 层 | ⚪ 基础设施 |
|------|--------|------------|----------|---------|-----------|
| 0.5 Sprint Contract | Test Agent + 编排器 | ■ | ■ | □ | ○ |
| 1. 生成骨架（接口/组件） | Test Agent | ■ | ■ | ■ | ■ |
| 2. 生成测试骨架 | Test Agent | ■ | ■ | ■ | □ |
| 3. 编写测试断言 | Test Agent | ■ | ■* | ■* | ○ |
| 4. 运行测试→确认失败（红） | 编排器 | ■ | ■* | ■* | ○ |
| 5. 实现代码 | Impl Agent | ■ | ■ | ■ | ■ |
| 6. 运行测试→确认通过（绿，skipped/todo=0） | Impl Agent | ■ | ■ | ■ | ■ |
| 7. 重构优化（保持测试通过） | Impl Agent | ■ | □ | ○ | ○ |
| 8. 检查验收标准（AC 完备性表） | 编排器 | ■ | ■ | ■ | ■ |
| 9a. 前置验证（ms-verify） | 编排器 | ■ --impl | ■ --impl | ■ --impl + --ui --impl（有设计稿，两次调用）/ 无设计稿降级 | ■ --impl --trace |
| 9 / Phase 1~3（内置角色演绎对抗式验证） | 编排器 | ■ 自动 | □ --review | □ --review | ○ --review |
| 9 / Phase 4（外部对抗审查，embedded-headless） | 编排器调度 T1 → T2 | ■ 自动（必须落 T1/T2 + EXT_REVIEWED） | □ --external-review | □ --external-review | ○ --external-review |
| 10. 更新自描述 | 编排器 | ■ | ■ | ■ | ■ |
| 11. 提交决策+原子提交 | 编排器 | ■ | ■ | ■ | ■ |

### 🟢 UI 层旁路补充

🟢 UI 层的核心差异不是"少做步骤"，而是"补充 UI 维度"。

**S3 旁路产物**（与测试骨架并行，非替代）：
🟢 任务的 Test Agent 在 S3 结束时**必须**产出 UI 验收清单，无论后续是否执行 S4。
S4 执行时，在清单基础上补全可运行断言。S4 跳过时，清单仍作为 S9 Phase 2-UI 的输入。

清单生成优先级链：
1. AC 中显式描述的视觉/交互要求 → 直接提取
2. 项目设计 token / 设计系统约束 → 引用已有规范
3. 以上均无 → 色值/字体/资源项标记 N/A，仅保留交互状态和结构类检查

清单内容：
- 视觉验收点：布局结构、色值（引用 token）、字体、图标资源
- 交互验收点：状态覆盖（hover/active/disabled/error/loading）、表单反馈、空状态
- 清单中 **Blocker 项**必须在 S8 AC 完备性表中对应三类证据之一（详见 [ui-quality-checklist.md](ui-quality-checklist.md#blocker-项证据要求)）。仅"Suggestion"级别不硬性要求可执行证据。

**S9 扩展（Phase 2-UI，仅 🟢）**：
🟢 UI 任务触发 S9 时，在 Phase 2 之后、Phase 3（综合报告）之前增加：
- Phase 2-UI: UI 质量自查（基于 S3 产出的 UI 验收清单）
  - 设计还原度：布局结构与 AC 一致(Blocker)、间距/色值/字体使用 token(Suggestion)
  - 交互完整性：状态覆盖完整(Blocker)、定义动画时长/缓动参数(Suggestion)、空状态处理(Blocker)
  - 基础质量：语义 HTML/组件层级(Suggestion)、触摸目标尺寸(Suggestion)、响应式约束(Suggestion)
- 分级规则：与 Phase 1/2 一致，使用 Blocker / Suggestion
- Phase 3 综合报告汇总 Phase 1 + Phase 2 + Phase 2-UI 的结果
- 所有检查项为静态可判定的代理指标；运行态/感知类判断归 `/ms-verify --ui` 或 `--live`
- 详细审查清单见 [ui-quality-checklist.md](ui-quality-checklist.md)

平台特定检查（SwiftUI 安全区、Android 导航栏等）不在此列，引用对应外部 skill。

### 执行流程图

```
┌─ Test Agent（独立子 Agent）─────────────────────────────┐
│                                                        │
│  1. 开始任务                                            │
│     │                                                  │
│     ▼                                                  │
│  1.5 Sprint Contract（S1.5）          ← ■/■/□/○        │
│     ├── 基于 AC + 代码上下文生成验收契约                │
│     ├── 具体到：函数签名、返回值、边界条件、异常场景    │
│     └── 编排器审核（过度→裁剪，不足→补充）后确认        │
│     │                                                  │
│     ▼                                                  │
│  2. 生成骨架（S2）                    ← ■ 全层级必须    │
│     ├── 接口/组件签名 + @requirement/@satisfies 标注    │
│     └── 方法体: throw new Error('Not implemented')     │
│     │                                                  │
│     ▼                                                  │
│  3. 生成测试骨架（S3）                ← ■/■/■/□        │
│     ├── 测试结构来自 03-test-*.md                      │
│     ├── 断言值来自行为契约 + AC 对应测试用例            │
│     ├── @verifies/@testcase 标注                       │
│     └── 测试体: test.skip() 或 test.todo()             │
│     │                                                  │
│     ▼                                                  │
│  4. 编写测试断言（S4）                ← ■/■*/■*/○      │
│     └── 移除 skip，完成完整断言                         │
│                                                        │
└── 产出：骨架文件 + 测试文件 ───────────────────────────┘
                    │
                    ▼
┌─ 编排器：红色验证（S5）──────────────── ← ■/■*/■*/○ ───┐
│  运行测试（对比任务开始前的测试基线）                   │
│  ├── 新测试全失败 + 无基线外新增失败 → 进入 Impl Agent│
│  ├── 新测试意外通过 → ⛔ 测试无效，回退 Test Agent    │
│  └── 基线外新增失败 → ⛔ 骨架破坏已有功能，回退       │
└────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─ Impl Agent（独立子 Agent）────────────────────────────┐
│  ⛔ 信息屏障：不可读取 03-test-*.md，不可修改测试文件   │
│                                                        │
│  5. 实现代码（S6，遵循 /code-quality）← ■ 全层级必须   │
│     │                                                  │
│     ▼                                                  │
│  6. 运行测试→确认通过（绿）           ← ■ 全层级必须    │
│     ├── 失败 → 修复实现（最多 N 次，默认 3）           │
│     ├── 疑似测试缺陷 → 报告 test_defects，停止         │
│     ├── ⛔ skipped/todo 计数 > 0 → 回退 Test Agent      │
│     │      补齐断言（豁免需在任务文档显式登记原因）     │
│     │                                                  │
│     ▼                                                  │
│  7. 重构优化（S7，保持测试通过）      ← ■/□/○/○        │
│                                                        │
└── 产出：实现文件 + 测试结果 ──────────────────────────┘
                    │
                    ▼
┌─ 编排器：完成检查 ─────────────────────────────────────┐
│                                                        │
│  8. S8：AC 完备性 + 声称 vs 实际 diff ← ■ 全层级必须   │
│     ├── 产出 AC 完备性表（编号/AC 类型/证据类型/位置/判定）│
│     │   按 SKILL.md "AC 类型 × 证据类型分级矩阵" 判定   │
│     ├── 声称 vs 实际 diff 交叉验证                     │
│     ├── 缺证据 / 违反分级矩阵 / 遗漏实现 / 大块 diff 无关联 │
│     │      → ⛔ 回到 S6（补实现）或 S4（补测试）       │
│     └── 全部满足 ─────────────┐                        │
│                               ▼                        │
│  9. 对抗式验证（S9）                                    │
│     ├── Phase 1: 代码质量审查（/code-quality）          │
│     ├── Phase 2: 测试完备性审查（/testing-guide）       │
│     ├── Phase 2-UI: UI 质量自查（仅 🟢，ui-quality-checklist）│
│     ├── Phase 3: 综合报告                              │
│     ├── Blocker → 修复 → 重新验证                      │
│     └── 通过 ────────────────┐                         │
│                               ▼                        │
│  10. 测试文件不可变校验                                 │
│      └── diff 测试文件，有变更 → ⛔ Blocker            │
│                               │                        │
│                               ▼                        │
│  11. 更新自描述（S10）                ← ■ 全层级必须    │
│                               │                        │
│                               ▼                        │
│  12. 提交决策 + Commit 1（S11）       ← ■ 全层级必须    │
│                               │                        │
│                               ▼                        │
│  13. 更新任务状态 + /ms-sync → Commit 2            │
│                                                        │
└────────────────────────────────────────────────────────┘
```

> **跳过记录**：□ 或 ○ 步骤被跳过时，在提交信息中记录 `跳过: 步骤X（原因）`。

## 任务完成流程

所有层级遵循统一完成流程，对抗式验证的触发方式因层级而异：

1. **确认测试状态**：检查 Impl Agent 测试结果（全部通过）
2. **确认双 Agent 隔离**：Test Agent 产出测试文件未被 Impl Agent 修改（diff 校验）
3. **检查重构**（■🔴 □🟡 ○🟢⚪）：代码是否经过优化
4. **验证验收标准（S8 完备性）**：
   - 输出 AC 检查表（编号/AC 类型/证据类型/代码或测试位置/判定），证据组合按 [SKILL.md 完成检查约束](../SKILL.md#完成检查约束) 中的 **AC 类型 × 证据类型分级矩阵**判定（不再使用单一白名单）
   - 执行声称 vs 实际 diff 交叉验证（对比 AC 列表与 `git diff`）
   - 任一 AC 缺证据 / 分级矩阵不满足 / 声称满足但 diff 无变更 / 未关联 AC 的大块变更 → ⛔ 回到对应步骤修复
5. **前置验证（按层级默认必做）**：
   - 🔴/🟡：`/ms-verify --impl`（AC 满足度 + 设计一致性 + 追溯）
   - 🟢：
     - 有设计稿 → `/ms-verify --impl` + `/ms-verify --ui --impl`（两次显式调用：前者覆盖 AC+追溯，后者覆盖设计稿↔实现）
     - 无设计稿 → Phase 2-UI 自查 + `/ms-verify --impl`
   - ⚪：`/ms-verify --impl --trace`（仅追溯子集，不要求完整 AC 语义对齐）
   - Blocker → ⛔ 回退修复，不因"未加 --review"而放行
6. **对抗式验证 Phase 1~3**（■🔴自动 / □🟡🟢--review / ○⚪--review；`--review` 仅作增强叠加；产出 `int_review_state`）：
   - Phase 1: 代码质量审查（/code-quality 视角）
   - Phase 2: 测试完备性审查（/testing-guide 视角）
   - Phase 2-UI: UI 质量自查（仅 🟢，ui-quality-checklist）
   - Phase 3: 综合报告，处理 Blocker
6.5. **对抗式验证 Phase 4：外部对抗审查**（■🔴 默认自动 / □🟡🟢--external-review / ○⚪--external-review；产出 `ext_review_state`）：
   - 调度器调用双通道 T1 codex CLI → T2 codex-mcp（T1/T2 全失败 → `EXT_UNRESOLVED` → --headless fail-fast，不设子 Agent 兜底）
   - 自动收敛循环（`max_rounds=3`，`--external-rounds N` 覆盖上限 5）
   - 按状态真值表映射到 `EXT_REVIEWED / EXT_PENDING / EXT_UNRESOLVED / EXT_BLOCKED`
   - 🔴 任务必须落 T1/T2 + L2 yaml 可读 + `EXT_REVIEWED` 才放行
   - 非 `EXT_REVIEWED`（任何状态）→ ⛔ 阻塞 Commit 1
   - 详细契约、真值表、证据协议（L2 权威） 见 [verification-flow.md Phase 4 章节](verification-flow.md)
7. **更新自描述**：运行 /code-self-describe --update
8. **提交决策**：
   - **前置门禁**：`int_review_state=INT_REVIEWED`（或未触发时为空）∧ `ext_review_state=EXT_REVIEWED`（或未触发时为空）才允许进入下面任一模式；任一为 `*_PENDING` / `*_UNRESOLVED` / `*_BLOCKED` → ⛔ 阻塞提交（恢复动作见各自 canonical state 定义）
   - `--headless` 模式：自动提交（安全不变量已在前置步骤保证）
   - `--auto-commit` 模式：测试通过 + 无 Blocker 时自动提交
   - 交互模式：AskUserQuestion："任务 T-XX 已完成，是否提交代码？"
     - 选项："提交" / "继续修改" / "跳过"
9. **如提交**（原子提交）：
   - Commit 1: `git add [代码文件] && git commit -m "<type>(T-XX): <名称>"`
   - 更新 04-dev-tasks*.md 状态为 `已完成`
   - 运行 /ms-sync
   - Commit 2: `git add [文档文件] && git commit -m "docs(T-XX): 更新任务状态并同步 trace"`
10. **更新 TodoWrite**：将任务标记为已完成

## 提交信息格式

遵循 `/commit-convention` 规范，格式如下：

```
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
External-Review-Verdict: <Phase 4 触发时必填：EXT_REVIEWED | EXT_PENDING | EXT_UNRESOLVED | EXT_BLOCKED；含 rounds 和 health_scores>
External-Review-Channel: <Phase 4 触发时必填：T1 | T2 | none（非状态字段）>
Skip-Review-Reason: <仅 🔴 任务使用 --skip-review-reason 时填写；其他情况省略此行>
Skip-External-Review-Reason: <仅 🔴 任务使用 --skip-external-review-reason 时填写>
Skip-Trace-Reason: <单任务使用 --skip-trace 时填写；其他情况省略此行>
Exploration-Mode: <探索模式设为 true 并登记证据/豁免原因；其他情况省略此行>
```

**type 类型**：feat | fix | refactor | test | docs | chore

## TodoWrite 集成

用户确认开始开发时：

```
使用 TodoWrite 添加任务：
- 每个任务成为一个 todo 项
- 保持定义的任务顺序
- todo 内容包含任务编号
- 提交后更新状态
```

### 批量模式下 TodoWrite

```
1. 初始化：将执行队列中所有任务添加为 todo 项
2. 执行中：当前任务标记为 in_progress
3. 完成时：任务标记为 completed
4. 断点续做：读取 TodoWrite 状态辅助判断进度
```
