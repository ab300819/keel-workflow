/**
 * keel OpenCode 适配层 —— 把 hooks/ 下的公共检查脚本接到 OpenCode 的 tool.execute.after。
 *
 * 检查逻辑一份不动（`devdocs-drift` / `skill-flag-lint`，它们按 Claude Code / Codex 的
 * hook 输出契约打印 JSON）；本文件只做两件事：喂输入、把 additionalContext 追加到
 * 模型能读到的地方。
 *
 * 安装：软链进 ~/.config/opencode/plugins/ 或项目的 .opencode/plugins/。
 *   ln -s <keel>/hooks/opencode-plugin.js ~/.config/opencode/plugins/keel.js
 *
 * 契约依据（官方）：
 *   - 插件目录发现与导出形状 https://opencode.ai/docs/plugins
 *   - tool.execute.after(input:{tool,sessionID,callID,args}, output:{title,output,metadata})
 *     见 @opencode-ai/plugin 的 index.d.ts；output.output 是模型读到的工具结果文本。
 */

import { execFile } from "node:child_process"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const HOOK_DIR = dirname(fileURLToPath(import.meta.url))
const EDIT_TOOLS = new Set(["edit", "write", "patch"])
// devdocs-drift 看 git status,与改动用的是哪个工具无关 → bash 改文件也要跑。
// skill-flag-lint 依赖 tool_input.file_path,bash 调用没有该字段,跑了也是空转。
const CHECKS_EDIT = ["devdocs-drift", "skill-flag-lint"]
const CHECKS_BASH = ["devdocs-drift"]

function runCheck(name, cwd, payload) {
  return new Promise((resolve) => {
    const child = execFile(
      "bash",
      [join(HOOK_DIR, name)],
      { cwd, env: { ...process.env, CLAUDE_PROJECT_DIR: cwd }, timeout: 10_000 },
      (err, stdout) => resolve(err ? "" : (stdout || "").trim()),
    )
    child.stdin.end(payload)
  })
}

/** 脚本按 Claude/Codex 契约输出；这里只取出人话那一段。 */
function extractContext(stdout) {
  if (!stdout) return ""
  try {
    return JSON.parse(stdout)?.hookSpecificOutput?.additionalContext || ""
  } catch {
    return ""
  }
}

export const KeelPlugin = async ({ directory, worktree }) => {
  const cwd = worktree || directory || process.cwd()
  return {
    "tool.execute.after": async (input, output) => {
      const checks = EDIT_TOOLS.has(input.tool)
        ? CHECKS_EDIT
        : input.tool === "bash"
          ? CHECKS_BASH
          : null
      if (!checks) return
      const payload = JSON.stringify({
        hook_event_name: "PostToolUse",
        tool_name: input.tool,
        tool_input: input.args || {},
        cwd,
      })
      const msgs = (await Promise.all(checks.map((c) => runCheck(c, cwd, payload))))
        .map(extractContext)
        .filter(Boolean)
      // OpenCode 无 additionalContext 通道：追加进工具结果，这是模型唯一会读到的位置
      if (msgs.length) output.output = `${output.output}\n\n${msgs.join("\n")}`
    },
  }
}
