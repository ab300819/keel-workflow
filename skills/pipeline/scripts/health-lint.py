#!/usr/bin/env python3
"""health-lint —— health-lint-implementation.md 的可执行实现（v1，10/12 条）。

零依赖，仅 stdlib。规格见同级 ../references/health-lint-implementation.md。
⚠️ 条数改了这里、argparse description、规格 Rule 集表三处必须同改
（已漂移过一次，见 audits/2026-06-12-skill-ssot-audit.md A4）。

project scope（--target）：state/total-size-cap · state/line-length-cap
         state/forbidden-content · state/max-id-stale · health/dead-link · id/unknown-prefix
skill 库 scope（--skills-dir，扫描对象是 **skill 库本身**，⛔ 不与 project scope 混用同一
target）：flag/dangling-reference · skill/dead-link · skill/name-mismatch · skill/size-cap
v1 未实现（如实报 not_implemented，⛔ 不要当成 pass）：
         design/adr-only-revision（需 git diff 行范围 × heading map）
         submodule/pointer-drift（仅 shell 拓扑）

v1 不含：--apply / 自动修复。baseline 见 --baseline-init / --since-baseline。

退出码（规格「退出码（CLI 集成）」）：0 无违规 / 1 仅 warning / 2 有 blocker / 3 lint 自身错误
"""
import argparse, json, os, re, subprocess, sys, unicodedata

WHITELIST = ["T-RF", "Journey", "ADR", "BUG", "CON", "E2E", "INS", "AC", "US", "IT", "UT", "F", "T"]
ID_RE = re.compile(r"(?<![\w-])(" + "|".join(WHITELIST) + r")-(\d+)([a-z]?)(?![\w-])")
RANGE_RE = re.compile(r"(?<![\w-])(" + "|".join(WHITELIST) + r")-(\d+)~(?:(?:" + "|".join(WHITELIST) + r")-)?(\d+)(?![\w-])")
PREFIX_RE = re.compile(r"(?<![\w-])([A-Z][A-Za-z0-9]{0,5})-\d{1,4}[a-z]?(?![\w-])")
PREFIX_SKIP = set(WHITELIST) | {"M", "FR", "NFR"}

DEF_HEADING = re.compile(r"^#{1,4}\s+(" + "|".join(WHITELIST) + r")-(\d+)([a-z]?)\b")
DEF_TABLE = re.compile(r"^\|\s*\*{0,2}(" + "|".join(WHITELIST) + r")-(\d+)([a-z]?)\*{0,2}\s*\|")
DEF_LIST = re.compile(r"^\s*[-*]\s+\*{0,2}(" + "|".join(WHITELIST) + r")-(\d+)([a-z]?)\b")
KEY_RE = re.compile(r"^(.+)-(\d+)([a-z]?)$")

LAYOUT_DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "..", "shared", "devdocs-layout.md")
_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*(`[^`]+`|—)\s*\|\s*$")


def pat_to_re(pattern):
    """清单路径模式 → 正则源串。语法见 devdocs-layout.md「路径模式语法」节。"""
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if c == "{":
            j = pattern.index("}", i)
            alts = [re.escape(a) for a in pattern[i + 1:j].split(",")]
            out.append("(?:" + "|".join(alts) + ")")
            i = j + 1
        elif c == "<":
            j = pattern.index(">", i)
            tok = pattern[i + 1:j]
            out.append({"N": r"\d+", "slug": r"[A-Za-z0-9_-]+"}.get(tok, r"[^/]+"))
            i = j + 1
        elif pattern.startswith("**/", i):
            out.append(r"(?:[^/]+/)*")
            i += 3
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


def load_layout(path=None):
    """解析布局清单「## 清单」节的三列表，返回 [(编译正则, owner, 主文件|None), ...]。

    只收「## 清单」标题之后、下一个「## 」标题之前的行 —— 清单文件里还有路径模式语法 /
    双形态存储 / 阈值分工三张说明性表格，逐行匹配 _ROW_RE 会把它们的示例行也当成清单条目。

    ⛔ 清单缺失或零可解析行一律抛 RuntimeError —— 静默返回空表会让
    layout/unknown-path 把项目里每个文件都判成「待分类」，是最糟的失效形态。
    """
    p = path or LAYOUT_DOC
    try:
        text = open(p, encoding="utf-8").read()
    except OSError as e:
        raise RuntimeError(f"布局清单读不到：{p}：{e}")
    lines = text.split("\n")
    has_section = any(ln.strip() == "## 清单" for ln in lines)
    rows = []
    # 无「## 清单」标题（如不分节的最小夹具）时退化为整篇扫描，保持向后兼容。
    in_section = not has_section
    for ln in lines:
        if ln.startswith("## "):
            in_section = ln.strip() == "## 清单"
            continue
        if not in_section:
            continue
        m = _ROW_RE.match(ln)
        if not m:
            continue
        pat, owner, parent = m.group(1), m.group(2).strip(), m.group(3)
        rows.append((re.compile(pat_to_re(pat)), owner,
                     None if parent == "—" else parent.strip("`")))
    if not rows:
        raise RuntimeError(f"布局清单无可解析行：{p}")
    return rows


def key_parts(k):
    """归一化键 → (类型, 数字)。字母后缀参与身份、不参与数值上界。"""
    m = KEY_RE.match(k)
    return m.group(1), int(m.group(2))


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


def changed_set(root):
    """--changed-only 的变更集，返回 realpath 集合（调用方也须按 realpath 比对）。

    ⛔ 任何失败一律抛异常 —— 调用方必须 exit 3。这三条红线是同一个失效模式
    （静默全漏扫 + exit 0）的三个方向，⛔ 补其一时必须回头查另两个：
      1. git 调用失败 ⇒ 不得当成「没有变更」
      2. git 输出是**仓根**相对路径，不是 root 相对 —— root 为子目录时直接
         join(root, x) 会全部对不上，集合成空
      3. `diff --name-only` **不含未跟踪文件** —— 新建的文档会整份漏扫
    """
    def git(*a):
        out = subprocess.run(["git", "-C", root, *a], capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            raise RuntimeError(out.stderr.strip() or f"git {' '.join(a)} exit {out.returncode}")
        return out.stdout.splitlines()   # ⛔ 不用 split()：文件名可能含空格
    top = git("rev-parse", "--show-toplevel")[0]
    # ⛔ ls-files 默认输出**相对 CWD**，与 diff 的仓根相对不同基准 —— 必须 --full-name
    names = git("diff", "--name-only", "HEAD") + git("ls-files", "--others", "--exclude-standard", "--full-name")
    return {os.path.realpath(os.path.join(top, x)) for x in names}


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
    flag 必然自证通过** —— `verify/SKILL.md` 里写 `/verify --foo` 抓不到。
    实测出的 6 处漂移全是跨 skill 的（消费方与生产方不同目录），故 v1 接受该盲区。
    """
    names = {d.name for d in os.scandir(skills_dir) if d.is_dir()}
    owned = {}  # skill -> 该目录下全部文本（用于判 flag 是否存在）
    degraded = set()  # 目录内有 .md 读失败 → 内容不全，⛔ 不得据此判 flag 不存在
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
                                    except OSError as e:
                                        # ⛔ 不得静默：内容读不全会让「搜不到 flag」变成误报
                                        print(f"lint error: {os.path.join(r2, n2)}: {e}", file=sys.stderr)
                                        degraded.add(target)
                        owned[target] = "\n".join(buf)
                    if target in degraded:
                        continue          # 内容不全，判不了，⛔ 宁可漏报不误报
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
                print(f"  {k}: " + json.dumps(str(v).replace("\n", " "), ensure_ascii=False))
            elif isinstance(v, bool):
                print(f"  {k}: {str(v).lower()}")
            else:
                print(f"  {k}: {v}")


SKILL_LINE_CAP = 500
REL_LINK_RE = re.compile(r"\]\((\.{1,2}/[^)\s]*)\)")


def scan_skill_repo(skills_dir):
    """skill 库自检 3 条 —— AGENTS.md 已声明但此前零人执行的约束。

    skill/size-cap      SKILL.md ≤ 500 行（AGENTS.md 硬约束）
    skill/name-mismatch 目录名 ≡ frontmatter name（安装按 name 复制整个目录）
    skill/dead-link     仓内相对链接目标存在
    """
    fs = []
    for d in sorted(os.scandir(skills_dir), key=lambda e: e.name):
        # shared/ 是共享资源目录（constraints.md / runlog.md），不是 skill
        if not d.is_dir() or d.name.startswith(".") or d.name == "shared":
            continue
        sk = os.path.join(d.path, "SKILL.md")
        if not os.path.isfile(sk):
            fs.append(find("skill/name-mismatch", "blocker", d.name, None,
                           f"目录 {d.name}/ 没有 SKILL.md", fix="补 SKILL.md 或删除空目录"))
            continue
        lines = open(sk, encoding="utf-8", errors="replace").read().splitlines()
        n = len(lines)
        if n > SKILL_LINE_CAP:
            fs.append(find("skill/size-cap", "blocker", f"{d.name}/SKILL.md", None,
                           f"{n} 行 > {SKILL_LINE_CAP}（AGENTS.md 硬约束）", n, SKILL_LINE_CAP,
                           fix="把细节下沉到 references/"))
        name = next((l[5:].strip() for l in lines[:20] if l.startswith("name:")), None)
        if name != d.name:
            fs.append(find("skill/name-mismatch", "blocker", f"{d.name}/SKILL.md", None,
                           f"目录名 {d.name!r} != frontmatter name {name!r}；"
                           f"安装按 name 复制整个目录，跨 skill 相对引用依赖该约定",
                           fix="改 frontmatter name 或重命名目录（两者须一致）"))

    # dead-link：⛔ 只查真实相对链接（./ 或 ../ 开头），⛔ 不用裸正则一刀切。
    #
    # ⛔ **跳过 templates/** —— 模板会被复制进用户项目，其中的相对路径是按
    # **产物落点**算的，不是仓内路径。实测：prd/templates 的
    # `../../codebase-insight.md` 在仓内不存在，但模板落到用户项目
    # `docs/prd/requirements/index.md` 后正好解析到 `docs/codebase-insight.md`，
    # 完全正确。按仓内文件系统校验模板 = 必然误报。
    # 这是 repo-governance 1.2 明确警告过的那一类。
    for root, dirs, files in os.walk(skills_dir):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x != "templates"]
        for fn in sorted(f for f in files if f.endswith(".md")):
            path = os.path.join(root, fn)
            lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
            mask = strip_code_blocks(lines)
            for i, ln in enumerate(lines):
                if mask[i] or "health-lint-disable-line skill/dead-link" in ln:
                    continue
                for m in REL_LINK_RE.finditer(ln):
                    tgt = m.group(1).split("#")[0]
                    if not tgt or os.path.exists(os.path.join(root, tgt)):
                        continue
                    fs.append(find("skill/dead-link", "warning",
                                   os.path.relpath(path, skills_dir), i + 1,
                                   f"相对链接目标不存在：{tgt}", ctx=ln.strip()[:100],
                                   fix="修正路径；若为示例请加 <!-- health-lint-disable-line skill/dead-link -->"))
    return fs


ELEM_QUOTED = re.compile(r'^"[^"]*"$')
ELEM_BARE = re.compile(r"^[A-Za-z0-9_-]+$")
BASELINE_REL = os.path.join(".claude", "rules", ".health-baseline.yml")
BASELINE_SCHEMA = "health-baseline.v1"
SIZE_DELTA_IGNORE = 2048   # 规格：delta < 2 KiB 视为可忽略小增长


def _git(root, *a):
    try:
        r = subprocess.run(["git", "-C", root, *a], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def write_baseline(root, findings):
    """按规格「Baseline 文件」的结构写盘。⛔ 只记 delta 规则用得到的字段。"""
    fc = sorted({(f["file"], f["line"]) for f in findings if f["rule_id"] == "state/forbidden-content"})
    dl = sorted({f["message"].split(" ")[0] for f in findings if f["rule_id"] == "health/dead-link"})
    px = sorted({f["message"].split("：")[0].replace("未知前缀 ", "")
                 for f in findings if f["rule_id"] == "id/unknown-prefix"})
    size = next((f["actual"] for f in findings if f["rule_id"] == "state/total-size-cap"), 0)
    sp = os.path.join(root, ".claude", "rules", "devdocs-state.md")
    if not size and os.path.isfile(sp):
        size = os.path.getsize(sp)
    path = os.path.join(root, BASELINE_REL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    import datetime
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"schema: {BASELINE_SCHEMA}\n")
        fh.write(f"generated_at: {datetime.datetime.now().astimezone().isoformat()}\n")
        fh.write(f"source_git_commit: {_git(root, 'rev-parse', 'HEAD') or 'unknown'}\n")
        fh.write("baseline_findings:\n")
        fh.write("  state/total-size-cap:\n")
        fh.write(f"    devdocs_state_size_bytes: {size}\n")
        fh.write("  state/forbidden-content:\n")
        fh.write(f"    count: {len(fc)}\n")
        fh.write("    lines: [" + ", ".join(f'"{a}:{b}"' for a, b in fc) + "]\n")
        fh.write("  health/dead-link:\n")
        fh.write(f"    count: {len(dl)}\n")
        fh.write("    refs: [" + ", ".join(f'"{x}"' for x in dl) + "]\n")
        fh.write("  id/unknown-prefix:\n")
        fh.write("    prefixes: [" + ", ".join(px) + "]\n")
        fh.write("notes: |\n  首次扫描快照；新增违规以此为基线计算 delta。\n"
                 "  ⛔ 本文件只是本机噪声抑制，不是语义审批；推荐 gitignore。\n")
    return path


def read_baseline(root):
    """⛔ 不是通用 YAML 解析器——只读本脚本自己写的固定结构。

    手改后格式不符会报 health/baseline-corrupt，这是有意的：baseline 是机器快照，
    不是给人编辑的配置。
    """
    path = os.path.join(root, BASELINE_REL)
    if not os.path.isfile(path):
        return None, "health/baseline-missing"
    try:
        txt = open(path, encoding="utf-8").read()
        if not re.match(r"^schema:\s*" + re.escape(BASELINE_SCHEMA) + r"\s*$", txt.split("\n")[0]):
            return None, "health/baseline-corrupt"
        def lst(key, quoted=True):
            m = re.search(r"^\s+" + re.escape(key) + r":\s*\[(.*?)\]\s*$", txt, re.M)
            if not m:
                raise ValueError(f"缺字段或列表未闭合：{key}")
            body = m.group(1).strip()
            if not body:
                return set()
            # ⛔ 逐元素比对写入器的形状：`["a", "b"]`（引号）/ `[D, X]`（裸词）。
            # 只验方括号闭合不够——`["AC-001]` 也能过，strip('"') 会把它洗成合法值，
            # 于是坏掉的 baseline 静默压制掉真实违规。
            rx = ELEM_QUOTED if quoted else ELEM_BARE
            parts = [x.strip() for x in body.split(",")]
            for x in parts:
                if not rx.match(x):
                    raise ValueError(f"元素格式不符：{key} → {x}")
            return {x.strip('"') for x in parts}
        m = re.search(r"^\s+devdocs_state_size_bytes:\s*(\d+)\s*$", txt, re.M)
        if not m:
            raise ValueError("缺字段：devdocs_state_size_bytes")
        # ⛔ 缺字段一律判 corrupt，不得回落默认值——size 回落 0 会静默解除
        # total-size-cap 的压制，把「baseline 坏了」变成「体积没超」
        return {"size": int(m.group(1)),
                "forbidden": lst("lines"), "dead": lst("refs"),
                "prefixes": lst("prefixes", quoted=False)}, None
    except Exception:
        return None, "health/baseline-corrupt"


def apply_baseline(findings, bl):
    """按规格「Delta 计算规则」过滤。⛔ 规格未定义 delta 的 rule 一律不过滤。"""
    out = []
    for f in findings:
        r = f["rule_id"]
        if r == "state/total-size-cap":
            delta = (f["actual"] or 0) - bl["size"]
            # ⛔ delta 过滤不得吞掉严重度升级 —— realign.md「有 baseline」行要求
            # delta ≥ 2 KiB / warn→blocker 升级 / baseline 不可读 三者之一即提示
            base_sev = "blocker" if bl["size"] > SIZE_BLOCK else "warning" if bl["size"] > SIZE_WARN else None
            escalated = f["severity"] == "blocker" and base_sev != "blocker"
            if delta < SIZE_DELTA_IGNORE and not escalated:
                continue
            note = f"（较 baseline +{delta} bytes"
            note += "，且已由 warning 升级为 blocker）" if escalated else "）"
            f = dict(f, message=f["message"] + note)
        elif r == "state/forbidden-content":
            if f"{f['file']}:{f['line']}" in bl["forbidden"]:
                continue
        elif r == "health/dead-link":
            if f["message"].split(" ")[0] in bl["dead"]:
                continue
        elif r == "id/unknown-prefix":
            if f["message"].split("：")[0].replace("未知前缀 ", "") in bl["prefixes"]:
                continue
        out.append(f)
    return out


def scan_project(root, files=None, ref_only=None):
    """project scope 的 6 条 rule。files=None 时自行遍历 docs/devdocs/。

    ⛔ ref_only 只收窄「报告哪些文件的引用」，定义索引恒取 files 全量——
    增量扫描若同时缩定义索引，引用未改动文件里的合法编号会误报 dead-link。
    """
    devdocs = os.path.join(root, 'docs', 'devdocs')
    if not os.path.isdir(devdocs):
        return []
    if files is None:
        files = collect_files(devdocs)

    rel = lambda p: os.path.relpath(p, root)
    docs = {}
    for f in files:
        try:
            lines = open(f, encoding="utf-8", errors="replace").read().split("\n")
        except OSError as e:
            print(f"lint error: {f}: {e}", file=sys.stderr)
            continue
        docs[f] = (lines, strip_code_blocks(lines))

    # ---- Phase A：定义索引（⛔ 不从 devdocs-state.md 取上界）----
    defined, def_end = set(), {}
    for f, (lines, mask) in docs.items():
        for i, ln in enumerate(lines):
            if mask[i]:
                continue
            for rx in (DEF_HEADING, DEF_TABLE, DEF_LIST):
                m = rx.match(ln)
                if m:
                    defined.add(f"{m.group(1)}-{int(m.group(2))}{m.group(3)}")
                    def_end[(f, i)] = m.end()
                    break
    derived_caps = {}
    for d in defined:
        t, n = key_parts(d)
        derived_caps[t] = max(derived_caps.get(t, 0), n)

    findings = []

    # ---- Phase B：引用扫描 ----
    dead = {}
    for f, (lines, mask) in docs.items():
        if ref_only is not None and f not in ref_only:
            continue
        for i, ln in enumerate(lines):
            if mask[i]:
                continue
            # ⛔ 只排除定义 occurrence 本身，不排整行——追溯矩阵
            # `| F-001 | US-001 | AC-001 |` 的首列是定义，其余列是必须查的引用
            dend = def_end.get((f, i), 0)
            refs = []  # (归一化 key, 文件里的原始拼写)
            for m in RANGE_RE.finditer(ln):
                if m.start() < dend:
                    continue
                t, a, b = m.group(1), int(m.group(2)), int(m.group(3))
                if b >= a and b - a <= 500:
                    w = len(m.group(2))
                    refs += [(f"{t}-{n}", f"{t}-{n:0{w}d}") for n in range(a, b + 1)]
            for m in ID_RE.finditer(ln):
                if m.start() < dend:
                    continue
                refs.append((f"{m.group(1)}-{int(m.group(2))}{m.group(3)}", m.group(0)))
            for r, raw in refs:
                if r in defined:
                    continue
                t, n = key_parts(r)
                sub = "out-of-range" if n > derived_caps.get(t, 0) else "missing-definition"
                dead.setdefault((rel(f), raw, sub), []).append(i + 1)
    for (fp, r, sub), occ in sorted(dead.items()):
        hint = ("超出资源文件中该类型的最大已定义编号，可能是未来引用或拼写错误"
                if sub == "out-of-range" else "编号在声明范围内但找不到定义；可能拼写错误 / 未创建 / 已删除")
        findings.append(find("health/dead-link", "blocker", fp, occ[0],
                             f"{r} 无定义（{sub}）：{hint}", ctx=f"occurrences: {occ[:10]}", auto=False))

    # ---- id/unknown-prefix：按 prefix 聚合，⛔ 只报不判 ----
    agg = {}
    for f, (lines, mask) in docs.items():
        if ref_only is not None and f not in ref_only:
            continue
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
    return findings


def selftest():
    """最小可跑自检：造夹具 → 断言每条 rule 都命中/不命中。

    ⛔ 不是完整测试套件。它只保证"规格改了脚本没跟上"时会响。
    """
    import io, tempfile, shutil
    t = tempfile.mkdtemp()
    try:
        # --- project scope 夹具 ---
        dd = os.path.join(t, "docs", "devdocs"); os.makedirs(os.path.join(dd, "_archived"))
        os.makedirs(os.path.join(t, ".claude", "rules"))
        open(os.path.join(dd, "01.md"), "w").write(
            "## F-001 x\n- AC-001 a\n- AC-002 b\n  - **AC-010** 缩进列表定义，⛔ 不得报无定义\n"
            "引用 AC-003 与范围 AC-001~002。决策 D-014。外部单号 SIDM-71103。\n"
            "## AC-004a 后缀定义\n引用 AC-004b\n"          # 后缀参与身份

            "| F-001 | AC-009 | 追溯矩阵行 |\n"              # 首列定义，同行引用仍须查
            "```\nAC-777 代码块内不算\n```\n")
        open(os.path.join(dd, "_archived", "old.md"), "w").write("## AC-555 归档不进索引\n")
        open(os.path.join(t, ".claude", "rules", "devdocs-state.md"), "w").write(
            "# s\n## 编号状态\n| 类型 | 当前最大 |\n|---|---|\n| AC | AC-001 |\n"
            "- T-01 done trade@0c263bf4d4 净 -85 LOC +184/-5 见 src/F.java:L5\n"
            "- " + "长" * 600 + "\n")
        # --- 布局清单解析 ---
        lay = os.path.join(t, "devdocs-layout.md")
        open(lay, "w").write(
            "# 布局清单\n\n"
            "| 相对路径模式 | owner | 主文件 |\n"
            "|---|---|---|\n"
            "| `01-requirements.md` | requirements | — |\n"
            "| `03-test-{unit,integration,e2e}.md` | test-cases | `03-test-cases.md` |\n"
            "| `04-dev-tasks-p<N>.md` | dev-tasks | `04-dev-tasks.md` |\n"
            "| `patterns/<slug>.md` | compound | — |\n"
            "| `audit/**/<slug>.yaml` | dev-workflow | — |\n")
        rows = load_layout(lay)
        if len(rows) != 5:
            print(f"FAIL load_layout: 期望 5 行，实得 {len(rows)}", file=sys.stderr)
            return 1
        cases = [("01-requirements.md", 0), ("03-test-e2e.md", 1),
                 ("04-dev-tasks-p12.md", 2), ("patterns/sqlite-wal.md", 3),
                 ("audit/x/y/T-01-external-review.yaml", 4)]
        for relpath, idx in cases:
            if not rows[idx][0].fullmatch(relpath):
                print(f"FAIL load_layout: 模式 {idx} 匹配不到 {relpath}", file=sys.stderr)
                return 1
        if rows[1][2] != "03-test-cases.md" or rows[0][2] is not None:
            print("FAIL load_layout: 主文件列解析错（— 应为 None）", file=sys.stderr)
            return 1
        try:
            load_layout(os.path.join(t, "nope.md"))
        except RuntimeError:
            pass
        else:
            print("FAIL load_layout: 清单缺失应抛 RuntimeError，静默空表会把所有文件判成待分类",
                  file=sys.stderr)
            return 1
        # --- skills scope 夹具 ---
        sk = os.path.join(t, "sk"); os.makedirs(os.path.join(sk, "good"))
        os.makedirs(os.path.join(sk, "bad")); os.makedirs(os.path.join(sk, "empty"))
        open(os.path.join(sk, "good", "SKILL.md"), "w").write("---\nname: good\n---\n引用 [x](../bad/SKILL.md)\n")
        os.makedirs(os.path.join(sk, "edge"))
        open(os.path.join(sk, "edge", "SKILL.md"), "w").write(
            "---\nname: edge\n---\n" + "行\n" * 497)     # 恰好 500 行 == 上限，合规
        open(os.path.join(sk, "bad", "SKILL.md"), "w").write(
            "---\nname: WRONG\n---\n" + "行\n" * 501 + "死链 [y](../nope/SKILL.md)\n调 `/good --ghost`\n")

        want = {
            "health/dead-link": 3,        # AC-003 + AC-004b（后缀）+ AC-009（定义行同行）
            "id/unknown-prefix": 1,       # D（SIDM 限位数排除）
            "state/forbidden-content": 1,
            "state/line-length-cap": 1,
            "state/max-id-stale": 2,      # AC: 表 1 < 实际 2(stale) + F: 表无该行(missing-row)
            "skill/name-mismatch": 2,     # bad 名不符 + empty 无 SKILL.md
            "skill/size-cap": 1,
            "skill/dead-link": 1,
            "flag/dangling-reference": 1,
        }
        got = {}
        for f in scan_project(t) + scan_skill_flags(sk) + scan_skill_repo(sk):
            got[f["rule_id"]] = got.get(f["rule_id"], 0) + 1
        # --- 计数夹具覆盖不到的两条静默失效，直接断言 ---
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit([find("x/y", "warning", "f.md", 1, 'msg', ctx='含 "引号" 与 \\ 反斜杠')])
        ctx_line = next(l for l in buf.getvalue().split("\n") if l.startswith("  context: "))
        try:
            json.loads(ctx_line[len("  context: "):])   # YAML 双引号标量 ≡ JSON 字符串
        except ValueError:
            print(f"FAIL emit: context 未转义，产出非法 YAML：{ctx_line}", file=sys.stderr)
            return 1
        # apply_baseline 的严重度升级：夹具计数覆盖不到（delta 过滤在 baseline 路径上），
        # 而它恰恰是最容易在重构中被当成冗余删掉的一行。⛔ 删了就是静默放过跨阈值增长。
        bl_warn = {"size": 39909, "forbidden": [], "dead": [], "prefixes": []}
        esc = find("state/total-size-cap", "blocker", "s.md", None, "已 41009 bytes", 41009, SIZE_BLOCK)
        if not apply_baseline([esc], bl_warn):
            print("FAIL apply_baseline: warning→blocker 升级被 delta 过滤吞掉（delta<2KiB）", file=sys.stderr)
            return 1
        noop = find("state/total-size-cap", "warning", "s.md", None, "已 40009 bytes", 40009, SIZE_WARN)
        if apply_baseline([noop], bl_warn):
            print("FAIL apply_baseline: 未升级的小增长（delta<2KiB）应被过滤却报出", file=sys.stderr)
            return 1

        # changed_set 的三条红线：静默全漏扫 + exit 0，是本脚本最难发现的失效
        # （不崩溃、CI 绿）。已在此栽过两次，故三个方向各钉一条。git 缺失时跳过。
        if shutil.which("git"):
            g = os.path.join(t, "gitfix"); os.makedirs(os.path.join(g, "sub", "docs", "devdocs"))
            tracked = os.path.join(g, "sub", "docs", "devdocs", "01.md")
            open(tracked, "w").write("## F-001 x\n")
            run = lambda *a: subprocess.run(["git", "-C", g, *a], capture_output=True, text=True)
            run("init", "-q"); run("add", "-A")
            run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
            open(tracked, "a").write("引用 AC-007\n")                      # 已跟踪文件的改动
            untracked = os.path.join(g, "sub", "docs", "devdocs", "02.md")
            open(untracked, "w").write("## F-002 y\n")                     # 未跟踪的新文件
            cs = changed_set(os.path.join(g, "sub"))                        # ⛔ target 是子目录
            for path, why in ((tracked, "仓根相对路径未按 toplevel 归一 → 子目录 target 全对不上"),
                              (untracked, "未跟踪文件缺失 → 新建文档整份漏扫")):
                if os.path.realpath(path) not in cs:
                    print(f"FAIL changed_set: {os.path.basename(path)} 不在变更集（{why}）", file=sys.stderr)
                    return 1
            # 方向 1 的判例选「已 add 未 commit」而不是「非 git 目录」：后者会在
            # rev-parse 取下标时偶然抛 IndexError，断言看似通过、实则没验到红线。
            # 这里 rev-parse 正常而 `diff HEAD` 失败（无 HEAD），已暂存文件正是会被漏掉的那批。
            ng = os.path.join(t, "nocommit"); os.makedirs(ng)
            open(os.path.join(ng, "a.md"), "w").write("x\n")
            subprocess.run(["git", "-C", ng, "init", "-q"], capture_output=True)
            subprocess.run(["git", "-C", ng, "add", "-A"], capture_output=True)
            try:
                changed_set(ng)
            except Exception:
                pass
            else:
                print("FAIL changed_set: git diff 失败未抛 → 已暂存文件会被当成「没有变更」静默漏扫",
                      file=sys.stderr)
                return 1

        bp = os.path.join(t, ".claude", "rules", os.path.basename(BASELINE_REL))
        for bad_bl, why in (
            (f"schema: {BASELINE_SCHEMA}\n  devdocs_state_size_bytes: 1\n  refs: [AC-001\n", "缺字段/列表未闭合"),
            (f"schema: {BASELINE_SCHEMA}\n  devdocs_state_size_bytes: 1\n"
             '  lines: []\n  refs: ["AC-001]\n  prefixes: []\n', "元素引号未闭合"),
        ):
            open(bp, "w").write(bad_bl)
            if read_baseline(t)[1] != "health/baseline-corrupt":
                print(f"FAIL read_baseline: 畸形 baseline({why}) 未判 corrupt", file=sys.stderr)
                return 1
        os.remove(bp)

        bad = [(k, want[k], got.get(k, 0)) for k in want if got.get(k, 0) != want[k]]
        extra = sorted(set(got) - set(want))
        for k, w, g in bad:
            print(f"FAIL {k}: 期望 {w} 条，实得 {g}", file=sys.stderr)
        for k in extra:
            print(f"FAIL 未预期的 rule: {k} ({got[k]} 条)", file=sys.stderr)
        if bad or extra:
            return 1
        print(f"selftest OK —— {len(want)} 条 rule 全部命中预期", file=sys.stderr)
        return 0
    finally:
        shutil.rmtree(t, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="health-lint v1 (10/12 rules)")
    ap.add_argument("--target", default=".", help="项目根（含 docs/devdocs/）")
    ap.add_argument("--changed-only", action="store_true", help="仅扫 git diff HEAD 变更的文件")
    ap.add_argument("--fix", metavar="RULE_ID", help="仅运行指定 rule")
    ap.add_argument("--selftest", action="store_true", help="跑内置夹具自检")
    ap.add_argument("--baseline-init", action="store_true", help="写 baseline 快照，不报告违规")
    ap.add_argument("--since-baseline", action="store_true", help="只报告 baseline 之后新增的违规")
    ap.add_argument("--skills-dir", metavar="DIR",
                    help="改扫 skill 库，只跑 flag/dangling-reference（⛔ 与 --target 的 project-scope rule 互斥）")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if args.skills_dir:
        sd = os.path.abspath(args.skills_dir)
        if not os.path.isdir(sd):
            print(f"lint error: {sd} 不存在", file=sys.stderr)
            return 3
        fs = scan_skill_flags(sd) + scan_skill_repo(sd)
        fs.sort(key=lambda f: (f["file"], f["line"] or 0))
        if args.fix:
            fs = [f for f in fs if f["rule_id"] == args.fix]
        emit(fs)
        sys.stdout.flush()
        bl = sum(1 for f in fs if f["severity"] == "blocker")
        print(f"\n# skills-dir scan | blocker={bl} warning={len(fs) - bl}", file=sys.stderr)
        return 2 if bl else (1 if fs else 0)

    root = os.path.abspath(args.target)
    devdocs = os.path.join(root, "docs", "devdocs")
    if not os.path.isdir(devdocs):
        print(f"not_applicable: {devdocs} 不存在", file=sys.stderr)
        return 0

    files = collect_files(devdocs)
    ref_only = None
    if args.changed_only:
        try:
            changed = changed_set(root)
        except Exception as e:
            print(f"health/git-unavailable: {e}", file=sys.stderr)
            return 3
        ref_only = {f for f in files if os.path.realpath(f) in changed}
    findings = scan_project(root, files, ref_only)

    if args.baseline_init:
        path = write_baseline(root, findings)
        print(f"# baseline 已写入 {os.path.relpath(path, root)}"
              f"（{len(findings)} 条现状快照，⛔ 未报告违规）\n"
              f"# 建议 gitignore —— 它是本机噪声抑制，不是语义审批", file=sys.stderr)
        return 0

    if args.since_baseline:
        bl, err = read_baseline(root)
        if err:
            print(f"{err}: {os.path.join(root, BASELINE_REL)}", file=sys.stderr)
            return 3
        before = len(findings)
        findings = apply_baseline(findings, bl)
        print(f"# since-baseline: {before} → {len(findings)} 条"
              f"（抑制 {before - len(findings)} 条存量）", file=sys.stderr)

    if args.fix:
        findings = [f for f in findings if f["rule_id"] == args.fix]

    emit(findings)

    sys.stdout.flush()
    blockers = sum(1 for f in findings if f["severity"] == "blocker")
    warnings = len(findings) - blockers
    print(f"\n# scanned {len(files)} files | blocker={blockers} warning={warnings}"
          + ("" if os.path.isfile(os.path.join(root, ".claude", "rules", "devdocs-state.md"))
             else " | devdocs-state.md: not_applicable"), file=sys.stderr)
    print("# not_implemented(v1): design/adr-only-revision, submodule/pointer-drift", file=sys.stderr)
    return 2 if blockers else (1 if warnings else 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"lint error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)
