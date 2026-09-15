# Skill 软触发漏检：真实案例与硬触发课题

> 来源：`~/Projects/dev-ops` 2026-08-27/28 会话的外部输入。
>
> ## ⛔ 已调研，判定**暂不做**（2026-09-16）
>
> 独立调研（Codex，只读）结论见 §「调研结论」。**证据部分全部有效**，候选方向 A–D 全部暂缓。
> 重启条件写在 §「重启条件」——满足任一条再动，不要重新论证。

## Summary

一次有完整证据的 skill 漏触发：`python-spec` 存在、描述里已列出字面关键词、全局
`AGENTS.md` 也有显式"先加载"指令，**三重指引同时在场，仍然没有触发**，导致产出违反规范
并返工。

关键结论：

- 失败**不在**"描述写得不够具体"——`python-spec` 的 description 已把语义触发降级为词表，
  而输出字面 `uv venv` 命中其中三个词，仍未触发。**任何"把描述再写清楚"的方案已被本案例证伪。**
- 失败是**静默**的：无任何信号，直到人工执行 `/python-spec` 才暴露。
- 这不是 `python-spec` 的个案，而是"做 X 前先加载 Y"这一类软触发的共性问题；
  skill 数量越多越差（当前部署 71 个）。
- 用户机器上已有**同思路的成功先例**（mise 三道环境守卫），本课题本质是把
  "让错误提前、响亮地暴露"从环境层搬到 skill 触发层。

## 关键发现

1. **两个触发点同时失效**

   任务：为本地 LLM 的 RAG 规划 Python 环境。产出并写进两份文档 + 一个脚本：

   ```bash
   uv venv ~/.venvs/rag
   uv pip install --python ~/.venvs/rag mlx-embeddings
   ```

   违反 `python-spec` 两条：① 禁止手工 venv（"不要在这之上再叠 pyenv / conda /
   手工 venv / 全局 pip install"）；② 独立辅助脚本应走 PEP 723 + `uv run`。

   证据 A —— 全局 `AGENTS.md`（经 `~/.claude/CLAUDE.md` 的 `@import` 内联，全程在上下文）：

   > Toolchain conventions live in skills, not here. **Load the matching one before doing
   > environment / dependency / project-bootstrap work**
   > `| Python (mise + uv) | python-spec |`

   证据 B —— [skills/python-spec/SKILL.md](../../skills/python-spec/SKILL.md) 的 description：

   > Triggers on keywords like "uv", "mise", **"venv"**, "pyproject.toml", "uv.lock",
   > "PEP 723", "pip install 失败", "虚拟环境"…

   **三个关键词同时命中，未触发。**

2. **失败静默，成本外部化给用户**

   无警告、无降级提示。用户手动 `/python-spec` 后才暴露，返工 3 个文件 + 1 次额外提交。
   换言之：漏检率对系统不可见，只能靠人偶然发现。

3. **同构场景不止一个**

   | skill | 应在什么之前触发 |
   |---|---|
   | `python-spec` | 建 venv / 装依赖 / 初始化 Python 项目 |
   | `commit-convention` | `git commit` |
   | `git-safety` | 改历史 / 强推 / `reset --hard` |
   | `markdown-style`、`doc-organization` | 写改文档 |
   | `code-quality` | 写代码 |

   共性：都是"做某类动作前应先加载"，都靠模型自觉。方案应针对这一类，
   而不是给 `python-spec` 打补丁。

## 环境事实（决定方案落点）

- `~/.claude/skills/` 下 **71 个条目，全部是符号链接** → `~/.agents/skills/`
- `~/.agents/skills/` 是**部署副本**（inode 与本仓不同，非链接），源在本仓
  `skills/`（**41 个**，2026-09-16 实测）。⚠️ 原文引用的 `scripts/deploy-skills.sh` **已于 `01816e8` 删除**，
  实际安装走 `npx skills` / Plugin Marketplace
- 差额来自本仓之外（`lark-*` 等）。**"收敛 skill 数量"这条路，本仓只管得了其中一部分**
- `~/.claude/settings.json` **目前没有 `hooks` 段**（顶层仅 `alwaysThinkingEnabled` /
  `autoMode` / `enabledPlugins` / `env` / `extraKnownMarketplaces` / `permissions` /
  `skipAutoPermissionPrompt` / `statusLine` / `theme`）——是从零新增，不是改现有配置
- 可参照的成功先例：`~/.zsh_unix/mise-config.toml` 的三道守卫
  （`UV_PYTHON_DOWNLOADS=never` / `PIP_REQUIRE_VIRTUALENV=true` /
  `python.uv_venv_auto="source"`），设计意图明确写着"让错误提前、响亮地暴露"

## 候选方向（不预设结论，请自行评估与增补）

| # | 方向 | 已知代价 |
|---|---|---|
| A | `PreToolUse` hook 在 Bash 层词法拦截（`uv venv`、`pip install`、`python -m venv`…），命中即 deny 并回"先加载 python-spec" | 正则维护；误报；**只覆盖 Bash**——用 Write/Edit 直接写 `pyproject.toml` 绕得过 |
| B | `UserPromptSubmit` hook 关键词预注入对应 skill 要点 | 更前置，但可能过度注入、挤占上下文 |
| C | 加强 `AGENTS.md` 措辞 | **本案例已证伪其单独有效性**，仅可作组合项 |
| D | 收敛 / 分组 skill，降低 71 条描述的列表噪声 | 治本但工程量大，且只覆盖本仓 42 个 |

## 约束

- **不在 `dev-ops` 仓处理**——那是个人运维文档仓，不该承载 agent 基础设施
- **不放宽任何既有守卫**
- 落地走本仓约定：`skills/<dir>/SKILL.md`；跨 skill 协议进
  [skills/_shared/constraints.md](../../skills/_shared/constraints.md)；设计稿进
  `docs/superpowers/specs/`
- **hook 配置不是 skill 内容**，其事实源与部署路径须一并定：写进
  `~/.claude/settings.json`，还是本仓 plugin 自带 `hooks/`？（⚠️ 2026-09-16 调研已答：见 §调研结论）
  注意 `~/.claude/skills/*` 是链接、`~/.agents/skills/*` 是副本，两级链路已存在

## 期望产出

1. **先判断值不值得机制化。** "不做"是合法结论，但要给依据（例如漏检率未知、
   误报成本高于漏检成本）。不要默认往下做。
2. 若做：触发机制设计 + 覆盖面（哪些 skill、哪些动作）+ **失败模式**
   （误报如何绕过；hook 本身挂了会不会阻断一切）。
3. 明确 hook 配置的事实源与部署路径。
4. **可验证的验收判据**：能构造复现本案例的最小场景（让 agent 在无提示下规划 Python
   环境），并证明修复后被拦下——而不是只在文档里写"应该会被拦下"。

---

## 调研结论（2026-09-16，Codex 独立只读调研 + 本仓复核）

### 判定：候选方向 A–D 全部暂不做

对照物 `superpowers` 用 `SessionStart` hook 把入口 skill 正文注入每个会话
（`hooks/hooks.json:3-11`，matcher `startup|clear|compact`；实测注入 **3333 UTF-8 字节**）。
这是本课题唯一已知的"硬触发"实现。**照搬不成立**，四条边界事实：

| # | 事实 | 证据 |
|---|---|---|
| 1 | **`npx skills add` 不安装根级 hook** —— copy 与 symlink 两种模式的复制边界都是单个 skill 目录 | `skills@1.5.24` `dist/cli.mjs:2220,2236` |
| 2 | **hook 写进 SKILL frontmatter 也救不了首次漏加载** —— Claude 在 skill *被调用之后* 才注册其中的 hooks | Claude 官方 hooks 文档 |
| 3 | **superpowers 在 Codex 上根本没有这个 hook** —— portal 包 manifest 为 `"hooks": {}`，打包脚本明确排除 `hooks/` | `.codex-plugin/plugin.json:23`、`scripts/package-codex-plugin.sh:334` |
| 4 | **superpowers 自身也有静默退化路径** —— Windows wrapper 找不到 Bash 退出 0；读入口文件失败时把错误文字装进上下文后仍退出 0 | `hooks/run-hook.cmd:37`、`hooks/session-start:11,49` |

⇒ 本仓虽已是 plugin（`.claude-plugin/plugin.json`，可承载 hook），但 hook **只覆盖 Plugin Marketplace 一条安装路径**，
`npx` 路径覆盖不到，因此**删不掉**现有的 `agent-memory` 项目级 AGENTS.md 路由。
它是**净增机制而非替代** —— 违反"禁止用新增机制作答"这条反规则，也未过 [AGENTS.md](../../AGENTS.md) 的 ROI 门槛。

### 本轮新增的一条机制性证据（强化 §关键发现 1）

Codex CLI 自身在本次调研中输出：

> `warning: Skill descriptions were shortened to fit the skills context budget.`

即 **Codex 客户端会机制性截断 skill description**。这把 §关键发现 1 的结论
（"任何『把描述再写清楚』的方案已被本案例证伪"）从**概率性**升级为**机制性**：
在 Codex 上这不是描述写得够不够好的问题，是写多了会被主动削掉。

⚠️ 但它**不构成第二个撞墙案例** —— 没有对应的返工事实，只是能力上限的证明。

### 绕法（现在就用）

需要 DevDocs 流程时**显式调用** `/ms-pipeline`，或直接点名原子 skill。
净增文件 / 状态 / 概念均为 0。这不是零漏检保证，是当前证据下成本最低的走法。

### 重启条件（满足任一条再动，⛔ 不要重新论证上面已判定的部分）

1. **出现第二个项目的实际漏触发返工**（要有返工事实，不是"这类场景也可能中"的枚举）。
   本轮检索 `docs/audits` 与 `docs/workflows.md`，漏触发案例**只有本文一份**。
2. `npx skills` 上游支持随 skill 分发 hook —— 事实 1 失效，覆盖面问题消失。
3. 放弃 `npx` 安装路径，只走 Plugin Marketplace —— 覆盖面问题同样消失，但这是用户面破坏性变更。

### 验证边界

真达到门槛时，验证要分两层：本仓只能检查注册文件、JSON 与注入大小；
**"任务是否正确触发 / 是否误触发 / 压缩恢复后是否仍有效"必须到真实客户端做对照实验，本仓静态规格验不了。**
superpowers 自己的 hook 测试也只验输出形状与文本存在（`tests/hooks/test-session-start.sh:74-132`），同样不能替代模型行为验证。
