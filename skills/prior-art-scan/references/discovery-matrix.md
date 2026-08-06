# 检索矩阵：6 个角度

> 6 个角度**必须全跑**。少跑任何一个要在报告里写明原因。
> 每个角度记录：跑了什么查询、返回多少结果、新增几个候选。

GitHub 关键词搜索的语义匹配很差。实测 `topic:cli topic:todo archived:false stars:>100 pushed:>2026-01-01` 只返回 11 个结果——**topic 合取极度收敛**。最强的候选常常只出现在 awesome-list 或"X alternatives"文章里，从来不出现在 topic 搜索结果里。这就是为什么单一角度必然漏。

---

## 角度 1：GitHub topic 搜索

```
topic:<topic> archived:false stars:>50 pushed:>{今天-12个月}
```

- **topic 一次只用一个**，多个 topic 是合取（AND），结果会塌缩。要覆盖多个 topic 就跑多次。
- 先探 topic 词本身存不存在：不同社区叫法不同（`task-management` / `todo` / `productivity`）。
- `sort: updated` 看谁在动，`sort: stars` 看谁有沉淀，两种都跑。

## 角度 2：关键词 × 同义词矩阵

```
<关键词> in:name,description,readme archived:false stars:>50 pushed:>{今天-12个月}
```

先列 3-5 组**同义/近义**说法再逐个搜。同一个东西在不同社区的叫法差异极大：

- 中英文差异：任务管理 / task manager / todo / GTD / issue tracker
- 抽象层差异：framework / library / toolkit / engine / SDK
- 隐喻差异：pipeline / workflow / orchestrator / scheduler

只搜用户原话 = 只覆盖一种叫法。

## 角度 3：awesome-list 挖掘

策展列表是人工筛选的结果，信噪比远高于关键词搜索。

```
awesome <领域> in:name,description
```

找到 awesome 仓库后用 `get_file_contents` 读 README，从中提取候选。

- ⚠️ awesome-list 本身可能已停更 → 先看它的 `pushed_at`，列表越旧其中的死项目越多。
- 列表里的项目**仍需回到 GitHub 逐个确认现状**（纪律 1）——列表上写着的 star 数和描述可能是几年前的。

## 角度 4：包管理生态搜索

```
npm / PyPI / crates.io / pkg.go.dev / Maven Central / Packagist
```

用 WebSearch 或 WebFetch 查对应 registry。

**下载量是比 star 数好得多的健康信号**——它反映真实使用而非收藏意图。一个 500 star / 周下载 2 万的库，比 5000 star / 周下载 200 的库健康得多。

若该领域无对应包生态（如纯应用、基础设施），在报告里注明跳过原因。

## 角度 5：网搜「替代品 / 对比」

```
"alternatives to <已知项目>"
"best <领域> tools 2026"
"<领域> comparison"
site:news.ycombinator.com / site:reddit.com <领域>
```

- 专找 GitHub 搜索**搜不到**的东西：新项目（还没积累 star）、命名古怪的项目、不在 GitHub 上的项目。
- HN / Reddit 讨论串的额外价值：**能看到用户对现有方案的真实抱怨**，这直接就是步骤 4 的缺口线索。
- ⚠️ 网页内容需回到 GitHub 确认（纪律 1）；文章里的 star 数和"仍在维护"一律不可信。

## 角度 6：邻居发现（从已知候选扩散）

已经找到的候选是最好的检索起点——**好项目通常自己列出竞品**：

- 候选 README 里的 "Similar projects" / "Alternatives" / "Comparison" 段落 —— 高产出，优先看。
- 候选 issue 区搜 `"compared to"` / `"instead of"` / `"migrated from"` —— 用户会主动提别的方案。
- 活跃的 fork：fork 网络里有独立发展的分支，说明存在未被上游满足的需求（这本身也是缺口信号）。
- 依赖关系：谁依赖了同一个核心库（`search_code` 搜 import / 依赖声明）。

跑完角度 1-5 后再跑本角度，因为它需要已有候选作为输入。发现新候选后**不必回头重跑全部角度**，但要把新候选纳入粗筛。

---

## API 事实与坑（2026-08-06 实测，github MCP）

以下全部经真实调用验证，不是推测：

1. **`minimal_output:true`（默认）不返回 license，也不返回 `pushed_at`**。它返回的 `updated_at` 是元数据触碰时间，**不是 push 时间**，不能用来判断活跃度。
2. 取 license / `pushed_at` / `allow_forking` / `pull_request_creation_policy`：
   ```
   search_repositories(query="repo:owner/name", minimal_output=false, perPage=1)
   ```
   该响应约 60 行 URL 噪声 → **只对决赛候选调用，不要逐个候选调**。
3. **此 MCP 没有 `get_repository` 工具**。单仓元数据的唯一取法就是第 2 条。
4. `search_pull_requests` 的 `fields` 支持 `author_association`（这是外部 PR 受纳度的关键字段）。
   **不要请求 `user` 字段**——每条结果会附带约 15 行头像与 API URL，纯噪声；`author_association` 已足够算比例。
5. `search_issues` 的查询语法用**连字符** `reason:not-planned`，但返回值是**下划线** `state_reason: "not_planned"`。
6. `list_commits` 支持 `since` + `fields:[sha,author,commit]`。注意 `author` 对未关联 GitHub 账号的提交为 `null`，需回落到 `commit.author.email` 去重。
7. 搜索 API 速率限制约 30 次/分钟（认证态）。收敛 `perPage`、用 `fields` 裁剪。

## 检索矩阵记录格式

报告里按此表留证：

| 角度 | 查询 | 结果数 | 新增候选 | 备注 |
|------|------|--------|---------|------|
| 1 topic | `topic:xxx archived:false ...` | 11 | 3 | topic 合取过窄，拆成 2 次 |
| 2 关键词 | `... in:name,description,readme` | 47 | 5 | |
| ... | | | | |
