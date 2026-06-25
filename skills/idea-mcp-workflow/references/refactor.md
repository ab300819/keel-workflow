# 重构 / 重命名

> 前提：所有工具显式传 `projectPath`（见 SKILL.md 纪律 1）。下面只讲**决策和坑**，工具参数以 MCP 描述为准。

## 核心决策：改符号用 rename_refactoring，别用文本替换

重命名**符号**（类 / 方法 / 字段 / 变量 / 参数）时，用 `rename_refactoring`——它是 PSI 级、**跨文件更新所有引用**，且不会误伤注释和字符串里的同名文本。

裸文本替换（`replace_text_in_file` / `search_in_files` 改写）做重命名的典型翻车：

- **漏掉其它文件的引用** → 编译断裂；
- **误改字符串字面量 / 注释 / 无关同名标识符**；
- 不处理 import、不识别重载/继承关系。

```
判断：要改的是「一个有定义和引用的符号」吗？
  是 → rename_refactoring（先用 search_symbol / get_symbol_info 定位确认作用域）
  否 → 才用 replace_text_in_file（纯字符串内容、配置值、符号引擎够不到的动态引用）
```

## 流程

1. `search_symbol` / `get_symbol_info` 定位目标符号，确认唯一、作用域清楚。
2. **rename 前**先 `search_in_files_by_text` 全局搜一遍旧名，记下符号引擎可能覆盖不到的命中（见下）。
3. `rename_refactoring` 执行。IDE 的 rename 有 **preview / 冲突检测**——有冲突或歧义时会提示，别忽略。
4. `reformat_file` 收尾格式（如需要）。
5. **回到编译验证**（SKILL.md 编译工作流）`build_project` 确认引用全部更新、无断裂；再 `git diff` 核对改动面是否符合预期、没误伤。

## 高频坑：符号引擎覆盖不到的引用

`rename_refactoring` 处理代码内的符号引用、import、override、文件名很可靠，但**下面这些往往不在覆盖范围**，rename 后不会自动改，必须靠第 2 步的全局搜旧名 + 第 5 步 git diff 兜底：

- 反射 / 字符串拼出来的类名、方法名
- Spring bean 名、`@Qualifier`、SpEL 表达式
- MyBatis XML、JPA `@Query`、原生 SQL 里的列/表名
- 配置文件里的 key（YAML / properties）、JSON 字段名
- 注释、文档、日志里的旧名（视情况要不要改）

大范围重命名先在小作用域验证一次行为再放开。
