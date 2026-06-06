# pyreact-debug

调试运行在网易我的世界基岩版 ModSDK 中的 Pyreact UI 框架的技能。

## 概述

通信架构：**剪切板作为双向通道**
- 外部工具写触发 JSON → 游戏每帧轮询剪切板 → 执行调试命令 → 写结果 JSON 回剪切板

日志流：游戏启动时携带 `loggingIP=localhost loggingPort=N`，外部 TCP server 接收日志。  
Studio 命令（reload_pack 等）：通过 TCP 反向通道发送 null-terminated 字符串。  
UI 检查命令：只能通过剪切板触发（TCP 反向通道是引擎层，ModSDK 脚本层无法监听）。

## 文件结构

```
.agents/skills/pyreact-debug/scripts/
  _mcs.py          Windows 注册表：查找 MC Studio / Minecraft.Windows.exe 路径；setup_runtime() 自动生成 .cppconfig
  launch_game.py   启动游戏 + 启动 log server
  kill_game.py     杀掉 Minecraft.Windows.exe 进程
  log_server.py    TCP log server（接收游戏日志 + 发送 studio 命令）
  send_command.py  向游戏发送 null-terminated studio 命令
  perf.py          性能 profile 命令快捷方式
  get_ui_tree.py   写触发 JSON 到剪切板 → 等待游戏写回结果 → 打印/保存
```

框架侧变更（`PyreactRuntimeScript/`）：
- `PyreactNativeRuntime.py`：`_serialize_shadow_node`, `debug_get_ui_tree`, `debug_get_subtree`, `debug_get_node_props`
- `PyreactRuntimeClientSystem.py`：`_poll_debug_clipboard`（在 `GameRenderTickEvent` 首行调用）、`DebugDumpUiTree/Subtree/NodeProps`

## 常用工作流

### 1. 启动游戏并流日志
```bash
cd .agents/skills/pyreact-debug/scripts

# 自动发现/生成 .cppconfig（推荐）
python launch_game.py --project "D:/path/to/addon_project" --port 8765

# 或手动指定已有 .cppconfig
python launch_game.py --config "D:/path/to/project.cppconfig" --port 8765
```

`--project` 指向含 `studio.json` 的 addon 项目根目录。若未指定，按以下顺序自动检测：
1. **当前目录有 `studio.json`** → 直接使用
2. **当前目录是 pyreact 框架根**（有 `sync_to_test.cmd`）→ 解析其中的 `TARGET_ROOT`，打印 addon 项目路径并退出，提示在那里重新运行
3. 否则回退到 pyreact 框架根目录

若目标目录下没有 `.runtime/*.cppconfig`，会自动调用 `setup_runtime()` 生成一个（自动发现 behavior_pack / resource_pack、创建 AppData symlink、写入 engine 版本等）。

### 2. 热重载脚本
```bash
python send_command.py --port 8765 reload_pack
```

### 3. 获取 UI 树
```bash
# 第一个已挂载 app 的完整树
python get_ui_tree.py --output tree.json

# 指定 app
python get_ui_tree.py --app-id my_app --output tree.json

# 单个节点 props
python get_ui_tree.py --node-id panel_0 --output node.json

# 子树
python get_ui_tree.py --node-id panel_0 --subtree --output subtree.json
```

### 4. 性能 profile
```bash
python perf.py --port 8765 start   # 开始 profile
# ... 操作游戏 ...
python perf.py --port 8765 stop    # 停止并打印结果到游戏日志
```

### 5. 关掉游戏
```bash
python kill_game.py
```

## 剪切板触发协议

外部写入：
```json
{"pyreact_debug": "dump_tree", "params": {"app_id": "my_app"}}
{"pyreact_debug": "dump_subtree", "params": {"app_id": "my_app", "node_id": "panel_0"}}
{"pyreact_debug": "dump_node", "params": {"node_id": "panel_0"}}
```

游戏在下一个 `GameRenderTickEvent` 中检测到 `pyreact_debug` 字段后执行，清空触发内容，将结果 JSON 写回剪切板。

## UI 树节点结构

```json
{
  "id": "panel_0",
  "type": "Panel",
  "props": {},
  "style": {},
  "opacity": 1.0,
  "layout": {"x": 0, "y": 0, "width": 100, "height": 50},
  "children": [...]
}
```

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

## 重要约束

- 框架代码用 **Python 2** 语法（无 f-string，无类型注解）
- UI 检查命令只能通过剪切板触发，**不能**走 TCP 反向通道（引擎层内部）
- Studio 命令（reload_pack 等）只能走 TCP 反向通道，**不需要**剪切板
- `_poll_debug_clipboard` 检测到非 pyreact_debug 内容时直接返回，不影响正常剪切板使用
