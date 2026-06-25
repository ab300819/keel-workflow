# XDebug 断点调试

> 前提：所有工具显式传 `projectPath`（见 SKILL.md 纪律 1）。下面只讲**决策和坑**，工具参数以 MCP 描述为准。

## 会话生命周期（核心心智模型）

调试器是「监听 + 命中 + 挂起 + 检视 + 释放」的状态机，不是一次性查询：

1. `xdebug_start_debugger_session` — IDE **开始监听**调试连接。它不会自己产生流量。
2. **设断点要在触发代码路径之前**：`xdebug_set_breakpoint`。
3. **必须由外部触发代码执行**才会命中断点——发一个 HTTP 请求 / 跑一条 CLI / 执行一个测试。MCP 自己**不会**制造这次执行，需要你或用户去触发。
4. 轮询 `xdebug_get_debugger_status` 直到状态为**已挂起 (suspended/paused)**，才允许检视。**未挂起时调 get_stack / get_frame_values / evaluate 多半拿不到有效结果。**
5. 检视：`xdebug_get_stack` → 选定栈帧 → `xdebug_get_frame_values` 看该帧变量 → 用 `xdebug_get_value_by_path` 或 `xdebug_evaluate_expression` 下钻复杂对象。
6. 推进：`xdebug_control_session`（resume / step over / step into / step out）；`xdebug_run_to_line` 跑到指定行。
7. **收尾**：`xdebug_remove_breakpoint` 清掉本次断点，结束会话。残留断点会影响**下一次**运行——别留垃圾。

## 高频坑

- **检视前必确认已挂起**：拿不到栈/变量时，第一反应是查 `xdebug_get_debugger_status`，而不是反复重调检视工具。
- **evaluate / frame values 是「当前帧」上下文**：先用 `get_stack` 选对帧，否则取到的是错误作用域的变量。
- **多线程/多请求**：必要时用 `xdebug_get_threads` 确认停在哪个线程/请求上。
- **`set_variable` 会改运行时状态**：用于验证假设很强，但记住它改变了程序行为，结论要据此修正。
- **远程 / 容器调试断点不命中**时，先排查环境而非代码：监听端口对不对、path mapping（容器内路径↔本地路径）是否配好、**容器里跑的代码和本地是否同一版本**（没重新部署就调不到新逻辑）。
- 调完用 `xdebug_list_breakpoints` 核对没有漏删。
