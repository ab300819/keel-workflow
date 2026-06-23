---
name: code-quality
description: Opinionated constraints for writing maintainable, testable code. Apply MTE principles, naming, comment, and logging standards, avoid over-engineering, guide refactoring, and provide code review checklists. Use when users write code, refactor, or need code review. Triggers on keywords like "code quality", "refactor", "review", "MTE", "naming", "logging", "代码质量", "重构", "审查", "命名", "注释", "日志". NOT for systematic refactoring workflow with scope analysis and test gates (use refactor).
allowed-tools: Read, Write, Glob, Grep, Edit, Bash, AskUserQuestion
---

# Code Quality

编码和重构时的质量约束（代码质量 SSOT），确保代码可维护、可测试、适度扩展。

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese

## Trigger Conditions

- 用户正在编写新代码 / 重构现有代码
- 用户需要 Code Review 检查清单
- 用户提到 MTE 原则、代码质量、命名、注释、避免过度设计

## 核心原则：MTE

所有代码必须遵循 **MTE 原则**：

| 原则 | 说明 | 检查点 |
|------|------|--------|
| **Maintainability** | 可维护性 | 职责单一、依赖清晰、命名与注释合规、易于理解 |
| **Testability** | 可测试性 | 核心逻辑可单元测试、依赖可 Mock |
| **Extensibility** | 可扩展性 | 预留合理扩展点、接口抽象 |

## 核心阈值表

**全仓唯一权威阈值源**。谓词语义统一：**≤ 最大值 = 合规；> 建议值且 ≤ 最大值 = [Suggestion]；> 最大值 = [Blocker]**。镜像处（如 dev-workflow verification-flow Phase 1）须标注"摘录自本表，变更需同 commit 同步"。

| 指标 | 建议值 | 最大值 | 超最大值的重构方向 |
|------|-------:|-------:|--------------------|
| 函数长度 | 30 行 | 50 行 | 提取函数 |
| 参数数量 | 3 个 | 5 个 | 参数对象 |
| 嵌套深度 | 2 层 | 3 层 | 早返回、提取函数 |
| 重复代码 | — | 3 处（Rule of Three） | 提取公共逻辑（<3 处禁止提前抽象） |
| 单类/单文件行数 | — | 500 行 | 拆分职责（上帝类） |

## 模块设计

- **单一职责**：一个类/函数只做一件事（UserService 业务 / UserRepository 数据访问 / UserValidator 校验分开；反例：UserManager 全包）
- **依赖方向**：外层依赖内层（Interface → Service → Domain → Infrastructure）；依赖接口，不依赖实现
- 正反例代码见 [references/mte-examples.md](references/mte-examples.md)

## 命名规范

**总原则**：

1. **精确优先**：减长度靠删冗词（不重复类型信息），禁止截短单词（实证：完整单词比缩写定位 bug 快 19%，名长 10-16 字符调试成本最低）
2. **调用点清晰**：名字在调用处读起来像自然短语（clarity at the point of use）
3. **项目一致性**：同概念同名；沿用项目既有大小写惯例而非语言默认；引入新名词前先 grep 项目既有词表

### 分类规则

| 类别 | 规则 |
|------|------|
| 类/接口 | 名词短语，描述角色而非实现；禁 `Manager/Helper/Util/Processor/Info/Data` 等空泛后缀收尾 |
| 方法/函数 | 有副作用用动词短语、纯查询用名词；全库同一动作只用一个动词（get/fetch/retrieve 选一）；`get*` 禁副作用 |
| 变量 | 长度与作用域成正比：循环/闭包 ≤10 行可用惯用单字母（i/j/k/err/ctx）；函数级 ≥1 完整词；导出符号默认 ≥2 词自含上下文* |
| 布尔 | 读作断言（isEmpty/hasChildren/canEdit）；`is*/has*` 必须返回布尔；禁否定式名（isNotReady） |
| 常量 | 魔法数字按含义命名（MAX_RETRIES 而非 FIVE） |

> \* 调用点已有命名空间上下文时按语言惯例豁免（如 Go 包名 `http.Client`、Swift 类型命名空间）。

### 命名黑名单（本次 diff 新增命中即 [Blocker]；存量未触碰为 [Suggestion]）

| 反模式 | 分级 |
|--------|------|
| 误导名：名实不符（`accountList` 非 List、`is*` 返回非布尔、`get*` 带副作用） | [Blocker]（最高红线：误导名同样降低 agent 自身代码分析准确率） |
| 泛化名作完整名：`data/info/temp/result/obj/item/thing/flag/val`（局部惯用语除外） | [Blocker] |
| 同概念多名漂移：同一实体 user/account/customer 混用（引入新名词前必须先 grep 项目词表） | [Blocker] |
| 类型编码（匈牙利前缀 `strName/m_x`）、不可发音自造缩写 | [Blocker] |
| 无意义区分（`data1/data2`、`ProductInfo` 与 `ProductData` 并存）、大作用域单字母 | [Suggestion] |

**边界**：本规范只判定结构合规（白/黑名单、词性、一致性），不裁决具体选词。正反例见 [references/naming-examples.md](references/naming-examples.md)。

## 注释规范

**信息归宿三分法**：源码注释 = 面向未来读者的稳定事实；commit message = 本轮变更说明；traceability/任务文档 = 过程追溯。注释唯一合法用途是承载代码无法表达的信息——能用命名/重构表达的不写注释，后两类信息禁止写进源码注释。

### 白名单（注释必须属于以下类别之一）

| 类别 | 判定 |
|------|------|
| 公共契约 | exported API 上方，说明调用契约/错误/边界/不变量，不复述函数名和类型 |
| 非显然 why | 外部协议、兼容性、性能、并发、安全、算法取舍；删掉后读者无法判断"为什么这样写" |
| 不变量/风险约束 | 类型系统与测试名无法表达的业务约束，紧邻校验或状态转换 |
| 复杂 what + 出处 | 复杂算法/正则/反惯用绕坑写法，说明不这样写会踩什么坑；出处仅限**外部稳定来源**（论文/RFC/issue 链接），项目内过程文档（设计/AC/UT）引用归 traceability，不入注释 |
| 抑制类 | `eslint-disable` / `ts-ignore` 等必须附具体原因 |
| 临时脚手架 | 仅限 S2/S3 骨架阶段（TODO / `test.skip`/`todo` / 纯 AAA 占位）；S4/S6/S7 后必须清除 |

> 文件头 INPUT/OUTPUT/POS 自描述由 `/code-self-describe` 独立管理，不受本规范约束。

### 黑名单（本次 diff 新增/修改命中即 [Blocker]；按语义判定，关键词仅作信号）

| 类别 | 判定 |
|------|------|
| 变更日志式 | 注释描述本轮变更过程而非代码当前状态（信号词：本次/新增/修改/修复/已按要求；描述业务规则的"新增用户走邀请码通道"合法） |
| 对审查者说话 | "此处已修复""按要求处理"等面向 reviewer/agent 而非未来读者的话 |
| 来源记录式/注释式追溯 | 记录"来自 UT-XX/AC-XX/后置条件/行为契约"等过程来源；layout.v2 新增 `@satisfies/@verifies/@testcase/@requirement` 追溯标注（layout.v1 legacy retained 注释除外） |
| 复述代码 | 只是翻译紧邻代码（`// 校验邮箱` + `validateEmail(email)`） |
| 注释掉的代码 | 整段旧实现注释保留且无 issue/迁移理由 |
| 过量注释 | 同函数连续注释 >3 行，或变更块注释行 > 可执行代码行，且不属白名单 |

### 分级

- **[Blocker]**：本次 diff 新增/修改黑名单注释；抑制类注释无理由；S4/S6/S7 后残留骨架脚手架注释；注释与代码当前语义不符（改代码必须同步更新受影响注释，过期注释比没注释更糟）
- **[Suggestion]**：存量坏注释（本次未触碰）；public API 缺契约注释（仅当缺失已造成安全/兼容/行为歧义时按对应风险升级）

## 日志规范

日志唯一目标是**让线上失败被快速排查 / 审计 / 观测**——价值在"对的级别 + 对的上下文 + 不泄密"，不在量；烂日志是烂注释的运行时版本（见上节），同样按本次 diff 新增/修改命中分级。设计阶段"在哪打日志点"见 [system-design log-design-guide.md](../system-design/templates/log-design-guide.md)，本节是**编码纪律 SSOT**。

### 六条硬规则

| 规则 | 判定要点 |
|------|----------|
| **目的门槛** | 每条日志须服务排查/审计/观测；禁 `here`/`step1`/进出方法/"执行完成"等无对象无结果的占位日志 |
| **级别纪律** | ERROR/WARN/INFO/DEBUG·TRACE 准入见下表；最常见误用：所有异常都 ERROR、INFO 刷屏、WARN 当 INFO |
| **最小上下文** | 业务日志含 event + result + 关联 id + 组件 + 一个**安全**主对象 id；失败日志另加 error_code/异常类型 + 原因 + 已采取动作；用结构化字段承载，禁纯文本拼接关键上下文（字段名沿用项目词表）|
| **异常纪律** | 异常只在**处理边界**记一次完整堆栈；禁 log-and-throw（逐层 log 再抛 = 重复"根因"）；禁吞异常只 log（除非契约明确已降级/补偿并注明）|
| **安全红线** | 禁入日志：密码、token、session/cookie、密钥、验证码、原始请求/响应体、原始 SQL/查询、PII、支付/银行/医疗数据、未脱敏的第三方或 LLM 原始响应 |
| **事实优先** | 写不可变事实 + 系统动作；推测/风险/模型判断须带来源、规则名或置信度（禁 `payment service is broken`，写 `upstream_status=504, retry_scheduled=true`）|

### 级别准入（规则「级别纪律」展开）

| 级别 | 准入判据 |
|------|----------|
| ERROR | 当前请求/任务/事务失败，用户或系统可感知，需调查或可触发告警 |
| WARN | 异常但已处理、系统可继续：降级、重试耗尽前兆、配置风险 |
| INFO | **低频且长期有价值**的里程碑：启动/停止、配置版本、任务摘要、关键状态变更 |
| DEBUG / TRACE | 默认**生产关闭**的诊断细节；必须排查的失败不得只放 DEBUG |

### 分级

- **[Blocker]**：本次 diff 新增/修改命中安全红线、log-and-throw 重复堆栈 / 吞异常只 log、把推测写成事实
- **[Suggestion]**：本次 diff 新增/修改的级别误用、上下文不足、占位日志；存量坏日志（本次未触碰）

### 不写死（留给项目规范）

日志格式（JSON/logfmt）、字段大小写、每业务事件清单、采样率、保留周期、**脱敏或截断后**的 SQL/HTTP payload 策略——依赖运行平台与监管，写死有害。（注：**原始** SQL/请求/响应体始终属安全红线，禁入日志，不在"留给项目"之列。）

## 设计原则（代码级）

SOLID + 迪米特六大原则的**代码级/diff 级可机械判定特征**。设计级判定（启发式阈值/三态结论表/ADR 联动）权威归 [system-design solid-principles-guide.md](../system-design/references/solid-principles-guide.md)，本节不替代。

| 原则 | 代码级判定特征 |
|------|---------------|
| SRP 单一职责 | 类/函数职责描述含"和/并且"等多职责连接词 |
| OCP 开闭 | 新增类型靠修改已有 switch/if-else 分支扩展 |
| LSP 里氏替换 | 子类/实现抛出父类（接口）契约外异常，或强化前置条件/弱化后置条件 |
| LoD 迪米特 | 链式跨层调用 `a.getB().getC().getD()`（跨 >2 层；fluent API/builder 除外） |
| ISP 接口隔离 | 单接口方法数 >7，或消费方使用比例 <50%（胖接口） |
| DIP 依赖倒置 | 跨模块依赖出现具体实现类名而非接口 |

**分级**：DIP 违反为 [Blocker]（与设计级硬约束对齐）；其余五条为 [Suggestion]（启发式，违反须说明理由）。

## 可测试性设计

可测试代码三要素（详细测试编写规范见 `/testing-guide`）：

1. **依赖可注入** —— 外部依赖通过参数/构造器传入，不硬编码
2. **纯函数优先** —— 业务逻辑无副作用，相同输入相同输出
3. **边界分离** —— 业务逻辑与 IO 分离

正反例见 [references/mte-examples.md](references/mte-examples.md)。

## 避免过度设计

- **YAGNI**：不为假设需求添加配置/扩展点
- **Rule of Three**：3 个以上实现才建接口（除非为测试）、3 处以上重复才提取、3 个以上相似场景才建基类
- **简单方案优先**：简单场景不套复杂模式
- 正反例见 [references/mte-examples.md](references/mte-examples.md)

## 设计模式使用

- **必要时才用**：解决实际问题，不为炫技
- **说明理由**：为什么选择这个模式
- **保持一致**：相同问题用相同模式

> 模式选择是设计时决策，场景→模式映射表权威见 [system-design design-patterns.md](../system-design/references/design-patterns.md)（由 02-system-design §6 设计模式章节消费），本文件不镜像。

## 重构指导

安全约束（不可降）：

- [ ] **重构前必须有测试覆盖**（无测试先补测试）
- [ ] **每步重构后运行测试**，小步前进
- [ ] **不在重构中添加新功能**，不在添加功能时重构
- [ ] 单次重构只改一类问题

Code Smells 触发信号、风险评估、详细流程见 [references/refactor-signals.md](references/refactor-signals.md)；系统性重构工作流（范围分析 + 测试门禁）用 `/refactor`。

## Code Review

### 反馈分级

> 全仓反馈分级**元语义**（Blocker/Suggestion/Question/Nice 的含义与处置要求）以本表为权威；各审查场景（verification-flow / ui-quality-checklist / adversarial-review 等）只定义领域特定判定条目，不重定义级别含义。

| 级别 | 标记 | 含义 | 要求 |
|------|------|------|------|
| 阻塞 | `[Blocker]` | 必须修复才能合并 | 安全问题、逻辑错误、核心阈值表超最大值、命名/注释黑名单、DIP 违反 |
| 建议 | `[Suggestion]` | 建议修改但不阻塞 | 超建议值、代码风格、小优化 |
| 疑问 | `[Question]` | 需要作者解释 | 不理解的设计决策 |
| 赞 | `[Nice]` | 写得好的地方 | 鼓励好的实践 |

### 最小审查清单

- [ ] 核心阈值表全部合规（函数/参数/嵌套/重复/单类）
- [ ] 命名无黑名单命中（误导名/泛化名/同概念漂移/类型编码）
- [ ] 注释无黑名单命中（变更日志式/对审查者说话/来源记录式/复述代码）
- [ ] 设计原则（代码级）六条无命中
- [ ] 依赖可注入、业务逻辑与 IO 分离
- [ ] 无过度设计（YAGNI / Rule of Three）
- [ ] 错误处理：边界条件、错误信息有意义、不吞异常
- [ ] 日志：级别正确、含关联 id + 最小上下文、无 log-and-throw（命中安全红线即 Blocker，详见日志规范）
- [ ] 安全：无注入/XSS 风险、敏感数据不入日志、权限正确

反馈必须分级并说明理由；安全问题必须 [Blocker]。完整审查维度与输出格式见 [references/review-rubric.md](references/review-rubric.md)。

## 参考资料

| 文件 | 内容 |
|------|------|
| [references/mte-examples.md](references/mte-examples.md) | 模块/函数/可测试性/YAGNI 正反例代码 |
| [references/naming-examples.md](references/naming-examples.md) | 命名正反例、大小写惯例、命名空间例外 |
| [references/refactor-signals.md](references/refactor-signals.md) | Code Smells 信号、重构流程、风险评估 |
| [references/review-rubric.md](references/review-rubric.md) | Review 详细清单与输出格式 |
