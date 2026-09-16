# code-quality 结构优化 + 命名规范方案

> 2026-06-12 · 状态：已对齐（Claude 评估 ⇄ Codex 独立调研 2 轮收敛；命名规则对齐 A 3/3 + B 5/5 AGREE）
> 前序：[2026-06-12-dev-workflow-comment-quality.md](2026-06-12-dev-workflow-comment-quality.md)（注释规范已落地 `a4dc354` —— ⚠️ 该提交是 pre-push amend 遗留的游离对象，任何 clone 都解析不到）

## 1. 动因（双方独立调研收敛）

| 问题 | 证据 | 紧迫度 |
|------|------|--------|
| 行数余量耗尽 | 495/500 行，命名规范按注释规范同等密度需 25-40 行，必然超限 | **高（阻塞命名规范落地）** |
| 内容冗余 | 函数/参数/嵌套阈值在 4 处重复（函数设计、重构触发表、Review 清单、Constraints 总表） | 中 |
| 阈值表述已漂移 | 主文件"最大不超过 50/5/3" vs Review 清单 `<50/<5/<3` vs verification-flow `≤50/≤5/≤3`——重复已产生真实边界 bug | **高（正确性问题）** |
| 信息密度低 | 12 个代码块约 175 行通用 TS 示例；Part 4 应用场景复述 Part 1 | 中 |
| 镜像漂移风险 | verification-flow Phase 1 镜像了完整阈值清单，无同步机制 | 中 |

code-quality 被约 17 处引用（dev-workflow S6/S9 Phase 1、bugfix、refactor、verify、adversarial-review、system-design、testing-guide 等），是事实上的代码质量 SSOT——结构必须先于内容扩张收敛。

## 2. 目标结构

| 位置 | 内容 | 预估行数 |
|------|------|---------:|
| `SKILL.md` | frontmatter（description 补命名触发词）、触发条件、MTE 总原则、**核心阈值表**（唯一权威）、**命名规范**（新）、**注释规范**（保留锚点）、**设计原则（代码级）**（新，见 §3.5）、设计模式三条使用原则 + 指针（表删除，见 §3.5）、Review 反馈分级 + 最小审查清单、references 索引 | **~280** |
| `references/mte-examples.md` | DI、纯函数、边界分离、早返回、参数对象、YAGNI、简单方案优先的正反例代码 | 80-120 |
| `references/refactor-signals.md` | Code Smells 触发表、小步重构流程、风险矩阵（与 /refactor skill 边界声明保留） | 50-80 |
| `references/review-rubric.md` | Review 输出格式、Blocker/Suggestion 详例、前置检查 | 40-70 |
| `references/naming-examples.md` | 命名正反例、语言差异示例（大小写惯例、命名空间例外） | 50-90 |

**直接删除**：Part 4 应用场景（复述 Trigger Conditions）；末尾 Constraints 总表（合并入核心阈值表与最小审查清单）。

### 核心阈值表（统一语义，修漂移 bug）

谓词统一：**≤ 最大值 = 合规；> 建议值且 ≤ 最大值 = Suggestion；> 最大值 = Blocker**

| 指标 | 建议值 | 最大值 |
|------|-------:|-------:|
| 函数长度 | 30 行 | 50 行 |
| 参数数量 | 3 个 | 5 个 |
| 嵌套深度 | 2 层 | 3 层 |
| 重复代码 | — | 3 处（Rule of Three，超出须提取） |
| 单类行数 | — | 500 行（上帝类） |

全仓引用处（verification-flow Blocker 表等）统一按此谓词修正。

## 3. 命名规范章节设计（新增，~40 行）

### 总原则（3 条）

1. **精确优先**：减长度靠删冗词（不重复类型信息），禁止截短单词（实证：完整单词比缩写定位 bug 快 19%，Hofmeister 2017；名长 10-16 字符调试成本最低，Gorla/Code Complete）
2. **调用点清晰**：clarity at the point of use（Swift API Guidelines）
3. **项目一致性**：同概念同名；沿用项目既有大小写惯例而非语言默认（LLM 风格偏移实证 arXiv 2506.12014）

### 分类规则表（5 类）

| 类别 | 规则 |
|------|------|
| 类/接口 | 名词短语，描述角色而非实现；禁 `Manager/Helper/Util/Processor/Info/Data` 空泛后缀收尾 |
| 方法/函数 | 副作用用动词短语、纯查询用名词；全库同一动作只用一个动词（get/fetch/retrieve 选一）；`get*` 禁副作用 |
| 变量 | 长度与作用域成正比：循环/闭包 ≤10 行可惯用单字母（i/j/k/err/ctx）；函数级 ≥1 完整词；导出符号默认 ≥2 词自含上下文* |
| 布尔 | 读作断言（isEmpty/hasChildren/canEdit）；`is*/has*` 必须返回布尔；禁否定式名（isNotReady） |
| 常量 | 魔法数字按含义命名（MAX_RETRIES 而非 FIVE） |

> \* 脚注（Codex B2 补强）：调用点已有命名空间上下文时按语言惯例豁免（如 Go 包名 `http.Client`、Swift 类型命名空间）。

### 黑名单分级（沿用注释规范模式：本次 diff 新增命中 → Blocker；存量未触碰 → Suggestion）

| 反模式 | 分级 | 依据 |
|--------|------|------|
| 误导名（名实不符：`accountList` 非 List、`is*` 返回非布尔、`get*` 带副作用） | **Blocker（最高红线）** | 误导名显著降低 LLM 自身代码分析准确率（arXiv 2307.12488），双向反噬 |
| 泛化名 deny-list（`data/info/temp/result/obj/item/thing/flag/val` 作完整名；局部惯用语除外） | Blocker | LLM 补全低能耗默认路径，须硬禁 |
| 同概念多名漂移（同一实体 user/account/customer 混用；引入新名词前必须先 grep 项目既有词表） | Blocker | LLM 跨轮无记忆特有失败模式 |
| 类型编码（匈牙利前缀）、不可发音自造缩写 | Blocker | Clean Code；Google 各语言指南均废弃 |
| 无意义区分（data1/data2、ProductInfo 与 ProductData 并存）、大作用域单字母 | Suggestion | Clean Code；Go Style |

### 边界声明

规范只判定**结构合规**（白/黑名单、词性、一致性），不裁决具体选词（Feitelson TSE 2021：两人独立选同名概率仅 6.9%，但多数名可被理解）。正反例归 `references/naming-examples.md`。

## 3.5 跨 skill 收敛：六大原则与设计模式（R3 新增）

### 六大原则（SOLID+LoD）——分层引用，不整体迁移

`system-design/references/solid-principles-guide.md` 是**设计级**审查资产（阈值挂 02-system-design §4/§5 章节、三态结论表、ADR 联动、复杂度分级触发），保持权威不动。code-quality 新增「设计原则（代码级）」小节（~12 行）——六原则各一行**代码级/diff 级可机械判定特征**：

| 原则 | 代码级判定特征 |
|------|---------------|
| SRP | 类/函数职责描述含"和/并且"等多职责连接词 |
| OCP | 新增类型靠修改已有 switch/if-else 分支扩展 |
| LSP | 子类/实现抛出父类（接口）契约外的异常，或强化前置/弱化后置 |
| LoD | 链式跨层调用（`a.getB().getC().getD()`，跨 >2 层） |
| ISP | 单接口方法数 >7，或消费方使用比例 <50%（胖接口） |
| DIP | 跨模块依赖出现具体实现类名而非接口 |

并声明：设计级判定（启发式阈值/三态表/ADR）归 solid-principles-guide；guide 加一行反向指针。「反例对照」节保留在 guide 原处不搬。

### design-patterns 镜像收敛——权威归 system-design

code-quality 的"设计模式使用"推荐场景表与 `system-design/references/design-patterns.md` 逐行镜像（既存 SSOT 违反）。模式选择是设计时决策（02-system-design 有 §6 设计模式章节）：code-quality **删除自己的表**，仅保留"必要时才用 / 说明理由 / 保持一致"三条使用原则 + 指针。

行数影响：C1 增 ~12 行、C2 减 ~15 行，主文件 ~280 行目标不变。

## 4. SSOT 镜像策略（verification-flow Phase 1）

- **不改纯指针**：Phase 1 是执行入口，子 Agent 需低成本拿到可执行阈值
- **保留短镜像 + 同步标注**：镜像处标注"摘录自 `/code-quality` 核心阈值表，变更需同 commit 同步"；删除解释性重复，只留审查执行所需最小清单
- **新增「命名卫生」短清单**（与注释卫生同模式，3-4 行 + 指针）：只覆盖红线——误导名、泛化名、同概念漂移、类型编码/不可发音缩写
- **health-lint 镜像一致性 rule 不在本次范围**：登记到 AGENTS.md「当前状态」deferred 项（原拟 `/ms-backlog`，但 backlog.v1 `source_id` 强制复用 F/US/AC/T 等已有编号，本规格库无该编号体系，落地时调整）

## 5. SSOT 稳定锚点清单（对外契约，重构不得破坏）

| 锚点 | 既有引用方 |
|------|-----------|
| `#注释规范` | dev-workflow SKILL.md、task-orchestration.md ×2、verification-flow.md、skeleton-examples.md、execution-flow.md |
| `#核心阈值表`（新） | verification-flow.md Phase 1 镜像标注 |
| `#命名规范`（新） | verification-flow.md 命名卫生清单 |
| `#设计原则代码级`（新） | solid-principles-guide.md 反向指针；verification-flow Phase 1 后续可短链引用（不复制六原则表） |

## 6. 迁移步骤

1. 创建 4 个 references/ 文件，搬移示例与展开内容（git 原生操作，遵循 /git-safety）
2. 重写 SKILL.md：核心阈值表（统一谓词）+ 命名规范 + 注释规范（原文保留）+ 设计原则（代码级）+ 设计模式三条原则 + 指针（删推荐场景表）+ 最小清单 + references 索引；删 Part 4 与 Constraints 总表
3. system-design/references/solid-principles-guide.md 加反向指针（一行，指向 `#设计原则代码级`）
4. 修正 verification-flow.md：Phase 1 镜像加同步标注、按统一谓词修正 Blocker 表、加命名卫生短清单
5. 校验：SKILL.md ≤500、全部锚点链接可达、阈值表述全仓一致
6. AGENTS.md「当前状态」登记 health-lint 镜像一致性 rule deferred 项（backlog.v1 source_id 约束不适用于本规格库，见 §4）
7. Codex 审查 diff 至 PASS 后提交

## 7. 对齐记录

- R1（优化必要性）：Codex 独立调研结论与 Claude 评估收敛——紧迫度高、主文件 SSOT 核心化 + references 拆分、删 Part 4/Constraints；Codex 额外发现阈值表述漂移 bug（`<50` vs `≤50`）
- R2（结构微调 + 命名规则）：A1 主文件 ~280 行 / A2 镜像同步标注 + backlog / A3 阈值谓词统一，3/3 AGREE；命名 B1 总原则 / B2 分类表 / B3 黑名单分级 / B4 结构合规边界 / B5 Phase 1 命名卫生，5/5 AGREE + B2 命名空间例外脚注补强
- R3（跨 skill 收敛）：C1 六大原则分层引用（设计级归 solid-principles-guide，代码级判定入 code-quality）/ C2 design-patterns 镜像收敛权威归 system-design，2/2 AGREE；Codex 支持新增 `#设计原则代码级` 锚点（Phase 1 现有 MTE 清单未覆盖 LoD/LSP/OCP/ISP 代码级特征，锚点是稳定引用点而非镜像）

## 引用

- Martin, *Clean Code* ch.2；McConnell, *Code Complete 2e* ch.11；Ousterhout, *A Philosophy of Software Design* ch.14
- [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)；[Google Go Style: Naming](https://google.github.io/styleguide/go/decisions.html)
- Feitelson et al., "How Developers Choose Names", IEEE TSE 2021（[arXiv 2103.07487](https://arxiv.org/abs/2103.07487)）
- Hofmeister et al., "Shorter identifier names take longer to comprehend"（EMSE 2017）
- Arnaoudova et al., Linguistic Antipatterns
- [arXiv 2506.12014](https://arxiv.org/pdf/2506.12014)（LLM 命名风格偏移）；[arXiv 2307.12488](https://arxiv.org/abs/2307.12488)（误导名降低 LLM 分析准确率）
