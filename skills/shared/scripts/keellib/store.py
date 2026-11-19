"""项目根、锁、原子写、manifest 与完整性校验（K1/K2 的判据）。"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import time
from contextlib import contextmanager
from collections.abc import Iterator

STATE_REL = "docs/devdocs/state"
_V2_RE = re.compile(r"^spec_version:\s*[\"']?(tasks|backlog)\.v2\b", re.M)
_FM_RE = re.compile(r"\A---\n(.*?)\n---", re.S)
ACCEPT_HINT = "状态文件被非工具改动；用 keel 命令改回，或人工确认后执行 `! .keel/bin/keel state accept`"


class KeelError(Exception):
    def __init__(self, msg: str, code: int = 1) -> None:
        super().__init__(msg)
        self.code = code


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
            raise KeelError("项目仍是 tasks.v2 / backlog.v2 文档，先执行 /pipeline realign 迁移后再写状态", 3)
        raise KeelError("项目未初始化，先执行 keel init", 3)

    @contextmanager
    def lock(self, timeout: float = 5.0) -> Iterator[None]:
        os.makedirs(self.keel_dir, exist_ok=True)
        with open(os.path.join(self.keel_dir, "lock"), "w") as fh:
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise KeelError("拿不到 .keel/lock（另一个 keel 进程在写），稍后重试", 3) from None
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
            raise KeelError(".keel/manifest.json 损坏，人工确认状态文件后执行 `! .keel/bin/keel state accept` 重建", 3) from None

    def save_manifest(self, m: dict[str, str]) -> None:
        os.makedirs(self.keel_dir, exist_ok=True)
        tmp = self.manifest_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, self.manifest_path)


def head_blobs(project: Project, paths_prefix: str) -> dict[str, str]:
    out = _git(project.root, "ls-tree", "-r", "-z", "HEAD", "--", paths_prefix)
    res: dict[str, str] = {}
    for rec in (out or b"").decode("utf-8", "replace").split("\0"):
        meta, _, path = rec.partition("\t")
        if path:
            res[path] = meta.split()[2]
    return res


def head_text(project: Project, relpath: str) -> str | None:
    out = _git(project.root, "show", "HEAD:./" + relpath)
    return None if out is None else out.decode("utf-8", "replace")


def write_atomic(project: Project, relpath: str, data: bytes) -> None:
    """调用方须已持有 project.lock()。"""
    path = os.path.join(project.root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = os.path.join(os.path.dirname(path), "." + os.path.basename(path) + ".keel-tmp")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    m = project.manifest()
    m[relpath] = blob_sha(data)
    project.save_manifest(m)


def record_region(project: Project, key: str, text: str) -> None:
    m = project.manifest()
    m[key] = blob_sha(text.encode("utf-8"))
    project.save_manifest(m)


def _current_blobs(project: Project) -> dict[str, str]:
    """受保护项的当前 blob：相对路径或区键 -> sha；新增受保护项（如 #ledger 区）加在这里。"""
    cur: dict[str, str] = {}
    for d, _dirs, files in os.walk(project.state_dir):
        for f in files:
            if f.startswith(".") and f.endswith(".keel-tmp"):
                continue
            p = os.path.join(d, f)
            with open(p, "rb") as fh:
                cur[os.path.relpath(p, project.root)] = blob_sha(fh.read())
    return cur


def integrity_violations(project: Project) -> list[str]:
    cur = _current_blobs(project)
    man = project.manifest()
    head = head_blobs(project, STATE_REL)
    keys = set(cur) | set(head) | {k for k in man if k.startswith(STATE_REL + "/")}
    return sorted(k for k in keys if cur.get(k) is None or cur[k] not in (head.get(k), man.get(k)))


def require_intact(project: Project) -> None:
    bad = integrity_violations(project)
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
                    raise KeelError(f"{rel} 有合并冲突，手工解决后执行 `! .keel/bin/keel state accept`", 3) from None
    raise KeelError("\n".join(bad) + "\n" + ACCEPT_HINT, 3)


def cleanup_tmp(project: Project) -> None:
    for d, _dirs, files in os.walk(project.state_dir):
        for f in files:
            if f.startswith(".") and f.endswith(".keel-tmp"):
                os.remove(os.path.join(d, f))
