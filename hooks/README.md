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
| OpenCode | `hooks/opencode-plugin.js` | 该端**不读 hooks.json**，只加载 `plugins/*.js`；且**没有 additionalContext 通道**，只能在 `tool.execute.after` 里把消息追加进 `output.output`（[docs](https://opencode.ai/docs/plugins)）|

OpenCode 安装：

```bash
ln -s <keel>/hooks/opencode-plugin.js ~/.config/opencode/plugins/keel.js
```

| hook | 作用域 | 触发 | 干什么 |
|---|---|---|---|
| `devdocs-drift` | **用户 keel 项目** | PostToolUse `Edit\|Write\|NotebookEdit\|Bash` | 改了代码但 `docs/devdocs/` 没动 → 一行提示。5 分钟冷却 |
| `skill-flag-lint` | **skill 库自身** | PostToolUse `Edit\|Write\|NotebookEdit`，且编辑的是 `skills/**/*.md` | 跑 `health-lint.py --skills-dir` 的 `flag/dangling-reference`。2 分钟冷却 |

⚠️ **两者 matcher 不同，是有意的。** `devdocs-drift` 看 `git status`，与用哪个工具改的无关，所以必须覆盖 `Bash`——否则 shell 改文件（auto 模式、脚本化编辑、CI）全程不触发。`skill-flag-lint` 依赖 `tool_input.file_path`，`Bash` 调用没有该字段，加进去也只是空转，故不加。

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
| OpenCode 真实会话触发 | ⬜ 未跑 |
| `Bash` matcher 真实会话触发 | ✅ 2026-09-17，装上 2.0.1 后一次 `Bash` 调用（`echo > tmp-probe.py`）触发 `devdocs-drift`，提示正确指名该文件 |
