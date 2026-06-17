---
name: ms-verify
description: Unified verification skill combining document alignment, implementation correctness, UI design alignment, and development readiness checks. Supports --docs, --impl, --ui, --readiness, --schema-drift flags; auto-detects dimensions when called without flags. Triggers on "verify", "review", "alignment", "验证", "审查", "对齐检查", "需求验证", "设计一致性", "UI 对齐", "就绪检查", "质量关卡", "readiness". NOT for syncing docs with progress (use ms-sync).
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
metadata:
  patterns: [reviewer]
  interaction: multi-turn
  handoff: yaml-summary-v1
---

# 统一验证

> 视角：质量审查员 — 以批判性视角检查一致性，标记偏差而非默认通过。

四合一验证 Skill：文档对齐 + 实现正确性 + UI 设计对齐 + 开发就绪检查，替代原 `devdocs-review`、`ms-requirements-alignment`、`devdocs-ui-alignment`。

- 共享约束 SSOT：[../_shared/constraints.md](../_shared/constraints.md)

> 本 skill 遵循共享约束 SSOT：门控标记、yaml-summary-v1、Task 委托、用户确认、Recovery 格式、只读 / dry-run、FUTURE 三态、realign / spec_version 见 [skills/_shared/constraints.md](../_shared/constraints.md)。本文件只描述 ms-verify 私有规则（P 级评分、四维验证、盲区机制、verify-report 契约）。

## 快速定位

- 语言：支持中英文提问，统一中文回复，使用中文生成报告。
- 一句话：检查文档/实现/UI/就绪性偏差，标记不一致。
- 常见用法：`/ms-verify`（自动检测）、`/ms-verify --readiness`（开发前）、`/ms-verify --impl`（代码完成后）。
- 不适合：同步文档进度→`/ms-sync`；代码质量审查→`/adversarial-review`。

| 模式 | 关注点 | 关系 |
|------|--------|------|
| `--docs` | 各层文档之间是否对齐 | 原 requirements-alignment |
| `--impl` | 代码是否做对 AC / 设计 / 追溯 | 原 review；在对抗式验证之前 |
| `--ui` | UI 设计和实现是否对齐 | 原 ui-alignment |
| `--readiness` | 能否进入开发 | pipeline 关卡 |
| `--review-drain` | 收集所有 `review_pending` 任务,集中补跑延后的独立审查(Phase 1~3 + Phase 4),按 [dev-workflow verification-flow drain 失败矩阵](../dev-workflow/references/verification-flow.md) 出 verdict 并更新任务状态;全通过转已完成,有 Blocker 走 fix-forward 并阻断 sprint close |
| 对抗式验证 | 代码质量是否合格 | dev-workflow 内置，互补而非替代 |

> `--review-drain` 复用 dev-workflow S9 Phase 1~3/Phase 4 的 embedded-headless 通道,是 fast/guarded 延后审查的清算入口;单任务 inline 审查仍由 dev-workflow 内部触发。

> 细分检查由 LLM 根据用户意图自动聚焦；只有高成本交互验证需显式追加 `--live`。

## 触发条件

- 需求/设计/测试文档完成后（`--docs`）
- 任务开发完成后、对抗式验证之前（`--impl`）
- UI 相关任务开发完成后（`--ui`）
- 任务拆分完成、进入开发前（`--readiness`）
- 用户要求检查文档/实现/UI 对齐

## 运行模式

```bash
/ms-verify                    → 自动检测维度（LLM 路由）
/ms-verify --docs             → 文档对齐（三层默认覆盖）
/ms-verify --impl             → 实现正确性（默认覆盖 AC / 设计 / 追溯）
/ms-verify --impl "检查 AC"   → LLM 自动聚焦 AC 子维度
/ms-verify --impl --live      → 显式启用实际交互验证（启动应用 + 浏览器自动化）
/ms-verify --ui               → UI 设计对齐（两阶段默认覆盖）
/ms-verify --readiness        → 开发就绪检查（进入 dev-workflow 前的质量关卡）
/ms-verify --schema-drift     → 合并 drift 报告（schema drift + layout drift）
/ms-verify T-01 T-02          → 指定任务范围（自动 --impl）
```

> 除 `--live` 外，二级控制（`--layer1/2/3`、`--ac`、`--design`、`--trace`、UI 阶段选择）不作为顶部用户面入口暴露；用户用自然语言表达聚焦意图，执行细则按 references 内部说明。`--schema-drift` 为只读合并入口，输出 schema drift 与 layout drift 两段：前者扫产物 spec_version，详见 [references/schema-drift.md](references/schema-drift.md)；后者扫治理层 layout/id/trace 兼容性，对齐 `/ms-pipeline realign --docs-layout`，详见 [skills/pipeline/references/layout/](../pipeline/references/layout/)。

### 四维验证选择矩阵

无参数调用时，先按项目状态自动选择维度；无法判断时询问用户。

| 场景 | 维度 | 必要条件 | 跳过 / 降级条件 |
|------|------|----------|-----------------|
| 文档阶段：需求/设计/测试文档完成 | A `--docs` | 有 `03-test-cases.md` 但无代码提交；或用户要求文档对齐 | 层 1 缺 `## 0. 原始需求` 且为历史/Retrofit 文档 → 输出 `⏭️ 前置缺失` 跳过层 1 |
| 开发完成：任务代码已提交或进行中 | B `--impl` | 任务开发完成后、对抗式验证之前；最新 `05-test-report.md` 可辅助判断 | 用户要求检查 AC/设计/追溯时自动聚焦对应子维度；`--live` 无浏览器 MCP 时降级静态验证 |
| UI 任务完成 | C `--ui` | UI 任务 + 有设计稿 + 有代码提交；或用户要求 UI 对齐 | 无设计稿输入且无 design_context → 不可运行，提示用户提供 |
| 任务拆分完成，进入开发前 | D `--readiness` | dev-tasks 完成后、dev-workflow 前 | 通常全量检查；若任务范围明确可限定 T-XX |

## 工作流程

1. 确定验证维度（自动检测或用户指定）。
2. 读取 DevDocs：`01-requirements.md`、`02-system-design.md`、`03-test-cases.md`、`05-test-report.md`（如存在）。
3. 加载 `docs/devdocs/patterns/verify-blindspots.md`（如存在），将历史盲区转化为本次额外关注点。
4. 按维度执行检查：`--docs` 三层、`--impl` 三维度 + 可选 `--live`、`--ui` 两阶段、`--readiness` 四维度。
5. 生成验证报告，给出 P1/P2/P3 分级、修复建议与路由。

---

## 维度 A：文档对齐（--docs）

验证各层文档之间是否对齐，防止需求精化过程中的偏移和遗漏。

```
原始需求（用户原话）
    │
    ├─ 层 1：原始需求 → 需求文档（F/US/AC）
    ├─ 层 2：需求文档 → 系统设计
    └─ 层 3：需求文档 → 测试用例
```

每层独立可执行，越早发现偏移，修复成本越低。

### 层 1：原始需求 → 需求文档

**前提**：需求文档中应包含 `## 0. 原始需求` 章节。

| 文档类型 | `## 0. 原始需求` 状态 | 层 1 行为 |
|----------|----------------------|-----------|
| 新建文档 | 必须存在 | 正常执行语义对齐检查 |
| 历史/Retrofit 文档 | 可能不存在 | 输出 `⏭️ 前置缺失`，跳过层 1 |

**检测类型**：遗漏（原始需求未被 F/US/AC 体现）、过度扩展（超出原始需求范围）、偏移（语义偏离）。

### 层 2：需求文档 → 系统设计

检查 F → 设计模块映射、AC → 实现路径、设计孤立项。

**设计文档内部一致性**（ADR ↔ 正文同期修订）：委托 health-lint `design/adr-only-revision` 同款算法（详见 [pipeline/references/health-lint-implementation.md](../pipeline/references/health-lint-implementation.md#designadr-only-revision)）。

| 维度 | 说明 |
|------|------|
| 触发条件 | `--docs` 默认启用；git 不可用时自动 fallback skip（标 `health/git-unavailable` 写入 verify-report，不引入用户面新 flag）|
| 时间窗 | 默认最近 30 天 commit；与 `--scope=health` 共享窗口配置 |
| 输出字段 | 复用 health-lint Finding schema（rule_id / severity / commit / adr_ids / declared_impact / hint）|
| 严重度 | warning（不阻断 `--docs` 主流程；如需阻断走 `--scope=health` 评分）|
| 写入位置 | verify-report.md 的"层 2"小节，独立子标题"设计文档内部一致性"|
| **去重规则** | verify-report 与 `.health-report.md` 用 `(rule_id, source_git_commit, ref_commit_sha)` 三元组互斥消费；若同 commit 在 `.health-report.md` 中 manual_decision 已 answered → verify 不重复报，仅标"已在 health-report 处理"|

### 层 3：需求文档 → 测试用例

检查 AC → 测试用例映射、正向路径覆盖、异常路径覆盖。**复用 ms-sync --check 的孤立编号检测能力**（只读模式，不修改文档）。

---

## 维度 B：实现正确性（--impl）

验证代码实现是否正确——AC 满足度、设计符合度、追溯完整性。

### B1：AC 满足度审查

逐条验证实现是否匹配验收标准。

1. 读取 `01-requirements.md` 中所有 AC（layout.v1）/ `requirements/AC-NNN.md`（layout.v2 [FUTURE]）
2. 通过 `@satisfies` 标注（layout.v1 legacy）或 `traceability.yml`（layout.v2 [FUTURE]）+ 代码搜索定位实现
3. **语义判断**实现是否匹配 AC 描述（不仅检查标注存在性）
4. 对每条 AC 给出判定：✅ 满足 / ⚠️ 部分满足 / ❌ 未满足

**辅助判断**：如存在最新 `05-test-report.md`，用实际测试通过率辅助判断 AC 满足度——测试全部通过的 AC 可提高判定信心，测试失败的 AC 需重点审查。

### B2：设计符合度审查

| 检查项 | 说明 | 严重程度 |
|--------|------|----------|
| 接口签名一致性 | 实际参数/返回值与设计文档不符 | Blocker |
| 模块职责偏离 | 模块承担了设计中未分配的职责 | Blocker |
| 数据流符合度 | 数据流转路径与设计不符 | Warning |
| 组件边界 | 组件间依赖关系与设计不符 | Warning |
| ADR 实施约束场景假设 | ADR 中"向后兼容性约束"/"桥接策略"未明确区分"已发布 vs 未发布"或"内部 vs 跨服务 vs 公开 SDK"前置假设，疑似默认采用已发布产品演进模式 | Warning |

### B3：追溯完整性审查

检查 `@satisfies`/`@verifies` 覆盖率（layout.v1 legacy）或 `traceability.yml` 完整性（layout.v2 [FUTURE]）。**复用 ms-sync --check 的追溯扫描能力**（只读模式，不修改文档）。

### B4：实际交互验证（--live，可选）

通过浏览器自动化实际操作运行中的应用，验证 AC 描述的用户行为是否正确。

**前提**：环境中有 Playwright MCP 或 Chrome DevTools MCP，可从 DevDocs 或 package.json 获取启动命令并本地启动应用。

**流程**：启动应用 → 逐条读取 AC 用户操作 → 用浏览器 MCP 执行导航/点击/填表/验证 → 对比实际行为与 AC 预期 → 停止应用。

| 任务类型 | --live 行为 |
|----------|-------------|
| UI/前端（🟢） | ✅ 推荐 |
| API 接口（🟡） | ✅ 可选（curl/API 调用验证） |
| 核心逻辑（🔴） | ⏭️ 跳过（单元测试已覆盖） |
| 基础设施（⚪） | ⏭️ 跳过 |

**降级**：无浏览器 MCP → 跳过并输出 `ℹ️ 建议：环境中无浏览器 MCP，--live 验证已跳过`；应用启动失败 → 记录为 P2 Warning，继续静态验证；`--live` 与静态验证互补，不替代 B1/B2/B3。

> 灵感来源：[Harness Design](https://www.anthropic.com/engineering/harness-design-long-running-apps) 中 Evaluator 使用 Playwright 与运行中的应用交互验证，比纯静态代码审查更有效。

---

## 维度 C：UI 设计对齐（--ui）

验证 UI 设计和实现是否对齐——两阶段验证。

### C1：设计稿 ↔ 需求对齐

**设计稿来源**：优先从 `01-requirements.md` 的 `## 设计资产`（design_context）获取设计稿位置和 access_method，自动选择获取工具：

| access_method | 获取方式 |
|--------------|---------|
| `structured_dsl` | MasterGo getDsl MCP |
| `node_tree` | Pencil batch_get MCP |
| `vision` | 读取截图/图片 |
| `manual` | 要求用户描述 |

无 design_context 时，兼容直接提供：Pencil .pen 文件、截图/图片、Figma（通过截图或 MCP）。

检查设计稿是否覆盖 `01-requirements.md` 中 UI 相关 AC。

### C2：设计稿 ↔ 实现对齐

获取实现截图，与设计稿逐维度对比。**默认路径**：要求用户提供实现截图；**自动化路径**：如环境中有浏览器 MCP 工具可用，自动截图。

#### 截图获取方式

| 优先级 | 方式 | 条件 |
|--------|------|------|
| 1（默认） | 用户提供实现截图 | 始终可用 |
| 2（自动） | 浏览器 MCP 自动截图 | 环境中有 Playwright/Chrome DevTools MCP |

#### 对比维度

| 维度 | 检查内容 | 严重程度 |
|------|----------|----------|
| 布局结构 | 元素排列、层级关系 | P1 |
| 间距 | 元素间距、内外边距 | P2~P3 |
| 颜色 | 主色、辅色、文字色 | P2~P3 |
| 字体 | 字族、字号、字重 | P2~P3 |
| 交互状态 | hover/active/disabled/error | P1 |
| 响应式 | 不同断点下的布局变化 | P2~P3 |

### UI 降级策略

| 条件 | 行为 |
|------|------|
| 有 design_context | 按 access_method 自动选择工具获取设计稿 |
| 无设计稿输入（且无 design_context） | **不可运行**——提示用户提供设计稿 |
| 有设计稿，无浏览器 MCP | 阶段 1 正常；阶段 2 要求用户提供实现截图 |
| 有浏览器 MCP，无设计稿 MCP | 要求用户提供设计稿截图 |

**工具说明**：Pencil MCP（`mcp__pencil__*`）、Playwright MCP（`mcp__playwright__*`）、Chrome DevTools MCP（`mcp__chrome_devtools__*`）为可选依赖，按可用性自动选择。无 MCP 时降级为用户提供截图，不影响验证能力。

---

## 维度 D：开发就绪检查（--readiness）

验证任务文档是否达到开发就绪状态——在 dev-tasks → dev-workflow 过渡时作为质量关卡。

**与 --docs 的区别**：`--docs` 检查文档层间对齐（漂移检测），`--readiness` 检查任务级开发就绪条件（具体性、一致性、可执行性）。

### D1：AC ↔ 测试用例对齐

检查每条 AC 是否有对应的测试用例设计：

1. 读取 `01-requirements.md` 中所有 AC
2. 读取 `03-test-cases*.md` 中的追溯矩阵
3. 逐条检查 AC → UT/IT/E2E 映射
4. 输出未覆盖的 AC 列表

### D2：任务文件路径具体性

检查 `04-dev-tasks*.md` 中每个任务的文件路径是否具体可执行：

| 检查项 | 合格标准 | 不合格示例 |
|--------|---------|-----------|
| 文件路径 | 明确到文件名 | "修改相关文件" |
| 方法/接口 | 明确到方法名或接口名 | "调整接口" |
| 测试方法 | 指定测试类型和编号 | "编写测试" |

### D3：任务依赖无环

检查任务依赖关系是否存在循环：

1. 从 `04-dev-tasks*.md` 提取所有任务依赖关系
2. 构建有向图，执行拓扑排序
3. 若存在环路 → 报告环路路径

### D4：设计 ↔ 任务一致性

检查任务定义是否与系统设计一致：

1. 任务引用的模块/接口在 `02-system-design*.md` 中存在
2. 任务的文件路径与设计文档的**模块落位原则 / 模块-接口映射**一致（§7 代码落位原则，非完整目录树）
3. 无孤立任务（任务未关联任何 F-XXX/AC-XXX）

---

## CE 三个审查问题（--impl 专属）

`--impl` 审查完成后，必须追加回答：

1. **"实现中最难的决策是什么？"** — 识别技术复杂度核心
2. **"拒绝了哪些替代方案？为什么？"** — 确认决策有对比论证
3. **"最不确信的部分是什么？"** — 暴露隐性风险

## 问题分级

所有维度发现统一按优先级分级：

| 优先级 | 含义 | 处理方式 |
|--------|------|----------|
| **P1** | 阻塞合并 / 阻塞发布 | 必须修复，建议转入 ms-dev-tasks |
| **P2** | 必须修复但不阻塞 | 建议修复，建议转入 ms-insights |
| **P3** | 建议改进 | 可选修复，记录备忘 |

P1/P2/P3 判定标准详见 [references/p-severity-rubric.md](references/p-severity-rubric.md)，执行时按需加载。

## verify-report 输出契约

| 报告 | 适用维度 | 必填字段 / 章节 |
|------|----------|----------------|
| `docs/devdocs/verify-report.md` | `--docs` / `--impl` / `--ui` | 验证时间、`verified_commit`、验证维度、验证范围、关联文档、验证结果摘要（各维度 P1/P2/P3/状态）、对应 A/B/C 章节、问题汇总、修复路由 |
| `docs/devdocs/readiness-report.md` | `--readiness` | 验证时间、验证维度、验证范围、关联文档、D1-D4 就绪度摘要、D1-D4 明细、问题汇总、修复路由 |

`--impl` 报告必须包含 CE 三问；触发盲区 6/7 时必须填写 B4/B5。字段与 A/B/C 类示例见 [templates/verify-report.md](templates/verify-report.md)，就绪报告见 [templates/readiness-report.md](templates/readiness-report.md)。

## 上下文管理

### 分批原则

- **--docs**：按层级分批（层 1、层 2、层 3 各为一个批次）
- **--impl**：按任务 (T-XX) 或功能点 (F-XXX) 分批，每批完成全部三个子维度
- **--ui**：按页面/组件分批
- **--readiness**：一次性全量检查（通常任务数量有限，不需分批）

### 质量锚点

- **--docs**：使用**完备性验证**——每层检查后核对已报告数量 == 输入编号总数
- **--impl**：首个功能点的审查结果作为**质量锚点**，后续深度不低于首批
- **--ui**：首个页面的检查结果作为质量锚点
- **--readiness**：使用**完备性验证**——所有任务和 AC 均已出现在检查结果中

### 一致性自检

每批完成后对比检查：
- [ ] 判定标准跨批次一致（同类问题同等判定）
- [ ] 统计口径一致
- [ ] （--docs）所有输入编号均已出现在输出矩阵中
- [ ] （--impl）AC 语义判断深度不低于首批

## 约束

### 检查约束

- [ ] **必须读取所有相关 DevDocs 文档后再检查**
- [ ] **如存在 `docs/devdocs/patterns/verify-blindspots.md`，必须加载并作为额外检查项**（评估者调优闭环）
- [ ] **--docs 层 1 依赖"原始需求"章节——新文档必须存在，历史文档若不存在则输出"前置缺失"并跳过**
- [ ] **--impl AC 满足度必须语义判断，不仅检查标注存在性**
- [ ] **--impl 设计符合度必须对照设计文档原文，不凭记忆**
- [ ] **--ui 阶段 1 必须读取需求文档中的 UI 相关 AC**
- [ ] **--ui 阶段 2 必须获取实现截图进行视觉对比**
- [ ] **--ui 无设计稿输入时不可运行，必须提示用户提供**
- [ ] **必须生成验证报告**

- [ ] **IT 断言完备性检查**（盲区 6, P1）：spec 显式提及 IT-XXX 期望 N 类断言时，`--impl --ac` 必须 diff 期望 vs 实际 @Test 数 + 类级断言粒度；不匹配 ⛔ 阻断 DoD ✅。判定/源案例见 [references/impl-completeness-rubric.md](references/impl-completeness-rubric.md)。
- [ ] **DoD checkbox 粒度约束**（盲区 6）：测试用例部分完成（K/N 类）时 DoD 必须显式标 `[完成 X/Y 类]`，禁止整项 ✅。
- [ ] **SPI DTO 字段透传完备性 cross-check**（盲区 7, P1）：DTO 字段集变化时必须扫描上游 PO 视觉展示性字段类型集做交叉验证；缺失字段必须 `DEFER:<原因>` + cross-link 前端锚点，否则 ⛔ 阻断 SPI 升级合并。
- [ ] **task spec "字段透传矩阵"必填项**（盲区 7）：SPI 出参升级 task 必须含 `Upstream PO Field → New DTO Field → Frontend Display Anchor` 三列映射表。
- [ ] **UI 视觉对齐 review 提前触发**（盲区 7）：SPI 升级影响前端时，`--ui --design` 必须在 DTO 字段定稿前执行（先提取 `visual_anchor_field_set` 再设计 DTO）。

### 分级约束

- [ ] **所有发现必须按 P1/P2/P3 分级**
- [ ] P1 必须列出修复建议
- [ ] 不将 P2/P3 升级为 P1（除非用户要求严格模式）
- [ ] **--impl 必须回答 CE 三个审查问题**

### --live 约束

- [ ] **--live 为可选模式，无浏览器 MCP 时自动降级为静态验证**
- [ ] **--live 必须在 B1/B2/B3 静态验证之后执行**
- [ ] **应用启动失败不阻塞验证流程**（记录 P2 Warning）
- [ ] 仅对 UI/API 类任务执行，核心逻辑和基础设施任务跳过

### 安全约束

- [ ] **不修改代码，只生成报告**
- [ ] **不修改 DevDocs 文档**
- [ ] **不修改设计稿**

### 上下文管理约束

- [ ] 后批次审查深度不低于首批次
- [ ] 每批完成后执行一致性自检
- [ ] --docs 每层检查后验证编号完备性

## Skill 协作

| 场景 | 协作 Skill | 说明 |
|------|-----------|------|
| 开发完成 | `/ms-dev-workflow` | 被调用：任务完成后触发 --impl |
| 对抗式验证 | `/ms-dev-workflow` | 协作：作为验证流程的前置步骤 |
| 需求完成 | `/ms-requirements` | 被调用：需求扩写后触发 --docs --layer1 |
| 设计完成 | `/ms-system-design` | 被调用：设计完成后触发 --docs --layer2 |
| 测试设计完成 | `/ms-test-cases` | 被调用：测试设计后触发 --docs --layer3 |
| UI 任务完成 | `/ms-dev-workflow` | 被调用：UI 任务完成后触发 --ui |
| 追溯扫描 | `/ms-sync` | 复用：标注扫描能力（追溯同步） |
| 追溯检查 | `/ms-sync` | 复用：孤立编号检测（审计同步） |
| AC 缺失 | `/ms-requirements` | 路由：发现 AC 不完整时 |
| 设计偏离 | `/ms-system-design` | 路由：发现设计文档需更新时 |
| 测试缺失 | `/ms-test-cases` | 路由：发现测试缺失时 |
| 代码质量 | `/code-quality` | 互补：code-quality 关注代码质量约束 |
| UI 开发 | `/ui-orchestrator` | 互补：路由开发 vs 验证对齐 |
| 知识沉淀 | `/ms-compound` | 前置：读取验证报告提取改进模式 |
| 验证盲区 | `/ms-compound` | 闭环：compound 沉淀盲区 → verify 加载为额外检查项 |
| 开发就绪 | `/ms-pipeline` | 被调用：dev-tasks 完成后、dev-workflow 前的质量关卡 |

## 外部审查状态机

`--impl` 是外部对抗审查前置验证；外审由 `/ms-dev-workflow` Phase 4 embedded-headless 或 `/adversarial-review` 执行，二者与本 skill 互补。`ms-verify` 不替代外审，只在报告中记录外审前置状态和后续路由。

| 状态 | 含义 | verify 处理 |
|------|------|-------------|
| `EXT_REVIEWED` | T1 codex CLI 或 T2 codex-mcp 成功且无 blocker | 可继续后续同步/沉淀 |
| `EXT_PENDING` | audit 任务经 `--skip-external-review-reason` **主动跳过**外审后待补跑的**阻塞态**（≠ fast/guarded 的延后审查） | 阻塞;须补跑外审达 `EXT_REVIEWED` |
| `review_pending` | fast/guarded 任务独立审查**延后**(非阻塞,已 Commit 1) | 由 `--review-drain` 集中清审转 `已完成`（不复用 `EXT_PENDING`） |
| `EXT_UNRESOLVED` | T1/T2 全失败或环境不可用 | 标为 P2 环境风险，提示补跑外审 |
| `EXT_BLOCKED` | 外审发现未解除 blocker | 保持阻塞，修复后重跑 `--impl` + 外审 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent（通过 Task tool）运行时，遵循 [../_shared/constraints.md § 2-3](../_shared/constraints.md)：统一 envelope 不重复复制；verify 私有统计只放 `summary.details`。

| `summary.details` 字段 | 内容 |
|------------------------|------|
| `dimensions` | `[docs, impl, ui, readiness]` 本次执行维度 |
| `total_p1/total_p2/total_p3` | 各级问题总数 |
| `docs` | `layer1/layer2/layer3: pass | fail | skipped` |
| `impl` | `ac_satisfaction`、`design_conformance`、`traceability`、`test_report_used`、`live_verification` |
| `ui` | `stage1/stage2: pass | fail | skipped` |
| `readiness` | `ac_test_coverage`、`path_specificity`、`dependency_cycle`、`design_task_consistency` |

`blockers` 使用 `"P1: <问题>（<维度>）"`；`output_files` 列出 `verify-report.md` / `readiness-report.md`；`next_recommended` 条件分支：全部通过→`ms-sync`，有 P1→按下方"下一步"表路由。

## 下一步

| 维度 | 结果 | 建议下一步 |
|------|------|------------|
| --docs 层 1 有遗漏 | P1 | `/ms-requirements --incremental` 补充 F/US/AC |
| --docs 层 1 有偏移 | P2 | 与用户确认需求理解是否正确 |
| --docs 层 2 有缺失 | P1 | `/ms-system-design` 补充设计 |
| --docs 层 3 有缺失 | P1 | `/ms-test-cases` 补充测试用例 |
| --impl 有 Blocker | P1 | 修复后重新运行 `/ms-verify --impl` |
| --impl 仅 Warning | P2 | 进入对抗式验证 |
| --impl 设计偏离 | - | `/ms-system-design` 更新设计文档 |
| --ui 阶段 1 有缺失 | P1 | 补充设计稿，覆盖缺失的 AC |
| --ui 阶段 2 有 P1 | P1 | 修复实现后重新验证 |
| --readiness AC 无测试 | P1 | `/ms-test-cases` 补充测试用例 |
| --readiness 循环依赖 | P1 | `/ms-dev-tasks` 重新拆分任务 |
| --readiness 路径不具体 | P2 | `/ms-dev-tasks` 细化任务定义 |
| --readiness 全部通过 | - | 进入 `/ms-dev-workflow` 开发执行 |
| 全部通过 | - | 进入对抗式验证 |
