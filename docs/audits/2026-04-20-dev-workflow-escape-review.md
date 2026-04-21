# Dev-Workflow 逃逸漏洞审查与加固计划

## Summary

已确认 `ms-dev-workflow` 的 spec 层存在多条可导致“漏做、错做、未验证也能过关”的逃逸路径，且多数不是实现细节，而是规范本身允许降级或缺少完备性校验。

最高风险结论：

- 非 🔴 任务默认可绕过对抗式验证，导致错做/漏做仅靠自检通过。
- UI/接口/基础设施层允许“有测试文件但无有效断言”进入提交流程。
- 单任务模式不做全量 `trace` 验证，回归和追溯缺口可直接逃逸。
- 🔴 任务仍暴露 `--skip-review` 旁路，等于给最高风险层开后门。
- 断点续做/历史检测有“按提交存在即跳过”的弱判定，可能把未真正完成的任务误判为已完成。

## 关键发现

1. **非核心层默认不做前置验证和对抗式验证，存在“错做后直接提交”逃逸**

   证据：
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:141) 将 `/ms-verify --impl`、`/ms-verify --ui` 绑定到 `--review`。
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:355) 规定 🟡/🟢/⚪ 默认不触发对抗式验证。

   风险：
   - 接口层、UI 层、基础设施层可以在仅完成“测试通过 + AC 自查”的情况下提交，缺少独立验证者，容易出现声称满足 AC 但实际漏做或做偏。

2. **S4 红色断言对 🟡/🟢/⚪ 非强制，允许“只有 skip/todo 骨架”的伪 TDD**

   证据：
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:242) 要求测试骨架使用 `skip/todo`。
   - [skills/dev-workflow/references/execution-flow.md](/Users/mason/Projects/skills/skills/dev-workflow/references/execution-flow.md:81) 规定 S4 对 🟡/🟢/⚪ 仅推荐或可选。
   - [skills/dev-workflow/references/execution-flow.md](/Users/mason/Projects/skills/skills/dev-workflow/references/execution-flow.md:172) 绿灯只要求“运行测试→确认通过”。

   风险：
   - 若测试仍是 `skip/todo`，S6 的“测试通过”不代表任何行为被验证，属于典型“没有验证登等情况”的逃逸。

3. **🟢 UI 层把关键校验移到清单和静态自查，运行态验证不形成强制闭环**

   证据：
   - [skills/dev-workflow/references/execution-flow.md](/Users/mason/Projects/skills/skills/dev-workflow/references/execution-flow.md:100) UI 任务必须产出清单，但明确“不影响 S5/S6 的红/绿闭环”。
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:330) UI 层可选 TDD。

   风险：
   - hover/disabled/error/loading 等状态可以只写在清单里，不必有可执行断言；若也未加 `--review`/`--ui`，则整条 UI 验证链可被绕过。

4. **单任务模式不做全量 `/ms-test-run --trace`，回归和追溯完整性可逃逸**

   证据：
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:428) 只要求批量模式完成后调用 `/ms-test-run --trace`。
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:429) 明确单任务模式不触发全量测试。

   风险：
   - 单任务只验证局部测试，无法保证全局回归和 trace 完整性；“本任务通过但破坏别处”会延后暴露。

5. **🔴 核心逻辑允许 `--skip-review`，直接破坏最高风险层的安全不变量**

   证据：
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:355) 明确 🔴 可用 `--skip-review`。

   风险：
   - 核心逻辑本应依赖对抗式验证兜底，但现在允许显式关闭，属于硬旁路。

6. **断点续做用“是否已有 code/docs commit”判定跳过，缺少完成性复核**

   证据：
   - [skills/dev-workflow/references/task-orchestration.md](/Users/mason/Projects/skills/skills/dev-workflow/references/task-orchestration.md:88) “有代码提交 + 有文档提交 → 跳过”。

   风险：
   - 只要存在带 `T-XX` 的历史提交，就可能被误判为完成；没有要求重新核对 AC、测试、trace、任务状态一致性。

7. **S8 AC 验证没有完备性协议，容易变成口头式“都满足了”**

   证据：
   - [skills/dev-workflow/SKILL.md](/Users/mason/Projects/skills/skills/dev-workflow/SKILL.md:338) 只写“AC 全部满足”。
   - 对比 [skills/verify/SKILL.md](/Users/mason/Projects/skills/skills/verify/SKILL.md:356)，`ms-verify` 明确要求完备性验证；`dev-workflow` 没把同等级要求内建进 S8。

   风险：
   - 编排器可在没有逐条 AC 证据的情况下进入提交，形成“漏做但未被显式发现”的漏洞。

## 修补方案

1. **把验证从“可选 review”改为“按层级最小必做”**

   - 🔴：保留强制对抗式验证，并移除 `--skip-review`。
   - 🟡：至少强制 `/ms-verify --impl`。
   - 🟢：至少强制 `/ms-verify --ui --impl` 或等价 UI 专项验证。
   - ⚪：至少强制 `/ms-verify --impl --trace` 或轻量实现验证。
   - `--review` 仅作为“增强审查”开关，不再决定是否有独立验证。

2. **禁止无有效断言进入绿灯**

   - 将 S4 从 🟡/🟢/⚪ 的推荐/可选提升为“若存在测试文件则必须转为可执行断言”。
   - 新增门禁：`skip/todo` 测试不可计入通过；提交前必须校验“新增测试中无残留 skip/todo，除非任务文档显式豁免并记录原因”。
   - 对 UI 任务新增门禁：清单项中的 Blocker 类状态必须映射到至少一种可执行验证或 `ms-verify --ui --live` 证据。

3. **把单任务模式补成闭环**

   - 单任务完成后默认执行受影响范围测试 + trace 校验。
   - 若项目没有可用 affected-test 机制，至少执行 `/ms-test-run --trace` 的轻量子集，而不是完全跳过。
   - 批量与单任务只允许在“验证范围”上不同，不允许在“是否做全局追溯检查”上不同。

4. **强化 S8 为“逐条 AC 完备性验证”**

   - 强制输出 AC 检查表：`AC 编号 / 证据类型 / 对应测试或代码位置 / 判定`。
   - 任一 AC 没有证据时禁止提交。
   - “声称 vs 实际 diff” 从 S9 的增强项前移为 S8 必做项，避免把遗漏实现拖到可选 review 阶段才发现。

5. **修正断点续做和历史跳过判定**

   - “有 code/docs commit 即跳过”改为“仅当任务状态=已完成 且 AC 表/测试/trace 均可复核时跳过”。
   - 若仅检测到历史提交但缺少验证证据，应进入“待复核续做”而不是直接跳过。
   - 续做信号表里增加 `verification_pending`、`trace_pending`、`docs_only_pending` 三类中断点。

6. **收紧探索模式和 UI 降级语义**

   - 探索模式允许跳过文档强制，但不得跳过“最小行为验证”。
   - UI 层可以弱化红灯，但不能弱化“状态覆盖证明”；必须声明每个状态是通过测试、live 验证还是显式豁免关闭。

## Test Plan

- 场景 1：🟡 任务只有 `todo/skip` 测试时，流程必须在提交前阻断。
- 场景 2：🟢 UI 任务只产出清单、不写状态断言时，流程必须要求补齐 `--ui` 证据或 live 验证。
- 场景 3：单任务开发破坏其他模块时，新增的单任务后置 trace/回归校验必须能拦截。
- 场景 4：历史上已有 `T-XX` 两个 commit，但 AC 证据不全时，续做检测必须进入复核，不得直接跳过。
- 场景 5：🔴 任务尝试 `--skip-review` 时，规范应判定为非法参数或硬阻塞。
- 场景 6：S8 AC 表中缺 1 条 AC 证据时，必须禁止 Commit 1。

## Assumptions

- 本次结论针对 **spec 审查边界**，不评估实际 agent 实现是否额外补了安全网。
- “逃逸漏洞”定义为：规范允许任务在缺少独立验证、缺少逐条证据、或缺少真实可执行断言的情况下继续到提交。
- 若下一步进入修订，建议优先改 3 个文件：`skills/dev-workflow/SKILL.md`、`references/execution-flow.md`、`references/task-orchestration.md`；`verification-flow.md` 主要做配套收紧。
