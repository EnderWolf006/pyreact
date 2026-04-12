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

### 基础组件（Primitives）

#### `Panel`

`Panel` 是最基础的布局容器，只参与布局和 children 组织，不会单独创建原生 `panel` 控件。

常用 props：

- `style`
- `children`

要点：

- `Panel` 的子节点会直接继承当前挂载目标，例如 `root` 或最近的 `scroll_content`
- 适合做横纵布局、包裹节点、绝对定位容器

#### `Image`

`Image` 用于贴图、纯色底板、图标和按钮背景。

常用 props：

- `style`
- `src`
- `color`
- `grayscale`
- `clipRatio`
- `uv` / `uvSize`
- `resizeMode`
- `imageAdaptionType`
- `nineSlice` / `nineSliceType`
- `rotation` / `rotatePivot`
- `children`
- `onClick`

要点：

- 图片渲染相关能力走 props，不走 `style`
- `src` 为空时，runtime 会回退到 `textures/ui/white_bg`

#### `Label`

`Label` 用于文本展示。

常用 props：

- `style`
- `content`
- `color`
- `fontSize`
- `textAlign`
- `linePadding`
- `shadow`

要点：

- 文本内容和文本样式走 props
- 位置、尺寸、margin 等布局能力仍然写在 `style`
- 手动换行使用 `\n`

#### `Item`

`Item` 用于渲染物品图标，对应 `inventory_item_renderer`。

常用 props：

- `style`
- `children`
- `identifier`
- `aux`
- `enchant`
- `userData`
- `itemDict`

要点：

- 可直接传扁平 props
- 也可传 `itemDict`，runtime 会兼容常见的物品字段命名

#### `Button`

`Button` 是可点击容器，支持 `default / hover / pressed` 三态。

常用 props：

- `style`
- `children`
- `onClick`
- `buttonBuilder`

要点：

- 不传 `buttonBuilder` 时，runtime 会使用默认三态背景
- 传 `buttonBuilder` 时，通常写成 `lambda state: Image(...)` 或 `def builder(state): ...`

#### `Input`

`Input` 用于文本输入。

常用 props：

- `style`
- `value`
- `onChange`
- `placeholder`
- `children`

要点：

- `value + onChange` 是受控写法
- 只传 `onChange` 或不传 `value` 时，runtime 会尽量保持非受控输入内容

#### `Scroll`

`Scroll` 用于滚动列表容器。

常用 props：

- `style`
- `children`
- `showScrollbar`
- `ref`

要点：

- 子节点会渲染到 `scroll_content`
- 需要滚动控制时，给 `Scroll(ref=...)` 再调用底层 scroll 接口

#### `PaperDoll`

`PaperDoll` 对应 `netease_paper_doll_renderer`，用于实体、骨骼模型和方块几何模型预览。

常用 props：

- `style`
- `renderType`
- `entityId` / `entityIdentifier`
- `skeletonModelName`
- `animation` / `animationLooped`
- `blockGeometryModelName`
- `scale`
- `renderDepth`
- `initRotX` / `initRotY` / `initRotZ`
- `molangDict`
- `rotationAxis`
- `lightDirection`

要点：

- runtime 会按参数映射到 `RenderEntity` / `RenderSkeletonModel` / `RenderBlockGeometryModel`
- 若不显式传 `renderType`，会按 `entityId/entityIdentifier`、`skeletonModelName`、`blockGeometryModelName` 自动推断
- 当前只暴露了已在本地文档确认的渲染参数；`rotation`、`screen_scale` 这类模板字段没有作为业务 props 暴露

### 组合组件（Composites）

#### `FilledButton`

`FilledButton` 是对 `Button` 的纯色封装，适合“纯色底板 + 内容”的按钮场景。

常用 props：

- `style`
- `default`
- `hover`
- `pressed`
- `children`
- `onClick`

要点：

- 可直接 `from pyreact import FilledButton`
- 内部会生成一个铺满按钮区域的 `Image` 作为背景，并按按钮状态切换颜色
- `hover` / `pressed` 缺失时会自动回退到已给定状态

#### `ImageButton`

`ImageButton` 是对 `Button` 的图片态封装，适合“给三态贴图值，再由 builder 生成背景图”的场景。

常用 props：

- `style`
- `default`
- `hover`
- `pressed`
- `imageBuilder`
- `children`
- `onClick`

要点：

- `default` / `hover` / `pressed` 负责提供三态贴图路径
- `imageBuilder(src)` 是更常用的主写法；需要区分状态时可写成 `imageBuilder(src, state)`
- 返回的 `Image` 会自动注入 `width='100%'` 和 `height='100%'`
- `hover` / `pressed` 缺失时会自动回退到已给定状态

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

### `clone_component`

`clone_component` 用于基于现有 `ComponentNode` 创建一个新的组件节点副本，并按需覆盖部分 props。它适合像 `ImageButton` 这类“拿模板节点做变体”的场景，避免直接修改原节点带来的共享引用污染。

公开导入方式：

```python
from pyreact import clone_component
```

常见用法：

```python
base_image = Image(
    style=Style(width='100%', height='100%'),
    src='textures/ui/store/button_default',
)

hover_image = clone_component(
    base_image,
    src='textures/ui/store/button_hover',
)
```

说明：

- `clone_component` 的输入必须是 `ComponentNode`
- 它会复制组件的 `props`，并递归复制其中的 `dict` / `list` / `tuple` / 子组件节点
- 传入的覆盖参数会写到新节点上，不会修改原组件
- 对于 `style` / `children` / 嵌套子节点模板复用场景，比手写浅拷贝更安全

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

#### `ImageButton`

`ImageButton` 是对 `Button` 的图片态封装。它接收一个 `default` 的 `Image` 组件作为模板，再根据 `hover` / `pressed` 传入的贴图路径快速生成三态图片按钮。

公开导入方式：

```python
from pyreact import ImageButton
```

参数说明：

| 参数 | 类型 | 说明 |
|------|------|------|
| `default` | `Image` | 默认态图片模板，必须传 `Image(...)` 组件 |
| `hover` | `str` | 悬浮态贴图路径；不传时回退到其他已给定状态 |
| `pressed` | `str` | 按下态贴图路径；不传时回退到其他已给定状态 |
| `style` | `Style` | 按钮自身尺寸/布局，和普通 `Button` 一致 |
| `children` | `list` | 按钮内部内容，例如文字、图标覆盖层 |
| `onClick` | `callable` | 点击回调 |

状态回退规则：

- `hover` 和 `pressed` 都不传：两者都回退到 `default.src`
- 只传 `pressed`：`hover` 回退到 `pressed`
- 只传 `hover`：`pressed` 回退到 `hover`

常见用法：

```python
ImageButton(
    style=Style(width=96, height=32),
    default=Image(
        style=Style(width='100%', height='100%'),
        src='textures/ui/store/button_default',
    ),
    hover='textures/ui/store/button_hover',
    pressed='textures/ui/store/button_pressed',
    onClick=lambda: do_something(),
    children=[
        Label(content='购买', color=Colors.white),
    ],
)
```

实现约束：

- `ImageButton` 不会原地修改你传入的 `default Image`，而是读取它的 props 后为每个状态重新构建新的 `Image`。
- 这样做是为了避开当前框架里浅拷贝带来的共享引用风险，尤其是 `style`、`children` 这类嵌套对象。
- `hover` / `pressed` 目前只快捷覆盖 `src`；其余图片属性（如 `color`、`uv`、`nineSlice`）沿用 `default` 模板。
- 如果你需要不同状态下切的不只是 `src`，而是整套 `Image` 参数甚至完全不同的背景结构，应继续使用 `Button(buttonBuilder=...)`。

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
