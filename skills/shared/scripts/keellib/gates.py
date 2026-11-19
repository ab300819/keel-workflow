"""K1–K4 判定、档位、命中记录与 check / gate / state accept 命令。"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter, namedtuple
from typing import Any

from . import store, tasks
from .common import dump, write_session
from .store import KeelError, Project

LINE_CAP = 500
SIZE_CAP = 98304
DEFAULT_LEVELS = {"K1": "block", "K2": "block", "K3": "block", "K4": "block"}
CARRIER_GLOBS = ("docs/devdocs/04-dev-tasks*.md", "docs/devdocs/backlog.md", "docs/devdocs/00-context.md",
                 ".claude/rules/devdocs-state.md")
_CARRIER_RE = re.compile(r"docs/devdocs/04-dev-tasks[^/]*\.md|docs/devdocs/backlog\.md|docs/devdocs/00-context\.md"
                         r"|\.claude/rules/devdocs-state\.md")
GATES_REL = store.STATE_REL + "/gates.json"
LOG_REL = ".keel/gate-log.jsonl"
FIX = {
    "K1": "用 `keel task|backlog` 命令改，或人工确认后 `! .keel/bin/keel state accept`",
    "K2": "生成区只由 keel 写，改回后跑 `keel render`",
    "K3": "超长内容移到 `audit/T-xxx/` 或 `backlog/<id>.md`，此处留链接",
    "K4": "先归档或拆分（`/sync --archive`），本文件只能改小",
}
Finding = namedtuple("Finding", "gate path line detail")


def is_carrier(relpath: str) -> bool:
    return bool(_CARRIER_RE.fullmatch(relpath))


def line_too_long(line: str) -> bool:
    return len(line) > LINE_CAP


def check_k1k2(project: Project) -> list[Finding]:
    return [Finding("K1", v, None, "状态文件被非工具改动") if v.startswith(store.STATE_REL + "/")
            else Finding("K2", v, None, "生成区被手改") for v in store.integrity_violations(project)]


def check_k3(project: Project, relpath: str, text: str) -> list[Finding]:
    old = store.head_text(project, relpath)
    seen = Counter(old.splitlines() if old is not None else [])
    out = []
    for i, ln in enumerate(text.splitlines(), 1):
        if seen[ln] > 0:  # 与 HEAD 某行相同：未改动，按多重集合消耗
            seen[ln] -= 1
        elif line_too_long(ln):
            out.append(Finding("K3", relpath, i, f"新增或改动的行有 {len(ln)} 字符（上限 {LINE_CAP}）"))
    return out


def check_k4(project: Project, relpath: str, size: int) -> list[Finding]:
    old = store.head_text(project, relpath)
    if size > SIZE_CAP and (old is None or size > len(old.encode("utf-8"))):
        return [Finding("K4", relpath, None, f"文件 {size} 字节（上限 {SIZE_CAP}）")]
    return []


def level(project: Project, gate: str) -> str:
    try:
        with open(os.path.join(project.root, GATES_REL), encoding="utf-8") as f:
            lv = json.load(f)[gate]["level"]
        if lv in ("block", "warn", "off"):
            return str(lv)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return DEFAULT_LEVELS[gate]


def log_hit(project: Project, gate: str, lv: str, result: str, client: str, tool: str, path: str, detail: str) -> None:
    project.check_links()
    os.makedirs(project.keel_dir, exist_ok=True)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "gate": gate, "level": lv, "result": result,
           "client": client, "tool": tool, "path": path, "detail": detail}
    with open(os.path.join(project.root, LOG_REL), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def apply_levels(project: Project, findings: list[Finding], client: str, tool: str) -> tuple[list[Finding], list[Finding]]:
    blocks: list[Finding] = []
    warns: list[Finding] = []
    for f in findings:
        lv = level(project, f.gate)
        log_hit(project, f.gate, lv, "skip" if lv == "off" else lv, client, tool, f.path, f.detail)
        if lv == "block":
            blocks.append(f)
        elif lv == "warn":
            warns.append(f)
    return blocks, warns


def format_findings(findings: list[Finding]) -> str:
    return "\n".join(f"{f.gate} `{f.path}`{'' if f.line is None else f':{f.line}'}：{f.detail}；{FIX[f.gate]}"
                     for f in findings)


def _changed_carriers(project: Project) -> list[str]:
    cands = [r for g in CARRIER_GLOBS for r in _expand(project, g)]
    if not cands or store._git(project.root, "rev-parse", "--verify", "HEAD") is None:
        return cands
    out = store._git(project.root, "diff", "--name-only", "-z", "HEAD", "--", *cands) or b""
    new = store._git(project.root, "ls-files", "-z", "--others", "--exclude-standard", "--", *cands) or b""
    names = set((out + new).decode("utf-8", "replace").split("\0"))
    return [c for c in cands if c in names]


def _expand(project: Project, glob: str) -> list[str]:
    d, pat = os.path.split(glob)
    rx = re.compile(re.escape(pat).replace(r"\*", ".*"))
    full = os.path.join(project.root, d)
    return [d + "/" + n for n in sorted(os.listdir(full)) if rx.fullmatch(n)] if os.path.isdir(full) else []


def run_check(project: Project, staged: bool, paths: list[str] | None, client: str = "cli", tool: str = "check") -> int:
    scope: set[str] | None = None
    if staged:
        out = store._git(project.root, "diff", "--cached", "--name-only", "-z") or b""
        scope = {p for p in out.decode("utf-8", "replace").split("\0") if p}
    elif paths:
        scope = {os.path.relpath(os.path.join(project.root, p), project.root) for p in paths}
    files = [p for p in (sorted(scope) if scope is not None else _changed_carriers(project)) if is_carrier(p)]
    findings: list[Finding] = []
    for rel in files:
        try:
            with open(os.path.join(project.root, rel), "rb") as f:
                data = f.read()
        except OSError:
            continue
        findings += check_k3(project, rel, data.decode("utf-8", "replace")) + check_k4(project, rel, len(data))
    if project.is_migrated():
        findings += [f for f in check_k1k2(project) if scope is None or f.path.split("#")[0] in scope]
    blocks, warns = apply_levels(project, findings, client, tool)
    if blocks or warns:
        print(format_findings(blocks + warns), file=sys.stderr)
    return 1 if blocks else 0


def gate_set(project: Project, gate: str, lv: str, reason: str) -> None:
    if gate not in DEFAULT_LEVELS:
        raise KeelError(f"{gate} 不可调：只能是 K1–K4（K5 不可调）", 2)
    if lv not in ("block", "warn", "off"):
        raise KeelError(f"档位 {lv!r} 不对：只能是 block|warn|off", 2)
    with write_session(project):
        try:
            with open(os.path.join(project.root, GATES_REL), encoding="utf-8") as f:
                cur: dict[str, Any] = json.load(f)
        except FileNotFoundError:
            cur = {}
        cur[gate] = {"level": lv, "reason": reason, "set_at": time.strftime("%Y-%m-%d")}
        store.write_atomic(project, GATES_REL, dump(cur))
        log_hit(project, gate, lv, "gate-set", "cli", "gate set", GATES_REL, reason)


def report(project: Project, since: str | None) -> str:
    hits: dict[str, list[str]] = {}
    try:
        with open(os.path.join(project.root, LOG_REL), encoding="utf-8") as f:
            recs = [json.loads(x) for x in f if x.strip()]
    except FileNotFoundError:
        recs = []
    for r in recs:
        if r["result"] in ("gate-set", "accept") or (since and r["ts"][:10] < since):
            continue
        hits.setdefault(r["gate"], []).append(r["path"])
    lines = [f"{g} {len(ps)}  {' '.join(sorted(set(ps)))}" for g, ps in sorted(hits.items())]
    cnt = Counter(t["derived_from"] for t in tasks.load_all(project)[0].values() if t.get("derived_from"))
    return "\n".join(lines + ["每卡派生数"] + [f"{k} {n}" for k, n in cnt.most_common(10)])


def read_tty(prompt: str) -> str:
    try:
        fd = os.open("/dev/tty", os.O_RDWR)
    except OSError:
        raise KeelError("打不开 /dev/tty，只能由人在终端确认；请输入 `! .keel/bin/keel state accept`", 3) from None
    with os.fdopen(fd, "r+") as t:
        t.write(prompt)
        t.flush()
        return t.readline().strip()


def accept(project: Project) -> None:
    project.require_writable()
    try:
        bad = store.integrity_violations(project)
    except KeelError as e:  # manifest 损坏时仍允许人工重建
        bad = [str(e)]
    items = "\n".join("  " + b for b in bad) or "  （当前无违规项，将重建 manifest）"
    if read_tty(f"将把以下状态接受为当前基线：\n{items}\n确认请输入 accept：") != "accept":
        raise KeelError("未输入 accept，状态未改动", 1)
    with project.lock():
        project.save_manifest(store._current_blobs(project))
        log_hit(project, "state", "-", "accept", "cli", "state accept", store.STATE_REL, ";".join(bad))
