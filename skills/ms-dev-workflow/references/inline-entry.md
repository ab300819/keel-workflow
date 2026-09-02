# inline 轻量入口(--inline)

> **私有协议**:仅 `ms-dev-workflow` 消费。出现第二个真实消费者时,按 [constraints.md](../../_shared/constraints.md) 宪章流程上升共享层;在此之前其他 skill 不得直接引用本文为规范源。
> 设计来源:[specs/2026-07-22-inline-input-satisfaction-design.md](../../../docs/superpowers/specs/2026-07-22-inline-input-satisfaction-design.md)(codex 对抗审查 2 轮)。

## 协议规则

- `inline/satisfy-not-exist`:前置条件的语义是"所需上下文可满足";具名文件存在只是**默认**满足方式,不是唯一方式。
- `inline/explicit-entry`:inline 分支仅由显式参数触发:`/ms-dev-workflow --inline "<任务定义>" --ac "<验收标准>"`;自由文本不进指定符解析,避免与 T/F/US 语法歧义。缺 `--ac` 时 ⚠️ 必须确认
  恢复方式:用户补验收标准后继续物化;或确认转 `/dev-flow`(零追溯);无确认不写入。
- `inline/materialize-two-files`:入口物化**两处** stub:`01-requirements.md`(AC 条目,唯一编号源)+ `04-dev-tasks.md`(任务条目);文件不存在则按下方模板创建最小骨架。
- `inline/provenance-marker`:stub 条目必须标注 `来源: inline`;追溯矩阵照常引用该编号;`grep "来源: inline" docs/devdocs/` 即未回填台账。
- `inline/upstream-optional`:inline 条目允许上游链不完整(AC 无所属 US/F、无 02/03 文档),缺口显式标记 `—(inline)`,不静默断链;下游受限行为见文末速查表。
- `inline/backfill-manual`:回填**仅手动执行**(不做任何 skill 的自动识别);编号在回填中**不变**,操作是**移动而非复制**。

## 编号分配

- **AC**:扫描 `01-requirements.md` **全文件**(含 Inline stubs 区)最大 AC 号续编;文件不存在从 AC-001 起。01 是 AC 唯一编号源。
- **T**:按 `04-dev-tasks.md` 现行规则续编;文件不存在从 T-01 起。
- **F/US**:不要求提供;关联需求列写 `—(inline)`,回填时补。

## stub 模板

### `01-requirements.md`

文件不存在时创建最小骨架;**已存在时**在 `## 4. 验收标准` 下创建(或复用)`### Inline stubs(待回填)` 小节并追加,不动其他章节:

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

### `04-dev-tasks.md`

文件不存在时创建最小骨架(frontmatter + 标题 + 层级分组齐全):

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

> **层级 ≠ 风险旋钮**:层级是分类输入,UI 任务就填 🟢、基础设施就填 ⚪,如实分类;安全阀只有一个——`review_profile` 不得低于 guarded(inline 缺上游信息属现行"不确定场景"),audit 信号照常升档。guarded/audit 的 test-first 约束不变。

## 回填协议(仅手动;预检-写入-恢复)

回填 = 用户主动发起(如"把 T-XX 的 inline 需求正式化"):

1. **预检(全部通过才开始写入)**:
   - 确定所属 F、US(选定或新建,编号续编);
   - 确认目标端无同 ID AC 定义,有则 ⛔ 禁止继续
     恢复方式:人工裁定重复 ID 归属(保留一处定义),再重跑预检;
   - 记录将修改文件的原始片段(用于失败恢复)。
2. **写入**:
   - 将 inline AC 从 `### Inline stubs(待回填)` 区**移动**(非复制)到对应 US 下,编号不变;
   - 补 `01` 追溯矩阵行;如已有 `03-test-cases.md`,补对应矩阵行(无 03 则跳过并提示);
   - `04` 任务条目 `—(inline)` 改为真实 F/US 引用,`来源` 改为 `inline(已回填 <日期>)`。
3. **失败恢复**:任一写入失败,按记录的原始片段恢复已写文件,并报告恢复结果。
4. **收尾校验**:联合扫描确认该 AC 在 `docs/devdocs/` 恰有一处定义。

## 下游受限分支速查

| 消费者 | inline 分支下行为 | 承载 |
|--------|------------------|------|
| 指定符解析 | `--inline` 显式分支,物化后转 T-XX 单任务路径 | [task-orchestration.md §1](task-orchestration.md) |
| `ms-verify --impl`(guarded 必跑) | **正常工作**:B1 从 01 读 AC,stub 条目可读 | 无需改动 |
| `ms-requirements`(后续正式化) | **正常工作**:01 已存在 → 增量模式,全文件扫号续编 | 无需改动 |
| Test Agent(S2~S4) | **受限分支**:输入表 02/03 字段传 `—(inline)`,测试输入约束 = S1.5 Sprint Contract(AC + 当前代码) | [task-orchestration.md 子 Agent 协议](task-orchestration.md) |
| `ms-sync --trace` | **受限**:无 03 且 AC 标 inline → 跳过 trace 写入并提示待回填 | [trace-mode.md](../../ms-sync/references/trace-mode.md) |
| health-lint `dead-link` | **正常工作**:01 stub 的 AC heading 是规则已识别的定义位置模式(落地实测项) | — |
