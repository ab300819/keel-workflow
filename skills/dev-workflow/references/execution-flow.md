# 任务执行流程详解

> ℹ️ 本文件提及的 `@satisfies` / `@verifies` / `@requirement` / `@testcase` 标注属于 **layout.v1 legacy**（v2 起改读 traceability.yml，[FUTURE 状态](../../pipeline/references/layout/docs-layout-migration.md#-执行接口落地状态future)）。Test/Impl Agent 的注释纪律（禁止变更日志式/来源记录式注释）见 [task-orchestration.md 子 Agent 协议](task-orchestration.md#子-agent-协议双-agent-模型) 与 [`/code-quality` 注释规范](../../code-quality/SKILL.md#注释规范)。

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
| S9 / Phase 4 | 外部对抗审查（audit inline；fast/guarded 延后到 `/ms-verify --review-drain`） | 编排器（embedded-headless 调度器） | `ext_review_state` ∈ {EXT_REVIEWED, EXT_PENDING, EXT_UNRESOLVED, EXT_BLOCKED} |
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

所有任务遵循相同步骤，`review_profile`（fast / guarded / audit）决定各步骤的强制程度；层级标签 🔴🟡🟢⚪ 仅作风险分类器输入，用于决定 review_profile，不直接决定矩阵强制程度：

| 符号 | 含义 |
|------|------|
| ■ | 必须执行 |
| ■* | 条件必须：满足条件时升级为 ■（不得跳过） |
| □ | 推荐执行（跳过时记录原因） |
| ○ | 可选 |

**■\* 条件升级规则**：当任务**存在测试骨架或测试文件**（S3 已产出）时，S4「编写测试断言」和 S5「红验」自动升级为 ■。只有在明确决定不产出测试（S3 为 ○ 或跳过）时才允许退化为 □/○。

### 强制程度矩阵

| 步骤 | fast | guarded | audit |
|------|:---:|:---:|:---:|
| S1 读任务 / S1.5 Contract | ■ | ■ | ■ |
| S2/S3 骨架 + 测试骨架(双 Agent) | ■ | ■ | ■ |
| S4-S7 红绿重构(测试冻结) | ■ | ■ | ■ |
| 质量地板 5 条 | ■ | ■ | ■ |
| S8 完成检查(AC 完备表) | ■(证据摘要) | ■ | ■(完整矩阵) |
| S9 前置验证 `/ms-verify --impl` | ○ | ■ | ■ |
| S9 Phase 1~3 内审 | ⏳ defer | ⏳ defer(风险触发则 ■) | ■ inline |
| S9 Phase 4 外审 | ⏳ defer | ⏳ defer | ■ inline |
| S10 自描述 / S11 Commit 1 | ■ | ■ | ■ |
| UI Phase 2-UI 自查(仅 UI 任务) | 按 ui-quality-checklist.md(不随 profile 变) | 同 | 同 |

> ⏳ defer = 延后到 `/ms-verify --review-drain`,任务期间标 `review_pending`。
> 层级标签 🔴🟡🟢⚪ 仅作风险分类器输入决定 review_profile,不再直接决定本矩阵强制程度。

### 🟢 UI 层旁路补充

🟢 UI 层在统一 11 步流程之上追加 Phase 2-UI（UI 质量自查），完整审查清单 + 与 `/ms-verify --ui` 边界 + UI 验收清单生成规则见 [ui-quality-checklist.md](ui-quality-checklist.md)。本文件不重复转述。

### 执行流程图

> **与 review_profile 的关系**:下列按"层级"组织的流程图仅为**示意分类**(层级=风险输入)。实际 S1~S11 强制程度与独立审查时机以上文 review_profile 矩阵为准:audit inline 全套;fast/guarded 独立审查延后到 `/ms-verify --review-drain`(任务标 `review_pending`);质量地板 5 条与 `/ms-verify --impl`(guarded/audit)恒定 inline。层级标记(🔴🟡🟢⚪)读作 review_profile 风险输入,不再独立决定流程强度。

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
│     │   按 verification-flow.md AC 完备性矩阵判定      │
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

所有任务遵循统一完成流程，独立审查（Phase 1~3+4）的触发时机因 review_profile 而异：

1. **确认测试状态**：检查 Impl Agent 测试结果（全部通过）
2. **确认双 Agent 隔离**：Test Agent 产出测试文件未被 Impl Agent 修改（diff 校验）
3. **检查重构**（audit/guarded: ■；fast: □）：代码是否经过优化
4. **验证验收标准（S8 完备性）**：
   - 输出 AC 检查表（编号/AC 类型/证据类型/代码或测试位置/判定），证据组合按 [verification-flow.md §AC 完备性](verification-flow.md#ac-完备性s8-权威定义) 的 **AC 类型 × 证据类型分级矩阵**判定（不再使用单一白名单；强制性约束见 [SKILL.md §完成检查约束](../SKILL.md#完成检查约束)）
   - 执行声称 vs 实际 diff 交叉验证（对比 AC 列表与 `git diff`）
   - 任一 AC 缺证据 / 分级矩阵不满足 / 声称满足但 diff 无变更 / 未关联 AC 的大块变更 → ⛔ 回到对应步骤修复
5. **前置验证（按 review_profile 决定）**：
   - guarded/audit：`/ms-verify --impl`（AC 满足度 + 设计一致性 + 追溯）；🟢 UI 任务额外：有设计稿 → 再跑 `/ms-verify --ui --impl`，无设计稿 → Phase 2-UI 自查 + `/ms-verify --impl`
   - fast：仅质量地板（行为型 AC 独立证据 + `/ms-test-run --affected`），跳过 `/ms-verify --impl`
   - 层级标签 🔴🟡🟢⚪ 仅作 review_profile 分档的风险输入，不直接决定本步强制程度
   - Blocker → ⛔ 回退修复，不因"未加 --review"而放行
6. **对抗式验证 Phase 1~3**（按 review_profile；产出 `int_review_state`）：
   - **audit**：inline fail-fast，必须通过（INT_REVIEWED）才允许继续
   - **fast/guarded**：⏳ 延后到 `/ms-verify --review-drain`（风险信号触发时 guarded 可升为 inline）
   - Phase 1: 代码质量审查（/code-quality 视角）
   - Phase 2: 测试完备性审查（/testing-guide 视角）
   - Phase 2-UI: UI 质量自查（仅 🟢，ui-quality-checklist）
   - Phase 3: 综合报告，处理 Blocker
6.5. **对抗式验证 Phase 4：外部对抗审查**（按 review_profile；产出 `ext_review_state`）：
   - **audit**：inline fail-fast，必须通过（EXT_REVIEWED）才允许继续
   - **fast/guarded**：⏳ 延后到 `/ms-verify --review-drain`

### Phase 4 外部对抗审查在 S9 中的位置

S9 阶段触发 Phase 4 时，状态字段（`ext_review_state`）、轮次控制（`max_rounds`/`--external-rounds`）、降级链（T1 codex CLI → T2 codex-mcp）、真值表与 L2 证据协议均由 [verification-flow.md](verification-flow.md) 权威定义。本文件不重复。

7. **更新自描述**：运行 /code-self-describe --update
8. **提交决策（按 review_profile 分支）**：
   - **audit**：前置门禁 `int_review_state=INT_REVIEWED` ∧ `ext_review_state=EXT_REVIEWED` 均满足才允许提交；任一为 `*_PENDING` / `*_UNRESOLVED` / `*_BLOCKED` → ⛔ 阻塞提交（恢复动作见各自 canonical state 定义）
   - **fast/guarded**：独立审查（Phase 1~3+4）已延后，不等 INT/EXT_REVIEWED；质量地板 + `/ms-verify --impl`（guarded）无 Blocker 即可提交
   - `--headless` 模式：自动提交（安全不变量已在前置步骤保证）
   - `--auto-commit` 模式：测试通过 + 无 Blocker 时自动提交
   - 交互模式：AskUserQuestion："任务 T-XX 已完成，是否提交代码？"
     - 选项："提交" / "继续修改" / "跳过"
9. **如提交**（原子提交）：
   - Commit 1: `git add [代码文件] && git commit -m "<type>(T-XX): <名称>"`
   - **audit**：提交后更新 04-dev-tasks*.md 状态为 `已完成`
   - **fast/guarded**：提交后更新 04-dev-tasks*.md 状态为 `review_pending`（独立审查延后），在 Commit 1 尾注附加：
     ```
     Review-Batch-Id: <batch-id>
     Review-Due: <YYYY-MM-DD>
     Pending-Reason: deferred-fast | deferred-guarded
     ```
     `/ms-verify --review-drain` 通过后（无 Blocker）才转 `已完成`
   - 运行 /ms-sync
   - Commit 2: `git add [文档文件] && git commit -m "docs(T-XX): 更新任务状态并同步 trace"`
10. **更新 TodoWrite**：将任务标记为已完成（audit）或 review_pending（fast/guarded）

## 提交信息格式

遵循 `/commit-convention` 规范（标题/type 权威）；trailer 字段语义权威见 [_shared/constraints.md §Commit trailers 协议](../../_shared/constraints.md)，本块为模板呈现与填写时机：

```
<type>(T-XX): <任务名称>

- <完成内容1>
- <完成内容2>

关联: F-XXX, AC-XXX
测试: UT-XXX, IT-XXX 通过
External-Review-Verdict: <audit profile Phase 4 inline 时必填：EXT_REVIEWED | EXT_PENDING | EXT_UNRESOLVED | EXT_BLOCKED；含 rounds 和 health_scores>
External-Review-Channel: <audit profile Phase 4 inline 时必填：T1 | T2 | none（非状态字段）>
Review-Batch-Id: <fast/guarded profile 延后时必填；audit 省略>
Review-Due: <fast/guarded profile 延后时必填（格式 YYYY-MM-DD）；audit 省略>
Pending-Reason: <fast/guarded profile 延后时必填：deferred-fast | deferred-guarded；audit 省略>
Skip-Review-Reason: <audit profile 使用 --skip-review-reason 时填写；其他情况省略此行>
Skip-External-Review-Reason: <audit profile 使用 --skip-external-review-reason 时填写；其他情况省略此行>
Skip-Trace-Reason: <单任务使用 --skip-trace 时填写；其他情况省略此行>
Exploration-Mode: <探索模式设为 true 并登记证据/豁免原因；其他情况省略此行>
```

**type 类型**：以 `/commit-convention` 为权威（feat/fix/refactor 等枚举不在此重述）；上方 `Review-Batch-Id` 等尾注为 DevDocs 专有 trailer 协议，归本文件管辖

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

见 [task-orchestration.md § TodoWrite 集成](task-orchestration.md#todowrite-集成)（唯一权威）。
