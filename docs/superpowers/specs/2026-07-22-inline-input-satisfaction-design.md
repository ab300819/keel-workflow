# 输入满足协议(inline/stub)——DevDocs 轻量入口设计

- 日期:2026-07-22(R1 修订)
- 状态:待评审(已过 codex R1,6 条发现全部确认并修复)
- 背景讨论:DevDocs"流程僵硬"诊断——僵硬的根因不是编号/追溯(用户明确保留),而是**skill 前置条件被实现为"具名上游产物文件必须物理存在"**,导致无法从链条中间轻量进入。

## 1. 问题定义

- 现状:`ms-dev-workflow` 前置要求 `04-dev-tasks.md` 存在,`ms-dev-tasks` 前置要求 `01/02/03` 三份文档存在——想执行一个任务必须把整条链的产物备齐,**无法从中间进入**(顺序耦合本质是数据依赖,不是控制依赖)。
- 现有逃生舱 `dev-flow` 是"彻底离开 DevDocs",零追溯——是悬崖不是旋钮。
- 目标:**保留追溯与 SSOT 不减一分**,新增一档"内联给一句任务定义/AC 即可进入"的轻量入口。

## 2. 核心机制(一句话)

> 前置条件的语义从"具名文件必须存在"松弛为"所需上下文可满足";用户内联提供上下文时,**入口 skill 就地将其物化为产物文件中的最小 stub 条目**(真编号、标 provenance),下游按"显式受限分支"运行,缺口显式标记、绝不静默。

选型结论(brainstorm 收敛):**B 为骨**(输入契约思想)+ **A 为满足方式**(stub 物化);否掉集中 manifest(C)——devdocs-state 膨胀之战已证明单一大清单是本仓已知反模式,provenance 随条目分散记录。

**R1 修订要点**(codex F-001/F-002):AC stub 物化到 `01-requirements.md`(最小骨架)而非任务条目内——AC 编号唯一源回归 01,`ms-verify --impl` 可直接读取,后续 `/ms-requirements` 因 01 已存在自然进入**增量模式**续编,SSOT 不分裂。

## 3. 改动清单(全部)

### 3.1 新增 `skills/dev-workflow/references/inline-entry.md`(私有协议,共享层零改动)

> **不进 `constraints.md`**(codex F-006):该文件宪章为"现状提取,不引入新规则"且禁止私有规则上升共享层。inline 协议现阶段只有 dev-workflow 一个消费者,置于其私有 reference;出现第二个真实消费者时再按 constraints.md 流程上升。

协议规则(5 条):

- `inline/satisfy-not-exist`:前置条件的语义是"所需上下文可满足";具名文件存在只是**默认**满足方式,不是唯一方式。
- `inline/materialize-two-files`:用户内联提供任务定义 + 验收标准时,入口按 §3.4 模板物化**两处** stub:`01-requirements.md` 最小骨架(AC 条目,唯一编号源)+ `04-dev-tasks.md` 任务条目;文件不存在则以模板最小骨架创建。
- `inline/provenance-marker`:stub 条目必须标注 `来源: inline`;追溯矩阵照常引用该编号;`grep "来源: inline"` 即未回填台账。
- `inline/upstream-optional`:inline 条目允许上游链不完整(AC 无所属 US/F、无 02/03 文档),缺口显式标记为 `—(inline)`,不静默断链;受限行为见 §5。
- `inline/backfill-manual`:回填**仅手动执行**(本次不做任何 skill 的自动识别),最小事务见 §3.5;编号在回填中**不变**,操作是**移动而非复制**,写入前必须确认目标端无同 ID 定义。

### 3.2 `skills/dev-workflow/SKILL.md` 前置条件章节(+约 6 行)

从:

> - 任务文档:`docs/devdocs/04-dev-tasks.md`

改为(增加"或"分支):

> - 任务文档:`docs/devdocs/04-dev-tasks.md`
> - **或**用户内联提供任务定义(做什么 + 验收标准):按 [inline-entry.md](references/inline-entry.md) 物化 stub(`01-requirements.md` AC 条目 + `04-dev-tasks.md` 任务条目)后进入 S1;Test Agent 输入中 `02/03` 字段标 `—(inline)`,以 S1.5 Sprint Contract(AC + 当前代码上下文)为测试输入约束。

### 3.3 编号归属裁定(规格级决定,写死避免歧义)

- **AC**:定义于 `01-requirements.md` stub 条目(**唯一编号源**,codex F-002 修复)。分配时扫描 `01-requirements.md` 现有最大 AC 号续编;文件不存在从 AC-001 起。后续 `/ms-requirements` 因 01 已存在走增量模式,自然续编,无冲突。
- **T-XX**:按 `04-dev-tasks.md` 现行规则续编;文件不存在时从 T-01 起。
- **F/US**:内联入口不要求提供;stub 的关联需求列写 `—(inline)`,显式缺口,回填时补。

### 3.4 stub 模板(codex F-003/F-005 修复:字段全给、可复制)

**`01-requirements.md` 最小骨架**(文件不存在时创建;已存在则仅追加 AC 条目):

```markdown
---
generated_by: ms-dev-workflow(inline-entry)
spec_version: <requirements 当前 spec_version>
generated_at: <日期>
---
# 需求文档(inline 最小骨架)

> 本文件由 inline 入口创建,仅含内联 AC;F/US 与完整章节待回填(/ms-requirements)。

## 验收标准

#### AC-XX: <内联验收标准原文>
- 所属: —(inline)
- 来源: inline(<日期>)
```

**`04-dev-tasks.md` 任务条目**(字段与 task-template 对齐,默认值写死):

```markdown
#### T-XX: <任务名称>

| 属性 | 内容 |
|------|------|
| **描述** | <内联任务定义原文> |
| **状态** | 待开发 |
| **依赖** | 无 |
| **优先级** | P1 |
| **层级** | 🔴 核心逻辑(风险输入;inline 缺上游信息,不得自动降级) |
| **review_profile** | guarded(inline 强制下限,禁 fast) |
| **TDD 模式** | 🔴 完整 TDD |
| **关联需求** | —(inline), AC-XX |
| **涉及文件** | <入口 skill 探索代码后填写> |
| **来源** | inline(<日期>) |

**测试用例**(来自 `03-test-*.md`):—(inline,以 Sprint Contract 为准)
**测试方法**:由 S1.5 Sprint Contract 生成
**验收标准**:AC-XX
**Review 要点**:由 Test Agent 按 AC + 代码上下文生成
```

> `review_profile: guarded` 是**强制下限**(codex F-005):inline 缺上游设计/测试信息,属现行规则的"不确定场景",不得沿用 fast 默认;命中现有 audit 信号(安全/资金/数据迁移等)时升 audit。层级/TDD 模式/优先级可由入口 skill 依据任务内容调整,但只能升不能降。

### 3.5 回填最小事务(codex F-004 修复:仅手动,步骤写死)

回填 = 用户主动发起(如"把 T-XX 的 inline 需求正式化"),按以下事务执行,中途失败则整体不落盘:

1. 在 `01-requirements.md` 选定或创建所属 F、US(编号续编);
2. 将 inline AC 从"最小骨架/追加区"**移动**(非复制)到对应 US 下,**编号不变**;写入前确认目标端无同 ID 定义,否则 ⛔ 停止;
3. 补 `01` 追溯矩阵行;如已有 `03-test-cases.md`,补对应矩阵行(无 03 则跳过并提示);
4. `04-dev-tasks.md` 任务条目的 `—(inline)` 改为真实 F/US 引用,`来源: inline` 改为 `来源: inline(已回填 <日期>)`;
5. 联合扫描确认该 AC 在 `docs/devdocs/` 恰有一处定义。

## 4. 明确不做(YAGNI 边界)

- ❌ **不改 `constraints.md`**——协议置于 dev-workflow 私有 reference,第二个消费者出现再上升(codex F-006)。
- ❌ 不改其余 20 个 skill——试点仅 `ms-dev-workflow`;`ms-requirements`/`ms-sync`/`ms-verify` 均不改(01 有 AC 后它们的现行逻辑自然工作)。
- ❌ 不做输入契约 DSL / 字段声明表 / 集中 manifest(方案 C,已否)。
- ❌ 不做回填提醒、债务追踪、健康度新维度、自动回填识别——回填仅手动(§3.5),`grep "来源: inline"` 即台账。
- ❌ 不物化 `02-system-design.md` / `03-test-cases.md`——宁可显式受限(§5),不造假产物。
- ❌ 不新增 yaml-summary status、门控标记、frontmatter 字段。

## 5. 下游影响:显式受限分支(取代 R0 稿"零波及"论断)

> codex F-001 证伪了"零波及":空 `docs/devdocs/` 下多个消费者依赖 01/02/03。修复后的立场是——**能自然工作的靠 01 stub 满足;不能的显式受限并提示,绝不静默**。

| 消费者 | inline 分支下行为 | 依据 |
|--------|------------------|------|
| `ms-verify --impl`(S9 前置验证,guarded 必跑) | **正常工作**:B1 从 `01-requirements.md` 读 AC,stub 条目可读 | AC 唯一源在 01 |
| `ms-requirements`(后续正式化) | **正常工作**:01 已存在 → 增量模式,扫描含 inline AC 的最大编号续编 | §3.3 |
| Test Agent(S2~S4) | **受限分支**:输入表 `02/03` 字段标 `—(inline)`,测试输入约束以 S1.5 Sprint Contract(AC + 当前代码)为准——S1.5 本就存在,非新机制 | §3.2 |
| `ms-sync --trace` | **受限**:无 `03-test-cases.md` 矩阵时该 AC 无矩阵行可更新,skip 并提示"inline 条目待回填" | 现行 trace 流程读 03 |
| health-lint `dead-link` | **正常工作**:01 stub 是合法定义位置(heading 模式可识别);落地时验证,如有位置假设加一行例外 | §6 风险表 |

## 6. 风险与验证

| 风险 | 处置 |
|------|------|
| health-lint dead-link 若不识别 stub 骨架中的 AC heading | 落地时以最小骨架实测扫描;不识别则调整 stub 的 AC 条目为规则已支持的 heading/表格行格式 |
| 多个 inline stub 并存时编号竞态 | 分配规则统一为"扫描 01 最大号续编"(§3.3),01 是唯一源,无竞态面 |
| inline 任务实际命中高风险(安全/资金) | §3.4:guarded 是下限,audit 信号照常升档,不因 inline 而豁免 |
| spec_version 是否 bump | `dev-workflow` 前置条件属结构性变更 → 按 `realign/bump-required-structure` bump 并同步三处 |

## 7. 验收标准

1. 空 `docs/devdocs/` 下,`/ms-dev-workflow "实现 X,验收标准:Y"` 物化 01 最小骨架(AC-001,标 inline)+ 04 任务条目(T-01,guarded),进入 S1;Test Agent 输入 02/03 字段为 `—(inline)`,S1.5 正常产出 Sprint Contract。
2. 已有完整 DevDocs 的项目行为完全不变(默认满足方式优先,inline 分支不触发)。
3. inline 入口后运行 `/ms-requirements`,进入增量模式且新 AC 编号不与 inline AC 冲突。
4. 手动回填按 §3.5 事务执行后:AC 编号不变、恰一处定义、追溯矩阵引用无需改动。
5. `grep "来源: inline"` 可列出全部未回填条目。
