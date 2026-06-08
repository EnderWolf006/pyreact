---
name: pyreact-debug
description: 调试运行在网易我的世界基岩版 ModSDK 中的 Pyreact UI 框架。提供游戏启动、日志流、热重载、UI 树检查、性能 profile 工作流，可以使 AI Agent 更高效地测试，定位，和修复 UI 相关问题。
compatibility: opencode
metadata:
  audience: agents
  domain: pyreact-debug
  platform: netease-minecraft-bedrock-modsdk
---

## 我能做什么

- 启动携带日志服务的游戏实例（自动生成 `.cppconfig`，无需依赖 mcpywrap）
- 实时流式接收游戏日志，log server 跟随游戏进程生命周期自动退出
- 热重载行为包脚本、重启世界
- 通过剪切板触发协议检查 Pyreact UI 树 / 子树 / 节点 props
- 模拟按钮点击、输入框输入
- 启停 engine / 脚本 / 内存性能 profile

## 什么时候使用

- 需要启动游戏进行 Pyreact UI 调试
- 检查运行时 UI 树结构（节点类型、props、layout）
- 做 engine 或脚本性能分析
- 热重载脚本或重启世界
- 模拟 UI 交互（点击、输入）
- 定位 Pyreact 渲染 bug（节点未渲染、布局异常、props 未生效）

## 通信架构

```
外部脚本 ──剪切板触发 JSON──▶ 游戏 GameRenderTickEvent 轮询
                              │  执行 DebugDump* / DebugClick / DebugSetInput
外部脚本 ◀──结果 JSON ────────┘  SetClipboardContent(result 或 __pyreact_ack__)

外部脚本 ──HTTP POST /send_command──▶ log server ──TCP null-terminated──▶ 游戏
游戏日志  ──TCP stream──────────────▶ log server（日志存内存 + 写文件）
外部脚本 ──HTTP GET  /logs──────────▶ log server（从内存返回）
```

- UI 检查/交互命令走剪切板通道（`clipboard_ipc.py` 封装，使用 pyperclip）
- `reload_pack` 等 studio 命令走 HTTP `/send_command` → log server → TCP 反向通道
- 日志通过 HTTP `/logs` 从 log server 内存获取，**不直接读文件**
- log server **跟随游戏进程生命周期不关闭**（`--game-pid` 仅用于监控游戏状态，不触发退出）
- HTTP API 监听在 `port+1`

## 框架侧变更

`PyreactRuntimeScript/` 已有以下调试支持（框架修改，非外部脚本）：
- `PyreactNativeRuntime.py`：`_sanitize`、`_serialize_shadow_node`、`debug_get_ui_tree/subtree/node_props`
- `PyreactRuntimeClientSystem.py`：`_poll_debug_clipboard`（每帧调用）、`DebugDumpUiTree/Subtree/NodeProps`、`DebugClickButton`、`DebugSetInput`
- `native_runtime/lifecycle_mixin.py`：首次渲染完成后打印 `=====> PyreactRuntime AppReady: <app_id> <=====`

## 启用调试功能

调试功能默认关闭（每帧不做任何操作）。必须在挂载时传入 `debug_mode=True`：

```python
render_app(root=MyApp, bind=bind, debug_mode=True)
```

---

## 脚本参考

### launch_game.py

启动 Minecraft 游戏并附带 detached log server，等待 AppReady 信号后退出。

```
python launch_game.py [--project DIR] [--config FILE] [--port PORT] [--log-output FILE]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--project DIR` | 自动检测 | addon 项目根目录，须含 `studio.json` |
| `--config FILE` | 自动发现 | 直接指定 `.cppconfig` 路径，跳过自动生成 |
| `--port PORT` | 随机 | log server 监听端口 |
| `--log-output FILE` | `%TEMP%/pyreact-debug/pyreact_game_<port>.log` | 日志持久化路径 |

`--project` 省略时的自动检测顺序：
1. 当前目录有 `studio.json` → 直接使用
2. 当前目录是 pyreact 框架根（有 `sync_to_test.cmd`）→ 解析 `TARGET_ROOT`，打印 addon 路径后退出提示
3. 否则报错退出

`--config` 省略时：扫描 `<project>/.runtime/*.cppconfig` 取最新文件；找不到则调用 `setup_runtime()` 自动生成（读 `studio.json` + 注册表）。

脚本输出端口和日志路径，后续命令需要这两个值：
```
[launch_game] log server port: 8765
[launch_game] log file: C:\Users\...\AppData\Local\Temp\pyreact_game_8765.log
```

---

### kill_game.py

杀掉所有 `Minecraft.Windows.exe` 进程。log server 检测到游戏 PID 消失后自动退出。

```
python kill_game.py [--wait]
```

| 参数 | 说明 |
|------|------|
| `--wait` | 等待进程完全消失后再返回（轮询最多 15 秒） |

---

### get_logs.py

通过 HTTP API 从 log server 内存获取游戏日志，支持行号定位和正则过滤。输出每行带行号，方便用 `--since` 续读。

```
python get_logs.py --port PORT
                   [--tail N | --head N | --lines START[-END] | --since LINENUM]
                   [--grep PATTERN] [--ignore-case]
```

| 参数 | 说明 |
|------|------|
| `--port PORT` | 必填，log server 端口（`launch_game.py` 输出的端口） |
| `--tail N` | 最后 N 行 |
| `--head N` | 前 N 行 |
| `--lines START[-END]` | 行号区间，1-based（如 `100-200` 或单行 `300`） |
| `--since LINENUM` | 从第 LINENUM 行起往后，1-based |
| `--grep PATTERN` | 正则过滤，只返回匹配行 |
| `--ignore-case` | 与 `--grep` 配合，大小写不敏感 |

```bash
python get_logs.py --port 8765 --tail 50
python get_logs.py --port 8765 --lines 100-200
python get_logs.py --port 8765 --since 500
python get_logs.py --port 8765 --grep "PyreactRuntime"
python get_logs.py --port 8765 --tail 200 --grep "ERROR" --ignore-case
```

---

### send_command.py

通过 log server HTTP API 向游戏发送 studio 命令。

```
python send_command.py --port PORT <command> [args...]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--port PORT` | 必填 | log server 端口（`launch_game.py` 输出的端口） |
| `command` | 必填 | 命令字符串，多个词会 join 成一条命令 |

```bash
python send_command.py --port 8765 reload_pack
python send_command.py --port 8765 restart_local_game
python send_command.py --port 8765 release_mouse
```

---

### perf.py

性能 profile 快捷方式，内部调用 `send_command.py`。

```
python perf.py --port PORT <action>
```

| action | 发送的命令组合 | 说明 |
|--------|--------------|------|
| `start` | `begin_performance_profile` + `start_profile` | 同时开始 engine + 脚本 profile |
| `stop` | `end_performance_profile` + `stop_profile` + `log_performance_profile_data` | 停止并打印结果 |
| `script-start` | `start_profile` | 仅脚本 profile |
| `script-stop` | `stop_profile` | 仅停止脚本 profile |
| `mem-start` | `start_mem_profile` | 内存 profile |
| `mem-stop` | `stop_mem_profile` | 停止内存 profile |
| `dump` | `log_performance_profile_data` | 打印当前数据到游戏日志 |

```bash
python perf.py --port 8765 start
# ... 在游戏中操作 ...
python perf.py --port 8765 stop
python get_logs.py --tail 100 --grep "profile"
```

---

### get_ui_tree.py

通过剪切板触发游戏内 UI 树转储，等待结果写回后打印并保存。

```
python get_ui_tree.py [--app-id APP_ID] [--node-id NODE_ID] [--subtree]
                      [--output FILE] [--timeout SECONDS] [--quiet]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--app-id APP_ID` | 第一个已挂载的 app | 目标 app |
| `--node-id NODE_ID` | 无（dump 整棵树） | 检查单个节点的 props |
| `--subtree` | false | 与 `--node-id` 配合，dump 子树而非仅 props |
| `--output FILE` | `%TEMP%/pyreact-debug/ui_tree.json` | 结果 JSON 保存路径（同时打印到 stdout） |
| `--timeout SECONDS` | `10` | 等待游戏响应的超时秒数 |
| `--quiet` | false | 不打印 JSON 到 stdout（文件仍会保存） |

> **编码注意**：Windows 默认 stdout 为 GBK。`get_ui_tree.py` 已使用 `sys.stdout.buffer.write(...encode('utf-8'))` 规避崩溃。
> Agent 推荐工作流：用 `--quiet` 静默保存，再用 `print_ui_tree.py` 读文件打印，或直接读已保存的 JSON 文件分析。

```bash
python get_ui_tree.py                                          # 整棵树
python get_ui_tree.py --app-id my_app --output tree.json      # 指定 app，保存
python get_ui_tree.py --node-id panel_0                       # 单节点 props
python get_ui_tree.py --node-id panel_0 --subtree             # 子树
```

节点结构：
```json
{
  "id": "panel_0",
  "type": "Panel",
  "props": {},
  "style": {"width": 100},
  "opacity": 1.0,
  "layout": {"x": 0, "y": 0, "width": 100, "height": 50},
  "children": [...]
}
```

---

### print_ui_tree.py

以 ASCII 安全的树形格式打印已保存的 UI 树 JSON，显示节点类型、id、layout 和交互标记。

```
python print_ui_tree.py [FILE] [--node-id NODE_ID] [--depth N]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FILE` | `%TEMP%/pyreact-debug/ui_tree.json` | UI 树 JSON 文件（`get_ui_tree.py` 保存的默认位置） |
| `--node-id NODE_ID` | 无（从根打印） | 从指定节点开始打印子树 |
| `--depth N` | 无限制 | 最多打印到第 N 层 |

```bash
python print_ui_tree.py                              # 打印默认临时文件的树
python print_ui_tree.py tree_before.json             # 打印指定文件
python print_ui_tree.py --node-id panel_left         # 只打印 panel_left 子树
python print_ui_tree.py --depth 2                    # 只打印前两层
```

输出示例：
```
`-- root (Panel) 653x429 @(0,0)
    |-- panel_left (Panel) 412x429 @(0,0)
    |   |-- k_mode_bedwar (Button) 80x30 @(10,10) [clickable]
    |   `-- search_input (Input) 200x28 @(10,50) [input]
    `-- panel_right (Panel) 240x429 @(413,0)
```

---

### diff_ui_tree.py

对比两个 UI 树 JSON 快照，输出新增/删除/变更的节点。用于验证交互后 UI 是否按预期更新。

```
python diff_ui_tree.py <before.json> <after.json> [--props] [--layout]
```

| 参数 | 说明 |
|------|------|
| `before.json` | 交互前的树快照 |
| `after.json` | 交互后的树快照 |
| `--props` | 在 changed 输出中包含 props 对比 |
| `--layout` | 在 changed 输出中包含 layout 对比 |

```bash
# 先保存交互前快照
python get_ui_tree.py --quiet --output before.json
# 执行交互
python simulate.py click --node-id k_mode_skywar
# 再保存交互后快照
python get_ui_tree.py --quiet --output after.json
# 对比
python diff_ui_tree.py before.json after.json --props
```

输出（JSON 到 stdout，摘要到 stderr）：
```json
{
  "added": ["new_node_id"],
  "removed": ["old_node_id"],
  "changed": [
    {"id": "label_mode", "before": {"type": "Text", "props": {"text": "床战"}}, "after": {"type": "Text", "props": {"text": "空岛战争"}}}
  ]
}
```

---

### simulate.py

通过剪切板触发游戏内按钮点击或输入框文本设置，等待游戏写回 `__pyreact_ack__` 确认。

```
python simulate.py <action> --node-id NODE_ID [--app-id APP_ID] [--text TEXT] [--timeout SECONDS]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `action` | 必填 | `click`（触发 `onClick`）或 `input`（设置文本并触发 `onChange`） |
| `--node-id NODE_ID` | 必填 | 目标节点 id，从 `get_ui_tree.py` 获取 |
| `--app-id APP_ID` | 第一个已挂载的 app | 目标 app |
| `--text TEXT` | `""` | 输入内容（`input` 专用） |
| `--timeout SECONDS` | `5` | 等待 `__pyreact_ack__` 的超时秒数 |

```bash
python simulate.py click --node-id submit_btn
python simulate.py input --node-id search_input --text "hello world"
python simulate.py click --node-id ok_btn --app-id my_app --timeout 10
```

---

## 剪切板触发协议

外部写入的触发 JSON 格式：

```json
{"pyreact_debug": "dump_tree",    "params": {"app_id": "my_app"}}
{"pyreact_debug": "dump_subtree", "params": {"app_id": "my_app", "node_id": "panel_0"}}
{"pyreact_debug": "click",        "params": {"node_id": "submit_btn"}}
{"pyreact_debug": "set_input",    "params": {"node_id": "search_input", "text": "hello"}}
```

> **注意**：`dump_node` 命令已废弃——游戏侧序列化时 `buttonBuilder`（函数）无法 JSON 化，导致报错且不写回剪切板。`get_ui_tree.py --node-id` 已改为统一使用 `dump_subtree`。

游戏在下一个 `GameRenderTickEvent` 检测到 `pyreact_debug` 字段后：
- dump 命令：执行 → 写结果 JSON 回剪切板
- click / set_input：执行 → 写 `__pyreact_ack__` 回剪切板

非 `pyreact_debug` 内容直接跳过，不影响正常剪切板使用。

## Studio 命令参考

| 命令 | 作用 |
|------|------|
| `reload_pack` | 热重载行为包脚本 |
| `reload_cache` | 从 pack cache 热重载 |
| `restart_local_game` | 重载当前世界 |
| `begin_performance_profile` | 开始 engine perf profile |
| `end_performance_profile` | 结束 engine perf profile |
| `log_performance_profile_data` | 打印 perf 数据到游戏日志 |
| `start_profile` | 开始脚本 profile |
| `stop_profile` | 停止脚本 profile |
| `start_mem_profile` | 开始内存 profile |
| `stop_mem_profile` | 停止内存 profile |
| `release_mouse` | 释放鼠标捕获 |
| `create_world` | 创建新世界 |

## 重要约束

- 框架代码用 **Python 2** 语法（无 f-string，无类型注解，`print` 为语句）
- UI 检查/交互命令只能通过剪切板触发，不能走 TCP 反向通道
- Studio 命令（`reload_pack` 等）通过 HTTP `/send_command` → log server → TCP 反向通道
- `get_logs.py` 必须通过 HTTP API 获取日志，不直接读文件
- `get_ui_tree.py` / `simulate.py` 的剪切板操作通过 `clipboard_ipc.py`（pyperclip）完成
- `setup_runtime()` 依赖 Windows 注册表（`HKCU\Software\Netease\MCStudio`），仅支持 Windows
- `debug_mode=True` 必须在挂载时传入，运行时无法动态开启
- log server 跟随游戏进程生命周期**不退出**；`--game-pid` 仅用于监控游戏状态
- HTTP API 在 `port+1` 上监听；`get_logs.py` / `send_command.py` 均使用此端口
- 需安装依赖：`pip install pyperclip psutil`

## Agent 推荐工作流

### UI 树检查（编码安全）

```bash
# 1. 静默保存到文件（规避 Windows GBK stdout 崩溃）
python get_ui_tree.py --quiet --output tree.json
# 2. 用脚本打印可读格式（不会崩溃）
python print_ui_tree.py tree.json
# 或直接读 JSON 文件分析（推荐，最可靠）
```

> 不要直接 `python get_ui_tree.py` 不加 `--quiet` 在 Windows 上打印含中文的树——GBK stdout 会崩溃。

### 交互后验证 UI 变更

```bash
python get_ui_tree.py --quiet --output before.json
python simulate.py click --node-id some_button
python get_ui_tree.py --quiet --output after.json
python diff_ui_tree.py before.json after.json --props
```

### 续读日志（不重复拉取）

```bash
# 第一次：记录最后行号
python get_logs.py --port 8765 --tail 50
# 之后续读
python get_logs.py --port 8765 --since 51
```
