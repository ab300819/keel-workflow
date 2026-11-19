"""测试夹具：临时 keel 项目与 keel.py 调用。"""
import os
import subprocess
import sys
from typing import Optional

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEL = os.path.join(SCRIPTS, "keel.py")
# 隔离 git hook 注入的 GIT_* 环境，避免夹具误操作外层仓库
CLEAN_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def git(root: str, *args: str) -> None:
    subprocess.run(["git", "-C", root, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   capture_output=True, check=True, env=CLEAN_ENV)


def make_project(tmp: str, git_repo: bool = True, commit: bool = True) -> str:
    root = os.path.realpath(tmp)
    os.makedirs(os.path.join(root, "docs", "devdocs"))
    with open(os.path.join(root, "docs", "devdocs", "01-requirements.md"), "w", encoding="utf-8") as f:
        f.write("# 需求\n")
    if git_repo:
        git(root, "init", "-q")
        if commit:
            git(root, "add", "-A")
            git(root, "commit", "-qm", "init")
    return root


def run_keel(root: str, *args: str, stdin: Optional[str] = None) -> "tuple[int, str, str]":
    p = subprocess.run([sys.executable, KEEL, "--root", root, *args], input=stdin,
                       capture_output=True, text=True, env=CLEAN_ENV)
    return p.returncode, p.stdout, p.stderr
