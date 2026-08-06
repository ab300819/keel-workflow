# prior-art-scan：新项目开工前的先例扫描 skill 设计

- 日期：2026-08-06
- 状态：已实现
- 类型：新增 standalone skill（非 DevDocs 流程，无 ms- 前缀）

## 1. 问题

新项目开工前缺一道强制的「先例检查」。没有它，两种失败反复出现：

1. **重复造轮子** —— 已有维护良好的同类项目，却从零开始。
2. **错误地 fork** —— 发现了同类项目，但用错误的方式接入：该贡献的去 fork（从此永久自负维护 + 分叉发散），该自建的去 fork 一个架构根本不匹配的东西。

要解决的是决策质量，不只是"搜出一个列表"。

## 2. 关键设计判断

### 2.1 幻觉是本 skill 的头号风险

LLM 编造 repo 名、star 数、"最近还在维护"的能力极强，而这类输出**看起来完全合理**，人几乎无法凭肉眼识别。一份编造的先例报告比没有报告更糟——它会直接导致错误的开工决策。

→ **证据门（硬约束）**：未经真实工具调用确认的候选不得入表；每条数据带 `repo URL + 产生它的查询 + observed_at`。

### 2.2 star / 最近 push 都是假信号

- `stargazers_count` 是滞后的虚荣指标，反映历史热度而非当前健康。
- 搜索限定符 `pushed:>DATE` 匹配**任意分支**的 push；dependabot / CI chore 能让一个实质已死的仓库始终"活着"。
- README 精美程度与代码质量无关。

→ 健康度必须走 **5 维 rubric**（见 §3.3），核心是"默认分支上的**实质**提交"而非"有提交"。

### 2.3 "能不能贡献"是独立于"健不健康"的维度

一个非常健康的项目完全可能根本不收外部 PR（BDFL 主导 / 产品化 OSS / 有 CLA 门槛）。健康度高 ≠ 贡献路径可行。这是"贡献"选项的**否决性**前置条件，必须单独测量。

→ 用 `author_association` 分布 + 外部 PR 合并延迟 + 陈旧 PR 堆积来量化（实测可行，见 §4）。

### 2.4 决策不是三选一

用户原始表述是 fork / 贡献 / 自建三分法。实际谱系有 6 条路径，且最常正确的是被三分法漏掉的中间项：

| 路径 | 何时正确 |
|------|---------|
| use-as-is | 缺口是伪需求，或可用配置解决 |
| 插件 / 扩展点 | 上游有扩展机制，缺口能在机制内实现 |
| 上游贡献 | 缺口是 help-wanted 型，且外部 PR 受纳度已验证 |
| **vendor + patch（边用边上游）** | 需要立刻可用，同时保留上游收敛路径 —— **默认优先考虑** |
| 硬 fork | 缺口是 wontfix/out-of-scope 型，且无扩展点 |
| 自建 | 架构根本不匹配，或有明确差异化理由 |

两条纪律：
- **fork 成本被系统性低估** —— 决策默认反对 fork，需要额外理由才成立。
- **自建是最贵的** —— 必须给出**差异化**理由，"我不喜欢他们的代码"不算。

### 2.5 最便宜的实验是"先问上游"

很多决策不问就是不可知的（维护者是否愿意接、是否已有人在做、是否有意不做）。开一个 issue / discussion 提方案，成本一天，能消除最大的不确定性。

→ 决策段必须包含"先问上游"的最小实验，且它是**行动项**而非分析瘫痪的借口。

### 2.6 只读

github MCP 提供 `fork_repository` / `issue_write` / `create_pull_request` 等写工具。在别人的仓库上开 issue、提 PR、fork 都是**对外动作**。

→ skill 对 GitHub 全程只读；所有写动作只能作为报告里的行动项，由用户另行显式批准。`allowed-tools` 白名单从工具层面兜住这条。

### 2.7 检索必须多角度

GitHub 关键词搜索语义匹配很差。实测 `topic:cli topic:todo archived:false stars:>100 pushed:>2026-01-01` 只有 11 个结果——topic 合取极度收敛，且最好的项目常常只出现在 awesome-list 或"X alternatives"文章里，不出现在 topic 搜索里。

→ **覆盖门**：6 个检索角度必须全跑并留证，少跑要写明原因。

## 3. 方案

### 3.1 定位与形态

| 项 | 决策 |
|----|------|
| 命名 | `prior-art-scan`（standalone，非 ms- 前缀）|
| 理由 | 产出是决策报告而非 DevDocs 编号产物，不进 `docs/devdocs/`，不接 constraints.md 门控标记 / spec_version / realign 治理 |
| 结构 | 单 SKILL.md + references 分层（仿 e2e-test-flow）|
| 产出 | cwd 单文件 `prior-art-<slug>-<YYYY-MM-DD>.md`，路径可覆盖 |
| 产出理由 | "新项目开工前"常常还没有仓库，必须能在空目录跑；且零污染当前仓库（不写 docs/、不改索引）|
| 交接 | 报告末尾给指针：自建 → `/ms-prd` 或 `/ms-pipeline init`；fork → `/ms-retrofit`；贡献 → `/dev-flow` |

### 3.2 主链路 6 步

```
0 澄清    must-have / nice-to-have / 硬约束(语言·许可·部署·合规)
1 发现    6 角度检索矩阵 → 长名单
2 粗筛    硬闸(archived / license / 语言栈 / 明显 dead) → 短名单 5-8
3 深评    5 维 health rubric → top 3
4 Gap     4 类 gap 分类
5 决策    6 路径谱系 + 硬闸 + 反方理由 + 先问上游的最小实验
6 报告    单文件 md + 交接指针
```

第 0 步不可跳过：没有 must-have 清单，后面的 gap 分析和决策全是空谈。

### 3.3 Health rubric 5 维

| 维 | 测什么 | 怎么测 |
|----|--------|--------|
| a 存活性 | 默认分支**实质**提交（排除 bot / chore / 纯 docs）、发布节奏 | `list_commits` + `list_releases` |
| b bus factor | 近 12 个月贡献者集中度 | `list_commits` 按 author 聚合 |
| c 响应性 | 近 90 天 issue 是否被真人回应 / 打标 | `search_issues` |
| d **外部 PR 受纳度** | `author_association` 分布、外部 PR 合并延迟、陈旧 PR 堆积 | `search_pull_requests` |
| e 法务与可分叉性 | license（AGPL/BSL/source-available 是硬闸）、是否改过 license、`allow_forking`、CLA | `search_repositories minimal_output:false` |

### 3.4 Gap 四分类 → 决策映射

gap 的**类型**比 gap 本身更决定路径：

| gap 类型 | 识别方式 | 映射路径 |
|---------|---------|---------|
| help-wanted 型（维护者想要） | `label:"help wanted"` / `label:enhancement` / 高 👍 open issue | 上游贡献 |
| wontfix 型（维护者明确不做） | `reason:not-planned` 关闭的 issue、"out of scope"、roadmap 反向声明 | 有扩展点 → 插件；否则 fork |
| 架构不匹配 | 深评时读关键源码判断 | 自建 |
| 只是无人维护但东西好 | 存活性差但质量与匹配度高 | 接手维护 / co-maintain（**先问**）|

`reason:not-planned` 是最强信号——它是维护者对"这不是我们要做的事"的显式记录，正是 fork 的合法领地。

## 4. 工具能力实测（2026-08-06，github MCP）

写进 skill 的检索配方全部经过 live 调用验证，避免凭印象编 API 用法。发现的坑：

1. `search_repositories` 的 `minimal_output:true`（默认）**不返回 license，也不返回 `pushed_at`**（只有 `updated_at`，那是元数据触碰时间，不是 push 时间）。取 license / `pushed_at` / `allow_forking` / `pull_request_creation_policy` 必须用 `minimal_output:false` + `repo:owner/name`，但该响应约 60 行 URL 噪声 → **只对决赛候选调用，不逐个候选调**。
2. 此 MCP **没有 `get_repository` 工具**。单仓元数据的唯一取法就是上面的 `repo:owner/name` 搜索。
3. `search_pull_requests` 的 `fields` 支持 `author_association`（实测 simonw/llm 近 4 个月 27 个合并 PR 中 OWNER / CONTRIBUTOR 可区分）。**不要请求 `user` 字段**——每条结果会带约 15 行头像与 API URL，纯噪声；`author_association` 已足够算比例。
4. `search_issues` 查询语法用连字符 `reason:not-planned`，返回值却是下划线 `state_reason: "not_planned"`。
5. `list_commits` 的 `since` + `fields:[sha,author,commit]` 可用于 bus factor 与 bot 识别；注意 `author` 对未关联 GitHub 账号的提交为 null，需回落到 `commit.author.email`。
6. topic 合取极度收敛（§2.7），证实覆盖门的必要性。

## 5. 文件清单

```
skills/prior-art-scan/
├── SKILL.md                          主链路 + 3 条跨切面纪律
├── references/
│   ├── discovery-matrix.md           6 检索角度 + 可复制查询配方 + API 坑
│   ├── health-rubric.md              5 维评估细则 + 判读阈值
│   └── decision-spectrum.md          6 路径谱系 + 硬闸 + 反方理由要求
└── templates/
    └── report-template.md            报告骨架
```

## 6. 未采纳

- **HTML 对比面板**（复用 ms-board 那套）：候选矩阵可排序确实更直观，但实现成本高于收益，md 表格够用。触发条件=真实出现"一次评审 8+ 候选且需要交互筛选"的场景。
- **编排 + 子代理并行检索**：覆盖率更高、上下文更省，但复杂度与不确定性上升，违背"skill 宜简"。单 skill 形态先跑，若实践中出现检索角度漏跑的系统性问题再升级。
- **接入 DevDocs 治理体系**（ms- 前缀）：产出不是编号产物，接门控标记 / spec_version / realign 是纯负担。
