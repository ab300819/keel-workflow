#!/usr/bin/env python3
"""keel —— 任务 / backlog 状态的唯一写入口。仅标准库，Python >= 3.9。"""
from __future__ import annotations

import argparse
import os
import sys
import unittest
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from keellib import backlog, gates, hookio, install, migrate, movecheck, schema, store, tasks  # noqa: E402
from keellib.common import write_session  # noqa: E402


def cmd_init(project: store.Project) -> int:
    if project.needs_migration():
        raise store.KeelError("项目台账还是 tasks.v2 / backlog.v2 格式，要先迁移到 keel 3.x：告诉用户需要迁移，经同意后走 pipeline 的规范升级流程（先预览，再确认执行）", 3)
    with project.lock():
        store.require_intact(project)
        store.cleanup_tmp(project)
        store.init_state(project)
    print("keel 状态已初始化：" + store.STATE_REL)
    return 0


def cmd_render(project: store.Project) -> int:
    with write_session(project, regen=True):
        pass  # 会话结束时 render_all 重新生成
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
        tasks.commit(project, a.id, a.ref, a.note, a.kind, a.branch)
    elif k == "archive":
        tasks.archive(project, a.id)
    elif k == "get":
        print("\n".join(tasks.diff_ranges(project, a.id)) if a.diff_range else tasks.get(project, a.id))
    else:
        print("\n".join(tasks.list_lines(project, a.status, a.fields)))
    return 0


def cmd_backlog(project: store.Project, a: argparse.Namespace) -> int:
    k = a.backlog_cmd
    if k == "park":
        print(backlog.park(project, a.source_id, a.note, a.by, a.related, a.append))
    elif k == "get":
        print(backlog.get(project, a.anchor))
    elif k == "list":
        print("\n".join(backlog.list_lines(project, a.status, a.fields)))
    else:
        def fn(e: dict[str, Any]) -> None:
            if k == "note":
                e["note"] = a.note
            elif k == "reactivate":
                e.update(status="reactivated", target_flow=a.target_flow, target_id=a.target_id)
            elif k == "close":
                e.update(status="closed", reason=a.reason)
            else:
                e.update(status="superseded", superseded_by=a.by_id)
        backlog.transition(project, a.anchor, fn)
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
    sub.add_parser("render", help="重新生成台账区与 backlog.md")
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
    p.add_argument("--kind", choices=list(schema.COMMIT_KINDS))
    p.add_argument("--branch", help="集成目标分支，只和 --kind integration 一起用")
    tp.add_parser("archive").add_argument("id")
    p = tp.add_parser("get")
    p.add_argument("id")
    p.add_argument("--diff-range", action="store_true")
    p = tp.add_parser("list")
    p.add_argument("--status")
    p.add_argument("--fields")
    bp = sub.add_parser("backlog", help="backlog 入池、迁移与查询").add_subparsers(dest="backlog_cmd", required=True)
    p = bp.add_parser("park")
    p.add_argument("source_id")
    p.add_argument("--note", required=True)
    p.add_argument("--by", required=True)
    p.add_argument("--related")
    p.add_argument("--append", action="store_true")
    for name, opts in (("note", ["--note"]), ("reactivate", ["--target-flow", "--target-id"]),
                       ("close", ["--reason"]), ("supersede", ["--by-id"])):
        p = bp.add_parser(name)
        p.add_argument("anchor")
        for o in opts:
            p.add_argument(o, required=True)
    bp.add_parser("get").add_argument("anchor")
    p = bp.add_parser("list")
    p.add_argument("--status")
    p.add_argument("--fields")
    p = sub.add_parser("check", help="K1–K4 门禁检查")
    p.add_argument("--staged", action="store_true")
    p.add_argument("--paths", nargs="+")
    p = sub.add_parser("move-check", help="判定 diff 是逐字搬动还是夹带胶水")
    p.add_argument("rev_range")
    p.add_argument("paths", nargs="*")
    gp = sub.add_parser("gate", help="档位与命中报告").add_subparsers(dest="gate_cmd", required=True)
    p = gp.add_parser("set")
    p.add_argument("gate")
    p.add_argument("level")
    p.add_argument("--reason", required=True)
    gp.add_parser("report").add_argument("--since")
    p = sub.add_parser("migrate", help="tasks.v2 / backlog.v2 迁移到 state/（默认 --dry-run）")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    p.add_argument("--map-status", action="append", default=[], metavar="原值=目标值")
    p.add_argument("--allow-partial", action="store_true")
    sub.add_parser("hook", help="客户端 hook 入口，stdin 读 payload").add_argument("event", choices=["pre", "post", "paths"])
    sub.add_parser("install-shim", help="写 .keel/bin/keel 垫片").add_argument("--plugin-root", required=True)
    sub.add_parser("git-hook", help="git pre-commit 串接").add_subparsers(dest="git_hook_cmd", required=True).add_parser("install")
    sub.add_parser("state", help="状态确认").add_subparsers(dest="state_cmd", required=True).add_parser("accept")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        return 2
    if args.cmd == "schema":
        print(schema.describe(args.kind))
        return 0
    if args.cmd == "hook":
        return hookio.main(args.root, args.event)
    try:
        project = store.Project.find(args.root or os.getcwd())
        if args.cmd in ("install-shim", "git-hook"):
            try:
                out = install.install_shim(project, args.plugin_root) if args.cmd == "install-shim" \
                    else install.git_hook_install(project)
            except Exception as e:
                if args.cmd == "install-shim":  # SessionStart 里由 keel-shim 静默，这里留一行日志
                    hookio.log_error(project, "install-shim", e)
                raise
            if out:
                print(out)
            return 0
        if args.cmd == "task":
            return cmd_task(project, args)
        if args.cmd == "check":
            return gates.run_check(project, args.staged, args.paths)
        if args.cmd == "move-check":
            moved, glue = movecheck.run(project.root, args.rev_range, args.paths)
            print(f"搬动 {moved} 行，胶水 {len(glue)} 行，其中疑似改逻辑 {sum(x.logic for x in glue)} 行")
            for x in glue:
                print(f"{x.path}:{x.line} {x.sign} {x.text}{'  ← 改逻辑' if x.logic else ''}")
            return 0
        if args.cmd == "gate":
            if args.gate_cmd == "set":
                gates.gate_set(project, args.gate, args.level, args.reason)
            else:
                print(gates.report(project, args.since))
            return 0
        if args.cmd == "state":
            gates.accept(project)
            return 0
        if args.cmd == "migrate":
            return migrate.run(project, args.apply, args.map_status, args.allow_partial)
        if args.cmd == "render":
            return cmd_render(project)
        return cmd_backlog(project, args) if args.cmd == "backlog" else cmd_init(project)
    except store.KeelError as e:
        print(str(e), file=sys.stderr)
        return e.code
    except Exception as e:  # 退出码 3 = 内部错误，不与 1（被门拦下）混淆
        print(f"keel 内部错误：{e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
