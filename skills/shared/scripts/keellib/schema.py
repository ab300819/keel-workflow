"""任务 / backlog 字段定义与校验（K5）。纯函数，无 I/O。"""
from __future__ import annotations

import re
from typing import Any

TASK_STATUSES = ("待开发", "进行中", "review_pending", "已完成", "已归档")
REVIEW_PROFILES = ("fast", "guarded", "audit")
PENDING_REASONS = ("deferred-fast", "deferred-guarded")
EXT_REVIEW_STATES = ("EXT_REVIEWED", "EXT_UNRESOLVED", "EXT_BLOCKED")
BACKLOG_STATUSES = ("parked", "reactivated", "closed", "superseded")
SOURCE_PREFIXES = ("F", "US", "AC", "T", "INS", "BUG", "FR", "NFR", "M")
TEXT_CAPS = {"title": 80, "skip_trace_reason": 200, "profile_downgrade_reason": 200, "note": 200,
             "milestone": 80, "layer": 80, "record": 200}

TASK_ID = re.compile(r"T-\d+")
COMMIT_REF = re.compile(r"[^@\s]+@[0-9a-f]{7,40}")
SOURCE_ID = re.compile(r"(" + "|".join(SOURCE_PREFIXES) + r")-\d+[a-z]?")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

_TASK_DEFAULTS: dict[str, Any] = {
    "schema": "keel.task.v1", "id": None, "title": None, "status": "待开发", "source": None,
    "derived_from": None, "review_profile": "fast", "depends_on": [], "milestone": None,
    "layer": None, "commits": [], "batch": None, "due": None, "pending_reason": None,
    "ext_review_state": None, "skip_trace_reason": None, "exploration_mode": False,
    "profile_downgrade_reason": None, "record": None,
}
_BACKLOG_DEFAULTS: dict[str, Any] = {
    "schema": "keel.backlog.v1", "source_id": None, "entry_no": None, "status": "parked",
    "created_at": None, "created_by_skill": None, "note": None, "detail": None,
    "related_ids": [], "target_flow": None, "target_id": None, "reason": None,
    "superseded_by": None, "updated_at": None,
}


def new_task(id: str, title: str, source: str, **fields: Any) -> dict[str, Any]:
    t = {**_TASK_DEFAULTS, "id": id, "title": title, "source": source}
    t["depends_on"], t["commits"] = [], []
    t.update(fields)
    return t


def new_backlog(source_id: str, entry_no: int, created_by_skill: str, note: str, created_at: str) -> dict[str, Any]:
    e = {**_BACKLOG_DEFAULTS, "source_id": source_id, "entry_no": entry_no,
         "created_by_skill": created_by_skill, "note": note, "created_at": created_at}
    e["related_ids"] = []
    e["detail"] = f"backlog/{source_id}-{entry_no}.md"
    return e


def _err(field: str, problem: str, fix: str) -> str:
    return f"`{field}`：{problem}；{fix}"


def _check_common(d: dict[str, Any], defaults: dict[str, Any], schema_v: str, errs: list[str]) -> None:
    for k in d:
        if k not in defaults:
            errs.append(_err(k, "不在字段定义内", "删除该字段或改正拼写，字段见 keel schema"))
    if d.get("schema") != schema_v:
        errs.append(_err("schema", f"应为 {schema_v}", "改回该值"))


def _enum(d: dict[str, Any], f: str, allowed: tuple[str, ...], errs: list[str], nullable: bool = False) -> None:
    v = d.get(f)
    if v is None and nullable:
        return
    if v not in allowed:
        errs.append(_err(f, f"取值 {v!r} 不合法", "改为 " + " / ".join(allowed)))


def _text(d: dict[str, Any], f: str, errs: list[str], required: bool = False) -> None:
    v = d.get(f)
    if v is None or v == "":
        if required:
            errs.append(_err(f, "必填且不能为空", "补上内容"))
        return
    if not isinstance(v, str):
        errs.append(_err(f, "应为字符串", "改为字符串"))
    elif any(c in v for c in ("\r", "\n", "<!--")):
        errs.append(_err(f, "含换行或 `<!--`，会破坏生成的表格与标记", "改为单行纯文本，细节放 detail / audit 记录"))
    elif f in TEXT_CAPS and len(v) > TEXT_CAPS[f]:
        errs.append(_err(f, f"{len(v)} 字，超过上限 {TEXT_CAPS[f]}", "精简到上限内，细节放 detail / audit 记录"))


def validate_task(task: dict[str, Any], known_ids: set[str]) -> list[str]:
    errs: list[str] = []
    _check_common(task, _TASK_DEFAULTS, "keel.task.v1", errs)
    for f in ("id", "title", "source"):
        _text(task, f, errs, required=True)
    if not (isinstance(task.get("id"), str) and TASK_ID.fullmatch(task["id"])):
        errs.append(_err("id", f"{task.get('id')!r} 格式不对", "改为 T-<数字>"))
    for f in ("skip_trace_reason", "profile_downgrade_reason", "milestone", "layer", "record"):
        _text(task, f, errs)
    _enum(task, "status", TASK_STATUSES, errs)
    _enum(task, "review_profile", REVIEW_PROFILES, errs)
    _enum(task, "pending_reason", PENDING_REASONS, errs, nullable=True)
    _enum(task, "ext_review_state", EXT_REVIEW_STATES, errs, nullable=True)
    if task.get("status") == "review_pending":
        for f in ("batch", "due", "pending_reason"):
            if not task.get(f):
                errs.append(_err(f, "status=review_pending 时必填", "补上该字段，或先改 status"))
    if task.get("review_profile") == "audit" and task.get("status") == "已完成" and not task.get("ext_review_state"):
        errs.append(_err("ext_review_state", "audit 档任务已完成必须有外部审查结论", "先跑外部审查并填 " + " / ".join(EXT_REVIEW_STATES)))
    deps = task.get("depends_on") or []
    for d in deps if isinstance(deps, list) else []:
        if d == task.get("id"):
            errs.append(_err("depends_on", f"{d} 依赖自身", "移除自身编号"))
        elif d not in known_ids:
            errs.append(_err("depends_on", f"{d} 不存在", "改为已有任务编号"))
    if not isinstance(deps, list):
        errs.append(_err("depends_on", "应为列表", "改为编号列表"))
    df = task.get("derived_from")
    if df is not None and df not in known_ids:
        errs.append(_err("derived_from", f"{df} 不存在", "改为已有任务编号或置空"))
    commits = task.get("commits") or []
    for c in commits if isinstance(commits, list) else []:
        ref = c.get("ref") if isinstance(c, dict) else None
        if not isinstance(ref, str) or not COMMIT_REF.fullmatch(ref):
            errs.append(_err("commits[].ref", f"{ref!r} 格式不对", "写成 <仓库>@<7-40位小写十六进制sha>"))
        note = c.get("note") if isinstance(c, dict) else None
        if isinstance(note, str) and len(note) > TEXT_CAPS["note"]:
            errs.append(_err("commits[].note", f"{len(note)} 字，超过上限 {TEXT_CAPS['note']}", "精简"))
    if not isinstance(commits, list):
        errs.append(_err("commits", "应为列表", "改为 {ref, note} 列表"))
    if not isinstance(task.get("exploration_mode"), bool):
        errs.append(_err("exploration_mode", "应为布尔值", "改为 true / false"))
    return errs


def validate_backlog(entry: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    _check_common(entry, _BACKLOG_DEFAULTS, "keel.backlog.v1", errs)
    sid = entry.get("source_id")
    if not isinstance(sid, str) or not SOURCE_ID.fullmatch(sid):
        errs.append(_err("source_id", f"{sid!r} 前缀或格式不对", "前缀限 " + "/".join(SOURCE_PREFIXES) + "，如 F-01、M-003"))
    n = entry.get("entry_no")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        errs.append(_err("entry_no", "应为 ≥1 的整数", "改为正整数"))
    for f in ("created_at", "updated_at"):
        v = entry.get(f)
        if (v is None and f == "created_at") or (v is not None and not (isinstance(v, str) and DATE.fullmatch(v))):
            errs.append(_err(f, f"{v!r} 不是 YYYY-MM-DD", "改成日期"))
    _text(entry, "created_by_skill", errs, required=True)
    _text(entry, "note", errs, required=True)
    _enum(entry, "status", BACKLOG_STATUSES, errs)
    need = {"reactivated": ("target_flow", "target_id"), "closed": ("reason",), "superseded": ("superseded_by",)}
    for f in need.get(entry.get("status") or "", ()):
        if not entry.get(f):
            errs.append(_err(f, f"status={entry['status']} 时必填", "补上该字段，或先改 status"))
    return errs


_DESC = {
    "task": [
        "schema：固定 keel.task.v1",
        "id：必填，如 T-248",
        "title：必填，≤80 字",
        "status：" + " / ".join(TASK_STATUSES),
        "source：必填，来源文档，如 dev-tasks",
        "derived_from：可空，须为已有任务编号",
        "review_profile：" + " / ".join(REVIEW_PROFILES),
        "depends_on：任务编号列表，须已存在且不含自身",
        "milestone：可空，≤80 字，如 M-003",
        "layer：可空，≤80 字",
        "commits：{ref, note} 列表；ref 形如 <仓库>@<7-40位sha>，note ≤200 字",
        "batch：status=review_pending 时必填",
        "due：status=review_pending 时必填",
        "pending_reason：" + " / ".join(PENDING_REASONS) + "；status=review_pending 时必填",
        "ext_review_state：" + " / ".join(EXT_REVIEW_STATES) + "；review_profile=audit 且 status=已完成 时必填",
        "skip_trace_reason：可空，≤200 字",
        "exploration_mode：布尔",
        "profile_downgrade_reason：可空，≤200 字",
        "record：可空，≤200 字，审查记录目录，如 audit/T-248/",
    ],
    "backlog": [
        "schema：固定 keel.backlog.v1",
        "source_id：必填，前缀限 " + "/".join(SOURCE_PREFIXES) + "，如 F-01、M-003",
        "entry_no：≥1 的整数",
        "status：" + " / ".join(BACKLOG_STATUSES),
        "created_at：必填，YYYY-MM-DD",
        "created_by_skill：必填",
        "note：必填，≤200 字",
        "detail：详情文档路径，默认 backlog/<source_id>-<entry_no>.md",
        "related_ids：编号列表",
        "target_flow：status=reactivated 时必填",
        "target_id：status=reactivated 时必填",
        "reason：status=closed 时必填",
        "superseded_by：status=superseded 时必填",
        "updated_at：可空，YYYY-MM-DD",
    ],
}


def describe(kind: str) -> str:
    return "\n".join(_DESC[kind])
