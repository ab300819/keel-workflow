"""完成门：任务进入已完成 / review_pending 前，按登记的提交检查测试顺序、测试冻结、注错记录与纯移动。"""
from __future__ import annotations

import fnmatch
import os
import subprocess
from typing import Any

from . import movecheck
from .store import KeelError, Project

DONE_STATES = ("已完成", "review_pending")
# 测试提交里只冻结测试文件（同提交的骨架不冻结）：任一目录段在 TEST_DIRS 里，或文件名匹配 TEST_PATH_PATTERNS
TEST_DIRS = ("test", "tests", "__tests__", "spec", "specs")
TEST_PATH_PATTERNS = ("test_*", "*_test.*", "*.test.*", "*.spec.*", "*Test.*", "*Tests.*", "*_spec.*")


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


def is_test_path(path: str) -> bool:
    *dirs, base = path.split("/")
    return any(d in TEST_DIRS for d in dirs) or any(fnmatch.fnmatchcase(base, p) for p in TEST_PATH_PATTERNS)


def _is_ancestor(d: str, a: str, b: str) -> bool:
    p = _git(d, "merge-base", "--is-ancestor", a, b)
    if p.returncode > 1:
        raise KeelError(f"git merge-base 失败：{p.stderr.strip()}", 1)
    return p.returncode == 0


def _latest(d: str, shas: list[str]) -> str:
    """拓扑上最晚的那个（其余都是它的祖先），不看登记顺序；分叉时退回最后登记的。"""
    for s in shas:
        if all(o == s or _is_ancestor(d, o, s) for o in shas):
            return s
    return shas[-1]


def _names(p: subprocess.CompletedProcess[str]) -> list[str]:
    return [n for n in p.stdout.split("\0") if n]


def check(project: Project, task: dict[str, Any]) -> list[str]:
    commits = task.get("commits") or []
    has_test = any(c.get("kind") == "test" for c in commits)
    move_done = task.get("review_profile") == "move" and task.get("status") == "已完成"
    if not has_test and not move_done:
        return []  # 老任务不碰 git
    errs: list[str] = []
    groups: dict[str, tuple[str, list[str], list[str]]] = {}  # repo -> (目录, 测试提交, 代码提交)
    for c in commits:
        repo, sha = c["ref"].split("@", 1)
        r = _repo_dir(project, repo, sha)
        if r is None:
            errs.append(f"{c['ref']} 在项目根和 <根>/{repo} 下都解析不到：先把执行者分支合进来再登记；"
                        "shell 子模块名与路径不同、或 linked 代码根在项目外时，完成门暂不支持登记测试提交")
            continue
        g = groups.setdefault(repo, (r[0], [], []))
        (g[1] if c.get("kind") == "test" else g[2]).append(r[1])
    if errs:
        return errs
    for d, tests, codes in groups.values():
        if not tests:
            continue  # 只有代码提交的仓（如配置仓）不查顺序与冻结
        tfiles: dict[str, list[str]] = {}
        for t in tests:
            p = _git(d, "diff-tree", "--no-ext-diff", "--no-textconv", "--root", "--no-commit-id",
                     "--name-only", "-r", "-z", t)
            if p.returncode != 0:
                errs.append(f"读不到测试提交 {t} 的文件：{p.stderr.strip()}")
                continue
            tfiles[t] = [n for n in _names(p) if is_test_path(n)]
            if not tfiles[t]:
                errs.append(f"测试提交 {t} 里没有识别出测试文件（按路径规则）")
        last = _latest(d, list(dict.fromkeys(tests + codes)))
        for c in codes:
            before = [t for t in tests if t != c and _is_ancestor(d, t, c)]
            if not before:
                errs.append(f"代码提交 {c} 之前没有测试提交（是否压缩合并了？）")
                continue
            # 冻结：C 之前各测试提交的测试文件，从其中拓扑最晚的那个到本仓最后一个提交不得再改；
            # 后一个测试提交可改前一个的，前提是两者之间没有代码提交
            files = sorted({f for t in before for f in tfiles.get(t, [])})
            if not files:
                continue
            tlast = _latest(d, before)
            p = _git(d, "--literal-pathspecs", "diff", "--no-ext-diff", "--no-textconv", "--name-only", "-z",
                     tlast, last, "--", *files)
            if p.returncode != 0 or _names(p):
                errs.append(f"测试提交 {tlast} 之后改了测试：{'、'.join(_names(p)) or p.stderr.strip()}")
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
            logic = [f"{g.path}:{g.line} {g.sign} {g.text}" for g in glue if g.logic]
            if logic:
                errs.append("搬移夹带改逻辑的行（列出前 5 条）：改 --profile guarded 走 review_pending\n"
                            + "\n".join(logic[:5]))
    return errs
