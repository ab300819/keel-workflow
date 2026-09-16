#!/usr/bin/env python3
"""health-lint —— health-lint-implementation.md 的可执行实现（v1，6/8 条）。

零依赖，仅 stdlib。规格见同级 ../references/health-lint-implementation.md。

v1 实现：state/total-size-cap · state/line-length-cap · state/forbidden-content
         health/dead-link · state/max-id-stale · id/unknown-prefix
v1 未实现（如实报 not_implemented，⛔ 不要当成 pass）：
         design/adr-only-revision（需 git diff 行范围 × heading map）
         submodule/pointer-drift（仅 shell 拓扑）
另有 flag/dangling-reference —— 扫描对象是 **skill 库本身**（非用户项目），
故走独立的 --skills-dir 模式，⛔ 不与上述 project-scope 的 rule 混用同一 target。

v1 不含：baseline / --apply / 自动修复。首扫噪声大属预期（尤见 id/unknown-prefix）。

退出码（规格「退出码（CLI 集成）」）：0 无违规 / 1 仅 warning / 2 有 blocker / 3 lint 自身错误
"""
import argparse, os, re, subprocess, sys, unicodedata

WHITELIST = ["T-RF", "Journey", "ADR", "BUG", "CON", "E2E", "INS", "AC", "US", "IT", "UT", "F", "T"]
ID_RE = re.compile(r"(?<![\w-])(" + "|".join(WHITELIST) + r")-(\d+)([a-z]?)(?![\w-])")
RANGE_RE = re.compile(r"(?<![\w-])(" + "|".join(WHITELIST) + r")-(\d+)~(?:(?:" + "|".join(WHITELIST) + r")-)?(\d+)(?![\w-])")
PREFIX_RE = re.compile(r"(?<![\w-])([A-Z][A-Za-z0-9]{0,5})-\d{1,4}[a-z]?(?![\w-])")
PREFIX_SKIP = set(WHITELIST) | {"M", "FR", "NFR"}

DEF_HEADING = re.compile(r"^#{1,4}\s+(" + "|".join(WHITELIST) + r")-(\d+)[a-z]?\b")
DEF_TABLE = re.compile(r"^\|\s*\*{0,2}(" + "|".join(WHITELIST) + r")-(\d+)[a-z]?\*{0,2}\s*\|")
DEF_LIST = re.compile(r"^[-*]\s+\*{0,2}(" + "|".join(WHITELIST) + r")-(\d+)[a-z]?\b")

FORBIDDEN = {
    "commit-hash": re.compile(r"(?:^|[@\s(\[])[0-9a-f]{7,40}(?=[\s.,;:)\]'\"`]|$)"),
    "loc-count": re.compile(r"(?:[+-]?\d+(?:\.\d+)?\s*(?:LOC|loc|lines?|行)\b|净\s*[+-]\d+\s*LOC)"),
    "codex-score": re.compile(r"(?:\bR\d+\s*(?:health\s*=)?\s*\d{2,3}(?:\s*PASS)?\b|\bR\d+\s+\d{2,3}\s*[→\-]+>?\s*R\d+\s+\d{2,3}\b|双\s*\d{2,3}\s*分)"),
    "diff-net": re.compile(r"(?<![\w\-])[+\-]\d+\s*/\s*[+\-]\d+(?![\w])"),
    "file-path": re.compile(r"\b[\w./\-]*\.(?:java|ts|tsx|js|jsx|py|go|kt|swift|md)(?::L?\d+)?\b"),
    "submodule-ref": re.compile(r"\b[a-z][\w-]*@[0-9a-f]{7,40}\b"),
}
URLPATH_RE = re.compile(r"https?://\S+|`[^`]*/[^`]*`")
SIZE_WARN, SIZE_BLOCK, LINE_CAP = 10240, 40960, 500


def strip_code_blocks(lines):
    """返回与 lines 等长的 mask：True = 该行在 ``` 围栏内，扫描时跳过。"""
    mask, inside = [], False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            inside = not inside
            mask.append(True)
        else:
            mask.append(inside)
    return mask


def collect_files(devdocs):
    out = []
    for root, dirs, files in os.walk(devdocs):
        dirs[:] = [d for d in dirs if d != "_archived"]
        for f in sorted(files):
            if f.endswith(".md") and f not in (".realign-plan.md", ".health-report.md"):
                out.append(os.path.join(root, f))
    return sorted(out)


def find(rule, sev, file, line, msg, actual=None, threshold=None, ctx=None, fix="manual_decision", auto=False):
    return dict(rule_id=rule, severity=sev, file=file, line=line, actual=actual,
                threshold=threshold, message=msg, context=ctx, fix_suggestion=fix, auto_fixable=auto)


def scan_state(state_path, rel, derived_caps):
    """state/* 四条 rule。state.md 不存在时返回 not_applicable 标记。"""
    fs = []
    if not os.path.isfile(state_path):
        return fs, True
    raw = open(state_path, "rb").read()
    size = len(raw)
    if size > SIZE_BLOCK:
        fs.append(find("state/total-size-cap", "blocker", rel, None,
                       f"devdocs-state.md 已 {size} bytes（阈值 40 KiB），违反占位 + sprint 锚点设计", size, SIZE_BLOCK))
    elif size > SIZE_WARN:
        fs.append(find("state/total-size-cap", "warning", rel, None,
                       f"devdocs-state.md 已 {size} bytes（阈值 10 KiB），建议归档", size, SIZE_WARN))

    lines = raw.decode("utf-8", "replace").split("\n")
    # frontmatter 不扫（规格：yaml 单行不扫）
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    for i in range(start, len(lines)):
        ln = lines[i]
        if "health-lint-disable-line state/line-length-cap" in ln:
            continue
        n = len(ln)
        if n > LINE_CAP:
            for anchor in ("；", "**T-RF-", "**T-", "; "):
                if anchor in ln:
                    hint = f"拆分锚点: {anchor}"
                    break
            else:
                hint = "无明显拆分点，需 manual"
            if ln.lstrip().startswith("|"):
                hint += " / table-row: yes"
            fs.append(find("state/line-length-cap", "blocker", rel, i + 1,
                           f"单行 {n} 字符（阈值 {LINE_CAP}）；{hint}", n, LINE_CAP, ln[:80] + "…"))

    # forbidden-content：从 "## 编号状态" 之后开始，fallback line 51
    hdr = next((i for i, l in enumerate(lines) if l.startswith("## 编号状态")), None)
    hdr = hdr if hdr is not None else min(50, len(lines))
    by_line = {}
    for i in range(hdr, len(lines)):
        ln = lines[i]
        if "health-lint-disable-line state/forbidden-content" in ln:
            continue
        hits = [pid for pid, rx in FORBIDDEN.items() if rx.search(ln)]
        if hits:
            by_line[i + 1] = (hits, ln.strip()[:80])
    for lineno in sorted(by_line):
        pids, ctx = by_line[lineno]
        fs.append(find("state/forbidden-content", "warning", rel, lineno,
                       "占位 prose 内含实现明细：" + ", ".join(sorted(pids)), ctx=ctx))

    # max-id-stale：解析 "## 编号状态" 表的「当前最大」列
    state_caps = {}
    if hdr is not None and hdr < len(lines):
        for ln in lines[hdr:]:
            if ln.startswith("## ") and not ln.startswith("## 编号状态"):
                break
            cells = [c.strip().strip("*") for c in ln.strip().strip("|").split("|")] if ln.strip().startswith("|") else []
            if len(cells) < 2:
                continue
            m = re.match(r"^(" + "|".join(WHITELIST) + r")\b", cells[0])
            if not m:
                continue
            for c in cells[1:]:
                mm = re.search(r"(?:" + "|".join(WHITELIST) + r")-(\d+)\b|^(\d+)$", c)
                if mm:
                    state_caps[m.group(1)] = int(mm.group(1) or mm.group(2))
                    break
    for t, sv in sorted(state_caps.items()):
        dv = derived_caps.get(t)
        if dv is None:
            fs.append(find("state/max-id-stale", "warning", rel, None,
                           f"{t}: 表中 {sv}，资源文件无该类型定义（phantom）", sv, None))
        elif sv < dv:
            fs.append(find("state/max-id-stale", "warning", rel, None,
                           f"{t}: 表中 {sv} < 资源文件 {dv}（stale，表滞后）", sv, dv))
        elif sv > dv:
            fs.append(find("state/max-id-stale", "warning", rel, None,
                           f"{t}: 表中 {sv} > 资源文件 {dv}（phantom，先查是否有编号被误删）", sv, dv))
    for t, dv in sorted(derived_caps.items()):
        if t not in state_caps:
            fs.append(find("state/max-id-stale", "warning", rel, None,
                           f"{t}: 资源文件已到 {dv}，表中无该行（missing-row，低优先）", dv, None))
    return fs, False


DISABLE = "health-lint-disable-line flag/dangling-reference"
FLAGREF_RE = re.compile(r"/([a-z][a-z0-9-]{2,})\s+(--[a-z][a-z-]*)")


def scan_skill_flags(skills_dir):
    """flag/dangling-reference：skill 互相引用的 `--flag` 在目标 skill 目录里是否存在。

    根因参见 audits/2026-09-11-devdocs-flow-backlog.md §4.1：子指令没有解析器，
    生产方删了 flag、消费方不知道，静默通过。

    ⚠️ 已知盲区：判据是「flag 在目标 skill 目录内能否搜到」，所以**skill 引用自己的
    flag 必然自证通过** —— `ms-verify/SKILL.md` 里写 `/ms-verify --foo` 抓不到。
    实测出的 6 处漂移全是跨 skill 的（消费方与生产方不同目录），故 v1 接受该盲区。
    """
    names = {d.name for d in os.scandir(skills_dir) if d.is_dir()}
    owned = {}  # skill -> 该目录下全部文本（用于判 flag 是否存在）
    fs = []
    for root, dirs, files in os.walk(skills_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(root, fn)
            try:
                lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
            except OSError:
                continue
            mask = strip_code_blocks(lines)
            for i, ln in enumerate(lines):
                if mask[i] or DISABLE in ln:
                    continue
                for m in FLAGREF_RE.finditer(ln):
                    target, flag = m.group(1), m.group(2)
                    if target not in names:
                        continue
                    if target not in owned:
                        buf = []
                        for r2, _d2, f2 in os.walk(os.path.join(skills_dir, target)):
                            for n2 in f2:
                                if n2.endswith(".md"):
                                    try:
                                        buf.append(open(os.path.join(r2, n2), encoding="utf-8", errors="replace").read())
                                    except OSError:
                                        pass
                        owned[target] = "\n".join(buf)
                    if flag not in owned[target]:
                        fs.append(find("flag/dangling-reference", "warning",
                                       os.path.relpath(path, skills_dir), i + 1,
                                       f"/{target} {flag} —— 目标 skill 目录内搜不到该 flag",
                                       ctx=ln.strip()[:120],
                                       fix=f"改为 /{target} 的真实入口；若为反例请加 <!-- {DISABLE} -->"))
    return fs


def emit(findings):
    """Finding 输出 schema。"""
    for f in findings:
        print(f"- rule_id: {f['rule_id']}")
        for k in ("severity", "file", "line", "actual", "threshold", "message", "context", "fix_suggestion", "auto_fixable"):
            v = f[k]
            if v is None:
                print(f"  {k}: null")
            elif k in ("message", "context"):
                print(f'  {k}: "{str(v)}"'.replace("\n", " "))
            elif isinstance(v, bool):
                print(f"  {k}: {str(v).lower()}")
            else:
                print(f"  {k}: {v}")


def main():
    ap = argparse.ArgumentParser(description="health-lint v1 (6/8 rules)")
    ap.add_argument("--target", default=".", help="项目根（含 docs/devdocs/）")
    ap.add_argument("--changed-only", action="store_true", help="仅扫 git diff HEAD 变更的文件")
    ap.add_argument("--fix", metavar="RULE_ID", help="仅运行指定 rule")
    ap.add_argument("--skills-dir", metavar="DIR",
                    help="改扫 skill 库，只跑 flag/dangling-reference（⛔ 与 --target 的 project-scope rule 互斥）")
    args = ap.parse_args()

    if args.skills_dir:
        sd = os.path.abspath(args.skills_dir)
        if not os.path.isdir(sd):
            print(f"lint error: {sd} 不存在", file=sys.stderr)
            return 3
        fs = scan_skill_flags(sd)
        if args.fix:
            fs = [f for f in fs if f["rule_id"] == args.fix]
        emit(fs)
        print(f"\n# skills-dir scan | warning={len(fs)}", file=sys.stderr)
        return 1 if fs else 0

    root = os.path.abspath(args.target)
    devdocs = os.path.join(root, "docs", "devdocs")
    if not os.path.isdir(devdocs):
        print(f"not_applicable: {devdocs} 不存在", file=sys.stderr)
        return 0

    files = collect_files(devdocs)
    if args.changed_only:
        try:
            out = subprocess.run(["git", "-C", root, "diff", "--name-only", "HEAD"],
                                 capture_output=True, text=True, timeout=10)
            changed = {os.path.join(root, p) for p in out.stdout.split()}
            files = [f for f in files if f in changed]
        except Exception as e:
            print(f"health/git-unavailable: {e}", file=sys.stderr)
            return 3

    rel = lambda p: os.path.relpath(p, root)
    docs = {}
    for f in files:
        try:
            lines = open(f, encoding="utf-8", errors="replace").read().split("\n")
        except OSError as e:
            print(f"lint error: {f}: {e}", file=sys.stderr)
            return 3
        docs[f] = (lines, strip_code_blocks(lines))

    # ---- Phase A：定义索引（⛔ 不从 devdocs-state.md 取上界）----
    defined, def_pos = set(), set()
    for f, (lines, mask) in docs.items():
        for i, ln in enumerate(lines):
            if mask[i]:
                continue
            for rx in (DEF_HEADING, DEF_TABLE, DEF_LIST):
                m = rx.match(ln)
                if m:
                    defined.add(f"{m.group(1)}-{int(m.group(2))}")
                    def_pos.add((f, i))
                    break
    derived_caps = {}
    for d in defined:
        t, n = d.rsplit("-", 1)
        derived_caps[t] = max(derived_caps.get(t, 0), int(n))

    findings = []

    # ---- Phase B：引用扫描 ----
    dead = {}
    for f, (lines, mask) in docs.items():
        for i, ln in enumerate(lines):
            if mask[i] or (f, i) in def_pos:
                continue
            refs = []  # (归一化 key, 文件里的原始拼写)
            for m in RANGE_RE.finditer(ln):
                t, a, b = m.group(1), int(m.group(2)), int(m.group(3))
                if b >= a and b - a <= 500:
                    w = len(m.group(2))
                    refs += [(f"{t}-{n}", f"{t}-{n:0{w}d}") for n in range(a, b + 1)]
            for m in ID_RE.finditer(ln):
                refs.append((f"{m.group(1)}-{int(m.group(2))}", m.group(0)))
            for r, raw in refs:
                if r in defined:
                    continue
                t, n = r.rsplit("-", 1)
                sub = "out-of-range" if int(n) > derived_caps.get(t, 0) else "missing-definition"
                dead.setdefault((rel(f), raw, sub), []).append(i + 1)
    for (fp, r, sub), occ in sorted(dead.items()):
        hint = ("超出资源文件中该类型的最大已定义编号，可能是未来引用或拼写错误"
                if sub == "out-of-range" else "编号在声明范围内但找不到定义；可能拼写错误 / 未创建 / 已删除")
        findings.append(find("health/dead-link", "blocker", fp, occ[0],
                             f"{r} 无定义（{sub}）：{hint}", ctx=f"occurrences: {occ[:10]}", auto=False))

    # ---- id/unknown-prefix：按 prefix 聚合，⛔ 只报不判 ----
    agg = {}
    for f, (lines, mask) in docs.items():
        for i, ln in enumerate(lines):
            if mask[i]:
                continue
            clean = URLPATH_RE.sub(" ", ln)
            for m in PREFIX_RE.finditer(clean):
                p = m.group(1)
                if p in PREFIX_SKIP:
                    continue
                a = agg.setdefault(p, {"n": 0, "s": []})
                a["n"] += 1
                if len(a["s"]) < 5:
                    a["s"].append(f"{rel(f)}:{i + 1}")
    for p, a in sorted(agg.items(), key=lambda kv: -kv[1]["n"]):
        fp, lno = a["s"][0].rsplit(":", 1)
        findings.append(find("id/unknown-prefix", "warning", fp, int(lno),
                             f"未知前缀 {p}：{a['n']} 次 occurrence，不在 dead-link 白名单内",
                             a["n"], None, ", ".join(a["s"])))

    # ---- state/* ----
    state_path = os.path.join(root, ".claude", "rules", "devdocs-state.md")
    sf, na = scan_state(state_path, os.path.relpath(state_path, root), derived_caps)
    findings += sf

    if args.fix:
        findings = [f for f in findings if f["rule_id"] == args.fix]

    emit(findings)

    sys.stdout.flush()
    blockers = sum(1 for f in findings if f["severity"] == "blocker")
    warnings = len(findings) - blockers
    print(f"\n# scanned {len(files)} files | blocker={blockers} warning={warnings}"
          + (" | devdocs-state.md: not_applicable" if na else ""), file=sys.stderr)
    print("# not_implemented(v1): design/adr-only-revision, submodule/pointer-drift", file=sys.stderr)
    return 2 if blockers else (1 if warnings else 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"lint error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)
