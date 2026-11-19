"""tasks.v2 / backlog.v2 → state/。只认几种实际出现过的形态，其余一律进报告「未识别」。"""
from __future__ import annotations

import glob
import json
import os
import re
from collections import Counter
from datetime import date
from typing import Any

from . import backlog, render, schema, store, tasks
from .common import dump
from .store import BEGIN, END, KeelError, Project

COLUMN_ALIASES = {
    "#": "id", "id": "id", "编号": "id", "任务": "id", "描述": "title", "标题": "title", "任务名称": "title",
    "状态": "status", "status": "status", "profile": "review_profile", "review_profile": "review_profile",
    "档": "review_profile", "依赖": "depends_on", "来源": "source", "层": "layer", "层级": "layer",
    "commits": "commits", "已提交？": "commits", "ext_review_state": "ext_review_state", "备注": "note",
}
STATUS_ALIASES = {
    "待开发": "待开发", "todo": "待开发", "⬜": "待开发", "进行中": "进行中", "🔄": "进行中",
    "review_pending": "review_pending", "已完成": "已完成", "✅": "已完成", "done": "已完成", "已归档": "已归档",
}
PROP_DROP = ("status", "commits", "ext_review_state")
EMPTY = ("", "—", "-", "无", "n/a")
REPORT = ".keel/migration-report.md"
ARCHIVE = "docs/devdocs/audit/migration-v3.md"
BL_SAVED = "docs/devdocs/audit/migration-v3-backlog.md"  # backlog/index.md 已存在时，手写 backlog.md 原文存这里
ROLLBACK = "git checkout -- docs/devdocs && git clean -fd docs/devdocs && rm -rf docs/devdocs/state .keel/manifest.json"
RP_REASON = {"fast": "deferred-fast", "guarded": "deferred-guarded"}
MAIN = "04-dev-tasks.md"
_H4 = re.compile(r"####\s+(T-[A-Za-z0-9-]*)\s*[:：]\s*(.*)")
_H2 = re.compile(r"##\s+(T-[A-Za-z0-9-]*)\s*·\s*(.*)")
_PROP = re.compile(r"\|\s*\*\*(.+?)\*\*\s*\|(.*)\|\s*$")
_TOKEN = re.compile(r"T-[A-Za-z0-9-]+")
_DEP = re.compile(r"\bT-\d+(?![A-Za-z0-9-])")
_BQ = re.compile(r">\s*\*\*状态[^*]*\*\*\s*[：:]?\s*(.*)")
_DATE_PAREN = re.compile(r"[（(]\d{4}-\d{2}-\d{2}[）)]")
_SEP = re.compile(r"\|[\s|:-]+")
_BL_HEAD = re.compile(r"###\s+([A-Z]+-\d+[a-z]?)(?:#(\d+))?(?:\s+-\s+(.*))?\s*$")
_YAML = re.compile(r"^```ya?ml\n(.*?)^```", re.S | re.M)
_FM_V2 = re.compile(r"^(spec_version:\s*[\"']?(?:tasks|backlog)\.)v2\b", re.M)


def _bump(text: str) -> str:
    m = store._FM_RE.match(text)
    return text if not m else text[:m.start(1)] + _FM_V2.sub(r"\g<1>v3", m.group(1)) + text[m.end(1):]


def _bare(v: str) -> str:
    return " ".join(re.sub(r"[`*]", "", v).split())


def _flat(v: str) -> str:
    return " ".join(v.split())


def _cells(line: str) -> list[str]:
    s = line.strip()[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def _scalar(v: str) -> Any:
    v = v.strip()
    if v[:1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v.strip('"')
    if v[:1] == "'":
        return v[1:-1].replace("''", "'")
    return None if v in ("", "null", "~") else v


def _yaml(text: str) -> dict[str, Any]:
    """shortcut: 只认单行 `key: value` 与 `[a, b]`；块列表 / 多行值丢弃，遇到再扩。"""
    d: dict[str, Any] = {}
    for line in text.split("\n"):
        m = re.match(r"([A-Za-z_]\w*):\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            d[m.group(1)] = [_scalar(x) for x in v[1:-1].split(",") if x.strip()] if v[:1] == "[" and v[-1:] == "]" \
                else _scalar(v)
    return d


def _status_text(v: str) -> str:
    """状态自由文本取到第一个括号 / 冒号 / 句读之前，如「关闭（用户裁定 …）：…」→「关闭」。"""
    return re.split(r"[（(：:。，,；;]", _bare(v))[0].strip()


class _Task:
    def __init__(self, where: str) -> None:
        self.where = where
        self.fields: dict[str, tuple[str, str]] = {}  # 字段 -> (原文, 文件)
        self.status: list[tuple[str, str, bool]] = []  # (原值, 位置, 是否主文件汇总表)
        self.moved: list[tuple[str, str, str]] = []  # (文件, 字段, 原文)


class Migration:
    def __init__(self, project: Project, maps: list[str]) -> None:
        self.p, self.today = project, date.today().isoformat()
        self.in_git = store._git(project.root, "rev-parse", "--git-dir") is not None
        self.map: dict[str, str] = {}
        for m in maps:
            k, _, v = m.rpartition("=")
            if not k or v not in schema.TASK_STATUSES:
                raise KeelError(f"--map-status {m!r} 不对：写成 原值=目标值，目标限 " + " / ".join(schema.TASK_STATUSES), 2)
            self.map[k.strip()] = v
        self.have_t = set(tasks.load_all(project)[0])
        self.have_b = set(backlog.load_all(project)[0])
        self.raw: dict[str, _Task] = {}
        self.unknown: list[str] = []
        self.pending: Counter[str] = Counter()
        self.conflicts: list[str] = []
        self.rp_filled: list[str] = []
        self.prop_rows: list[tuple[str, int, str]] = []
        self.tables: list[tuple[int, int, list[tuple[int, str | None]]]] = []  # 主文件汇总表 (起, 止, 行)
        self.texts: dict[str, str] = {}
        files = sorted(glob.glob(os.path.join(project.devdocs, "04-dev-tasks*.md")), key=lambda f: (f != MAIN, f))
        for f in files:
            rel = os.path.basename(f)
            with open(f, encoding="utf-8") as fh:
                self.texts[rel] = fh.read()
            self._scan(rel, self.texts[rel].split("\n"))
        main = self.texts.get(MAIN, "")
        if (BEGIN in main or END in main) and store.region_text(main) is None:
            raise KeelError("04-dev-tasks.md 里 keel 生成区标记重复或顺序不对，先手工修好再迁移", 3)
        self.tasks = self._build()
        self.entries: dict[str, dict[str, Any]] = {}
        self.sections: dict[str, str] = {}  # 集中形态：锚点 -> 原节正文，apply 时落成 backlog/<slug>.md
        self._scan_backlog()
        old = self._read(store.BACKLOG_MD)  # backlog.md 会整份重新生成：人写的原文另存
        human = bool(old) and "generated_by: keel" not in old and bool(self.entries or self.have_b)
        # ⛔ 原文一律另存：不在 git 里（或被 gitignore）时没有别的副本
        self.bl_save = "" if not human else "docs/devdocs/backlog/index.md" \
            if not os.path.exists(os.path.join(project.devdocs, "backlog", "index.md")) else BL_SAVED
        self.bl_note = [f"- backlog.md 原文 → {self.bl_save[len('docs/devdocs/'):]}"] if human else []

    def _unk(self, where: str, why: str, text: str) -> None:
        self.unknown.append(f"{where} · {why} · {_flat(text)[:60]}")

    def _tid(self, raw: str, where: str, line: str) -> str | None:
        if schema.TASK_ID.fullmatch(raw):
            return raw
        self._unk(where, "编号不是 T-<数字>", line)
        return None

    def _put(self, tid: str, key: str, raw: str, rel: str, where: str, main: bool = False) -> None:
        t = self.raw.setdefault(tid, _Task(where))
        if _bare(raw).lower() in EMPTY:
            return
        if key == "status":
            t.status.append((_bare(raw), where, main))
        elif key == "note":
            t.moved.append((rel, "备注", raw.strip()))
        elif key not in t.fields:
            t.fields[key] = (raw, rel)

    def _scan(self, rel: str, lines: list[str]) -> None:
        fence = region = False
        cur = sec = None  # 当前 #### 任务卡 / ## T-n · 节（节内只取第一条状态引用）
        i = 0
        while i < len(lines):
            s, where = lines[i].strip(), f"{rel}:{i + 1}"
            if s in (BEGIN, END):
                region = s == BEGIN
            elif s.startswith("```"):
                fence = not fence
            elif fence or region:
                pass
            elif s.startswith("#"):
                cur = sec = None
                m = _H4.fullmatch(s) or _H2.fullmatch(s)
                if m and (tid := self._tid(m.group(1), where, s)):
                    self._put(tid, "title", m.group(2), rel, where)
                    cur, sec = (tid, None) if s.startswith("####") else (None, tid)
            elif sec and (q := _BQ.match(s)):
                self._put(sec, "status", _status_text(q.group(1)), rel, where)
                sec = None
            elif s.startswith("|"):
                j = i
                while j < len(lines) and lines[j].strip().startswith("|"):
                    j += 1
                self._table(rel, lines, i, j, cur)
                i = j
                continue
            i += 1

    def _table(self, rel: str, lines: list[str], a: int, b: int, cur: str | None) -> None:
        if cur:  # ① #### T-n 后的属性表
            for k in range(a, b):
                m = _PROP.match(lines[k].strip())
                key = COLUMN_ALIASES.get(_bare(m.group(1)).lower()) if m else None
                if m and key and key != "id":
                    self._put(cur, key, m.group(2), rel, f"{rel}:{k + 1}")
                    if key in PROP_DROP:
                        self.prop_rows.append((rel, k, cur))
            return
        head = [_bare(h).lower() for h in _cells(lines[a])]
        cols = [COLUMN_ALIASES.get(h) for h in head]
        cols[1:] = ["title" if c == "id" else c for c in cols[1:]]  # `# | 任务 | …`：首列是编号，「任务」是标题
        if not any(c not in (None, "id", "note") for c in cols[1:]):
            return
        start = a + 2 if a + 1 < b and _SEP.fullmatch(lines[a + 1].strip()) else a + 1
        if cols[0] != "id":  # 像汇总表但首列表头不认识：T- 行全部报出
            for k in range(start, b):
                if _bare(_cells(lines[k])[0]).startswith("T-"):
                    self._unk(f"{rel}:{k + 1}", "汇总表首列表头不是 ID/编号/任务", lines[k])
            return
        rows: list[tuple[int, str | None]] = []
        for k in range(start, b):
            cells, where = _cells(lines[k]), f"{rel}:{k + 1}"
            tok = _TOKEN.match(_bare(cells[0]))
            tid = self._tid(tok.group(0), where, lines[k]) if tok else None
            if not tok:
                self._unk(where, "首列没有任务编号", lines[k])
            elif tid and head[0] == "#":  # `#` 表的状态写在编号后缀：`T-168 ✅`
                self._put(tid, "status", _DATE_PAREN.sub("", _bare(cells[0])[tok.end():]), rel, where, rel == MAIN)
            rows.append((k, tid))
            for c, key in enumerate(cols[1:], 1):
                if tid and key and key != "id" and c < len(cells):
                    self._put(tid, key, cells[c], rel, where, rel == MAIN)
        if rel == MAIN:
            self.tables.append((a, b, rows))

    def _fit(self, t: _Task, label: str, raw: str, cap: int, rel: str) -> str:
        """schema 会拒的文本（超长、`<!--`）截成单行；原文搬进 audit 记录。"""
        flat = _flat(raw)
        s = flat.replace("<!--", "")
        if len(s) > cap:
            s = s[:cap - 1] + "…"
        if s != flat:
            t.moved.append((rel, label, raw.strip()))
        return s

    def _norm(self, v: str) -> str | None:
        hit = self.map.get(v) or STATUS_ALIASES.get(v) or STATUS_ALIASES.get(v.lower())
        if hit:
            return hit
        each = {STATUS_ALIASES.get(x) or STATUS_ALIASES.get(x.lower()) for x in v.split()}
        return each.pop() if len(each) == 1 and None not in each else None  # 「✅ 已完成」各词同指一个状态

    def _build(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for tid, t in self.raw.items():
            if tid in self.have_t:
                continue
            for v, _w, _m in t.status:
                if self._norm(v) is None:
                    self.pending[v] += 1
            if len({self._norm(v) or v for v, _w, _m in t.status}) > 1:
                self.conflicts.append(f"{tid}：" + "；".join(f"{w} `{v}`" for v, w, _m in t.status))
            pick = [x for x in t.status if x[2]] or t.status
            if not pick or "title" not in t.fields:
                self._unk(t.where, "缺状态来源" if not pick else "缺标题", tid)
                continue
            if (status := self._norm(pick[0][0])) is None:
                continue  # 已计入「待映射状态」
            f = t.fields
            title = self._fit(t, "标题", f["title"][0], schema.TEXT_CAPS["title"], f["title"][1])
            d = schema.new_task(tid, title, "dev-tasks", status=status)
            for k in ("source", "layer"):
                if k in f:
                    d[k] = self._fit(t, k, f[k][0], schema.TEXT_CAPS.get(k, 10 ** 6), f[k][1])
            if "review_profile" in f:
                d["review_profile"] = _bare(f["review_profile"][0]).lower()
            if "ext_review_state" in f:
                d["ext_review_state"] = _bare(f["ext_review_state"][0])
            if "depends_on" in f:
                d["depends_on"] = list(dict.fromkeys(_DEP.findall(_bare(f["depends_on"][0]))))
            if status == "review_pending":  # 迁移来的 review_pending 补齐必填字段；audit / 缺档位不猜
                reason = RP_REASON.get(d["review_profile"] if "review_profile" in f else "")
                if not reason:
                    self.pending[f"{pick[0][0]}（review_pending，档位 {d['review_profile'] if 'review_profile' in f else '缺失'}）"] += 1
                    continue
                d.update(batch="migrated-v3", due=self.today, pending_reason=reason)
                self.rp_filled.append(f"- {tid}：batch=migrated-v3，due={self.today}，pending_reason={reason}")
            if "commits" in f:
                raw, rel = f["commits"]
                refs = [x for x in re.split(r"[\s,，;；]+", _bare(raw)) if x]
                if refs and all(schema.COMMIT_REF.fullmatch(r) for r in refs):
                    d["commits"] = [{"ref": r, "note": f"迁移自 {rel}"} for r in refs]
                else:
                    t.moved.append((rel, "commits", raw.strip()))
            if t.moved or os.path.isdir(os.path.join(self.p.devdocs, "audit", tid)):
                d["record"] = f"audit/{tid}/"
            out[tid] = d
        while True:  # 依赖指向未迁移任务时去掉并报出；校验失败的剔除后再算一轮
            known = set(out) | self.have_t
            bad = []
            for tid, d in out.items():
                drop = [x for x in d["depends_on"] if x not in known]
                if drop:
                    d["depends_on"] = [x for x in d["depends_on"] if x in known]
                    self._unk(self.raw[tid].where, f"{tid} 的依赖 {'、'.join(drop)} 未迁移，已从 depends_on 去掉", tid)
                if errs := schema.validate_task(d, known):
                    self._unk(self.raw[tid].where, "校验失败：" + errs[0], tid)
                    bad.append(tid)
            if not bad:
                return out
            for tid in bad:
                del out[tid]

    def _entry(self, y: dict[str, Any], title: str, detail: str, where: str) -> None:
        sid, no = y.get("source_id"), y.get("entry_no")
        if not sid and isinstance(y.get("id"), str):
            sid, _, n = y["id"].partition("#")
            no = no or n
        e = schema.new_backlog(str(sid), 1, str(y.get("created_by_skill") or ""), "", str(y.get("created_at") or ""))
        e["entry_no"] = int(str(no)) if str(no).isdigit() else no
        e.update({k: y[k] for k in ("status", "related_ids", "target_flow", "target_id", "reason", "superseded_by",
                                    "updated_at") if y.get(k) is not None})
        note = _flat(str(y.get("note") or title)).replace("<!--", "")
        e["note"] = note if len(note) <= 200 else note[:199] + "…"  # 全文留在 detail 文件
        e["detail"] = detail
        anchor = f"{sid}#{no}"
        if errs := schema.validate_backlog(e):
            self._unk(where, "backlog 校验失败：" + errs[0], anchor)
        elif anchor in self.entries:
            self._unk(where, "backlog 锚点重复", anchor)
        elif anchor not in self.have_b:
            self.entries[anchor] = e

    def _scan_backlog(self) -> None:
        for f in sorted(glob.glob(os.path.join(self.p.devdocs, "backlog", "*.md"))):
            rel = "backlog/" + os.path.basename(f)
            if rel == "backlog/index.md":
                continue
            with open(f, encoding="utf-8") as fh:
                text = fh.read()
            m, h = _YAML.search(text), _BL_HEAD.match(text.split("\n", 1)[0])
            if not m:
                self._unk(f"{rel}:1", "没有 yaml 块", text)
                continue
            self._entry(_yaml(m.group(1)), (h.group(3) or "") if h else "", rel, f"{rel}:1")
        path = os.path.join(self.p.root, store.BACKLOG_MD)
        if not os.path.isfile(path):
            return
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        heads = [i for i, s in enumerate(lines) if s.startswith(("## ", "### "))] + [len(lines)]
        for a, b in zip(heads, heads[1:]):
            h = _BL_HEAD.match(lines[a])
            if not h:
                continue
            sec = "\n".join(lines[a:b]).rstrip() + "\n"
            m = _YAML.search(sec)
            if not m:
                self._unk(f"backlog.md:{a + 1}", "没有 yaml 块", lines[a])
                continue
            y = _yaml(m.group(1))
            y.setdefault("source_id", h.group(1))
            y.setdefault("entry_no", h.group(2))
            slug = f"{y['source_id']}-{y['entry_no']}"
            n = len(self.entries)
            self._entry(y, h.group(3) or "", f"backlog/{slug}.md", f"backlog.md:{a + 1}")
            if len(self.entries) > n:
                self.sections[slug] = sec

    # ---- 写入 ----

    def _check_link(self, rel: str) -> str:
        p = self.p.root
        for part in rel.split("/"):
            p = os.path.join(p, part)
            if os.path.islink(p):
                raise KeelError(f"拒绝写入 {rel}：它或上级目录是符号链接", 3)
        return p

    def _write(self, rel: str, text: str) -> None:
        """改文档（非状态）：逐级拒绝符号链接，临时文件 + os.replace。"""
        p = self._check_link(rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        store._replace_file(p, text.encode("utf-8"))

    def _read(self, rel: str) -> str:
        try:
            with open(os.path.join(self.p.root, rel), encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def apply(self) -> None:
        """调用方须已持有 project.lock()。先算出全部目标并检查符号链接，再开始写，避免写一半。"""
        store.cleanup_tmp(self.p)
        store.require_intact(self.p)
        for rel in (store.BACKLOG_MD, store.TASKS_MD):
            store.check_generated_links(self.p, rel)
        state = {f"{tasks.TASKS_REL}/{tid}.json": dump(d) for tid, d in self.tasks.items()}
        state.update({backlog._rel(anchor): dump(e) for anchor, e in self.entries.items()})
        docs = self._docs()
        for rel in [*state, *docs]:
            self._check_link(rel)
        store.init_state(self.p)
        for rel, data in state.items():
            store.write_atomic(self.p, rel, data)
        for rel, text in docs.items():
            self._write(rel, text)
        render.render_all(self.p)

    def _docs(self) -> dict[str, str]:
        """要改写的文档：相对路径 -> 新内容；只读不写。"""
        docs: dict[str, str] = {}
        dd = "docs/devdocs/"
        for slug, sec in self.sections.items():
            if not os.path.exists(os.path.join(self.p.devdocs, "backlog", slug + ".md")):
                docs[f"{dd}backlog/{slug}.md"] = sec
        done = set(self.tasks) | self.have_t
        for tid in (x for x in self.raw if x in done):  # 已在 state 的任务：被删的汇总行里的备注也要搬
            rec = f"{dd}audit/{tid}/ledger-record.md"
            cur = old = self._read(rec)
            for rel in dict.fromkeys(r for r, _l, _t in self.raw[tid].moved):
                add = [(lb, tx) for r, lb, tx in self.raw[tid].moved if r == rel and tx not in cur]
                if add:
                    cur += ("\n" if cur and not cur.endswith("\n") else "") + ("\n" if cur else "")
                    cur += f"## 迁移自 {rel}（{self.today}）\n\n" + "".join(f"- **{lb}**：{tx}\n" for lb, tx in add)
            if cur != old:
                docs[rec] = cur
        arch = old_arch = self._read(ARCHIVE)
        for a, b, rows in self.tables:  # 被删的汇总表整表原样存档
            block = "\n".join(self.texts[MAIN].split("\n")[a:b])
            if any(tid in done for _k, tid in rows) and block not in arch:
                arch += ("" if not arch or arch.endswith("\n") else "\n") + ("\n" if arch else "")
                arch += f"## 迁移自 {MAIN}:{a + 1}（{self.today}）\n\n{block}\n"
        if arch != old_arch:
            docs[ARCHIVE] = arch
        for rel, text in self.texts.items():
            lines = text.split("\n")
            drop = {k for r, k, tid in self.prop_rows if r == rel and tid in done}
            insert: dict[int, list[str]] = {}
            if rel == MAIN:
                for n, (a, b, rows) in enumerate(self.tables):
                    if n == 0 and BEGIN not in text:
                        insert[a] = [BEGIN, END, ""]
                    keep = [k for k, tid in rows if tid not in done]
                    drop |= {k for k, _t in rows if k not in keep} if keep else set(range(a, b))
                if not self.tables and BEGIN not in text:
                    lines[-1:] = [lines[-1], BEGIN, END, ""] if lines[-1] else [BEGIN, END, ""]
            out = [x for k, line in enumerate(lines) for x in insert.get(k, []) + ([] if k in drop else [line])]
            if (edited := _bump("\n".join(out))) != text:
                docs[dd + rel] = edited
        if self.bl_save:  # 原文另存（spec_version 同样升到 v3，免得被当成未迁移文档）
            old_bl, saved = _bump(self._read(store.BACKLOG_MD)), self._read(self.bl_save)
            if old_bl not in saved:
                docs[self.bl_save] = saved + ("\n" if saved and not saved.endswith("\n") else "") + old_bl
        for base, dirs, files in os.walk(self.p.devdocs):  # 其余文档的 spec_version 一并升到 v3
            dirs[:] = [x for x in dirs if x != "state"]
            for f in files:
                if f.endswith(".md") and not (base == self.p.devdocs and f in self.texts):
                    rel = os.path.relpath(os.path.join(base, f), self.p.root)
                    text = docs[rel] if rel in docs else self._read(rel)
                    if (edited := _bump(text)) != text:
                        docs[rel] = edited
        return docs

    def report(self, mode: str) -> str:
        def sec(name: str, items: list[str]) -> list[str]:
            return [f"## {name}", "", *(items or ["（无）"]), ""]
        moved = [f"- {tid} → audit/{tid}/ledger-record.md：" + "、".join(dict.fromkeys(lb for _r, lb, _t in t.moved))
                 for tid, t in self.raw.items() if (tid in self.tasks or tid in self.have_t) and t.moved]
        return "\n".join([f"# keel 迁移报告（{mode}，{self.today}）", "",
                          *sec("已迁移", [f"- 任务：{len(self.tasks)}", f"- backlog：{len(self.entries)}"]),
                          *sec("未识别", [f"- {u}" for u in self.unknown]),
                          *sec("待映射状态", [f"- `{v}` → {n}" for v, n in self.pending.most_common()]),
                          *sec("状态冲突", [f"- {c}" for c in self.conflicts]),
                          *sec("review_pending 补字段", self.rp_filled),
                          *sec("搬出的长文本", moved + self.bl_note),
                          "## 回滚", "", f"迁移前 docs/devdocs 已提交；撤销本次迁移：`{ROLLBACK}`" if self.in_git else
                          "项目不在 git 仓库中，迁移没有回滚手段；被整份重写的 backlog.md 原文见上「搬出的长文本」"])


def run(project: Project, apply: bool, maps: list[str], allow_partial: bool) -> int:
    if apply and store._git(project.root, "rev-parse", "--git-dir") is not None \
            and store._git(project.root, "status", "--porcelain", "--", "docs/devdocs"):
        raise KeelError("docs/devdocs 有未提交改动，先提交或暂存再迁移", 1)
    with project.lock():
        m = Migration(project, maps)
        refuse = apply and bool(m.unknown or m.pending) and not allow_partial
        if apply and not refuse:
            m.apply()
        store.write_atomic(project, REPORT, m.report("apply" if apply else "dry-run").encode("utf-8"), record=False)
    summary = f"任务 {len(m.tasks)}、backlog {len(m.entries)}，未识别 {len(m.unknown)}，待映射状态 {len(m.pending)}"
    if refuse:
        raise KeelError(f"未执行：{summary}；见 {REPORT}，补 --map-status 或确认后加 --allow-partial", 1)
    print(("已迁移" if apply else "预演（未写入）") + f"：{summary}；报告 {REPORT}")
    return 0
