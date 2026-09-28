# ai-code 过程复盘：keel 暴露的问题与处置

调查日期：2026-09-28。对象：`~/Projects/Workspace/ai-code`（SIDM-71103，老系统技术栈升级，2026-09-06 ~ 09-27）。
仓库基线：`b443862`。来源：壳仓与两个 submodule 的 git 历史、`docs/devdocs/` 实际产物、563 个会话 jsonl、项目 memory。只读调查，未改 ai-code。

## 结论

时间主要花在写文档和订正文档上，搬代码的比重小：

| 指标 | 数值 |
|---|---|
| 壳仓 commit | 694，docs 占 93% |
| 自我订正类 commit | 166（24%）：计数错、状态过期、SHA/行号失效、因果判反、扫描漏扫 |
| 文档 : 代码 commit | 第一周 3.6 : 1 → 第三周 1.8 : 1 |
| `docs/devdocs/` | 114 个文件、6.7 MB；backlog.md 503 KB，04-dev-tasks-core.md 431 KB，00-context.md 232 KB |
| 用户「说人话」类要求 | 23~29 次；重申 M-001 范围至少 13 次 |

**主因是 skill 大多数时候不在上下文里。** 约 760 条用户消息，skill 实际载入 55 次；M-001 期间一个都没调，agent 另搭了派单台账、三门验收和 143 条纪律表，与 dev-workflow 已有内容重复（项目 memory `use-devdocs-workflow-not-reinvent.md` 自述）。dev-workflow 被载入的那几轮执行质量高：测试与实现分离、红验、外审失败如实记录。规格本身不是瓶颈；每轮都在上下文里的只有项目 AGENTS.md，而它长到 231 行，还带着过期的进度快照。

## 已处置

| 问题 | 处置 | commit |
|---|---|---|
| 门控标记被带进汇报与代码注释（文档里 3.4 万个，代码注释 emoji 清理两轮约 2.2 万行） | `constraints.md` 加 `gate/marker-scope`：标记只用于规格与门控输出，必须带文字标签；汇报、文档正文、代码注释不用装饰性 emoji | `7a845cc` |
| dev-workflow 允许往 AGENTS.md 写进度统计，与 agent-memory「进度放任务台账」冲突 | 改为只同步链接 | `10b45f4` |
| 行为规则只在 skill 载入时生效 | agent-memory 模板「工作流路由」节加四条常驻约束：执行走 dev-workflow、状态只看台账、范围外发现只登记一行、答复先说问题和影响 | `77ac15d` |
| health-lint 不认反引号与带装饰符的表格定义，ai-code 161 条 dead-link 里 136 条是误报 | 放宽 `DEF_TABLE`，加夹具；对照组 5 个项目计数不变 | `3fe948c` |

调查期间本地已并入的布局治理（`layout/size-cap`、`layout/unknown-path`、`layout/unregistered-split`、SessionStart hook）覆盖了原先的「体积护栏只看 state 文件」「中间调研产物无人管」两条，本文不再重复。

**存量项目不会自动获得新增的路由约束**：agent-memory 对已存在的「工作流路由」节保留原文不覆盖。ai-code 需要手动补这四行，或跑一次 `/agent-memory --restructure`；它的 AGENTS.md 还在用 `/ms-*` 旧名。

## 待第二个项目验证（未改规格）

按 ROI 判据，以下只在 ai-code 出现过，先记录，其他项目遇到同类问题再改。

1. **搬运型里程碑缺最小文档集。** 「复制加编译」的 M-001 走了需求、设计、用例、任务全套流程。M-001 没挂 F，成员无法按 `constraints.md` 的 F→M 推导，同一文件对 M-001 包含哪些 T 给了两个答案，分母在 12 / 24 / 33 个接口之间没定。绕法：在 `docs/workflows.md`「技术升级」一节说明，没有 F 的里程碑由任务卡的「归属里程碑」字段加一份范围清单决定成员。
2. **「当前状态」有 5 个载体。** AGENTS.md、00-context、`_dispatch.md`、三份 session-handover、tail-audit；分支名写错 9 天才订正。onboard 调用 7 次全是读取，00-context 被当成追加式日志，头部堆了 7 版快照。候选改法：00-context 只由 onboard 写且设上限；`--read` 做一次只读新鲜度核对（HEAD、分支）。
3. **dev-tasks 的拆分门槛与体积警报顺序未定。** 300 行即拆，远早于 96 KiB 的 size-cap；超阈值时先归档还是先拆没写明。
4. **backlog 条目不限长。** 151 条平均约 2.9K 字符；候选：note ≤200 字，证据只放链接，终态条目归档。
5. **pipeline 兜底问答没有「技术升级 / 重构」入口。** 对应指引只能经 `refactor/references/rewrite-flow.md` 的链接找到 workflows.md。
6. **多会话 / 团队协作没有约定。** 派单消息丢失、编号靠人工避让撞号。绕法：派单要求回执，编号预留落盘。
7. **子代理摘要协议执行率低。** yaml-summary 约 5/13 合规，握手字段 161 次委托用了 0 次，`.runlog.yaml` 从未写入。二选一：降级为推荐项，或编排层对不合规摘要按 `interrupted` 处理。

## 不归 keel 的部分

- 先下结论再核实，然后逐条提交订正，甚至订正上一次订正。
- 发现老代码缺陷就扩大范围，把「照搬、编译通过」做成「行为等价验证」。上面的常驻约束只能部分缓解。
- 多会话并行加频繁压缩（compact 边界 64 次），只能靠长文档传状态；这是项目特性（双子仓、多队友）。
- 项目 memory 里 5 条教训写下后同类问题仍复发，说明 memory 约束不住行为。这是把约束放进 AGENTS.md 的理由。
