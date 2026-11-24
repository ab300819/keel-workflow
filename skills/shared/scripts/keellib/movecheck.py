"""move-check：判定一段 diff 是逐字搬动还是夹带胶水。纯分析，不改任何文件。"""
from __future__ import annotations

import re
import subprocess
from collections import Counter
from typing import NamedTuple

from .store import KeelError


class Glue(NamedTuple):
    sign: str  # "+" 或 "-"
    path: str
    line: int  # "+" 为新文件行号，"-" 为旧文件行号
    text: str
    logic: bool


_NOT_LOGIC = ("import ", "from ", "using ", "package ", "#include", "require(", "//", "# ", "#!", "/*", "* ", "*/")
_LOGIC = [re.compile(p) for p in (
    r"\b(if|else|elif|for|foreach|while|switch|case|return|throw|try|catch|except|finally"
    r"|and|or|not|raise|break|continue|yield|await)\b",
    r"\b(true|false|True|False|None|null|nil|undefined)\b",
    r"==|!=|<=|>=|&&|\|\||\s[<>]\s|!(?!=)|\s\?\s.*\s:\s",  # 空格包围的 < > 免误判泛型与箭头；三元要求空格，避开 a?: T
    r"\b\d+(\.\d+)?\b",
    r"\"[^\"]*\"|'[^']*'",
)]


_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def is_logic(line: str) -> bool:
    s = line.strip()
    if s == "#" or s.startswith(_NOT_LOGIC):
        return False
    return any(r.search(s) for r in _LOGIC)


def find_glue(diff_text: str) -> tuple[int, list[Glue]]:
    removed: list[tuple[str, int, str]] = []  # (path, 行号, stripped)
    added: list[tuple[str, int, str]] = []
    old_path = new_path = ""
    old_no = new_no = 0
    in_header = False
    for raw in diff_text.splitlines():
        if raw.startswith("diff --git"):
            in_header = True
        elif raw.startswith("@@"):
            in_header = False
            m = _HUNK.match(raw)
            if m:
                old_no, new_no = int(m.group(1)), int(m.group(2))
        elif in_header:
            if raw.startswith("--- "):
                old_path = raw[4:].removeprefix("a/")
            elif raw.startswith("+++ "):
                new_path = raw[4:].removeprefix("b/")
        elif raw[:1] == "+":
            if raw[1:].strip():
                added.append((new_path, new_no, raw[1:].strip()))
            new_no += 1
        elif raw[:1] == "-":
            if raw[1:].strip():
                removed.append((old_path, old_no, raw[1:].strip()))
            old_no += 1
        elif raw[:1] == " ":
            old_no += 1
            new_no += 1
    matched = Counter(t for _, _, t in added) & Counter(t for _, _, t in removed)
    moved = sum(matched.values())
    glue: list[Glue] = []
    for sign, items in (("-", removed), ("+", added)):
        left = Counter(matched)
        for path, no, text in items:
            if left[text] > 0:
                left[text] -= 1
            else:
                glue.append(Glue(sign, path, no, text, is_logic(text)))
    return moved, glue


def run(project_root: str, rev_range: str, paths: list[str]) -> tuple[int, list[Glue]]:
    cmd = ["git", "-C", project_root, "-c", "core.fsmonitor=false", "diff", "--no-ext-diff", "--no-textconv", "--no-color", "-U0", "--no-renames", "--end-of-options", rev_range]
    if paths:
        cmd += ["--", *paths]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        raise KeelError(f"git 无法运行：{e}", 1) from e
    if p.returncode != 0:
        raise KeelError(f"git diff 失败：{p.stderr.strip()}", 1)
    return find_glue(p.stdout)
