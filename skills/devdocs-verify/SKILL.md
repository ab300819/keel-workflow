---
name: devdocs-verify
description: Unified verification skill combining document alignment, implementation correctness, UI design alignment, and development readiness checks. Supports --docs, --impl, --ui, --readiness flags; auto-detects dimensions when called without flags. Triggers on "verify", "review", "alignment", "验证", "审查", "对齐检查", "需求验证", "设计一致性", "UI 对齐", "就绪检查", "质量关卡", "readiness". NOT for syncing docs with progress (use devdocs-sync).
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion  # 可选: Playwright MCP, Chrome DevTools MCP, Pencil MCP
---

# 统一验证

四合一验证 Skill：文档对齐 + 实现正确性 + UI 设计对齐 + 开发就绪检查，替代原 `devdocs-review`、`devdocs-requirements-alignment`、`devdocs-ui-alignment`。

## 语言规则

- 支持中英文提问
- 统一中文回复
- 使用中文生成报告

## 定位

```
devdocs-verify --docs  ：各层文档之间是否对齐（原 requirements-alignment）
devdocs-verify --impl  ：实现是否正确（原 review）
devdocs-verify --ui    ：UI 设计和实现是否对齐（原 ui-alignment）
对抗式验证            ：代码质量是否合格（dev-workflow 内置）
devdocs-verify --readiness ：开发就绪条件是否满足（pipeline 关卡）
```

**互补关系**：`--docs` 检查"文档写对了没"，`--impl` 检查"代码做对了没"，`--ui` 检查"界面做对了没"，`--readiness` 检查"能开工了没"，对抗式验证检查"代码写得好不好"。

## 触发条件

- 需求/设计/测试文档完成后（`--docs`）
- 任务开发完成后、对抗式验证之前（`--impl`）
- UI 相关任务开发完成后（`--ui`）
- 任务拆分完成、进入开发前（`--readiness`）
- 用户要求检查文档/实现/UI 对齐

## 运行模式

```bash
/devdocs-verify                    → 自动检测维度（见下方规则）
/devdocs-verify --docs             → 仅文档对齐（三层检查）
/devdocs-verify --docs --layer1    → 仅原始需求 → 需求文档
/devdocs-verify --docs --layer2    → 仅需求文档 → 系统设计
/devdocs-verify --docs --layer3    → 仅需求文档 → 测试用例
/devdocs-verify --impl             → 仅实现正确性（AC + 设计 + 追溯）
/devdocs-verify --impl --ac        → 仅 AC 满足度
/devdocs-verify --impl --design    → 仅设计符合度
/devdocs-verify --impl --trace     → 仅追溯完整性
/devdocs-verify --ui               → 仅 UI 设计对齐（两阶段）
/devdocs-verify --ui --design      → 仅设计稿 ↔ 需求
/devdocs-verify --ui --impl        → 仅设计稿 ↔ 实现
/devdocs-verify --readiness          → 开发就绪检查（进入 dev-workflow 前的质量关卡）
/devdocs-verify T-01 T-02          → 指定任务范围（自动 --impl）
```

### 自动检测规则

无参数调用时，根据项目状态自动选择维度：

1. 检查是否存在最新 `05-test-report.md` → 有则 `--impl` 辅助判断
2. 检查当前开发阶段：
   - 有 `03-test-cases.md` 但无代码提交 → `--docs`（文档阶段）
   - 有代码提交且任务进行中 → `--impl`（开发阶段）
   - UI 任务 + 有设计稿 → `--impl` + `--ui`
3. 无法判断 → 询问用户

## 工作流程

```text
1. 确定验证维度（自动检测或用户指定）
   │
   ▼
2. 读取 DevDocs 文档
   ├── 01-requirements.md（AC 列表、原始需求）
   ├── 02-system-design.md（设计规范）
   ├── 03-test-cases.md（测试用例、追溯矩阵）
   └── 05-test-report.md（如存在，辅助 --impl 判断）
   │
   ▼
3. 按维度执行检查
   ├── --docs：三层对齐检查
   ├── --impl：三维度正确性审查
   ├── --ui：两阶段设计对齐
   └── --readiness：四维度就绪检查
   │
   ▼
4. 生成验证报告
   │
   ▼
5. 修复建议与路由
```

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

### 层 3：需求文档 → 测试用例

检查 AC → 测试用例映射、正向路径覆盖、异常路径覆盖。**复用 devdocs-sync --audit 的孤立编号检测能力**。

---

## 维度 B：实现正确性（--impl）

验证代码实现是否正确——AC 满足度、设计符合度、追溯完整性。

### B1：AC 满足度审查

逐条验证实现是否匹配验收标准。

1. 读取 `01-requirements.md` 中所有 AC
2. 通过 `@satisfies` 标注 + 代码搜索定位实现
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

### B3：追溯完整性审查

检查 `@satisfies`/`@verifies` 覆盖率。**复用 devdocs-sync --trace 的扫描能力**。

---

## 维度 C：UI 设计对齐（--ui）

验证 UI 设计和实现是否对齐——两阶段验证。

### C1：设计稿 ↔ 需求对齐

支持三种设计稿来源：Pencil .pen 文件、截图/图片、Figma（通过截图或 MCP）。

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
| 无设计稿输入 | **不可运行**——提示用户提供设计稿 |
| 有设计稿，无浏览器 MCP | 阶段 1 正常；阶段 2 要求用户提供实现截图 |
| 有浏览器 MCP，无设计稿 MCP | 要求用户提供设计稿截图 |

**工具说明**：Pencil MCP（`mcp__pencil__*`）、Playwright MCP（`mcp__playwright__*`）、Chrome DevTools MCP（`mcp__chrome-devtools__*`）为可选依赖，按可用性自动选择。无 MCP 时降级为用户提供截图，不影响验证能力。

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
2. 任务的文件路径与设计文档的代码结构一致
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
| **P1** | 阻塞发布 | 必须修复，建议转入 devdocs-dev-tasks |
| **P2** | 应修复 | 建议修复，建议转入 devdocs-insights |
| **P3** | 可优化 | 可选修复，记录备忘 |

### P1 判定标准

- **--docs**：原始需求遗漏（层 1）、AC 无设计支撑（层 2）、AC 无对应测试（层 3）
- **--impl**：AC 未满足（❌）、接口签名与设计不符、模块职责严重偏离、核心 AC 无 @satisfies 标注
- **--ui**：布局结构与设计稿不符、关键交互状态未实现、AC 描述的 UI 行为在设计稿中缺失
- **--readiness**：AC 无对应测试用例（D1）、任务存在循环依赖（D3）、孤立任务无需求关联（D4）

### P2 判定标准

- **--docs**：原始需求偏移（层 1）、AC 缺异常路径测试（层 3）
- **--impl**：AC 部分满足（⚠️）、数据流轻微偏离、@satisfies 覆盖率 < 80%
- **--ui**：间距/颜色/字体的显著偏差、响应式断点差异
- **--readiness**：任务文件路径不够具体（D2）、设计↔任务文件路径不一致（D4）

### P3 判定标准

- **--docs**：过度扩展（层 1）、设计孤立项（层 2）
- **--impl**：非核心代码缺少标注、非关键路径微偏离
- **--ui**：间距/颜色/字体的轻微偏差
- **--readiness**：任务描述过于简略但路径具体

## 输出文件

| 维度 | 输出文件 |
|------|----------|
| --docs / --impl / --ui | `docs/devdocs/verify-report.md` |
| --readiness | `docs/devdocs/readiness-report.md` |

详细模板参见 [templates/verify-report.md](templates/verify-report.md)（--docs/--impl/--ui）和 [templates/readiness-report.md](templates/readiness-report.md)（--readiness）

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
- [ ] **--docs 层 1 依赖"原始需求"章节——新文档必须存在，历史文档若不存在则输出"前置缺失"并跳过**
- [ ] **--impl AC 满足度必须语义判断，不仅检查标注存在性**
- [ ] **--impl 设计符合度必须对照设计文档原文，不凭记忆**
- [ ] **--ui 阶段 1 必须读取需求文档中的 UI 相关 AC**
- [ ] **--ui 阶段 2 必须获取实现截图进行视觉对比**
- [ ] **--ui 无设计稿输入时不可运行，必须提示用户提供**
- [ ] **必须生成验证报告**

### 分级约束

- [ ] **所有发现必须按 P1/P2/P3 分级**
- [ ] P1 必须列出修复建议
- [ ] 不将 P2/P3 升级为 P1（除非用户要求严格模式）
- [ ] **--impl 必须回答 CE 三个审查问题**

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
| 开发完成 | `/devdocs-dev-workflow` | 被调用：任务完成后触发 --impl |
| 对抗式验证 | `/devdocs-dev-workflow` | 协作：作为验证流程的前置步骤 |
| 需求完成 | `/devdocs-requirements` | 被调用：需求扩写后触发 --docs --layer1 |
| 设计完成 | `/devdocs-system-design` | 被调用：设计完成后触发 --docs --layer2 |
| 测试设计完成 | `/devdocs-test-cases` | 被调用：测试设计后触发 --docs --layer3 |
| UI 任务完成 | `/devdocs-dev-workflow` | 被调用：UI 任务完成后触发 --ui |
| 追溯扫描 | `/devdocs-sync` | 复用：标注扫描能力（追溯同步） |
| 追溯检查 | `/devdocs-sync` | 复用：孤立编号检测（审计同步） |
| AC 缺失 | `/devdocs-requirements` | 路由：发现 AC 不完整时 |
| 设计偏离 | `/devdocs-system-design` | 路由：发现设计文档需更新时 |
| 测试缺失 | `/devdocs-test-cases` | 路由：发现测试缺失时 |
| 代码质量 | `/code-quality` | 互补：code-quality 关注代码质量约束 |
| UI 开发 | `/ui-orchestrator` | 互补：路由开发 vs 验证对齐 |
| 知识沉淀 | `/devdocs-compound` | 前置：读取验证报告提取改进模式 |
| 开发就绪 | `/devdocs-pipeline` | 被调用：dev-tasks 完成后、dev-workflow 前的质量关卡 |

## 子 Agent 摘要格式

当本 Skill 作为子 Agent（通过 Task tool）运行时，返回以下结构化摘要：

```yaml
skill: devdocs-verify
dimensions: [docs, impl, ui, readiness]  # 实际执行的维度
summary:
  total_p1: 0
  total_p2: 0
  total_p3: 0
  status: pass | fail | partial
  docs:
    layer1: pass | fail | skipped
    layer2: pass | fail | skipped
    layer3: pass | fail | skipped
  impl:
    ac_satisfaction: "X/Y satisfied"
    design_conformance: pass | fail
    traceability: "X% coverage"
    test_report_used: true | false
  ui:
    stage1: pass | fail | skipped
    stage2: pass | fail | skipped
  readiness:
    ac_test_coverage: "X/Y covered"
    path_specificity: pass | fail
    dependency_cycle: false
    design_task_consistency: pass | fail
blockers:
  - "P1: AC-003 未满足（--impl）"
output_files:
  verify: docs/devdocs/verify-report.md      # --docs / --impl / --ui
  readiness: docs/devdocs/readiness-report.md # --readiness
```

## 下一步

| 维度 | 结果 | 建议下一步 |
|------|------|------------|
| --docs 层 1 有遗漏 | P1 | `/devdocs-requirements --incremental` 补充 F/US/AC |
| --docs 层 1 有偏移 | P2 | 与用户确认需求理解是否正确 |
| --docs 层 2 有缺失 | P1 | `/devdocs-system-design` 补充设计 |
| --docs 层 3 有缺失 | P1 | `/devdocs-test-cases` 补充测试用例 |
| --impl 有 Blocker | P1 | 修复后重新运行 `/devdocs-verify --impl` |
| --impl 仅 Warning | P2 | 进入对抗式验证 |
| --impl 设计偏离 | - | `/devdocs-system-design` 更新设计文档 |
| --ui 阶段 1 有缺失 | P1 | 补充设计稿，覆盖缺失的 AC |
| --ui 阶段 2 有 P1 | P1 | 修复实现后重新验证 |
| --readiness AC 无测试 | P1 | `/devdocs-test-cases` 补充测试用例 |
| --readiness 循环依赖 | P1 | `/devdocs-dev-tasks` 重新拆分任务 |
| --readiness 路径不具体 | P2 | `/devdocs-dev-tasks` 细化任务定义 |
| --readiness 全部通过 | - | 进入 `/devdocs-dev-workflow` 开发执行 |
| 全部通过 | - | 进入对抗式验证 |
