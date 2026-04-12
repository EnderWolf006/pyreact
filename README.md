# Pyreact

面向 **网易我的世界（基岩版）ModSDK** 的 Python UI 声明式渲染框架。

提供类似 React 的组件函数 + Hooks 写法，将组件树（VNode）经过 Diff 与布局计算后，渲染为原生控件集合。

## 特性

- **函数式组件** - 通过 `@Component` 装饰器声明组件
- **Hooks** - `useState` / `useEffect` / `useMemo` / `useCallback` / `useRef`
- **Flexbox 布局** - 支持 `width/height/padding/margin/flexDirection/justifyContent/alignItems` 等
- **基础控件** - `Panel` / `Image` / `Label` / `Button` / `Input` / `Scroll` / `Item`
- **运行时优化** - Typed Grid 批量创建、控件池复用、跨帧延迟渲染

---

## 快速开始

### 1. 集成到你的 AddOn

**行为包（behavior_pack）添加：**
```
pyreact/                    # 框架核心
PyreactRuntimeScript/       # 运行时系统
```

**资源包（resource_pack）的 `ui/` 目录添加：**
```
PyreactBase.json            # 基础控件模板
YourScreen.json             # 你的 Screen 定义
```

### 2. 注册 UI 并显示

```python
# -*- coding: utf-8 -*-
# YourClientSystem.py

import mod.client.extraClientApi as clientApi
ClientSystem = clientApi.GetClientSystemCls()

class YourClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.ListenForEvent(
            clientApi.GetEngineNamespace(),
            clientApi.GetEngineSystemName(),
            'UiInitFinished', self, self.OnUiInitFinished
        )

    def OnUiInitFinished(self, args):
        # 注册 UI
        clientApi.RegisterUI(
            'YourMod', 'YourUI',
            "YourMod.YourScreen.YourScreenNode",
            "YourNamespace.main"
        )
        # 在需要显示的时机显示界面
        clientApi.PushScreen('YourMod', 'YourUI', {"isHud": 1, "data": {}})
```

### 4. 编写组件并挂载

```python
# -*- coding: utf-8 -*-
# YourScreen.py

import mod.client.extraClientApi as clientApi
from pyreact import (
    Component, Panel, Label, Button, Scroll,
    Style, Color, Colors, FontSize,
    AlignItems, JustifyContent, FlexDirection,
    useState, useRef, render_app,
)

ScreenNode = clientApi.GetScreenNodeCls()

@Component
def CounterApp():
    """计数器示例组件"""
    count, set_count = useState(0)
    
    return Panel(
        style=Style(
            width='100%',
            height='100%',
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        children=[
            Label(
                content='Count: %d' % count,
                color=Colors.white,
                fontSize=FontSize.extraLarge,
            ),
            Button(
                style=Style(width=120, height=36, marginTop=16),
                onClick=lambda: set_count(count + 1),
                children=[
                    Label(content='Click Me', color=Colors.white)
                ],
            ),
        ],
    )


class YourScreenNode(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self.app_id = 'your_app_id'

    def Create(self):
        render_app(
            root=CounterApp,
            bind={
                'screen': self,
                'root': '/root',
                'app_id': self.app_id,
                'base_namespace': 'PyreactBase',
            },
        )

    def Destroy(self):
        runtime = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime:
            runtime.UnmountApp({'app_id': self.app_id})
```

---

## 核心 API

### 控件（Primitives）

| 控件 | 说明 | 常用属性 |
|------|------|----------|
| `Panel` | 布局容器（纯布局节点，不创建原生控件） | `style`, `children` |
| `Image` | 图片/色块 | `style`, `src`, `color` |
| `Label` | 文本 | `style`, `content`, `color`, `fontSize` |
| `Button` | 按钮（支持三态） | `style`, `onClick`, `buttonBuilder`, `children` |
| `Input` | 输入框 | `style`, `value`, `onChange`, `placeholder` |
| `Scroll` | 滚动容器 | `style`, `children`, `ref` |
| `Item` | 物品图标 | `style`, `identifier`, `aux`, `itemDict`, `enchant` |

### Hooks

```python
# 状态管理
count, set_count = useState(0)

# 副作用（可选依赖数组）
useEffect(lambda: (print('mounted'), lambda: print('unmount')), [])
useEffect(lambda: print('count changed'), [count])

# 缓存计算
memo_value = useMemo(lambda: expensive_calc(dep), [dep])

# 缓存回调
handler = useCallback(lambda x: process(x, dep), [dep])

# 引用原生控件
scroll_ref = useRef(None)
scroll_ref.current.asScrollView().SetScrollViewPercentValue(0)
```

### 样式（Style）

```python
Style(
    # 尺寸
    width=200,              # 数值或 '100%'
    height=100,
    
    # 间距
    padding=10,             # 统一内边距
    paddingLeft=8,          # 单侧内边距
    margin=12,              # 统一外边距
    marginTop=16,           # 单侧外边距
    
    # Flex 布局
    flexDirection=FlexDirection.row,    # row / column
    justifyContent=JustifyContent.center,  # flex-start / center / flex-end / space-between
    alignItems=AlignItems.center,       # flex-start / center / flex-end / stretch
    
    # 定位
    position=Position.absolute,         # relative / absolute
    left=10,
    top=20,
    
    # 层级
    zIndex=10,
)
```

### 颜色

```python
# 预定义颜色遵循CSS颜色数值
Colors.white          # 白色
Colors.black          # 黑色

# 自定义颜色（ARGB 格式）
Color(0xFF2563EB)     # 蓝色
Color(0x80FF0000)     # 半透明红色
```

### Button 三态

```python
def button_bg_builder(state):
    """按钮背景构建器"""
    colors = {
        ButtonState.default: Color(0xFF2563EB),
        ButtonState.hover: Color(0xFF1D4ED8),
        ButtonState.pressed: Color(0xFF1E40AF),
    }
    return Image(style=Style(width='100%', height='100%'), color=colors[state])

Button(
    style=Style(width=100, height=36),
    buttonBuilder=button_bg_builder,
    onClick=lambda: do_something(),
    children=[Label(content='Click', color=Colors.white)],
)
# 注: 纯色按钮可以用FilledButton组件简化
```

---

## 目录结构

```
pyreact/
├── dsl/                   # DSL 定义（控件、样式、颜色）
├── core/                  # 核心（VNode、Reconciler、Hooks）
├── layout/                # 布局引擎（Flexbox 计算）
└── utils/                 # 工具函数

PyreactRuntimeScript/
├── modMain.py             # 运行时入口
├── PyreactNativeRuntime.py # 原生渲染桥接
└── native_runtime/        # 渲染细节（扁平渲染、属性映射、生命周期）

PyreactExampleScript/
├── modMain.py             # 示例入口
├── PyreactExampleClientSystem.py
├── PyreactExampleUi.py
└── examples/              # 示例组件
    ├── FriendApp.py       # 好友面板（筛选、搜索、详情）
    ├── BedwarStoreApp.py  # 商店界面（分类、Scroll、Item）
    └── BattlePassApp.py   # 战令界面（双档位、任务、奖励）
```

---

## 示例页面

切换示例：修改 `PyreactExampleScript/PyreactExampleUi.py` 中的 `render_app` 调用：

```python
# 切换挂载不同的示例
render_app(root=BattlePassApp, bind=bind)
render_app(root=FriendApp, bind=bind)
render_app(root=BedwarStoreApp, bind=bind)
```

| 示例 | 演示内容 |
|------|----------|
| `FriendApp` | Tab 切换、搜索筛选、列表选择、详情面板、Scroll 滚动、useRef 控制 |
| `BedwarStoreApp` | 商品分类、Item 物品展示、价格标签、购买交互 |
| `BattlePassApp` | 多档位切换、任务列表、等级奖励轨道、Item 奖励 |

---

## JsonUI 配置

### 最简 Screen JSON

你要挂载pyreact的控件一定要继承@PyreactBase.rootBase才能使用
```json
{
    "main": {
        "type": "screen",
        "controls": [
            {
                "root@PyreactBase.rootBase": {}
            }
        ]
    },
    "namespace": "YourNamespace"
}
```


---

## 同步测试

```cmd
sync_to_test.cmd
```

修改脚本参数可覆盖默认同步路径。

