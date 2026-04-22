# 代码结构约定（团队开发约定，非设计决策）

> 本文件从 `templates/design-template.md` §7 剥离。**代码结构是开发约定，不是系统设计决策**——设计文档 §7 只保留"代码落位原则"的一两行文字，具体目录树由团队在开发启动时约定（或由既有代码库习惯驱动），放在本文件作为可选参考。

## 何时使用本文件

- **初始设计阶段**：不要在设计文档中填写完整目录树——只在 §4 模块表指明模块边界、在 §7 写"代码落位原则"即可
- **开发启动时**：团队约定具体目录结构，抄录或引用本文件
- **`/ms-retrofit` 反向同步**：从既有代码提取目录约定，可填回设计文档 §7 的 `<team-specific>` 部分

## 典型目录约定示例（分层架构）

```
src/
├── api/                    # 接口层
│   ├── controllers/        # 控制器
│   │   └── UserController.ts
│   ├── middlewares/        # 中间件
│   │   ├── auth.ts
│   │   └── errorHandler.ts
│   └── validators/         # 请求验证
│       └── userValidator.ts
├── services/               # 服务层
│   ├── interfaces/         # 服务接口
│   │   └── IUserService.ts
│   └── impl/               # 服务实现
│       └── UserService.ts
├── domain/                 # 领域层
│   ├── entities/           # 实体
│   │   └── User.ts
│   ├── value-objects/      # 值对象
│   │   └── Email.ts
│   └── events/             # 领域事件
│       └── UserCreatedEvent.ts
├── infrastructure/         # 基础设施层
│   ├── repositories/       # 仓储实现
│   │   └── UserRepository.ts
│   ├── external/           # 外部服务
│   │   └── EmailService.ts
│   └── config/             # 配置
│       └── database.ts
└── shared/                 # 共享
    ├── types/              # 类型
    ├── utils/              # 工具
    └── constants/          # 常量
```

## 命名约定参考

| 类型 | 后缀 | 示例 |
|------|------|------|
| 服务接口 | `I*` 或 `*Service` | `IUserService` / `UserService` |
| 仓储接口 | `I*Repository` | `IUserRepository` |
| 控制器 | `*Controller` | `UserController` |
| DTO | `*DTO` / `*Dto` | `CreateUserDTO` |
| 实体 | 名词 | `User`、`Order` |
| 值对象 | 名词 | `Email`、`Money` |
| 事件 | `*Event` | `UserCreatedEvent` |
| 异常 | `*Error` / `*Exception` | `ValidationError` |

## 边界约束

- **接口-实现分离**：`services/interfaces/` 与 `services/impl/` 物理隔离
- **模块落位**：设计文档 §4 每个模块对应代码一个子目录或命名空间
- **禁止反向依赖**：`api/` 可依赖 `services/`，反之不行
- **共享层不反向依赖业务**：`shared/` 中不引用 `domain/` 实体

## 不是设计决策的内容

以下内容即使写在本文件也不属于 §7 的一部分：
- 具体文件内的类结构（字段/方法顺序）
- 代码风格（缩进、引号、分号）
- 构建/打包配置
- 测试目录布局（交给测试约定文件）
