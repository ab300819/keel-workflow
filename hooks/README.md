# hooks

⚠️ **仅在 Claude Plugin 安装路径下生效。** `npx skills add` 只复制单个 skill 目录，
不带根级 `hooks/`（实测 `skills@1.5.26` `dist/cli.mjs:2220,2236`）。
⇒ hook 只能是**加速器**，规则本身必须仍写在 skill 正文里，⛔ 不得把门挪进 hook。

`hooks/hooks.json` 是 Claude Code 的默认发现路径，⛔ 不需要在 `plugin.json` 里声明。

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
  （Cursor 用 `additional_context`，Copilot CLI 用顶层 `additionalContext`——本目录暂只做 Claude Code）。

## 状态

⚠️ **两个都是试验件，均未在真实会话中跑过** ——本仓当前不在 `enabledPlugins` 里。
验不过就删，⛔ 不要在它们之上加功能。背景见
[docs/audits/2026-08-28-skill-soft-trigger-miss-brief.md](../docs/audits/2026-08-28-skill-soft-trigger-miss-brief.md)。
