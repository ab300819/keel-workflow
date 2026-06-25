---
name: idea-mcp-workflow
description: Operating manual for driving JetBrains projects through the `idea` MCP server (the ~60 `mcp__idea__` tools — file/symbol search, inspections, build/run, XDebug, database). Covers the cross-cutting projectPath discipline (required when multiple projects are open), keeping build_project's huge compile output from blowing up context (scope with filesToRebuild instead of dumping it), telling dependency/classpath errors apart from real code bugs, the "Maven reload is UI-only" gotcha, plus debug / database / refactor recipes. Use whenever the user operates a project through the idea / JetBrains / IntelliJ MCP — mentions idea、jetbrains、IntelliJ、编译项目 / build_project、IDE 调试 / xdebug 断点、execute_sql_query、reload maven、or invokes any mcp__idea__ tool — even if they don't name the skill. NOT for the general code-writing flow (use dev-flow) or DevDocs task execution (use ms-dev-workflow); this is specifically the idea-MCP operating playbook for decisions, gotchas, and tool sequences.
---

# idea MCP 操作手册

通过 `idea` MCP server（JetBrains IDE 插件，工具前缀 `mcp__idea__`）操作项目时的**决策、踩坑、工作流**。

`mcp__idea__*` 全是 **deferred 工具**：调用前必须先用 `ToolSearch` 加载 schema（如 `select:mcp__idea__build_project`），否则直接调用会 `InputValidationError`。本手册只承载怎么用、哪里会踩坑——具体工具的参数清单以 MCP 自带描述为准，不在此复制。

## Language

- Accept questions in both Chinese and English
- Always respond in Chinese

## 触发条件

- 用户要求用 idea / JetBrains / IntelliJ 操作某个项目（编译、调试、查库、改代码）
- 用户提到 `编译项目`、`build_project`、`IDE 调试`、`xdebug 断点`、`execute_sql_query`、`reload maven`
- 会话中需要调用任何 `mcp__idea__*` 工具

---

## 纪律 1：projectPath 必填（跨切面，最高频坑）

用户常**同时打开多个项目**（如 envo、trade，路径在 `/Users/mason/Projects/mic/mic-en/` 下）。此时任何 `mcp__idea__` 工具**不传 `projectPath` 会报「无法确定目标项目」**。

**规则：每次操作前先确认目标项目路径，并在调用时显式传 `projectPath`。** 不确定当前该操作哪个项目时，按序兜底：

1. 先调一次**不带 `projectPath`** 的轻量工具（如 `get_all_open_file_paths`），报错会回 `Currently open projects: {"projects":[{"path":...}]}`，从中拿候选路径；
2. 候选唯一就用它；多个且无法从上下文判断时——**以编号列表把候选项摆给用户选**，不要猜。

确定后**同一任务内固定复用**同一 `projectPath`；用户**切换项目或子模块**时要重新确认，不要沿用旧值。

> `projectPath` 必须是**绝对路径**。传裸项目名（如 `"envo"`）或相对名会报 `URI has an authority component`。

## 纪律 2：编译输出会撑爆上下文 → 在源头缩小范围

一次全项目编译错误可达 **~200K 字符**。关键事实：`build_project` 把结果**直接返回进上下文**（schema 无输出文件/限量参数）——**返回那一刻 token 就已经花掉了，事后落盘 jq 省不回来**。所以重点是**在源头把输出限小**：

1. **只编译改过的文件**：`build_project` 传 `filesToRebuild: ["相对路径", ...]`，而非整项目。输出量直接由改动面决定——这是首选。
2. **单文件自检**用 `get_file_problems`（传 `errorsOnly: true` 只看错误），比编译更轻。
3. **确实要全项目验证、且预期错误很多**时：改用 `execute_terminal_command` 跑构建工具并**重定向到文件**（如 `mvn -q compile > build.log 2>&1`），输出落盘**不进上下文**，再 grep / 聚合 `build.log`。
   - 注意（见纪律 4）：CLI 构建用 Maven 自己的解析，**不反映 IDE classpath**。判断「依赖是否在 IDE 里解析了」必须用 `build_project`（IDE 视角）；CLI 只适合纯粹「代码能不能编译过」。
4. 不论结果从哪来：**只回报 ERROR 摘要**给用户，WARNING 折叠成计数，不整段贴回。

> **先探样本再聚合**：`build_project` 的返回结构未经确认（可能是结构化 JSON，也可能是文本）。先看一条样本——JSON 用 `jq 'keys'` / `jq '.[0]'` 确认字段，文本就按级别 `grep`。**不要照搬下面的字段名**。

```bash
# 若结果确实是 {isSuccess, problems:[{kind,message,...}]} 这类结构（先 jq keys 确认）：
jq '{ok: .isSuccess, total: (.problems|length)}' build.json
jq '.problems | group_by(.kind) | map({kind: .[0].kind, count: length})' build.json
jq -r '.problems[]|select(.kind=="ERROR")|.message' build.json | sort | uniq -c | sort -rn
```

## 纪律 3：先区分「依赖未解析」还是「真·代码 bug」

下面这类是**依赖/classpath 未解析的强信号**（不是定论），先按依赖问题排查、不要急着改源码：

- `程序包 X 不存在` / `package X does not exist`
- `找不到符号` / `cannot find symbol` ——尤其指向 **注解处理器生成的代码**（Lombok 的 getter/setter/builder、MapStruct、QueryDSL、protobuf、jOOQ 等）或明显属于第三方依赖的类
- 大量错误集中指向同一组未知包名

**强信号≠定论**：`cannot find symbol` 也可能是真 bug（拼错、真的没引入）；生成代码类报错也可能是 annotation processing / generated-sources / JDK / Maven profile 没配好。所以：命中强信号 → 优先走纪律 4（reload）验证；reload 后仍在，才当真问题逐条查。

## 纪律 4：Maven reload 是 UI 动作，当前 MCP 没暴露

`execute_terminal_command` 跑 `mvn dependency:resolve` 之类**只更新本地仓库，不会刷新 IDEA 工程的 classpath**；而刷新 classpath 的 **Maven sync / reload 是 IDE 里的动作，当前 MCP 工具面没有暴露**——所以纪律 3 的依赖类报错，**Claude 这边自动触发不了**。

**规则：遇到依赖类报错，请用户手动操作**，不要反复自动重试编译：

> 请在 IDEA 的 **Maven 工具窗口**点 **"Reload All Maven Projects"**（默认快捷键 macOS `⇧⌘I`，以你的 keymap 为准），完成后告诉我，我再 `build_project` 验证。

用户 reload 完成后，重新走纪律 2（IDE 视角的 `build_project`）确认问题消失。

---

## 高频工作流

### 编译验证（核心链路）

确认 `projectPath` → **缩小范围编译**（`filesToRebuild` 只编改过的文件，或 `get_file_problems` 单文件自检；纪律 2）→ 探样本后聚合 → 分类报告：

- **依赖问题**（纪律 3 命中）→ 给 reload 建议（纪律 4），停下等用户；
- **代码错误**（排除依赖后）→ 才逐条 ERROR 分析、定位、修复。

只有确需整项目验证时才全量 `build_project`，并按纪律 2 第 3 条防止输出撑爆上下文。

### 调试 / 数据库 / 重构

这三类是「按序调工具」的食谱，用到再读对应 reference（不必预先加载）：

| 场景 | 触发 | 读这个 |
|------|------|--------|
| XDebug 断点调试 | 调试、断点、xdebug、单步、看变量 | [references/debug.md](references/debug.md) |
| 数据库查询 | 查库、执行 SQL、看表数据、连接 | [references/database.md](references/database.md) |
| 安全重命名 / 重构 | 重命名、改符号、提取、重构 | [references/refactor.md](references/refactor.md) |

## 读码工具选择（次要）

需要**符号级**理解（找定义/引用、跨文件追类型）时，IDE 的索引工具比裸文本搜索准：`search_symbol` / `get_symbol_info` / `find_files_by_glob`。纯文本/正则匹配用原生 Grep 或 `search_in_files_by_regex` 都行，按手头方便选。

> **搜索噪声坑**：全项目 `search_in_files_*` 会把 `~/.m2` 里的**依赖 jar 源码**一起搜进来，淹没项目自身命中。用 `directoryToSearch` 收窄到目标模块（如 `envo-core/src/main/java`）再搜。多模块 Maven 项目**没有顶层 `src`**，要按模块目录定位。
