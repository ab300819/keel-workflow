# 输入满足协议(inline/stub)——DevDocs 轻量入口设计

- 日期:2026-07-22(R2 修订,终版)
- 状态:已定稿(codex 对抗审查 2 轮:R1 6 条全修复;R2 复现 3 + 新增 3 全部接受修复后,用户决定结束审查;无未处理 P1)
- 背景讨论:DevDocs"流程僵硬"诊断——僵硬的根因不是编号/追溯(用户明确保留),而是**skill 前置条件被实现为"具名上游产物文件必须物理存在"**,导致无法从链条中间轻量进入。

## 1. 问题定义

- 现状:`ms-dev-workflow` 前置要求 `04-dev-tasks.md` 存在,`ms-dev-tasks` 前置要求 `01/02/03` 三份文档存在——想执行一个任务必须把整条链的产物备齐,**无法从中间进入**(顺序耦合本质是数据依赖,不是控制依赖)。
- 现有逃生舱 `dev-flow` 是"彻底离开 DevDocs",零追溯——是悬崖不是旋钮。
- 目标:**保留追溯与 SSOT 不减一分**,新增一档"内联给一句任务定义/AC 即可进入"的轻量入口。

## 2. 核心机制(一句话)

> 前置条件的语义从"具名文件必须存在"松弛为"所需上下文可满足";用户通过显式 `--inline` 入口提供上下文时,**入口 skill 就地将其物化为产物文件中的最小 stub 条目**(真编号、标 provenance),下游按"显式受限分支"运行,缺口显式标记、绝不静默。

选型结论(brainstorm 收敛):**B 为骨**(输入契约思想)+ **A 为满足方式**(stub 物化);否掉集中 manifest(C)——devdocs-state 膨胀之战已证明单一大清单是本仓已知反模式,provenance 随条目分散记录。

修订要点:
- **R1**(F-001/F-002):AC stub 物化到 `01-requirements.md`(唯一编号源),`ms-verify --impl` 可读、`ms-requirements` 自然进增量模式,SSOT 不分裂。
- **R2**(F-007):调用形式定为显式参数 `--inline`,在现有批量指定符解析器最前面加分支,物化后复用现有 T-XX 执行路径;(F-001 复现):改动清单如实列出全部承载文件,撤回"ms-sync 完全不改"的过紧边界。

## 3. 改动清单(全部,R2 如实扩容)

| # | 文件 | 改动 |
|---|------|------|
| 1 | `skills/dev-workflow/references/inline-entry.md` | **新增**:私有协议 5 条 + stub 模板(§3.4)+ 回填协议(§3.5) |
| 2 | `skills/dev-workflow/SKILL.md` | 前置条件加"或 `--inline`"分支(+约 6 行);运行模式表加 `--inline` 一行 |
| 3 | `skills/dev-workflow/references/task-orchestration.md` | ① 指定符解析加 `--inline "<任务>" --ac "<标准>"` 分支(物化 → 转 T-XX 路径);② Test Agent 输入表加 inline 行:`02/03` 字段为 `—(inline)`,测试输入约束 = S1.5 Sprint Contract(AC + 当前代码) |
| 4 | `skills/sync/references/trace-mode.md` | +1 行规则:无 `03-test-cases.md` 且 AC 标 inline → 跳过 trace 写入并提示"inline 条目待回填" |

**共享层(`constraints.md`)零改动**(R1 F-006:该文件宪章"现状提取,不引入新规则";协议置于 dev-workflow 私有 reference,第二个消费者出现再上升)。

### 3.1 inline-entry.md 协议规则(5 条)

- `inline/satisfy-not-exist`:前置条件的语义是"所需上下文可满足";具名文件存在只是**默认**满足方式,不是唯一方式。
- `inline/explicit-entry`:inline 分支仅由显式参数触发:`/ms-dev-workflow --inline "<任务定义>" --ac "<验收标准>"`(R2 F-007:自由文本不进指定符解析,避免与 T/F/US 语法歧义)。
- `inline/materialize-two-files`:入口按 §3.4 模板物化**两处** stub:`01-requirements.md`(AC 条目,唯一编号源)+ `04-dev-tasks.md`(任务条目);文件不存在则以模板最小骨架创建。
- `inline/provenance-marker`:stub 条目必须标注 `来源: inline`;追溯矩阵照常引用该编号;`grep "来源: inline"` 即未回填台账。
- `inline/upstream-optional`:inline 条目允许上游链不完整(AC 无所属 US/F、无 02/03 文档),缺口显式标记为 `—(inline)`,不静默断链;受限行为见 §5。
- `inline/backfill-manual`:回填**仅手动执行**(本次不做任何 skill 的自动识别),协议见 §3.5;编号在回填中**不变**,操作是**移动而非复制**。

### 3.2 SKILL.md 前置条件(+约 6 行)

> - 任务文档:`docs/devdocs/04-dev-tasks.md`
> - **或** `--inline "<任务定义>" --ac "<验收标准>"`:按 [inline-entry.md](references/inline-entry.md) 物化 stub 后进入 S1;Test Agent 输入中 `02/03` 字段标 `—(inline)`,以 S1.5 Sprint Contract 为测试输入约束。

### 3.3 编号归属裁定

- **AC**:定义于 `01-requirements.md`(**唯一编号源**)。分配时扫描 01 全文件最大 AC 号续编;文件不存在从 AC-001 起。后续 `/ms-requirements` 因 01 已存在走增量模式,自然续编,无冲突。
- **T-XX**:按 `04-dev-tasks.md` 现行规则续编;文件不存在时从 T-01 起。
- **F/US**:内联入口不要求提供;stub 的关联需求列写 `—(inline)`,显式缺口,回填时补。

### 3.4 stub 模板(可复制;字段与现行模板对齐)

**`01-requirements.md`**——文件不存在时创建最小骨架;**已存在时追加到唯一追加区**(R2 F-008):

```markdown
---
generated_by: ms-dev-workflow(inline-entry)
spec_version: <requirements 当前 spec_version>
generated_at: <日期>
---
# 需求文档(inline 最小骨架)

> 本文件由 inline 入口创建,仅含内联 AC;F/US 与完整章节待回填(/ms-requirements)。

## 4. 验收标准

### Inline stubs(待回填)

#### AC-XX: <内联验收标准原文>
- 所属: —(inline)
- 来源: inline(<日期>)
```

> 已有 01 时:在 `## 4. 验收标准` 下创建(或复用)`### Inline stubs(待回填)` 小节并追加;回填只从该区移动;编号扫描覆盖全文件(含此区)。

**`04-dev-tasks.md`**——文件不存在时创建最小骨架(R2 F-003:frontmatter + 标题 + 层级分组齐全):

```markdown
---
generated_by: ms-dev-workflow(inline-entry)
spec_version: <dev-tasks 当前 spec_version>
generated_at: <日期>
---
# 开发任务

## 任务列表

### <N>. <按实际层级分组,如"核心逻辑 🔴">

#### T-XX: <任务名称>

| 属性 | 内容 |
|------|------|
| **描述** | <内联任务定义原文> |
| **状态** | 待开发 |
| **依赖** | 无 |
| **优先级** | P1 |
| **层级** | <按实际任务类别填 🔴/🟡/🟢/⚪(分类输入,如实填写)> |
| **review_profile** | guarded(inline 强制下限,禁 fast;命中 audit 信号升 audit) |
| **TDD 模式** | <随实际层级填写> |
| **关联需求** | —(inline), AC-XX |
| **涉及文件** | <入口 skill 探索代码后填写> |
| **来源** | inline(<日期>) |

**测试用例**(来自 `03-test-*.md`):—(inline,以 Sprint Contract 为准)
**测试方法**:由 S1.5 Sprint Contract 生成
**验收标准**:AC-XX
**Review 要点**:由 Test Agent 按 AC + 代码上下文生成
```

> **层级 ≠ 风险旋钮**(R2 F-009):层级是分类输入,UI 任务就填 🟢、基础设施就填 ⚪,如实分类;安全阀只有一个——`review_profile` 不得低于 guarded(inline 缺上游信息属现行"不确定场景"),audit 信号照常升档。guarded/audit 的 test-first 约束不变。

### 3.5 回填协议(仅手动;R2 F-004:撤"整体不落盘"原子性承诺,改为预检-写入-恢复)

回填 = 用户主动发起(如"把 T-XX 的 inline 需求正式化"):

- **预检(全部通过才开始写入)**:① 确定所属 F、US(选定或新建,编号续编);② 确认目标端无同 ID AC 定义,有则 ⛔ 停止;③ 记录将修改文件的原始片段。
- **写入**:① 将 inline AC 从 `### Inline stubs(待回填)` 区**移动**(非复制)到对应 US 下,编号不变;② 补 `01` 追溯矩阵行;如已有 `03-test-cases.md`,补对应矩阵行(无 03 则跳过并提示);③ `04` 任务条目 `—(inline)` 改为真实 F/US 引用,`来源` 改为 `inline(已回填 <日期>)`。
- **失败恢复**:任一写入失败,按记录的原始片段恢复已写文件,并报告恢复结果。
- **收尾校验**:联合扫描确认该 AC 在 `docs/devdocs/` 恰有一处定义。

## 4. 明确不做(YAGNI 边界)

- ❌ **不改 `constraints.md`**——第二个消费者出现再上升共享层。
- ❌ 不改 `ms-requirements`/`ms-verify` 及其余 skill(01 有 AC 后现行逻辑自然工作);`ms-sync` 仅 trace-mode.md +1 行 skip 规则(R2 修正:此前"完全不改"的边界与 §5 承诺矛盾,如实列出)。
- ❌ 不做输入契约 DSL / 字段声明表 / 集中 manifest(方案 C,已否)。
- ❌ 不做回填提醒、债务追踪、健康度新维度、自动回填识别——回填仅手动(§3.5),`grep "来源: inline"` 即台账。
- ❌ 不物化 `02-system-design.md` / `03-test-cases.md`——宁可显式受限(§5),不造假产物。
- ❌ 不新增 yaml-summary status、门控标记、frontmatter 字段。

## 5. 下游影响:显式受限分支

> R1 证伪了初稿"零波及"论断。立场:**能自然工作的靠 01 stub 满足;不能的显式受限并提示,绝不静默**。每一行为均有 §3 改动清单中的承载文件(R2 F-001 复现修复)。

| 消费者 | inline 分支下行为 | 承载 |
|--------|------------------|------|
| 指定符解析 | `--inline` 显式分支,物化后转 T-XX 路径 | 改动 #3① |
| `ms-verify --impl`(guarded 必跑) | **正常工作**:B1 从 01 读 AC,stub 条目可读 | 无需改动 |
| `ms-requirements`(后续正式化) | **正常工作**:01 已存在 → 增量模式续编 | 无需改动 |
| Test Agent(S2~S4) | **受限分支**:输入表 02/03 标 `—(inline)`,测试输入约束 = S1.5 Sprint Contract | 改动 #3② |
| `ms-sync --trace` | **受限**:无 03 且 AC 为 inline → skip + 提示待回填 | 改动 #4 |
| health-lint `dead-link` | **正常工作**:01 stub 的 AC heading 是规则已识别的定义位置模式 | 落地时实测(§6) |

## 6. 风险与验证

| 风险 | 处置 |
|------|------|
| health-lint dead-link 若不识别 stub 骨架中的 AC heading | 落地时以最小骨架实测扫描;不识别则调整 stub 条目为规则已支持的 heading/表格行格式 |
| 多个 inline stub 并存时编号竞态 | 分配规则统一为"扫描 01 全文件最大号续编",01 是唯一源,无竞态面 |
| inline 任务实际命中高风险(安全/资金) | guarded 是下限,audit 信号照常升档,不因 inline 而豁免 |
| spec_version 是否 bump | `dev-workflow` 前置条件与指定符解析属结构性变更 → 按 `realign/bump-required-structure` bump 并同步三处 |

## 7. 验收标准

1. 空 `docs/devdocs/` 下,`/ms-dev-workflow --inline "实现 X" --ac "Y"` 物化 01 最小骨架(AC-001,标 inline)+ 04 最小骨架(T-01,guarded,层级如实分类),进入 S1;Test Agent 输入 02/03 字段为 `—(inline)`,S1.5 正常产出 Sprint Contract。
2. 已有完整 DevDocs 的项目行为完全不变(无 `--inline` 时 inline 分支不触发;指定符解析原语法不受影响)。
3. 已有 01 的项目使用 `--inline`:AC 追加到 `### Inline stubs(待回填)` 区,编号全文件续编不冲突;后续 `/ms-requirements` 增量模式正常。
4. 手动回填按 §3.5 执行:预检全过才写入,AC 编号不变、恰一处定义,失败可按原始片段恢复。
5. `grep "来源: inline"` 可列出全部未回填条目。

## 8. 审查记录

| 轮次 | 健康分 | 结果 |
|------|--------|------|
| R1(codex CLI) | 28 | 6 条(P1×2)全确认全修复:AC 落 01、协议下沉、guarded 下限、手动回填、stub 模板、撤零波及论断 |
| R2(codex CLI) | 46.75(⚠️ 预警) | 复现 3(改动清单漏写承载文件)+ 新增 3(P1:`--inline` 入口参数、04 骨架、追加区锚点、层级误用、原子性措辞)全确认全修复;用户决定修复后结束审查,不跑 R3 |

遗留项:无未处理发现;R3 复审未执行(用户决策),实施后可用 `/adversarial-review` 对最终 diff 补一轮代码级审查。
