"""完成门：任务进入已完成 / review_pending 前，按登记的提交检查测试顺序、测试冻结、注错记录与纯移动。"""
from __future__ import annotations

import os
import subprocess
from typing import Any

from . import movecheck
from .store import KeelError, Project

DONE_STATES = ("已完成", "review_pending")


def _git(d: str, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["git", "-C", d, *args], capture_output=True, text=True)
    except OSError as e:
        raise KeelError(f"git 无法运行：{e}", 1) from e


def _repo_dir(project: Project, repo: str, sha: str) -> str | None:
    for d in (project.root, os.path.join(project.root, repo)):
        if os.path.isdir(d) and _git(d, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0:
            return d
    return None


def check(project: Project, task: dict[str, Any]) -> list[str]:
    commits = task.get("commits") or []
    has_test = any(c.get("kind") == "test" for c in commits)
    move_done = task.get("review_profile") == "move" and task.get("status") == "已完成"
    if not has_test and not move_done:
        return []  # 老任务不碰 git
    errs: list[str] = []
    groups: dict[str, tuple[str, list[str], list[str]]] = {}  # repo -> (目录, 测试提交, 代码提交)，保持登记顺序
    for c in commits:
        repo, sha = c["ref"].split("@", 1)
        d = _repo_dir(project, repo, sha)
        if d is None:
            errs.append(f"{c['ref']} 在本地解析不到：先把执行者分支合进来再登记")
            continue
        g = groups.setdefault(repo, (d, [], []))
        (g[1] if c.get("kind") == "test" else g[2]).append(sha)
    if errs:
        return errs
    for d, tests, codes in groups.values():
        if not tests:
            continue  # 只有代码提交的仓（如配置仓）不查顺序与冻结
        for c in codes:
            if not any(t != c and _git(d, "merge-base", "--is-ancestor", t, c).returncode == 0 for t in tests):
                errs.append(f"代码提交 {c} 之前没有测试提交（是否压缩合并了？）")
        for t in tests if codes else []:
            files = _git(d, "diff-tree", "--no-commit-id", "--name-only", "-r", t).stdout.split()
            if not files:
                continue
            p = _git(d, "diff", "--name-only", t, codes[-1], "--", *files)
            if p.returncode != 0 or p.stdout.strip():
                errs.append(f"测试提交 {t} 之后改了测试：{'、'.join(p.stdout.split()) or p.stderr.strip()}")
    if has_test:
        rec = task.get("record")
        if not rec or not os.path.exists(os.path.join(project.root, rec)):
            errs.append("有测试提交但没有注错记录：先写 audit/<id>/ 并 --record")
    if move_done:
        if not any(codes for _, _, codes in groups.values()):
            errs.append("move 卡没有登记代码提交")
        for d, _, codes in groups.values():
            if not codes:
                continue
            _, glue = movecheck.run(d, f"{codes[0]}^..{codes[-1]}", [])
            logic = [f"{g.sign} {g.path}: {g.text}" for g in glue if g.logic]
            if logic:
                errs.append("搬移夹带改逻辑的行（列出前 5 条）：改 --profile guarded 走 review_pending\n"
                            + "\n".join(logic[:5]))
    return errs
