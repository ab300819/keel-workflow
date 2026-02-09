# 任务归档规则

任务归档功能已整合到 `/devdocs-sync --archive` 统一归档体系中。

详见 [devdocs-sync/archive.md](../devdocs-sync/archive.md)

## 快速参考

**归档命令**：

```bash
/devdocs-sync --archive tasks    # 仅归档任务
/devdocs-sync --archive          # 全量归档（包含任务）
```

**触发条件**：
- 主文档超过 **300 行**
- 已完成任务超过 **15 个**

**主文档保留**：
- 所有"待开发"和"进行中"任务
- 最近完成的 **5 个任务**
- 执行检查清单

**归档文件**：`docs/devdocs/archive/04-dev-tasks-archive.md`
