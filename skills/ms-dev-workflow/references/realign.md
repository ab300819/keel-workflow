# dev-workflow Realign 实例化（policy re-evaluation）

> 共享契约见 [../../ms-pipeline/references/realign.md](../../ms-pipeline/references/realign.md)。
>

## 当前 spec_version

**`devflow.v6`**（v5→v6：里程碑分段执行 + 段末人工验证停点，见 Migration Matrix）

## 与 12 种续做信号的关系（重要）

**realign 独立于续做机制，不是第 13 种信号**。

| 维度 | 续做（resume，12 种信号） | realign（policy re-evaluation）|
|---|---|---|
| 语义 | execution resume（执行恢复） | policy re-evaluation（策略再评估） |
| 触发 | 任务被中断、状态 ≠ 已完成 | 任务已完成 + spec_version 落后（或用户显式 `--realign`） |
| 入口 | `task-orchestration.md` 的 5 步检测 | 本文件的独立子流程 |
| 输出 | 补齐到"首次完成" | 在"已完成"之上追加"新规范差距补齐" |
| 原有证据 | 首次生成 | **完整保留**，仅追加 `Realigned-From` 尾注 |

> Step 1.5 的证据复核（AC 表 / 测试 / trace / 外审 / 后置测试）**不得**把 schema_drift 当作复核失败判据。schema_drift 必须走本文件的独立子流程。

## Migration Matrix（spec_version 演进）

### v5 → v6（里程碑分段执行）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | 队列按 `01` §2「归属里程碑」列切段 + 段末人工验证停点 | **无存量差距**——归属列全 `—` 或整列缺失时不分段，行为与 v5 完全一致 | 不适用 |
| additive | `01` §2.5 里程碑表新增「验收状态」列（人工验证事实的持久源）；检查点新增 `current_milestone` | 缺列/缺字段视为「本次不分段」，⛔ 不回填、⛔ 不推断历史段的验收结论 | 不适用 |

> **零迁移动作。** 里程碑是可选概念，未划分的项目一个字都不用改。
> ⛔ **不得为存量项目推断里程碑或补写「验收状态」**——人验事实只能由人产生，推断出来的「已验证」比没有更危险。

### v4 → v5（失效任务卡前置门）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | 任务卡 `superseded_by` → S1 ⛔ 阻断前置门 | 仅在 ADR 推翻决策时按 ADR 的「已知受影响制品」表回填；⛔ 不批量扫存量任务卡（谁失效需要语义判断） | 无判据——按需触发，不做全量检测 |
| — | 非编码类任务（`TDD 模式 = ⚪ 不适用`）按该档执行 | **无**——该字段本已存在，本次只是明确它对 `CON` 型任务同样适用 | 不适用 |

> ⛔ **本轮不改强制矩阵、主循环、子 Agent 协议、完成流程与 auto-mode。**
> 「`⚪ 基础设施` 任务在三档下均被强制走 S2/S3 + S4-S7」是 **CON 引入前就存在**的状况，与本次无关，单列待办。

### v3 → v4（commit 模板 + 任务台账）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| restructuring | commit 模板由「标题 + 完成内容 + 关联/测试 + 7 个 trailer」改为「标题 + Why + Tests」| 存量 commit ⛔ 不改写（历史不可变）；新 commit 走新模板 | — |
| restructuring | 7 个流程 trailer 迁到 `04-dev-tasks.md` 任务条目 | 存量 `review_pending` 任务：从其 Commit 1 尾注读出 `Review-Batch-Id`/`Review-Due`/`Pending-Reason` 回填台账后再 drain | 任务标 `review_pending` 但台账无 `batch` |
| restructuring | drain 定位 Commit 1 由「grep git log 找 trailer」改为「读台账 `commits`」| 同上，回填 `commits` 字段 | 台账无 `commits` 且任务已提交 |

### v2 → v3（反向依赖）

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| restructuring | 删除「代码追溯标注规范」节；S2-S3 骨架不再写 `@requirement`/`@satisfies`/`@verifies`/`@testcase` | 无回扫动作——**存量标注留着不清理**（删除是纯风险、无收益）；新任务走新规则 | SKILL.md 存在「代码追溯标注规范」节 |
| restructuring | 「标注删减检测」改为「用例删减检测」（快照对象从标注集合改为测试用例名集合）| 无存量差距；下次运行即生效 | verification-flow / auto-mode 仍写「标注删减」 |

### v1 → v2

| 分级 | 变更项 | 修复动作 | 判据 |
|---|---|---|---|
| additive | 新增 `--inline` 轻量入口（前置条件"或"分支 / 指定符解析 / Test Agent inline 分支，见 [inline-entry.md](inline-entry.md)） | 无:已完成任务无结构差距,回扫 no-op(仅规范能力扩展;dev-workflow 无自有产物模板,无模板 frontmatter 同步项) | 无(不产生存量差距) |
| additive | （示例）新增"Phase 4 外审必填"：audit 任务 Phase 4 必填；fast/guarded 延后 drain | 对存量 audit 任务补跑 Phase 4，登记 `EXT_REVIEWED`；fast/guarded 任务标 `review_pending` 等待 drain | review_profile=audit + 无 EXT_* 状态 |
| restructuring | （示例）AC 表列结构变更（新增"验收来源"列） | AskUserQuestion 呈现 before/after，逐任务确认后 Edit | AC 表列数 < 当前模板 |

## 入口

- 用户主入口：`/ms-pipeline realign`（由编排层自动调度到此子流程）
- 底层直用（调试/精细场景）：
  - `/ms-dev-workflow T-03 --realign` — 单任务 realign
  - `/ms-dev-workflow F-01 --realign` — 按功能点过滤
  - `/ms-dev-workflow --all --realign` — 全部已完成任务 realign（需工作区洁净）

## 子流程

```text
1. 加载当前 spec_version 常量 + Migration Matrix
     │
     ▼
2. 筛选目标任务（单任务/功能点/--all）
     │  预条件：任务状态 = 已完成；未完成任务不进入 realign（走续做）
     ▼
3. 工作区检查（同续做约束）
     ├── 非洁净 → fail-fast + 续做命令
     └── 洁净 → 继续
     │
     ▼
4. 对每个任务扫描差距
     ├── additive：按 Migration Matrix 条目判断是否缺字段/证据
     ├── restructuring：证据结构变更（如 AC 表列数）→ 标记待确认
     └── 已达标（无差距）→ 跳过
     │
     ▼
5. 呈现差距总览（按任务分组，分 additive / restructuring 两栏）
     │
     ▼
6. 用户确认执行（restructuring 项逐项 AskUserQuestion）
     │
     ▼
7. 按任务执行补齐
     ├── additive：Test Agent / Impl Agent / 编排器 最小补齐
     │   （如缺 Phase 4 外审 → 调用 /adversarial-review 补跑）
     │   （如缺测试断言 → Test Agent 补测试，Impl Agent 不参与）
     └── restructuring：按确认后方案 Edit
     │
     ▼
8. 原子提交：每任务一个 realign commit
     提交消息格式：
       realign(<task-id>): from <old_spec> to <new_spec>
       
       - additive: <条目列表>
       - restructuring: <条目列表>
       
       Realigned-From: <old_spec> at <iso-timestamp>
     │
     ▼
9. 更新任务正文：追加 `Realigned-From: <old_spec> at <ts>` 尾注
   （任务状态字段保持"已完成"不变）
     │
     ▼
10. 幂等校验：二次运行无新差距 = no-op
```

## 输出

- 补齐后的代码/测试/证据链（Phase 4 外审记录等）
- 每个任务新增 commit（realign commit）
- 任务正文新增 `Realigned-From:` 尾注
- yaml-summary-v1 信封（details: `{tasks_realigned, additive_count, restructuring_count, commits, skipped_tasks}`）

## 安全不变量

- ❌ **不**覆盖原完成证据（AC 表、外审记录、测试用例保留）
- ❌ **不**修改测试代码本身（除非 Migration Matrix 明确要求结构迁移，且标 restructuring）
- ❌ **不**并入续做机制（前文已述）
- ❌ **不**在 `--headless` 模式隐式触发（必须显式 `--realign`）
- ✅ 每任务原子提交，回滚粒度清晰
- ✅ 工作区必须洁净
- ✅ 未完成任务不进入 realign

## 证据保留策略

| 证据类型 | realign 行为 |
|---|---|
| 原 AC 表 | 保留；additive 补列时新列默认值 `—` 或按规范填充 |
| 原测试代码/断言 | 完全保留；additive 补新测试为独立追加，不修改既有断言 |
| 原 Phase 1~3 内审记录 | 保留 |
| 原 Phase 4 外审记录 | 保留；如新规范要求额外轮次 → `--realign` 与现有 `--external-review` 组合触发 Phase 4 复跑。复跑产物独立落盘：`audit/<T-XX>-external-review-realigned-<iso-ts>.yaml`（与原 `audit/<T-XX>-external-review.yaml` 并存，不覆盖）；任务正文追加 `Ext-Review-Realigned-At: <iso-ts>` + `Ext-Review-Realigned-Artifact: <路径>` 两条尾注；Step 1.5 [D2] 的 `ext_review_state` 从新路径读取（若存在），否则回退到原 L2 yaml |
| 原 Git 提交历史 | 保留；realign 追加新 commit，不 rebase 不 amend |

## 与 retrofit 的边界

- 任务在追溯矩阵中无「变更来源」→ 归 **retrofit**
- 任务已完成 + 追溯完整 + spec_version 落后 → 归 **realign**
