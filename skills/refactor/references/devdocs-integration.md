# keel 集成

## 在 keel 流程中的位置

```
keel 工作流（含重构）:

新项目:
/requirements → /system-design → /test-cases → /dev-tasks
                                                                              │
                                                                              ▼
                                                                           开发实现
                                                                    ┌────────┼────────┐
                                                                    ▼        ▼        ▼
                                                              /code-quality /ui-orchestrator /refactor
                                                                                        │
已有项目:                                                                               │
/retrofit ←─────────────────────────────────────────────────────────────────────┘
       │                                                              (不可测试时)
       ▼
  标准化文档 → 重新实现
```

## 与其他 Skills 的调用关系

```
/refactor
    │
    ├── 代码审查 → /code-quality (MTE 原则)
    │
    ├── UI 重构 → /ui-orchestrator (UI 约束)
    │
    ├── 不可测试 → /retrofit (建基线) → 确认目标行为
    │                    │
    │                    ├── /requirements
    │                    ├── /system-design
    │                    └── /test-cases
    │
    ├── 测试编写 → /testing-guide（测试质量约束；需要用例文档时再用 /test-cases）
    │
    └── 重构完成 → /code-self-describe --update (更新模块自描述)
```
