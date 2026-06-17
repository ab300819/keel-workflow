# 命名正反例

> 配合 [SKILL.md 命名规范](../SKILL.md#命名规范) 使用。规则与分级以主文件为权威，本文件仅提供示例展开。

## 类 / 接口

```
✅ OrderValidator / PaymentGateway / RetryPolicy   ← 名词短语，描述角色
❌ OrderManager / DataProcessor / CommonHelper / UserInfo   ← 空泛后缀，无信息量
```

## 方法 / 函数

```
✅ sendInvoice(order)        ← 有副作用：动词短语
✅ user.permissions          ← 纯查询：名词（或 getPermissions()，与项目惯例一致）
❌ fetchUser() + getOrder() + retrieveInvoice() 并存   ← 同一动作三个动词，选一个
❌ getUser() 内部写缓存并发埋点   ← get* 带副作用，名实不符（误导名，Blocker）
```

## 变量（长度与作用域成正比）

```
✅ for (let i = 0; i < rows.length; i++)        ← ≤10 行作用域，惯用单字母
✅ const overdueInvoices = ...                  ← 函数级，完整词
✅ export const DEFAULT_RETRY_BACKOFF_MS = ...  ← 导出符号，自含上下文
❌ const data = await fetchOrders()             ← 泛化名作完整名（Blocker）
❌ const ordIdx / usrMgr                        ← 截短单词、自造缩写
❌ 函数体 80 行里复用单字母 t 表示三种含义       ← 大作用域单字母
```

## 布尔

```
✅ isEmpty / hasChildren / canEdit / shouldRetry   ← 读作对主语的断言
❌ isNotReady / disableCheck = false               ← 否定式，调用处出现双重否定
❌ function isValid(): ValidationResult            ← is* 返回非布尔（误导名，Blocker）
```

## 常量

```
✅ const MAX_RETRIES = 5
❌ const FIVE = 5            ← 按值命名
❌ if (attempts > 5)         ← 魔法数字未提取
```

## 同概念漂移（LLM 特有失败模式）

```
❌ 同一实体在三个文件分别叫 user / account / customer
✅ 引入新名词前先 grep 项目词表：
   grep -rn "customer\|account" src/ → 已有 account → 沿用 account
```

## 大小写惯例：沿用项目，不用语言默认

```
✅ 项目既有 camelCase → 新代码 camelCase（即使生成偏好 snake_case）
✅ 项目测试文件用 should_xxx 风格 → 新测试沿用
❌ 同一目录下 getUserById 与 get_order_by_id 并存
```

## 命名空间上下文豁免（导出符号 ≥2 词的例外）

```
✅ Go:    http.Client / bytes.Buffer      ← 包名已提供上下文，Client 单词即可
✅ Swift: Order.Status                    ← 类型命名空间内嵌套类型
❌ TS 顶层 export class Client            ← 无命名空间上下文，应为 ApiClient/HttpClient
```
