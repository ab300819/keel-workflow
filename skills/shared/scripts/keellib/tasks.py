"""task 子命令的业务逻辑。"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from . import schema, store
from .render import render_all
from .store import KeelError, Project

TASKS_REL = store.STATE_REL + "/tasks"
_ID_RE = re.compile(r"^T-(\d+)\.json$")
# CLI 选项 -> 字段；depends 与 exploration-mode 另行转换
SET_FIELDS = ("status", "profile", "depends", "milestone", "layer", "title", "batch", "due", "pending_reason",
              "ext_review_state", "skip_trace_reason", "exploration_mode", "profile_downgrade_reason", "record")


def _dump(task: dict[str, Any]) -> bytes:
    return (json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_all(project: Project) -> tuple[dict[str, dict[str, Any]], list[str]]:
    tasks: dict[str, dict[str, Any]] = {}
    bad: list[str] = []
    d = os.path.join(project.root, TASKS_REL)
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not name.endswith(".json") or name.startswith("."):
            continue
        rel = TASKS_REL + "/" + name
        try:
            with open(os.path.join(d, name), encoding="utf-8") as f:
                t = json.load(f)
            if not isinstance(t, dict) or not isinstance(t.get("id"), str):
                raise ValueError
            tasks[t["id"]] = t
        except (ValueError, OSError):
            bad.append(rel)
    return tasks, bad


@contextmanager
def _write_session(project: Project) -> Iterator[None]:
    project.require_writable()
    with project.lock():
        store.cleanup_tmp(project)
        store.require_intact(project)
        yield
        render_all(project)


def _save(project: Project, task: dict[str, Any], known: set[str]) -> None:
    errs = schema.validate_task(task, known)
    if errs:
        raise KeelError(f"{task['id']} 校验失败，未写入：\n" + "\n".join(errs), 1)
    store.write_atomic(project, f"{TASKS_REL}/{task['id']}.json", _dump(task))


def _csv(v: str) -> list[str]:
    return [x.strip() for x in v.split(",") if x.strip()]


def add(project: Project, title: str, source: str, derived_from: str | None = None, profile: str | None = None,
        depends: str | None = None, milestone: str | None = None, layer: str | None = None) -> str:
    with _write_session(project):
        tasks, _ = load_all(project)
        d = os.path.join(project.root, TASKS_REL)
        nums = [int(m.group(1)) for n in (os.listdir(d) if os.path.isdir(d) else []) if (m := _ID_RE.match(n))]
        tid = f"T-{max(nums, default=0) + 1}"
        extra: dict[str, Any] = {"derived_from": derived_from, "milestone": milestone, "layer": layer}
        if profile:
            extra["review_profile"] = profile
        if depends:
            extra["depends_on"] = _csv(depends)
        _save(project, schema.new_task(tid, title, source, **extra), set(tasks))
    return tid


def _mutate(project: Project, tid: str, fn: Callable[[dict[str, Any]], None]) -> None:
    with _write_session(project):
        tasks, _ = load_all(project)
        if tid not in tasks:
            raise KeelError(f"任务 {tid} 不存在", 1)
        t = tasks[tid]
        fn(t)
        _save(project, t, set(tasks))


def set_fields(project: Project, tid: str, opts: dict[str, str]) -> None:
    def fn(t: dict[str, Any]) -> None:
        for k, v in opts.items():
            if k == "depends":
                t["depends_on"] = _csv(v)
            elif k == "profile":
                t["review_profile"] = v
            elif k == "exploration_mode":
                if v not in ("true", "false"):
                    raise KeelError("--exploration-mode 只能是 true 或 false", 2)
                t[k] = v == "true"
            else:
                t[k] = v if v != "" else None
    _mutate(project, tid, fn)


def commit(project: Project, tid: str, ref: str, note: str) -> None:
    _mutate(project, tid, lambda t: t["commits"].append({"ref": ref, "note": note}))


def archive(project: Project, tid: str) -> None:
    _mutate(project, tid, lambda t: t.update(status="已归档"))


def get(project: Project, tid: str) -> str:
    tasks, _ = load_all(project)
    if tid not in tasks:
        raise KeelError(f"任务 {tid} 不存在", 1)
    return _dump(tasks[tid]).decode("utf-8").rstrip("\n")


def list_lines(project: Project, status: str | None, fields: str | None) -> list[str]:
    tasks, bad = load_all(project)
    want = set(_csv(status)) if status else None
    cols = _csv(fields) if fields else None
    lines = []
    for t in sorted(tasks.values(), key=lambda t: (len(t["id"]), t["id"])):
        if want and t.get("status") not in want:
            continue
        vals = [t.get(c) for c in cols] if cols else [t["id"], t.get("status"), t.get("title")]
        lines.append(" · ".join("" if v is None else str(v) for v in vals))
    lines.append(f"# 扫描 {len(tasks) + len(bad)} 个文件，无法识别 {len(bad)} 个：" + "、".join(bad))
    return lines
