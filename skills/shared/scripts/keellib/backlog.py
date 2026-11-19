"""backlog 子命令的业务逻辑。锚点 F-01#1 对应文件 state/backlog/F-01-1.json。"""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import date
from typing import Any

from . import schema, store
from .common import check_anchor, dump, write_session
from .store import KeelError, Project

BACKLOG_REL = store.STATE_REL + "/backlog"


def _anchor(e: dict[str, Any]) -> str:
    return f"{e['source_id']}#{e['entry_no']}"


def _rel(anchor: str) -> str:
    return f"{BACKLOG_REL}/{anchor.replace('#', '-')}.json"


def load_all(project: Project) -> tuple[dict[str, dict[str, Any]], list[str]]:
    entries: dict[str, dict[str, Any]] = {}
    bad: list[str] = []
    d = os.path.join(project.root, BACKLOG_REL)
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not name.endswith(".json") or name.startswith("."):
            continue
        try:
            with open(os.path.join(d, name), encoding="utf-8") as f:
                e = json.load(f)
            if not isinstance(e, dict) or not isinstance(e.get("source_id"), str) or not isinstance(e.get("entry_no"), int):
                raise ValueError
            if name != _anchor(e).replace("#", "-") + ".json":
                raise ValueError
            entries[_anchor(e)] = e
        except (ValueError, OSError):
            bad.append(BACKLOG_REL + "/" + name)
    return entries, bad


def _save(project: Project, e: dict[str, Any]) -> None:
    errs = schema.validate_backlog(e)
    if errs:
        raise KeelError(f"{_anchor(e)} 校验失败，未写入：\n" + "\n".join(errs), 1)
    store.write_atomic(project, _rel(_anchor(e)), dump(e))


def _today() -> str:
    return date.today().isoformat()


def park(project: Project, source_id: str, note: str, by: str, related: str | None, append: bool) -> str:
    check_anchor(source_id + "#1")
    with write_session(project):
        entries, _ = load_all(project)
        mine = [e for e in entries.values() if e["source_id"] == source_id]
        parked = [_anchor(e) for e in mine if e.get("status") == "parked"]
        if parked and not source_id.startswith("M-") and not append:
            raise KeelError(f"{source_id} 已有 parked 条目 {parked[0]}；确认追加加 `--append`，"
                            f"要更新原条目用 `keel backlog note {parked[0]}`", 1)
        e = schema.new_backlog(source_id, max((x["entry_no"] for x in mine), default=0) + 1, by, note, _today())
        if not os.path.isfile(os.path.join(project.root, "docs", "devdocs", e["detail"])):
            e["detail"] = None
        if related:
            e["related_ids"] = [x.strip() for x in related.split(",") if x.strip()]
        _save(project, e)
    return _anchor(e)


def transition(project: Project, anchor: str, fn: Callable[[dict[str, Any]], None]) -> None:
    check_anchor(anchor)
    with write_session(project):
        entries, _ = load_all(project)
        if anchor not in entries:
            raise KeelError(f"backlog 条目 {anchor} 不存在", 1)
        e = entries[anchor]
        if e.get("status") != "parked":
            raise KeelError(f"{anchor} 当前为 {e.get('status')}，只能从 parked 迁出", 1)
        fn(e)
        e["updated_at"] = _today()
        _save(project, e)


def get(project: Project, anchor: str) -> str:
    check_anchor(anchor)
    entries, _ = load_all(project)
    if anchor not in entries:
        raise KeelError(f"backlog 条目 {anchor} 不存在", 1)
    return dump(entries[anchor]).decode("utf-8").rstrip("\n")


def list_lines(project: Project, status: str | None, fields: str | None) -> list[str]:
    entries, bad = load_all(project)
    want = {x.strip() for x in status.split(",")} if status else None
    cols = [x.strip() for x in fields.split(",") if x.strip()] if fields else None
    lines = []
    for a, e in sorted(entries.items(), key=lambda kv: (kv[1]["source_id"], kv[1]["entry_no"])):
        if want and e.get("status") not in want:
            continue
        vals = [e.get(c) for c in cols] if cols else [a, e.get("status"), e.get("note")]
        lines.append(" · ".join("" if v is None else str(v) for v in vals))
    lines.append(f"# 扫描 {len(entries) + len(bad)} 个文件，无法识别 {len(bad)} 个：" + "、".join(bad))
    return lines
