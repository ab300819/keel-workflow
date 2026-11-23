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
| `<any>` | 除 `/` 外任意字符（宽松兜底，用于时间戳等不受上面几种约束的片段）|
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
| `04-dev-tasks-<slug>.md` | dev-tasks | `04-dev-tasks.md` |
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
| `audit/<slug>-external-review-realigned-<any>.yaml` | dev-workflow | — |
| `audit/**/<slug>.txt` | dev-workflow | — |
| `.health-report.md` | pipeline | — |
| `.realign-plan.md` | pipeline（已废弃：产出它的 layout scope 已随 layout.v2 删除，存量文件可删）| — |
| `.batch-checkpoint.json` | dev-workflow | — |
| `.runlog.yaml` | 编排层（已废弃：runlog 规则 2026-11 按自带死期删除，存量文件可删）| — |
| `state/tasks/T-<N>.json` | keel | — |
| `state/backlog/<slug>.json` | keel | — |
| `state/meta.json` | keel | — |
| `state/gates.json` | keel | — |
| `audit/T-<N>/ledger-record.md` | keel | — |
| `audit/migration-v3.md` | keel | — |
| `audit/migration-v3-backlog.md` | keel | — |

## 双形态存储：集中文件 vs 资源目录

ADR / INS / BUG / Backlog 四类资源**两套形态都合法**，上表各登记两行。

| 资源 | 集中形态 | 资源目录形态 |
|---|---|---|
| ADR | 设计文档的 ADR 节 | `adr/ADR-<N>.md` + `adr/index.md` |
| INS | `05-insights.md` | `insights/INS-<N>.md` + 索引 |
| BUG | `05-bugfix-log.md` | `bugs/BUG-<N>.md` + 索引 |
| Backlog | `backlog.md` | `backlog/<slug>.md` + 索引 |

⚠️ **资源目录形态的声明来源目前只有 `skills/agent-memory/templates/devdocs-state-template.md`**，
四个生产方 skill（system-design / insights / bugfix / backlog）的正文**未声明**该形态。
这是已知的规格缺口，由用户裁定判为合法形态，⛔ 本清单不代表生产方已支持它。

**判据是规模，不是对错。** 实测：一个 360 md 的项目有 `bugs/` 122 文件、`insights/` 33、
`adr/` 30，集中文件全缩成 1~2 KB 指针并自留说明「本文件已采用一文件一资源结构」；
另一个 22 md 的项目，`05-bugfix-log.md` 才 2.3 KB，完全够用。

集中文件超 `layout/size-cap` 阈值 → 报「建议转资源目录」。
⛔ **转换不自动执行**——它是内容迁移，需用户触发。

## 三类阈值的分工（⛔ 不是同一件事）

| 阈值 | 归属 | 作用 |
|---|---|---|
| 各 skill 的 300 行拆分规则 | requirements / system-design / test-cases / dev-tasks | 生成时的**拆分建议** |
| `sync --archive` 的 400/500/400/300 行 + 数量 + 状态 | `sync/references/archive.md` | **归档触发器**（行数或数量任一超过即触发检查；状态条件决定哪些条目可归档）|
| `layout/size-cap` 的 96 KiB | `pipeline/scripts/health-lint.py` 的 `SIZE_CAP_BYTES`（:542） | **体积警报**（纯尺寸，无语义条件）|

`/sync --archive` 已于 2026-09-23 首次真实执行验证（一个实战项目，净减 767 行），
⛔ 不再是未验证路径。首跑暴露的 8 条规格缺口（拆分布局、任务多对多挂 F、无完成日期等）
已于 2026-11-17 补进 `sync/references/archive.md`，但补后的规格**尚未再次真跑**，
且需求 / 设计 / 测试三类的归档路径从未用真实数据验证 ⇒ 仍 ⛔ 不是按钮式自动出口。
详见 [docs/audits/2026-09-23-sync-archive-first-run.md](../../docs/audits/2026-09-23-sync-archive-first-run.md)。
