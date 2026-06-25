# 数据库查询

> 前提：所有工具显式传 `projectPath`（见 SKILL.md 纪律 1）。下面只讲**决策和坑**，工具参数以 MCP 描述为准。

## 第一步永远是「选对连接」（最大的坑）

`list_database_connections` 通常会列出**多个连接**（dev / staging / prod / 不同库）。**选错连接 = 操作错环境**，写操作下尤其危险（误改 prod）。

- `execute_sql_query` **必填 `connectionId` + `databaseName` + `schemaName`**——三者一起才唯一确定目标库。查询前先 `list_database_connections`，**按名称 + JDBC URL + 库/schema 三重核对**，不要只看连接名（名字可能重复，URL 才区分环境）。
- 不确定该用哪个连接 → **问用户**，不要默认第一个。
- 可用 `test_database_connection` 确认连接可用。

## 看数据 vs 真查询

| 目的 | 用 | 说明 |
|------|-----|------|
| 快速瞄一眼某张表 | `preview_table_data` | 自带分页/限量，最省 token |
| 找表/视图叫什么 | `list_schema_objects`（先 `list_database_schemas` / `list_schema_object_kinds`） | 不要靠猜表名 |
| 看表结构/DDL/字段 | `get_database_object_description` | 写 SQL 前确认列名类型 |
| 任意 SQL | `execute_sql_query` | 见下方限量坑 |

## 高频坑

- **结果集也会撑爆上下文**：`execute_sql_query` 返回 CSV，`SELECT *` 大表同样超 token。写查询**默认加 `LIMIT`**，需要全量统计就用聚合（`COUNT`/`GROUP BY`）而非拉全表。**避免拉 PII / BLOB / 大文本列**。
- **写操作要双确认**：`UPDATE`/`DELETE`/`DROP` 前再次核对连接环境和 `WHERE` 条件；能 `SELECT` 预演就先预演。**autocommit 行为不确定时按「立即生效、不可回滚」对待**，不要指望事务兜底。
- 长查询卡住用 `cancel_sql_query`；`list_recent_sql_queries` 可回看刚跑过什么。
