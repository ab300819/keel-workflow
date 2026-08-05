---
name: e2e-test-flow
description: 消费已有测试用例文档(md/html),对运行中的系统做 AI 驱动的黑盒 E2E 实测:用例分类 → 按分支变更影响排优先级(Spring/RPC 影响分析)→ curl 经代理打接口 + 浏览器 UI 自动化,全程只读观测数据库佐证,产出自包含 HTML 评审面板。Triggers on "/e2e-test-flow", "E2E 测试", "端到端测试", "接口测试", "UI 自动化", "用例执行", "黑盒测试", "跑用例". NOT for 设计测试用例(用 ms-test-cases)、执行项目自带测试套件(用 ms-test-run)、编写测试代码规范(用 testing-guide)、修 Bug(用 ms-bugfix / dev-flow)。
allowed-tools: Read, Write, Glob, Grep, Bash, Task, AskUserQuestion, TodoWrite, mcp__chrome-devtools__new_page, mcp__chrome-devtools__list_pages, mcp__chrome-devtools__select_page, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__click, mcp__chrome-devtools__fill, mcp__chrome-devtools__evaluate_script, mcp__chrome-devtools__list_network_requests, mcp__chrome-devtools__get_network_request, mcp__chrome-devtools__wait_for, mcp__chrome-devtools__handle_dialog, mcp__chrome-devtools__press_key
metadata:
  patterns: [orchestrator, tool-wrapper]
  interaction: multi-turn
  handoff: yaml-summary-v1
user-invocable: true
---

# E2E 测试工作流

对**运行中的真实系统**做 AI 驱动的**黑盒**端到端实测。输入已有用例文档(md/html),输出测试结论 + 自包含 HTML 评审面板。

**与 DevDocs 独立**:不读 `docs/prd/` `docs/devdocs/`,不写 F/US/AC 编号,不产追溯矩阵。用例编号沿用文档自身(如 `TC-J-001`)。产物落系统临时目录,**不入库**。

## Language

- 接受中英文提问,统一中文回复

## 首要原则

> **流程保持简单干净。任何不确定 —— 环境、连接方式、是否允许写、预期是否明确、用例该怎么测 —— 一律询问用户,而不是靠协议猜。**

本原则**优先于下面所有细则**。细则只描述常规路径;遇到边界情况,**问用户**就是正确答案。

## 触发条件

- 用户给出用例文档要求对运行中的系统实测
- 用户要求"跑一遍 E2E / 测一下这个分支影响的接口"
- 关键词:"E2E 测试"、"端到端测试"、"接口测试"、"UI 自动化"、"跑用例"

**不适合?** 设计用例 → `/ms-test-cases`;跑项目自带测试套件 → `/ms-test-run`;修 Bug → `/ms-bugfix` 或 `/dev-flow`

## 四条纪律

**D1 数据库只读** —— Agent 直连数据库只执行 `SELECT`,禁写。对被测系统的写操作走其自身 HTTP 接口(dev/test 环境)。连接时要求只读账号;拿不到就问用户。细则见 [references/execution-protocol.md](references/execution-protocol.md)。

**D2 预期结果 = 判定唯一权威** —— 判定只依据用例的 `预期结果`。不自造预期;预期不明确 → 标 `BLOCKED` 并**问用户**。未通过 = **疑似缺陷,交用户确认**,绝不放宽预期或改用例来凑全绿。

**D3 不改被测对象** —— 不为了测试而修改被测页面/代码。唯一例外是 `fault-injection` 必需的页面 hook,**必须留痕**。定位元素优先用页面既有锚点;**动态注入 aria 标签默认关闭**,真要用则 transient、**永不作断言依据**、必留痕。

**D4 白盒只用于排序,判定纯黑盒** —— 阶段③读代码,其结论**只用于提升优先级,永不用于缩小范围**。阶段④⑤只经外部接口驱动、只按用例预期判定,**禁止**用实现代码当"预期应该是什么"的来源。

落地:③与④⑤**由不同子 Agent 承担**(Task tool 派发),跨界只传**用例原文 + `{入口路径, 方法, 优先级}`**,代码/调用链/推理过程不过界。黑盒子 Agent 不给 idea MCP、不读被测源码,Bash 仅用于 curl。隔离强度取决于工具权限能否收窄;做不到就在报告标注"隔离为尽力而为",**不假装做到了**。影响分析细则见 [references/impact-analysis.md](references/impact-analysis.md)。

> 若工作区是 DevDocs 外壳布局（外壳仓根 `AGENTS.md` 含 `workspace_mode: shell`），源码在 `code_roots` 各子模块下而非仓库根。本 skill 与 DevDocs 独立，仅借该字段定位源码，不读 `docs/devdocs/`。代码根解析见 [_shared/workspace-mode.md](../_shared/workspace-mode.md)。

## 测试范围:只做功能,不做视觉

| 在范围内 | 出范围 |
|---|---|
| 跳转是否正确、内容是否变化 | 颜色、字体、间距 |
| 字段值、排序、数量限制 | 文本截断与省略号、hover 视觉态 |
| 接口调用与数据落库 | 布局溢出、像素比对 |
| 空态 / 失败态**是否出现** | — |

**文案内容**(按钮文本、金额格式)属功能正确性**在范围内**(snapshot 文本比对);**呈现样式**出范围。纯视觉用例标 `OUT-OF-SCOPE(视觉类)` 列入报告,**不静默跳过、不假装通过**。

## 流程

```
① 用例摄取      md/html → 结构化用例集          → references/case-ingestion.md
② 分类加工      每条用例定一个路由(下表)       → references/case-ingestion.md
⛔ 预估门        可执行性预估 + BLOCKED 分级 → **呈报用户**(占比>50% 须停下)
③ 影响分析      git diff → 受影响入口 → 优先级  → references/impact-analysis.md  [白盒子 Agent]
                    ↓ 只传 用例原文 + {路径,方法,优先级}
④⑤ 实测        按路由执行 + 只读 DB 观测       → references/execution-protocol.md [黑盒子 Agent]
⑥ 报告          自包含 HTML 面板(临时目录)    → references/panel-protocol.md
```

**开跑前一次性确认**(不搞门禁机器,就是问清楚并记下来):环境(dev/test,**不对生产跑**)、认证 cookie/curl 样例(整会话一份)、代理地址、DB 连接 + 只读账号、专属测试账号、是否允许写。**目标疑似生产 → 停下问用户。** 确认结果随报告产出。

## 用例路由(单一分类表)

阶段②给每条用例定**一个**路由。**一条用例只有一个路由,不叠加维度。**

| 路由 | 特征 | 执行方式 |
|------|------|---------|
| `api` | 后端数据驱动(统计口径、换算、排序、数量限制) | curl 经代理 + 只读 DB 观测 |
| `ui` | 前端功能行为(跳转、局部刷新、内容变化、文案) | 浏览器(chrome-devtools) |
| `ui+api` | 旅程类(点按钮 → 跳转 → 数据一致) | 浏览器为主,同时采网络记录 + DB 观测 |
| `fault-injection` | 异常态(接口失败 → 占位、超时 → Retry) | **三手段按序尝试**(见下),不得直接判 BLOCKED |
| `non-http` | `@Job` 等非 HTTP 入口 | 集成测试腿(见下) |
| `visual` | 纯视觉表现 | **不执行**,标 `OUT-OF-SCOPE` |
| `blocked` | 前置数据/环境不满足,或预期不明确 | 必附**解阻三元组 + 解阻成本分级**(见下) |

### fault-injection 三手段(⛔ 未逐个探测不得判 BLOCKED)

**禁用"mock"这个词来描述本流程。** 它会诱导出"我没有 mock 工具 → 测不了"的错误结论,而实际有三条可执行路径,**按序尝试**:

1. **非法参数触发系统真实错误分支** —— 最干净,**无注入**,优先
2. **`evaluate_script` 给 `fetch`/`XMLHttpRequest` 打补丁**返回构造的失败响应 —— **现成可用**(不依赖请求拦截能力),属注入故**必留痕**并写明补丁内容
3. **断网 / 超时模拟** —— 粒度粗,只适合"整体不可用"类场景

**三者逐个探测后都不适用**才判 `BLOCKED`,且报告**必须写明探测过哪些手段、为何不适用**。
> ⛔ 报告里出现"需 mock""无法 mock"这类表述 = 协议未被执行的信号。

**副作用预分类**(执行前从用例文本判断):`steps`/`title` 含支付/提交/确认/取消/删除/下单/修改等状态变更语义 → **写型**;语义不明 → **保守按写型**。判据细则见 [references/case-ingestion.md](references/case-ingestion.md)。

**写型用例三条规则(全流程无例外出口)**:
1. **只执行一次,一次取全证据** —— 首个外部动作(浏览器点击/curl/Job 触发)完成执行并同时采齐证据。**录制时那次动作就是唯一执行**,事后不得再用 curl 打一遍同一个写操作。
2. 转出的 curl **只作产物交付**给用户手工重放,工作流不自动重打。
3. **不自动重试、不自动重跑** —— 失败循环的重试/重跑仅适用非写型。写型任何再次执行**一律先问用户**。

> 铺前置数据若产生业务状态变更,同样适用本三条规则(与用例本身是否写型无关)。

## 集成测试腿(非 HTTP 入口)

`@Job` 等无法 curl 触发的入口:优先走**已部署且授权的手动触发入口**(属黑盒,最佳)→ 否则跑**项目已有集成测试**(可借 `/ms-test-run`)→ 缺失则最小新增触发,**新增测试代码必须先经用户批准**,不批准则 `BLOCKED` → 判断不了**问用户**。

**结论单独标注「本地集成验证」**,与部署环境黑盒结论**分区呈现不混列**(本地上下文不验证部署环境的调度配置、权限、依赖链)。

## 失败处理

```
用例 FAIL
 → 自查:① 环境/服务不可用 ② 前置数据不满足 ③ 偶发抖动(重试上限 1 次)
 → 可排除 → 修正后重跑
 → 不可排除 → 判「疑似缺陷」,冻结证据,上报待用户确认
```

- ⛔ **重试与重跑仅适用于非写型用例**(见上文写型三条规则)
- **连续多例同因失败** → 判环境性阻塞,**停下问用户**,不继续空跑
- **"直到全部通过"是目标不是强制结果**:真实缺陷一律如实判 FAIL 上报(D2)

## 判定状态

`PASS` / `FAIL` / `BLOCKED` / `OUT-OF-SCOPE`,每条附证据(响应片段 / SQL 观测 / 截图)。**证据中的凭据必须脱敏**,细则见 [references/execution-protocol.md](references/execution-protocol.md)。

### BLOCKED 不是终态:必附解阻三元组

⛔ **只写"环境不满足"是不合格的 BLOCKED。** 每条 BLOCKED 必须附:

| 字段 | 内容 | 反例(不合格) |
|------|------|--------------|
| `blocker` | 缺什么,具体到可操作 | ~~"需构造数据"~~ → "需含 EUR 币种订单的买家账号" |
| `unblock` | 谁做什么能解开 | ~~"待补测"~~ → "测试侧预置账号并授权可写" |
| `risk` | **这条挡住的是什么风险**(若此处真有 bug,后果是什么) | ~~留空~~ → "多币种换算错误会导致看板金额失真" |

**`risk` 回答的是用户最关心的问题**:BLOCKED 意味着**无法判断是否有 bug**(不得假装判断),但必须让用户知道**这条覆盖的风险有多大**,以决定值不值得投入解阻。

### BLOCKED 按解阻成本分级(不按阻断原因)

| 级 | 含义 | 用户可做 |
|---|------|---------|
| **A** | 用户当场能解 | 提供账号 / 权限 / 数据 / 授权 |
| **B** | 需环境改造 | 可写测试环境、故障注入能力、种子数据集 |
| **C** | **本流程永远测不到** | 明确告知**别指望本流程**,转人工验证或修用例(如需状态迁移历史、外部汇率源、跨天定时行为) |

**C 级是必须的诚实**:有些用例本 skill 根本不该承诺能测。按原因归类(需构造/写型/需 mock)对用户无用,一律改按本表分级。

## 开跑前可执行性预估(⛔ 硬门)

阶段②分类完成后、**任何实测动作之前**,先出一份预估并**呈报用户**:

```
可执行 N 条(api X / ui Y / ui+api Z / fault-injection W)
不执行  M 条(visual 出范围)
预计 BLOCKED K 条 —— A 级 a 条(你能解)/ B 级 b 条 / C 级 c 条
预计有效覆盖率 = N / 总数
```

**预计 BLOCKED 占比 > 50% → ⛔ 停下问用户**:"这样跑只能覆盖 X%,是先准备环境(A 级清单如下)还是就按当前覆盖率跑?"

理由:71% BLOCKED 这种结果**不该等跑完才让用户知道**。把发现时机从"事后"提前到"开跑前",用户才有机会先解阻再跑。

## 报告面板

自包含 HTML 面板 → 系统临时目录(**不入库**),附脱敏 curl 请求集。协议见 [references/panel-protocol.md](references/panel-protocol.md)。支持断点续跑(用例量可能很大)。

## 子 Agent 摘要格式(yaml-summary-v1)

```yaml
skill: e2e-test-flow
status: success | failed | partial | interrupted
summary:
  headline: "79 条用例:PASS 61 / FAIL 3(疑似缺陷)/ BLOCKED 8 / OUT-OF-SCOPE 7"
  details:
    environment: "test"
    cases_total: 79
    pass: 61
    fail: 3
    blocked: 8
    out_of_scope: 7
    impact_analysis: "12 个受影响入口(含 3 个跨服务不确定纳入)"
    isolation_level: "structural | best-effort"
blockers:
  - "FAIL TC-F-007: 多币种换算未按日终汇率(疑似缺陷,待用户确认)"
output_files:
  - "<临时目录>/e2e-report-<run_id>.html"
next_recommended:
  skill: ""
  args: ""
```

## 权威规格

设计定稿:[docs/superpowers/specs/2026-07-27-ai-e2e-test-flow-design.md](../../docs/superpowers/specs/2026-07-27-ai-e2e-test-flow-design.md)(codex 7 轮 R7 PASS)。**本文与规格冲突时以规格为准。**
