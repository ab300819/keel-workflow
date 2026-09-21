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
