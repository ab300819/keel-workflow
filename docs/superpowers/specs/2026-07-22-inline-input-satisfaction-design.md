# 输入满足协议(inline/stub)——DevDocs 轻量入口设计

- 日期:2026-07-22
- 状态:待评审
- 背景讨论:DevDocs"流程僵硬"诊断——僵硬的根因不是编号/追溯(用户明确保留),而是**skill 前置条件被实现为"具名上游产物文件必须物理存在"**,导致无法从链条中间轻量进入。

## 1. 问题定义

- 现状:`ms-dev-workflow` 前置要求 `04-dev-tasks.md` 存在,`ms-dev-tasks` 前置要求 `01/02/03` 三份文档存在——想执行一个任务必须把整条链的产物备齐,**无法从中间进入**(顺序耦合本质是数据依赖,不是控制依赖)。
- 现有逃生舱 `dev-flow` 是"彻底离开 DevDocs",零追溯——是悬崖不是旋钮。
- 目标:**保留追溯与 SSOT 不减一分**,新增一档"内联给一句任务定义/AC 即可进入"的轻量入口。

## 2. 核心机制(一句话)

> 前置条件的语义从"具名文件必须存在"松弛为"所需上下文可满足";用户内联提供上下文时,**入口 skill 就地将其物化为产物文件中的最小 stub 条目**(真编号、标 provenance),下游一切照旧。

选型结论(brainstorm 收敛):**B 为骨**(输入契约思想)+ **A 为满足方式**(stub 物化);否掉集中 manifest(C)——devdocs-state 膨胀之战已证明单一大清单是本仓已知反模式,provenance 随条目分散记录。

## 3. 改动清单(全部)

### 3.1 `skills/_shared/constraints.md` 新增 §10「输入满足协议(inline/stub)」

约 5 条 rule,不新增 status、门控标记或概念:

- `input/satisfy-not-exist`:前置条件的语义是"所需上下文可满足";具名文件存在只是**默认**满足方式,不是唯一方式。
- `input/inline-materialize`:用户内联提供上游上下文(如任务定义 + 验收标准)时,入口 skill 就地将其物化为对应产物文件中的最小条目(stub),编号按现行续编规则分配。
- `input/provenance-marker`:stub 条目必须标注来源(表格列或行内标记 `source: inline`),与完整产物区分;追溯矩阵照常引用该编号。
- `input/upstream-optional`:inline 条目允许上游链不完整(如 AC 无所属 US/F),缺口显式标记为 `—(inline)`,不静默断链。
- `input/backfill`:回填 = 后续运行上游 skill 时识别 inline 标记并撑成完整条目,**编号不变**;回填是可选动作,不是债务门控,inline 标记本身即可 grep 的台账。

### 3.2 `skills/dev-workflow/SKILL.md` 前置条件章节(+约 5 行)

从:

> - 任务文档:`docs/devdocs/04-dev-tasks.md`

改为(增加"或"分支):

> - 任务文档:`docs/devdocs/04-dev-tasks.md`
> - **或**用户内联提供任务定义(做什么 + 验收标准):按 [输入满足协议](../_shared/constraints.md#10-输入满足协议inlinestub) 就地在 `04-dev-tasks.md` 追加 stub 条目(文件不存在则以最小骨架创建),然后正常走 S1~S11。

### 3.3 编号归属裁定(规格级决定,写死避免歧义)

- **T-XX**:按 `04-dev-tasks.md` 现行规则续编;文件不存在时从 T-01 起。
- **AC**:内联 AC 就地登记在该 stub 任务条目内,编号按现行全局续编规则分配,标 `source: inline`;其**临时 SSOT 位置 = 该任务条目**。回填时迁移至 `01-requirements.md`,编号不变,任务条目改回纯引用。
- **F/US**:内联入口不要求提供;stub 条目对应列写 `—(inline)`,显式缺口。

## 4. 明确不做(YAGNI 边界)

- ❌ 不改其余 20 个 skill 的前置条件——试点仅 `ms-dev-workflow`;其他入口等真实使用撞墙后再扩展。
- ❌ 不做输入契约 DSL / 字段声明表。
- ❌ 不做集中 manifest / 上下文清单(方案 C,已否)。
- ❌ 不做回填提醒、债务追踪、健康度新维度。
- ❌ 不改 `ms-requirements` 等上游 skill 的自动回填识别——本次回填按 §10 协议**手动执行**(编号不变即合规);自动识别等真实回填需求出现再加。
- ❌ 不新增 yaml-summary status、门控标记、frontmatter 字段。

## 5. 为什么零波及(闭环论证)

- `04-dev-tasks.md` 仍是任务 SSOT:sync / verify / health-lint / 断点续做读到的是合法(只是薄的)条目,无需任何适配。
- 追溯不断:内联 AC 拿到真编号并进追溯矩阵;上游缺口是**显式标记**而非静默断链。
- dev-flow 与本机制的分工不变:dev-flow = 完全不进追溯网;本机制 = 轻量进入追溯网。二者 NOT-for 边界无需改动。

## 6. 风险与验证

| 风险 | 处置 |
|------|------|
| health-lint dead-link 规则若假设 AC 只能定义于 `01-requirements.md`,inline AC 会误报 | 落地时检查该 rule 实现;如有位置假设,加一行"`source: inline` 条目视为合法编号定义点"例外 |
| stub 条目缺 Sprint Contract 所需上下文(S1.5 要 AC + 代码上下文) | 无需处置:S1.5 本就基于 AC 文本 + 当前代码生成契约,内联 AC 文本已满足输入 |
| spec_version 是否 bump | `dev-workflow` 前置条件属结构性变更 → 按 `realign/bump-required-structure` 评估;constraints.md 新增节按其自身版本规则处理 |

## 7. 验收标准

1. 空 `docs/devdocs/` 目录下,`/ms-dev-workflow "实现 X,验收标准:Y"` 可直接进入 S1,并在 `04-dev-tasks.md` 生成带 `source: inline` 的 T-01 stub 条目。
2. 已有 `04-dev-tasks.md` 的项目行为完全不变(默认满足方式优先)。
3. 手动回填(把 inline AC 迁入 `01-requirements.md`、任务条目改回纯引用)后,编号不变、追溯矩阵引用无需改动;上游 skill 自动识别不在本次范围。
4. `grep "source: inline"` 可列出全部未回填条目。
