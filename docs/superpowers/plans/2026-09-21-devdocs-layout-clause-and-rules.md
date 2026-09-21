# devdocs 布局清单 + 三条检测规则 实施计划（P3）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 keel 一份 devdocs 布局清单作单一真源，并在 health-lint 上加三条非阻断检测，让「一次文档健康检查」能看见命名、登记与体积问题。

**Architecture:** 清单是 `skills/shared/devdocs-layout.md` 里的一张三列 markdown 表（路径模式 / owner / 主文件）。`health-lint.py` 运行时解析该表，⛔ 不在脚本里重抄一份路径模式——否则又是两处真源，正是本次要治的病。三条规则挂现役 health 维度，⛔ 不新建 scope。

**Tech Stack:** Python 3 标准库（`re` / `os` / `argparse`），无第三方依赖。测试是脚本自带的 `--selftest` 夹具，⛔ 不引入 pytest。

**Spec:** `docs/superpowers/specs/2026-09-20-devdocs-layout-governance-design.md`（v4，commit `62c6c37`）

## 对 spec 的两处偏离（已判断，执行者照本计划做）

1. **⛔ 不改 `collect_files()`。** spec §P3 写「`collect_files()` 需扩文件类型」。但该函数的返回值同时喂**编号定义索引**（`scan_project` Phase A），塞进 `.yaml`/`.txt` 会改变 `health/dead-link` 的现有行为——正是 P0（`35a4da8`）刚修完的那类风险。改为**新增独立收集器 `collect_all()`**，只供 layout 规则使用。spec §P3 里「不整目录排除 `archive/`」的死链顾虑随之消失，因为 `collect_files()` 一字未动。
2. **清单由脚本解析，⛔ 不硬编码。** spec 未规定清单如何被脚本消费。本计划定为运行时解析 markdown 表，单一真源。

## Global Constraints

- SKILL.md ≤ 500 行（AGENTS.md 硬约束，`skill/size-cap` 会拦）
- 三条新规则**严重度一律 `warning`**，⛔ 无 blocker（spec §P3：裁定 3 未授权自动拆分，设 blocker 即造无解之门）
- `layout/unknown-path` 的措辞是「**待分类**」，⛔ 不是「非法」（spec §P3）
- 尺寸阈值 **96 KiB = 98304 bytes**（spec §P3）
- 清单中**主文件列允许为空**，只有生产方明确声明过分册的才填（spec §P3）
- 每批改动必须 bump `plugin.json` 与 `.claude-plugin/plugin.json` 的 version，⛔ 不 bump 则分发空转且零报错
- 中文提交信息，Conventional Commits：`feat/fix/refactor/docs(scope): description`
- 提交信息结尾加：`Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`

---

## File Structure

| 文件 | 责任 | 动作 |
|---|---|---|
| `skills/shared/devdocs-layout.md` | 布局清单单一真源：三列表 + 双形态说明 + 三类阈值分工 | 创建 |
| `skills/pipeline/scripts/health-lint.py` | 清单解析器 `load_layout()` + 收集器 `collect_all()` + 三条规则 `scan_layout()` + 夹具 | 修改 |
| `skills/pipeline/references/health-lint-implementation.md` | Rule 集表登记三条新规则 + 算法说明 | 修改 |
| `skills/pipeline/references/realign-scope-health.md` | 三大维度表接入新规则；`AskUserQuestion` 加一行；apply 加改名 Phase；补「apply 后必须全量重扫」 | 修改 |
| `skills/onboard/SKILL.md` §8 | 4 行硬编码表 → 从清单 + 实际文件生成 | 修改 |
| `docs/architecture.md` 文件结构块 | 改为指向清单的一行 | 修改 |

---

## Task 1: 布局清单 + 解析器

**Files:**
- Create: `skills/shared/devdocs-layout.md`
- Modify: `skills/pipeline/scripts/health-lint.py`（新增 `LAYOUT_DOC` / `pat_to_re()` / `load_layout()`；在 `selftest()` 中加断言）

**Interfaces:**
- Produces: `load_layout(path=None) -> list[tuple[re.Pattern, str, str|None]]`，元素为 `(编译后的路径正则, owner, 主文件相对路径或 None)`，按清单表出现顺序。清单缺失或零可解析行时 **raise RuntimeError**。
- Produces: `pat_to_re(pattern: str) -> str`，把清单的路径模式语法转成正则源串。
- Consumes: 无。

**路径模式语法**（清单与解析器必须一致，⛔ 不得各写各的）：

| 记法 | 含义 | 正则 |
|---|---|---|
| `{a,b,c}` | 择一 | `(?:a|b|c)` |
| `<N>` | 一个或多个数字 | `\d+` |
| `<slug>` | 标识符片段 | `[A-Za-z0-9_-]+` |
| `**/` | 任意层级目录（含零层）| `(?:[^/]+/)*` |
| 其他字符 | 字面量 | `re.escape` |

- [ ] **Step 1: 写失败的断言**

在 `health-lint.py` 的 `selftest()` 里，紧接 `# --- skills scope 夹具 ---` 之前插入：

```python
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
```

- [ ] **Step 2: 跑，确认失败**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: FAIL，报 `NameError: name 'load_layout' is not defined`

- [ ] **Step 3: 实现解析器**

在 `health-lint.py` 的 `KEY_RE = ...` 那一行之后插入：

```python
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
    """解析布局清单的三列表，返回 [(编译正则, owner, 主文件|None), ...]。

    ⛔ 清单缺失或零可解析行一律抛 RuntimeError —— 静默返回空表会让
    layout/unknown-path 把项目里每个文件都判成「待分类」，是最糟的失效形态。
    """
    p = path or LAYOUT_DOC
    try:
        text = open(p, encoding="utf-8").read()
    except OSError as e:
        raise RuntimeError(f"布局清单读不到：{p}：{e}")
    rows = []
    for ln in text.split("\n"):
        m = _ROW_RE.match(ln)
        if not m:
            continue
        pat, owner, parent = m.group(1), m.group(2).strip(), m.group(3)
        rows.append((re.compile(pat_to_re(pat)), owner,
                     None if parent == "—" else parent.strip("`")))
    if not rows:
        raise RuntimeError(f"布局清单无可解析行：{p}")
    return rows
```

- [ ] **Step 4: 跑，确认通过**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: `selftest OK —— 9 条 rule 全部命中预期`

- [ ] **Step 5: 写清单文件**

创建 `skills/shared/devdocs-layout.md`，内容如下（表格行必须严格是 `| \`模式\` | owner | \`主文件\` 或 — |`，解析器按此正则匹配）：

````markdown
# devdocs 布局清单

> **本文件是 `docs/devdocs/` 里「允许存在什么」的单一真源。**
> 消费方：`health-lint.py`（运行时解析本表）· 各产出 skill（落盘路径权威）· `onboard` §8（生成文档索引）。
>
> ⛔ **任何 skill 新增一种 devdocs 产出，必须先在本表登记。** 历史教训：`verify-report.md` /
> `.health-report.md` / `schema-drift-report.md` 等都是各 skill 自己长出来的，从没人汇总，
> 于是 `docs/architecture.md` 的文件结构块只列 10 项而实际有 ≥18 种。

## 路径模式语法

| 记法 | 含义 |
|---|---|
| `{a,b,c}` | 择一 |
| `<N>` | 一个或多个数字 |
| `<slug>` | 标识符片段（字母/数字/下划线/连字符）|
| `**/` | 任意层级目录（含零层）|
| 其他 | 字面量 |

主文件列填 `—` 表示**无主从关系**。⛔ 只有生产方明确声明过分册的才填主文件；
⛔ 不得靠文件名连字符反推（`05-refactor-audit.md` 反推会去找不存在的 `05-refactor.md`）。

## 清单

| 相对路径模式 | owner | 主文件 |
|---|---|---|
| `00-baseline.md` | retrofit | — |
| `00-retrofit-report.md` | retrofit | — |
| `00-context.md` | onboard | — |
| `00-progress-report.md` | sync | — |
| `00-feature-log.md` | feature | — |
| `01-requirements.md` | requirements | — |
| `01-requirements-{stories,nfr}.md` | requirements | `01-requirements.md` |
| `02-system-design.md` | system-design | — |
| `02-system-design-{api,data}.md` | system-design | `02-system-design.md` |
| `03-test-cases.md` | test-cases | — |
| `03-test-{unit,integration,e2e}.md` | test-cases | `03-test-cases.md` |
| `04-dev-tasks.md` | dev-tasks | — |
| `04-dev-tasks-{infra,core,api,test,ui}.md` | dev-tasks | `04-dev-tasks.md` |
| `04-dev-tasks-p<N>.md` | dev-tasks | `04-dev-tasks.md` |
| `05-bugfix-log.md` | bugfix | — |
| `05-insights.md` | insights | — |
| `05-test-report.md` | test-run | — |
| `05-refactor-{audit,plan,report,rewrite}.md` | refactor | — |
| `backlog.md` | backlog | — |
| `verify-report.md` | verify | — |
| `readiness-report.md` | verify | — |
| `schema-drift-report.md` | verify | — |
| `patterns/<slug>.md` | compound | — |
| `adr/ADR-<N>.md` | system-design | — |
| `adr/index.md` | system-design | — |
| `insights/INS-<N>.md` | insights | — |
| `insights/index.md` | insights | — |
| `bugs/**/BUG-<N>.md` | bugfix | — |
| `bugs/**/index.md` | bugfix | — |
| `backlog/<slug>.md` | backlog | — |
| `backlog/index.md` | backlog | — |
| `requirements/F-<N>.md` | requirements | — |
| `requirements/index.md` | requirements | — |
| `archive/index.md` | sync | — |
| `archive/{01-requirements,02-system-design,03-test-cases,04-dev-tasks}-archive.md` | sync | — |
| `archive/releases/**/<slug>.md` | sync | — |
| `audit/<slug>-external-review.yaml` | dev-workflow | — |
| `audit/**/<slug>.txt` | dev-workflow | — |
| `.health-report.md` | pipeline | — |
| `.realign-plan.md` | pipeline | — |
| `.batch-checkpoint.json` | dev-workflow | — |
| `.runlog.yaml` | 编排层 | — |

## 双形态存储：集中文件 vs 资源目录

ADR / INS / BUG / Backlog 四类资源**两套形态都合法**，上表各登记两行。

| 资源 | 集中形态 | 资源目录形态 |
|---|---|---|
| ADR | 设计文档的 ADR 节 | `adr/ADR-<N>.md` + `adr/index.md` |
| INS | `05-insights.md` | `insights/INS-<N>.md` + 索引 |
| BUG | `05-bugfix-log.md` | `bugs/BUG-<N>.md` + 索引 |
| Backlog | `backlog.md` | `backlog/<slug>.md` + 索引 |

**判据是规模，不是对错。** 实测：`mic-en`（360 md）有 `bugs/` 122 文件、`insights/` 33、
`adr/` 30，集中文件全缩成 1~2 KB 指针并自留说明「本文件已采用一文件一资源结构」；
`tm-reborn`（22 md）的 `05-bugfix-log.md` 才 2.3 KB，完全够用。

集中文件超 `layout/size-cap` 阈值 → 报「建议转资源目录」。
⛔ **转换不自动执行**——它是内容迁移，需用户触发。

## 三类阈值的分工（⛔ 不是同一件事）

| 阈值 | 归属 | 作用 |
|---|---|---|
| 各 skill 的 300 行拆分规则 | requirements / system-design / test-cases / dev-tasks | 生成时的**拆分建议** |
| `sync --archive` 的 400/500/400/300 行 + 数量 + 状态 | `sync/references/archive.md` | **归档触发器**（需语义条件同时满足）|
| `layout/size-cap` 的 96 KiB | 本文件 | **体积警报**（纯尺寸，无语义条件）|
````

- [ ] **Step 6: 用真清单跑一次解析**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0,'skills/pipeline/scripts')
import importlib.util
spec=importlib.util.spec_from_file_location('hl','skills/pipeline/scripts/health-lint.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows=m.load_layout(); print(f'{len(rows)} rows')
for pat,owner,parent in rows[:3]: print(' ', pat.pattern, owner, parent)
"
```
Expected: `42 rows`，且前三行模式可读。若行数明显偏小，说明表格格式与 `_ROW_RE` 不符，回 Step 5 对齐。

- [ ] **Step 7: 提交**

```bash
cd /Users/mason/Projects/skills/keel-workflow
sed -i '' 's/"version": "2.0.7"/"version": "2.0.8"/' plugin.json .claude-plugin/plugin.json
git add skills/shared/devdocs-layout.md skills/pipeline/scripts/health-lint.py plugin.json .claude-plugin/plugin.json
git commit -F- <<'EOF'
feat(layout): 布局清单 SSOT + 运行时解析器

devdocs 里「允许存在什么」此前散在 ≥18 处 skill 正文，architecture.md 的文件结构块
只列 10 项已过期，onboard §8 是 4 行硬编码表——三份互不一致。本表收口为单一真源。

解析器在脚本运行时读表，⛔ 不在脚本里重抄路径模式，否则又是两处真源。
清单缺失或零可解析行抛 RuntimeError —— 静默空表会让 unknown-path 把每个文件
都判成待分类，是最糟的失效形态，故钉死在 selftest 里。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 2: `layout/unknown-path` —— 未登记路径报「待分类」

**Files:**
- Modify: `skills/pipeline/scripts/health-lint.py`（新增 `collect_all()` / `scan_layout()`；`main()` 接线；`selftest()` 加夹具与期望）

**Interfaces:**
- Consumes: `load_layout()`（Task 1）
- Produces: `collect_all(devdocs) -> list[str]`，devdocs 下**全部文件**的绝对路径（含 `.yaml` / `.txt` / 无扩展名），⛔ 不过滤扩展名。
- Produces: `scan_layout(root, devdocs, layout_rows) -> list[dict]`，返回 finding 列表。

⛔ **不改 `collect_files()`。** 它的返回值喂编号定义索引，塞非 `.md` 会改变 `health/dead-link`
的现有行为——P0（`35a4da8`）刚修完这类风险。layout 规则用独立的 `collect_all()`。

- [ ] **Step 1: 写失败的夹具**

在 `selftest()` 的 project scope 夹具区，紧接 `open(os.path.join(dd, "_archived", "old.md"), ...)` 那行之后插入：

```python
        # --- layout 夹具 ---
        os.makedirs(os.path.join(dd, "audit"))
        open(os.path.join(dd, "audit", "T-01-external-review.yaml"), "w").write("k: v\n")
        open(os.path.join(dd, "99-mystery.md"), "w").write("# 不在清单里\n")
```

并在 `want` 字典中加一行：

```python
            "layout/unknown-path": 1,     # 99-mystery.md 不在清单；audit/*.yaml 在清单
```

并把计数循环改为（原行为 `for f in scan_project(t) + scan_skill_flags(sk) + scan_skill_repo(sk):`）：

```python
        lay_rows = load_layout(lay)
        for f in (scan_project(t) + scan_layout(t, dd, lay_rows)
                  + scan_skill_flags(sk) + scan_skill_repo(sk)):
```

⚠️ Task 1 的夹具清单只有 5 行，`99-mystery.md` 与 `01.md` 都不匹配它。为让本用例只命中
一条，把 Task 1 夹具清单的第一行 `01-requirements.md` 改成 `01.md`，并把 Task 1 的
断言 `cases` 首项同步改为 `("01.md", 0)`。

- [ ] **Step 2: 跑，确认失败**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: FAIL，报 `NameError: name 'scan_layout' is not defined`

- [ ] **Step 3: 实现收集器与规则**

在 `collect_files()` 定义之后插入：

```python
def collect_all(devdocs):
    """layout 规则的扫描面：devdocs 下**全部文件**，⛔ 不过滤扩展名。

    ⛔ 与 collect_files() 分开：后者喂编号定义索引，塞进 .yaml/.txt 会改变
    health/dead-link 行为（见 commit 35a4da8 修的那类误报）。
    """
    out = []
    for root, dirs, files in os.walk(devdocs):
        for f in sorted(files):
            out.append(os.path.join(root, f))
    return sorted(out)
```

在 `scan_project()` 定义之前插入：

```python
SIZE_CAP_BYTES = 98304          # 96 KiB，spec §P3


def scan_layout(root, devdocs, layout_rows):
    """layout/* 三条规则。全部 warning，⛔ 无 blocker。"""
    findings = []
    for path in collect_all(devdocs):
        rel_dd = os.path.relpath(path, devdocs)
        rel = os.path.relpath(path, root)
        if not any(pat.fullmatch(rel_dd) for pat, _, _ in layout_rows):
            findings.append(find(
                "layout/unknown-path", "warning", rel, None,
                f"{rel_dd} 不在布局清单中 —— 待分类，⛔ 非「非法」",
                fix="在 skills/shared/devdocs-layout.md 登记该路径模式；"
                    "若属临时产物则移出 docs/devdocs/"))
    return findings
```

在 `main()` 里，把 `findings = scan_project(root, files, ref_only)` 改为：

```python
    findings = scan_project(root, files, ref_only)
    try:
        findings += scan_layout(root, devdocs, load_layout())
    except RuntimeError as e:
        print(f"layout/clause-unavailable: {e}", file=sys.stderr)
        return 3
```

- [ ] **Step 4: 跑，确认通过**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: `selftest OK`

- [ ] **Step 5: 在真实项目上验证，并对照组不变**

Run:
```bash
cd /Users/mason/Projects/mic/tm-reborn && python3 /Users/mason/Projects/skills/keel-workflow/skills/pipeline/scripts/health-lint.py --target . 2>/dev/null | grep -c "layout/unknown-path"
```
Expected: `2` —— 即 `06-ui-hig-swiftui-checklist.md` 与 `T-31-a11y-interactive-checklist.md`（spec §P3 的实测预测）。

若数字大于 2，说明清单漏登记了 tm-reborn 的合法产物：逐个看报出来的文件名，属合法产物的补进清单，⛔ 不要放宽规则。

Run（回归，确认 P0 的结论没被破坏）：
```bash
cd /Users/mason/Projects/mic/tm-reborn && python3 /Users/mason/Projects/skills/keel-workflow/skills/pipeline/scripts/health-lint.py --target . 2>/dev/null | grep -c "severity: blocker"
```
Expected: `9`（与 `35a4da8` 后一致，新规则不得改变 blocker 数）

- [ ] **Step 6: 提交**

```bash
cd /Users/mason/Projects/skills/keel-workflow
sed -i '' 's/"version": "2.0.8"/"version": "2.0.9"/' plugin.json .claude-plugin/plugin.json
git add -A
git commit -F- <<'EOF'
feat(health-lint): layout/unknown-path —— 未登记路径报「待分类」

措辞是「待分类」不是「非法」：新产物先于清单出现是正常时序，判非法会误伤。

新增独立收集器 collect_all()，⛔ 不动 collect_files()——后者喂编号定义索引，
塞进 .yaml/.txt 会改变 health/dead-link 行为（35a4da8 刚修完这类误报）。

实测 tm-reborn 命中 2 条（06-ui-hig-swiftui-checklist.md 自造段号、
T-31-a11y-interactive-checklist.md 不属任何载体），blocker 仍为 9，未受影响。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 3: `layout/unregistered-split` —— 分册未在主文件登记

**Files:**
- Modify: `skills/pipeline/scripts/health-lint.py`（扩 `scan_layout()`；`selftest()` 加夹具与期望）

**Interfaces:**
- Consumes: `load_layout()` 的第三列（主文件）、`collect_all()`
- Produces: 无新函数，扩 `scan_layout()`。

⚠️ **「分册名必须出现在主文件正文」是新增规则**，⛔ 不是既有约束。它只保证**可发现性下限**：
历史说明里写「已弃用 `02-system-design-api.md`」也会通过；链接文字对而目标错也会通过。
⛔ 不得把它宣传成索引完整性保证。

- [ ] **Step 1: 写失败的夹具**

在 Task 2 的 layout 夹具之后追加：

```python
        open(os.path.join(dd, "04-dev-tasks.md"), "w").write(
            "# 任务\n分册：[04-dev-tasks-p1.md](04-dev-tasks-p1.md)\n")
        open(os.path.join(dd, "04-dev-tasks-p1.md"), "w").write("# P1\n")   # 已登记 → 不报
        open(os.path.join(dd, "04-dev-tasks-p2.md"), "w").write("# P2\n")   # 未登记 → 报
```

`want` 中加：

```python
            "layout/unregistered-split": 1,   # p2 未在主文件出现；p1 已出现
```

并把 Task 1 夹具清单里 `04-dev-tasks-p<N>.md` 那行的主文件保持为 `` `04-dev-tasks.md` ``（Task 1 已写成这样，无需改）。

⚠️ 新增的 `04-dev-tasks.md` / `-p1` / `-p2` 三个文件都不匹配 Task 1 的 5 行夹具清单，
会让 `layout/unknown-path` 从 1 涨到 4。把 `want` 里的 `layout/unknown-path` 同步改为 `4`，
并在该行注释写明构成，⛔ 不要为了凑数去改规则。

- [ ] **Step 2: 跑，确认失败**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: FAIL，`layout/unregistered-split: 期望 1 条，实得 0`

- [ ] **Step 3: 实现**

在 `scan_layout()` 的 `for path in collect_all(devdocs):` 循环体末尾（`unknown-path` 判断之后）追加：

```python
        for pat, _owner, parent in layout_rows:
            if parent is None or not pat.fullmatch(rel_dd):
                continue
            ppath = os.path.join(devdocs, parent)
            if not os.path.isfile(ppath):
                break                       # 主文件不存在是另一类问题，⛔ 不在本规则报
            try:
                ptext = open(ppath, encoding="utf-8", errors="replace").read()
            except OSError:
                break
            if os.path.basename(rel_dd) not in ptext:
                findings.append(find(
                    "layout/unregistered-split", "warning", rel, None,
                    f"分册 {os.path.basename(rel_dd)} 未在主文件 {parent} 正文出现",
                    ctx=f"parent: {parent}",
                    fix=f"在 {parent} 的分册目录里加一行指向本文件；"
                        "⛔ 本规则只保证可发现性下限，不校验链接目标"))
            break
```

- [ ] **Step 4: 跑，确认通过**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: `selftest OK`

- [ ] **Step 5: 真实项目验证**

Run:
```bash
cd /Users/mason/Projects/mic/tm-reborn && python3 /Users/mason/Projects/skills/keel-workflow/skills/pipeline/scripts/health-lint.py --target . 2>/dev/null | grep -A2 "layout/unregistered-split" | head -20
```
Expected: 命中 `02-system-design-api.md` 与 `02-system-design-data.md` 两条——spec §2 实测过
`02-system-design.md` 有两个分册但主文件零登记。`03-test-*` 与 `04-dev-tasks-*` ⛔ 不得命中
（它们在主文件有目录，见 `03-test-cases.md:47` 与 `04-dev-tasks.md:16`）。

- [ ] **Step 6: 提交**

```bash
cd /Users/mason/Projects/skills/keel-workflow
sed -i '' 's/"version": "2.0.9"/"version": "2.0.10"/' plugin.json .claude-plugin/plugin.json
git add -A
git commit -F- <<'EOF'
feat(health-lint): layout/unregistered-split —— 分册未在主文件登记

只对清单第三列明确声明过主文件的分册生效，⛔ 不靠连字符反推主从：
03-test-unit.md 的主文件是 03-test-cases.md（词干就不同），
05-refactor-{audit,plan,report} 是四个独立产物反推会去找不存在的 05-refactor.md。

⚠️ 「分册名出现在主文件正文」是新增规则，不是既有约束，且只做字面检查——
历史说明里写「已弃用 X.md」也会通过。只保证可发现性下限，⛔ 不是索引完整性。

实测 tm-reborn 命中 02-system-design-{api,data}.md（主文件零登记），
03-test-* 与 04-dev-tasks-* 不命中（主文件已有分册目录）。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 4: `layout/size-cap` —— 体积警报 + 按类型分流

**Files:**
- Modify: `skills/pipeline/scripts/health-lint.py`（扩 `scan_layout()`；`selftest()` 加夹具与期望）

**Interfaces:**
- Consumes: `collect_all()`、`SIZE_CAP_BYTES`（Task 2 已定义 = 98304）
- Produces: 无新函数。

⚠️ **96 KiB 是新判据，⛔ 不是修 bug。** `realign-scope-health.md:294` 的「1500 行」是无实现的
散文承诺，清理它属修复；换成字节阈值属新功能。两者分开记账（Task 5 处理前者）。

**分流**：四类双形态资源的集中文件 → 建议转资源目录；其余 → 建议归档或拆分。

- [ ] **Step 1: 写失败的夹具**

在 Task 3 的夹具之后追加：

```python
        open(os.path.join(dd, "05-bugfix-log.md"), "w").write("B\n" * 60000)   # ~120 KB，四类之一
        open(os.path.join(dd, "02-system-design.md"), "w").write("D\n" * 60000)  # ~120 KB，其余
```

`want` 中加：

```python
            "layout/size-cap": 2,         # 05-bugfix-log(建议转资源目录) + 02(建议归档/拆分)
```

并把 `layout/unknown-path` 的期望从 `4` 改为 `6`（两个新文件同样不在 5 行夹具清单里）。

- [ ] **Step 2: 跑，确认失败**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: FAIL，`layout/size-cap: 期望 2 条，实得 0`

- [ ] **Step 3: 实现**

在 `SIZE_CAP_BYTES = 98304` 之后加：

```python
# 四类双形态资源的集中文件 → 超阈值建议转资源目录（devdocs-layout.md「双形态存储」）
DUAL_FORM_CENTRAL = {
    "05-bugfix-log.md": "bugs/BUG-<N>.md",
    "05-insights.md": "insights/INS-<N>.md",
    "backlog.md": "backlog/<slug>.md",
    "02-system-design.md": None,        # ADR 的集中形态是它的 ADR 节，⛔ 整文件不等于 ADR
}
```

⚠️ `02-system-design.md` 的值为 `None`：ADR 的集中形态是**该文件的一个节**，整文件超标
不等于 ADR 超标 ⇒ 它走「归档/拆分」分支，⛔ 不建议转 `adr/`。

在 `scan_layout()` 循环体末尾追加：

```python
        if rel_dd.endswith(".md"):
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            if size > SIZE_CAP_BYTES:
                target = DUAL_FORM_CENTRAL.get(rel_dd)
                if target:
                    sug = f"建议转资源目录 {target} + 索引；⛔ 转换是内容迁移，需用户确认后手动执行"
                else:
                    sug = ("历史内容 → /sync --archive；活跃内容 → 该 skill 的拆分规则；"
                           "⛔ 本 scope 不减量")
                findings.append(find(
                    "layout/size-cap", "warning", rel, None,
                    f"{rel_dd} 已 {size} bytes（阈值 {SIZE_CAP_BYTES}）",
                    actual=size, threshold=SIZE_CAP_BYTES, fix=sug))
```

- [ ] **Step 4: 跑，确认通过**

Run: `python3 skills/pipeline/scripts/health-lint.py --selftest`
Expected: `selftest OK`

- [ ] **Step 5: 三样本校准**

Run:
```bash
for p in mic/tm-reborn dji-4g mic/mic-en-legacy; do
  printf "%-22s " "$p"
  (cd /Users/mason/Projects/$p && python3 /Users/mason/Projects/skills/keel-workflow/skills/pipeline/scripts/health-lint.py --target . 2>/dev/null | grep -c "layout/size-cap")
done
```
Expected: `tm-reborn 0`（最大 61 KB，全部通过——它是正面样本）· `dji-4g 0` · `mic-en-legacy ≥4`
（`02`(400KB) `03-test-unit`(215KB) `01`(160KB) `04`(135KB)，spec §P3 校准值）。

若 tm-reborn 非 0，说明阈值定低了：⛔ 不要改阈值迁就，先看命中的是哪个文件、它是不是真的该报。

- [ ] **Step 6: 提交**

```bash
cd /Users/mason/Projects/skills/keel-workflow
sed -i '' 's/"version": "2.0.10"/"version": "2.0.11"/' plugin.json .claude-plugin/plugin.json
git add -A
git commit -F- <<'EOF'
feat(health-lint): layout/size-cap —— 96 KiB 体积警报，按类型分流出口

单位是字节不是行数：tm-reborn 01-requirements.md 620 行 28KB，
mic-en 同名文件 556 行 160KB（宽表格，288 B/行）——行数会测反，
而痛点是上下文预算被吃光，预算按 token 算。

⛔ 无 blocker：裁定 3 未授权自动拆分，02/00-context/backlog 的分册键仍未解，
设 blocker 即造一个用户被卡住却没有解法的门。

分流：四类双形态资源的集中文件 → 建议转资源目录；其余 → 归档或拆分。
02-system-design.md 走后者——ADR 的集中形态是它的一个节，整文件超标不等于 ADR 超标。

校准：tm-reborn 0 命中（最大 61KB，正面样本）· mic-en 命中 4 个已知大文件。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 5: 规格登记与维度接入

**Files:**
- Modify: `skills/pipeline/references/health-lint-implementation.md`（Rule 集表 + 算法节）
- Modify: `skills/pipeline/references/realign-scope-health.md`（三大维度表、扫描范围、`AskUserQuestion`、apply Phase、复查、清「1500 行」）

**Interfaces:**
- Consumes: Task 2~4 的三个 `rule_id` 与其严重度
- Produces: 规格文本，⛔ 无代码接口。

- [ ] **Step 1: Rule 集表登记**

在 `health-lint-implementation.md` 的 Rule 集表（`| \`state/total-size-cap\` |` 所在表）末尾、
`| \`skill/dead-link\` |` 那行之前插入三行：

```markdown
| `layout/unknown-path` | ⚠️ | a 结构正确性 | v1+v2 | ❌（manual_decision）|
| `layout/unregistered-split` | ⚠️ | b 索引/链接 | v1+v2 | ❌（manual_decision）|
| `layout/size-cap` | ⚠️ | c 过大 | v1+v2 | ❌（manual_decision）|
```

并把该表下方「12 条全部 [新增]，可执行」改为「15 条全部 [新增]；其中 `design/adr-only-revision`
与 `submodule/pointer-drift` 脚本输出 `not_implemented`，需 Agent 按算法补执行」。

⚠️ 原文那句「12 条全部可执行」本就不准（脚本实现 10/12）。本步顺带订正，⛔ 不要只加行不改数。

- [ ] **Step 2: 三大维度表接入**

在 `realign-scope-health.md` 的「三大健康维度」表里，三个维度的「检查内容」与「依赖能力」列
各追加对应规则：维度 a 加 `layout/unknown-path`、维度 b 加 `layout/unregistered-split`、
维度 c 加 `layout/size-cap`。

同时把「扫描范围」表加一行：

```markdown
| `docs/devdocs/**`（**全部文件**，含 `.yaml` / `.txt`）| `layout/*` 三条规则专属扫描（`collect_all()`，⛔ 与喂编号索引的 `collect_files()` 分开）|
```

- [ ] **Step 3: 清「1500 行」悬空承诺**

把 `realign-scope-health.md` 「与其他 scope 的边界」节里

```
- 维度 c 中单文件 ≥ 1500 行 → 仅报告，**不拆分**；归档减量走 `/sync --archive`。
```

改为

```
- 维度 c 中单文件 > 96 KiB（`layout/size-cap`）→ 仅报告，**不拆分**；历史内容归档走 `/sync --archive`，活跃内容走各 skill 拆分规则，四类双形态资源的集中文件建议转资源目录。
```

并把同文件 `route_note` 示例里的 `current.md >1500` 一并改为 `>96 KiB`。

⚠️ 原「1500 行」在 Rule 集表中**无对应规则**、脚本无实现——这是清理悬空承诺（修复）；
换成 96 KiB 是 Task 4 的新功能。两件事分开记，⛔ 不要在提交信息里混成一句。

- [ ] **Step 4: `AskUserQuestion` 触发点加一行**

在该表末尾加：

```markdown
| 待分类文件归属 | `layout/unknown-path` 检出 | 展示文件名 + 清单中相近的路径模式候选（≤3 个）+「移出 devdocs」选项；⛔ 判不出归属时不得代为猜测 |
```

- [ ] **Step 5: apply 加改名 Phase 并补复查**

在「修复路径」节，`#### Phase 1：维度 c 自动归档` 之前插入新 Phase 并把后续编号各 +1
（当前是 Phase 1 维度 c / Phase 2 维度 b / Phase 3 维度 a，改后为 Phase 1 布局 / 2 维度 c / 3 维度 b / 4 维度 a）：

```markdown
#### Phase 1：布局改名与归档移位（`layout/*`）

- 仅两种动作，均为 `git mv`：**改名**（清单中有明确旧名→新名映射时）、**归档移位**（把 `*-archive.md` 移进 `archive/`）。
- ⛔ **改名必须同批更新所有指向它的引用**。实证：tm-reborn 的 `06-ui-hig-swiftui-checklist.md` 在 `04-dev-tasks.md:19` 被链接，只 `git mv` 即制造死链。
- ⛔ **仅移动无法闭合的项单列**：补登记（`unregistered-split`）要编辑正文、集中→资源目录转换是内容迁移——两者均超出「只改名 + 归档移位」授权，列清单逐项问用户。
- ⛔ `layout/unknown-path` **不自动动手**，一律走 `AskUserQuestion`。
```

并在「Apply 失败处理」节之前插入：

```markdown
#### 复查（⛔ 必须执行）

apply 全部 Phase 完成后**重新全量 dry-run**，比对 `total_score` 与各 rule 计数。

⛔ 不接受「post-apply 估算总分」——实证：mic-en 的 `47252f3` 报告写的就是估算值，
而当次 apply 后 state 又涨回 58 KB，估算掩盖了未收敛的事实。
```

⚠️ `health-lint-implementation.md:147` 引用了「Phase 1 维度 c 自动归档」并带锚点链接。
Phase 重编号后该引用会失效，**本步必须同步改为 Phase 2 并更新锚点**。

- [ ] **Step 6: 验证规格自洽**

Run:
```bash
cd /Users/mason/Projects/skills/keel-workflow
python3 skills/pipeline/scripts/health-lint.py --skills-dir skills
grep -rn "1500" skills/pipeline/references/ || echo "1500 残留归零"
grep -rn "Phase 1" skills/pipeline/references/health-lint-implementation.md
```
Expected: `blocker=0 warning=0`；`1500` 归零；`health-lint-implementation.md` 的 Phase 引用
已指向 Phase 2 且锚点与新标题一致。

- [ ] **Step 7: 提交**

```bash
cd /Users/mason/Projects/skills/keel-workflow
sed -i '' 's/"version": "2.0.11"/"version": "2.0.12"/' plugin.json .claude-plugin/plugin.json
git add -A
git commit -F- <<'EOF'
docs(health-scope): 登记三条 layout 规则，apply 加布局 Phase 并补强制复查

Rule 集表补三行并订正「12 条全部可执行」——脚本实际实现 10/12，
design/adr-only-revision 与 submodule/pointer-drift 输出 not_implemented。

apply 新增 Phase 1 布局改名与归档移位并把后续 Phase 顺延；
health-lint-implementation.md:147 的 Phase 引用与锚点同步更新。

补「apply 后必须全量重扫」：⛔ 不接受估算总分——mic-en 的 47252f3 报告
写的就是估算值，而当次 apply 后 state 又涨回 58 KB，估算掩盖了未收敛。

清掉「1500 行」悬空承诺（Rule 集表无对应规则、脚本无实现），
改指向 layout/size-cap。⚠️ 清承诺是修复，96 KiB 判据是 Task 4 的新功能，两件事。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 6: `onboard` §8 从清单生成 + `architecture.md` 改指针

**Files:**
- Modify: `skills/onboard/SKILL.md`（§8「keel 文档索引」）
- Modify: `docs/architecture.md`（「文件结构」块）

**Interfaces:**
- Consumes: `skills/shared/devdocs-layout.md`
- Produces: 无代码接口。

⚠️ **插件内的路径类型清单 ≠ 项目当前文件索引。** 清单说「允许存在什么」，
onboard §8 说「这个项目现在有什么」。⛔ 两者不可互替，本任务是让后者**依据**前者生成。

- [ ] **Step 1: 改 onboard §8**

把 `skills/onboard/SKILL.md` §8 那张 4 行硬编码表（需求/系统设计/测试用例/开发任务）
替换为生成指令：

```markdown
## 8. keel 文档索引

> 按 [shared/devdocs-layout.md](../shared/devdocs-layout.md) 的清单**逐项比对项目实际文件**生成，
> ⛔ 不得沿用固定四行——实测 tm-reborn 有 21 个产物、mic-en 含子目录有 360 个。

生成规则：

1. 列出 `docs/devdocs/` 下全部文件（含子目录，含 `.yaml` / `.txt`）
2. 逐个匹配清单的路径模式，取其 owner 作「产出方」列
3. 清单中有主文件的，在「说明」列标注 `<主文件> 的分册`
4. 匹配不到任何模式的，「产出方」列填 `待分类`，⛔ 不得省略不列
5. 清单里有模式但项目中无对应文件的，⛔ 不列（本节是项目现状，不是规范）

| 文档 | 路径 | 产出方 | 说明 |
|------|------|--------|------|
| （按上述规则生成）| | | |
```

- [ ] **Step 2: `architecture.md` 文件结构块改指针**

把 `docs/architecture.md` 「文件结构」节里 `devdocs/` 那段目录树（10 项）替换为：

```markdown
`docs/devdocs/` 的完整产物清单（路径模式 / owner / 主从关系）见
[skills/shared/devdocs-layout.md](../skills/shared/devdocs-layout.md)。

⛔ **本文件不再复述该清单。** 此处曾列 10 项而 skills 实际产出 ≥18 种，
是三份互不一致的清单之一（另两份：`onboard` §8 的 4 行硬编码表、各 skill 散落声明）。
```

⚠️ 保留该节里 `docs/prd/` 与 `codebase-insight.md` 两部分，⛔ 只替换 `devdocs/` 那段。

- [ ] **Step 3: 验证无死链**

Run:
```bash
cd /Users/mason/Projects/skills/keel-workflow
python3 skills/pipeline/scripts/health-lint.py --skills-dir skills
cd docs && [ -e ../skills/shared/devdocs-layout.md ] && echo "architecture 链接可达"
cd ../skills/onboard && [ -e ../shared/devdocs-layout.md ] && echo "onboard 链接可达"
```
Expected: `blocker=0 warning=0`，两条链接均可达。

- [ ] **Step 4: 提交**

```bash
cd /Users/mason/Projects/skills/keel-workflow
sed -i '' 's/"version": "2.0.12"/"version": "2.0.13"/' plugin.json .claude-plugin/plugin.json
git add -A
git commit -F- <<'EOF'
refactor(index): onboard §8 改为按清单生成，architecture 文件结构块改指针

三份互不一致的清单收口为一份：architecture.md 曾列 10 项而实际 ≥18 种，
onboard §8 是 4 行硬编码表（实测 tm-reborn 21 个产物、mic-en 含子目录 360 个）。

⚠️ 插件内的路径类型清单 ≠ 项目当前文件索引：前者说允许存在什么，
后者说这个项目现在有什么。onboard §8 依据清单生成，⛔ 两者不互替。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 7: `/sync --archive` 未验证路径跑通

**Files:**
- 无代码改动。产出是一次真实执行记录。

**Interfaces:**
- Consumes: Task 4 的 `layout/size-cap` 分流建议（「历史内容 → `/sync --archive`」）
- Produces: 验证结论；若跑不通，产出缺陷清单并**停下来报告**，⛔ 不擅自改 sync。

⚠️ **实测事实：17 个项目里 `archive/` 目录数 = 0。** `/sync --archive`、`archive/index.md`、
那套归档行数阈值**从未在任何真实项目上执行过**。Task 4 把它写成减量出口，
⛔ 不得只在规格里声明就算数。

- [ ] **Step 1: 选样本并确认前置**

Run:
```bash
cd /Users/mason/Projects/mic/tm-reborn && git status --porcelain | head && ls docs/devdocs/archive 2>/dev/null || echo "无 archive/（预期）"
```
Expected: 工作区洁净（`sync --archive` 要求）；无 `archive/` 目录。

⛔ 若工作区不洁净，**停下来问用户**，不要 stash 或提交别人的改动。

- [ ] **Step 2: dry-run**

在 tm-reborn 会话中执行 `/sync --archive --dry-run`（若该 skill 不支持 `--dry-run`，
先只读地按 `skills/sync/references/archive.md` 的归档条件人工核算），记录：
哪些文件满足归档条件、拟生成哪些 `archive/*` 文件。

Expected: 产出一份拟归档清单。tm-reborn 任务已完成数较少，**很可能一条都不满足**——
这本身是有效结论，说明该路径在小项目上无触发。

- [ ] **Step 3: 若有可归档项则执行，否则换样本**

若 Step 2 为空，改用 `mic-en-legacy` 重跑 Step 1~2（它有 46 个 >300 行文件、
大量已完成任务，必然有可归档项）。

⚠️ mic-en-legacy 是 legacy 项目，**执行前先 `git branch archive-trial` 建分支**，
⛔ 不要直接在 main 上跑未验证路径。

- [ ] **Step 4: 记录结论**

无论跑通与否，把结果写进 `docs/audits/2026-09-21-sync-archive-first-run.md`：
实际执行的命令、产出的文件、遇到的错误、`archive/index.md` 是否按模板生成。

若跑不通：列出具体失败点（`file:line` 或错误文本），**停下来报告用户**，
⛔ 不擅自修 sync——那是范围外改动。

- [ ] **Step 5: 提交**

```bash
cd /Users/mason/Projects/skills/keel-workflow
git add docs/audits/2026-09-21-sync-archive-first-run.md
git commit -F- <<'EOF'
docs(audits): /sync --archive 首次真实执行记录

该路径此前在 17 个项目里零执行（archive/ 目录数 = 0），
而 layout/size-cap 把它写成历史内容的减量出口——不实测不能算数。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Self-Review

**1. Spec 覆盖**

| spec §P3 要求 | 对应任务 |
|---|---|
| 清单落 `skills/shared/devdocs-layout.md`，三列 | Task 1 |
| 主文件列允许为空，只填明确声明过的 | Task 1 清单 + Task 3 规则 |
| 四类双形态资源各登记两行 | Task 1 清单「双形态存储」节 |
| `layout/unknown-path` 报「待分类」 | Task 2 |
| `layout/unregistered-split` | Task 3 |
| `layout/size-cap` 96 KiB + 三条分流出口 | Task 4 |
| 扫描面扩到非 `.md` | Task 2（`collect_all()`，偏离见开头）|
| ⛔ 不整目录排除 `archive/` | 不适用——`collect_files()` 未改动 |
| 三类阈值分工写清 | Task 1 清单末节 |
| 闭环四步（检查/决策/执行/复查）| Task 5 Step 4/5 |
| 改名须同批改引用；仅移动无法闭合的单列 | Task 5 Step 5 |
| `onboard` §8 改生成 | Task 6 |
| `architecture.md` 改指针 | Task 6 |
| 清「1500 行」悬空承诺 | Task 5 Step 3 |
| `/sync --archive` 须真实跑通 | Task 7 |
| 每批 version bump | 各任务提交步骤 |

⚠️ **spec §P4（`SessionStart` hook）不在本计划内**——它依赖 P3 完成，另起计划。

**2. Placeholder 扫描**：无 TBD / TODO；每个代码步骤都带可直接粘贴的代码块；
每个验证步骤都带具体命令与期望值（含具体数字 `2` / `9` / `0` / `≥4`）。

**3. 类型一致性**：`load_layout()` 返回 `(re.Pattern, str, str|None)` 三元组，
Task 2 用 `for pat, _, _ in layout_rows`、Task 3 用 `for pat, _owner, parent in layout_rows`
——解包元数一致。`SIZE_CAP_BYTES` 在 Task 2 定义、Task 4 使用。
`collect_all()` 在 Task 2 定义、Task 3/4 复用。`find()` 用的是脚本现有签名
`find(rule, sev, file, line, msg, actual=, threshold=, ctx=, fix=)`。

**4. 夹具计数连锁**：Task 2/3/4 各自新增夹具文件都会推高 `layout/unknown-path` 的期望值
（1 → 4 → 6），每个任务的 Step 1 已显式写明要同步改，⛔ 不得靠放宽规则来凑数。
