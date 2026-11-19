"""生成台账区与 backlog.md。"""
from __future__ import annotations

import os
from typing import Any

from . import store
from .store import BACKLOG_MD, BEGIN, END, REGION_KEY, TASKS_MD, KeelError, Project, region_text

__all__ = ["BEGIN", "END", "REGION_KEY", "region_text", "ledger_region", "backlog_md", "render_all"]
GROUPS = ("parked", "reactivated", "closed", "superseded")


def _num(tid: str) -> int:
    return int(tid.rpartition("-")[2])


def _cell(v: Any) -> str:
    return str(v).replace("|", "\\|") if v else "—"


def ledger_region(tasks: dict[str, dict[str, Any]]) -> str:
    live = sorted((t for t in tasks.values() if t.get("status") != "已归档"), key=lambda t: _num(t["id"]))
    rows = ["| 编号 | 标题 | 状态 | profile | 依赖 | 里程碑 | 记录 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for t in live:
        rec = f"[记录]({t['record']})" if t.get("record") else None
        cells = [t["id"], t.get("title"), t.get("status"), t.get("review_profile"),
                 ", ".join(t.get("depends_on") or []), t.get("milestone"), rec]
        rows.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    n = len(tasks) - len(live)
    rows.append("")
    rows.append(f"已归档 {n} 张，定义见 [archive/04-dev-tasks-archive.md](archive/04-dev-tasks-archive.md)")
    return "\n" + "\n".join(rows) + "\n"


def backlog_md(entries: dict[str, dict[str, Any]]) -> str:
    out = ["---", "generated_by: keel", "spec_version: backlog.v3", "---", "", "# Backlog", "",
           "本文件由 keel 生成，改状态用 `keel backlog …`", "", "## Index"]
    for g in GROUPS:
        items = sorted((e for e in entries.values() if e.get("status") == g),
                       key=lambda e: (e["source_id"], e["entry_no"]))
        if not items:
            continue
        out += ["", f"### {g}", ""]
        for e in items:
            line = f"- {e['source_id']}#{e['entry_no']} · " + " ".join(str(e.get("note") or "").split())
            if e.get("detail"):
                line += f" · [详情]({e['detail']})"
            out.append(line)
    return "\n".join(out) + "\n"


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def render_all(project: Project) -> None:
    """调用方须已持有 project.lock()。内容没变不重写。"""
    from . import backlog, tasks  # 延迟导入：它们经 common 依赖本模块

    man = project.manifest()
    text = _read(os.path.join(project.root, TASKS_MD))
    if text is not None:
        if region_text(text) is None:
            raise KeelError("04-dev-tasks.md 缺少 keel 生成区标记，先跑 `keel migrate`", 3)
        region = ledger_region(tasks.load_all(project)[0])
        i, j = text.find(BEGIN) + len(BEGIN), text.find(END)
        new = text[:i] + region + text[j:]
        if new != text:
            store.write_atomic(project, TASKS_MD, new.encode("utf-8"), record=False)
        if man.get(REGION_KEY) != store.blob_sha(region.encode("utf-8")):
            store.record_region(project, REGION_KEY, region)
    entries = backlog.load_all(project)[0]
    if entries:
        data = backlog_md(entries).encode("utf-8")
        cur = _read(os.path.join(project.root, BACKLOG_MD))
        if cur is None or cur.encode("utf-8") != data or man.get(BACKLOG_MD) != store.blob_sha(data):
            store.write_atomic(project, BACKLOG_MD, data)
