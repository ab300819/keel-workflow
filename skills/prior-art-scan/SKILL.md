---
name: prior-art-scan
description: 新项目开工前检索同类开源项目，评估维护度和缺口，帮助选择复用、扩展、贡献、fork 或自建。用于先例扫描和开源选型。
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion, TodoWrite, WebSearch, WebFetch, mcp__plugin_github_github__search_repositories, mcp__plugin_github_github__search_code, mcp__plugin_github_github__search_issues, mcp__plugin_github_github__search_pull_requests, mcp__plugin_github_github__list_commits, mcp__plugin_github_github__list_releases, mcp__plugin_github_github__get_latest_release, mcp__plugin_github_github__get_file_contents, mcp__plugin_github_github__list_issues, mcp__plugin_github_github__list_pull_requests, mcp__plugin_github_github__list_repository_collaborators, mcp__plugin_github_github__issue_read, mcp__plugin_github_github__pull_request_read
metadata:
  patterns: [research, decision-support]
  interaction: multi-turn
user-invocable: true
---

# Prior Art Scan

新项目开工前的先例扫描：**别人做过没有 → 做得好不好 → 差什么 → 我该怎么接入**。

产出一份单文件 md 报告，终点是一个**可执行的决策**，不是一张仓库列表。

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese

## 跨切面纪律（贯穿全流程，违反即作废）

### 纪律 1：证据门 —— 未经工具确认的，不存在

编造 repo 名、star 数、"仍在维护"是本 skill 的头号失败模式，且编造出来的东西**看起来完全合理**，人肉眼无法识别。一份编造的先例报告比没有报告更糟——它直接导致错误的开工决策。

- ⛔ **不得凭记忆写任何候选项目、数字或结论**。只要没有一次真实工具调用产生它，它就不能进报告。
- 每个候选带 `repo URL`；每个数字带**产生它的查询**和 `observed_at` 日期。
- 训练数据里的"我知道有个项目叫 X"只能作为**检索输入**（拿去搜），不能作为**检索输出**（直接写进表）。搜不到就是搜不到，如实写"未确认"。
- 报告里任何一处出现无法追溯到工具调用的数据 → 整份报告作废重做。

### 纪律 2：只读 —— 别人的仓库不是你的

- ⛔ 全程不 fork、不开 issue、不提 PR、不评论。这些是**对外动作**，一旦发出无法撤回。
- `allowed-tools` 已从工具层面排除全部 GitHub 写工具。即使用户在会话中说"顺便帮我提个 issue"，也要**退出本 skill 后单独确认再做**。
- 克隆到本地做深度阅读：需先征得用户同意，且只落在临时目录，不污染当前工作区。

### 纪律 3：覆盖门 —— 6 个角度必须全跑

GitHub 关键词搜索语义匹配很差，最好的项目常常只出现在 awesome-list 或"X alternatives"文章里。只搜一轮 GitHub 就下结论 = 系统性漏掉最强候选。

- 6 个检索角度（见 [`references/discovery-matrix.md`](references/discovery-matrix.md)）必须全部执行并在报告中留证。
- 少跑任何一个，必须在报告的「检索矩阵」段写明**原因**（如"该领域无对应包管理生态"）。
- ⛔ 不得因为"第一轮已经搜到几个不错的"就停止检索。

---

## 主链路

### 步骤 0：澄清需求（不可跳过）

没有 must-have 清单，后面的缺口分析和决策全是空谈——"差什么"必须相对于**你要什么**才有定义。

用 AskUserQuestion 问清：

| 项 | 说明 |
|----|------|
| 一句话目标 | 这个项目要解决什么问题、给谁用 |
| must-have | 缺了就不可用的能力（3-6 条），后续逐条比对候选 |
| nice-to-have | 有更好，缺了能忍 |
| 硬约束 | 语言 / 运行环境 / 部署形态 / 许可证要求（商用？闭源分发？）/ 合规 |
| 差异化意图 | 你是否**本来就想**做点不一样的？如果有，具体是什么 |

**门控**：must-have 清单未确认 ⛔ 不进入步骤 1。

「差异化意图」要如实记录但**先搁置**——它是步骤 5 的输入之一，不能在这一步就变成"所以我要自建"的预设结论。

### 步骤 1：发现（6 角度检索矩阵）

加载 [`references/discovery-matrix.md`](references/discovery-matrix.md)，逐角度执行，记录每个角度**跑了什么查询、出了几个结果**。

产出：候选长名单（含 repo URL + 首次发现来源）。宁滥勿缺，粗筛在下一步。

### 步骤 2：粗筛（硬闸）

对长名单逐个过硬闸，任一不过即出局，**并记录出局原因**（出局记录本身是报告的一部分——它证明你看过）：

- `archived: true` → 出局（除非它正是"接手维护"的目标，单独标注）
- 许可证与用户硬约束冲突（AGPL / SSPL / BSL / source-available vs 闭源商用需求）→ 出局
- 语言 / 运行环境与硬约束不可调和 → 出局
- 明显 dead：默认分支 12 个月无实质提交且无 release
- 明显不是同类：只是关键词撞车

产出：短名单 5-8 个。多于 8 个说明需求描述太宽，回步骤 0 收敛。

### 步骤 3：深评（5 维健康度）

加载 [`references/health-rubric.md`](references/health-rubric.md)，对短名单做健康度评估。

⚠️ **star 数和"最近有 push"都是假信号**：star 是滞后的虚荣指标；`pushed:>DATE` 匹配任意分支，dependabot 能让死仓一直"活着"。真信号是**默认分支上的实质提交**。

五维：存活性 / bus factor / 响应性 / **外部 PR 受纳度** / 法务与可分叉性。

其中「外部 PR 受纳度」是独立维度，不可由健康度推导：**一个非常健康的项目完全可能根本不收外部 PR**（BDFL 主导 / 产品化 OSS / CLA 门槛）。它是"上游贡献"路径的否决性前置条件。

产出：top 3 决赛候选 + 每维带证据的评分。

### 步骤 4：缺口分析

对每个决赛候选，两个方向同时做：

**A. 正向比对** —— 用步骤 0 的 must-have 清单逐条打勾。缺失项必须给出判定依据（读文档 / 读源码 / 搜 issue），不能凭 README 有没有提到就下结论。

**B. 反向挖掘** —— 从项目自己的 issue 区挖，这比你凭空想更准：

| 挖什么 | 查询 | 意味着 |
|--------|------|--------|
| 维护者想要的 | `label:"help wanted"` / `label:enhancement` / 高 👍 open issue | 缺口有人欢迎你补 |
| 维护者明确不做的 | `is:closed reason:not-planned`、"out of scope" | 缺口是**设计意图**，不是疏忽 |
| 正在做的 | open PR、roadmap、discussions | 别重复劳动 |

把每个缺口归入**四类之一**——类型比缺口本身更决定路径：

| 缺口类型 | 映射路径 |
|---------|---------|
| help-wanted 型（维护者想要） | 上游贡献 |
| wontfix 型（维护者明确不做） | 有扩展点 → 插件；否则 fork |
| 架构不匹配（根本性设计冲突） | 自建 |
| 只是没人维护但东西好 | 接手维护 / co-maintain（先问）|

`reason:not-planned` 关闭的 issue 是最强信号——它是维护者对"这不是我们要做的事"的显式记录，正是 fork 的合法领地。

### 步骤 5：决策

加载 [`references/decision-spectrum.md`](references/decision-spectrum.md)。**不是三选一，是六条路径**：

```
use-as-is → 插件/扩展 → 上游贡献 → vendor+patch → 硬 fork → 自建
                                     ↑ 默认优先考虑        成本递增 →
```

三条必须遵守的纪律：

1. **默认反对 fork** —— fork 成本被系统性低估：从此永久自负维护 + 与上游发散。选它需要额外理由。
2. **自建最贵** —— 必须给出**差异化**理由。"我不喜欢他们的代码"不算理由。
3. **每个推荐必须同时写出「反对本决策的最强理由」** —— 写不出来说明没想清楚，回步骤 3。

并给出**先问上游的最小实验**：很多决策不问就是不可知的（维护者愿不愿意接、是否已有人在做）。开一个 issue / discussion 提方案，成本一天，能消除最大的不确定性。这是**行动项**，不是拖延的借口——报告要写明"问什么、怎么问、什么回答对应什么路径"。

⚠️ 决策若依赖尚未验证的假设（"应该能通过插件实现"），必须标为**待验证**并给出验证方法，不能当成结论。

### 步骤 6：报告

按 `templates/report-template.md` 写入 **cwd 的 `prior-art-<slug>-<YYYY-MM-DD>.md`**（用户可指定其他路径）。

零污染：不写 `docs/`、不改任何索引、不碰当前仓库其他文件。"新项目开工前"往往还没有仓库，报告必须能在空目录里生成。

报告末尾给交接指针：

| 决策 | 下一步 |
|------|--------|
| 自建 | `/ms-prd` 或 `/ms-pipeline init`（重型）；`/dev-flow`（轻量）|
| fork / vendor+patch | 拿到代码后 `/ms-retrofit` 补文档体系 |
| 上游贡献 | `/dev-flow` 执行，注意遵守上游的 CONTRIBUTING |
| use-as-is / 插件 | `/ms-system-design` 做集成设计 |

## 工具与降级

- 主用 github MCP（`mcp__plugin_github_github__*`，只读子集）。**该 MCP 没有 `get_repository` 工具**——单仓元数据靠 `search_repositories` + `repo:owner/name` + `minimal_output:false`。
- MCP 不可用时降级到 `gh` CLI（`gh api` / `gh search repos`）；`gh` 也不可用则告知用户并停止——⛔ 不得凭记忆补数据（纪律 1）。
- 搜索 API 有速率限制（认证态约 30 次/分钟）。批量查询时收敛 `perPage`、善用 `fields` 裁剪响应。
- 具体查询配方与已知 API 坑：[`references/discovery-matrix.md`](references/discovery-matrix.md)。

## 快速模式

用户明确要"快速看一眼"时：跑检索矩阵的角度 1/3/4（GitHub topic、awesome-list、生态搜索），只出候选清单 + 一句话健康度，**明确标注"未做深评，不构成决策依据"**。

⛔ 快速模式不得输出六路径决策——那需要完整的深评与缺口分析支撑。
