"""task / backlog 命令共用：JSON 序列化与写会话。"""
from __future__ import annotations

import json
import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from . import schema, store
from .render import precheck, render_all


def dump(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


@contextmanager
def write_session(project: store.Project, regen: bool = False) -> Iterator[None]:
    """regen=True 只给 render：生成内容被手改（K2）时也放行，结束时从状态重新生成。"""
    project.require_writable()
    with project.lock():
        store.cleanup_tmp(project)
        store.require_intact(project, only_state=regen)
        store.prune_manifest(project)
        precheck(project)
        yield
        render_all(project)


def check_task_id(tid: str) -> str:
    if not schema.TASK_ID.fullmatch(tid):
        raise store.KeelError(f"编号格式不对：{tid!r}，应为 T-<数字>", 2)
    return tid


def check_anchor(anchor: str) -> str:
    sid, _, no = anchor.partition("#")
    if not (schema.SOURCE_ID.fullmatch(sid) and re.fullmatch(r"\d+", no)):
        raise store.KeelError(f"编号格式不对：{anchor!r}，应为 F-01#1 这类锚点", 2)
    return anchor
