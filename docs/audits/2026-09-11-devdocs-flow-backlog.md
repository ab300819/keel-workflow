# DevDocs 流程待办

> 2026-09-11 登记。⚠️ **未分析，只有取证。** 两条都需要先做判断再动手。
>
> 与 [对象模型收敛设计](../superpowers/specs/2026-09-11-devdocs-object-model-convergence-design.md) 是**两条轴**：那份管编号对象与文档结构，本文管流程本身的暴露面与外部复用。

## 1. 用户面仍有子指令露出

**与现役规则直接冲突。** `_shared/constraints.md:162` 的 `task/intent-normalization` 明写：

> 协议参数（`--from-prd` / `--review-drain` / `--schema-drift` / `--force-code-docs` / `--review-profile` / `--no-realign` 等）**保留**，但**只存在于编排层与子 Agent 之间，用户无需知道它们存在**

### 取证（2026-09-11 实测）

**用户入口文档 `README.md`** 直接露出：`/ms-onboard --read`（2 处）· `/ms-dev-workflow --all` · `--readiness` · `--impl` · `--docs` · `--list`

**各 SKILL.md 的「运行模式 / 快速开始」节**（用户敲 `/<skill>` 时会读到）露出的子指令数：

| skill | 数量 | | skill | 数量 |
|---|---:|---|---|---:|
| `ms-verify` | 8 | | `ms-test-run` / `ms-prd-brainstorm` / `ms-compound` | 2 |
| `ms-sync` | 8 | | `ms-test-cases` / `ms-system-design` / `ms-retrofit` | 1 |
| `ms-pipeline` | 7 | | `ms-prd-parser` / `ms-feature` / `ms-dev-tasks` | 1 |
| `ms-requirements` / `ms-prd` / `ms-onboard` | 3 | | `ms-codebase-insight` / `ms-bugfix` | 1 |

**17 个 ms- skill 的用户面入口节都有。**

### 待判断的（⛔ 不要直接删）

1. **规则是不是过宽了？** `--readiness` / `--impl` / `--docs` 这类**选阶段**的参数，与 `--fast` / `--deep` 这类**选档位**的偏好词，性质可能不同。规则原文举的例子全是后者。前者删掉后用户怎么表达"我只想查实现正确性"？
2. 若确认要收，`/ms-pipeline` 的 8 个模式名（`init`/`feature`/`bugfix`/…）算不算子指令？它们是位置参数不是 flag，但同样要求用户记。
3. 收敛后编排层靠什么判断意图——`task/intent-normalization` 要求"归一化后下传"，但没写归一化的判据表。

⇒ **先判 1，再谈动手。** 判断结论应回写 `constraints.md:158` 那条规则本身（要么收窄规则，要么收窄暴露面）。

## 2. 根据 superpowers 优化 DevDocs 流

DevDocs 的多个阶段与 `superpowers` 插件的过程型 skill 职责重叠。需要逐对比对，判断是**重复实现**（应删一边）、**应当委托**（DevDocs 调 superpowers），还是**确实不同**（保留并写清边界）。

### 候选重叠对

| DevDocs 侧 | superpowers 侧 | 初判（⚠️ 未验证）|
|---|---|---|
| `ms-prd-brainstorm` | `brainstorming` | 都做需求探索 |
| `ms-dev-tasks` | `writing-plans` | 都做多步任务拆分 |
| `ms-dev-workflow` | `executing-plans` · `subagent-driven-development` · `test-driven-development` | 重叠最重的一处 |
| `ms-verify` | `verification-before-completion` | 都是完成前质量门 |
| `adversarial-review` | `requesting-code-review` · `receiving-code-review` | 都做外部审查 |
| `ms-bugfix` | `systematic-debugging` | 都是测试先行的缺陷流程 |

### 判据（比对时用）

- **删一边的条件**：两者的输入、产物、门控完全可互换，且没有 DevDocs 特有的追溯要求
- **委托的条件**：superpowers 侧的过程更完整，DevDocs 只需在前后补追溯写入
- **保留的条件**：DevDocs 侧承载了编号追溯 / yaml-summary 契约 / 断点恢复，superpowers 侧没有

⚠️ `superpowers:using-superpowers` 声明「process skills come first — they set the approach」。若这条成立，`ms-*` 里的过程部分本就该是委托而非自实现。**这个前提要先核实**，它决定整件事的方向。

⇒ 依赖第 1 条的结论：暴露面若要收敛，委托关系会一并变化，两件事应同批做。
