# keel 门禁机制化 第 1 段 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 任务状态与 backlog 状态改由 `keel` 命令独写并当场校验，K1–K5 五道门经工具自检、客户端 hook、git pre-commit 三层执行，每次命中留记录；存量项目经 `keel migrate` 升级；相关 skill 改走命令、删去被接管的条文。

**Architecture:** `skills/shared/scripts/keel.py` 是唯一入口（argparse 分发），业务逻辑在同目录 `keellib/` 包里按职责分文件。状态存 `docs/devdocs/state/**.json`，人看的台账区与 `backlog.md` 由工具生成。hook 只是薄壳：bash 包装调用 `keel.py hook pre|post`，OpenCode 插件调同一命令。完整性判据用 git blob sha1：工作区内容等于 HEAD 的 blob 或等于本地 manifest 登记的 blob 即合法。

**Tech Stack:** Python 3.9 标准库（`argparse` `json` `hashlib` `fcntl` `subprocess` `unittest`）；bash；Node（仅 `hooks/opencode-plugin.js`）；git。开发期：`uvx ruff`、`uvx mypy`、mise 提供的 Python 3.9。

**Spec:** `docs/superpowers/specs/2026-11-19-keel-mechanized-gates-design.md`

## Global Constraints

- **开发期质量门禁**（用户 2026-11-19 定）：`keellib/` 与 `keel.py` 全部写类型标注，过 `mypy --strict --python-version 3.9`；`keellib/`、`keel.py`、`health-lint.py` 过 `ruff check --target-version py39 --select E4,E7,E9,F,B,UP`；自测在真实 Python 3.9 下跑一遍。ruff、mypy 用 `uvx` 临时拉取，只在本仓开发时用，⛔ 不进运行时依赖。3.9 由 `mise install python@3.9` 提供，⛔ 不放宽 `UV_PYTHON_DOWNLOADS=never`。`health-lint.py` 只过 ruff，不补类型。
- Python 只用标准库，兼容 3.9；不依赖 jq。运行时要求 `python3`（≥3.9）+ `bash`；原生 Windows 第 1 段不支持（`fcntl` 也只在 POSIX 上有），README 写明。
- 阈值只在 `keellib/gates.py` 写一处：`LINE_CAP = 500`（按字符计，`len(str)`）、`SIZE_CAP = 98304`（96 KiB，按字节）。`health-lint.py` 改为导入它们。
- 文本上限：任务 `title` ≤ 80 字；`skip_trace_reason`、`profile_downgrade_reason`、backlog `note`、commit `note` ≤ 200 字。
- 任务状态枚举：`待开发` / `进行中` / `review_pending` / `已完成` / `已归档`。
- 状态载体文件（K3/K4 范围）：`docs/devdocs/04-dev-tasks*.md`（仅 devdocs 根下）、`docs/devdocs/backlog.md`、`docs/devdocs/00-context.md`、`.claude/rules/devdocs-state.md`。`audit/**`、`backlog/<id>.md`、01–03 规格文档不在范围内。
- 档位：`block` / `warn` / `off`；默认全部 `block`；K5 不可调。项目覆盖只经 `keel gate set`。第 1 段没有单次放行。
- `keel state accept` 只能人执行：从 `/dev/tty` 读确认，打不开 `/dev/tty` 就拒绝，并提示「这一步只能由人在交互终端执行：另开一个终端，在项目根目录运行 `.keel/bin/keel state accept`」（2026-11-19 实测 Claude Code 的 `!` 命令无 tty，故改为另开终端）。
- 未迁移项目（devdocs 下有 `tasks.v2` / `backlog.v2` 文档且无 `state/meta.json`）：所有写状态的命令拒绝执行，提示先跑 `/pipeline realign`；只读命令照常可用。
- 被拦提示一到两行：哪里违反、怎么改。
- 本仓「一条规则只写一处」：被接管的规则从 spec 删除条文，只留一行「由 `keel` 的 Kx 保证，被拦时这样处理」。
- SKILL.md ≤ 500 行。插件版本升到 `3.0.0`，各 manifest 同步。
- ⛔ 不改 `~/Projects/Workspace/ai-code`；迁移实测只在其 `docs/devdocs/` 的临时副本上跑。

## Review Focus

1. **Claude Code 的 `!` 命令可能拿不到 `/dev/tty`**：那样 `state accept` 人也用不了。Task 10 实测；拿不到就改为提示用户在另开的终端执行，并更新设计稿 §5.3 和错误信息。
2. **git merge 后状态 JSON 里留着冲突标记**：命令应报「`state/tasks/T-12.json` 有合并冲突，先手工解决冲突，再由人另开终端执行 `.keel/bin/keel state accept`」，不能抛 Python 栈。Task 1 测。
3. **新项目还没有任何提交，或目录不是 git 仓库**：完整性只看 manifest，K3/K4 把所有行当新增。Task 1、Task 6 测。
4. **worktree 或子模块里 `.git` 是文件**：exclude 和 hooks 路径一律用 `git rev-parse --git-path`，不能拼 `$ROOT/.git`。Task 8 测。
5. **非 keel 项目或取不到 python3**：hook 静默 exit 0，不能拦住和 keel 无关的项目。Task 8 测。

---

## 文件结构

```
skills/shared/scripts/
├── keel.py                  # CLI 入口：argparse 分发、退出码、--self-test
├── keellib/
│   ├── __init__.py
│   ├── store.py             # 路径、项目根、锁、原子写、manifest、完整性（K1/K2 的判据）
│   ├── schema.py            # 任务 / backlog 字段定义与校验（K5）
│   ├── tasks.py             # task 子命令的业务逻辑
│   ├── backlog.py           # backlog 子命令的业务逻辑
│   ├── render.py            # 生成台账区、backlog.md
│   ├── gates.py             # 阈值、K1–K4 判定、档位、命中记录、report
│   ├── hookio.py            # hook 输入解析（三端形状）与输出
│   ├── migrate.py           # tasks.v2 / backlog.v2 → state/
│   └── install.py           # 垫片、git pre-commit 串接
└── tests/                   # unittest；keel.py --self-test 跑 discover
    ├── helpers.py           # 建临时 git 项目的夹具
    └── test_<模块>.py
scripts/
└── check-python.sh          # 开发期门禁：ruff + mypy + 3.9 下自测（不随插件分发）
hooks/
├── keel-gate                # bash 薄壳：pre|post → keel.py hook
├── keel-shim                # SessionStart：keel.py install-shim
└── test-keel-gate.sh        # hook 夹具（Claude Code / Codex 两种输入形状）
```

**退出码**（全部命令）：`0` 成功；`1` 被门拦下或校验失败；`2` 用法错误；`3` 工具未就绪（未迁移、未初始化、完整性对不上、拿不到锁、内部错误）。

**数据形状**（Task 2 定死，后续任务照用）：

```json
// docs/devdocs/state/tasks/T-248.json
{"schema": "keel.task.v1", "id": "T-248", "title": "…", "status": "进行中",
 "source": "dev-tasks", "derived_from": null, "review_profile": "fast",
 "depends_on": ["T-240"], "milestone": "M-003", "layer": "core",
 "commits": [{"ref": "ai-code@<40位sha>", "note": "…"}],
 "batch": null, "due": null, "pending_reason": null, "ext_review_state": null,
 "skip_trace_reason": null, "exploration_mode": false,
 "profile_downgrade_reason": null, "record": "audit/T-248/"}

// docs/devdocs/state/backlog/F-01-1.json（文件名 = 锚点 F-01#1 把 # 换成 -）
{"schema": "keel.backlog.v1", "source_id": "F-01", "entry_no": 1, "status": "parked",
 "created_at": "2026-11-19", "created_by_skill": "verify", "note": "…",
 "detail": "backlog/F-01-1.md", "related_ids": [], "target_flow": null,
 "target_id": null, "reason": null, "superseded_by": null, "updated_at": null}

// docs/devdocs/state/meta.json
{"schema": "keel.state.v1"}

// docs/devdocs/state/gates.json（只放覆盖项）
{"K3": {"level": "warn", "reason": "…", "set_at": "2026-11-20"}}

// .keel/manifest.json：相对项目根的路径 → git blob sha1；生成区用键 "docs/devdocs/04-dev-tasks.md#ledger"
// .keel/gate-log.jsonl 每行：
{"ts": "…", "gate": "K3", "level": "block", "result": "block|warn|skip|accept|gate-set",
 "client": "claude|codex|opencode|cli", "tool": "Edit", "path": "…", "detail": "…"}
```

JSON 写盘一律 `json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`。

---

### Task 1: store —— 项目根、锁、原子写、manifest、完整性

**Files:**
- Create: `skills/shared/scripts/keel.py`、`skills/shared/scripts/keellib/__init__.py`、`skills/shared/scripts/keellib/store.py`、`scripts/check-python.sh`
- Modify: `skills/pipeline/scripts/health-lint.py`（只修 ruff 报出的问题，不改行为）、`AGENTS.md` § 验证与交付（加一行：改 `*.py` 后跑 `bash scripts/check-python.sh`，本地 pre-commit 会自动跑）
- Test: `skills/shared/scripts/tests/helpers.py`、`skills/shared/scripts/tests/test_store.py`

**Interfaces:**
- Produces:
  - `class KeelError(Exception)`，带 `code: int`（退出码）；`keel.py` 捕获后打印 `str(e)` 到 stderr 并按 `code` 退出。
  - `class Project`：`Project.find(start: str) -> Project`（git toplevel，非 git 时取 `start`）；属性 `root`、`devdocs`、`state_dir`、`keel_dir`（`<root>/.keel`）；`is_migrated() -> bool`（`state/meta.json` 存在）；`needs_migration() -> bool`（未迁移且 devdocs 下有 frontmatter 为 `tasks.v2` / `backlog.v2` 的文档）；`require_writable()`（未迁移 / 未初始化时抛 `KeelError(code=3)`，消息分别指向 `/pipeline realign` 和 `keel init`）。
  - `blob_sha(data: bytes) -> str`：git blob sha1（`sha1(b"blob %d\0" % len(data) + data)`）。
  - `head_blobs(project, paths_prefix: str) -> dict[str, str]`：一次 `git ls-tree -r HEAD -- <prefix>` 得到路径→blob；无 HEAD 或非 git 返回 `{}`。
  - `head_text(project, relpath) -> Optional[str]`：`git show HEAD:<path>`，无则 `None`。
  - `with project.lock(timeout=5.0):`：`.keel/lock` 上 `fcntl.flock`，非阻塞轮询，超时抛 `KeelError(code=3, "拿不到 .keel/lock（另一个 keel 进程在写），稍后重试")`。
  - `write_atomic(project, relpath, data: bytes)`：写同目录 `.<name>.keel-tmp` → `os.replace` → 更新 manifest 中该路径的 blob。
  - `record_region(project, key, text)`：登记生成区 blob 到 manifest。
  - `integrity_violations(project) -> list[str]`：返回不合法项的相对路径（含 `#ledger` 键）。合法 = 工作区 blob ∈ {HEAD blob, manifest blob}；工作区新增但两边都没有、或 manifest/HEAD 有而工作区被删，均不合法。
  - `require_intact(project)`：有违规就抛 `KeelError(code=3)`，消息列出文件并说「状态文件被非工具改动；用 keel 命令改回，或人工确认（人另开终端执行 `.keel/bin/keel state accept`）」。JSON 解析失败且含 `<<<<<<<` 时，消息改为合并冲突提示（Review Focus 2）。
  - `cleanup_tmp(project)`：删除 `state/` 下残留的 `.*.keel-tmp`。
  - `keel init`：建 `state/tasks/`、`state/backlog/`、`state/meta.json`，写 manifest。

- [ ] **Step 0: 开发期门禁 `scripts/check-python.sh`**：依次执行，任一失败即非零退出，并打印失败的是哪一步：
  1. `uvx ruff check --target-version py39 --select E4,E7,E9,F,B,UP skills/shared/scripts skills/pipeline/scripts`
  2. `uvx mypy --strict --python-version 3.9 skills/shared/scripts/keel.py skills/shared/scripts/keellib`（keellib 尚不存在时跳过并提示）
  3. `PY39=$(mise where python@3.9 2>/dev/null)/bin/python3`；不存在 → 失败并提示 `mise install python@3.9`（⛔ 不改用别的版本凑数）；存在 → `$PY39 skills/shared/scripts/keel.py --self-test`（keel.py 尚不存在时跳过）与 `$PY39 skills/pipeline/scripts/health-lint.py --selftest`
  然后 `mise install python@3.9`，修掉 `health-lint.py` 的 ruff 报错，跑 `bash scripts/check-python.sh` 至全绿。再写本地 `.git/hooks/pre-commit`：暂存区有 `*.py` 时跑 `bash scripts/check-python.sh`，已有 hook 时串接不覆盖。单独提交：`git commit -m "chore: Python 开发期门禁（ruff + mypy + 3.9 自测）"`。

- [ ] **Step 1: 写测试夹具 `tests/helpers.py`**：`make_project(tmp, git=True, commit=True) -> str` 建 `docs/devdocs/01-requirements.md`，可选 `git init` 并提交；`run_keel(root, *args, stdin=None) -> (code, out, err)` 用 `subprocess` 跑 `keel.py`。

- [ ] **Step 2: 写失败测试 `tests/test_store.py`**
  - `test_init_creates_state`：`keel init` 后 `state/meta.json` 存在，`.keel/manifest.json` 含 `docs/devdocs/state/meta.json`。
  - `test_tool_write_is_intact` / `test_head_content_is_intact`：工具写入后无违规；`git commit` 后删掉 manifest 仍无违规。
  - `test_hand_edit_detected`：直接改 `meta.json` → `integrity_violations` 含该路径；写命令退出码 3，stderr 含 `state accept`。
  - `test_hand_added_file_detected`、`test_deleted_file_detected`。
  - `test_merge_conflict_message`：在状态 JSON 中写入 `<<<<<<< HEAD` → stderr 含「合并冲突」，不含 `Traceback`。
  - `test_no_git_uses_manifest_only`：`git=False` 时工具写入合法、手改被发现。
  - `test_lock_timeout`：另一进程持锁时 `lock(timeout=0.2)` 抛 code 3。
  - `test_unmigrated_refuses_write`：devdocs 下放 frontmatter `spec_version: tasks.v2` 的 `04-dev-tasks.md` 且无 `state/` → 写命令退出码 3，stderr 含 `/pipeline realign`。

- [ ] **Step 3: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_store.py' -v` → 失败（模块不存在）。

- [ ] **Step 4: 实现 `store.py` 与 `keel.py` 骨架**（`init` 子命令、`--self-test` 跑 `unittest discover`、`KeelError` 退出码处理、`--root` 可选参数默认 `Project.find(os.getcwd())`）。

- [ ] **Step 5: 跑测试确认通过**：同 Step 3 → 全部 PASS；再跑 `bash scripts/check-python.sh` 全绿（含 mypy 与 3.9）。

- [ ] **Step 6: Commit**：`git commit -m "feat(keel): 状态存储、锁、原子写与完整性校验"`

---

### Task 2: schema —— 字段定义与校验（K5）

**Files:**
- Create: `skills/shared/scripts/keellib/schema.py`
- Test: `skills/shared/scripts/tests/test_schema.py`

**Interfaces:**
- Consumes: 无。
- Produces:
  - `TASK_STATUSES`、`REVIEW_PROFILES = ("fast","guarded","audit")`、`PENDING_REASONS = ("deferred-fast","deferred-guarded")`、`EXT_REVIEW_STATES = ("EXT_REVIEWED","EXT_UNRESOLVED","EXT_BLOCKED")`、`BACKLOG_STATUSES = ("parked","reactivated","closed","superseded")`、`SOURCE_PREFIXES = ("F","US","AC","T","INS","BUG","FR","NFR","M")`。
  - `TEXT_CAPS = {"title": 80, "skip_trace_reason": 200, "profile_downgrade_reason": 200, "note": 200}`。
  - `new_task(id, title, source, **fields) -> dict`、`new_backlog(source_id, entry_no, created_by_skill, note, created_at) -> dict`：按上方数据形状补全默认值。
  - `validate_task(task: dict, known_ids: set) -> list[str]`、`validate_backlog(entry: dict) -> list[str]`：返回中文错误，每条一行，格式「`<字段>`：<问题>；<怎么改>」。
  - `describe(kind: str) -> str`：`keel schema task|backlog` 的输出（字段、取值、上限、条件必填各一行）。

- [ ] **Step 1: 写失败测试**
  - 任务：枚举外状态报错；`title` 81 字报错、80 字通过（用中文字符测，确认按字符计）；`status=review_pending` 缺 `batch`/`due`/`pending_reason` 任一报错；`review_profile=audit` 且 `status=已完成` 而 `ext_review_state` 为空报错；`depends_on` 含不在 `known_ids` 的编号报错；`depends_on` 含自身报错；`derived_from` 不存在报错；`commits[].ref` 不匹配 `^[^@\s]+@[0-9a-f]{7,40}$` 报错；`source` 为空报错。
  - backlog：`source_id` 前缀为 `B` 报错；`reactivated` 缺 `target_flow`/`target_id` 报错；`closed` 缺 `reason` 报错；`superseded` 缺 `superseded_by` 报错；`note` 201 字报错。
  - `test_describe_lists_all_fields`：`describe("task")` 含每个字段名。

- [ ] **Step 2: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_schema.py' -v`

- [ ] **Step 3: 实现 `schema.py`**；`keel.py` 增加 `schema` 子命令。

- [ ] **Step 4: 跑测试确认通过**：`bash scripts/check-python.sh` 全绿。

- [ ] **Step 5: Commit**：`git commit -m "feat(keel): 任务与 backlog 字段校验（K5）"`

---

### Task 3: task 命令 —— 增、改、归档、查询

**Files:**
- Create: `skills/shared/scripts/keellib/tasks.py`
- Modify: `skills/shared/scripts/keel.py`
- Test: `skills/shared/scripts/tests/test_tasks.py`

**Interfaces:**
- Consumes: Task 1 的 `Project`、`lock`、`write_atomic`、`require_intact`、`require_writable`；Task 2 的 `new_task`、`validate_task`。
- Produces（命令行语法，skill 里照写）：
  - `keel task add --title <t> --source <s> [--derived-from T-x] [--profile fast|guarded|audit] [--depends T-1,T-2] [--milestone M-003] [--layer <l>]` → stdout 打印新编号。编号 = 现有最大 `T-<n>` + 1，在锁内分配。
  - `keel task set <id> [--status …] [--profile …] [--depends …] [--milestone …] [--layer …] [--title …] [--batch …] [--due …] [--pending-reason …] [--ext-review-state …] [--skip-trace-reason …] [--exploration-mode true|false] [--profile-downgrade-reason …] [--record …]`：一次调用里的多个字段原子生效；校验失败原文件不动、退出码 1。
  - `keel task commit <id> <repo@sha> --note <n>`：追加一条 commit。
  - `keel task archive <id>`：状态改 `已归档`。
  - `keel task get <id>`：打印该条完整 JSON。`keel task list [--status s[,s]] [--fields a,b]`：只输出文本，每条一行 `T-12 · 进行中 · 标题`（`--fields` 指定时按所列字段以 ` · ` 连接），末行 `# 扫描 N 个文件，无法识别 M 个：<路径>`（M=0 时也打印）。不提供 JSON 列表格式（用户 2026-11-19 削减）。
  - 每个写命令结束前调用 Task 5 的 `render_all(project)`。Task 5 完成前该调用是空函数。
  - `tasks.load_all(project) -> (dict[str, dict], list[str])`：返回 (id→任务, 无法解析的文件)。

- [ ] **Step 1: 写失败测试**
  - `test_add_allocates_next_id`：已有 `T-7`、`T-12` → 新增得 `T-13`。
  - `test_add_requires_source`：缺 `--source` 退出码 2。
  - `test_set_multiple_fields_atomic`：一次设 `--status review_pending --batch b1 --due 2026-11-30 --pending-reason deferred-fast` 成功；只设 `--status review_pending` 退出码 1 且文件未变。
  - `test_concurrent_set_keeps_both`：两个子进程同时对 `T-1` 分别 `set --milestone M-1` 与 `set --layer core`，结束后两个字段都在（Spec §9 并发）。
  - `test_list_reports_unreadable`：放一个坏 JSON 到 `state/tasks/` → `list` 末行含「无法识别 1 个」与该路径，退出码 0。
  - `test_list_fields`：`list --fields id,status` 每行恰为 `T-1 · 待开发` 形式。
  - `test_write_refused_when_tampered`：手改一个状态文件后 `task set` 退出码 3。

- [ ] **Step 2: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_tasks.py' -v`

- [ ] **Step 3: 实现 `tasks.py` 并接入 `keel.py`**。写命令流程固定为：`require_writable` → `lock` → `cleanup_tmp` → `require_intact` → 读 → 改 → `validate_task` → `write_atomic` → `render_all`。

- [ ] **Step 4: 跑测试确认通过**：`bash scripts/check-python.sh` 全绿。

- [ ] **Step 5: Commit**：`git commit -m "feat(keel): task 增改、归档与查询命令"`

---

### Task 4: backlog 命令

**Files:**
- Create: `skills/shared/scripts/keellib/backlog.py`
- Modify: `skills/shared/scripts/keel.py`
- Test: `skills/shared/scripts/tests/test_backlog.py`

**Interfaces:**
- Consumes: Task 1、Task 2 同上。
- Produces：
  - `keel backlog park <source_id> --note <n> --by <skill> [--related AC-1,AC-2]` → 打印锚点 `F-01#2`。同一 `source_id` 下 `entry_no` 递增。已有 `parked` 条目时：`M-` 前缀直接追加；其他前缀要求 `--append` 才写，否则退出码 1，提示「`F-01` 已有 parked 条目 F-01#1；确认追加加 `--append`，要更新原条目用 `keel backlog note F-01#1`」。
  - `keel backlog note <anchor> --note <n>`、`keel backlog reactivate <anchor> --target-flow <f> --target-id <id>`、`keel backlog close <anchor> --reason <r>`、`keel backlog supersede <anchor> --by-id <x>`：只允许从 `parked` 迁出。
  - `keel backlog get <anchor>`（完整 JSON）、`keel backlog list [--status s] [--fields …]`（文本，覆盖情况同 task list）。
  - `backlog.load_all(project) -> (dict[str, dict], list[str])`，键为锚点。

- [ ] **Step 1: 写失败测试**：`park` 编号递增；`B-001` 被拒；非 M 来源重复入池无 `--append` 被拒、有则追加；`M-003` 重复入池直接追加；`closed` 后再 `reactivate` 被拒；`list --status parked` 只返回 parked；note 201 字被拒。

- [ ] **Step 2: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_backlog.py' -v`

- [ ] **Step 3: 实现 `backlog.py` 并接入 `keel.py`**，写命令流程同 Task 3 Step 3。

- [ ] **Step 4: 跑测试确认通过**：`bash scripts/check-python.sh` 全绿。

- [ ] **Step 5: Commit**：`git commit -m "feat(keel): backlog 入池、迁移与查询命令"`

---

### Task 5: render —— 生成台账区与 backlog.md

**Files:**
- Create: `skills/shared/scripts/keellib/render.py`
- Modify: `skills/shared/scripts/keellib/tasks.py`、`skills/shared/scripts/keellib/backlog.py`（接上 `render_all`）、`skills/shared/scripts/keel.py`（`keel render`）
- Test: `skills/shared/scripts/tests/test_render.py`

**Interfaces:**
- Consumes: `tasks.load_all`、`backlog.load_all`、`write_atomic`、`record_region`。
- Produces：
  - `BEGIN = "<!-- keel:begin ledger -->"`、`END = "<!-- keel:end ledger -->"`、`REGION_KEY = "docs/devdocs/04-dev-tasks.md#ledger"`。
  - `ledger_region(tasks: dict) -> str`：表头 `| 编号 | 标题 | 状态 | profile | 依赖 | 里程碑 | 记录 |`，按编号数值升序列出未归档任务；末行 `已归档 N 张，定义见 [archive/04-dev-tasks-archive.md](archive/04-dev-tasks-archive.md)`。
  - `backlog_md(entries: dict) -> str`：frontmatter `generated_by: keel` / `spec_version: backlog.v3`，提示行「本文件由 keel 生成，改状态用 `keel backlog …`」，`## Index` 下按 `parked` / `reactivated` / `closed` / `superseded` 分组，每条一行 `- F-01#1 · <note> · [详情](backlog/F-01-1.md)`（无 detail 不加链接）。
  - `render_all(project)`：`04-dev-tasks.md` 存在且含标记 → 只替换两标记之间的内容并 `record_region`；存在但无标记 → 退出码 3，提示「04-dev-tasks.md 缺少 keel 生成区标记，先跑 `keel migrate`」；不存在 → 跳过。`backlog.md` 有条目时整份重写。
  - `region_text(file_text) -> Optional[str]`：取两标记之间的文本，供 Task 1 的完整性判据和 Task 6 使用（在 `store.integrity_violations` 里接上 `#ledger` 键）。

- [ ] **Step 1: 写失败测试**：生成区只改两标记之间、外部字节不变；已归档不出现在表中、末行计数正确；手改生成区一个字 → `integrity_violations` 含 `#ledger`；`backlog.md` 分组正确；每行 ≤ 500 字符（30 字依赖列表的夹具）。

- [ ] **Step 2: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_render.py' -v`

- [ ] **Step 3: 实现 `render.py`**，接入 task/backlog 写命令和 `store.integrity_violations`。

- [ ] **Step 4: 跑全部测试确认通过**：`bash scripts/check-python.sh` 全绿。

- [ ] **Step 5: Commit**：`git commit -m "feat(keel): 生成台账区与 backlog 索引"`

---

### Task 6: gates —— K1–K4、档位、命中记录、check、state accept

**Files:**
- Create: `skills/shared/scripts/keellib/gates.py`
- Modify: `skills/shared/scripts/keel.py`、`skills/pipeline/scripts/health-lint.py`
- Test: `skills/shared/scripts/tests/test_gates.py`

**Interfaces:**
- Consumes: Task 1 的完整性与 `head_text`；Task 5 的 `region_text`。
- Produces：
  - `LINE_CAP = 500`、`SIZE_CAP = 98304`、`DEFAULT_LEVELS = {"K1": "block", "K2": "block", "K3": "block", "K4": "block"}`、`CARRIER_GLOBS`（见 Global Constraints）。
  - `is_carrier(relpath) -> bool`、`line_too_long(line: str) -> bool`（health-lint 用）。
  - `Finding = namedtuple("Finding", "gate path line detail")`。
  - `check_k1k2(project) -> list[Finding]`；`check_k3(project, relpath, text: str) -> list[Finding]`（与 `head_text` 比对：当前行若不在 HEAD 行的多重集合里即为新增或改动，超 `LINE_CAP` 记一条；无 HEAD 时全部算新增）；`check_k4(project, relpath, size: int) -> list[Finding]`（`size > SIZE_CAP` 且大于 HEAD 版本字节数，无 HEAD 版本时只看 `size > SIZE_CAP`）。
  - `level(project, gate) -> str`：读 `state/gates.json` 覆盖，否则默认。
  - `log_hit(project, gate, level, result, client, tool, path, detail)`：追加 `.keel/gate-log.jsonl`。
  - `apply_levels(project, findings, client, tool) -> (blocks: list[Finding], warns: list[Finding])`：按档位分流，每条都 `log_hit`（`off` 记 `skip`）。
  - `format_findings(findings) -> str`：每条一行「Kx `<路径>`[:行]：<问题>；<怎么改>」。各门的「怎么改」：K1「用 `keel task|backlog` 命令改，或人工确认（人另开终端执行 `.keel/bin/keel state accept`）」；K2「生成内容只由 keel 写，跑 `.keel/bin/keel render` 从状态重新生成」；K3「超长内容移到 `audit/T-xxx/` 或 `backlog/<id>.md`，此处留链接」；K4「先归档或拆分（`/sync --archive`），本文件只能改小」。
  - 命令：`keel check [--staged] [--paths p1 p2 …]`（`--staged` 时只检查 `git diff --cached --name-only` 列出的文件，读的是它们在**工作区**的内容。shortcut: 部分暂存时检查内容与提交内容可能不同，最后一道兜底可接受；真遇到漏放再改读 index。无 `--paths` 时检查所有与 HEAD 不同的载体文件），有 block 退出码 1；`keel gate set <K1..K4> <block|warn|off> --reason <r>`（写 `state/gates.json` 走 `write_atomic`，并记 `gate-set`）；`keel gate report [--since YYYY-MM-DD]`（按门汇总次数与涉及文件，附「每卡派生数」：按 `derived_from` 计数，列出前 10）；`keel state accept`（打开 `/dev/tty` 读入 `accept` 才执行：把当前所有状态文件与生成区 blob 写入 manifest，记 `accept`；打不开就退出码 3 并提示另开终端执行 `.keel/bin/keel state accept`）。

- [ ] **Step 1: 写失败测试**
  - K3：HEAD 已有 600 字符行，改其他行 → 无命中；新增 501 字中文行 → 命中（按字符计）；新增 500 字 → 不命中；改动已有超长行使其仍超长 → 命中；非载体文件（`audit/T-1/x.md`）新增 900 字 → 不命中；无提交的仓库里 501 字行 → 命中。
  - K4：HEAD 120KiB、现在 119KiB → 不命中；现在 121KiB → 命中；HEAD 90KiB、现在 97KiB → 命中。
  - 档位：`gate set K3 warn --reason x` 后 K3 进 warns；日志新增 `gate-set` 与 `warn` 各一行；`gate set K5 off` 退出码 2。
  - `check --staged`：暂存一个手改的状态文件 → 退出码 1。
  - `state accept` 在无 tty 的子进程里退出码 3，stderr 含「另开一个终端」与 `.keel/bin/keel state accept`。
  - `gate report`：夹具日志 3 条 K3、1 条 K1 → 输出含 `K3 3`、`K1 1`。

- [ ] **Step 2: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_gates.py' -v`

- [ ] **Step 3: 实现 `gates.py` 与命令**。

- [ ] **Step 4: `health-lint.py` 改为导入阈值**：在文件头 `sys.path.insert(0, <本文件>/../../shared/scripts)` 后 `from keellib.gates import LINE_CAP, SIZE_CAP, line_too_long`；删除本地 `LINE_CAP` 与 `SIZE_CAP_BYTES` 定义，`scan_state` / `scan_layout` 用导入值。`SIZE_WARN` / `SIZE_BLOCK`（devdocs-state.md 专用的 10/40 KiB）保持原样。

- [ ] **Step 5: 跑测试确认通过**：`bash scripts/check-python.sh` 全绿（含 health-lint 自测）。

- [ ] **Step 6: Commit**：`git commit -m "feat(keel): K1–K4 门禁、档位、命中记录与 state accept"`

---

### Task 7: migrate —— 存量项目升级

**Files:**
- Create: `skills/shared/scripts/keellib/migrate.py`
- Modify: `skills/shared/scripts/keel.py`、`skills/shared/devdocs-layout.md`（登记 `state/tasks/T-<N>.json`、`state/backlog/<slug>.json`、`state/meta.json`、`state/gates.json`，属主 `keel`）
- Test: `skills/shared/scripts/tests/test_migrate.py`、`skills/shared/scripts/tests/fixtures/migrate/`（keel 模板样例 + 按 ai-code 表头仿造的小样例，⛔ 不复制 ai-code 原文）

**Interfaces:**
- Consumes: Task 1–5 全部。
- Produces：
  - `keel migrate [--dry-run | --apply] [--map-status "<原值>=<目标值>" …] [--allow-partial]`，默认 `--dry-run`；两种模式都写 `.keel/migration-report.md`。
  - `COLUMN_ALIASES`：`ID|编号|任务` → id；`描述|标题|任务名称` → title；`状态|status` → status；`profile|review_profile|档` → review_profile；`依赖` → depends_on；`来源` → source；`层|层级` → layer；`commits|已提交？` → commits；`ext_review_state` → ext_review_state；`备注` → 只进长文本记录。
  - `STATUS_ALIASES`：`待开发|todo|⬜` → 待开发；`进行中|🔄` → 进行中；`review_pending` → review_pending；`已完成|✅|done` → 已完成；`已归档` → 已归档。其余值进报告，须 `--map-status` 指定，⛔ 不猜。
  - 只认下列实际出现过的形态，⛔ 不写通用 markdown 表格解析（用户 2026-11-19 削减）；其余一律进报告「未识别」。识别来源：①`#### T-<n>: <名称>` 后的属性表（`| **状态** | … |`）；②首列表头命中 id 别名、单元格匹配 `T-\d+` 的汇总表；③分册的 `## T-<n> · <标题>` 节（只取标题）。同一编号多处出现时，状态以主文件汇总表为准，不一致的写进报告。
  - 超上限文本（标题 >80、备注、非 `repo@sha` 形状的 commits 文本）：追加到 `audit/T-<n>/ledger-record.md`，段首 `## 迁移自 <文件>（<日期>）`；该文件已含同一段文本则不重复追加；`record` 指向 `audit/T-<n>/`；标题截到 79 字加 `…`。
  - backlog 识别：集中形态 `### <锚点>` + 其后第一个 yaml 围栏块；目录形态 `backlog/*.md` 的第一个 yaml 围栏块。键 `id` 视同 `source_id`（ai-code 样本 54 条用 `id`）；锚点形如 `T-26#1` 时从中拆出 `entry_no`。`detail` 指向原 `backlog/<file>.md`。
  - `--apply`：先 `keel init`；写全部状态；`04-dev-tasks.md` 中被解析的汇总表整体替换为生成区标记（插在第一张表的位置），属性表里删去 状态 / commits / ext_review_state 三行；各文档 frontmatter `spec_version` 改为 `tasks.v3` / `backlog.v3`；`backlog.md` 重新生成。有未识别任务或未映射状态且无 `--allow-partial` 时，拒绝执行、退出码 1。
  - 报告结构：`## 已迁移`（计数）、`## 未识别`（文件:行 + 原文前 60 字）、`## 待映射状态`（值 → 出现次数）、`## 状态冲突`、`## 搬出的长文本`。

- [ ] **Step 1: 写夹具**：`fixtures/migrate/keel-template/`（按 `skills/dev-tasks/templates/task-template.md` 写 3 张卡）；`fixtures/migrate/aicode-shape/`（主文件汇总表 `ID | 描述 | 状态 | profile | 执行 | 依赖 | 来源 | 层`、另一张 `任务 | 档 | 已提交？ | ext_review_state | 备注` 表、一个 `-core` 分册的 `## T-xx · 标题` 节、`backlog/` 目录里 3 个文件（一个用 `source_id`、一个用 `id`、一个无 yaml 的索引卡）、一个自定义状态 `🔍 待审查`、一条 700 字备注）。

- [ ] **Step 2: 写失败测试**：keel 模板 dry-run 识别 3 张、无未识别；aicode-shape dry-run 报告列出 `🔍 待审查` 与那张索引卡；无 `--map-status` 时 `--apply` 退出码 1 且原文件字节不变；带 `--map-status "🔍 待审查=review_pending" --allow-partial` 时 `--apply` 成功，`audit/T-x/ledger-record.md` 含那 700 字，第二次 `--apply` 不重复追加；迁移后 `task list` 条数 = 报告「已迁移」条数；迁移后 `keel check` 无 K1/K2；迁移后 `health-lint.py --target` 无 `layout/unknown-path` 指向 `state/`。

- [ ] **Step 3: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_migrate.py' -v`

- [ ] **Step 4: 实现 `migrate.py`、登记布局**。

- [ ] **Step 5: 跑测试确认通过**：`bash scripts/check-python.sh` 全绿。

- [ ] **Step 6: ai-code 副本实测**：
  ```bash
  S=$(mktemp -d); cp -R ~/Projects/Workspace/ai-code/docs "$S/"; git -C "$S" init -q && git -C "$S" add -A && git -C "$S" -c user.name=t -c user.email=t@t commit -qm snap
  python3 skills/shared/scripts/keel.py --root "$S" migrate --dry-run; cat "$S/.keel/migration-report.md" | head -80
  ```
  预期：报告给出已迁移、未识别、待映射计数，不抛异常。按报告补 `--map-status` 后 `--apply --allow-partial` 成功，`task list` 末行的扫描数与报告一致。把报告摘要（计数 + 未识别类别）记进本计划末尾「实测记录」。⛔ 不动 ai-code 原目录。

- [ ] **Step 7: Commit**：`git commit -m "feat(keel): tasks.v2/backlog.v2 迁移与布局登记"`

---

### Task 8: hook 与安装 —— Pre/Post、垫片、git pre-commit

**Files:**
- Create: `skills/shared/scripts/keellib/hookio.py`、`skills/shared/scripts/keellib/install.py`、`hooks/keel-gate`、`hooks/keel-shim`、`hooks/test-keel-gate.sh`
- Modify: `skills/shared/scripts/keel.py`、`hooks/hooks.json`、`hooks/opencode-plugin.js`、`hooks/skill-flag-lint`（Codex 补丁路径，见下）
- Test: `skills/shared/scripts/tests/test_hookio.py`、`hooks/test-keel-gate.sh`

**Interfaces:**
- Consumes: Task 6 的 `check_k1k2`、`check_k3`、`check_k4`、`apply_levels`、`format_findings`。
- Produces：
  - `hookio.edited_paths(payload: dict, root: str) -> list[str]`：`tool_input.file_path`/`filePath`/`path`；以及 `tool_input` 任一字符串字段里的 `*** (Add|Update|Delete) File: <p>` 与 `*** Move to: <p>` 行（Codex `apply_patch`、OpenCode `patchText`）。返回相对项目根的路径。
  - `keel hook pre`：stdin 读 payload。目标路径落在 `docs/devdocs/state/` 下或等于 `docs/devdocs/backlog.md` 时按 K1/K2 档位处理：block 输出 `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"<format_findings>"}}`；warn 输出 additionalContext。Bash/shell 不在 Pre 拦（Post 兜）。
  - `keel hook post`：跑 `check_k1k2` + 对「与 HEAD 不同的载体文件」跑 K3/K4。有 block 输出 `{"decision":"block","reason":"…"}`；只有 warn 输出 `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"…"}}`；无命中不输出。
  - `keel hook paths`：stdin 读 payload，按 `edited_paths` 一行输出一个相对路径（供 `skill-flag-lint` 用）。
  - client 判定：环境变量 `KEEL_CLIENT`（OpenCode 插件设为 `opencode`）；否则 `tool_name` 为 `apply_patch` 或 `shell` 记 `codex`，其余记 `claude`。只用于日志。
  - `keel install-shim --plugin-root <dir>`：写 `<root>/.keel/bin/keel`（`#!/bin/bash\nexec python3 "<dir>/skills/shared/scripts/keel.py" "$@"\n`，chmod 755）；把 `.keel/` 加进 `git rev-parse --git-path info/exclude` 指向的文件（已有则不重复）。项目 `needs_migration()` 时 stdout 输出 SessionStart additionalContext：「keel 3.0：本项目台账尚未迁移，写台账和 backlog 的命令会拒绝执行；先跑 /pipeline realign」。
  - `keel git-hook install`：目标目录 = `git rev-parse --git-path hooks`（尊重 `core.hooksPath`）。已有非 keel 的 `pre-commit` → 改名 `pre-commit.keel-chained`，新 hook 先跑 `.keel/bin/keel check --staged`（退出码 0 放行；垫片不存在或自检失败（4，或 126/127）时打印一行警告并放行；其余非 0，含 1 被拦与 3 检查完成不了，一律拒绝），再 `exec` 被串接的旧 hook；已是 keel 的 hook → 不动。打印做了什么。
  - `hooks/keel-gate <pre|post>`：非 keel 项目（无 `docs/devdocs/`）或无 `python3` → `exit 0`；否则 `exec python3 "${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/skills/shared/scripts/keel.py" --root "${CLAUDE_PROJECT_DIR:-$PWD}" hook "$1"`。⛔ 不用 `timeout(1)`（见 `hooks/README.md`）。
  - `hooks/keel-shim`：同样的静默条件，然后 `keel.py --root … install-shim --plugin-root "${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}"`。
  - `hooks.json`：SessionStart 增加 `keel-shim`；新增 PreToolUse `matcher: "Edit|Write|MultiEdit|NotebookEdit|apply_patch"` → `keel-gate pre`；PostToolUse 增加 `matcher: "Edit|Write|MultiEdit|NotebookEdit|apply_patch|Bash|shell"` → `keel-gate post`。
  - `opencode-plugin.js`：`setup` 里跑一次 `keel.py install-shim`；新增 `ctx.tool.hook("execute.before", …)`：对 edit/write/patch 工具跑 `keel.py hook pre`（`KEEL_CLIENT=opencode`），输出含 `permissionDecision: "deny"` 时 `throw new Error(reason)`；`execute.after` 对 edit/write/patch/shell 追加跑 `keel.py hook post`，把 `reason` 或 additionalContext 追加进结果。路径解析复用 `hookio` 的规则：插件把原始 `event.input` 原样传给 `keel.py`，不在 JS 里重复解析。
  - `skill-flag-lint`：现在只读 `tool_input.file_path`，Codex 上拿不到路径。改为当 `file_path` 为空时调用 `keel.py hook paths`（输出 `edited_paths` 一行一个），对其中 `skills/**/*.md` 逐个跑原检查。

- [ ] **Step 1: 写失败测试 `test_hookio.py`**：Claude `Edit` payload 取到 `file_path`；Codex `apply_patch` 补丁文本（含 `*** Update File:` 与 `*** Move to:`）取到两个路径；OpenCode `patchText` 同理；Pre 对 `state/tasks/T-1.json` 输出 deny、对 `src/a.py` 无输出；Post 在手改状态文件后输出 `decision: block`；K3 档位设 `warn` 后 Post 输出 additionalContext 而非 block；`install-shim` 在 worktree（`git worktree add`）里写对 exclude 文件；`git-hook install` 遇到已有 hook 时串接、第二次运行不重复改名。

- [ ] **Step 2: 写 `hooks/test-keel-gate.sh`**（仿 `test-devdocs-drift.sh`）：用例——Claude 形状 Pre 拒绝写状态文件；Codex 形状 Pre 拒绝补丁改 `backlog.md`；Post 发现 Bash 改过的状态文件；Post 拦新增超长行；非 keel 项目静默；`PATH` 里去掉 python3 时静默。

- [ ] **Step 3: 跑测试确认失败**：`python3 -m unittest discover -s skills/shared/scripts/tests -p 'test_hookio.py' -v`；`bash hooks/test-keel-gate.sh`

- [ ] **Step 4: 实现上述文件**。

- [ ] **Step 5: 跑测试确认通过**：`bash scripts/check-python.sh` 与 `bash hooks/test-keel-gate.sh` 全过；`bash hooks/test-devdocs-drift.sh` 仍通过；`node --check hooks/opencode-plugin.js`。

- [ ] **Step 6: 性能**：在 Task 7 Step 6 的 ai-code 迁移副本上 `time (echo '{"tool_name":"Edit","tool_input":{"file_path":"'$S'/docs/devdocs/04-dev-tasks.md"}}' | CLAUDE_PROJECT_DIR=$S bash hooks/keel-gate post)` 三次取中位数，预期 < 300ms；超出时先查 git 调用次数（应为常数次：一次 `ls-tree`、一次 `diff --name-only`、按需 `show`）。

- [ ] **Step 7: Commit**：`git commit -m "feat(hooks): keel 门禁 hook、垫片与 git pre-commit 串接"`

---

### Task 9: skill 改走命令、spec 瘦身

规则：每个文件里「写状态字段」「改 backlog 条目」「取最大 T 编号」的指令改为对应 `keel` 命令；重复字段表、枚举、条件必填、行长 / 体积条文删除，只留一行「由 `keel` 的 Kx 保证；字段与取值见 `.keel/bin/keel schema task|backlog`；被拦时按提示处理」。读状态改为「读 `04-dev-tasks.md` 生成区或 `keel task list/get`」。垫片不存在时的统一说法写在 `constraints.md` 一处：「`.keel/bin/keel` 不存在 → 告诉用户 keel 工具未就绪（可能原因：会话启动 hook 未运行、Codex 未在 `/hooks` 信任插件、缺 python3），⛔ 不手写状态文件」，别处只链接。

**Files:**
- Modify（写方）：`skills/shared/constraints.md`（§任务台账协议、§review_pending 字段段落、新增「keel 工具」小节作为垫片与退出码的唯一出处）；`skills/dev-tasks/SKILL.md`、`skills/dev-tasks/templates/task-template.md`（`spec_version: tasks.v3`；任务状态表下放生成区标记；属性表删 状态 / commits / 审查状态行；新建任务先 `keel task add` 拿编号）；`skills/dev-workflow/SKILL.md` 与 `references/{execution-flow,task-orchestration,verification-flow,auto-mode,inline-entry}.md`；`skills/verify/SKILL.md`（`--review-drain` 段）；`skills/sync/SKILL.md` 与 `references/{archive,absorb-mode}.md`；`skills/feature/SKILL.md`；`skills/retrofit/SKILL.md`；`skills/backlog/SKILL.md`、`skills/backlog/references/realign.md`（`backlog.v3`；四个动作改为 `keel backlog …`；门控条文删除）；`skills/pipeline/SKILL.md` 与 `references/realign.md`（检测到 `tasks.v2` / `backlog.v2` 时调度 `keel migrate --dry-run`，restructuring 级别逐项确认后 `--apply`，完成后询问是否 `keel git-hook install`）；`skills/agent-memory/templates/memory-template.md`（「台账状态由 keel 工具维护，直接编辑会被拦」）。
- Modify（只读方）：`skills/onboard`、`skills/compound`、`skills/test-run`、`skills/dev-flow`、`skills/verify`（readiness、schema-drift 认 `tasks.v3` / `backlog.v3`）、`skills/retrofit`（version-migration 表加 v2→v3 行）、`skills/agent-memory/templates/devdocs-state-template.md` 中读状态的位置。

- [ ] **Step 1: 列出全部改动点**：
  ```bash
  grep -rnE 'commits|batch|pending_reason|ext_review_state|skip_trace_reason|exploration_mode|profile_downgrade_reason|review_pending|tasks\.v2|backlog\.v2|最大 T|max.*T-|backlog\.md' skills --include='*.md' > "$(mktemp -t keel-p1-hits)"  # 在输出文件里逐条标注
  ```
  逐条标注：改为命令 / 删除（规则已由工具保证）/ 保留（只是语义说明且 `constraints.md` 是真源）。

- [ ] **Step 2: 先改真源 `constraints.md`**，再改各 skill（按 AGENTS.md「先收回真源再改」）。

- [ ] **Step 3: 检查**：`python3 skills/pipeline/scripts/health-lint.py --skills-dir skills` 无新增 blocker；`wc -l skills/*/SKILL.md | sort -n | tail -3` 均 ≤ 500；`git diff --check`；再跑 Step 1 的 grep，剩余命中逐条确认属于「保留」。

- [ ] **Step 4: 代表性走查**（行为检查，不靠格式）：在 Task 7 的 keel 模板夹具迁移结果上，按改后的 `dev-workflow` 文本手动走一遍「认领 → review_pending → drain → 已完成」，每一步对应的 `keel` 命令都能成功执行；按改后的 `backlog` 文本走一遍 park → close。

- [ ] **Step 5: Commit**：`git commit -m "refactor(skills): 台账与 backlog 状态改走 keel 命令，删去被工具接管的条文"`

---

### Task 10: 文档、发布与真实客户端验证

**Files:**
- Modify：`hooks/README.md`（改写「门不进 hook」决策，注明依据本设计稿；新增 keel-gate / keel-shim 说明；三端漏口表引用设计稿 §6）；`docs/audits/2026-09-28-ai-code-process-audit.md`（「hook 拦截直接编辑台账——不做」处加一行：已由 2026-11-19 设计稿推翻）；`docs/architecture.md`（四层防线、`state/` 布局、`keel.py` 位置）；`README.md`（运行时要求 python3≥3.9 + bash、原生 Windows 不支持、Codex 升级插件后须在 `/hooks` 重新信任、`keel gate report` 用途）；`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`plugin.json`、`.agents/plugins/marketplace.json`、`package.json` 版本 → `3.0.0`。

- [ ] **Step 1: 改文档与版本**；`grep -rn '"version"' .claude-plugin plugin.json .agents package.json` 全部为 `3.0.0`。

- [ ] **Step 2: Claude Code 真实会话实测**（在 Task 7 的 ai-code 迁移副本里开会话）：① 会话启动后 `.keel/bin/keel` 存在；② 让模型用 Edit 改 `state/tasks/` 下文件 → 被拒并看到原因；③ 让模型用 Bash `sed -i` 改状态文件 → 下一次工具调用的 Post 拦回；④ 新增一行 600 字到 `04-dev-tasks.md` → Post 拦回；⑤ 在会话里输入 `! .keel/bin/keel state accept` → 记录是否拿到 `/dev/tty`（Review Focus 1）。拿不到时：错误信息改为「请在另开的终端执行 `.keel/bin/keel state accept`」，并同步改设计稿 §5.3 与 Global Constraints。

- [ ] **Step 3: Codex、OpenCode 能测则测**：同样的 ②③④；另测 Codex 是否触发 SessionStart、`"shell": "bash"` 字段是否被接受、hook 名 `apply_patch` / `shell` 是否匹配。测不了的逐项写进交付说明。

- [ ] **Step 4: 全量检查**：`bash scripts/check-python.sh`；`bash hooks/test-keel-gate.sh`；`bash hooks/test-devdocs-drift.sh`；`node --check hooks/opencode-plugin.js`；`git diff --check`。

- [ ] **Step 5: 独立审查**：按 AGENTS.md 用 codex 审查脚本与 hook 的代码行为（`/adversarial-review --code`）。

- [ ] **Step 6: Commit**：`git commit -m "docs: keel 3.0.0 门禁机制化第 1 段发布说明与版本号"`

---

## 实测记录

（Task 7 Step 6、Task 8 Step 6、Task 10 Step 2–3 的结果写在这里。）

### Task 7 Step 6：ai-code 副本迁移（2026-11-19）

在 `mktemp -d` 下的 `ai-code/docs` 副本上跑（新 `git init`，清掉 `GIT_*`），原目录未动。

- `--dry-run`：任务 0、backlog 204，未识别 444，待映射状态 1（`⚪` 1 次，2.13 表一行列错位，状态列里填的是层）；无异常。
- 未识别类别：
  - 256 条：汇总表首列表头是 `#`，不是 ID / 编号 / 任务（2.1–2.12 各段总表）。按削减后的范围不认。
  - 156 条：缺状态来源。ai-code 的状态写在编号单元格后缀（`T-168 ✅`、`T-302 🔍 待审查`）和分册节里的 `> **状态（日期）**` 引用块，这两种形态都不在识别范围内。外审台账、执行检查清单两张表都没有状态列。
  - 23 条：backlog 校验失败，其中 11 条 `source_id` 前缀为 `CON`（不在 schema 前缀表），11 条 `status: closed` 缺 `reason`，1 条缺 `created_at`。
  - 9 条：`backlog/*.md` 没有 yaml 块（索引卡）。
- `--apply` 无 `--allow-partial`：退出码 1，未写入。`--apply --allow-partial`：成功；`task list` 末行「扫描 0 个文件」、`backlog list` 末行「扫描 204 个文件」，与报告一致；`keel check` 无 K1/K2；第二次 `--apply` 不重复写入。
- 文档改动：`04-dev-tasks*.md` 与 `24-master-merge-20261104.md` 的 `spec_version` 升到 v3；主文件在外审台账表前插入生成区（该表各行未迁移，原样保留在区外）；`backlog.md` 重新生成，原文另存为 `backlog/index.md`。
- 结论：按削减后的识别范围，ai-code 的任务状态一张都迁不过来。要迁 ai-code 的任务，至少还要认「`#` 首列表头」和「编号单元格后缀里的状态」两种形态，需用户决定是否扩大范围。

#### 修订 1 后重跑（A1–A5，2026-11-19）

识别范围补了 ai-code 的三种实际形态：`#` 首列表头、编号单元格后缀里的状态、分册节下的 `> **状态**` 引用块。重跑使用新的 mktemp 副本，原目录未动。

- 不带 `--map-status` 的 dry-run：任务 61、backlog 204，未识别 213，待映射状态 23 种。待映射里次数最多的是 `🔍 待审查` 37、`关闭` 15、`→ M-004` 7、`关闭（作废）` 6；其余多是一次性的自由文本，例如「M-002 内关闭·余下交 M-003 测试」。
- 示例映射：`🔍 待审查=review_pending`、`关闭=已完成`、`关闭（作废）=已归档`、`已提交`/`已提交·外审过=已完成`、`→ M-004`/`→ 第 2 批`/`→ M-003=待开发`。这只是测量用的示例，正式映射由用户定。
- 示例映射下 `--apply --allow-partial` 的结果：
  - 迁出任务 117（其中 36 张补成 review_pending），backlog 204；`task list` / `backlog list` 的扫描数与报告一致；
  - 无 K1/K2；health-lint 对 `state/`、`ledger-record.md`、`migration-v3.md` 没有 unknown-path；
  - docs 未提交时再跑 apply 被拒；提交后再跑，迁出 0，不重复写入。
- 剩余未识别（示例映射下 240 条）：
  - 138 条缺状态来源：这些任务的状态在任务文档里没有任何结构化写法，只出现在 `00-context.md` 的叙述里（如 T-15），工具无从识别，不猜；
  - 23 条任务校验失败：16 条 audit 档已完成但缺 `ext_review_state`，7 条 profile 列里填了层图标或长文本（列错位）；
  - 6 条依赖指向未迁移任务；3 条缺标题（阻塞任务块的行）；
  - backlog 23 条校验失败、9 张索引卡没有 yaml，情况同首轮。
- 结论：大约 117 / 280 张任务能迁出。剩下的主要缺口是任务文档里本来就没写状态，要由用户补写，或在迁移后用 `keel task add` / `set` 补录。

### Task 10 Step 2：Claude Code 真实会话实测（2026-11-19）

Claude Code headless `claude -p --plugin-dir`，ai-code devdocs 副本（已迁移 102 任务 / 204 backlog）。

- ① 垫片 `.keel/bin/keel` 写出：✅
- ② Edit 状态文件 → Pre 拒绝 K1：✅
- ③ Bash `sed` 改状态文件 → Post 拦回 K1：✅
- ④ 600 字一行 → Post 拦回 K3（并带 K4）：✅
- ⑤ `!` 命令没有 tty → 改为另开终端执行：✅（已改，同步改设计稿 §5.3、Global Constraints、constraints.md、README、提示文案）
- ⑥ 模型 Bash 调 `state accept` → Pre 拒绝（human）：✅
- Task 10 Step 3（Codex / OpenCode）：本轮未测。
