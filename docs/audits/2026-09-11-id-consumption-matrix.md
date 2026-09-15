# 矩阵 1：编号类型逐文件消费矩阵

> 2026-09-11 实测。**本文是 [对象模型收敛 v1](../superpowers/specs/2026-09-11-devdocs-object-model-convergence-design.md) 被否后的前置交付物之一**，用于回答「改一个编号类型到底要动多少地方」。
>
> ⛔ 本文只列事实，⛔ 不含设计结论。

## 0. 总量

| 口径 | 文件数 |
|---|---:|
| 引用**实例**（`UT-001` / `IT-003` / `E2E-001` / `Journey-001`）| 32 |
| 出现**类型名**（白名单 / 正则 / 枚举 / 链路图）| 21 |
| 引用 `CON` | 13 |
| **并集** | **46**（跨 16 个 skill）|

> ⚠️ v1 设计估计「约 23 个文件」，**实测偏小一倍**。

## 1. 按角色分类（角色决定迁移成本）

| 角色 | 含义 | 文件数 | 迁移成本 |
|---|---|---:|---|
| **W** 类型白名单 / 正则 / 链路图 | 硬编码了 `UT/IT/E2E/Journey` 这组名字 | 16 | 🔴 **必改**，漏一处就静默漏扫 |
| **U** 用户面 flag | 子指令直接建在类型名上 | 2 | 🔴 **必改**，且影响用户可见语法 |
| **P** 产物模板占位 | 模板里的 `UT-XXX` 占位与表头 | 9 | 🟡 必改，但机械 |
| **X** 示例 / 说明文字 | 举例用的具体编号 | 17 | 🟢 alias 可覆盖，可延后 |
| **N** 反例 / 防陷阱 | 提到编号但不是消费（扫描陷阱论证）| 2 | ⚪ 不必改 |

**🔴 + 🟡 = 27 个文件是硬改动面。**

## 2. 逐文件表

### 2.1 W — 类型白名单 / 正则 / 链路图（🔴 16 个）

| 文件 | 行 | 证据 |
|---|---:|---|
| `ms-pipeline/references/health-lint-implementation.md` | 239 | `health/dead-link` 定义源正则：`（F/US/AC/T/T-RF/ADR/INS/BUG/UT/IT/E2E/Journey）` |
| `ms-verify/SKILL.md` | 288 | 「逐条检查 AC → UT/IT/E2E 映射」 |
| `ms-dev-workflow/SKILL.md` | 101 | S1「从 `04-dev-tasks.md` 获取任务、F/AC/UT/IT/E2E 关联」 |
| `ms-dev-workflow/references/verification-flow.md` | 182 | S8 判据「补一条 UT/IT/E2E 断言或走豁免枚举」 |
| `ms-dev-workflow/references/ui-quality-checklist.md` | 83 | 「可执行断言（UT / IT / E2E）」 |
| `ms-sync/SKILL.md` | 72 | 追溯链图「UT/IT/E2E 测试 ←→ 测试文件」 |
| `ms-pipeline/SKILL.md` | 220 | 交接摘要「UT/IT/E2E 编号、覆盖到的 AC」 |
| `ms-test-cases/SKILL.md` | 3 | **`description` 本身**：「设计可追溯的 UT/IT/E2E 用例文档」 |
| `ms-test-cases/references/realign.md` | 22 | realign 判据含「UT/IT/E2E 选择理由」 |
| `ms-dev-tasks/references/realign.md` | 16 | 「行为型任务才强制 `UT/IT/E2E`」 |
| `ms-feature/SKILL.md` | 155 | 追溯链「F → US → AC → UT/IT/E2E」 |
| `ms-bugfix/SKILL.md` | 42 | 「测试执行失败（UT/IT/E2E）」 |
| `ms-retrofit/SKILL.md` | 155 | 「**测试编号** \| UT-XXX, IT-XXX, E2E-XXX \| 必须」 |
| `ms-retrofit/references/version-migration.md` | 38 | 「为测试用例添加 UT/IT/E2E-XXX」 |
| `testing-guide/SKILL.md` | 125 | ⛔ 不写 `@testcase UT-XXX` 的禁令 |
| `testing-guide/templates/branch-coverage-analysis.md` | 26 | BCA 回溯规则「转为正式测试（UT/IT/E2E 编号）」 |

### 2.2 U — 用户面 flag（🔴 2 个）

| 文件 | 行 | 证据 |
|---|---:|---|
| `ms-test-run/SKILL.md` | 19, 42-44 | `/ms-test-run --ut` / `--it` / `--e2e` —— **子指令直接建在类型名上** |
| `ms-test-run/templates/test-report-template.md` | 9 | 报告头「执行模式: 全量 / `--ut` / `--it` / `--e2e` / `F-XXX` / `--trace` / `--affected`」 |

> ⚠️ **与 [flow-backlog 第 1 条](2026-09-11-devdocs-flow-backlog.md) 相交**：这三个 flag 既是「类型名耦合」又是「子指令露出」。两件事必须同批决策，否则会改两次。

### 2.3 P — 产物模板占位（🟡 9 个）

| 文件 | 行 | 证据 |
|---|---:|---|
| `ms-test-cases/templates/test-cases-template.md` | 68 | 追溯矩阵表头 + 行 |
| `ms-test-cases/templates/unit-test-template.md` | 34 | `\| UT-001 \| AC-001 \| …` |
| `ms-test-cases/templates/integration-test-template.md` | 88 | `\| IT-001 \| AC-003 \| …` |
| `ms-test-cases/templates/e2e-test-template.md` | 103 | `\| E2E-001 \| US-001 \| …` |
| `testing-guide/templates/traceability-matrix.md` | 10 | 「单元测试 \| UT \| UT-XXX」类型表 |
| `ms-dev-tasks/templates/task-template.md` | 76 | 任务卡「IT-001: 验证表结构创建成功」 |
| `ms-verify/templates/readiness-report.md` | 36 | 「AC-001 \| … \| UT-001, IT-001」 |
| `ms-verify/templates/verify-report.md` | 90 | 同上 |
| `ms-feature/templates/feature-log-template.md` | 17 | 「UT-013 ~ UT-015, E2E-003」 |

### 2.4 X — 示例 / 说明（🟢 17 个，alias 可覆盖）

`ms-sync/references/{absorb,archive,audit}-mode.md` · `ms-dev-workflow/references/{skeleton-examples,task-orchestration}.md` · `ms-system-design/references/incremental-design.md` · `ms-feature/references/full-mode-steps.md` · `ms-verify/references/{impl-completeness,p-severity}-rubric.md` · `ms-requirements/templates/requirements-template.md` · `ms-test-run/templates/test-report-template.md` · `code-quality/SKILL.md` · 及 CON-only 引用的 `ms-requirements/{SKILL,references/realign,references/release-compliance}.md` · `ms-system-design/references/realign.md` · `ms-dev-workflow/references/realign.md`

### 2.5 N — 反例，⛔ 不必改（2 个）

| 文件 | 行 | 为什么不改 |
|---|---:|---|
| `_shared/constraints.md` | 456 | `id/scan-word-boundary` 里论证「`UT-001` 含 `T-001` 会产生幻影」的**反例**，改了论证就废了 |
| `agent-memory/templates/devdocs-state-template.md` | 54 | 同上，扫描陷阱说明 |

## 3. `CON` 的消费面（13 个文件）

| 文件 | 引用数 | 性质 |
|---|---:|---|
| `ms-requirements/references/release-compliance.md` | 28 | 🔴 上架合规清单，CON 的最大单一消费者 |
| `_shared/constraints.md` | 17 | 🔴 标识登记 + 消费边界两节 |
| `ms-requirements/templates/requirements-template.md` | 12 | 🟡 §6 约束表模板 |
| `ms-requirements/SKILL.md` | 8 | 🔴 生成规则 |
| `ms-system-design/references/incremental-design.md` | 5 | 🟢 |
| `ms-dev-tasks/SKILL.md` | 4 | 🔴 `:187` 追溯约束二选一 + `:189` TDD 档 |
| `ms-requirements/references/realign.md` | 3 | 🟡 |
| `ms-system-design/references/realign.md` · `ms-dev-tasks/references/realign.md` · `agent-memory/templates/devdocs-state-template.md` | 2 each | 🟡 |
| `ms-test-run/SKILL.md` · `ms-pipeline/references/health-lint-implementation.md` · `ms-dev-workflow/references/realign.md` | 1 each | 🟢 |

> `release-compliance.md` 的 28 处是之前几轮**完全没发现**的消费者。任何动 `CON` 的方案都要先看它。

## 4. 迁移期四态：每个角色的行为

假设引入新类型 `X` 替换旧类型集合 `{A,B,C}`，并保留 alias。

| 角色 | 旧 ID（`A-001`）| 新 ID（`X-001`）| alias（`X-001` ⟵ `A-001`）| 混用（同文件两种）|
|---|---|---|---|---|
| **W** 白名单 / 正则 | 命中 | ❌ **漏扫**（正则不含 X）| ❌ 取决于是否解析 alias | ⚠️ 部分命中 = 最危险 |
| **U** 用户 flag | 可用 | ❌ 无对应 flag | — | ⚠️ 用户不知道该用哪个 |
| **P** 模板 | 产出旧号 | 需改模板 | — | ⚠️ 新产物混两种 |
| **X** 示例 | 无影响 | 无影响 | 无影响 | 无影响 |
| **M** 追溯矩阵 / 覆盖率 | 计入 | ❌ 不计入 | ⚠️ **可能重复计分** | 🔴 分母不可信 |

**最危险格**：W 角色的「混用」——正则部分命中会**静默**产生假阴性，没有任何门会报。这正是 `constraints.md:407` 记载的 `CON` 覆辙形态（「没有单一执行 SSOT，消费方逐渐分叉」）。

## 5. 前置结论（供 v2 设计使用）

1. **改动面实测 46 文件 / 16 skill**，其中 🔴🟡 硬改动 27 个。任何「约 N 个文件」的估计必须以本表为准。
2. **W 角色 16 处是成败关键**。迁移方案必须给出：这 16 处如何在同一批 commit 内改完，以及改完前如何防止混用。
3. **`ms-test-run` 的 `--ut/--it/--e2e` 是类型名与用户语法的耦合点**，与 flow-backlog 第 1 条同批。
4. **`release-compliance.md` 的 28 处 CON 引用**是此前未发现的消费者，动 `CON` 前必须先读它。
5. **`constraints.md:456` 与 `devdocs-state-template.md:54` ⛔ 不得改**——它们是防扫描陷阱的反例，改了论证就废。
