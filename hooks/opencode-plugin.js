/**
 * keel OpenCode 适配层（仅 v2，v1 插件 API 不再支持）—— 做两件事：
 *   1. 把包内 skills/<name>/SKILL.md 注册进 OpenCode（ctx.skill.transform），免软链；
 *   2. 把 hooks/ 下的公共检查脚本接到 OpenCode 的 tool.hook("execute.after")。
 *
 * 检查逻辑一份不动（`devdocs-drift` / `skill-flag-lint`，它们按 Claude Code / Codex 的
 * hook 输出契约打印 JSON）；本文件只做两件事：喂输入、把 additionalContext 追加到
 * 模型能读到的地方。
 *
 * 安装：opencode plugin add github:ab300819/keel-workflow
 *   包入口由仓库根 package.json 的 main 指向本文件。
 *
 * 契约依据（官方，opencode 2.0.20 实测）：
 *   - 插件形状与发现 https://opencode.ai/v2/docs/build/plugins
 *     默认导出 { id, setup(ctx) }；Plugin.define 只是恒等函数，故不 import @opencode/plugin，
 *     软链文件无需解析依赖。
 *   - execute.after 事件见 @opencode/plugin 的 dist/promise/tool.d.ts：
 *     { tool, input, status } & ({ status:"completed", result } | { status:"error", error })；
 *     result.content（string | {type:"text",text}[]）是模型读到的工具结果文本。
 *   - 实测工具名：改文件走 `patch`（input.patchText，无 file_path），shell 走 `shell`。
 */

import { execFile } from "node:child_process"
import { readFileSync, readdirSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const HOOK_DIR = dirname(fileURLToPath(import.meta.url))
const SKILLS_DIR = join(HOOK_DIR, "..", "skills")
const EDIT_TOOLS = new Set(["edit", "write", "patch"])
// devdocs-drift 看 git status,与改动用的是哪个工具无关 → shell 改文件也要跑。
// skill-flag-lint 依赖 tool_input.file_path,shell 调用没有该字段,跑了也是空转。
const CHECKS_EDIT = ["devdocs-drift", "skill-flag-lint"]
const CHECKS_SHELL = ["devdocs-drift"]

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

/** skill-flag-lint 只认单个绝对 file_path；patch 给相对路径且可能改多个文件，优先取 skills 下的 .md。 */
function filePathOf(input = {}, cwd) {
  const direct = input.file_path || input.filePath || input.path
  if (direct) return direct
  const paths = [...String(input.patchText || "").matchAll(/^\*\*\* (?:Add|Update) File: (.+)$/gm)].map((m) => m[1].trim())
  const p = paths.find((p) => /(^|\/)skills\/.*\.md$/.test(p)) || paths[0]
  return p ? resolve(cwd, p) : ""
}

/** 读 skills/<name>/SKILL.md；无 SKILL.md 的目录（如 shared/）跳过。description 支持单行与 >/| 块。 */
function loadSkills() {
  const skills = []
  for (const dir of readdirSync(SKILLS_DIR, { withFileTypes: true })) {
    if (!dir.isDirectory()) continue
    const path = join(SKILLS_DIR, dir.name, "SKILL.md")
    let text
    try {
      text = readFileSync(path, "utf8")
    } catch {
      continue
    }
    const m = text.match(/^---\n([\s\S]*?)\n---\n?/)
    const front = m ? m[1] : ""
    const d = front.match(/^description:[ \t]*(?:[>|][+-]?[ \t]*\n((?:[ \t]+.*\n?)+)|(.*))$/m)
    const description = d ? (d[1] ? d[1].trim().split(/\s*\n\s*/).join(" ") : d[2].trim()) : undefined
    skills.push({ id: dir.name, name: dir.name, description, path, content: m ? text.slice(m[0].length) : text })
  }
  return skills
}

export default {
  id: "keel",
  async setup(ctx) {
    const cwd = ctx.location?.directory || process.cwd()
    const skills = loadSkills()
    await ctx.skill.transform((editor) => {
      for (const skill of skills) editor.add(skill)
    })
    await ctx.tool.hook("execute.after", async (event) => {
      if (event.status !== "completed") return
      const checks = EDIT_TOOLS.has(event.tool)
        ? CHECKS_EDIT
        : event.tool === "shell"
          ? CHECKS_SHELL
          : null
      if (!checks) return
      const payload = JSON.stringify({
        hook_event_name: "PostToolUse",
        tool_name: event.tool,
        tool_input: { ...(event.input || {}), file_path: filePathOf(event.input, cwd) },
        cwd,
      })
      const msgs = (await Promise.all(checks.map((c) => runCheck(c, cwd, payload))))
        .map(extractContext)
        .filter(Boolean)
      if (!msgs.length) return
      // OpenCode 无 additionalContext 通道：追加进工具结果，这是模型唯一会读到的位置
      const text = msgs.join("\n")
      const c = event.result.content
      event.result = {
        ...event.result,
        content: typeof c === "string" ? `${c}\n\n${text}` : [...(c || []), { type: "text", text }],
      }
    })
  },
}
