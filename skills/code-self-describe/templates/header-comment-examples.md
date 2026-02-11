# 源文件头部注释示例

## 格式规范

头部注释由三行组成，必须放在文件最开始（在 import/require 语句之前）：

```
// INPUT: <依赖模块/服务> (<依赖用途>)
// OUTPUT: <导出函数/类/接口> (<功能描述>)
// POS: <在系统中的角色和位置>
```

| 字段 | 含义 | 来源 |
|------|------|------|
| INPUT | 该文件依赖什么 | 分析 import/require/use 语句 |
| OUTPUT | 该文件提供什么 | 分析 export/pub/public 声明 |
| POS | 该文件在系统中的位置 | 根据目录结构和模块角色推断 |

---

## TypeScript / JavaScript

```typescript
// INPUT: UserRepository (数据访问), ValidatorService (输入校验), bcrypt (密码加密)
// OUTPUT: createUser(), getUser(), updateUser(), deleteUser() (用户 CRUD 操作)
// POS: 用户模块核心服务层，处理用户业务逻辑

import { UserRepository } from './user.repository';
import { ValidatorService } from '../common/validator.service';
import bcrypt from 'bcrypt';

export class UserService {
  // ...
}
```

```typescript
// INPUT: AuthService (认证逻辑), Request (HTTP 请求)
// OUTPUT: AuthGuard (路由守卫中间件)
// POS: 认证模块中间件层，拦截并验证所有需要认证的请求

import { AuthService } from './auth.service';
// ...
```

## Python

```python
# INPUT: user_repository (数据访问), validator (输入校验), bcrypt (密码加密)
# OUTPUT: create_user(), get_user(), update_user(), delete_user() (用户 CRUD 操作)
# POS: 用户模块核心服务层，处理用户业务逻辑

from .user_repository import UserRepository
from common.validator import Validator
import bcrypt
```

## Go

```go
// INPUT: UserRepo (数据访问), Validator (输入校验)
// OUTPUT: CreateUser(), GetUser(), UpdateUser(), DeleteUser() (用户 CRUD 操作)
// POS: 用户模块核心服务层，处理用户业务逻辑

package user

import (
    "context"
    "myapp/internal/validator"
)
```

## Java

```java
// INPUT: UserRepository (数据访问), PasswordEncoder (密码加密)
// OUTPUT: UserService (用户业务服务，提供 CRUD + 状态管理)
// POS: 用户模块核心服务层，处理用户业务逻辑

package com.myapp.modules.user;

import com.myapp.modules.user.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
```

## C# / .NET

```csharp
// INPUT: IUserRepository (数据访问), IPasswordHasher (密码加密)
// OUTPUT: UserService (用户业务服务，提供 CRUD + 状态管理)
// POS: 用户模块核心服务层，处理用户业务逻辑

using MyApp.Modules.User.Repositories;
using MyApp.Common.Security;
```

## Rust

```rust
// INPUT: UserRepository (数据访问), Validator (输入校验)
// OUTPUT: UserService, create_user(), get_user() (用户 CRUD 操作)
// POS: 用户模块核心服务层，处理用户业务逻辑

use crate::modules::user::repository::UserRepository;
use crate::common::validator::Validator;
```

## Swift

```swift
// INPUT: UserRepository (数据访问), Validator (输入校验)
// OUTPUT: UserService (用户业务服务，提供 CRUD 操作)
// POS: 用户模块核心服务层，处理用户业务逻辑

import Foundation
```

## Kotlin

```kotlin
// INPUT: UserRepository (数据访问), PasswordEncoder (密码加密)
// OUTPUT: UserService (用户业务服务，提供 CRUD + 状态管理)
// POS: 用户模块核心服务层，处理用户业务逻辑

package com.myapp.modules.user

import com.myapp.modules.user.UserRepository
```

---

## 特殊情况处理

### 入口文件 (main/index)

```typescript
// INPUT: Express (HTTP框架), routes (路由定义), middleware (中间件)
// OUTPUT: app (应用实例), startServer() (启动函数)
// POS: 应用入口，负责初始化框架、注册路由和启动服务
```

### 纯类型定义文件

```typescript
// INPUT: 无外部依赖
// OUTPUT: User, CreateUserDTO, UserRole (用户相关类型定义)
// POS: 用户模块类型层，定义数据结构和接口契约
```

### 配置文件

```typescript
// INPUT: 环境变量 (DATABASE_URL, JWT_SECRET 等)
// OUTPUT: config (应用配置对象)
// POS: 全局配置层，集中管理环境相关配置
```

### 工具函数文件

```typescript
// INPUT: 无外部依赖
// OUTPUT: formatDate(), parseJSON(), debounce() (通用工具函数)
// POS: 公共工具层，提供跨模块复用的通用函数
```
