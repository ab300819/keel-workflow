"""hook 输入解析（Claude Code / Codex / OpenCode 三端形状）与 Pre/Post 判定。"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

from . import gates, store
from .gates import Finding
from .store import Project

_PATCH_RE = re.compile(r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+?)\s*$", re.M)
# 只能人执行：state accept 与把档位放宽到 warn|off。只认命令位置上的 keel / keel.py（可带环境变量赋值、python3/bash 前缀），
# grep、commit -m 里提到不算。shortcut: 变量拼接、eval、sh -c "…" 等混淆写法拦不住，靠 /dev/tty 与 pre-commit 兜底
_HUMAN_RE = re.compile(r"(?:^|[;&|`\n]|\$\()\s*(?:\w+=\S*\s+)*(?:(?:\S*/)?(?:python3?|bash|sh)\s+)?"
                       r"(?:\S*/)?keel(?:\.py)?\s+(?:--root\s+\S+\s+)?(state\s+accept|gate\s+set\s+\S+\s+(?:warn|off))\b")
SHELL_TOOLS = ("Bash", "shell")


def _strings(payload: dict[str, Any]) -> list[str]:
    ti = payload.get("tool_input")
    vals = list(ti.values()) if isinstance(ti, dict) else [ti]
    return [x for v in vals for x in (v if isinstance(v, list) else [v]) if isinstance(x, str)]


def edited_paths(payload: dict[str, Any], root: str) -> list[str]:
    ti = payload.get("tool_input")
    ti = ti if isinstance(ti, dict) else {}
    raw = [ti[k] for k in ("file_path", "filePath", "path", "notebook_path") if isinstance(ti.get(k), str) and ti[k]][:1]
    if not raw:  # Codex apply_patch / OpenCode patchText：从补丁头取路径
        raw = [m for s in _strings(payload) for m in _PATCH_RE.findall(s)]
    out: list[str] = []
    for p in raw:
        full = os.path.join(root, p)  # 上级目录取 realpath：消掉 ..、/tmp→/private/tmp 这类别名
        rel = os.path.relpath(os.path.join(os.path.realpath(os.path.dirname(full)), os.path.basename(full)), root)
        if rel not in out:
            out.append(rel)
    return out


def client(payload: dict[str, Any]) -> str:
    return os.environ.get("KEEL_CLIENT") or ("codex" if payload.get("tool_name") in ("apply_patch", "shell") else "claude")


def _key(path: str) -> str:
    """比较用：解开符号链接（含末级），并按大小写不敏感比较（macOS 默认文件系统 State/ 与 state/ 是同一目录）。"""
    return os.path.normcase(os.path.realpath(path)).casefold()


def _out(event: str, **kw: str) -> str:
    return json.dumps({"hookSpecificOutput": {"hookEventName": event, **kw}}, ensure_ascii=False)


def _deny(reason: str) -> str:
    return _out("PreToolUse", permissionDecision="deny", permissionDecisionReason=reason)


def pre(project: Project, payload: dict[str, Any]) -> str:
    tool, cl = str(payload.get("tool_name") or ""), client(payload)
    if tool in SHELL_TOOLS:  # shell 不按路径拦（Post 兜），只拦模型代人执行的命令；不可调档
        m = next((m for m in map(_HUMAN_RE.search, _strings(payload)) if m), None)
        if m is None:
            return ""
        cmd = ".keel/bin/keel " + " ".join(m.group(1).split()) + ("" if m.group(1).startswith("state") else " …")
        gates.log_hit(project, "human", "block", "block", cl, tool, "", m.group(0))
        return _deny(f"{store.HUMAN_ONLY} `{cmd}`")
    findings: list[Finding] = []
    for rel in edited_paths(payload, project.root):
        key = _key(os.path.join(project.root, rel))
        if any(key == d or key.startswith(d + os.sep) for d in (_key(project.state_dir), _key(project.keel_dir))):
            findings.append(Finding("K1", rel, None, "状态文件只能由 keel 写"))
        elif key == _key(os.path.join(project.root, store.BACKLOG_MD)) and project.is_migrated():
            findings.append(Finding("K2", rel, None, "backlog.md 是生成文件"))  # 未迁移项目的 backlog.md 仍是手写文档
    blocks, warns = gates.apply_levels(project, findings, cl, tool)
    if blocks:
        return _deny(gates.format_findings(blocks))
    return _out("PreToolUse", additionalContext=gates.format_findings(warns)) if warns else ""


def post(project: Project, payload: dict[str, Any]) -> str:
    tool = str(payload.get("tool_name") or "")
    blocks, warns = gates.apply_levels(project, gates.collect(project, None), client(payload), tool)
    if blocks:
        return json.dumps({"decision": "block", "reason": gates.format_findings(blocks + warns)}, ensure_ascii=False)
    return _out("PostToolUse", additionalContext=gates.format_findings(warns)) if warns else ""


def main(root: str | None, event: str) -> int:
    """hook 入口：任何内部错误都静默放行（第 1、3 层兜底），能写日志就记 hook-error。"""
    project = None
    try:
        project = Project.find(root or os.getcwd())
        payload = json.loads(sys.stdin.read() or "{}")
        if event == "paths":
            out = "\n".join(edited_paths(payload, project.root))
        else:
            out = pre(project, payload) if event == "pre" else post(project, payload)
        if out:
            print(out)
    except Exception as e:  # hook 层绝不能让客户端崩
        log_error(project, event, e)
    return 0


def log_error(project: Project | None, event: str, e: BaseException) -> None:
    try:
        if project is not None:
            gates.log_hit(project, "hook-error", "-", "hook-error", client({}), event, "", repr(e)[:200])
    except Exception:
        pass
