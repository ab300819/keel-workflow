# dev-workflow 注释质量治理方案

> 2026-06-12 · 状态：已对齐（Claude 调研方案 ⇄ Codex 独立方案，2 轮收敛，修订点 5/5 AGREE）
> 范围：代码注释质量。追溯标注外置（layout.v2 traceability.yml）已解决不重复设计；code-self-describe 文件头（INPUT/OUTPUT/POS）为独立机制不在本方案范围。

## 1. 问题与根因

**症状**：dev-workflow 驱动 LLM 开发时产出大量"变更日志式"注释（记录本轮改了什么、按哪个 AC 改、修复了什么），有时注释比代码多；多轮修复循环后注释持续堆积。

**根因（三处叠加的规则真空）**：

| # | 位置 | 问题 |
|---|------|------|
| 1 | `skills/code-quality/SKILL.md` | 全文无任何注释规则；S6"遵循 /code-quality"因此管不到注释 |
| 2 | `verification-flow.md` Phase 1 审查清单 | MTE + 安全维度，无注释维度，坏注释永远不被审出 |
| 3 | `skeleton-examples.md` | 示例本身示范"来源记录式"注释（`// Arrange — 输入来自 UT-001`、`// 后置条件：id 非空`），被 agent 模仿成风格 |

加上 LLM 固有失败模式：实证研究（arXiv 2605.13280）显示人类代码缺注释为主（60:3），LLM 代码冗余注释为主（10:24）——规范须以**负面清单 + 数量抑制**为主，而非鼓励写注释。

## 2. 调研结论（规则依据）

经典共识（Ousterhout《A Philosophy of Software Design》ch.12-13、McConnell《Code Complete》ch.32、Martin《Clean Code》ch.4、Google eng-practices、Stack Overflow blog 2021）：

- **注释唯一合法用途是承载代码无法表达的信息**（why、契约、约束、警示）
- 一致禁止：重复代码语义、变更日志（Journal Comments）、署名/任务编号（Attributions）、注释掉的代码
- 分歧裁决：采 **Ousterhout 框架为主体**（注释按接口/实现/why 分类，捕获设计者头脑中写不进代码的信息）+ **Clean Code 坏注释黑名单**做硬性禁止

**框架原则——信息归宿三分法**（置于 SSOT 章节首句）：

> 源码注释 = 面向未来读者的稳定事实；commit message = 本轮变更说明；traceability/任务文档 = 过程追溯。变更日志注释的根因是把 commit 内容错放进源码。

## 3. 规则集（SSOT，落 code-quality）

### 白名单：注释必须落入以下类别之一

| 类别 | 判定条件 |
|------|----------|
| 公共契约 | exported API 上方；说明调用契约/错误/边界/不变量；不复述函数名和类型 |
| 非显然 why | 外部协议、兼容性、性能、并发、安全、算法取舍；删掉后读者无法判断"为什么这样写" |
| 不变量/风险约束 | 紧邻校验或状态转换；类型系统与测试名无法表达的业务约束 |
| 复杂 what + 出处 | 复杂算法/正则/反惯用绕坑写法的解释性注释，说明"不这样写会踩什么坑"，可附稳定出处链接 |
| 抑制类 | `eslint-disable`/`ts-ignore` 等必须附具体原因 |
| 临时骨架脚手架 | 仅限 S2/S3：TODO、`test.skip/todo`、纯 AAA 占位（`// Arrange`，不带来源）；S4/S6/S7 后必须清除 |
| 文件头自描述 | code-self-describe 管理，本规则不替代 |

### 黑名单：当前 diff 新增/修改命中即 Blocker

| 类别 | 判定条件 |
|------|----------|
| 变更日志式 | 注释描述的是**本轮变更过程**而非代码当前状态（关键词"本次/新增/修改/修复/已按要求"仅作信号，按语义判定——`// 新增用户走邀请码通道` 描述业务规则，合法） |
| 对审查者说话 | "此处已修复/按要求处理/无需再改"等面向 reviewer/agent 的话 |
| 来源记录式 | 注释记录"来自 UT/AC/后置条件/行为契约"等过程来源（layout.v1 legacy retained 除外） |
| 注释式追溯 | layout.v2 新增 `@satisfies/@verifies/@testcase/@requirement` |
| 复述代码 | 只是翻译下一行代码（`// 校验邮箱` + `validateEmail(email)`） |
| 陈旧脚手架 | S4/S6/S7 后仍保留 `TODO: 实现测试`、`Not implemented` 等骨架占位注释 |
| 注释掉的代码 | 整段旧实现注释保留且无外部 issue/迁移理由 |
| 过量注释 | 同函数连续注释 >3 行，或 changed hunk 注释行 > 可执行代码行，且不属白名单 |

### 分级

- **Blocker**：当前 diff 新增/修改黑名单注释；抑制类无理由；S4/S6/S7 后残留脚手架；**注释与代码当前语义不符**（过期注释比没注释更糟——改代码必须同步更新受影响注释）
- **Suggestion**：旧代码存量坏注释（本次未触碰）；public API 缺契约注释（不因"没写注释"本身阻断，仅当缺失已造成安全/兼容/行为歧义时按对应风险升级）

## 4. 挂载点（双防线，不升质量地板）

**SSOT**：`skills/code-quality/SKILL.md` 新增「注释规范」章节（≤35 行，当前 461 行 < 500 硬约束）。理由：S6 与 S9 Phase 1 已引用 /code-quality；注释是代码可维护性的一部分，非 dev-workflow 私有协议；不进 `_shared/constraints.md`（非跨 skill 协议）。

**防线 1 — 生成时约束（主防线）**：fast/guarded 档 Phase 1 延后到 review-drain，坏注释若只靠 S9 兜底，已进 Commit 1。故 Test/Impl Agent prompt 须内置约束：
- Test Agent 协议：S3 可用纯 AAA 占位；S4 写完断言后删除来源记录式注释
- Impl Agent 协议：实现与修复循环中不得添加解释本轮修改的注释；必要注释只写 durable why；**该协议同样适用于 review-drain 产生的 fix-forward 修复**（Codex 对齐补强）

**防线 2 — S9 Phase 1 审查兜底**：审查清单加「注释卫生」维度；Blocker 判定表加"当前 diff 新增黑名单注释"。

## 5. 存量示例治理（skeleton-examples.md）

原则：代码块只展示希望 agent 模仿的最终风格；流程说明移到 prose。

| 现状 | 处理 |
|------|------|
| `test.skip` / `it.todo`、`throw new Error('Not implemented: T-XX')` | 保留（骨架占位，S6 必须移除） |
| 空测试体纯 AAA 占位 | 保留，仅限 `// Arrange` / `// Act` / `// Assert`，不带来源 |
| `// Arrange — 输入来自 UT-001`、`// Act & Assert — 断言来自错误契约...` | 改纯 AAA 或删除 |
| `expect(...); // 后置条件：id 非空` | 删除（测试名+断言已表达） |
| `// Impl Agent 在此填充...`、`// 业务逻辑...由测试断言驱动`、`// layout.v2：不写 @satisfies...` | 删除或移到代码块外 prose |
| "测试骨架必须包含 AAA 结构注释提示"（约束清单） | 改为"S3 可含纯 AAA 占位；S4 后不得保留来源记录式注释" |

## 6. 落地改动清单（5 文件，无新增流程/文件）

1. `skills/code-quality/SKILL.md` — 新增「注释规范」SSOT 章节（三分法置顶 + 白/黑名单 + 分级，≤35 行）
2. `skills/dev-workflow/SKILL.md` — S6/S4 处加 1-2 行指针引用 /code-quality 注释规范
3. `skills/dev-workflow/references/task-orchestration.md` — Test/Impl Agent 协议加生成时约束，显式覆盖 review-drain fix-forward
4. `skills/dev-workflow/references/verification-flow.md` — Phase 1 清单加「注释卫生」维度 + Blocker 判定项
5. `skills/dev-workflow/references/skeleton-examples.md` — 按 §5 清理示例

## 7. 对齐记录

- R1：Claude 调研（7 来源）+ Codex 独立方案（读仓出方案），结构性结论一致：code-quality SSOT、双防线、不升质量地板、清理 skeleton 示例
- R2：Claude 基于调研提 5 修订点（三分法置顶 / 白名单补复杂 what / 契约注释降 Suggestion / 注释同步维护规则 / 黑名单语义判定收紧），Codex 5/5 AGREE；Codex 补强 review-drain fix-forward 覆盖

## 引用

- Ousterhout, *A Philosophy of Software Design* ch.12-13
- Martin, *Clean Code* ch.4 (Journal Comments / Attributions / Noise)
- McConnell, *Code Complete 2nd ed.* ch.32
- [Google eng-practices: Looking for — Comments](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- [Stack Overflow Blog: Best practices for writing code comments (Spertus, 2021)](https://stackoverflow.blog/2021/12/23/best-practices-for-writing-code-comments/)
- [The Readability Spectrum: LLM-Generated Code (arXiv 2605.13280)](https://arxiv.org/html/2605.13280v1)
