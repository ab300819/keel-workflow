---
title: DevDocs 重新定位 + dev-workflow 重构设计
date: 2026-06-08
status: draft
supersedes_direction: docs/superpowers/specs/2026-05-25-ms-dev-workflow-speed-optimization-design.md
codex_review: [T-131, T-132, T-133]
---

# DevDocs 重新定位 + dev-workflow 重构设计

## 0. 背景与动机

过去几周对 DevDocs / ms-dev-workflow 持续做"加法治理"(governance 6 原则、health-lint、scope=health、spec_version、FUTURE 三态、49→20 flag 收敛……)。结果是单个 🔴 核心任务的执行链极重:S1 读任务 → S1.5 Sprint Contract 协商 → S2/S3 骨架 → S4-S7 双 Agent 红绿重构 → S8 完成检查(AC 完备表 + AC×证据矩阵 + diff 交叉验证)→ S9 `/ms-verify --impl` + Phase 1~3 自审 + Phase 4 外部对抗审查(≤3 轮)→ S10 自描述 → S11 Commit 1 → Commit 2(`/ms-sync` + `/ms-compound`)。**一个 🔴 任务派发 7~10 次子 Agent + 双 commit,S9 串行链 120-270s。**

用户反馈:**开发比人还慢,根本吃不到大模型红利。** 2026-05-25 的速度优化 spec 只解决了根因的一半——它保留了"spec 即门禁"的主假设和 11 步骨架,只做局部并行/批量合并。本 spec 是父级方向,处理定位本身。

> Codex T-131 独立判决:"DevDocs 应从『前置完整契约 + 每步门禁』改成『LLM 上下文记忆 + 风险触发护栏』……2026-05-25 设计可作为局部优化材料,但不应作为最终方向。"

## 1. 定位:代码是事实源,文档是"为什么"层

> **代码是权威事实源(SSOT);文档是"为什么"层——解释当时的设计是什么、为什么这么设计、后来为什么变更,服务于事后理解、review 和交接。之所以叫"记忆"而非"spec",是因为大模型本来就不保证严格照 spec 开发,与其假装 spec 是契约去门控,不如承认代码才是事实、文档负责解释决策。**

### 1.1 两类仪式切分

当前系统把两类本质不同的"仪式"混为一谈。重新定位把它们分开:

| 类别 | 它在护什么 | 命运 |
|------|-----------|------|
| **文档符合性仪式** | 代码是否符合文档(AC×证据矩阵门、追溯同步门、Sprint Contract 前置协商、`@satisfies` 标注) | **砍/弱化**——拿文档门控代码是本末倒置 |
| **代码正确性仪式** | 代码本身对不对(测试红绿、测试不可变、信息屏障、行为型 AC 独立证据、外部对抗审查) | **保留甚至更重要**——代码既是 SSOT,它对不对是唯一底线;只能改触发条件,不能砍 |

**当前流程慢,慢在大量"文档符合性仪式",不在"代码正确性仪式"。** 提速的来源不是削弱重路径,而是**不再把不该走重路径的任务硬塞进重路径**。

### 1.2 追溯矩阵:从门控降为索引(保留)

追溯矩阵是 DevDocs 核心优势,**保留**,采用 layout.v2 外置 `traceability.yml`(不污染代码注释)。但角色从**门控**变为**索引/记忆导航层**:让人/LLM 能从任意代码反查"它满足哪条需求、对应哪个决策"。变的是它**不再是每任务提交前的阻塞门**,改为随开发增量维护、按需/惰性校验。

## 2. 质量地板(所有 review_profile 一律强制,不可协商)

无论风险高低,5 条不变量永远生效。它们都便宜、且全是"防作弊 / 防回归"性质——这是 fast 路既快又不掉质量的根本原因:

| # | 地板不变量 | 防的失败模式 |
|---|-----------|------------|
| 1 | 绿验 `skipped/todo=0` | 假绿、用 skip 蒙混 |
| 2 | 测试一旦写成并红验通过即冻结(实现不得改测试,疑似缺陷须确认) | 实现反向改测试自证 |
| 3 | 声称 vs 实际 diff 一致 | LLM 谎报做了什么 |
| 4 | 行为型 AC 至少 1 条独立行为证据(不能只靠实现代码自证;无则显式豁免) | LLM 自己宣布满足 |
| 5 | 受影响测试后置 `/ms-test-run --affected` | 改坏既有行为 |

> 这 5 条不需要双 Agent、不需要外部审查、不需要完整 AC 矩阵。审查与完整矩阵是"加在地板之上的高风险增强",不是地板本身。**review_profile 只改变独立审查的*时机*,绝不降低这 5 条地板。**(防新仪式规则 #6)

## 3. review_profile:三档 + 审查延后

引入 `review_profile`(命名避开 pipeline Harness 档位与 dev-workflow 层级标签),替代旧 `🔴🟡🟢⚪ 层级=固定流程强度`模型。**每个任务始终保留双 Agent 红绿(Test Agent 写红 / Impl Agent 写绿 + 信息屏障)**;变的是独立审查的时机。

| review_profile | 双 Agent 红绿 | 质量地板 | Phase 1~3 内审 | Phase 4 外审 | 提交状态 |
|---------|:---:|:---:|------|------|------|
| **fast**(默认) | ✓ | ✓ | 延后到批/sprint | 延后到批/sprint | 即提交 → `review_pending` |
| **guarded** | ✓ | ✓ + `/ms-verify --impl` | 风险触发则 inline,否则延后 | 延后到批/sprint | 即提交 → `review_pending` |
| **audit** | ✓ | ✓ | **inline fail-fast** | **inline fail-fast** | 审过才提交(≈ 今天 🔴 全套) |

> **关键区分(三类,不是两类)**:本 spec 的"延后"只作用于**独立对抗审查**(Phase 1~3 自审 + Phase 4 外审)。另有两类**始终 inline 阻塞、永不延后**:
> - **质量地板**(§2 五条)——所有档强制,inline。
> - **前置验证 `/ms-verify --impl`**(语义:AC↔实现一致)——属于"前置验证门"而非"独立审查",Blocker **inline 阻塞提交**。`fast` 仅靠地板(含行为证据 + affected),`guarded`/`audit` 额外 inline 跑 `/ms-verify --impl`。
>
> 因此"review_profile 只改独立审查的*时机*"成立且不矛盾:`/ms-verify --impl` 不是独立审查,它和地板一样永远 inline。

### 3.1 审查延后的设计依据

把"证据生成(每任务)"与"独立审查(批/sprint)"解耦。地板已把便宜、高频的失败模式(假绿、改测试、谎报、回归)挡在每任务里,所以延后到批量的审查 catch 的是**更高阶**的东西——设计连贯性、跨任务交互、测试没覆盖的微妙正确性。这正是单任务孤立审查看不到、而全局批量审查才看得清的,所以延后能让审查质量*更高*而非更低。

### 3.2 累积风险闸(防 T-01 缺陷被 T-05 继承)

缓解不是靠"最后审得更狠",而是**限制 pending 的传播半径**:

- 依赖链上游处于 `review_pending` 时,下游**只允许继续低风险叶子任务**;
- 一旦出现公共 API / schema / 核心域 / 迁移 / 权限 / 安全 / 跨模块契约,**进入下游前必须先审**;
- 硬阈值:`pending ≤ 3`、`pending 依赖深度 ≤ 1`、`sprint 关闭前 pending = 0`、超数量/年龄/依赖深度 → **强制 drain(集中跑延后审查),不静默升 audit**(执行语义见 §10)。

### 3.3 `review_pending`:新增任务级状态(不复用 EXT_PENDING)

延后审查的任务**立即提交代码**(保住小步快跑),但状态 ≠ "完成"。

- 新增任务级状态 `review_pending`(`implemented_pending_review`),配尾注 `Review-Batch-Id` / `Review-Due` / `Pending-Reason`。
- **严禁复用现有 `EXT_PENDING`**:后者语义是"Phase 4 主动跳过后的阻塞恢复态,所有放行路径阻塞"(verification-flow.md:421)。复用会让执行器与断点恢复状态机自相矛盾。
- batch/sprint 边界集中清 `review_pending`;批量审查是边界上的**强制门**,不是可选项。Step 1.5 增加"pending 年龄/数量/依赖深度"清理门禁。

## 4. 风险分类器

### 4.1 信号 → 档位(就近升档,从不静默降档)

| 升到 | 触发信号(任一命中) |
|------|---------------------|
| **audit** | 不可逆数据变更/schema 迁移;安全/认证/权限/密钥;PII/隐私/合规/审计日志/数据保留;钱/支付/计费;**外部不可逆副作用**(邮件/短信/webhook/队列/第三方 API 写入);共享核心 API 或被广泛 import 的模块;复杂算法(非平凡分支/状态机);线上事故热修;并发/事务边界;依赖/lockfile/运行时版本升级;CI/测试框架/质量门自身变更;生产配置/IaC/部署/特性开关/限流/缓存/重试/幂等/超时;序列化/DTO/协议兼容;高流量热路径/成本敏感路径;依赖链根节点(大量下游依赖) |
| **guarded** | 有分支的新行为;公开/对外接口;跨模块契约;行为边界不清的新测试 |
| **fast**(默认) | 配置(仅限非运行时·非安全·非部署);文案;样式;有覆盖的内部重构;文档;无下游叶子任务 |

**组合规则**:命中 ≥2 个 guarded 信号,或 diff 面积/导入面明显放大 → 自动升 audit。

### 4.2 治理三原则("质量不可丢"的程序保障)

1. **不确定默认 guarded**——歧义时绝不静默走 fast。
2. **可自由升档;降档必须带显式理由 + 记录**——防止为图快往下压。
3. **`🔴🟡🟢⚪` 层级标签降级为众多输入信号之一**——不再是流程开关。`ms-dev-tasks` 拆分时提议初始 review_profile,`dev-workflow` 执行时做一次廉价信号扫描复核。

## 5. 文档 = 记忆:四类卡片(现有产物的视图/字段,非新文件族)

| 卡片 | 它是"记忆"的哪部分 | 复用的现有 owner 产物 |
|------|------------------|----------------------|
| **Context Card** | 项目结构/命令/约束/风险/当前决策 | AGENTS.md `当前状态` + `ms-onboard`/`codebase-insight` + `design_context` |
| **Task Card** | 单任务:目标/影响文件/验收要点/风险档/要跑命令/证据槽(20-40 行) | `04-dev-tasks.md` 任务条目瘦身形态 |
| **Evidence Ledger** | 本次实际验证命令/结果/commit/截图/测试位置 | S8 AC 完备性表 + Phase 4 L2 audit yaml 的摘要/指针 |
| **ADR Decision Log** | 只存不可逆/跨任务/影响后续的决策,带过期·复查条件 | `system-design` ADR 章节 / `design-revision` |

`traceability.yml` = 串起 Task Card ↔ 代码 ↔ ADR Decision Log 的索引(§1.2)。

> **改名 2**:dev-workflow 子 Agent 已有 `decision_log` 字段(执行期决策)。本卡片是架构/产品决策记忆,定名 **ADR Decision Log** 以区分。

### 5.1 八条"防新仪式"硬规则

1. Card 不是新文件类型,只能是现有 owner 产物中的视图或字段。
2. 每个字段必须有消费者(Step 1.5 / review planner / ms-sync / ms-verify / 人工);无消费者不写。
3. **Evidence Ledger 永不替代 S8 AC 表**,只压缩展示;至少保留每条 AC 的证据指针(否则与 Step 1.5 证据复核冲突)。
4. ADR Decision Log 只收不可逆/跨任务/影响后续的决策;普通实现选择进 commit/任务摘要即可。
5. `traceability.yml` 只做代码/测试/文档追溯索引,不扩成通用知识图谱。
6. fast/guarded/audit 只改独立审查的*时机*,不得降低 5 条质量地板。
7. 卡片硬上限:Task Card 20-40 行;Context 只保留当前有效状态;超限改链接。
8. batch/sprint 边界集中清 `review_pending`,不允许长期堆积成新 backlog。

## 6. 与现有产物 / 既有方向的关系

- **2026-05-25 速度优化 spec**:降为"局部优化材料"。其 P1(S9 并行化)、P2(批量 Batch-Id trailer)仍可作为 audit 档内部提速手段复用,但不再是顶层方向。
- **WIP-dev-workflow-speed-optimization.md**:本 spec 落地后,该 handoff 文件的 Phase 2 范围被本设计取代,按其自带清理协议处理(删除 + cleanup commit)。
- **adr-only-revision rule**(e1a6f13):ADR Decision Log 与 system-design 正文的同步规则需对齐此 rule,避免"只追加 ADR 不更新当前设计"。

## 7. 非目标

- 不重做 F/US/AC/T/INS/BUG 编号体系。
- 不删除追溯矩阵(只改其角色)。
- 不削弱 audit 档(≈ 今天 🔴 全套,原样保留)。
- 不引入新文件族(四类卡片是现有产物的视图)。

## 8. writing-plans 前必修(动工前必须补死,Codex T-134 判定)

> **状态**:§8.1-5 已在 §10 决议闭合(Codex T-135 有条件通过)。§8.6-7 切到下一轮 **Plan B(记忆卡片层)**,不在本轮 Plan A 范围。

本 spec 是方向 spec,方向已闭合;但实现计划第一阶段必须先把以下执行语义写成明确落点,**之后才能拆实施任务、动 `ms-dev-workflow` runtime**:

1. **批/sprint 边界审查触发器**:由谁触发、入口命令是什么、落在哪个 skill(现状批量编排只有逐任务 `/ms-sync`+Commit 2+后置测试,**无 batch review drain**)。单任务无自然 batch 边界,需定义其 drain 入口避免长期 pending。
2. **`review_pending` 状态机闭合**:状态字段 + 尾注 schema(`Review-Batch-Id`/`Review-Due`/`Pending-Reason`)+ Step 1.5 检测 + 依赖解析如何对待上游 pending + `--all` 是否收集 + 何时从 `review_pending` 转 `已完成`。**不得做成第二个 `EXT_PENDING`**(后者永久阻塞 Commit 1,会与"允许先提交"打架)。
3. **post-commit blocker 恢复策略**:延后审查发现 Blocker 时(代码已落盘)→ fix-forward / revert / 重开任务 / 阻断 sprint close 的判定规则,以及如何限制下游继续(对接 §3.2 传播闸)。
4. **`Review-Due` 年龄参数**:默认值 + 超期动作(超期 → 升 inline audit 还是强制 drain)。
5. **风险分类器可执行判据**:`dev-workflow` 如何廉价扫出"被广泛 import 的模块""diff 面积/导入面明显放大"等信号。
6. **Evidence Ledger 最小可复核格式**:每条 AC 证据指针的最简形态(§5.1 规则 #3 的落地)。
7. **ADR Decision Log 与 system-design 正文同步规则**:对齐 adr-only-revision(e1a6f13),避免"只追加 ADR 不更新当前设计"。

## 9. Codex 复核轨迹

- **T-131**:方向判决——支持"前置契约+每步门禁 → LLM 记忆+风险触发护栏";提出 fast/guarded/audit profile + 风险触发 + 四类卡片雏形;警告最大风险=矫枉过正砍掉独立证据。
- **T-132**:审查延后判决——支持"条件延后,反对一刀切";audit 不延后;限制 pending 传播半径;`review_pending` 不得复用 `EXT_PENDING`。
- **T-133**:§3+§4 判决(有条件通过)——补全 audit 信号 + 组合规则;`profile`→`review_profile`、`Decision Log`→`ADR Decision Log` 改名;四类卡片必须是现有产物视图;Evidence Ledger 保留每条 AC 证据指针;8 条防新仪式硬规则。
- **T-134**:整合稿通审(有条件通过)——主线一致无致命矛盾,可进 writing-plans;修正 1 处内部歧义(§3 `/ms-verify --impl` 前置验证 vs 独立审查的三类区分),4 条执行落点列入 §8 writing-plans 前必修。
- **T-135**:§8 执行语义决议通审(有条件通过)——决议①-④ 闭合 §8.1-4;消 §3.2 与决议④措辞矛盾(统一为强制 drain);补 5 项细节(drain 失败矩阵 / headless 触发 / `Review-Due` 序列化格式 / `review_pending` 被覆盖规则 / §8.5 风险判据)+ 范围切分(Plan A 核心 / Plan B 记忆卡片)。全部纳入 §10。

## 10. 执行语义决议(§8.1-5 闭合,Plan A 范围)

### 10.1 batch/sprint review drain(§8.1)

- **入口**:`/ms-verify --review-drain`——收集所有 `review_pending` 任务,集中跑延后的 Phase 1~3 + Phase 4(复用现有 embedded-headless 通道)。落点 skill:`ms-verify`(新增 flag)+ `dev-workflow` 编排器在边界调用。
- **触发**:(a) 批量 `T-01~T-05` 跑完,编排器宣告 batch 完成**前自动 drain**;(b) sprint close 显式调用;(c) 传播闸跳闸(`pending>3` / 依赖深度`>1` / `Review-Due` 超期)→ **强制 drain**。
- **headless 触发者**(Codex T-135):headless 下 batch 完成前由 `dev-workflow` 编排器**自动调用 drain**;pending 超阈值 / `Review-Due` 到期 → **自动 drain 或 fail-fast,不得只"告警"等人**;drain 失败 → fail-fast 输出续做命令。

### 10.2 `review_pending` 状态机(§8.2)

- **新任务状态值** `review_pending`(与 待开发/进行中/已完成 并列;**独立于**续做信号 `INT_PENDING`/`EXT_PENDING`/`postcheck_pending`,**严禁复用 `EXT_PENDING`**)。
- **Commit 1 尾注**:`Review-Batch-Id: <id>`、`Review-Due: <值见 10.4>`、`Pending-Reason: deferred-fast | deferred-guarded`。
- **Step 1.5 新增分支 [F]**:`review_pending` 任务 = 非"完成",不得跳过,必须经 drain 才转 `已完成`。
- **依赖解析**:上游 `review_pending` 时,下游仅允许低风险叶子任务(§3.2);触及公共 API/schema/迁移/权限/安全/跨模块契约 → 进下游前强制先 drain。
- **`--all` 解析新规则**(现状收集"状态≠已完成",task-orchestration.md:24):dev 执行**跳过 `review_pending`**(不重跑),由 `--review-drain` 专门收集。
- **转移**:`review_pending` --(drain 无 Blocker)--> `已完成`;有 Blocker → §10.3。

### 10.3 post-commit blocker 恢复(§8.3)

- **默认 fix-forward**:开修复任务追加新 commit,**不 revert**(原子提交已落盘,保历史)。
- **revert** 仅限"已落盘代码主动有害且 fix-forward 无法快速处理",**罕见,须 AskUserQuestion 确认**。
- drain 发现的 Blocker 全部 fix-forward + 重新 drain 通过前,**阻断 sprint close**。
- **下游限制**:Blocker 在被依赖的上游节点 → §3.2 闸本应已挡住下游(只放低风险叶子);若漏网,标记下游依赖任务重审。
- **drain 失败矩阵**(Codex T-135):

  | 场景 | 任务状态 | 退出 | 报告字段 |
  |------|---------|:---:|---------|
  | 单任务 Blocker | 保持 `review_pending` + fix-forward 入队 | 非0 | `drain.blockers[]` |
  | 部分通过 | 过的转 `已完成`,未过保持 `review_pending` | 非0 | `drain.passed` / `drain.pending` |
  | T1/T2 全失败 | 保持 `review_pending`(EXT_UNRESOLVED) | 非0 | `drain.channel_failure` |
  | L2 yaml 无效 | 保持 `review_pending` | 非0 | `drain.invalid_evidence` |
  | 用户中断 | 已处理落定,余下保持 `review_pending` | 130 | `drain.interrupted_at` |
  | headless fail-fast | 保持 `review_pending` | 非0 | `drain.headless_halt` |

  共性:**任何非全通过 → 阻断 sprint close**。

### 10.4 `Review-Due` 序列化格式(§8.4)

- 取值二选一:(a) sprint 符号值 `sprint:<id>`;(b) 无 sprint 时 ISO 日期 `due:YYYY-MM-DD`(默认 = 落盘日 + N,N 默认 3 个工作会话)。
- **判超期**:有 sprint → sprint close 时;无 sprint → `当前日期 > due` **或** `pending 计数 > 3` 任一命中(与 §3.2 阈值一致:`≤ 3` 可接受,`> 3` 触发)。
- **超期动作**:强制 drain(§10.1),不静默升 audit。

### 10.5 `review_pending` 被新需求覆盖(Codex T-135)

- **禁止原地覆盖**。新需求触及同一 `review_pending` 任务 → 要么**先 drain**(转 `已完成` 或 fix-forward)再改,要么**创建依赖/替代任务并保留原 pending 审查链路**(原 `Review-Batch-Id` 不丢)。

### 10.6 风险分类器可执行判据(§8.5)

- **"被广泛 import 的模块"** = 反向依赖计数 ≥ 阈值(默认 5,`grep`/`rg` 统计 import/require 引用数)。
- **"diff 面积/导入面明显放大"** = 改动行数 > 阈值(默认 150)**或** 触及文件数 > 阈值(默认 5)。
- 评估时机:`ms-dev-tasks` 拆分时静态估算初始 `review_profile`;`dev-workflow` 执行时按实际 diff 廉价复核,可升档。

### 10.7 本轮范围切分

- **Plan A(本轮)**:§1~§4 核心执行模型 + §10.1~10.6 执行语义 + §5.1 防仪式规则中与 review_profile/状态机相关者。
- **Plan B(下一轮)**:§5 四类卡片视图落地 + §8.6 Evidence Ledger 最小格式 + §8.7 ADR 同步规则。

## 11. Plan B 执行语义决议(记忆卡片层;§8.6-7 闭合 + §5 视图落地)

> **状态**:brainstorm 三决议闭合(Evidence→trace.v1 字段 / ADR 透镜走 adr-only-revision / 四卡片零新文件纯视图)。本节为 Plan B 方向闭合,**实现计划前必修见 §11.4**。

### 11.0 总决议:四卡片 = 现有 owner 产物的渲染视图,零新文件族(§5 落地)

四类卡片不落地为任何新文件/新编号。每张卡片是对一个**既有 owner 产物**的视图(view)或字段(field)投影,渲染时机由消费者按需拼装,不持久化为独立产物。逐卡映射见下表(对齐 §5.1 八条硬规则):

| 卡片 | 落地形态 | owner 产物(权威) | 渲染者/消费者 | 防仪式锚点 |
|------|---------|-----------------|--------------|-----------|
| Context Card | **视图**:动态拼装,不落文件 | AGENTS.md `当前状态` + `ms-onboard`/`codebase-insight` 输出 + `design_context` | `ms-onboard --read` 拼装;dev-workflow 任务启动读 | §5.1#1,#7(只保留当前有效状态) |
| Task Card | **字段子集视图**:20-40 行 | `04-dev-tasks.md` 任务条目(权威) | dev-workflow Test/Impl Agent 输入 | §5.1#7(硬上限 20-40 行,超限改链接) |
| Evidence Ledger | **字段**:trace.v1 link 上的 `evidence`(§11.1) | `traceability.yml` link(指针) + S8 AC 表(权威完整源) | Step 1.5 [A] 证据复核 / `--review-drain` | §5.1#2,#3(永不替代 S8 表) |
| ADR Decision Log | **透镜**:既有 ADR 章节投影 + 同步规则(§11.2) | `02-system-design` ADR 章节 / `design/decisions/`(权威) | `ms-verify` / health-lint `adr-only-revision` / 人工 | §5.1#4(只收不可逆/跨任务决策) |

> 验收:任一卡片若需要"新建文件才能承载",即违反 §5.1#1,该卡片设计判失败回退。

### 11.1 Evidence Ledger 最小可复核格式(§8.6 闭合)→ trace.v1 `evidence` 字段

**决议**:Evidence Ledger 不是新 section,落为 `traceability.yml` 中 `kind: verifies` link 的**可选 `evidence` 字段**——把"本次实际验证的命令/结果/产物指针"压缩为索引,与既有 `tests:`(测试编号)互补:`tests` 记"哪些用例覆盖",`evidence` 记"非测试类证据 + 本轮实际跑出的结果指针"。

```yaml
links:
  - id: AC-001
    kind: verifies
    repo: trade-fund-impl
    path: tests/.../FundServiceTest.java
    symbol: FundServiceTest#rejectsEmptyPassword
    commit: 22cfb53f
    tests: [UT-001]                  # 既有:覆盖该 AC 的用例编号(覆盖关系,非本轮执行结果)
    evidence:                        # [新增,可选] Evidence Ledger 投影
      - ac_type: behavioral          # behavioral | visual | structural(对齐 S8 AC 类型)
        s8_evidence_type: "UT 断言"          # canonical:取 S8 矩阵证据类型枚举(见下)
        locator: "UT-001"            # 测试编号 / artifact 路径 / 命令输出指针 / 外部票据
        result: pass                 # pass | fail | n/a
        at_commit: 22cfb53f          # 产出该证据时的 commit
```

**最小必需字段**:`ac_type` + `s8_evidence_type` + `locator` + `result` + `at_commit`(五者缺一不可复核——`locator`/`result`/`at_commit` 共同证明"本轮实际跑出"而非仅覆盖关系)。

`s8_evidence_type` 取值为 S8 矩阵证据类型 canonical 枚举(**不自造**,与 [verification-flow.md 证据类型×AC类型分级矩阵](../../../skills/dev-workflow/references/verification-flow.md#ac-完备性s8-权威定义) 逐字一致):`UT 断言` / `IT 断言` / `E2E 断言` / `--ui --live 截图` / `--ui --live trace` / `UI 清单` / `实现代码` / `显式豁免（附原因）`。`locator` 是该证据的索引形态(测试编号 / artifact 路径 / CI run / 本地命令输出指针 / 外部票据),不改变 `s8_evidence_type` 的合法性判定。

**硬约束(§5.1#3 落地)**:
- `evidence` 字段是 S8 AC 完备性表的**压缩投影/指针**,**永不替代** S8 表本体;**每条 AC(行为型/视觉型/结构型三类均含)**至少保留一条 `evidence` 指针,合法性按 S8 矩阵判(行为型禁纯实现代码、视觉型需 live/断言等,同矩阵不另立);任一 AC 缺指针 → 与 Step 1.5 [A] 证据复核冲突 → 复核判 `verification_pending`。
- 每条 `evidence` 必须指向"本轮执行结果"之一:S8 表对应行 / 测试运行 artifact / CI run / 本地命令输出;仅 `tests: [UT-001]`(覆盖关系)不构成 evidence。
- 写入者:见 §11.4#2(唯一写入者归属待定),S8 通过后回填,dev-workflow Commit 2 触发同步。

### 11.2 ADR Decision Log 同步规则(§8.7 闭合)→ 透镜 + adr-only-revision

**决议**:ADR Decision Log 是既有 system-design ADR 章节(`02-system-design` §16 / layout.v2 `design/decisions/`)的**透镜投影**,不新建文件。同步规则**直接复用已实装的 health-lint `design/adr-only-revision`**(e1a6f13 → 现 [health-lint-implementation.md](../../../skills/pipeline/references/health-lint-implementation.md)),不另造规则:

- **同步保障**:ADR 章节有增量(新增/改 ADR)但正文相关章节无同期更新 → `adr-only-revision` 告警(⚠️),对应 system-design SKILL.md:336 硬约束。Plan B 不新增检测逻辑,仅声明 ADR Decision Log 的"同步"语义 = 该 rule。
- **§5 "带过期·复查条件"落地**:现有 ADR 模板(状态/背景/决策/替代方案/下游影响/关联)**新增可选字段 `复查条件`**——仅对"有时效假设的决策"(如"暂选 X 因当前 Y 限制")填写,记"何种信号下该 ADR 需重审"。无时效假设的决策(如选型)不填,避免 §5.1#4 仪式化。
- **收录边界(§5.1#4)**:只收不可逆/跨任务/影响后续的决策;普通实现选择进 commit/任务摘要,不进 ADR Decision Log。dev-workflow 子 Agent 的 `decision_log` 字段(执行期决策)与本透镜**不同源**(§5 改名 2 已区分),不互相回填。

### 11.3 范围与非目标(Plan B)

- **落地范围**:trace.v1 schema 增 `evidence` 可选字段 + ADR 模板增 `复查条件` 可选字段 + 文档声明四卡片视图映射;**不动 dev-workflow runtime 的执行流**(卡片是读侧视图,写侧仍走既有 S8/trace/ADR 产出路径)。
- **非目标**:不新增卡片持久化文件;不改 trace.v1 严格校验规则(`evidence` 走软校验);不把 Evidence Ledger 或 ADR Log 做成独立 skill;不动 §10 已闭合的 Plan A 执行语义。

### 11.4 writing-plans 前必修(Plan B 动工前补死)

实现计划拆任务前,以下落点必须确认(否则不动 trace schema / ADR 模板):

1. **trace.v1 `evidence` 字段的版本影响 + schema 摘要更新**:[layout-versioning-policy.md](../../../skills/pipeline/references/layout/layout-versioning-policy.md) 明确"traceability.yml schema 字段变化触发 traceability_version 升级评估",故**必须走升级评估**(可选字段是否构成 breaking 由该评估裁定,不预设"不 bump");无论是否 bump,都须**同步更新 layout-versioning-policy 的 trace.v1 schema 摘要**(当前摘要不含 evidence)。
2. **`evidence` 写入 API 契约打通**:现执行层声明 traceability.yml schema 严格、手动可编辑字段仅 `notes/confidence/tests`([code-decoupling-implementation.md](../../../skills/pipeline/references/layout/code-decoupling-implementation.md))——必须**把 `evidence` 加入可写字段白名单 + 明确 `generator` 枚举**,否则实现会被现有严格契约拦截或丢字段。
3. **`evidence` 唯一写入者归属**:`ms-sync --extract-trace` vs `ms-verify` 谁是唯一写入者,避免双写冲突(对齐 trace.v1 `generator` 字段枚举)。
4. **`evidence` 的 canonical 枚举/字段 schema 归属**:`s8_evidence_type` 枚举权威在 verification-flow S8 矩阵,trace.v1 schema 引用而非复制;`ac_type`/`result` 枚举归属(trace.v1 自有 vs 引用 S8)需定。
5. **`evidence` 最小字段 + 指针有效性由谁校验**:扩 health-lint 新 rule,还是复用 trace.v1 软校验(`tests` 编号存在性那条扩到 `locator`);若不扩,须明确**哪个现有 validator 负责**(不能无主)。
6. **ADR `复查条件` 字段是否触发 design.v1 模板 bump**:同 #1 升级评估判据。

### 11.5 Codex 复核轨迹(Plan B)

- 待补:本节(§11)起草后的 Codex 集中送审结论。
