# CON-XXX 非编码类需求追溯 —— 实施记录与待办

> 2026-09-02。**已缩回。** 配对方案：[specs/2026-09-01-artifact-requirement-traceability-design.md](../superpowers/specs/2026-09-01-artifact-requirement-traceability-design.md)（该文记录的是**扩张版**，已被本文推翻，⛔ 不作为现役规格）。
>
> 现役规格：[_shared/constraints.md § CON 标识登记 / CON 的消费边界](../../skills/_shared/constraints.md)。

## 1. 最终落地（4 点）

| # | 内容 | 位置 |
|---|---|---|
| 1 | 01 §6 约束表**加编号** `CON-XXX`，让非编码类需求有个可被引用的对象 | `requirements` 模板 + SKILL |
| 2 | `dev-tasks` 追溯约束：`F+AC` **或** `CON`；非编码类任务不强制测试编号 | `dev-tasks/SKILL.md` |
| 3 | 非编码类任务走 `TDD 模式 = ⚪ 不适用`（**该字段本已存在**） | 同上 + task-template |
| 4 | **消费边界**：除两个 owner 外，其余 skill 不拥有 CON，⛔ 既不拦也不报 | `_shared/constraints.md` |

**什么是非编码类任务**：改配置 / 加资源 / 调元数据 / 改文案 / 删权限声明——没有可写测试的业务逻辑。上架合规、日志规约、安全基线、构建守卫属于这类。

## 2. 为什么从「一等公民」缩回

原方案要把 `CON` 注入全部消费方。经 **7 轮外部审查**，消费方计数 4 → 12 → 14 → 15 → 17 → **36 → 37**，每轮都发现**新形状**的消费方。R7 判定**不会稳定收敛**，依据：

- 同一执行事实分散在强制矩阵 / 主循环 / 子 Agent 协议 / 完成流程 / auto-mode / 模板 / `CLAUDE.md`，**没有单一执行 SSOT**。R6 专门修了主循环，R7 就从它下一层的 owner 协议找出阻塞
- 本仓**无 runner / 无 CI**，只有一次性人工走查，无法防止下次修改重新制造分歧
- 第 37 处是**新形状**（跨文档 owner/producer 协议断链），继续补同类关键词扫描找不到它
- 我自己的修复**造出过死锁**：Step 4 要 S1.5 契约 → 唯一生产者是 Test Agent → 我的分派又不启动 Test Agent

### 更根本的一条：我修错了问题

用户原话抱怨的是「**挂不上追溯**」（`dev-tasks` 那条门），不是「跑不了 TDD」。

而 `⚪ 基础设施` 任务在**CON 引入前**就已经是强制矩阵三档全 ■（`S2/S3` + `S4-S7`）。R4–R7 在执行层打的那一整场仗，修的是一个**本来就存在、且与原始诉求无关**的问题。

## 3. 明说的代价

`CON` **没有自动治理**。以下情况 ⛔ 不会被任何门发现：

- 某条 CON 没写验证方式
- 验证方式与守卫脚本已分叉
- CON 无对应任务（立了约束没人做）
- CON 被误当 F 归档掉（护栏消失）
- PRD 侧的 `NFR-XX` 映射永远停在 `active`

它保住的是**一件事**：配置类任务不编造 AC 就能挂上追溯。
`CON-XXX (01 §6) ← 关联需求 → T-XX (04) → 涉及文件 / commit`

**D4（同一事实多处定义的一致性扫描）未实现**，且缩回后连人工 lens 也不在 `ms-verify` 里了。用户给的 `.readWrite` vs `.addOnly` 场景没有任何检测。

## 4. 随本次落地的独立缺陷修复（与 CON 无关，自身成立）

| 缺陷 | 位置 |
|---|---|
| `health-lint` `id-reference-check` 把自称「不追踪 drift」的 state 表当编号上界（实测：表停 AC-062 而资源文件已 AC-064） | `pipeline/references/health-lint-implementation.md` |
| 编号扫描无规定方法 → 裸 `grep -o` 产幻影编号（`UT-001` 含 `T-001`）、字典序判 `T-9 > T-106` | `_shared/constraints.md` `id/scan-word-boundary` |
| ADR 推翻决策后无影响回扫，已完成任务卡留在旧世界 | `system-design/references/incremental-design.md` + `dev-tasks/templates/task-template.md` `superseded_by` |
| `needs review` 无归属 / 无关闭条件 / 无报龄 | `requirements/SKILL.md` + `sync/references/audit-mode.md` |
| `incremental-design.md` 检查清单两行重复 | 同文件 |
| `task-template.md` 外层围栏被内部裸围栏提前关闭 | 已改四反引号 |
| `test-cases` 模板 frontmatter 停在 `test.v1`（上次 bump 就漏同步） | 已修到 `test.v2` |

## 5. 待办

### 5.1 ~~既存缺陷：非编码类任务被强制走 TDD~~ —— 已修，不再是待办

原判「⚪ 基础设施任务被强制走 TDD」**措辞有误**：`TDD 模式 ⚪ 不适用` 的含义是**不先写测试**，不是**没有测试**（⚪ 任务卡照样有 `IT-001` 与「测试方法」）。

真正的矛盾只有一处，且很窄：**■\* 规则已明说 S4/S5 可退化，矩阵却把 `S4-S7` 并成一行全 ■**，不给它退化余地。

已修：拆成 `S4/S5`（■\*）与 `S6/S7`（■）两行 + 把 `TDD 模式` 明确为该 ■\* 条件的声明位。

- **S2/S3 保持 ■**（Test Agent 恒启动 → S1.5 契约存在 → Step 4 输入满足），⛔ 不重演之前的死锁
- **S6/S7 恒 ■** —— 无论哪种 TDD 模式，实现都不可跳过；合成一行会让「不先写测试」被读成「可以不实现」
- 改动面 **2 文件 / +15 -2**，⛔ 未触及主循环、子 Agent 协议、auto-mode、完成流程

### 5.2 未验证

- **端到端从未在真实项目上跑过。** 触发本次工作的项目不在本机，项目侧证据全部按用户现场报告采信
- 部署未做：源在 `~/Projects/skills/skills/`，运行态在 `~/.agents/skills/`，**两份拷贝非符号链接**

### 5.3 方案文档需要重写

`specs/2026-09-01-artifact-requirement-traceability-design.md` 记录的是扩张版（19 项改动清单、12 处消费方、执行层复用红绿）。它**已被本文推翻**，但仍留在 specs/ 下。要么重写为缩回版，要么在顶部加推翻声明。
