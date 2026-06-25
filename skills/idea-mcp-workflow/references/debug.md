# 调试（断点 / XDebug）

> 前提：所有工具显式传 `projectPath`（见 SKILL.md 纪律 1）。下面只讲**决策和坑**，工具参数以 MCP 描述为准。
>
> 工具名虽叫 `xdebug_*`，但**支持 JVM（Java/Kotlin）**，不止 PHP——Java 微服务调试可用。

## 主力场景：调试微服务接口（curl → 断点 → 查库排 bug）

适用「应用已在 IDEA 里以 **Debug 模式**启动」——此时**调试会话已经活着，不要再 `start_debugger_session`**（那是启动/挂接 run configuration，会另起实例）。

1. `xdebug_get_debugger_status` 拿到活动会话（`sessions[]` / `activeSessionId`），确认应用在 debug 下运行。
2. `xdebug_set_breakpoint` 在 handler 行设断点。
   - 接口被高频命中时，加 `condition`（如 `orderId == 123`）只在目标请求停；
   - 看返回的 `lineText` 确认断点落在对的行；`condition` 写错是**异步**报在 `control_session(...).breakpointErrorsTail`，别假设一定生效。
3. **curl 必须后台发**：用 `execute_terminal_command` 跑 `curl ... &`（或后台 bash）。⚠️ 断点命中时服务线程挂起 → **前台同步等 curl 会死锁**（请求 hang 住、你也拿不回控制权）。
4. `xdebug_control_session(action=WAIT_FOR_PAUSE)` 等命中（超时给够，30s–120s 视负载）。**不要靠轮询 `get_debugger_status` 判挂起**——`WAIT_FOR_PAUSE` 才是阻塞等待的正解。
5. 命中后检视：`xdebug_get_stack` → 选定栈帧 → `xdebug_get_frame_values` 看入参/局部变量 → `xdebug_get_value_by_path` 或 `xdebug_evaluate_expression` 下钻复杂对象。
6. 要核对数据状态 → `execute_sql_query` 查库（见 [database.md](database.md)：连接+库+schema 钉死、只读、加 LIMIT）。
7. 定位后 `xdebug_control_session(action=RESUME)`，**紧接再 `WAIT_FOR_PAUSE`** 确认下一次挂起或结束；此时后台 curl 才会返回——看响应是否符合预期。
8. 收尾 `xdebug_remove_breakpoint` 清掉断点（残留会影响下一次请求）。

## 通用控制流要点

- 程序在跑就先 `WAIT_FOR_PAUSE` 或 `PAUSE`，再 `STEP_*` / `RESUME`；`RESUME` 不会自动设断点，没有效断点会一路跑完、会话结束。
- 推进：`STEP_INTO` / `STEP_OVER` / `STEP_OUT`；`run_to_line` 跑到指定行。
- 会话超时/消失后，先 `get_debugger_status` 刷新再用新 `sessionId`。

## 高频坑

- **curl 前台等 = 死锁**（见上，最常踩）。
- **检视前必确认已挂起**：拿不到栈/变量时先确认 `WAIT_FOR_PAUSE` 真的返回了 paused，而不是反复重调检视工具。
- **evaluate / frame values 是「当前帧」上下文**：先 `get_stack` 选对帧，否则取到错误作用域的变量。
- **并发请求**：默认 `suspendPolicy=ALL` 会挂起所有线程；多请求并发时用 `get_threads` 确认停在哪个请求，或对断点用 `THREAD` 策略。
- **`set_variable` 会改运行时状态**：验证假设很强，但它改变了程序行为，结论要据此修正。
- **远程/容器调试断点不命中**：先排环境而非代码——监听端口、path mapping（容器内↔本地路径）、**容器里代码和本地是否同版本**（没重新部署就调不到新逻辑）。
- 调完 `xdebug_list_breakpoints` 核对没漏删。
