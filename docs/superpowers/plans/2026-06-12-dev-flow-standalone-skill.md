# dev-flow：独立通用开发流程 skill 方案

> 2026-06-12 · 状态：已对齐（Codex 独立方案 ⇄ Claude 业界调研，2 轮收敛，D1-D5 全 AGREE）· 未实施
> 定位：不依赖 DevDocs 的通用简化开发执行器——"契约先行 + 红绿 + 质量地板 + 证据交付"，复杂治理留给 ms-*。

## 1. 动因

- ms-dev-workflow 深度绑定 DevDocs：输入要 `04-dev-tasks` 的 T-XX/AC 编号、Sprint Contract 从 AC+设计文档推导、Commit 2 + /ms-sync + traceability、review-drain 走 /ms-verify——无 DevDocs 文档体系无法启动
- 业界框架（CE/superpowers/BMAD 等）只有松散过程片段，没有带门控的完整执行管线；"带门控的执行内核"是 dev-workflow 的差异化资产
- 质量层已可移植：code-quality（阈值/命名/注释/设计原则）与 testing-guide 均为独立 SSOT，2026-06-12 重构后无 DevDocs 依赖
- 目标：**一般化、通用、简化**——覆盖但不限于 CE/superpowers/BMAD 的使用场景

## 2. 调研结论（10+ 框架，引用见文末）

**共性骨架（最大公约数）**：意图澄清 → 写下计划（人审）→ 小任务实现循环 → 独立验证 → 提交/沉淀。

**跨流派 3 硬门控交集**：
1. **计划/契约批准门**——Kiro/Spec Kit/BMAD Quick Dev/Claude Code 官方四家共有且仅共有的人工检查点；BMAD 明言"把人工控制重定位到少数高杠杆时刻"
2. **可执行验证门**——"给 agent 一个能跑的检查"是官方第一原则
3. **fresh-context 审查门**——"审查者必须是新上下文"为跨流派共识（superpowers 双阶段审查 / BMAD QA gate / 官方对抗式子代理三方背书）

**隐性共同纪律**：fresh chat per task（对抗 context rot）。
**反模式**：Kiro 式逐阶段批准（人力瓶颈）、Taskmaster 式无验证执行、审查噪音淹没主任务（BMAD"审查即分诊"为解法）。
**分歧裁决**：spec 重 vs 轻——dev-flow 走轻 spec + 重纪律路线（重 spec 场景归 DevDocs）。

## 3. 方案

### 3.1 基本形态

- **命名**：`dev-flow`，目录 `skills/dev-flow/`，**不带 ms- 前缀**（ms- 为 DevDocs 流程命名空间）
- description 要点：Execute general development tasks from a plan document, prompt, or issue text without DevDocs. Contract-first TDD gates, quality floor, fresh-context verification. NOT for DevDocs T-XX execution (use ms-dev-workflow)
- SKILL.md 目标 ≤300 行（硬约束 ≤500）；契约模板内嵌，不建复杂 references

### 3.2 五阶段骨架

| 阶段 | 目的 | 输出 |
|------|------|------|
| 1. 输入定位 | 读计划文档/prompt/issue，扫代码上下文 | 目标、范围、风险、候选测试命令 |
| 2. 执行契约 | 从"任务描述+代码上下文+现有测试习惯"协商 Execution Contract | 契约 yaml（见 3.4）；**Contract Gate** |
| 3. 测试先行 | 写最小测试，确认红验，测试冻结 | 红验记录；**Red-Green Gate** |
| 4. 实现与重构 | 只实现契约内行为，跑到绿验 | 代码变更、绿验结果 |
| 5. 证据与交付 | 质量地板 + fresh-context 契约审查 + 可选提交 | 交付报告；**Verify Gate** |

### 3.3 三硬门控

1. **Contract Gate**：必须形成可执行验收契约（目标/范围/可观察行为/证据方式）。**唯一默认人工批准点**（交互模式一次 AskUserQuestion；headless/明确任务自动通过并记录理由）。后续仍可临时询问（测试缺陷/范围冲突/危险操作），但不做 Kiro 式逐阶段批准。
2. **Red-Green Gate**：行为变更且自动测试可行时必须先红后绿；红验后测试冻结（diff 机械校验），实现阶段不得改测试；自动测试不可行时必须在契约中声明降级证据（命令/截图/手动验证 + 原因）。
3. **Verify Gate**（两个独立子判定，均必过，不揉黑盒）：
   - **Evidence Check**：质量地板通用化——绿验 `skipped/todo=0`、测试冻结 diff 校验、声称 vs 实际 diff 一致、每个契约行为至少一条独立证据、受影响测试后置
   - **Fresh-Context Contract Review**：新上下文子 Agent 只校验 `diff ↔ Execution Contract ↔ evidence` 合规（spec 合规优先于代码质量），contract-critical 阻断；不扩展为完整代码质量审查

**审查即分诊**：审查发现分两类——契约内（含通用不变量：不破坏现有测试、测试冻结、无未解释大 diff、安全底线）critical 阻断修复；契约外发现（顺手发现的 bug/坏味道）不阻断、不顺手改，列入交付报告 deferred 清单。

### 3.4 Execution Contract（Sprint Contract 的通用化改造）

```yaml
execution_contract:
  source: "<plan path | prompt | issue text>"
  goal: "<一句话目标>"
  in_scope: ["<本次会做什么>"]
  out_of_scope: ["<明确不做什么>"]
  expected_behavior: ["<用户或系统可观察结果>"]
  evidence_plan:
    - kind: "test | command | screenshot | manual"
      command_or_path: "<验证方式>"
  risk_flags: ["<public-api | schema | auth | data-loss | ui | low-risk>"]
  stop_conditions: ["<遇到什么必须暂停确认>"]
```

**模糊任务处理**：可推导单一可验证目标 → 写明"推导契约"继续；多个合理方向 → 必须确认；完全无验收标准（"优化一下"）→ 不进实现、降级为契约澄清；`--explore` 允许 spike/方案/可回滚实验，不得声称"已完成"。
**不引入新编号体系**：契约只用本轮局部 checklist，不生成 DF-XX/AC-XX。

### 3.5 执行模型取舍（对照 ms-dev-workflow 内核）

| 机制 | 结论 |
|------|------|
| 红验 + 测试冻结 | 保留为硬门控（比物理双 Agent 更本质） |
| 双 Agent 物理隔离 | 降级为条件强制：默认单 Agent "Test Pass / Impl Pass" 两阶段；`--strict-tdd` 或高风险 flag 强制物理子 Agent；补偿：Verify Gate 的 fresh-context 审查为默认（"写码者不自评"的最低保障） |
| 质量地板 5 条 | 全保留，术语通用化（"行为型 AC"→"契约行为"） |
| review_profile 三档 / 断点状态机 / Phase 1-4 / Commit 2 文档同步 | 砍掉；对抗审查降级为 `--audit`（调 /adversarial-review）；中断恢复靠计划文档勾选状态 |
| 原子提交 | 保留为提交规范（/commit-convention），不强制自动提交 |
| codify | 交付报告末尾可选"建议沉淀项"一行（仅确有可复用惯例/踩坑时输出），不自动写 memory、不调 ms-compound |

### 3.6 Flags（极少）

| flag | 作用 |
|------|------|
| `--strict-tdd` | 强制物理双 Agent / 信息屏障（核心逻辑） |
| `--audit` | 完成前跑完整独立审查（/adversarial-review） |
| `--no-commit` | 只改代码 + 输出证据，不提交 |
| `--explore` | 模糊/调研任务：spike/方案/可回滚实验，不声称完成 |

### 3.7 批量形态

计划文档含多个 checklist 项：逐项执行、每项 fresh context（对抗 context rot）；仅"可独立执行、可验收"的项进入批量，叙事型 checklist 先转任务队列；每项启动前重读计划文档勾选状态（天然断点恢复，无检查点文件）。单任务 prompt 输入无批量逻辑。

### 3.8 体系边界与复用

| 维度 | 决策 |
|------|------|
| NOT-for（dev-flow） | DevDocs T-XX/traceability/04-dev-tasks 状态推进/review-drain → 用 ms-dev-workflow |
| NOT-for（ms-dev-workflow 侧补） | 仅有计划文档/普通 issue/CE-superpowers-BMAD 松散计划 → 用 dev-flow |
| superpowers 衔接 | writing-plans 产出可作输入；executing-plans 可作上层计划执行器、单项开发由 dev-flow 接管门控；只识别 Markdown checklist + 自然语言，不复制其计划语法 |
| 升级路径 | 项目转文档驱动时用 /ms-retrofit 反向生成 DevDocs；dev-flow 交付报告可作 retrofit 辅助输入 |
| 复用资产 | code-quality（Verify 阶段挂载阈值/命名/注释/设计原则 Blocker）、testing-guide（断言质量）、commit-convention、git-safety、adversarial-review（--audit）、ui-orchestrator（UI 任务可选） |

## 4. 实施清单（待确认后执行）

1. 新建 `skills/dev-flow/SKILL.md`（≤300 行：触发条件、五阶段、三门控、契约模板、flags、批量、NOT-for、复用索引）
2. ms-dev-workflow SKILL.md 的 NOT-for 区补一行反向边界（仅指针，不改流程）
3. AGENTS.md 架构决策/当前状态登记新 skill
4. README.md skill 清单更新
5. Codex 审查 diff 至 PASS 后提交

## 5. 对齐记录

- R1：Codex 独立出方案（dev-flow 命名/5 阶段/3 门控/Execution Contract/取舍表/边界），Claude 并行业界调研（12 来源、7+ 框架）
- R2：调研证据驱动 5 修订点全 AGREE——D1 fresh-context 审查升默认（Verify Gate 子项，范围收紧为 diff↔契约↔证据）/ D2 Contract Gate=唯一默认人工批准点（措辞补强：计划性必经，临时询问不受限）/ D3 审查即分诊（契约定义含通用不变量）/ D4 codify 尾巴（防仪式化）/ D5 批量 fresh context + checklist 天然恢复（补：仅可验收项进批量）；Verify Gate 采纳"一个门、两个独立 verdict"结构

## 引用

- superpowers（obra）；Compound Engineering（Every）；BMAD-METHOD v6（含 Quick Dev）；GitHub Spec Kit；Amazon Kiro；Aider；Claude Code official best practices；OpenSpec；Taskmaster；Agent OS；Sakasegawa 2026《A Survey of Development Workflows in the Coding Agent Era》
- 完整链接见调研纪要（会话内）；关键论断已内化于 §2
