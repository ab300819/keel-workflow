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
        return subprocess.run(["git", "-C", d, *args], capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
    except OSError as e:
        raise KeelError(f"git 无法运行：{e}", 1) from e


def _inside(project: Project, rel: str) -> str | None:
    """rel 来自任务文件：只认项目内的相对路径，免得读项目外的目录或在外部仓库跑 git（及其 diff 配置）。"""
    root = os.path.realpath(project.root)
    full = os.path.realpath(os.path.join(root, rel))
    if os.path.isabs(rel) or ".." in rel.replace("\\", "/").split("/") or os.path.commonpath([root, full]) != root:
        return None
    return full


def _repo_dir(project: Project, repo: str, sha: str) -> tuple[str, str] | None:
    """返回 (仓目录, 完整 sha)；短 sha 展开后才能比较是否同一提交。"""
    for d in (project.root, _inside(project, repo)):
        if d and os.path.isdir(d):
            p = _git(d, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
            if p.returncode == 0:
                return d, p.stdout.strip()
    return None


def _names(p: subprocess.CompletedProcess[str]) -> list[str]:
    return [n for n in p.stdout.split("\0") if n]


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
        r = _repo_dir(project, repo, sha)
        if r is None:
            errs.append(f"{c['ref']} 在本地解析不到：先把执行者分支合进来再登记")
            continue
        g = groups.setdefault(repo, (r[0], [], []))
        (g[1] if c.get("kind") == "test" else g[2]).append(r[1])
    if errs:
        return errs
    for d, tests, codes in groups.values():
        if not tests:
            continue  # 只有代码提交的仓（如配置仓）不查顺序与冻结
        for c in codes:
            before = [t for t in tests if t != c and _git(d, "merge-base", "--is-ancestor", t, c).returncode == 0]
            if not before:
                errs.append(f"代码提交 {c} 之前没有测试提交（是否压缩合并了？）")
                continue
            # 冻结：C 之前各测试提交动过的文件，从其中最后登记的那个到 C 不得再改（后一个测试提交可改前一个的）
            files: set[str] = set()
            for t in before:
                p = _git(d, "diff-tree", "--no-ext-diff", "--no-textconv", "--root", "--no-commit-id",
                         "--name-only", "-r", "-z", t)
                if p.returncode != 0:
                    errs.append(f"读不到测试提交 {t} 的文件：{p.stderr.strip()}")
                files.update(_names(p))
            if not files:
                continue
            last = before[-1]
            p = _git(d, "--literal-pathspecs", "diff", "--no-ext-diff", "--no-textconv", "--name-only", "-z",
                     last, c, "--", *sorted(files))
            if p.returncode != 0 or _names(p):
                errs.append(f"测试提交 {last} 之后改了测试：{'、'.join(_names(p)) or p.stderr.strip()}")
    if has_test:
        rec = task.get("record")
        full = _inside(project, rec) if rec else None
        if not full or not os.path.exists(full):
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
