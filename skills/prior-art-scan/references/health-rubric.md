# 健康度 rubric：5 维

> 每维给 🟢 / 🟡 / 🔴 并**附证据**（查询 + 数字 + observed_at）。无证据的评分不成立。

## 先说不能用什么

| 假信号 | 为什么假 |
|--------|---------|
| star 数 | 滞后的虚荣指标。反映历史热度，不反映当前健康。star 只增不减，死项目的 star 不会掉。 |
| "最近有 push" | 搜索限定符 `pushed:>DATE` 匹配**任意分支**。dependabot / CI chore / 自动化 release 能让实质已死的仓库永远"活着"。 |
| README 精美程度 | 与代码质量、维护状态都无关。营销投入 ≠ 工程投入。 |
| open issue 数量 | 多可能是用户多，少可能是没人用，也可能是维护者直接关掉不处理。单看无意义。 |

---

## 维度 a：存活性

**测的是：默认分支上有没有实质的人类工作。**

```
list_commits(owner, repo, since={今天-6个月}, fields=["sha","author","commit"], perPage=100)
list_releases(owner, repo, perPage=10)
```

判读时**先剔除噪声提交**再数：

- bot 提交（`author.login` 含 `[bot]`、dependabot、renovate、github-actions）
- 纯 chore（版本号 bump、lockfile 更新、格式化、"Ran <工具>"）
- 纯文档 typo

| | 标准 |
|---|---|
| 🟢 | 近 6 个月有稳定的实质提交；release 节奏可预期 |
| 🟡 | 近 6 个月有实质提交但稀疏；或只有维护性提交无功能推进 |
| 🔴 | 近 12 个月默认分支无实质提交；或剔除 bot 后几乎为空 |

⚠️ 剔除 bot 后为空的仓库是最典型的伪活跃陷阱——列表里它看起来天天有更新。

## 维度 b：bus factor

**测的是：这个项目死于一个人失去兴趣的概率。**

```
list_commits(owner, repo, since={今天-12个月}, fields=["sha","author"], perPage=100)
```

按 `author.login` 聚合（null 回落到 `commit.author.email`），算贡献者集中度。

| | 标准 |
|---|---|
| 🟢 | 3+ 个活跃贡献者，最大贡献者占比 < 60%；或有组织/基金会背书 |
| 🟡 | 2 个活跃贡献者；或单人主导但有稳定的外部贡献流入 |
| 🔴 | 单人 100%，且该人近期活跃度在下降 |

bus factor = 1 **不等于**出局。很多优秀工具是单人项目。它的意义是：**提高了"接手维护"和"vendor+patch"路径的权重**，降低了"深度依赖"的安全性。

## 维度 c：响应性

**测的是：提了问题有没有人理。**

```
search_issues(query="repo:owner/name is:issue created:>{今天-90天}",
              fields=["number","title","state","state_reason","comments","created_at","closed_at"])
```

| | 标准 |
|---|---|
| 🟢 | 近 90 天新 issue 多数有真人回应 / 打标 / 关联 PR |
| 🟡 | 部分有回应，延迟以周计 |
| 🔴 | 新 issue 大面积零回应；或只有 stale-bot 自动关闭 |

⚠️ **stale-bot 自动关闭 ≠ 已处理**。看到大量 `not_planned` 且无人类评论的关闭，那是放弃维护的信号，不是高效治理。

## 维度 d：外部 PR 受纳度 ★

**测的是：外人的代码进不进得去。这是"上游贡献"路径的否决性前置条件。**

一个非常健康的项目完全可能根本不收外部 PR —— BDFL 主导、产品化 OSS、CLA 门槛。健康度高 **≠** 贡献路径可行。所以这一维必须独立测量，不能从维度 a-c 推导。

```
# 已合并的
search_pull_requests(query="repo:owner/name is:pr is:merged merged:>{今天-6个月}",
                     fields=["number","title","author_association","created_at","closed_at"])
# 堆积的
search_pull_requests(query="repo:owner/name is:pr is:open created:<{今天-6个月}",
                     fields=["number","title","author_association","created_at"])
```

⚠️ 不要请求 `user` 字段（每条约 15 行 URL 噪声）；`author_association` 已足够。

`author_association` 取值含义：

| 值 | 含义 |
|----|------|
| `OWNER` / `MEMBER` / `COLLABORATOR` | 内部人 —— **不计入外部贡献** |
| `CONTRIBUTOR` | 之前已有 PR 被合并过的外部人 |
| `FIRST_TIME_CONTRIBUTOR` / `NONE` | 真正的路人 —— **最强信号** |

| | 标准 |
|---|---|
| 🟢 | 近 6 个月有外部 PR 被合并，其中有路人（`NONE`/`FIRST_TIME_*`）；合并延迟以天计 |
| 🟡 | 只有固定几个 `CONTRIBUTOR` 的 PR 进得去；或延迟以月计 |
| 🔴 | 合并的几乎全是 `OWNER`/`MEMBER`；或有大量 6 个月以上无人处理的外部 open PR |

补充查证（决赛候选才做）：`CONTRIBUTING.md`、CLA / DCO 要求、`pull_request_creation_policy`、治理文档里的"我们不接受什么"。

## 维度 e：法务与可分叉性

**测的是：你在法律上和实操上能不能用、能不能改。**

```
search_repositories(query="repo:owner/name", minimal_output=false, perPage=1)
```
（这是取 license 的唯一途径——该 MCP 没有 `get_repository`）

看四件事：

1. **license 与用户硬约束是否冲突** —— AGPL / SSPL / BSL / "source available" 对闭源商用是硬闸。无 license = 默认保留全部权利，比 GPL 更严格。
2. **license 改过没有** —— 查 LICENSE 文件的提交历史。有过 relicense（尤其 OSS → BSL/SSPL）说明存在再次变更的风险，这直接影响长期依赖决策。
3. **`allow_forking`** 与 `pull_request_creation_policy`。
4. **实操可分叉性** —— 是不是绑定某个 SaaS 的 monorepo？能不能独立构建？有没有闭源依赖或必需的私有服务？**能 fork 不等于 fork 出来能跑。**

| | 标准 |
|---|---|
| 🟢 | 宽松许可（MIT/Apache-2.0/BSD），无 relicense 史，可独立构建 |
| 🟡 | copyleft 但与用途兼容；或有 CLA；或构建有一定耦合 |
| 🔴 | 许可与硬约束冲突；无 license；有 relicense 史；实质无法独立构建 |

---

## 汇总

| 候选 | a 存活 | b bus | c 响应 | d 外部PR | e 法务 | 结论 |
|------|-------|-------|--------|---------|-------|------|
| owner/name | 🟢 | 🟡 | 🟢 | 🔴 | 🟢 | 可用不可贡献 → 走 vendor+patch |

**不要把五个维度加权求和成一个总分。** 它们的作用不同：e 是硬闸（不过就出局），d 决定"贡献"可不可行，a/b 决定长期依赖风险。求和会把"许可证不兼容"这种致命项稀释成扣几分。
