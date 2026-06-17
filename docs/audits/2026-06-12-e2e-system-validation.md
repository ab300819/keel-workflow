# 完整体系实测报告（SSOT 批次 1-4 后）

> 2026-06-12 · 方法：双沙箱实测——DevDocs 全链路（/tmp/devdocs-e2e）+ dev-flow 对照（/tmp/devflow-e2e），由编排者按 skill spec 逐步执行并核对每道门控
> 范围：ms-requirements → ms-system-design → ms-test-cases → ms-dev-tasks → ms-dev-workflow（fast 档 T-01 全程）；dev-flow 五阶段三门控（含真实 fresh-context 子 Agent 审查）

## 一、DevDocs 链路实测（邀请码校验服务，T-01 fast 档）

| 环节 | 结果 | 证据 |
|------|------|------|
| 01-04 文档链（frontmatter req.v1/design.v1/test.v1/task.v1） | ✅ | F-001/US-001/AC-001~003/UT-001~004 链路完整 |
| S1.5 Sprint Contract | ✅ | 设计文档行为契约含校验位公式 → Test Agent 可独立推导断言值（"ABCDEFGV"），信息屏障前提成立 |
| S2/S3/S4 骨架+测试（注释纪律） | ✅ | 测试仅纯 AAA 占位注释，无来源记录式；骨架 `NotImplementedError("TODO(T-01)")` |
| S5 红验 | ✅ | 4 新测试全失败，无基线外失败；冻结哈希记录 |
| S6/S7 实现+绿验（命名/注释纪律） | ✅ | 4/4 通过，`skipped/todo=0`；命名避开 deny-list（`outcome` 而非 `result`）；唯一注释为校验位公式（复杂 what 白名单） |
| 测试冻结 diff 校验 | ✅ | sha256 比对一致（FREEZE-OK） |
| S8 AC 完备性 | ✅ | 3 条行为型 AC 各有独立 UT 断言证据，符合分级矩阵（行为型可由 UT 作唯一证据） |
| S11 Commit 1 trailers（fast 档） | ✅ | `Review-Batch-Id/Review-Due/Pending-Reason: deferred-fast` 按 _shared trailers 协议写入 |
| Commit 2 + trace | ✅ | 04 状态 → `review_pending`；traceability.yml（trace.v1）AC↔测试映射 |
| 受影响测试后置 | ✅ | pytest 4/4 |

**质量地板 5 条全部可执行且通过**；fast 档"独立审查延后 + review_pending"语义按规范落地，无规范缺口。

## 二、dev-flow 对照实测（slugify 工具）

| 门控 | 结果 | 证据 |
|------|------|------|
| Contract Gate | ✅ | execution-contract.yml（goal/in_scope/out_of_scope/expected_behavior×4/evidence_plan/stop_conditions）；headless 自动通过理由已记录 |
| Red-Green Gate | ✅ | 红验 4 失败 → 实现 → 绿验 4/4；冻结 sha256 一致 |
| Verify Gate 3a Evidence Check | ✅ | 绿验/冻结/契约行为逐条有测试证据 |
| Verify Gate 3b Fresh-Context Review | ✅ PASS | **真实 Task 子 Agent**（新上下文）逐条核对 4 项 expected_behavior↔测试、5 项 in_scope↔实现行号、out_of_scope 无侵入、运行 pytest 验证证据真实 |

## 三、实测发现与处置

| # | 发现 | 级别 | 处置 |
|---|------|------|------|
| 1 | 注释规范解释张力：实现时想写"规则源自系统设计 §5.1"——黑名单"来源记录式"应禁，但白名单"复杂 what + 出处"似乎允许 | 规范歧义 | **已修**：code-quality 白名单"出处"限定为外部稳定来源（论文/RFC/issue），项目内过程文档引用归 traceability |
| 2 | `__pycache__/*.pyc` 进入 dev-flow 沙箱 commit；fresh-context reviewer 判为 acceptable 而非契约外变更 | 门控漏洞（轻） | **已修**：dev-flow 约束清单加"提交前排除构建/缓存生成物；生成物入 diff 视为未解释变更" |
| 3 | 命名 deny-list 有真实约束力：实现中本能用 `result` 被规则拦下改 `outcome` | 正向验证 | 无需处置（规则生效证据） |
| 4 | Test Agent 独立推导断言值的前提是设计文档行为契约足够具体（含公式/错误码）——若设计文档只写"校验邀请码合法性"则信息屏障不可行 | 经验确认 | 无需处置（ms-system-design 行为契约表已强制此粒度） |

## 四、结论

批次 1-4 的 SSOT 治理未破坏任何执行语义：DevDocs fast 档全链路与 dev-flow 三门控均按规范可执行、门控真实拦截（红验/冻结/契约审查均非走过场）。实测暴露 2 个规范缺口并已修复（注释出处定义、生成物排除），1 个正向证据（deny-list 生效），1 个经验确认（行为契约粒度前提）。

沙箱产物：`/tmp/devdocs-e2e`（3 commits）、`/tmp/devflow-e2e`（2 commits），未纳入仓库。
