"""垫片 .keel/bin/keel 与 git pre-commit 串接。"""
from __future__ import annotations

import os
import shlex

from . import store
from .store import KeelError, Project

MARK = "# keel pre-commit"
NOT_READY = 4  # 垫片自检失败（缺 python3 或 keel.py）：pre-commit 只对它放行
HOOK = f"""#!/bin/bash
{MARK}：先跑 keel 门禁，再执行被串接的旧 hook
K=./.keel/bin/keel
if [ -x "$K" ]; then
  "$K" check --staged; rc=$?
  case $rc in
    0) ;;
    {NOT_READY}|126|127) echo "keel 不可用（退出码 ${{rc}}），本次提交未检查；开新会话会重写垫片" >&2 ;;
    *) exit 1 ;;  # 1 被门拦下；3 检查启动了却完成不了（状态读不出、manifest 损坏）：同样拒绝
  esac
else echo "keel：.keel/bin/keel 不存在，跳过状态检查（开一次装了 keel 插件的会话即可生成）" >&2
fi
C="$(dirname "$0")/pre-commit.keel-chained"
if [ -x "$C" ]; then exec "$C" "$@"; fi
exit 0
"""
SHIM = """#!/bin/bash
T={target}
command -v python3 >/dev/null 2>&1 || {{ echo "keel 工具未就绪：缺 python3" >&2; exit {rc}; }}
[ -f "$T" ] || {{ echo "keel 工具未就绪：缺 ${{T}}（插件已升级或卸载；开一次装了 keel 插件的会话即可重写垫片）" >&2; exit {rc}; }}
exec python3 "$T" "$@"
"""
UNMIGRATED = ('{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":'
              '"keel 3.0：本项目台账尚未迁移，写台账和 backlog 的命令会拒绝执行；先跑 /pipeline realign"}}')


def git_path(project: Project, rel: str) -> str | None:
    """⛔ 不拼 $ROOT/.git：worktree、子模块里 .git 是文件，core.hooksPath 也会改 hooks 位置。"""
    out = store._git(project.root, "rev-parse", "--git-path", rel)
    return None if out is None else os.path.join(project.root, out.decode().strip())


def install_shim(project: Project, plugin_root: str) -> str:
    project.check_links()
    bindir = os.path.join(project.keel_dir, "bin")
    if os.path.islink(bindir):
        raise KeelError(".keel/bin 是符号链接，拒绝写垫片", 3)
    os.makedirs(bindir, exist_ok=True)
    target = os.path.join(os.path.abspath(plugin_root), "skills", "shared", "scripts", "keel.py")
    shim = os.path.join(bindir, "keel")
    store._replace_file(shim, SHIM.format(target=shlex.quote(target), rc=NOT_READY).encode())
    os.chmod(shim, 0o755)
    ex = git_path(project, "info/exclude")
    if ex is not None:
        try:
            with open(ex, encoding="utf-8") as f:
                old = f.read()
        except FileNotFoundError:
            old = ""
        if ".keel/" not in old.splitlines():
            os.makedirs(os.path.dirname(ex), exist_ok=True)
            with open(ex, "a", encoding="utf-8") as f:
                f.write(("" if old.endswith("\n") or not old else "\n") + ".keel/\n")
    return UNMIGRATED if project.needs_migration() else ""


def git_hook_install(project: Project) -> str:
    d = git_path(project, "hooks")
    if d is None:
        raise KeelError("不是 git 仓库，无法安装 pre-commit", 3)
    hook, chained = os.path.join(d, "pre-commit"), os.path.join(d, "pre-commit.keel-chained")
    msgs = []
    rel = os.path.relpath(os.path.realpath(d), project.root)
    if not rel.startswith("..") and rel.split(os.sep)[0] != ".git":
        msgs.append(f"注意：hooks 目录 {rel} 在工作区内（core.hooksPath），本次改动的是与团队共享的受控文件")
    old = None
    if os.path.lexists(hook):
        with open(hook, encoding="utf-8", errors="replace") as f:
            old = f.read()
    if old == HOOK:
        return "\n".join(msgs + [f"{hook} 已是 keel hook，未改动"])
    if old is not None and MARK not in old:  # 旧版 keel hook 直接覆盖升级；别人的 hook 串接
        if os.path.lexists(chained):
            raise KeelError(f"{chained} 已存在，先人工合并两个 hook 再重试", 3)
        os.rename(hook, chained)
        msgs.append(f"原 pre-commit 改名为 {chained}，由 keel hook 串接执行")
    os.makedirs(d, exist_ok=True)
    with open(hook, "w", encoding="utf-8") as f:
        f.write(HOOK)
    os.chmod(hook, 0o755)
    return "\n".join(msgs + [f"已写入 {hook}：提交前跑 .keel/bin/keel check --staged"])
