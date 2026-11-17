# adversarial-review 交叉验证 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/adversarial-review` 交互调用时可让 codex 与 agy 并行独立完成同一件事，对齐意见后给出一个最终结论。

**Architecture:** 规格改动，无代码。对齐规则、询问规则、一方失败判据集中写在新文件 `references/cross-validation.md`（单一真源）；agy 的命令只出现在 `references/external-reviewer-integration.md`；`SKILL.md` 只留流程骨架与硬约束并指向这两处。

**Tech Stack:** Markdown 规格；`codex` CLI；`agy` CLI 1.5.7；`skills/pipeline/scripts/health-lint.py`。

**Spec:** `docs/superpowers/specs/2026-11-16-adversarial-review-cross-validation-design.md`

## Global Constraints

- `skills/adversarial-review/SKILL.md` ≤ 500 行（现 453 行）。
- 一条规则只写一处（`AGENTS.md` § 修改约束）：对齐 / 询问 / 一方失败的判据只在 `cross-validation.md`，其余位置只留名字和链接。
- 不动：`skills/dev-workflow/`、`skills/verify/`、`skills/shared/constraints.md`；embedded-headless 仍只用 codex T1/T2。
- agy 用的模型 ⛔ 不得与宿主或 codex 同族；默认取 `agy models` 里非同族的最高档。
- 设计稿里三项「我的决定」按设计稿执行：`both` 来源仍走完整验证；codex 额度耗尽但 agy 成功时不停下、如实标单方；无法提问时默认单方 codex。
- 实测修正设计稿一处：`--print-timeout` 要带单位（`600s`），纯数字会被拒绝。

## Review Focus

1. 一方截断、另一方成功：截断方的输出 ⛔ 不进对齐，结论首行标单方。
2. 一方沉默、另一方提出：算单方来源，⛔ 不算冲突。
3. 两方共同误解同一条约束：`both` 不免除验证。
4. agy 结构化输出的 `response` 字段带过程叙述：取最后一个完整顶层 JSON 对象再校验。
5. 用户请求里已说明用谁：不再询问。

以上都是规则走查项，写进 Task 1 的判据表；Task 5 用真跑覆盖 1（以不存在的模型名模拟失败）和 4。

---

### Task 1: `references/cross-validation.md`（新增，单一真源）

**Files:** Create `skills/adversarial-review/references/cross-validation.md`

**Produces:** 章节名供其他文件链接——`§ 询问审查方式`、`§ 并行调度`、`§ 对齐`、`§ 一方失败`、`§ 摘要字段`。

- [ ] 按设计稿 5.2（询问）、5.3（对齐与来源处置）、5.5（一方失败）、5.6（摘要字段与现有字段调整后的含义）写入，表格照搬设计稿的行。
- [ ] 验证：`grep -c "^## " skills/adversarial-review/references/cross-validation.md` 输出 5。
- [ ] Commit。

### Task 2: `references/external-reviewer-integration.md` 加 agy

**Files:** Modify 同名文件（概述、两种使用模式、新增 `## agy CLI` 一节、失败分类表后补 agy 的失败信号）

- [ ] 新增 agy 一节：检测（`which agy` + 含一次真实工具调用的冒烟）、两条调用命令（文本 / 结构化，`--mode plan --sandbox --model <id> --print-timeout 600s … < /dev/null`）、解析（外层 JSON 的 `response` 取最后一个完整顶层 JSON 对象）、模型选取规则、失败信号（模型不可用：退出码 1 + stderr `invalid model selection`，已实测；额度 / 鉴权标「未实测」）。
- [ ] 概述改为「两个外部审查方 + 同模型兜底」；写明 embedded-headless 不变。
- [ ] 补一条：brief 走命令行参数时必须 `< /dev/null`；用标准输入传 brief 的路径 ⛔ 不加。
- [ ] 验证：`health-lint.py --skills-dir skills` 0 blocker。Commit。

### Task 3: `SKILL.md` 流程骨架

**Files:** Modify `skills/adversarial-review/SKILL.md`

- [ ] 概述一句、流程图加 S2.5 与 S4.5、S3 开头说明并行调度、S4 两方分别展示、S5 开头加来源一句、约束清单加三条、摘要加 `reviewers[]` / `single_reviewer` / `agreement`、`review_method` 枚举加 `cross` 与 `agy-cli`、S6「接受修复方案」补「由宿主 Agent 在本 skill 之外修改」。判据一律链接到 Task 1 的章节，⛔ 不复述。
- [ ] 验证：`wc -l` ≤ 500；`health-lint.py --skills-dir skills` 0 blocker。Commit。

### Task 4: 周边文件

**Files:** Modify `references/independent-work.md`（两方同 brief、四列对照表）、`references/finding-verification-rubric.md`（`both` 来源口径一句 + 链接）、`templates/review-report.md`（对齐表 + 总裁决）、`README.md:136`（一句话说明）

- [ ] 改完 `git diff --check`。Commit。

### Task 5: 真跑验证

- [ ] 对本分支一个小 diff 并行跑一次 codex + agy 代码审查，按 `cross-validation.md` 做对齐，记录各来源条数。
- [ ] 用不存在的模型名让 agy 失败一次，确认按 § 一方失败得到单方结论。
- [ ] 未能验证的如实写进设计稿 § 7：额度耗尽、截断、询问交互（本会话无法对自己发起 `/adversarial-review`）。
- [ ] 设计稿状态改为「已实施」，修正 `--print-timeout` 写法。Commit。
