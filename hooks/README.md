# hooks

⚠️ **只在插件安装路径下生效。** ⇒ hook 只能是**加速器**，规则本身必须仍写在 skill 正文里，
⛔ 不得把门挪进 hook。

## 三端适配

**公共检查逻辑一份**（`devdocs-drift` / `skill-flag-lint`，按 `hookSpecificOutput.additionalContext`
契约打印 JSON），适配层三个里只需要两份文件：

| 端 | 适配层 | 依据 |
|---|---|---|
| Claude Code | `hooks/hooks.json` | 插件根下的默认发现路径，⛔ 不需要在 `plugin.json` 里声明 |
| Codex CLI | **同一个 `hooks/hooks.json`** | Codex 默认发现插件根的 `hooks/hooks.json`（根 `plugin.json` 的 `extensions.com.openai.hooks` 显式声明了同一路径）；事件名 / handler 字段 / 输出契约与 Claude Code 同形，`${CLAUDE_PLUGIN_ROOT}` 作为 `PLUGIN_ROOT` 的 legacy 别名仍受支持（[docs](https://learn.chatgpt.com/docs/hooks)）|
| OpenCode（仅 v2） | `hooks/opencode-plugin.js` | 该端**不读 hooks.json**，由根 `package.json` 的 `main` 指向本文件作为插件包入口（同时用 `ctx.skill.transform` 注册 `skills/`）；且**没有 additionalContext 通道**，只能在 `ctx.tool.hook("execute.after")` 里把消息追加进 `event.result.content`（[docs](https://opencode.ai/v2/docs/build/plugins)）。⛔ v1 插件 API（返回 hooks 对象）在 v2 不运行，已不再支持 |

OpenCode 安装：

```bash
opencode plugin add github:ab300819/keel-workflow
```

| hook | 作用域 | 触发 | 干什么 |
|---|---|---|---|
| `devdocs-drift` | **用户 keel 项目** | PostToolUse `Edit\|Write\|NotebookEdit\|Bash` | 改了代码但 `docs/devdocs/` 没动 → 一行提示。5 分钟冷却 |
| `skill-flag-lint` | **skill 库自身** | PostToolUse `Edit\|Write\|NotebookEdit`，且编辑的是 `skills/**/*.md` | 跑 `health-lint.py --skills-dir` 的 `flag/dangling-reference`。2 分钟冷却 |
| `devdocs-layout` | **用户 keel 项目** | SessionStart（⛔ 无 matcher） | 跑 `health-lint.py --target` 取 `layout/*` 三条 → 一行提示。⛔ 无冷却（SessionStart 天然低频）|

⚠️ **`devdocs-layout` ⛔ 跑真实扫描而非启发式探针。** 实测 0.11s（22 文件）/ 0.48s（360 文件），
远低于路由探针的 2s 预算，所以没必要退化成廉价启发式——这样它的提示内容与用户手动跑
`/pipeline realign --scope=health` **完全一致**，两者不会给出打架的结论。
⚠️ 它**只扩大触达，⛔ 不能证明用户会处理**：闭环靠「检查→决策→执行→复查」四步，不靠本 hook。

⚠️ **`devdocs-drift` 与 `skill-flag-lint` 两者 matcher 不同，是有意的。** `devdocs-drift` 看 `git status`，与用哪个工具改的无关，所以必须覆盖 `Bash`——否则 shell 改文件（auto 模式、脚本化编辑、CI）全程不触发。`skill-flag-lint` 依赖 `tool_input.file_path`，`Bash` 调用没有该字段，加进去也只是空转，故不加。

两者都在不适用时**静默 exit 0**，互不干扰。

## 写 hook 的坑（实测踩过）

- ⛔ **不要用 `timeout(1)`** —— macOS 默认没有。`timeout 1 cat || true` 会静默吞掉
  整个 stdin payload，hook 变成永远不触发且没有任何错误。用 bash 内建读。
- PostToolUse **每次工具调用都触发**，不加冷却必然变噪声。
- ⛔ **matcher 别只写 `Edit|Write|NotebookEdit`** —— 用 shell 改文件不属于这三者，hook 全程不触发。按「这个检查依不依赖 `file_path`」决定要不要覆盖 `Bash`。
- `skill-flag-lint` 的检出能力受 `health-lint.py` 限制：`REL_LINK_RE` 只认 `./` / `../` 开头的链接，**裸相对链接（`references/x.md`）不在检查范围**——实测本仓 253 条裸链接 vs 226 条被检查。别把「hook 没报」当成「没断链」。
- 输出契约：`{"hookSpecificOutput":{"hookEventName":"...","additionalContext":"..."}}`
  Claude Code 与 Codex 共用这一份；OpenCode 由 `opencode-plugin.js` 解析出 `additionalContext`
  再追加进工具结果（该端无等价通道）。

## ⛔ 改完当场测不到（2026-09-16 实测）

`hooks/` 与 `skills/` **只从插件安装路径加载**，工作树的改动不即时生效。链路三级都会卡：

```text
工作树 HEAD
   │  ① 未推送的 commit 进不了下一级
   ▼
marketplaces/<mp>/          ← git clone，`/plugin` 会 pull 到最新
   │  ② ⛔ 安装目录按版本号建：cache/<mp>/<plugin>/<version>/
   │     version 没变 → 更新器认为「已是最新」→ 一个文件都不拷
   ▼
cache/<mp>/<plugin>/<ver>/  ← 实际被加载的那份（Skill 工具报的 base directory）
   │  ③ 会话读入一次后缓存；`/reload-plugins` 可原地刷新，不必重开会话
   ▼
本会话的 skill 正文 / hooks.json
```

**② 是主卡点，实测**（2026-09-17）：推送 `7fa9a98` 后跑 `/plugin update` + `/reload-plugins`，marketplace clone 确实 pull 到了 `7fa9a98`（`hooks.json` mtime 更新），但 `cache/…/2.0.0/hooks/hooks.json` 的 mtime 纹丝不动，`installed_plugins.json` 里记的仍是旧 commit —— 因为 `plugin.json` 的 `version` 一直是 `2.0.0`。

> ⛔ **改了 skill 或 hook，必须同时 bump `plugin.json` 的 `version`**（根 `plugin.json` 与 `.claude-plugin/plugin.json` 两处），否则 `git push` + `/plugin update` 都是空转。
>
> 完整生效路径：bump version → commit → push → `/plugin update` → `/reload-plugins`（或新会话）。

**③ 不是死路（2026-09-17 实测）**：手工把新文件拷进 `cache/…/` 后，同一会话里跑 `/reload-plugins`，新起的子代理立刻拿到新正文（Skill 工具报的 base directory 确认是 cache 那份）。所以「改完当场测不到」的责任全在 ②，不在会话生命周期。

同理，下面记的「已验证」一律指**被安装的那一版**，不是工作树。

## 状态

⚠️ **两个都是试验件。** 验不过就删，⛔ 不要在它们之上加功能。背景见
[docs/audits/2026-08-28-skill-soft-trigger-miss-brief.md](../docs/audits/2026-08-28-skill-soft-trigger-miss-brief.md)。

| 验证项 | 状态 |
|---|---|
| 脚本逻辑（构造 payload，9 个场景：该响 / 文档跟上 / 只改文档 / 冷却 / 非 keel 项目 / 非 skills 路径 / lint 干净 / lint 有 finding / Bash 形状 payload） | ✅ 2026-09-16 全过 |
| **Claude Code 真实会话触发** | ✅ 2026-09-16，`Edit` 埋断链探针，`additionalContext` 正确送达 |
| Codex CLI 真实会话触发 | ⬜ 未跑 |
| `devdocs-layout` 脚本逻辑（3 种输入：非 keel 项目须静默 / 合规项目须静默 / tm-reborn 须命中 8 项） | ✅ 2026-09-24 全过 |
| `devdocs-layout` 真实会话触发（SessionStart） | ✅ 2026-09-28 · `chiaki-ng-dev`、`investment` 的 `resume` 会话，见下方记录；`startup` / `compact` 未在 keel 项目中实际观察到 |
| OpenCode v2 真实会话触发 | ✅ 2026-09-30，opencode 2.0.20 `opencode run`：`git+file://` 包安装（项目 `opencode.json` 的 `plugins`）后 `patch` 与 `shell` 均触发 `devdocs-drift`，模型原文复述提示；插件注册的 skill 可被 skill 工具加载；`skill-flag-lint` 仅验证了 patch 路径提取（未在真实会话触发）|
| `Bash` matcher 真实会话触发 | ✅ 2026-09-17，装上 2.0.1 后一次 `Bash` 调用（`echo > tmp-probe.py`）触发 `devdocs-drift`，提示正确指名该文件 |

### 已验证：`devdocs-layout` 的 SessionStart 真实触发

**验证记录**（2026-09-28，plugin 2.1.0，Claude Code 2.1.28）：从会话 jsonl 取证，两个 keel 项目
各有一次 `SessionStart:resume` 调起本 hook，退出码 0，耗时 83 / 143 ms；紧随其后出现
`hook_additional_context` 条目，说明提示已送进模型上下文：

- `chiaki-ng-dev`：「检出 3 个待分类路径（共 3 项…）」
- `investment`：「检出 18 个待分类路径、3 个分册未在主文件登记、1 个文件超 96 KiB（共 22 项…）」

`hooks.json` 的 `SessionStart` 未设 matcher，`startup` / `compact` / `clear` 走同一注册；
这三种来源在 keel 项目里尚无实际记录，若将来出现不触发，按下文分环排查。

以下为原验证步骤，保留作排查参考。

**已验证的部分**（2026-09-24，plugin 2.1.0）：脚本逻辑三输入全过；**已安装副本**
（`~/.claude/plugins/cache/ab300819-keel/keel/2.1.0/hooks/devdocs-layout`）直接调用时
静默路径与命中路径均正确；该版本的 `hooks.json` 确实注册了 `SessionStart`。

**没验到的一环**：Claude Code 是否真的在会话开始时调起它、`additionalContext` 是否送达。

⛔ **`/reload-plugins` 验不了这件事**，两个原因：① 它重载定义，不重新放 `SessionStart` 事件；
② 本仓自身没有 `docs/devdocs/`，hook 在这里必然静默（正确行为，但也意味着验不出正向路径）。

**怎么验**：在一个**有待处理项的 keel 项目**里**新开一个会话**。`tm-reborn` 稳定命中 8 项，
是现成的样本。会话开头应出现：

```
ℹ️ devdocs-layout: 检出 6 个待分类路径、2 个分册未在主文件登记（共 8 项，均为 ⚠️ 非阻断）。
要处理跑 /pipeline realign --scope=health；不处理可继续，本提示不拦任何操作。
```

- **出现** ⇒ 整条链通，把本表该行改 ✅ 并记日期与所用项目。
- **不出现** ⇒ ⛔ 不要直接改 hook。先分清是哪一环：`SessionStart` 没被调起 / 调起了但脚本静默 /
  脚本输出了但 `additionalContext` 没送达。可在脚本首行临时加 `echo "$(date) fired" >> /tmp/devdocs-layout.log`
  区分前两者——日志有行说明被调起了，问题在脚本或送达；日志无行说明事件压根没到。
