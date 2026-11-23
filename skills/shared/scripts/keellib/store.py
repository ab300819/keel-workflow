"""项目根、锁、原子写、manifest 与完整性校验（K1/K2 的判据）。"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from contextlib import contextmanager
from collections.abc import Iterator

STATE_REL = "docs/devdocs/state"
_V2_RE = re.compile(r"^spec_version:\s*[\"']?(tasks|backlog)\.v2\b", re.M)
_FM_RE = re.compile(r"\A---\n(.*?)\n---", re.S)
BACKLOG_MD = "docs/devdocs/backlog.md"
TASKS_MD = "docs/devdocs/04-dev-tasks.md"
BEGIN = "<!-- keel:begin ledger -->"
END = "<!-- keel:end ledger -->"
REGION_KEY = TASKS_MD + "#ledger"
HUMAN_ONLY = "这一步只能由人在交互终端执行：另开一个终端，在项目根目录运行"
ACCEPT_CMD = "`.keel/bin/keel state accept`"
ACCEPT_HINT = f"用 keel 命令改回，或人工确认。{HUMAN_ONLY} {ACCEPT_CMD}"
RENDER_HINT = "生成内容只由 keel 写，跑 `.keel/bin/keel render` 从状态重新生成"
OP_HEADS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REBASE_HEAD")  # 进行中的合并类操作：对方提交里的内容也合法
UNREADABLE = "unreadable"  # 读不出的受保护文件（悬空符号链接、无权限）：一律判违规


class KeelError(Exception):
    def __init__(self, msg: str, code: int = 1) -> None:
        super().__init__(msg)
        self.code = code


class LockBusy(KeelError):
    pass


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _git(root: str, *args: str) -> bytes | None:
    try:
        p = subprocess.run(["git", "-C", root, *args], capture_output=True)
    except OSError:
        return None
    return p.stdout if p.returncode == 0 else None


class Project:
    def __init__(self, root: str) -> None:
        self.root = root
        self.devdocs = os.path.join(root, "docs", "devdocs")
        self.state_dir = os.path.join(root, STATE_REL)
        self.keel_dir = os.path.join(root, ".keel")
        self.manifest_path = os.path.join(self.keel_dir, "manifest.json")

    @staticmethod
    def find(start: str) -> Project:
        out = _git(start, "rev-parse", "--show-toplevel")
        return Project(os.path.realpath(out.decode().strip() if out else start))

    def is_migrated(self) -> bool:
        return os.path.isfile(os.path.join(self.state_dir, "meta.json"))

    def guarded(self) -> bool:
        """K1/K2 是否生效。⛔ 不只看 meta.json：它可被删掉，删了不能让检查整体关闭。"""
        return os.path.isdir(self.state_dir) or os.path.exists(self.manifest_path) or bool(head_blobs(self, STATE_REL))

    def needs_migration(self) -> bool:
        if self.is_migrated():
            return False
        for d, dirs, files in os.walk(self.devdocs):
            dirs[:] = [x for x in dirs if x != "state"]
            for f in files:
                if not f.endswith(".md"):
                    continue
                with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                    m = _FM_RE.match(fh.read(4096))
                if m and _V2_RE.search(m.group(1)):
                    return True
        return False

    def require_writable(self) -> None:
        if self.is_migrated():
            return
        if self.needs_migration():
            raise KeelError("项目台账还是 tasks.v2 / backlog.v2 格式，要先迁移到 keel 3.x：告诉用户需要迁移，经同意后走 pipeline 的规范升级流程（先预览，再确认执行），迁移后再写状态", 3)
        raise KeelError("项目未初始化，先执行 keel init", 3)

    def check_links(self) -> None:
        for p in (self.keel_dir, self.state_dir):
            if os.path.islink(p):
                raise KeelError(f"{os.path.relpath(p, self.root)} 是符号链接，拒绝操作", 3)

    def refuse_in_worktree(self) -> None:
        """linked worktree 里各写各分支的台账，合并必冲突：台账只在主工作树写。"""
        gd, cd = _git(self.root, "rev-parse", "--git-dir"), _git(self.root, "rev-parse", "--git-common-dir")
        if gd is None or cd is None:
            return
        if os.path.realpath(os.path.join(self.root, gd.decode().strip())) == \
                os.path.realpath(os.path.join(self.root, cd.decode().strip())):
            return
        first = (_git(self.root, "worktree", "list", "--porcelain") or b"").decode("utf-8", "replace").split("\n\n")[0]
        lines = first.splitlines()
        main = lines[0].partition(" ")[2] if lines else ""
        if "bare" in lines:
            raise KeelError(f"这里是 git worktree，主仓 {main} 是 bare 仓库、没有主工作树，台账无法写入", 3)
        raise KeelError(f"这里是 git worktree，台账只在主工作树写：{main}。多 agent 并行时交给负责台账的会话；"
                        "独自开发时到主工作树执行同一条命令", 3)

    @contextmanager
    def lock(self, timeout: float = 5.0, shared: bool = False) -> Iterator[None]:
        """写方用排他锁；只读检查（Post、pre-commit）用共享锁，避免看到写到一半的状态。"""
        if not shared:
            self.refuse_in_worktree()
        self.check_links()
        os.makedirs(self.keel_dir, exist_ok=True)
        try:  # O_NOFOLLOW 且不截断：lock 若是指向别处的符号链接则拒绝
            fd = os.open(os.path.join(self.keel_dir, "lock"), os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o644)
        except OSError as e:
            raise KeelError(f"打不开 .keel/lock：{e}", 3) from None
        with os.fdopen(fd, "w") as fh:
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(fh, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise LockBusy("拿不到 .keel/lock（另一个 keel 进程在写），稍后重试", 3) from None
                    time.sleep(0.05)
            yield  # 退出 with 关闭文件即释放 flock

    def manifest(self) -> dict[str, str]:
        try:
            with open(self.manifest_path, encoding="utf-8") as f:
                data: dict[str, str] = json.load(f)
            return data
        except FileNotFoundError:
            return {}
        except ValueError:
            raise KeelError(f".keel/manifest.json 损坏，人工确认状态文件后重建。{HUMAN_ONLY} {ACCEPT_CMD}", 3) from None

    def save_manifest(self, m: dict[str, str]) -> None:
        os.makedirs(self.keel_dir, exist_ok=True)
        _replace_file(self.manifest_path, (json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _replace_file(path: str, data: bytes) -> None:
    """mkstemp 新建同目录临时文件（不跟随符号链接）再 os.replace；临时名与 cleanup_tmp 的匹配一致。"""
    d, name = os.path.split(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix="." + name + ".", suffix=".keel-tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def head_blobs(project: Project, paths_prefix: str, ref: str = "HEAD") -> dict[str, str]:
    out = _git(project.root, "ls-tree", "-r", "-z", ref, "--", paths_prefix)
    res: dict[str, str] = {}
    for rec in (out or b"").decode("utf-8", "replace").split("\0"):
        meta, _, path = rec.partition("\t")
        if path:
            res[path] = meta.split()[2]
    return res


def head_text(project: Project, relpath: str, ref: str = "HEAD") -> str | None:
    out = _git(project.root, "show", f"{ref}:./{relpath}")
    return None if out is None else out.decode("utf-8", "replace")


def region_text(file_text: str) -> str | None:
    """两个生成区标记之间的文本；标记缺失、重复或顺序不对返回 None。"""
    i, j = file_text.find(BEGIN), file_text.find(END)
    ok = 0 <= i < j and file_text.count(BEGIN) == 1 and file_text.count(END) == 1
    return file_text[i + len(BEGIN):j] if ok else None


def check_generated_links(project: Project, relpath: str) -> None:
    chain = [os.path.join(project.root, "docs"), project.devdocs, os.path.join(project.root, relpath)]
    if any(os.path.islink(c) for c in chain):
        raise KeelError(f"拒绝写入 {relpath}：它或上级目录是符号链接", 3)


def write_atomic(project: Project, relpath: str, data: bytes, *, record: bool = True) -> None:
    """调用方须已持有 project.lock()。record=False 用于只有部分内容归 keel 的文件（04-dev-tasks.md）。"""
    project.check_links()
    raw = os.path.normpath(os.path.join(project.root, relpath))
    if raw in {os.path.join(project.root, r) for r in (BACKLOG_MD, TASKS_MD)}:
        # 两个具名文件按字面路径比较；自身或上级是符号链接就会写到项目外，拒绝
        check_generated_links(project, relpath)
        path = raw
    else:
        path = os.path.realpath(raw)
        allowed = (os.path.realpath(project.state_dir), os.path.realpath(project.keel_dir))
        if not any(path.startswith(a + os.sep) for a in allowed):
            raise KeelError(f"拒绝写入 {relpath}：目标不在 state/、.keel/ 或两个生成文件内", 3)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _replace_file(path, data)
    if record:
        m = project.manifest()
        m[relpath] = blob_sha(data)
        project.save_manifest(m)


def init_state(project: Project) -> None:
    """调用方须已持有 project.lock()。"""
    for d in ("tasks", "backlog"):
        os.makedirs(os.path.join(project.state_dir, d), exist_ok=True)
    if not project.is_migrated():
        write_atomic(project, STATE_REL + "/meta.json", b'{\n  "schema": "keel.state.v1"\n}\n')


def record_region(project: Project, key: str, text: str) -> None:
    m = project.manifest()
    m[key] = blob_sha(text.encode("utf-8"))
    project.save_manifest(m)


def _file_sha(path: str) -> str:
    try:
        with open(path, "rb") as fh:
            return blob_sha(fh.read())
    except OSError:
        return UNREADABLE


def _current_blobs(project: Project) -> dict[str, str]:
    """受保护项的当前 blob：相对路径或区键 -> sha；新增受保护项（如 #ledger 区）加在这里。"""
    cur: dict[str, str] = {}

    def unreadable_dir(e: OSError) -> None:  # 读不了的子目录会藏住其中文件，记为违规
        if not isinstance(e, FileNotFoundError) and e.filename:
            cur[os.path.relpath(e.filename, project.root)] = UNREADABLE

    for d, _dirs, files in os.walk(project.state_dir, onerror=unreadable_dir):
        for f in files:
            if f.startswith(".") and f.endswith(".keel-tmp"):
                continue
            p = os.path.join(d, f)
            cur[os.path.relpath(p, project.root)] = _file_sha(p)
    p = os.path.join(project.root, BACKLOG_MD)
    if os.path.lexists(p):
        cur[BACKLOG_MD] = _file_sha(p)
    p = os.path.join(project.root, TASKS_MD)
    if os.path.lexists(p):
        try:
            with open(p, "rb") as fh:
                r = region_text(fh.read().decode("utf-8", "replace"))
        except OSError:
            r = None
        # 文件在而区块读不出（标记被删坏）与读不了同判；只有文件本身不在才算区块缺失
        cur[REGION_KEY] = UNREADABLE if r is None else blob_sha(r.encode("utf-8"))
    return cur


def backlog_guarded(project: Project, man: dict[str, str]) -> bool:
    """backlog.md 归 keel：manifest 登记过，或 HEAD 里是 keel 生成的版本（新 clone 没有 manifest）。
    手写且从未生成过的 backlog.md（迁移时一条 backlog 也没有）不归 keel。"""
    if BACKLOG_MD in man:
        return True
    ht = head_text(project, BACKLOG_MD)
    return ht is not None and "generated_by: keel" in ht


def _legal(c: str | None, mv: str | None, heads: list[str | None]) -> bool:
    """c 等于 manifest 或任一合法提交里的版本即合法。缺失时：只要有一个合法提交里也没有它就合法
    （切分支带走的、对方删掉的）；HEAD 有而工作区没有仍是删除。"""
    if c is None:
        return None in heads
    return c != UNREADABLE and c in [*heads, mv]


def _violations(project: Project, cur: dict[str, str], man: dict[str, str], refs: list[str]) -> list[str]:
    heads = [head_blobs(project, STATE_REL, r) for r in refs]
    keys = {k for k in set(cur) | set(heads[0]) | set(man) if k.startswith(STATE_REL + "/")}
    bad = [k for k in keys if not _legal(cur.get(k), man.get(k), [h.get(k) for h in heads])]
    c, mv = cur.get(BACKLOG_MD), man.get(BACKLOG_MD)
    if c != mv and backlog_guarded(project, man):
        if not _legal(c, mv, [head_blobs(project, BACKLOG_MD, r).get(BACKLOG_MD) for r in refs]):
            bad.append(BACKLOG_MD)
    c, mv = cur.get(REGION_KEY), man.get(REGION_KEY)
    if c != mv:  # 只有区块与 manifest 对不上时才查 HEAD
        hs: list[str | None] = []
        for r in refs:
            ht = head_text(project, TASKS_MD, r)
            hr = region_text(ht) if ht else None
            hs.append(None if hr is None else blob_sha(hr.encode("utf-8")))
        if (mv is not None or any(hs)) and not _legal(c, mv, hs):
            bad.append(REGION_KEY)
    return sorted(bad)


def integrity_violations(project: Project) -> list[str]:
    project.check_links()
    if not project.guarded():
        return []
    cur, man = _current_blobs(project), project.manifest()
    bad = _violations(project, cur, man, ["HEAD"])
    if bad:  # 只在有疑点时才查合并类操作，平常不多跑 git
        ops = [r for r in OP_HEADS if _git(project.root, "rev-parse", "--verify", "-q", r) is not None]
        if ops:
            bad = _violations(project, cur, man, ["HEAD", *ops])
    return bad


def prune_manifest(project: Project) -> None:
    """调用方须已持有锁且 require_intact 已通过：此时文件缺失的登记项都是合法缺失（如切分支），删掉。"""
    m = project.manifest()
    kept = {k: v for k, v in m.items() if os.path.lexists(os.path.join(project.root, k.split("#")[0]))}
    if kept != m:
        project.save_manifest(kept)


def require_intact(project: Project, only_state: bool = False) -> None:
    """only_state=True 供 render：只有生成内容（K2）对不上时允许继续，由 render 从状态重新生成。"""
    bad = integrity_violations(project)
    if only_state:
        bad = [b for b in bad if b.startswith(STATE_REL + "/")]
    if not bad:
        return
    for rel in bad:
        p = os.path.join(project.root, rel)
        if rel.endswith(".json") and os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
            try:
                json.loads(text)
            except ValueError:
                if "<<<<<<<" in text:
                    raise KeelError(f"{rel} 有合并冲突：先手工解决冲突，再人工确认。{HUMAN_ONLY} {ACCEPT_CMD}", 3) from None
    state = [b for b in bad if b.startswith(STATE_REL + "/")]
    lines = [f"{b}：状态文件被非工具改动" for b in state] + [f"{b}：生成内容被手改" for b in bad if b not in state]
    raise KeelError("\n".join(lines) + "\n" + (ACCEPT_HINT if state else RENDER_HINT), 3)


def cleanup_tmp(project: Project) -> None:
    for d, _dirs, files in os.walk(project.state_dir):
        for f in files:
            if f.startswith(".") and f.endswith(".keel-tmp"):
                os.remove(os.path.join(d, f))
