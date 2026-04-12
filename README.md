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

### 公共 props

以下公共能力适用于所有公开组件；各组件小节里不再重复列 `key` / `children` / `style`。

#### `key`

- 用途：给节点提供稳定身份，便于列表复用、diff 和状态对齐
- 传法：所有 `@Component` 组件都可以通过关键字参数传入 `key=...`
- 建议：动态列表优先使用业务唯一 ID，不要用随机值

#### `children`

- 用途：传入子节点内容
- 支持：单个节点，或 `list` / `tuple` 节点列表
- 说明：不传时会自动归一化为空列表

#### `style`

- 用途：承载布局、定位、显示层属性
- 支持：`Style(...)` 或 `dict`
- 说明：组件专属能力例如 `Image.src`、`Label.content`、`Button.onClick` 不写在 `style` 里

尺寸相关：

| 字段 | 类型 | 说明 |
|------|------|------|
| `width` | `int / str` | 宽度，可写数值或 `'100%'` |
| `height` | `int / str` | 高度，可写数值或 `'100%'` |
| `minWidth` | `int / str` | 最小宽度 |
| `maxWidth` | `int / str` | 最大宽度 |
| `minHeight` | `int / str` | 最小高度 |
| `maxHeight` | `int / str` | 最大高度 |
| `minSize` | `tuple` | 最小尺寸，通常是 `(width, height)` |
| `maxSize` | `tuple` | 最大尺寸，通常是 `(width, height)` |

间距相关：

| 字段 | 类型 | 说明 |
|------|------|------|
| `padding` | `int / float` | 统一内边距 |
| `paddingTop` | `int / float` | 上内边距 |
| `paddingRight` | `int / float` | 右内边距 |
| `paddingBottom` | `int / float` | 下内边距 |
| `paddingLeft` | `int / float` | 左内边距 |
| `margin` | `int / float` | 统一外边距 |
| `marginTop` | `int / float` | 上外边距 |
| `marginRight` | `int / float` | 右外边距 |
| `marginBottom` | `int / float` | 下外边距 |
| `marginLeft` | `int / float` | 左外边距 |

Flex 相关：

| 字段 | 类型 | 说明 |
|------|------|------|
| `flex` | `int / float` | Flex 比例 |
| `flexDirection` | `str` | 主轴方向，通常为 `FlexDirection.row` / `column` |
| `justifyContent` | `str` | 主轴对齐 |
| `alignItems` | `str` | 交叉轴对齐 |
| `alignSelf` | `str` | 当前节点自身对齐 |
| `flexWrap` | `str` | 换行策略 |

定位与显示相关：

| 字段 | 类型 | 说明 |
|------|------|------|
| `position` | `str` | 定位方式，通常为 `Position.relative` / `absolute` |
| `top` | `int / float` | 顶部偏移 |
| `left` | `int / float` | 左侧偏移 |
| `right` | `int / float` | 右侧偏移 |
| `bottom` | `int / float` | 底部偏移 |
| `opacity` | `float` | 透明度 |
| `display` | `str` | 显示状态，例如 `'none'` |
| `zIndex` | `int` | 层级 |

说明：`ref` 也由 `@Component` 统一支持，最常见于 `Scroll(ref=...)` 这类需要访问原生控件的场景。

### 基础组件（Primitives）

#### `Panel`

`Panel` 是最基础的布局容器，只参与布局和 children 组织，不会单独创建原生 `panel` 控件。

除公共 props 外，无额外 props。

| prop | 类型 | 说明 |
|------|------|------|
| `（无）` | - | `Panel` 只使用公共的 `key` / `children` / `style` |

#### `Image`

`Image` 用于贴图、纯色底板、图标和按钮背景。

| prop | 类型 | 说明 |
|------|------|------|
| `src` | `str` | 图片路径；不传时 runtime 会回退到 `textures/ui/white_bg` |
| `color` | `Color` | 颜色蒙版 |
| `grayscale` | `bool` | 是否灰度化 |
| `clipRatio` | `float` | 裁剪比例 |
| `uv` | `tuple` | UV 起点 |
| `uvSize` | `tuple` | UV 尺寸 |
| `resizeMode` | `str` | 图片缩放模式 |
| `imageAdaptionType` | `str` | 图片适配类型 |
| `nineSlice` | `tuple` | 九宫格切片参数 |
| `nineSliceType` | `str` | 九宫格类型 |
| `rotation` | `float` | 旋转角度 |
| `rotatePivot` | `tuple` | 旋转中心 |
| `onClick` | `callable` | 点击回调 |

#### `Label`

`Label` 用于文本展示。

| prop | 类型 | 说明 |
|------|------|------|
| `content` | `str` | 文本内容 |
| `color` | `Color` | 文本颜色 |
| `fontSize` | `int` | 字号 |
| `textAlign` | `str` | 对齐方式 |
| `linePadding` | `float` | 行间距 |
| `shadow` | `bool` | 是否显示阴影 |

#### `Item`

`Item` 用于渲染物品图标，对应 `inventory_item_renderer`。

| prop | 类型 | 说明 |
|------|------|------|
| `identifier` | `str` | 物品标识符 |
| `aux` | `int` | 物品附加值 |
| `enchant` | `bool` | 是否显示附魔效果 |
| `userData` | `object` | 额外物品数据 |
| `itemDict` | `dict` | 完整物品字典，runtime 会兼容常见字段命名 |

#### `Button`

`Button` 是可点击容器，支持 `default / hover / pressed` 三态。

| prop | 类型 | 说明 |
|------|------|------|
| `onClick` | `callable` | 点击回调 |
| `buttonBuilder` | `callable` | 背景构造器，签名通常为 `builder(state)` |

#### `Input`

`Input` 用于文本输入。

| prop | 类型 | 说明 |
|------|------|------|
| `value` | `str` | 当前输入值 |
| `onChange` | `callable` | 输入变化回调 |
| `placeholder` | `str` | 占位文本 |

#### `Scroll`

`Scroll` 用于滚动列表容器。

| prop | 类型 | 说明 |
|------|------|------|
| `showScrollbar` | `bool` | 是否显示滚动条 |

#### `PaperDoll`

`PaperDoll` 对应 `netease_paper_doll_renderer`，用于实体、骨骼模型和方块几何模型预览。

| prop | 类型 | 说明 |
|------|------|------|
| `renderType` | `str` | 渲染类型，通常为 `RenderType.entity` / `skeleton` / `blockGeometry` |
| `entityId` | `int` | 实体 id |
| `entityIdentifier` | `str` | 实体 identifier，例如 `minecraft:cow` |
| `skeletonModelName` | `str` | 骨骼模型名 |
| `animation` | `str` | 骨骼动画名 |
| `animationLooped` | `bool` | 骨骼动画是否循环 |
| `blockGeometryModelName` | `str` | 方块几何模型名 |
| `scale` | `float` | 模型缩放 |
| `renderDepth` | `float` | 渲染深度微调 |
| `initRotX` | `float` | 初始 X 轴旋转 |
| `initRotY` | `float` | 初始 Y 轴旋转 |
| `initRotZ` | `float` | 初始 Z 轴旋转 |
| `molangDict` | `dict` | Molang 参数字典 |
| `rotationAxis` | `tuple` | 旋转轴向量 |
| `lightDirection` | `tuple` | 光照方向 |

### 组合组件（Composites）

#### `FilledButton`

`FilledButton` 是对 `Button` 的纯色封装，适合“纯色底板 + 内容”的按钮场景。

| prop | 类型 | 说明 |
|------|------|------|
| `default` | `Color` | 默认态背景色 |
| `hover` | `Color` | 悬浮态背景色；不传时按回退规则补齐 |
| `pressed` | `Color` | 按下态背景色；不传时按回退规则补齐 |
| `onClick` | `callable` | 点击回调，透传给内部 `Button` |

状态回退规则：

- 只传 `default`：`hover` 和 `pressed` 都回退到 `default`
- 传 `default + pressed`：`hover` 回退到 `pressed`
- 传 `default + hover`：`pressed` 回退到 `hover`

#### `ImageButton`

`ImageButton` 是对 `Button` 的图片态封装，适合“给三态贴图值，再由 builder 生成背景图”的场景。

| prop | 类型 | 说明 |
|------|------|------|
| `default` | `str` | 默认态贴图路径 |
| `hover` | `str` | 悬浮态贴图路径；不传时按回退规则补齐 |
| `pressed` | `str` | 按下态贴图路径；不传时按回退规则补齐 |
| `imageBuilder` | `callable` | 图片构造器，支持 `imageBuilder(src)` 或 `imageBuilder(src, state)` |
| `onClick` | `callable` | 点击回调，透传给内部 `Button` |

状态回退规则：

- 只传 `default`：`hover` 和 `pressed` 都回退到 `default`
- 传 `default + pressed`：`hover` 回退到 `pressed`
- 传 `default + hover`：`pressed` 回退到 `hover`
- `imageBuilder` 必须返回 `Image(...)`；返回结果会自动注入 `width='100%'` 和 `height='100%'`

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

`Style(...)` 的完整字段已经在上面的公共 props `style` 表格中列全；这里不再重复写示例代码块。

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
