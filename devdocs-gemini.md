# DevDocs 流程审查与优化建议

通过深入审查 `devdocs` 系列 Skills 定义文件及 `devdocs-advise.md`，对当前开发流程进行了全面分析。

当前流程是一套**高度自律、质量优先**的工程化体系，深受 MTE (Maintainability, Testability, Extensibility) 和 TAR (Testable, Acceptable, Reviewable) 原则驱动。但在个人开发者（Solo Developer）场景下，确实存在**流程过重**和**上下文负载过高**的问题。

以下是详细的审查报告与优化建议：

## 1. 现状分析：优点与代价

### ✅ 核心优势
*   **极致追溯性**：从 `F-XXX` (功能) 到 `US` (故事) 到 `AC` (验收) 再到 `UT/IT` (测试) 和 `T-XX` (任务)，形成了完整的证据链。代码变更均有据可查。
*   **分层 TDD 策略**：`devdocs-dev-tasks` 明确了 Core (强制 TDD)、API (推荐)、UI (可选) 的分层策略，非常务实。
*   **增量设计支持**：`devdocs-system-design` 内置了增量设计模式，符合长期维护需求。
*   **闭环反馈**：`devdocs-insights` 将外部输入转化为需求，`devdocs-sync` 保持文档与代码同步，形成了闭环。

### ⚠️ 存在的问题 (Pain Points)
1.  **"重型"流程与"轻量"需求的矛盾**：
    *   无论功能大小，都要经历 4 个阶段（需求->设计->测试->任务），产生或更新 4 个文档。对于"给登录页加个验证码"这种中小型任务，文档维护成本远超开发成本。
    *   `devdocs-feature` 虽然试图简化，但实际上要求在一个 Skill session 中更新所有 4 个文档，这对 Agent 的**上下文窗口**和**注意力**是巨大挑战，容易导致更新不完整。

2.  **"代码优先"路径摩擦大**：
    *   README 提到了 "Path B: 探索后补"，但实际工具链支持不足。
    *   `devdocs-retrofit` 更像是一次性迁移工具。
    *   `devdocs-sync` 目前主要负责"找茬"（报告偏差），缺乏"自动修补"（Auto-fix/Reverse-generate）的能力。如果你写了新代码，`sync` 只会告诉你"文档缺了"，而不会帮你"把文档补上"。

3.  **文档维护债 (Sync Debt)**：
    *   一旦代码和文档发生偏离，手动修正 4 个文档的追溯关系非常痛苦。如果 `devdocs-sync` 不能自动化处理修复，文档很快就会过时被废弃。

---

## 2. 优化建议 (Actionable Suggestions)

结合 `devdocs-advise.md` 的思路与审查结果，建议进行以下 **3 点核心优化**：

### 建议一：引入 "DevDocs-Lite" 模式 (针对中小型任务)
对于不涉及复杂架构变更的功能，跳过繁琐的 01-04 分离文档，使用**单文件流**。

*   **方案**：新增 `devdocs-lite` Skill 或在 `devdocs-feature` 中增加 `--lite` 模式。
*   **产物**：仅更新 `docs/devdocs/changelog.md` 或创建一个临时的 `specs/F-XXX-feature.md`。
*   **结构**：
    ```markdown
    # F-005: 登录验证码
    > 包含需求、核心设计点、关键测试用例、开发任务清单 (All-in-One)
    - [ ] AC-01: 验证码校验逻辑 (关联 UT-020)
    - [ ] T-01: 实现验证码生成服务
    ```
*   **价值**：将文档维护成本降低 70%，适合 4 小时内的开发任务。

### 建议二：增强 "逆向同步" 能力 (Reverse Sync)
让 `devdocs-sync` 从"检查员"进化为"记录员"。

*   **现状**：`devdocs-sync` 仅报告 "T-05 已实现但文档未更新"。
*   **优化**：增加 `devdocs-sync --fix` 或 `--absorb` 功能。
    *   **自动吸纳**：扫描新代码中的注释和结构，自动在 `02-system-design.md` 中追加接口定义，在 `04-dev-tasks.md` 中标记任务完成。
    *   **测试提取**：从 `*.test.ts` 自动提取测试用例并追加到 `03-test-cases.md`。
*   **价值**：完美支持 "Path B: 先写代码后补文档" 流程，大幅降低维护债。

### 建议三：重构 `devdocs-feature` 为 "流程编排者"
解决 `devdocs-feature` 上下文过载的问题。

*   **现状**：Agent 尝试在一个会话中修改 01, 02, 03, 04 四份文档，极易出错。
*   **优化**：
    *   将 `devdocs-feature` 变为一个**编排器 (Orchestrator)**。
    *   它不再直接修改所有文件，而是引导用户（或自动调用子 Agent）分步执行：
        1.  Step 1: 仅追加 `01-requirements.md` (调用 `devdocs-requirements` 的追加模式)。
        2.  Step 2: 仅追加 `02-system-design.md` (调用 `devdocs-system-design` 的增量模式)。
        3.  ...以此类推。
*   **价值**：保持 Agent 关注点分离，提高复杂任务的文档准确性。

## 3. 行动计划

按优先级落地优化：

1.  **P0**: 改造 `devdocs-sync`，增加从代码反向更新 Task 状态和测试结果的能力（减少手动打勾的痛苦）。
2.  **P1**: 实现 `devdocs-lite` 模板，用于快速迭代。
3.  **P2**: 优化 `devdocs-feature` 的 Prompt 逻辑，使其更像是一个向导而非全能执行者。
