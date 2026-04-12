# Pyreact

面向 **网易我的世界（基岩版）ModSDK** 的 Python UI 声明式渲染框架。

提供类似 React 的组件函数 + Hooks 写法，将组件树（VNode）经过 Diff 与布局计算后，渲染为原生控件集合。

## 特性

- **函数式组件** - 通过 `@Component` 装饰器声明组件
- **Hooks** - `useState` / `useEffect` / `useMemo` / `useCallback` / `useRef`
- **Flexbox 布局** - 支持 `width/height/padding/margin/flexDirection/justifyContent/alignItems` 等
- **基础控件** - `Panel` / `Image` / `Label` / `Button` / `Input` / `Scroll` / `Item` / `PaperDoll`
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

### 基础组件（Components）

| 控件 | 说明 | 常用属性 |
|------|------|----------|
| `Panel` | 布局容器（纯布局节点，不创建原生控件） | `style`, `children` |
| `Image` | 图片/色块 | `style`, `src`, `color` |
| `Label` | 文本 | `style`, `content`, `color`, `fontSize` |
| `Button` | 按钮（支持三态） | `style`, `onClick`, `buttonBuilder`, `children` |
| `Input` | 输入框 | `style`, `value`, `onChange`, `placeholder` |
| `Scroll` | 滚动容器 | `style`, `children`, `ref` |
| `Item` | 物品图标 | `style`, `identifier`, `aux`, `itemDict`, `enchant` |
| `PaperDoll` | 纸娃娃 / 实体预览 | `style`, `renderType`, `entityId`, `entityIdentifier`, `skeletonModelName`, `blockGeometryModelName` |

#### `PaperDoll`

`PaperDoll` 对应 `netease_paper_doll_renderer`，运行时会按本地文档映射到以下接口之一：

- `RenderEntity`
- `RenderSkeletonModel`
- `RenderBlockGeometryModel`

参数说明：

| 参数 | 类型 | 说明 |
|------|------|------|
| `style` | `Style` | 控件尺寸/布局，常见至少设置 `width`、`height` |
| `renderType` | `str` | 可选：`RenderType.entity` / `RenderType.skeleton` / `RenderType.blockGeometry` |
| `entityId` | `int` | 通过实体 id 渲染实体模型 |
| `entityIdentifier` | `str` | 通过实体 identifier 渲染实体模型，例如 `minecraft:cow` |
| `skeletonModelName` | `str` | 骨骼模型名，用于 `RenderSkeletonModel` |
| `animation` | `str` | 骨骼模型动画名 |
| `animationLooped` | `bool` | 骨骼动画是否循环 |
| `blockGeometryModelName` | `str` | 方块几何模型名，用于 `RenderBlockGeometryModel` |
| `scale` | `float` | 模型缩放 |
| `renderDepth` | `float` | 渲染深度/前后关系调整 |
| `initRotX` | `float` | 初始 X 轴旋转 |
| `initRotY` | `float` | 初始 Y 轴旋转 |
| `initRotZ` | `float` | 初始 Z 轴旋转 |
| `molangDict` | `dict` | Molang 参数字典 |
| `rotationAxis` | `tuple/list[3]` | 旋转轴向量 `(x, y, z)` |
| `lightDirection` | `tuple/list[3]` | 光照方向，仅骨骼模型渲染有效 |

当前公开支持的 Pyreact props：

- `renderType=RenderType.entity | RenderType.skeleton | RenderType.blockGeometry`
- `entityId` / `entityIdentifier`
- `skeletonModelName`
- `animation` / `animationLooped`
- `blockGeometryModelName`
- `scale`
- `renderDepth`
- `initRotX` / `initRotY` / `initRotZ`
- `molangDict`
- `rotationAxis`
- `lightDirection`（仅骨骼模型渲染有效）

若不显式传 `renderType`，runtime 会按参数自动推断：`entityId/entityIdentifier` > `skeletonModelName` > `blockGeometryModelName`。

常见用法：

#### 1. 实体预览

```python
PaperDoll(
    style=Style(width=120, height=120),
    renderType=RenderType.entity,
    entityIdentifier='minecraft:cow',
    scale=0.8,
    renderDepth=-15,
    initRotY=60,
)
```

#### 2. 骨骼模型预览

```python
PaperDoll(
    style=Style(width=140, height=140),
    renderType=RenderType.skeleton,
    skeletonModelName='custom.skin_preview',
    animation='idle',
    animationLooped=True,
    scale=1.0,
    initRotY=45,
    lightDirection=(0.0, 1.0, 0.0),
)
```

#### 3. 方块几何模型预览

```python
PaperDoll(
    style=Style(width=96, height=96),
    renderType=RenderType.blockGeometry,
    blockGeometryModelName='geometry.custom_hat',
    scale=0.9,
    initRotY=30,
)
```

使用建议：

- 业务侧优先用 `RenderType` 枚举，不要手写裸字符串，避免拼写错误。
- 业务侧优先把 `PaperDoll` 当作“预览控件”使用，始终显式传 `style.width` / `style.height`。
- 实体预览常用 `entityIdentifier`，只有你手里已经有实体 id 时才传 `entityId`。
- `renderDepth`、`scale`、`initRotY` 往往需要一起调，常用于把模型摆进预览框中央。
- 当前 `PaperDoll` 已纳入 runtime grid 池，层级由外层 wrapper panel 承担，不应再依赖 widget 模板里的静态 layer。
- 若出现位置或显示异常，优先检查外层布局尺寸，再检查 `scale` / `renderDepth` / `initRot*`，不要先猜网易 renderer 参数。

注意：当前只暴露了本地文档中确认过的渲染接口参数。`rotation`、`screen_scale` 这类 JSON 模板字段仍由 `PyreactBase.paperDollBase` 固定提供，没有在 Pyreact props 中做动态映射。

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

### 组合组件（Composites）

组合组件基于基础组件封装，提供更高级的抽象，简化常见使用场景。

#### `FilledButton`

`FilledButton` 是对 `Button` 的轻量封装，适合“纯色底板 + 内容”的按钮场景。它会内部生成一个铺满按钮区域的 `Image` 作为背景，并按按钮状态切换颜色。

公开导入方式：

```python
from pyreact import FilledButton
```

参数说明：

| 参数 | 类型 | 说明 |
|------|------|------|
| `default` | `Color` | 默认态背景色 |
| `hover` | `Color` | 悬浮态背景色；不传时会回退到其他已给定状态 |
| `pressed` | `Color` | 按下态背景色；不传时会回退到其他已给定状态 |
| `style` | `Style` | 按钮自身尺寸/布局，背景会自动铺满 `100% x 100%` |
| `children` | `list` | 按钮内部内容，例如 `Label` / `Image` |
| `onClick` | `callable` | 点击回调，和普通 `Button` 一致 |

状态回退规则：

- 只传 `default`：`hover` 和 `pressed` 都会使用 `default`
- 传 `default + pressed`：`hover` 会回退到 `pressed`
- 传 `default + hover`：`pressed` 会回退到 `hover`

常见用法：

```python
FilledButton(
    style=Style(
        width=100,
        height=36,
        alignItems=AlignItems.center,
        justifyContent=JustifyContent.center,
    ),
    default=Color(0xFF2563EB),
    hover=Color(0xFF1D4ED8),
    pressed=Color(0xFF1E40AF),
    onClick=lambda: do_something(),
    children=[
        Label(content='Click', color=Colors.white),
    ],
)
```

仓库内真实示例（`PyreactExampleScript/examples/BedwarStoreApp.py`）：

```python
FilledButton(
    style=Style(
        width=22,
        height=22,
        alignItems=AlignItems.center,
        justifyContent=JustifyContent.center,
    ),
    default=Colors.black.withAlpha(0.2),
    pressed=Colors.black.withAlpha(0.1),
    children=[
        Label(content='x'),
    ],
)
```

使用建议：

- 当你只需要纯色按钮，而不是自定义贴图背景时，优先用 `FilledButton`，比手写 `buttonBuilder` 更直接。
- 按钮尺寸、对齐、margin 等仍然写在外层 `style`；背景层会自动填满，不需要自己再写 `Image(style=Style(width='100%', height='100%'))`。
- 文本、图标等内容仍然通过 `children` 传入，所以它的组合方式和普通 `Button` 完全一致。
- 若你需要的不只是换色，而是不同状态下切贴图/切结构，应该回到 `Button(buttonBuilder=...)`。

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
