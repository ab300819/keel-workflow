# SSOT Lint Implementation（#3 单一事实源检查实施规范）

> 把 [folder-organization-implementation.md § SSOT 强约束清单](folder-organization-implementation.md#ssot-强约束清单落地到-3-ssot-lint) 的 12 条 `rule_id` 落地为可执行的 lint 系统：CLI 入口、触发时机、输出格式、忽略机制、baseline 管理、与 ms-verify 集成。
>
> 与 [folder-organization-implementation.md](folder-organization-implementation.md) 同级：前者治理目录组织 + 内容契约 + lint rule **声明**；本文件治理 lint rule **执行**。

## ⚠️ 执行接口当前状态

本文件描述的 `/ms-verify --ssot-lint` / `--ssot-lint-fix` / baseline 管理命令均依赖 [FUTURE] 接口，详见 [docs-layout-migration.md § 执行接口落地状态（FUTURE）](docs-layout-migration.md#-执行接口落地状态future)。

当前阶段（#3 spec 起草）**只产出规范**，runtime 实现由后续阶段落地。`ms-verify` 现有 `--docs-drift` / `--layout-drift` 子命令保持不变；`--ssot-lint` 作为新增子命令，未实现前不可调用。

## 定位

| 治理对象 | 文件 |
|---------|------|
| 12 条 lint rule 声明（rule_id / 检测对象 / 算法 / 触发条件 / 严重度）| [folder-organization-implementation.md § SSOT 强约束清单](folder-organization-implementation.md#ssot-强约束清单落地到-3-ssot-lint) |
| baseline 机制声明 | [folder-organization-implementation.md § baseline 机制](folder-organization-implementation.md#baseline-机制用于-legacy-annotation-additions) |
| **本文件**：lint 执行机制 + CLI + 输出 + 忽略 + ms-verify 集成 | ssot-lint-implementation.md |
| 编号体系前置依赖 | [id-scheme-implementation.md](id-scheme-implementation.md) |

## CLI 入口

### 命令形态

`/ms-verify --ssot-lint` 接入 `ms-verify` 既有子命令体系，遵守 `ms-verify` 现有的 args 约定。

| 命令 | 行为 |
|------|------|
| `/ms-verify --ssot-lint` | 只读全量扫描 12 条 rule，输出报告（不修改文件）|
| `/ms-verify --ssot-lint --rule <rule_id>` | 只跑指定 rule（如 `--rule ssot/owner-uniqueness`）|
| `/ms-verify --ssot-lint --severity P0` | 只扫严重度 P0 的 rule（4 条）|
| `/ms-verify --ssot-lint --changed-only` | 只扫 git diff HEAD 的变更文件 |
| `/ms-verify --ssot-lint --baseline <commit>` | 显式指定 baseline commit（覆盖 `_archived/layout-v2-baseline-*.yml`）|
| `/ms-verify --ssot-lint --fix` [FUTURE] | 尝试自动修复（4 条全量支持 + 1 条部分支持，见 § 自动修复支持矩阵）|
| `/ms-verify --ssot-lint --baseline-init` | **内部命令**，仅由 `ms-pipeline init`（layout.v2 初始化）与 `ms-pipeline realign --docs-layout`（升级迁移）调用：创建或更新 baseline 文件。用户直调报 `ssot/baseline-init-misuse`。|

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 无违规 |
| 1 | 仅 P1 违规（warn） |
| 2 | 有 P0 违规（block） |
| 3 | lint 自身运行错误（如 baseline 文件缺失、git 不可用）|

CI 集成默认按退出码 0 / 1 / 2 区分通过 / 警告 / 失败。

## 触发时机

### 自动触发

| 时机 | 行为 | 阻断/告警 |
|------|------|----------|
| `/ms-pipeline init` 直接以 layout.v2 初始化 | 内部调用 `--baseline-init` 创建初始 baseline + 全量 lint | 仅告警（init 后允许过渡态）|
| `/ms-pipeline realign --docs-layout` 迁移完成 | 内部调用 `--baseline-init` 更新 baseline + 全量 lint | P0 违规阻断（迁移视为完成态）|
| `/ms-dev-workflow` Commit 2（doc commit）前 | `--changed-only` 增量 lint | P0 阻断 commit；P1 告警继续 |
| `/ms-sync --archive` 后 | 全量 lint | P0 告警（archive 触发被动检测）|
| `/ms-verify` 任意子命令调用时 | 顺带跑 `--ssot-lint --changed-only` | 报告中独立小节，不影响主子命令退出码 |

> ⛔ **`--baseline-init` 调用边界**：仅由 `ms-pipeline init` 与 `ms-pipeline realign --docs-layout` 内部调用，**禁止**用户直接调用。若用户绕过 pipeline 直接调 `--baseline-init`，lint 报 `ssot/baseline-init-misuse`（恢复方式：删除 baseline 文件后通过 realign 重建）。

### 手动触发

用户主动调用 `/ms-verify --ssot-lint` 任意 flag 组合。

### CI 集成（[FUTURE]）

`/ms-verify` 是 ms-verify skill 的 slash 命令，CI 环境需通过 CLI wrapper（如 `claude --skill ms-verify --args "--ssot-lint --changed-only"` 或项目自定义 wrapper）调用。推荐 GitHub Actions 示例：

```yaml
- name: SSOT lint
  id: ssot
  run: |
    set +e
    npx claude-skill-runner ms-verify --ssot-lint --changed-only --format json > lint.json
    code=$?
    set -e
    echo "exit_code=$code" >> "$GITHUB_OUTPUT"
    case "$code" in
      0) echo "✅ PASS" ;;
      1) echo "⚠️ WARN (P1 only)" ;;       # warn but pass：不 exit 1
      2) echo "❌ FAIL (P0 violations)" && exit 1 ;;
      3) echo "❌ LINT ERROR" && exit 1 ;;
      *) echo "❌ UNKNOWN exit $code" && exit 1 ;;
    esac

- name: Upload report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: ssot-lint-report
    path: lint.json
```

**关键设计**：
- 用本地 shell 变量 `code` 在同 step 内做分支（不能用 `${{ steps.ssot.outputs.exit_code }}` —— GitHub Actions step output 仅下游 step 可读）
- 退出码 1 (P1 only) 通过 case 拦截，不让 shell 误判 fail（与 § 退出码 "warn but pass" 一致）
- 退出码 2/3 显式 `exit 1` 让 CI fail；其他未知码也 fail-fast
- `--format json` 输出供后续工具消费 + artifact 留痕
- `set +e` / `set -e` 包围保证 exit code 可捕获

## 输出格式

### 标准报告（Markdown）

```markdown
# SSOT Lint Report

- **Scope**: full | changed-only | rule:<id> | severity:<level>
- **Baseline**: <commit-hash> (from _archived/layout-v2-baseline-<commit>.yml)
- **Total findings**: P0=<n>, P1=<n>
- **Verdict**: PASS / WARN / FAIL

## P0 违规（block）

### ssot/owner-uniqueness (P0)

- **File**: docs/devdocs/requirements/FEAT-001.md:1
- **Conflict**: docs/devdocs/_archived/01-requirements.md:42 也存在 H1 `# FEAT-001`
- **Fix**: 确认 owner 后删除非 owner 副本（或移入 `_archived/` 排除范围）

### ssot/aliases-exists (P0)

- **File**: docs/devdocs/aliases.yml
- **Issue**: 文件缺失
- **Fix**: 运行 `/ms-pipeline realign --docs-layout` 重新初始化

## P1 违规（warn）

### ssot/file-size-cap (P1)

- **File**: docs/devdocs/_archived/04-dev-tasks.md
- **Issue**: 行数 3247 > 3000（但属 `_archived/`，已自动排除——本条为伪命中，已忽略）

### ssot/legacy-annotation-additions (P1)

- **File**: src/services/user.ts:42
- **Issue**: layout.v2 baseline (commit abc1234) 后新增 `@satisfies AC-001` 注释
- **Fix**: 改写为 `docs/devdocs/traceability.yml` 条目，删除代码注释
```

### JSON 输出（`--format json`）

```json
{
  "schema_version": 1,
  "tool": "ms-verify --ssot-lint",
  "tool_version": "1.0.0",
  "timestamp": "2026-05-18T10:00:00+08:00",
  "scope": "full | changed-only | rule:<id> | severity:<level>",
  "baseline": {
    "commit": "abc1234",
    "file": "_archived/layout-v2-baseline-abc1234.yml",
    "created_at": "2026-05-15T08:00:00+08:00"
  },
  "exit_code": 2,
  "verdict": "PASS | WARN | FAIL",
  "totals": {
    "p0": 1,
    "p1": 2,
    "total_findings": 3,
    "rules_evaluated": 12,
    "files_scanned": 87
  },
  "ignored": {
    "by_file": 3,
    "by_line": 5,
    "by_severity_skip": 0,
    "files": [
      ".ssot-lintignore matched: api-docs/index.md (rule: ssot/file-size-cap)"
    ]
  },
  "meta_warnings": [
    "行级 disable 忽略了 P0 rule ssot/no-restatement @ docs/devdocs/requirements/FEAT-001.md:42"
  ],
  "findings": [
    {
      "rule_id": "ssot/owner-uniqueness",
      "severity": "P0",
      "file": "docs/devdocs/requirements/FEAT-001.md",
      "line": 1,
      "column": 1,
      "message": "H1 owner FEAT-001 与另一文件冲突",
      "context": {
        "conflict_with": "docs/devdocs/_archived/01-requirements.md:42"
      },
      "fix_suggestion": "确认 owner 后删除非 owner 副本",
      "auto_fixable": false,
      "doc_url": "https://.../ssot-lint-implementation.md#ssotowner-uniqueness"
    }
  ]
}
```

**字段稳定性承诺**：
- `schema_version: 1` 不变期间，已声明字段类型 + 语义不变；新增字段允许（向后兼容）
- 字段删除或类型变更必须 bump `schema_version` 到 2 并同步更新本文件
- JSON 输出供 CI / `ms-verify` 编排层 / 外部工具消费

## 忽略机制

### 文件级忽略

`docs/devdocs/.ssot-lintignore`（gitignore 语法）：

```
# 排除 _archived/ 全部（默认行为，可显式覆盖）
_archived/**

# 排除特定 legacy 模板（迁移期临时使用）
templates/v1-template.md

# 排除外部生成的索引（如 typedoc 输出）
api-docs/**
```

⚠️ `.ssot-lintignore` 不能覆盖 P0 rule（`ssot/aliases-exists` 等必须存在性检查）；仅对内容/结构类规则生效。

### 行级忽略

```markdown
# FEAT-001: 登录功能 <!-- ssot-lint-disable-next-line ssot/no-restatement -->

详细描述与 owner 一致但本行需保留（如 navigation 索引）...
<!-- ssot-lint-disable ssot/no-restatement -->
段落 1
段落 2
<!-- ssot-lint-enable ssot/no-restatement -->
```

支持三种指令：
- `<!-- ssot-lint-disable-next-line <rule_id> -->` 仅下一行
- `<!-- ssot-lint-disable <rule_id> -->` 起点
- `<!-- ssot-lint-enable <rule_id> -->` 终点

⚠️ 行级忽略**必须**指定 rule_id（不允许 `ssot-lint-disable` 不带参数）；忽略 P0 规则会被 lint 报 meta-warning（"P0 不应被忽略"）。

### 全局忽略

不支持。任何 P0 必须在 lint 通过或被显式 fix，不允许全局静默。

## baseline 管理

### baseline 文件

位置：`docs/devdocs/_archived/layout-v2-baseline-<commit-short>.yml`

```yaml
---
version: baseline.v1
schema_version: 1                                   # 防止 schema drift
managed_by: ms-pipeline                             # 仅此 owner 可写
generated_from: realign-docs-layout | init-v2       # 创建来源标识
active: true                                        # 当前活跃 baseline 标记（多 baseline 共存时只有 1 个 true）
created_at: 2026-05-18T10:00:00+08:00
created_by: /ms-pipeline realign --docs-layout
target_layout: layout.v2
target_id_scheme: id.v2
target_traceability: trace.v1
git_commit: abc1234567890def
git_branch: main
content_checksum: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                                                    # 上述全部字段（除 content_checksum 本身）的序列化 sha256
notes: |
  layout.v2 升级时刻的代码快照。
  ssot/legacy-annotation-additions 以此 commit 为对比基线。
---

# 历史 baseline（仅记录，不读取）
- baseline.v1 @ abc1234 (2026-05-18) — 首次 layout.v2 升级
```

### baseline 防篡改（`ssot/baseline-tampered`）

| 检测项 | 算法 | 触发 |
|--------|------|------|
| checksum 不匹配 | 计算文件除 `content_checksum` 字段外的全部 YAML 序列化的 sha256，与文件中存储值对比 | 任一字段被手编 |
| managed_by 不匹配 | 字段值不在 `[ms-pipeline]` 白名单 | 误删或被外部工具改写 |
| active 字段多 baseline 同时为 true | 列出全部 baseline，统计 `active: true` 数量 > 1 | 手编或迁移异常 |
| schema_version 不匹配 | 与本文件声明的 `schema_version: 1` 对比 | 版本漂移 |
| git_commit 不可达 | `git cat-file -e <commit>` 检查 | commit 已被 force-push 删除 |

**恢复方式**：
- checksum/managed_by/schema_version 不匹配 → 删除 baseline 文件 + 重跑 `/ms-pipeline realign --docs-layout` 重建
- active 多 baseline 冲突 → AskUserQuestion 让用户选保留哪一个 active，其余降为历史
- git_commit 不可达 → 找一个最接近的本地 commit 作为新 baseline，重跑 realign

⛔ **禁止手编 baseline 文件**：任何修改必须走 `--baseline-init` / `--baseline-refresh` 命令；checksum 自动维护。手编后 lint 报 `ssot/baseline-tampered (P0)`，阻断所有 lint 操作直到恢复。

### baseline 生命周期

| 操作 | 命令 | 时机 |
|------|------|------|
| 创建 | `/ms-verify --ssot-lint --baseline-init` | 由 `ms-pipeline init`（layout.v2 初始化）或 `ms-pipeline realign --docs-layout`（升级迁移）内部调用；用户禁止直调 |
| 查询 | `/ms-verify --ssot-lint --baseline-show` [FUTURE] | 显示当前活跃 baseline 内容 |
| 更新 | `/ms-verify --ssot-lint --baseline-refresh <commit>` [FUTURE] | 重置 baseline 到新 commit（如 batch legacy cleanup 后）|
| 列出 | `/ms-verify --ssot-lint --baseline-list` [FUTURE] | 列出所有历史 baseline |

⛔ **禁止手编 baseline 文件**：任何修改必须走上述命令，否则 lint 拒绝读取并报 `ssot/baseline-tampered`。

### 多 baseline 共存

正常情况下只有 1 个活跃 baseline。多 baseline 共存场景：

- batch cleanup 后产生新 baseline，旧 baseline 自动 archive 到 `_archived/baselines/`
- 多分支并行开发，每分支可有独立 baseline（lint 读 `git rev-parse --abbrev-ref HEAD` 对应文件）

跨分支 merge 时，baseline 冲突由 `realign --docs-layout` 自动 reconcile（取较旧 commit 作为合并基线）。

## 自动修复支持矩阵

`--fix` [FUTURE] 仅对幂等 + 低风险的 rule 启用。支持矩阵：**4 条全量支持 (✅) + 1 条部分支持 (⚠️) + 7 条不支持 (❌)** = 12 条 rule 全覆盖。

| rule_id | auto-fix 支持 | 修复动作 |
|---------|-------------|---------|
| `ssot/index-summary-length` | ✅ 支持 | 截断 summary 到 117 字符 + 添加 `…`（保留 owner 文件原文） |
| `ssot/no-drafts-dir` | ✅ 支持（仅检测后提示，需用户确认归类）| AskUserQuestion 让用户选择移入 `<type>/<ID>.md` 或删除 |
| `ssot/aliases-exists` | ✅ 支持 | 自动创建空 aliases.yml + frontmatter |
| `ssot/traceability-exists` | ✅ 支持 | 自动创建空 traceability.yml + frontmatter |
| `ssot/agents-frontmatter` | ⚠️ 部分 | 缺失字段填默认值（id_scheme=id.v1 等），需用户确认 |
| `ssot/owner-uniqueness` | ❌ 不支持 | 涉及内容仲裁，必须人工 |
| `ssot/no-restatement` | ❌ 不支持 | 涉及内容仲裁 |
| `ssot/index-body-clean` | ❌ 不支持 | 涉及内容仲裁 |
| `ssot/current-md-size` | ❌ 不支持 | 涉及拆分决策（拆哪个模块）|
| `ssot/file-size-cap` | ❌ 不支持 | 同上 |
| `ssot/modules-size-cap` | ❌ 不支持 | 同上 |
| `ssot/legacy-annotation-additions` | ❌ 不支持 | 涉及 traceability.yml 写入决策 |

⛔ **`--fix` 必须配合 dry-run**：默认 `--fix --dry-run` 列出将修改的文件；`--fix --apply` 才实际执行。

## 与 ms-verify 集成

### ms-verify 主入口扩展

`ms-verify` SKILL.md 在 `--ssot-lint` 下作为新增子命令文档化：

```markdown
## --ssot-lint（layout.v2 [FUTURE]）

只读检测 SSOT 强约束违规。详见 [pipeline/references/layout/ssot-lint-implementation.md](../pipeline/references/layout/ssot-lint-implementation.md)。

| flag | 行为 |
|------|------|
| `--rule <id>` | 只跑指定 rule |
| `--severity P0` | 只扫指定严重度 |
| `--changed-only` | 仅扫 git diff |
| `--fix --dry-run / --apply` [FUTURE] | 自动修复（4 条全量 + 1 条部分支持）|

⚠️ 仅在 `AGENTS.md devdocs.docs_layout_version: layout.v2` 时可用；layout.v1 项目报 `not_applicable`。
```

### yaml-summary 集成

`ms-verify` 调用 `--ssot-lint` 后，子 Agent 摘要（yaml-summary-v1）新增字段：

```yaml
skill: ms-verify
status: success | failed
summary:
  headline: "SSOT lint: 0 P0, 2 P1"
  details:
    ssot_lint:
      verdict: PASS | WARN | FAIL
      p0_count: 0
      p1_count: 2
      baseline: abc1234
      findings_by_rule:
        ssot/file-size-cap: 1
        ssot/legacy-annotation-additions: 1
```

### 阻断逻辑

| 触发场景 | P0 行为 | P1 行为 |
|----------|--------|--------|
| `ms-dev-workflow` Commit 2 前 | ⛔ 阻断 commit；要求修复或显式 `--ssot-lint-skip-reason="<原因>"` | ⚠️ 告警继续，写入 commit 尾注 `SSOT-Lint-Warnings: N` |
| `/ms-pipeline realign --docs-layout` 后 | ⛔ 阻断 realign 完成；要求修复 | ⚠️ 告警，realign 标记为 `partial_success` |
| `/ms-verify --all` | 报告中独立小节，不阻断 verify 主流程 | 同上 |
| 手动 `/ms-verify --ssot-lint` | 退出码 2 | 退出码 1 |

### `--ssot-lint-skip-reason` 参数规范

对齐 `dev-workflow` 既有 `--skip-review-reason` / `--skip-external-review-reason` 模式：

| 约束 | 行为 |
|------|------|
| 非空 | 必填；空字符串视为非法参数（lint 报 `ssot/skip-reason-invalid`）|
| 字数 | 10 ≤ len ≤ 200（过短无信息量，过长应写到独立 ISSUE 文件）|
| 写入位置 | Commit 2 message 尾注：`SSOT-Lint-Skip-Reason: <原因>` |
| 状态登记 | 触发跳过的 commit 标记 `pending_ssot_recheck: true` 到 `traceability.yml` [FUTURE]，待用户后续 `/ms-verify --ssot-lint --recheck-pending` 处理 |
| 头部 commit 限制 | `--headless` 模式禁用此 flag（仅交互模式允许）|

**与 `--skip-review-reason` / `--skip-external-review-reason` 的差异**：
- `--skip-review-reason` 仅 🔴 任务可用；`--skip-external-review-reason` 仅 🔴 + 交互模式可用；`--ssot-lint-skip-reason` 任何任务层级都可用，但**与 `--skip-external-review-reason` 一致：headless 模式禁用**（见上表"头部 commit 限制"），防 CI 跳过质量门
- `--skip-review-reason` 标 `INT_PENDING`（dev-workflow Step 1.5 [D1] 拦截至补跑）；`--skip-external-review-reason` 标 `EXT_PENDING`（[D2] 拦截至补跑）；`--ssot-lint-skip-reason` 标 `pending_ssot_recheck`（通过 `traceability.yml` 跟踪，由 `/ms-verify --ssot-lint --recheck-pending` 后续处理）

## 性能与边界

### 性能预期

| Repo 规模 | 全量 lint 时间预期 | changed-only lint |
|----------|-----------------|-------------------|
| < 100 编号文件 | < 2s | < 500ms |
| 100-500 编号文件 | < 10s | < 1s |
| 500-2000 编号文件 | < 60s | < 2s |
| > 2000 编号文件 | 推荐拆分项目；--changed-only 必用 |

`ssot/no-restatement`（n-gram 相似度）是 O(N²) 算法，超 500 文件时建议加 `--skip-rule ssot/no-restatement` 跑全量，单独按需触发。

### 不支持的边界

- ❌ 二进制文件（图片、PDF 等）— lint 跳过
- ❌ 代码语言不在白名单（.ts/.tsx/.js/.jsx/.py/.go/.java）— `legacy-annotation-additions` 不扫
- ❌ Symlinks 跨目录 — 按目标文件解析；循环 symlink 报 `ssot/lint-error`
- ❌ 非 UTF-8 编码 — 报 `ssot/lint-error` 跳过该文件

## frontmatter 升级规则（条件性）

`ms-verify` `writes_layout` 保持 `layout.v1`（当前 transitional state）。**升级到 `layout.v2` + 启用 `--ssot-lint` 的触发条件（必须 1+2+3+4 全满足）**：

1. SKILL.md 正文已加入 `--ssot-lint` 子命令双轨说明 ⏳
2. 本文件 + folder-organization-implementation.md 已 FINAL-GO ✅
3. Runtime lint 引擎 [FUTURE] 已实现 ⏳
4. 至少 1 个 v2 项目已成功跑过 `--ssot-lint` ⏳

> ⛔ **禁止仅凭 1+2 升级**：满足 1+2 仅代表 spec 准备完成，runtime 行为仍不可用。提前升级会触发"声明先行陷阱"。必须 1+2+3+4 全满足才可改 `writes_layout: layout.v2`。
>
> 恢复方式：发现提前升级时，立即回退到 `layout.v1` 并补齐 3/4 条件。

## 历史项目兼容（mic-en 等）

- **mic-en 等 layout.v1 项目**：`--ssot-lint` 报 `not_applicable`，不执行
- 任何时候用户主动调用 `/ms-pipeline realign --docs-layout` [FUTURE] 升级到 layout.v2 后，`--ssot-lint` 自动可用
- 本阶段（#3）**不执行** mic-en 迁移或 lint；仅完成 spec 改造

## 与其他阶段的接口

| 阶段 | 接口点 |
|------|-------|
| #1 编号体系 | 已消费 FEAT/STORY/AC/TASK/ISSUE/ADR/PATTERN/NOTE 全部 8 类前缀 + alias 解析（`ssot/owner-uniqueness` 必须识别 alias.yml 中的旧编号）|
| #2 文件夹组织 | 已消费 12 条 lint rule 声明 + baseline 机制；本文件**扩展**为执行规范，不重复 rule 定义 |
| #4 代码解耦 | `ssot/legacy-annotation-additions` 是 #4 的强制工具（强制不新增 @satisfies）；#4 阶段同时负责设计 `traceability.yml` 写入 API，被 `--fix` 调用 [FUTURE] |
| #5 迭代蒸馏 | `ssot/current-md-size` / `ssot/modules-size-cap` / `ssot/file-size-cap` 是蒸馏触发器；#5 阶段负责定义蒸馏后的合并/拆分动作 |

## 引用关系

| 引用本文件的位置 | 引用目的 |
|------------|---------|
| `skills/verify/SKILL.md` § `--ssot-lint` | 子命令文档化（待 #3 落地后加）|
| `skills/pipeline/SKILL.md` § realign | `realign --docs-layout` 后调用 lint 验证 |
| `skills/dev-workflow/SKILL.md` § Commit 2 | Commit 2 前 `--changed-only` lint |
| `folder-organization-implementation.md` § SSOT 强约束 | 本文件执行声明的 rule |

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-18 | 初始版本（#3 SSOT lint 实施规范）|
