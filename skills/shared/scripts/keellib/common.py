"""task / backlog 命令共用：JSON 序列化与写会话。"""
from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from . import store
from .render import render_all


def dump(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


@contextmanager
def write_session(project: store.Project) -> Iterator[None]:
    project.require_writable()
    with project.lock():
        store.cleanup_tmp(project)
        store.require_intact(project)
        yield
        render_all(project)
