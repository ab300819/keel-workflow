"""完成门：任务进入已完成 / review_pending 前，按登记的提交检查测试顺序、测试冻结、注错记录、纯移动与是否已合入。"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from typing import Any

from . import movecheck
from .store import KeelError, Project

DONE_STATES = ("已完成", "review_pending")
# 测试提交里只冻结测试文件（同提交的骨架不冻结）：任一目录段在 TEST_DIRS 里，或文件名匹配 TEST_PATH_PATTERNS
TEST_DIRS = ("test", "tests", "__tests__", "spec", "specs")
TEST_PATH_PATTERNS = ("test_*", "*_test.*", "*.test.*", "*.spec.*", "*Test.*", "*Tests.*", "*_spec.*")
INTEGRATION = "integration"
_FM_RE = re.compile(r"\A---\n(.*?)\n---", re.S)


def _git(d: str, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["git", "-C", d, "-c", "core.fsmonitor=false", *args], capture_output=True, text=True, encoding="utf-8",
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


def _clean(v: str) -> str:
    v = re.sub(r"\s+#.*$", "", v).strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


def declaration(project: Project) -> tuple[str, dict[str, str]] | None:
    """AGENTS.md frontmatter 的 workspace 块 -> (mode, {代码根 name: path})；没有该块返回 None。
    只认 mode 与 code_roots 的 name / path（字符串项、对象项、行内列表），不是通用 YAML 解析。"""
    try:
        with open(os.path.join(project.root, "AGENTS.md"), encoding="utf-8", errors="replace") as f:
            m = _FM_RE.match(f.read(65536))
    except OSError:
        return None
    lines = m.group(1).split("\n") if m else []
    start = next((k for k, ln in enumerate(lines) if ln.rstrip() == "workspace:"), None)
    if start is None:
        return None
    items: list[dict[str, str]] = []
    mode, in_roots, key_indent = "", False, 0
    for raw in lines[start + 1:]:
        t = raw.strip()
        if not t or t.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0:
            break
        if in_roots and (t.startswith("-") or indent > key_indent):
            if t.startswith("-"):
                t = t[1:].strip()
                items.append({})
                if ":" not in t:  # 字符串项 foo 等价于 {name: foo}
                    items[-1]["name"] = _clean(t)
                    continue
            k, _, v = t.partition(":")
            if items and k.strip() in ("name", "path"):
                items[-1][k.strip()] = _clean(v)
            continue
        in_roots = False
        k, _, v = t.partition(":")
        if k.strip() == "mode":
            mode = _clean(v)
        elif k.strip() == "code_roots":
            v = _clean(v)
            key_indent, in_roots = indent, not v
            items += [{"name": _clean(n)} for n in v.strip("[]").split(",") if _clean(n)]
    return mode, {i["name"]: i.get("path", "") for i in items if i.get("name")}


def _repo_dirs(project: Project, repo: str, decl: tuple[str, dict[str, str]] | None) -> tuple[list[str], str]:
    """(候选仓目录, 都解析不到时的提示)。有声明时只认声明，不猜同名目录（可能是另一个仓）。"""
    if decl is None:
        return ([d for d in (project.root, _inside(project, repo)) if d],
                f"在项目根和 <根>/{repo} 下都解析不到：核对 sha；shell / linked 布局先用 /workspace-topology 落声明")
    mode, roots = decl
    if mode == "shell":
        p = _git(project.root, "config", "-f", ".gitmodules", f"submodule.{repo}.path")
        sub = p.stdout.strip() if p.returncode == 0 else ""
        if sub:
            d = _inside(project, sub)
            return ([d] if d else []), f"在子模块 {repo}（{sub}）里解析不到：先 git submodule update，或核对 sha"
    if mode == "linked" and roots.get(repo):
        d = os.path.realpath(os.path.join(project.root, os.path.expanduser(roots[repo])))
        if not os.path.isdir(d):
            return [], f"声明的代码根 {repo} 路径 {roots[repo]} 不存在：用 /workspace-topology reconcile 修声明"
        return [d], f"在代码根 {repo}（{d}）里解析不到：核对 sha，或先把提交取到这个仓"
    return [project.root], "在项目根解析不到：核对 sha 与仓名（仓名须是声明里的代码根 name，或本仓自己）"


def _repo_dir(project: Project, repo: str, sha: str, decl: tuple[str, dict[str, str]] | None) -> tuple[str, str] | str:
    """返回 (仓目录, 完整 sha)，解析不到返回提示；短 sha 展开后才能比较是否同一提交。"""
    dirs, hint = _repo_dirs(project, repo, decl)
    for d in dirs:
        if os.path.isdir(d):
            p = _git(d, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
            if p.returncode == 0:
                return d, p.stdout.strip()
    return hint


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
    if not has_test and not move_done and not any(c.get("kind") == INTEGRATION for c in commits):
        return []  # 老任务不碰 git
    errs: list[str] = []
    decl = declaration(project)
    groups: dict[str, tuple[str, list[str], list[str]]] = {}  # repo -> (目录, 测试提交, 代码提交)
    integ: dict[str, tuple[str, str]] = {}  # repo -> (合入点 sha, 目标分支)；只是合入证据，不算代码提交
    for c in commits:
        repo, sha = c["ref"].split("@", 1)
        r = _repo_dir(project, repo, sha, decl)
        if isinstance(r, str):
            errs.append(f"{c['ref']} {r}")
            continue
        g = groups.setdefault(repo, (r[0], [], []))
        if c.get("kind") == INTEGRATION:
            integ[repo] = (r[1], str(c.get("branch") or ""))
        else:
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
    errs += _unmerged(groups, integ)
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


def _unmerged(groups: dict[str, tuple[str, list[str], list[str]]], integ: dict[str, tuple[str, str]]) -> list[str]:
    """本卡的测试 / 代码提交须已合入：默认看仓当前 HEAD；该仓登记了合入点就看合入点，且合入点须在目标分支上。"""
    errs: list[str] = []
    for repo, (d, tests, codes) in groups.items():
        target, where = "HEAD", f"{repo} 当前检出的分支"
        if repo in integ:
            target, branch = integ[repo]
            where = f"合入点 {target[:12]}"
            p = _git(d, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}")
            if p.returncode != 0:
                errs.append(f"{repo} 的集成目标分支 {branch} 在本地不存在（按 refs/heads/ 解析）")
                continue
            if not _is_ancestor(d, target, p.stdout.strip()):
                errs.append(f"合入点 {target[:12]} 不在 {repo} 的 {branch} 分支上：分支被改写过就重新登记 --kind integration")
                continue
        miss = [x[:12] for x in dict.fromkeys(tests + codes) if not _is_ancestor(d, x, target)]
        if miss:
            errs.append(f"代码还没合入：{'、'.join(miss)} 不在{where}上。先合并（不要 squash）；合到了别的分支就登记合入点："
                        f"task commit <id> {repo}@<合入后的 sha> --kind integration --branch <目标分支> --note <一句话>")
    return errs
