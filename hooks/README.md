# hooks

⚠️ **只在插件安装路径下生效。** ⇒ hook 只能是**加速器**，规则本身必须仍写在 skill 正文里，
⛔ 不得把门挪进 hook。

## 三端适配

**公共检查逻辑一份**（`devdocs-drift` / `skill-flag-lint`，按 `hookSpecificOutput.additionalContext`
契约打印 JSON），适配层三个里只需要两份文件：

| 端 | 适配层 | 依据 |
|---|---|---|
| Claude Code | `hooks/hooks.json` | 插件根下的默认发现路径，⛔ 不需要在 `plugin.json` 里声明 |
| Codex CLI | **同一个 `hooks/hooks.json`** | Codex 插件默认也读插件根的 `hooks/hooks.json`，事件名 / handler 字段 / 输出契约与 Claude Code 同形；`${CLAUDE_PLUGIN_ROOT}` 作为 `PLUGIN_ROOT` 的 legacy 别名仍受支持（[docs](https://learn.chatgpt.com/docs/hooks)）|
| OpenCode | `hooks/opencode-plugin.js` | 该端**不读 hooks.json**，只加载 `plugins/*.js`；且**没有 additionalContext 通道**，只能在 `tool.execute.after` 里把消息追加进 `output.output`（[docs](https://opencode.ai/docs/plugins)）|

OpenCode 安装：

```bash
ln -s <keel>/hooks/opencode-plugin.js ~/.config/opencode/plugins/keel.js
```

| hook | 作用域 | 触发 | 干什么 |
|---|---|---|---|
| `devdocs-drift` | **用户 DevDocs 项目** | PostToolUse `Edit\|Write\|NotebookEdit` | 改了代码但 `docs/devdocs/` 没动 → 一行提示。5 分钟冷却 |
| `skill-flag-lint` | **skill 库自身** | 同上，且编辑的是 `skills/**/*.md` | 跑 `health-lint.py --skills-dir` 的 `flag/dangling-reference`。2 分钟冷却 |

两者都在不适用时**静默 exit 0**，互不干扰。

## 写 hook 的坑（实测踩过）

- ⛔ **不要用 `timeout(1)`** —— macOS 默认没有。`timeout 1 cat || true` 会静默吞掉
  整个 stdin payload，hook 变成永远不触发且没有任何错误。用 bash 内建读。
- PostToolUse **每次工具调用都触发**，不加冷却必然变噪声。
- 输出契约：`{"hookSpecificOutput":{"hookEventName":"...","additionalContext":"..."}}`
  Claude Code 与 Codex 共用这一份；OpenCode 由 `opencode-plugin.js` 解析出 `additionalContext`
  再追加进工具结果（该端无等价通道）。

## 状态

⚠️ **两个都是试验件。** 脚本本身已用构造 payload 逐条实测（见下），但**三端真实会话触发尚未各跑一次**。
验不过就删，⛔ 不要在它们之上加功能。背景见
[docs/audits/2026-08-28-skill-soft-trigger-miss-brief.md](../docs/audits/2026-08-28-skill-soft-trigger-miss-brief.md)。
