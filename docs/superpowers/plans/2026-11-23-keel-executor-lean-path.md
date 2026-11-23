# keel 精简执行路径 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 被派执行者自己做卡、纯移动卡只做确定性检查、表征测试先绿、按批提交台账，并由 keel「完成门」用 git 机器检查顺序、冻结与纯移动。

**Architecture:** keel CLI 增加 `move` 档、`commits[].kind`、`move-check` 子命令、`task get --diff-range`，以及在 `task set --status 已完成|review_pending` 写入前运行的完成门（新模块 `keellib/donegate.py`，纯 git 调用）。skill 文档只写流程，规则真源在 `shared/constraints.md`。

**Tech Stack:** Python 3.9 标准库 + git CLI；unittest；ruff、mypy --strict 1.18.2（`scripts/check-python.sh`）。

**Spec:** `docs/superpowers/specs/2026-11-22-keel-executor-lean-path-design.md`

## Global Constraints

- 仅标准库，Python ≥ 3.9（`from __future__ import annotations`，不用 3.10+ 语法如 `match`、`X | Y` 运行时求值）。
- schema 仍为 `keel.task.v1`；只加枚举值 `move` 和可选字段 `commits[].kind`（取值仅 `test`）。
- 完成门任一检查不过：退出码 1、任务文件不变、提示原因；⛔ 不提供跳过开关。
- 用户面零子指令：keel 打印给用户/agent 的提示不得出现 `/<skill> <子命令>` 或 `--flag` 形式的用户入口（agent 用的 keel 命令本身除外）。
- 一条规则只写一处：跨 skill 定义写 `skills/shared/constraints.md`，别处只留指针。
- SKILL.md ≤ 500 行（dev-workflow 现 433 行）。
- 每个改 `*.py` 的任务结束跑 `bash scripts/check-python.sh` 全绿；改文档跑 `git diff --check`。
- 提交：Conventional Commits，结尾 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- 版本升到 3.1.0（`plugin.json`、`.claude-plugin/plugin.json`）。

## Review Focus

1. 老用户零影响：没有 `kind=test` 提交、`review_profile` 不是 `move` 的任务，`task set --status 已完成` 行为与 3.0.3 完全一致，不调用 git（Task 3 `test_gate_skipped_without_test_commits_or_move`）。
2. shell 拓扑：sha 在子模块目录 `<root>/<repo>` 里而不在根仓，完成门要能解析（Task 3 `test_resolves_sha_in_subrepo_dir`）。
3. 只改缩进的搬移不算胶水（Task 2 `test_indent_only_move_has_no_glue`）。
4. JS/TS `import x from './y'` 这类带字符串的导入行是胶水但不算改逻辑（Task 2 `test_import_lines_not_logic`）。
5. 只改非状态字段（如 `--record`）不触发完成门，即使任务已是已完成（Task 3 `test_gate_only_on_status_change`）。

---

### Task 1: schema——`move` 档与 `commits[].kind`

**Files:**
- Modify: `skills/shared/scripts/keellib/schema.py`（`REVIEW_PROFILES`、commits 校验、schema 说明行 `:165`）
- Modify: `skills/shared/scripts/keellib/tasks.py`（`commit()` 加 `kind`）
- Modify: `skills/shared/scripts/keel.py`（`task commit` 加 `--kind`）
- Test: `skills/shared/scripts/tests/test_schema.py`、`tests/test_tasks.py`

**Interfaces:**
- Produces: `schema.REVIEW_PROFILES == ("fast", "guarded", "audit", "move")`；`schema.COMMIT_KINDS == ("test",)`；`tasks.commit(project, tid, ref, note, kind: str | None = None) -> None`，`kind` 非空时写入条目 `{"ref", "note", "kind"}`，为空时条目不含 `kind` 键（旧文件字节不变）。

- [ ] **Step 1: 写失败测试**
  - `test_schema.py::test_move_profile_valid`：`validate_task(new_task("T-1","t","F-001", review_profile="move"), set())` 返回 `[]`。
  - `test_schema.py::test_commit_kind_test_valid`：commits `[{"ref":"app@abcdef1","note":"n","kind":"test"}]` 无错。
  - `test_schema.py::test_commit_kind_unknown_rejected`：`kind:"code"` → 错误里含 `commits[].kind`。
  - `test_tasks.py::test_commit_kind_cli`：`run_keel(root,"task","commit","T-1","app@abcdef1","--note","t","--kind","test")` rc 0，`task get` 输出含 `"kind": "test"`；不带 `--kind` 的条目不含 `kind` 键。
- [ ] **Step 2: 跑测试确认失败** — `cd skills/shared/scripts && python3 -m unittest tests.test_schema tests.test_tasks -v`，预期上述 4 条 FAIL。
- [ ] **Step 3: 实现**：`REVIEW_PROFILES` 加 `"move"`；新增 `COMMIT_KINDS`；commits 循环里 `kind` 存在且不在 `COMMIT_KINDS` → `_err("commits[].kind", f"{kind!r} 不是合法取值", "只能是 test 或省略")`；`:165` 说明行补「可选 kind=test 标测试提交」；`keel.py` 的 `commit` 子解析器加 `--kind`（`choices=["test"]`），`cmd_task` 传 `a.kind`。
- [ ] **Step 4: 跑测试确认通过** — 同 Step 2，全 PASS；再 `bash scripts/check-python.sh` 输出 `check-python OK`。
- [ ] **Step 5: 提交** — `feat(keel): 任务新增 move 档与测试提交标记`

### Task 2: `keel move-check`

**Files:**
- Create: `skills/shared/scripts/keellib/movecheck.py`
- Modify: `skills/shared/scripts/keel.py`（新子命令）
- Test: `skills/shared/scripts/tests/test_movecheck.py`

**Interfaces:**
- Produces:
  - `movecheck.Glue = NamedTuple("Glue", [("sign", str), ("path", str), ("text", str), ("logic", bool)])`，`sign` 为 `"+"` 或 `"-"`。
  - `movecheck.find_glue(diff_text: str) -> tuple[int, list[Glue]]`：返回（搬动行数, 胶水列表）。纯函数，输入为 `git diff --no-color -U0` 文本。
  - `movecheck.is_logic(line: str) -> bool`。
  - `movecheck.run(project_root: str, rev_range: str, paths: list[str]) -> tuple[int, list[Glue]]`：在 `project_root` 跑 git diff 后调 `find_glue`。
  - CLI：`keel move-check <rev-range> [paths...]`，退出码 0；git 失败 → `KeelError(..., 1)`。

`find_glue` 算法：逐行解析 diff，`+++`/`---` 头跳过，`+`/`-` 开头的行去掉符号后 `strip()`，空行忽略；删除行与新增行按 strip 后文本做多重集合抵消，抵消掉的计入搬动行数（按新增侧计），剩余的为胶水（保留 path 与原文本）。

`is_logic` 规则：先排除——strip 后以 `import `、`from `、`using `、`package `、`#include`、`require(`、`//`、`#`、`/*`、`*` 开头 → False。再判定命中任一即 True：关键字正则 `\b(if|else|elif|for|foreach|while|switch|case|return|throw|try|catch|except|finally)\b`；运算符 `==|!=|<=|>=|&&|\|\|`；数字字面量 `\b\d+(\.\d+)?\b`；字符串字面量 `"[^"]*"|'[^']*'`。

- [ ] **Step 1: 写失败测试**（`find_glue` 用手写 diff 文本，`run` 用 `helpers.make_project` 的临时 git 仓）
  - `test_pure_move_across_files_no_glue`：a.py 删 3 行、b.py 加同样 3 行 → `(3, [])`。
  - `test_indent_only_move_has_no_glue`：删 `    x = f(y)`，加 `        x = f(y)` → 无胶水。
  - `test_signature_glue_not_logic`：多出 `def helper(a, b):` 与调用 `helper(a, b)` → 2 条胶水，`logic` 均 False。
  - `test_condition_change_is_logic`：删 `if a > b:` 加 `if a >= b:` → 胶水 2 条，`+` 那条 `logic` True。
  - `test_literal_change_is_logic`：删 `x = 3` 加 `x = 4` → 有 `logic=True` 胶水。
  - `test_import_lines_not_logic`：加 `import { a } from './a'` → 胶水 1 条，`logic` False。
  - `test_cli_reports_and_exits_zero`：临时仓两次提交（第二次把函数搬到新文件并夹带 `return 1`），`run_keel(root,"move-check","HEAD~1..HEAD")` rc 0，stdout 含 `胶水` 与 `return 1`。
- [ ] **Step 2: 跑测试确认失败** — `python3 -m unittest tests.test_movecheck -v`，预期 ImportError/FAIL。
- [ ] **Step 3: 实现** `movecheck.py` 与 CLI。输出格式（stdout）：第一行 `搬动 {n} 行，胶水 {m} 行，其中疑似改逻辑 {k} 行`，之后每条胶水一行 `{path} {sign} {text}{'  ← 改逻辑' if logic else ''}`。
- [ ] **Step 4: 跑测试确认通过**，再 `bash scripts/check-python.sh` 全绿。
- [ ] **Step 5: 提交** — `feat(keel): 新增 move-check，判定逐字搬与胶水`

### Task 3: 完成门

**Files:**
- Create: `skills/shared/scripts/keellib/donegate.py`
- Modify: `skills/shared/scripts/keellib/tasks.py`（`set_fields` 调用完成门）
- Test: `skills/shared/scripts/tests/test_donegate.py`

**Interfaces:**
- Consumes: `schema.COMMIT_KINDS`（Task 1），`movecheck.run`（Task 2）。
- Produces: `donegate.DONE_STATES = ("已完成", "review_pending")`；`donegate.check(project: Project, task: dict[str, Any]) -> list[str]`，返回错误信息列表，空表示通过；内部 `_repo_dir(project, repo: str, sha: str) -> str | None`。

判定（spec §4.6），按仓分组 `commits`（`ref` 拆成 `repo@sha`，组内保持登记顺序）：
- 不触发：任务无 `kind=test` 提交，且不是「`review_profile=move` 且 `status=已完成`」→ 直接返回 `[]`，⛔ 不调 git。
- 解析：`_repo_dir` 依次试 `project.root`、`os.path.join(project.root, repo)`，取第一个 `git -C d cat-file -e {sha}^{commit}` 成功的目录；都不行 → 错误「{ref} 在本地解析不到：先把执行者分支合进来再登记」。
- 测试先于代码：组内每个代码提交（无 `kind`）都至少有一个 sha 不同于它的测试提交满足 `git merge-base --is-ancestor T C`；否则「代码提交 {C} 之前没有测试提交（是否压缩合并了？）」。
- 测试冻结：组内每个测试提交 T，`git diff-tree --no-commit-id --name-only -r T` 得到文件列表，`git diff --quiet T <组内最后一个代码提交> -- <files>` 非 0 → 「测试提交 {T} 之后改了测试：{文件}」。
- 注错记录：有测试提交时 `task["record"]` 非空且 `os.path.exists(os.path.join(project.root, record))`；否则「有测试提交但没有注错记录：先写 audit/<id>/ 并 --record」。
- 纯移动：`review_profile=move` 且 `status=已完成`：至少一个代码提交，否则「move 卡没有登记代码提交」；对每仓 `movecheck.run(dir, f"{首个代码提交}^..{最后代码提交}", [])`，有 `logic=True` 胶水 → 「搬移夹带改逻辑的行（列出前 5 条）：改 --profile guarded 走 review_pending」。

`tasks.set_fields`：在 `fn` 应用完字段后，若 `"status" in opts` 且 `t["status"] in donegate.DONE_STATES`，`errs = donegate.check(project, t)`，非空则 `raise KeelError("完成门未通过，未写入：\n" + "\n".join(errs), 1)`。

- [ ] **Step 1: 写失败测试**（每个用例在 `make_project` 的临时仓上造提交，`--root` 指向它；先 `task add` 建卡、`task commit` 登记，必要时 `--kind test`）
  - `test_gate_skipped_without_test_commits_or_move`：只登记代码提交的 fast 卡（sha 甚至是假的 `app@abcdef1`）→ `--status 已完成` rc 0。
  - `test_test_before_code_passes`：T 提交测试文件、C 提交实现，`--record` 指向已建的 `audit/T-1/`，→ `--status review_pending --batch b --due 2026-12-01 --pending-reason deferred-fast` rc 0。
  - `test_code_without_prior_test_rejected`：C 在前、T 在后 → rc 1，stderr 含「之前没有测试提交」，任务 JSON 字节不变。
  - `test_test_modified_after_freeze_rejected`：C 里也改了 T 的测试文件 → rc 1，stderr 含「之后改了测试」。
  - `test_squashed_rejected`：一个同时含测试和实现的提交，既登记为 `kind=test` 又登记为代码提交 → rc 1，stderr 含「之前没有测试提交」（「测试先于代码」要求测试提交与代码提交不是同一个 sha）。
  - `test_missing_record_rejected`：有测试提交无 `--record` → rc 1，stderr 含「注错记录」。
  - `test_unresolvable_sha_rejected`：登记 `app@` + 40 位不存在 sha 且 `kind=test` → rc 1，stderr 含「解析不到」。
  - `test_resolves_sha_in_subrepo_dir`：在 `<root>/svc` 建独立 git 仓做 T、C，登记为 `svc@…` → rc 0。
  - `test_move_with_logic_glue_rejected`：move 卡，C 搬函数并夹带 `if` 改动 → `--status 已完成` rc 1，stderr 含「改 --profile guarded」；随后 `--profile guarded --status review_pending ...` rc 0。
  - `test_move_pure_passes`：move 卡纯搬 → `--status 已完成` rc 0。
  - `test_gate_only_on_status_change`：已完成且有测试提交的卡，事后删掉 record 目录，再 `task set T-1 --title x` → rc 0（不触发）。
- [ ] **Step 2: 跑测试确认失败** — `python3 -m unittest tests.test_donegate -v`。
- [ ] **Step 3: 实现** `donegate.py` 与 `set_fields` 接入；git 调用用 `subprocess.run([...], capture_output=True, text=True)`，与 `store` 现有 git 调用风格一致。
- [ ] **Step 4: 跑测试确认通过**，再跑全量 `bash scripts/check-python.sh`，确认既有 133 个测试仍过。
- [ ] **Step 5: 提交** — `feat(keel): 完成门——测试先于代码、测试冻结、纯移动与注错记录由工具检查`

### Task 4: `task get --diff-range`

**Files:**
- Modify: `skills/shared/scripts/keellib/tasks.py`、`skills/shared/scripts/keel.py`
- Test: `skills/shared/scripts/tests/test_tasks.py`

**Interfaces:**
- Produces: `tasks.diff_ranges(project, tid) -> list[str]`，每仓一行 `{repo} {首个登记sha}^..{最后登记sha}`（含测试提交，按登记顺序），无登记提交 → `KeelError("任务 {tid} 没有登记提交", 1)`。CLI：`keel task get <id> --diff-range` 打印这些行。

- [ ] **Step 1: 写失败测试** `test_diff_range_spans_test_and_code`：登记 `app@aaaaaaa`（kind test）、`app@bbbbbbb`、`lib@ccccccc` → 输出两行 `app aaaaaaa^..bbbbbbb`、`lib ccccccc^..ccccccc`；`test_diff_range_no_commits` → rc 1。
- [ ] **Step 2: 跑测试确认失败。**
- [ ] **Step 3: 实现**（纯字符串，不调 git；根提交无父的情况由 drain 侧 Recovery 处理，不在此特判）。
- [ ] **Step 4: 跑测试确认通过**，`check-python.sh` 全绿。
- [ ] **Step 5: 提交** — `feat(keel): task get --diff-range 给出审查用改动范围`

### Task 5: 规则真源与审查档位文档

**Files:**
- Modify: `skills/shared/constraints.md`（`:151` 枚举、`:506-511` 档位表、`:552` commits 语义）
- Modify: `skills/dev-workflow/references/verification-flow.md`（move 档与胶水规则；drain diff 源 `:367-368`）
- Modify: `skills/dev-workflow/references/execution-flow.md`（S5 红验 `:136` 例外）
- Modify: `skills/refactor/references/rewrite-flow.md:59-62`（改为引用 execution-flow 例外）
- Modify: `skills/dev-tasks/SKILL.md`（`:142` 风险分类器加 move 提议）
- Modify: `skills/verify/SKILL.md`（`--review-drain` 送审范围改读 `task get <id> --diff-range`）

- [ ] **Step 1: constraints.md**
  - `:151` 与 `:506` 标题「三档」改为四档，枚举加 `move`。
  - 档位表加一行：`move | 测试先于代码（复用或本卡补表征测试） | ✓ | — | 不做；Commit 1 后直接已完成，由完成门检查纯移动`；表下加一句「move 判定不过 → 升 guarded」。
  - 新增小节「完成门（工具检查）」：照 spec §4.6 表格四项 + 「不压缩合并」「没有测试提交的卡跳过」「sha 解析不到」「不提供跳过开关」四句。这是完成门的唯一文字真源。
  - `:552` `commits` 行：语义改为「测试提交加 `--kind test`；完成门据此检查顺序与冻结（见上节）」，删去「⛔ 不作门控依据」。
  - 质量地板第 2 条「测试写成红验通过即冻结」补「表征测试与 move 卡为绿验通过即冻结，见 execution-flow S5 例外」。
- [ ] **Step 2: execution-flow.md** `:136` 下加例外行：`move` 档或表征测试（期望值取自基线）→ 测试提交上应全绿，「意外通过」不适用。
- [ ] **Step 3: rewrite-flow.md** 表征测试段保留「重写前先补」，红绿判定改为一行指针到 execution-flow S5 例外。
- [ ] **Step 4: verification-flow.md** 新增「move 档」小节：胶水允许类型与改逻辑类型（spec §4.3 判定规则）、执行者先自判、派单方按批过目、事后否决另开修复卡（`--derived-from`）；drain diff 源改为 `.keel/bin/keel task get <id> --diff-range` 的范围。
- [ ] **Step 5: dev-tasks/SKILL.md** 风险分类器加：任务为拆分/搬移且声明行为不变 → 提议 `move`。
- [ ] **Step 6: verify/SKILL.md** drain 段改用 `--diff-range`。
- [ ] **Step 7: 校验** — `git diff --check` 无输出；`grep -rn "三档" skills/` 只剩无关处；`grep -rn "不作门控依据" skills/` 无结果。
- [ ] **Step 8: 提交** — `docs(keel): move 档、完成门与表征测试先绿写入规则真源`

### Task 6: 执行者模式与按批提交台账

**Files:**
- Create: `skills/dev-workflow/references/executor-mode.md`
- Modify: `skills/dev-workflow/SKILL.md`（编排规范 `:170-191`、`:284`、`:335`、任务台账表 `:390`）
- Modify: `skills/dev-workflow/references/task-orchestration.md`（`:300`、`:319`、`:433`、续做信号表 `:212`）
- Modify: `skills/dev-workflow/references/auto-mode.md`（`:125`、`:189`）
- Modify: `docs/workflows.md`（PM 派单段）
- Modify: `docs/superpowers/specs/2026-11-20-keel-parallel-agents-design.md`（§4.1 加引用）

- [ ] **Step 1: executor-mode.md**：照 spec §4.1、§4.1.1 写成执行步骤：判定依据与反例（用户主会话说「做 T-xxx」不是执行者模式）、7 步、档位/步骤表、子代理只用于大读、阻塞等待不轮询、交卡消息字段清单、不写台账与 `docs/devdocs/`、断点续做两条。⛔ 不复述完成门细则，指向 constraints.md「完成门」。
- [ ] **Step 2: SKILL.md**：编排规范节首加一行「被另一个会话派来做指定卡时按 [executor-mode.md](references/executor-mode.md)，不派子代理」；`:284`、`:335` 的逐任务 Commit 2 改为「Commit 2 可按批一次，见 task-orchestration」；任务台账表加一行「测试提交落盘后：`task commit <id> <repo>@<sha> --kind test --note …`」。确认 `wc -l` ≤ 500。
- [ ] **Step 3: task-orchestration.md**：主循环第 9 步改为「批末一次 /sync + Commit 2」；洁净校验改为「每任务 Commit 1 后 `docs/devdocs/` 以外洁净；批末 Commit 2 后全洁净」；续做信号表加「有测试提交无代码提交 → 从写实现续做」「代码已提交、批末 Commit 2 未做 → 从批末同步续做」。
- [ ] **Step 4: auto-mode.md** `:125`、`:189` 同步洁净校验时点（指向 task-orchestration，不复述）。
- [ ] **Step 5: docs/workflows.md** PM 段：派单消息写明执行者身份；收卡后登记两次提交（测试提交带标记）、落盘注错记录、合并后再登记、不压缩合并。
- [ ] **Step 6: 并行设计稿** §4.1 末加一句：「执行者身份与执行方式见 [精简执行路径设计稿](2026-11-22-keel-executor-lean-path-design.md) §4.1；`assignee` 即执行者名。」
- [ ] **Step 7: 校验** — `git diff --check`；`wc -l skills/dev-workflow/SKILL.md` ≤ 500；`grep -n "每任务 Commit 2" -r skills/` 只剩已改写处；用户面零子指令自查：`grep -nE "/[a-z-]+ --?[a-z]" skills/dev-workflow/references/executor-mode.md` 无用户入口形式。
- [ ] **Step 8: 提交** — `docs(dev-workflow): 执行者模式与按批提交台账`

### Task 7: 走查、版本与发布准备

**Files:**
- Modify: `plugin.json`、`.claude-plugin/plugin.json`（3.1.0）

- [ ] **Step 1: 代表性走查（只读推演，写在提交说明里）**：按 executor-mode.md 走一张行为卡、一张 move 卡；按主会话批量走 3 张卡一批。逐条对照 spec §5 验收，记录每条落在哪个文件哪一行。
- [ ] **Step 2: 端到端 CLI 演练**：临时仓里 `task add` → 测试提交 → `task commit --kind test` → 代码提交 → `task commit` → `--record` → `task set --status review_pending …` rc 0；再造一张 move 卡夹带 `if`，`--status 已完成` rc 1，改 guarded 后 rc 0；`task get --diff-range` 输出正确。
- [ ] **Step 3: 版本** 两个 manifest 改 `3.1.0`。
- [ ] **Step 4: 全量校验** — `bash scripts/check-python.sh` 输出 `check-python OK`；`git diff --check` 无输出。
- [ ] **Step 5: 提交** — `chore(keel): 版本升到 3.1.0`（推送等用户确认）。
