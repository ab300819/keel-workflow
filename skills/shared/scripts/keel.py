#!/usr/bin/env python3
"""keel —— 任务 / backlog 状态的唯一写入口。仅标准库，Python >= 3.9。"""
from __future__ import annotations

import argparse
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from keellib import store  # noqa: E402


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


def self_test() -> int:
    suite = unittest.defaultTestLoader.discover(os.path.join(HERE, "tests"), top_level_dir=os.path.join(HERE, "tests"))
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="keel")
    ap.add_argument("--root", help="项目根（默认：当前目录所在 git 仓库根）")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("init", help="初始化 state/ 与 manifest")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        return 2
    try:
        project = store.Project.find(args.root or os.getcwd())
        return cmd_init(project)
    except store.KeelError as e:
        print(str(e), file=sys.stderr)
        return e.code
    except Exception as e:  # 退出码 3 = 内部错误，不与 1（被门拦下）混淆
        print(f"keel 内部错误：{e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
