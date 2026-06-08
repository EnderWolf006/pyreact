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


## 启用调试功能

调试功能默认关闭（每帧不做任何操作）。必须在挂载时传入 `debug_mode=True`：

```python
render_app(root=MyApp, bind=bind, debug_mode=True)
```

---

## 脚本参考

### launch_game.py

启动 Minecraft 游戏并附带后台常驻 log server，等待 AppReady 信号后退出。**启动前自动杀掉残留的游戏进程和 log_server 进程。**

```
python launch_game.py [--project DIR] [--config FILE] [--port PORT] [--log-output FILE]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--project DIR` | 自动检测 | addon 项目根目录，须含 `studio.json`（注意：`studio.json` 在 addon **上一级**目录，即 addon 本体目录的父目录） |
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
[launch_game] log file: C:\Users\...\AppData\Local\Temp\pyreact-debug\pyreact_game_8765.log
[launch_game] AppReady received, done.
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

通过 HTTP API 从 log server 内存获取游戏日志，支持行号定位、正则过滤和实时跟踪。输出每行带行号，方便用 `--since` 续读。

```
python get_logs.py --port PORT
                   [--tail N | --head N | --lines START[-END] | --since LINENUM]
                   [--grep PATTERN] [--ignore-case]
                   [--follow]
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
| `--follow` | 实时跟踪新日志，每 0.5s 轮询一次（Ctrl+C 停止）；可与 `--tail N` 组合先打印最后 N 行再开始跟踪 |

```bash
python get_logs.py --port 8765 --tail 50
python get_logs.py --port 8765 --since 500
python get_logs.py --port 8765 --grep "ERROR|WARNING" --ignore-case
# 实时跟踪，先显示最后 20 行
python get_logs.py --port 8765 --follow --tail 20
# 实时跟踪 + 只显示 Pyreact 相关日志
python get_logs.py --port 8765 --follow --grep "Pyreact"
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

通过剪切板触发游戏内 UI 树转储，等待结果写回后打印并保存。默认输出美化树形（内部调用 `print_ui_tree.py`），`--json` 改为原始 JSON，`--quiet` 完全静默。

```
python get_ui_tree.py [--app-id APP_ID] [--node-id NODE_ID]
                      [--output FILE] [--timeout SECONDS]
                      [--quiet] [--json]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--app-id APP_ID` | 第一个已挂载的 app | 目标 app |
| `--node-id NODE_ID` | 无（dump 整棵树） | 检查单个节点（含子树） |
| `--output FILE` | `%TEMP%/pyreact-debug/ui_tree.json` | 结果 JSON 保存路径 |
| `--timeout SECONDS` | `10` | 等待游戏响应的超时秒数 |
| `--quiet` | false | 不打印到 stdout（文件仍会保存） |
| `--json` | false | 输出原始 JSON 而非美化树形（`--quiet` 时忽略） |

```bash
python get_ui_tree.py                          # 整棵树，打印美化树形
python get_ui_tree.py --json                   # 整棵树，打印原始 JSON
python get_ui_tree.py --quiet                  # 只保存文件，不打印
python get_ui_tree.py --node-id panel_0        # 单节点子树，打印美化树形
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

以 UTF-8 安全的树形格式打印已保存的 UI 树 JSON，显示节点类型、id、关键 props（Label 的 `content`、Image 的 `src`、Item 的 `item_name`）、layout 和交互标记（`[clickable]`/`[input]`）。`--json` 输出原始 JSON。

```
python print_ui_tree.py [FILE] [--node-id NODE_ID] [--depth N] [--json]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FILE` | `%TEMP%/pyreact-debug/ui_tree.json` | UI 树 JSON 文件 |
| `--node-id NODE_ID` | 无（从根打印） | 从指定节点开始打印子树 |
| `--depth N` | 无限制 | 最多打印到第 N 层 |
| `--json` | false | 输出原始 JSON 而非美化树形 |

```bash
python print_ui_tree.py                              # 打印默认文件的树
python print_ui_tree.py --json                       # 输出原始 JSON
python print_ui_tree.py --node-id panel_left         # 只打印子树
python print_ui_tree.py --depth 2                    # 只打印前两层
```

输出示例：
```
`-- root (Image) 609x429 @(0,0)
    |-- p_0 (Panel) 368x429 @(0,0)
    |   |-- k_mode_bedwar (Button) 80x30 @(10,10) [clickable]
    |   |-- k_label_title (Label) "空岛战争 · 最后生还·4人" 200x20 @(10,50)
    |   `-- p_0_8 (Button) 100x36 @(10,380) [clickable]
    `-- p_2 (Panel) 240x429 @(369,0)
        |-- p_2_2_1 (Input) 200x28 @(10,40) [input]
        `-- k_inv_f_nova (Button) 220x36 @(10,100) [clickable]
```

---

### diff_ui_tree.py

对比两个 UI 树 JSON 快照，输出新增/删除/变更的节点。节点以完整路径（`parent/child`）为 key，避免重复 id 覆盖。

```
python diff_ui_tree.py <before.json> <after.json> [--props] [--layout]
```

| 参数 | 说明 |
|------|------|
| `before.json` | 交互前的树快照 |
| `after.json` | 交互后的树快照 |
| `--props` | 在 changed 输出中包含 props 对比 |
| `--layout` | 在 changed 输出中包含 layout 对比 |

输出（JSON 到 stdout，摘要到 stderr）：
```json
{
  "added": ["root/panel_right/k_slot_f_nova"],
  "removed": [],
  "changed": [
    {"path": "root/panel_left/p_0_8", "before": {"type": "Button"}, "after": {"type": "Button"}}
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

### simulate_and_diff.py ⭐

**一步完成：操作 + 等待 + diff**，是交互测试的推荐工具。内部自动完成 before 快照 → simulate → settle → after 快照 → diff，无需手动管理文件。

```
python simulate_and_diff.py <action> --node-id NODE_ID [--app-id APP_ID]
                            [--text TEXT] [--timeout N] [--settle N]
                            [--props] [--layout]
                            [--output-before FILE] [--output-after FILE]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `action` | 必填 | `click` 或 `input` |
| `--node-id NODE_ID` | 必填 | 目标节点 id |
| `--app-id APP_ID` | 第一个挂载的 app | 目标 app |
| `--text TEXT` | `""` | 输入内容（`input` 专用） |
| `--timeout N` | `5.0` | 等待 ack/树响应的超时秒数 |
| `--settle N` | `0.5` | 操作后等待 UI 稳定的秒数 |
| `--props` | false | diff 输出包含 props 对比 |
| `--layout` | false | diff 输出包含 layout 对比 |
| `--output-before FILE` | 不保存 | 保存 before 快照到文件 |
| `--output-after FILE` | 不保存 | 保存 after 快照到文件 |

```bash
# 点击按钮并查看 diff
python simulate_and_diff.py click --node-id k_mode_skywar --props

# 输入文本并查看 diff（含 layout 变化）
python simulate_and_diff.py input --node-id search_input --text "Nova" --props --layout

# 保存快照供后续分析
python simulate_and_diff.py click --node-id ready_btn --output-before before.json --output-after after.json --props
```

输出（JSON 到 stdout，进度到 stderr）：
```json
{
  "added": [],
  "removed": [],
  "changed": [
    {
      "path": "root/p_0/p_0_8/p_0_8_0",
      "before": {"type": "Label", "props": {"content": "✔  准备", "color": "#ffffffff"}},
      "after":  {"type": "Label", "props": {"content": "取消准备", "color": "#ffffffff"}}
    }
  ]
}
```

> **props 自动过滤**：`buttonBuilder`/`onClick` 等序列化为 `<function ...>` 字符串的闭包 props 会被自动剔除，diff 输出只包含真实数据变化，不会被每次渲染重建的内存地址污染。

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

### UI 树检查

```bash
# 直接打印美化树形（推荐）
python get_ui_tree.py
# 只看前两层
python get_ui_tree.py --node-id p_0 --depth 2
# 需要原始 JSON 时
python get_ui_tree.py --json
# 只保存文件不打印
python get_ui_tree.py --quiet
```

### 交互后验证 UI 变更（推荐）

**用 `simulate_and_diff.py`，一条命令搞定**：

```bash
# 点击按钮，查看 props 变化
python simulate_and_diff.py click --node-id k_mode_skywar --props

# 输入文本，查看列表过滤结果
python simulate_and_diff.py input --node-id search_input --text "Nova" --props

# 保存快照供后续 debug
python simulate_and_diff.py click --node-id ready_btn --props \
    --output-before before.json --output-after after.json
```

如需手动分步（例如操作和验证之间有复杂交互）：

```bash
python get_ui_tree.py --quiet --output before.json
python simulate.py click --node-id some_button
python get_ui_tree.py --quiet --output after.json
python diff_ui_tree.py before.json after.json --props
```

### 续读日志（不重复拉取）

```bash
# 第一次拉取，记录输出的 total 行号
python get_logs.py --port 8765 --tail 50
# 之后从上次结束位置续读
python get_logs.py --port 8765 --since <上次 total+1>
# 只看 ERROR/WARNING
python get_logs.py --port 8765 --tail 100 --grep "ERROR|WARNING" --ignore-case
```
