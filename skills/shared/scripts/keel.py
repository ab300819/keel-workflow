#!/usr/bin/env python3
"""keel —— 任务 / backlog 状态的唯一写入口。仅标准库，Python >= 3.9。"""
from __future__ import annotations

import argparse
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from keellib import schema, store, tasks  # noqa: E402


def cmd_init(project: store.Project) -> int:
    if project.needs_migration():
        raise store.KeelError("项目仍是 tasks.v2 / backlog.v2 文档，先执行 /pipeline realign 迁移", 3)
    with project.lock():
        if project.is_migrated():
            store.require_intact(project)
        store.cleanup_tmp(project)
        for d in ("tasks", "backlog"):
            os.makedirs(os.path.join(project.state_dir, d), exist_ok=True)
        if not project.is_migrated():
            store.write_atomic(project, store.STATE_REL + "/meta.json", b'{\n  "schema": "keel.state.v1"\n}\n')
    print("keel 状态已初始化：" + store.STATE_REL)
    return 0


def cmd_task(project: store.Project, a: argparse.Namespace) -> int:
    k = a.task_cmd
    if k == "add":
        print(tasks.add(project, a.title, a.source, a.derived_from, a.profile, a.depends, a.milestone, a.layer))
    elif k == "set":
        opts = {f: getattr(a, f) for f in tasks.SET_FIELDS if getattr(a, f) is not None}
        if not opts:
            raise store.KeelError("至少给一个要改的字段，如 --status", 2)
        tasks.set_fields(project, a.id, opts)
    elif k == "commit":
        tasks.commit(project, a.id, a.ref, a.note)
    elif k == "archive":
        tasks.archive(project, a.id)
    elif k == "get":
        print(tasks.get(project, a.id))
    else:
        print("\n".join(tasks.list_lines(project, a.status, a.fields)))
    return 0


def self_test() -> int:
    suite = unittest.defaultTestLoader.discover(os.path.join(HERE, "tests"), top_level_dir=os.path.join(HERE, "tests"))
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="keel")
    ap.add_argument("--root", help="项目根（默认：当前目录所在 git 仓库根）")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("init", help="初始化 state/ 与 manifest")
    sp = sub.add_parser("schema", help="打印任务 / backlog 字段定义")
    sp.add_argument("kind", choices=["task", "backlog"])
    tp = sub.add_parser("task", help="任务增改归档查询").add_subparsers(dest="task_cmd", required=True)
    p = tp.add_parser("add")
    p.add_argument("--title", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--derived-from")
    p.add_argument("--profile")
    p.add_argument("--depends")
    p.add_argument("--milestone")
    p.add_argument("--layer")
    p = tp.add_parser("set")
    p.add_argument("id")
    for f in tasks.SET_FIELDS:
        p.add_argument("--" + f.replace("_", "-"), dest=f)
    p = tp.add_parser("commit")
    p.add_argument("id")
    p.add_argument("ref")
    p.add_argument("--note", required=True)
    tp.add_parser("archive").add_argument("id")
    tp.add_parser("get").add_argument("id")
    p = tp.add_parser("list")
    p.add_argument("--status")
    p.add_argument("--fields")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        return 2
    if args.cmd == "schema":
        print(schema.describe(args.kind))
        return 0
    try:
        project = store.Project.find(args.root or os.getcwd())
        return cmd_task(project, args) if args.cmd == "task" else cmd_init(project)
    except store.KeelError as e:
        print(str(e), file=sys.stderr)
        return e.code
    except Exception as e:  # 退出码 3 = 内部错误，不与 1（被门拦下）混淆
        print(f"keel 内部错误：{e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
