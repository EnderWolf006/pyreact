# Pyreact

面向 **网易我的世界（基岩版）ModSDK** 的 Python UI 声明式渲染框架（实验性）。

Pyreact 提供类似 React 的组件函数 + Hooks 写法，将组件树（VNode）经过 Diff、Flex 布局和运行时提交后，渲染为网易 `ScreenNode` / JsonUI 控件树。


## 特性

- **函数式组件** - 通过 `@Component` 声明组件
- **Hooks** - `useState` / `useEffect` / `useMemo` / `useCallback` / `useRef`
- **Flexbox 布局子集** - 支持尺寸、间距、Flex、相对/绝对定位、透明度、层级
- **基础控件** - `Panel` / `Image` / `Label` / `Item` / `PaperDoll` / `Button` / `Input` / `Scroll`
- **复合组件** - `FilledButton` / `ImageButton` / `Animated`
- **动画系统** - `Animation` / `Transition` / `Easing` 与 `fadeIn`、`slideInUp` 等预设
- **运行时桥接** - 统一管理挂载、卸载、Diff 提交、resize 刷新和 `GameRenderTickEvent` 动画 tick

---

## 快速开始

如只想体验示例，可以修改 `sync_to_test.cmd` 中的参数后运行同步脚本。

### 1. 集成到你的 AddOn

**行为包（behavior_pack）添加：**

```text
pyreact/                    # 框架核心
PyreactRuntimeScript/       # 运行时系统
```

**资源包（resource_pack）的 `ui/` 目录添加：**

```text
JsonUI/PyreactBase.json     # 基础控件模板
YourScreen.json             # 你的 Screen 定义
```

### 2. 注册 UI 并显示

```python
# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystemCls()


class YourClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.ListenForEvent(
            clientApi.GetEngineNamespace(),
            clientApi.GetEngineSystemName(),
            'UiInitFinished',
            self,
            self.OnUiInitFinished,
        )

    def OnUiInitFinished(self, args):
        clientApi.RegisterUI(
            'YourMod',
            'YourUI',
            'YourMod.YourScreen.YourScreenNode',
            'YourNamespace.main',
        )
        clientApi.PushScreen('YourMod', 'YourUI', {'isHud': 1, 'data': {}})
```

### 3. 编写组件并挂载

```python
# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
from pyreact import *

ScreenNode = clientApi.GetScreenNodeCls()


@Component
def CounterApp():
    count, setCount = useState(0)

    def increment():
        setCount(count + 1)

    return Panel(
        style=Style(
            width="100%",
            height="100%",
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        children=[
            Label(
                style=Style(marginBottom=8),
                fontSize=FontSize.large,
                shadow=True,
                content="这是一个计数器示例"
            ),
            FilledButton(
                style=Style(padding=8),
                default=Colors.dodgerBlue,
                hover=Colors.dodgerBlue.withAlpha(0.8),
                pressed=Colors.dodgerBlue.withAlpha(0.6),
                onClick=increment,
                children=Label(shadow=True, content="Count: " + str(count))
            ),
        ]
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
            log_perf=False,
        )

    def Destroy(self):
        runtime = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime is not None:
            runtime.UnmountApp({'app_id': self.app_id})
```

---

## 核心 API

公开入口优先看 `pyreact/__init__.py`。

### 顶层导出

- 组件装饰器：`Component`
- primitives：`Panel`、`Image`、`Label`、`Item`、`PaperDoll`、`Button`、`Input`、`Scroll`
- composites：`FilledButton`、`ImageButton`、`Animated`
- 动画：`Animation`、`Transition`、`Easing`、`fadeIn`、`fadeOut`、`slideInUp`、`slideInDown`、`slideInLeft`、`slideInRight`、`slideOutUp`、`slideOutDown`、`slideOutLeft`、`slideOutRight`
- 样式与枚举：`Style`、`AlignItems`、`JustifyContent`、`FlexDirection`、`FlexWrap`、`FontSize`、`TextAlign`、`Position`、`ButtonState`、`RenderType`
- 颜色：`Color`、`Colors`
- hooks：`useState`、`useEffect`、`useMemo`、`useCallback`、`useRef`
- 工具：`clone_component`、`render_app`、`flat_button_builder_preset`

### 公共 props

#### `key` (自动处理)

- 用途：给节点提供稳定身份，便于 Diff、列表复用、动画状态和输入/滚动状态对齐
- 建议：动态列表、可重排节点、筛选结果必须使用业务唯一 ID
- 说明：自定义组件不用在形参里声明 `key`，`@Component` 会自动注入

#### `ref` （自动处理）

- 用途：获取对应原生控件实例，访问底层 API
- 支持：`useRef` 创建的 ref 对象
- 说明：`ref` 由 `@Component` 注入，会透传到最终 primitive 节点

#### `children` （形参处理）

- 用途：传入子节点
- 支持：单个节点，或 `list` / `tuple` 节点列表
- 说明：自定义组件需要在形参里声明 `children`（非强制但最好支持），并把它传给子组件；primitive 组件会自动把 `children` 里的节点渲染到对应控件上

#### `style` （形参处理）

- 用途：布局、定位、尺寸、层级、透明度等通用属性
- 支持：`Style(...)`（推荐）或 `dict`
- 原则：图片路径、文本字号、物品参数、纸娃娃参数等组件专属能力必须走 props，不要写进 `style`
- 说明：自定义组件需要在形参里声明 `style`（非强制但最好支持），并把它传给子组件；primitive 组件全部原生支持


### `style` 字段

尺寸相关：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `width` / `height` | `int / float / str` | 宽高，可写数值或 `'100%'`；不填写时按内容自适应，受 `flex` 与交叉轴 `stretch` 影响时除外 |
| `minWidth` / `maxWidth` | `int / float / str` | 最小/最大宽度 |
| `minHeight` / `maxHeight` | `int / float / str` | 最小/最大高度 |
| `minSize` / `maxSize` | `tuple / list` | 尺寸约束 |

不填写 `width` / `height` 时，该轴默认按内容包裹：容器取非绝对子节点边界，`Label` 取文本测量结果，无内容的普通节点为 `0`。如果节点在 Flex 主轴上设置了 `flex`，主轴尺寸会按剩余空间分配；如果交叉轴继承或设置了 `alignItems` / `alignSelf=stretch`，且父节点该交叉轴有确定尺寸，则交叉轴会被拉伸。

间距相关：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `padding` | `int / float` | 统一内边距 |
| `paddingTop` / `paddingRight` / `paddingBottom` / `paddingLeft` | `int / float` | 单边内边距 |
| `margin` | `int / float` | 统一外边距 |
| `marginTop` / `marginRight` / `marginBottom` / `marginLeft` | `int / float` | 单边外边距 |

Flex 相关：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `flex` | `int / float` | Flex 比例 |
| `flexDirection` | `str` | 主轴方向，常用 `FlexDirection.row` / `column` |
| `justifyContent` | `str` | 主轴对齐 |
| `alignItems` | `str` | 交叉轴对齐 |
| `alignSelf` | `str` | 当前节点自身对齐 |
| `flexWrap` | `str` | 换行策略 |

定位与显示：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `position` | `str` | 默认按 `Position.relative`；也可写 `Position.absolute` |
| `top` / `right` / `bottom` / `left` | `int / float` | 定位偏移 |
| `opacity` | `float` | 透明度，取值范围 `0.0 ~ 1.0`，会继承并与祖先透明度相乘 |
| `display` | `str` | 显示状态，例如 `'none'` |
| `zIndex` | `int` | 原生 layer 微调 |

定位语义：

- 未传 `position` 时等同于 `Position.relative`
- `Position.relative`：节点保留原本 Flex 流占位，再按 `top/right/bottom/left` 做视觉偏移；同轴冲突时 `left` 优先于 `right`，`top` 优先于 `bottom`
- `Position.absolute`：节点脱离 Flex 流，按父节点内容区解析 `top/right/bottom/left`；左右同时设置且未设置 `width` 时会撑满剩余宽度，上下同时设置且未设置 `height` 时会撑满剩余高度

透明度语义：

- `style.opacity` 会沿组件树继承，子节点最终透明度会乘上所有祖先的 `style.opacity`
- `Color.fromRGBA(..., alpha)`、`Color.withAlpha()` 里的 alpha 只作用于当前节点颜色，不会被子节点继承
- 普通渲染最终 alpha 为“继承后的 `style.opacity` * 当前节点 `Color.alpha`”
- 动画字段 `opacity` 会递归作用到完整子树与 Button 三态槽位；动画字段 `alpha` 只作用到动画根和直接子组件，不会传播到更深后代

---

## 基础组件（Primitives）

### `Panel`

通用容器和布局节点。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `style` | `Style / dict` | 布局与显示样式 |
| `children` | `ComponentNode / list` | 子节点 |

当前 runtime 会为 `Panel` 创建 `panelBase` 控件；它适合承载布局、定位和作为动画子树根。

### `Image`

用于贴图、纯色底板、按钮背景、图标。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `src` | `str` | 图片路径；为空时 runtime 回退到 `textures/ui/white_bg` |
| `color` | `Color` | 颜色蒙版 |
| `grayscale` | `bool` | 是否灰度 |
| `clipRatio` | `float` | 裁剪比例 |
| `uv` / `uvSize` | `tuple / list` | UV 起点和尺寸 |
| `resizeMode` | `str` | 图片缩放模式 |
| `imageAdaptionType` | `str` | 图片适配类型 |
| `nineSlice` / `nineSliceType` | `tuple / str` | 九宫格参数 |
| `rotation` / `rotatePivot` | `float / tuple` | 旋转角度和旋转中心 |
| `onClick` | `callable` | 点击回调 |

### `Label`

用于文本展示。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `content` | `str` | 文本内容，支持 `\n` 和 Minecraft `§` 格式码 |
| `color` | `Color` | 文本颜色 |
| `fontSize` | `int` | 字号，常用 `FontSize.small/normal/large` |
| `textAlign` | `str` | 对齐方式 |
| `linePadding` | `float` | 行间距 |
| `shadow` | `bool` | 文本阴影 |

### `Item`

用于渲染物品图标，对应 `inventory_item_renderer`。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `identifier` | `str` | 物品标识符 |
| `aux` | `int` | 附加值 |
| `enchant` | `bool` | 是否显示附魔效果 |
| `userData` | `object` | 额外物品数据 |
| `itemDict` | `dict` | 完整物品字典，可与扁平 props 组合使用 |

### `PaperDoll`

对应 `netease_paper_doll_renderer`，用于实体、骨骼模型或方块几何模型预览。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `renderType` | `str` | `RenderType.entity` / `skeleton` / `blockGeometry` |
| `entityId` | `int` | 实体 id |
| `entityIdentifier` | `str` | 实体 identifier，例如 `minecraft:player` |
| `skeletonModelName` | `str` | 骨骼模型名 |
| `animation` | `str` | 骨骼动画名 |
| `animationLooped` | `bool` | 骨骼动画是否循环 |
| `blockGeometryModelName` | `str` | 方块几何模型名 |
| `scale` | `float` | 模型缩放 |
| `renderDepth` | `float` | 渲染深度微调 |
| `initRotX` / `initRotY` / `initRotZ` | `float` | 初始旋转 |
| `molangDict` | `dict` | Molang 参数 |
| `rotationAxis` | `tuple / list` | 旋转轴向量 |
| `lightDirection` | `tuple / list` | 光照方向，主要用于骨骼模型 |

要点：

- 注意该组件 `layer` 不要设置太高会导致渲染问题，如需调整可加一个父 Panel 调整层级
- runtime 映射的网易 API：`RenderEntity` / `RenderSkeletonModel` / `RenderBlockGeometryModel`

### `Button`

可点击容器，支持 `default / hover / pressed` 三态。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `onClick` | `callable` | 点击回调 |
| `buttonBuilder` | `callable` | 三态背景构造器，`builder(state) -> ComponentNode` |

当 `buttonBuilder` 三态都返回无子节点、`width='100%'`、`height='100%'` 的 `Image` 时，runtime 会直接复用按钮 JSONUI 三态槽位，避免额外 clone 子 Image；否则会把槽位图片设为透明，再按通用子树渲染 builder 返回内容。

### `Input`

文本输入。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `value` | `str` | 受控值 |
| `onChange` | `callable` | 输入变化回调 |
| `placeholder` | `str` | 占位文本 |

`value + onChange` 形成受控输入；只传 `onChange` 或不传 `value` 时，runtime 保留非受控输入在重渲染后的内容。

### `Scroll`

滚动列表容器。

| prop | 类型 | 说明 |
| --- | --- | --- |
| `showScrollbar` | `bool` | 是否显示滚动条 |
| `ref` | `Ref` | 获取底层 ScrollView |

---

## 复合组件（Composites）

### `FilledButton`

`Button` 的纯色三态封装。

```python
FilledButton(
    default=Colors.black.withAlpha(0.45),
    hover=Colors.black.withAlpha(0.60),
    pressed=Colors.black.withAlpha(0.75),
    style=Style(width=120, height=32),
    children=[Label(content='OK', color=Colors.white)],
)
```

回退规则：

- 只传 `default`：`hover` 和 `pressed` 都回退到 `default`
- 传 `default + pressed`：`hover` 回退到 `pressed`
- 传 `default + hover`：`pressed` 回退到 `hover`

### `ImageButton`

`Button` 的图片三态封装。

```python
def build_button_image(src, state):
    return Image(src=src, nineSlice=(4, 4, 4, 4))

ImageButton(
    default='textures/ui/button_default',
    hover='textures/ui/button_hover',
    pressed='textures/ui/button_pressed',
    imageBuilder=build_button_image,
    style=Style(width=120, height=32),
    children=[Label(content='Buy', color=Colors.white)],
)
```

`imageBuilder` 支持 `imageBuilder(src)` 或 `imageBuilder(src, state)`，必须返回 `Image(...)`。返回的 Image 会自动补 `width='100%'` 和 `height='100%'`。

### `Animated`

声明式入场、出场和连续过渡包装器。

```python
Animated(
    key='notice_anim',
    enter=slideInUp(distance=20, duration=240),
    exit=fadeOut(duration=180),
    children=Panel(style=Style(width=220, height=80), children=[...]),
)
```

行为要点：

- `Animated` 必须包裹单个 `ComponentNode`；多个节点先用 `Panel` 聚合
- transform / size 动画只挂在直接子树根节点上，子内容由引擎随父节点一起移动，避免列表项、关闭按钮和文字不同步
- `opacity` 会在 runtime 中递归传播到完整子树和 Button 三态槽位，因为部分 JsonUI 控件不继承父透明度
- `alpha` 只作用到动画根和直接子组件，不会传播到更深后代，语义与 `Color.alpha` 一致
- `enter` 只在真正新建逻辑节点时播放； keyed MOVE 不会重放 enter
- 删除期间 runtime 会克隆出独立 `__pyreact_exit_*` ghost 播放 exit，立即释放原路径给新布局使用；快速切换/全量清空会先清理 ghost
- 列表增删必须给 `Animated` 或其根节点稳定 `key`

---

## 动画

Pyreact 动画由 Python runtime 监听 `GameRenderTickEvent` 驱动。每帧由 `PyreactRuntimeClientSystem.GameRenderTickEvent` 调用各 app runtime 的 `tick_animations()`；有动画值变化时调用 `UpdateScreen()` 刷新界面。

运行时维护 `_animation_states`，每个逻辑节点或 ghost 节点记录当前值、目标值、开始时间、持续时间、缓动函数和完成回调。`tick_animations()` 根据当前时间计算进度，经过 easing 后插值，并把结果提交到原生控件。

### API 组成

| API | 用途 |
| --- | --- |
| `Animated` | 把入场、出场、连续过渡配置挂到单个子节点根部 |
| `Animation` | 描述一次从 `from_` 到 `to` 的动画，用于 `enter` / `exit` |
| `Transition` | 描述状态变化后的目标值，用于 `animate` |
| `Easing` | 缓动函数命名空间 |
| `fadeIn` / `fadeOut` / `slideIn*` / `slideOut*` | 返回 `Animation` 的预设函数 |

所有动画 API 都可从顶层导入：

```python
from pyreact import Animated, Animation, Transition, Easing, fadeIn, fadeOut, slideInUp
```

### `Animated`

`Animated` 是声明式动画入口：

```python
Animated(
    key='notice_anim',
    enter=slideInUp(distance=20, duration=240),
    exit=fadeOut(duration=180),
    animate={'opacity': 1.0},
    children=Panel(style=Style(width=220, height=80), children=[...]),
)
```

参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `children` | `ComponentNode` | 被动画控制的单个子节点 |
| `enter` | `Animation` | 节点首次进入时播放 |
| `exit` | `Animation` | 节点删除前播放 |
| `animate` | `Transition / dict` | 目标值变化时播放连续过渡 |
| `key` | `str / int` | 节点稳定身份；子节点没有 key 时写入子节点 |

结构规则：

- `Animated` 只能包裹一个 `ComponentNode`
- 多个节点先用 `Panel` 聚合，再把 `Panel` 传给 `Animated`
- `Animated` 不创建额外原生控件；它会 clone 直接子节点，并把内部 `__animation__` 配置写入子节点 props
- `key` 写在 `Animated(...)` 或直接子节点上都可形成稳定身份

### `Animation`

`Animation` 描述一次性动画，主要用于 `enter` 和 `exit`：

```python
Animation(
    duration=300,
    delay=0,
    easing=Easing.easeOutQuad,
    from_={'opacity': 0.0, 'translateY': 20.0},
    to={'opacity': 1.0, 'translateY': 0.0},
    onComplete=lambda: None,
)
```

参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `duration` | `300` | 持续时间，单位毫秒；负数归一化为 `0` |
| `delay` | `0` | 延迟时间，单位毫秒；负数归一化为 `0` |
| `easing` | `Easing.easeOutQuad` | 缓动函数 |
| `from_` | `{}` | 起始值字典，只接收可动画字段 |
| `to` | `{}` | 目标值字典，只接收可动画字段 |
| `onComplete` | `None` | 动画完成回调 |

`from_` 与 `to` 的字段值会转为 `float`；不支持的字段和非数字值会被忽略。`duration <= 0` 时，runtime 在下一次 tick 直接应用最终值。

`Animation.clone(**overrides)` 返回一个新的 `Animation`，用于复用基础动画并覆盖个别字段：

```python
base_enter = slideInUp(distance=16, duration=240)
slow_enter = base_enter.clone(duration=420, delay=80)
```

### `Transition`

`Transition` 描述连续过渡目标值，用于 `Animated(animate=...)`。当 `values` 生成的签名变化时，runtime 从当前动画值或布局基线过渡到新目标值。

```python
Animated(
    animate=Transition(
        values={'opacity': 0.35 if disabled else 1.0},
        duration=220,
        delay=0,
        easing=Easing.easeOutQuad,
    ),
    children=Panel(style=Style(width=120, height=40)),
)
```

参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `values` | `{}` | 目标值字典，只接收可动画字段 |
| `duration` | `200` | 持续时间，单位毫秒 |
| `delay` | `0` | 延迟时间，单位毫秒 |
| `easing` | `Easing.easeOutQuad` | 缓动函数 |

`animate` 可以直接传 dict：

```python
Animated(
    animate={'opacity': group_opacity, 'translateX': offset},
    children=Panel(style=Style(width=120, height=40)),
)
```

dict 写法等价于 `Transition(values=dict_value, duration=200, delay=0, easing=Easing.easeOutQuad)`。

### 可动画字段

| 字段 | 原生提交 | 行为 |
| --- | --- | --- |
| `opacity` | `SetAlpha` | 值会限制在 `0.0 ~ 1.0`，并递归传播到完整子树和 Button 三态槽位；传播时保留每个节点自己的 `Color.alpha` |
| `alpha` | `SetAlpha` | 值会限制在 `0.0 ~ 1.0`，只作用到动画根和直接子组件，不会传播到更深后代 |
| `translateX` | `SetPosition` | 基于布局结果的 X 方向本地偏移，不改变兄弟节点布局 |
| `translateY` | `SetPosition` | 基于布局结果的 Y 方向本地偏移，不改变兄弟节点布局 |
| `width` | `SetSize` | 改变当前控件宽度；`Label` 跳过尺寸动画 |
| `height` | `SetSize` | 改变当前控件高度；`Label` 跳过尺寸动画 |

字段基线：

- `opacity` 缺省基线为节点当前 `style.opacity`，没有设置时为 `1.0`
- `alpha` 缺省基线为 `1.0`
- `translateX` / `translateY` 缺省基线为 `0.0`
- `width` / `height` 缺省基线为当前布局尺寸
- `translateX` / `translateY` 是视觉偏移，不参与 Flex 剩余空间计算
- `width` / `height` 动画只改原生控件尺寸，不重新计算兄弟布局

### 生命周期行为

#### 入场 `enter`

- 节点首次创建并提交到 native 后播放 `enter`
- 同一个逻辑节点完成入场后会记录 `entered=True`
- keyed MOVE 不重放 `enter`
- 节点被真正删除后再次创建，会重新播放 `enter`

#### 出场 `exit`

删除带 `exit` 的节点时，runtime 不直接移除原控件。实际流程：

1. 收集删除子树中带 `exit` 的节点
2. clone 原生子树到 `__pyreact_exit_*` ghost 路径
3. 立即删除原路径，释放该路径给新布局使用
4. 在 ghost 子树上播放各节点的 `exit`
5. 所有 exit 动画完成后删除 ghost 子树和动画状态

这个机制允许新列表布局立即占用原路径，同时旧节点独立播放出场动画。

#### 连续过渡 `animate`

- `animate` 首次出现且没有 active animation 时，runtime 直接应用目标值作为初始状态
- `animate` 的目标值签名变化时，runtime 启动 `Transition`
- 过渡起点来自当前动画值；没有当前值时使用字段基线
- `Transition` 不包含 `onComplete`

#### 布局移动动画

keyed 列表发生 MOVE 时，runtime 会记录旧位置到新位置的差值，并启动内置 layout move 动画：

- `duration=180`
- `delay=0`
- `easing=Easing.easeOutQuad`
- 从旧位置偏移过渡到 `translateX=0` / `translateY=0`

MOVE 动画只处理由 diff 识别出的 keyed 节点移动；没有稳定 key 的列表无法得到正确的移动关系。

### 透明度传播

部分 JsonUI 控件不继承父控件透明度，因此普通 `style.opacity` 和动画 `opacity` 都由 runtime 显式递归应用到完整子树。`Button` 的 `default` / `hover` / `pressed` 三态槽位单独处理：runtime 记录槽位基础透明度，动画时提交 `base_alpha * opacity`。

`style.opacity` 是继承属性，会和祖先透明度连乘；`Color.alpha` 只属于当前节点颜色，不继承。最终普通 alpha 为继承后的 `style.opacity * Color.alpha`；动画 `opacity` 再作用于 runtime 提交的完整子树基础 alpha，并保留后代自己的 `Color.alpha`。动画 `alpha` 语义与 `Color.alpha` 一致，只影响该动画根和直接子组件，不会传播到孙级及更深组件。

### Easing

`Easing` 中的函数都把输入进度限制到 `0.0 ~ 1.0`。

| 名称 | 说明 |
| --- | --- |
| `linear` | 线性 |
| `easeIn` | `easeInQuad` 别名 |
| `easeOut` | `easeOutQuad` 别名 |
| `easeInOut` | `easeInOutQuad` 别名 |
| `easeInQuad` / `easeOutQuad` / `easeInOutQuad` | 二次曲线 |
| `easeInCubic` / `easeOutCubic` / `easeInOutCubic` | 三次曲线 |
| `easeOutBack` / `easeInBack` | 带回弹的曲线 |

### 预设

| 函数 | 默认参数 | `from_` | `to` |
| --- | --- | --- | --- |
| `fadeIn` | `duration=300, delay=0, easing=None` | `{'opacity': 0.0}` | `{'opacity': 1.0}` |
| `fadeOut` | `duration=300, delay=0, easing=None` | `{'opacity': 1.0}` | `{'opacity': 0.0}` |
| `slideInUp` | `distance=20, duration=300, delay=0, easing=None` | `{'translateY': distance, 'opacity': 0.0}` | `{'translateY': 0.0, 'opacity': 1.0}` |
| `slideInDown` | `distance=20, duration=300, delay=0, easing=None` | `{'translateY': -distance, 'opacity': 0.0}` | `{'translateY': 0.0, 'opacity': 1.0}` |
| `slideInLeft` | `distance=20, duration=300, delay=0, easing=None` | `{'translateX': -distance, 'opacity': 0.0}` | `{'translateX': 0.0, 'opacity': 1.0}` |
| `slideInRight` | `distance=20, duration=300, delay=0, easing=None` | `{'translateX': distance, 'opacity': 0.0}` | `{'translateX': 0.0, 'opacity': 1.0}` |
| `slideOutUp` | `distance=20, duration=300, delay=0, easing=None` | `{'translateY': 0.0, 'opacity': 1.0}` | `{'translateY': -distance, 'opacity': 0.0}` |
| `slideOutDown` | `distance=20, duration=300, delay=0, easing=None` | `{'translateY': 0.0, 'opacity': 1.0}` | `{'translateY': distance, 'opacity': 0.0}` |
| `slideOutLeft` | `distance=20, duration=300, delay=0, easing=None` | `{'translateX': 0.0, 'opacity': 1.0}` | `{'translateX': -distance, 'opacity': 0.0}` |
| `slideOutRight` | `distance=20, duration=300, delay=0, easing=None` | `{'translateX': 0.0, 'opacity': 1.0}` | `{'translateX': distance, 'opacity': 0.0}` |

`easing=None` 时由 `Animation` 使用 `Easing.easeOutQuad`。

### 列表入场和出场

```python
@Component
def NoticeList(items):
    children = []
    for item in items:
        children.append(
            Animated(
                key=item['id'],
                enter=slideInUp(distance=12, duration=200),
                exit=fadeOut(duration=150),
                children=Panel(
                    style=Style(width=180, height=28, marginBottom=4),
                    children=[Label(content=item['text'], shadow=True)]
                )
            )
        )
    return Panel(children=children)
```

列表动画的关键条件：

- 每个列表项使用稳定业务 key
- 增加项触发 `enter`
- 删除项触发 `exit`
- 重排项触发内置 layout move 动画

### 状态连续过渡

```python
@Component
def ToggleCard(disabled):
    group_opacity = 0.35 if disabled else 1.0
    offset = 8 if disabled else 0
    return Animated(
        animate=Transition(
            values={'opacity': group_opacity, 'translateX': offset},
            duration=220,
            easing=Easing.easeOutQuad,
        ),
        children=Panel(
            style=Style(width=160, height=48),
            children=[Label(content='State Card')]
        )
    )
```

`disabled` 变化会改变 `values` 签名，runtime 从当前显示值过渡到新的 `opacity` 和 `translateX`。

### 自定义动画

```python
def complete():
    print('enter complete')

custom_enter = Animation(
    duration=400,
    delay=80,
    easing=Easing.easeOutBack,
    from_={'opacity': 0.0, 'translateY': 24.0, 'height': 0.0},
    to={'opacity': 1.0, 'translateY': 0.0, 'height': 60.0},
    onComplete=complete,
)

Animated(
    key='custom_panel',
    enter=custom_enter,
    exit=custom_enter.clone(
        delay=0,
        easing=Easing.easeInBack,
        from_={'opacity': 1.0, 'translateY': 0.0},
        to={'opacity': 0.0, 'translateY': 24.0},
        onComplete=None,
    ),
    children=Panel(style=Style(width=220, height=60), children=[...]),
)
```

### 动画边界

- `Animated` 包裹多个子节点会抛出 `ValueError('Animated expects exactly one child')`
- `Animated(children=None)` 返回 `None`
- 非 `ComponentNode` 子节点会原样返回，不附加动画配置
- 已经存在 `__animation__` 的节点不会被新的 `Animated` 覆盖内部配置
- `Label` 不执行 `width` / `height` 动画
- `translateX` / `translateY` 不改变布局占位
- 没有稳定 key 的动态列表无法可靠触发 MOVE 和 exit 对齐

---

## `clone_component`

基于已有 `ComponentNode` 创建副本并覆盖 props，适合模板复用。

```python
base_image = Image(style=Style(width='100%', height='100%'), src='textures/ui/button_default')
hover_image = clone_component(base_image, src='textures/ui/button_hover')
```

说明：

- 输入必须是 `ComponentNode`
- 会递归复制 `dict` / `list` / `tuple` / 子组件节点
- 覆盖参数只写入新节点，不修改原组件

---

## Color / Colors

`Color` 是不可变 ARGB 颜色对象。

```python
Color(0xFFFF0000)
Color.fromRGB(255, 0, 0)
Color.fromRGBA(255, 0, 0, 0.5)
Color.fromHex('#80FF0000')
Colors.white
Colors.black.withAlpha(0.3)
```

常用属性和方法：

- `value`：原始 32-bit ARGB 整数
- `alpha8` / `red` / `green` / `blue`：`0~255` 通道
- `alpha`：`0.0~1.0` 透明度
- `withAlpha(alpha)`：按 `0.0~1.0` 修改透明度
- `withAlpha8(alpha8)`：按 `0~255` 修改透明度
- `withRed()` / `withGreen()` / `withBlue()`：修改颜色通道
- `toRGBUnitTuple()` / `toRGBAUnitTuple()`：导出归一化浮点 tuple

注意：当前实现没有 `fromARGB` / `fromRGBO` / `toCSSRGBA`，也没有 `opacity` / `withOpacity()` 别名。最终原生透明度会把 `style.opacity` 和 `color.alpha` 相乘。

---

## Hooks

```python
count, set_count = useState(0)
useEffect(lambda: (lambda: None), [])
value = useMemo(lambda: expensive_calc(dep), [dep])
handler = useCallback(lambda: do_something(dep), [dep])
ref = useRef(None)
```

要点：

- 自定义组件必须加 `@Component` 才能正确使用 hooks
- `useEffect` 可以返回 cleanup
- `useRef` 常用于保存原生控件引用或不触发重渲染的可变对象

---

## 运行时行为与性能

当前运行链路：

```text
业务组件函数
  -> VNode 树
  -> Shadow Tree + Flex 布局
  -> Diff mutations
  -> Native Runtime 增量提交
  -> NetEase ScreenNode / JsonUI 控件
```

关键行为：

- 首次挂载后优先走增量提交；结构变化提交受影响父子树，非布局属性更新只提交精确节点
- 若一次 render 没有 VNode mutation 且没有 layout refresh，会跳过布局、native commit 和 `UpdateScreen`
- `ScreenSizeChangedClientEvent` 会触发延迟 layout refresh，root size 优先读取 game component 的 `GetScreenSize()`
- Runtime 会缓存原生控件、adapter、Label/Image 属性、几何位置尺寸、按钮绑定、按钮三态槽位、Scroll content path 和文本测量结果
- 删除或重建控件时会按路径前缀清理缓存
- `log_perf=True` 会打印组件执行、VNode 构建、Diff、布局、native commit、`UpdateScreen`、按钮槽位和 native API 明细

---

## JsonUI 配置

挂载 Pyreact 的 root 原生控件必须继承 `PyreactBase.rootBase`：

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

`PyreactBase.json` 提供运行时克隆所需基础 type_def：`panelBase` / `imageBase` / `textBase` / `itemBase` / `paperDollBase` / `buttonBase` / `inputBase` / `scrollBase`。

---

## 示例页面

示例入口位于 `PyreactExampleScript/`，具体页面在 `PyreactExampleScript/examples/`。

| 示例 | 演示内容 |
| --- | --- |
| `AnimationDemo` | 入场、出场、连续过渡、列表增删动画、resize 背景铺满 |
| `SkinShopApp` | 商品预览、`PaperDoll`、复合布局 |
| `FriendApp` | Tab、搜索、列表选择、详情面板、Scroll |
| `BedwarStoreApp` | 商品分类、Item 物品展示、购买交互 |
| `BattlePassApp` | 等级奖励、任务列表、轨道布局 |

---

## 目录结构

```text
pyreact/
├── components/            # primitives、Style、Color、enums
├── composites/            # FilledButton、ImageButton、Animated
├── animation/             # Animation、Easing、Transition、预设
├── core/                  # VNode、Reconciler、Hooks、TreeBuilder
├── layout/                # Flexbox、ShadowNode、布局计算
└── renderer/              # 文本测量等辅助

PyreactRuntimeScript/
├── modMain.py
├── PyreactNativeRuntime.py
└── native_runtime/
    ├── lifecycle_mixin.py
    ├── props_mixin.py
    ├── native_api_mixin.py
    └── animation_mixin.py

PyreactExampleScript/
├── PyreactExampleClientSystem.py
├── PyreactExampleUi.py
└── examples/

JsonUI/
└── PyreactBase.json
```

---

## 同步测试

```cmd
sync_to_test.cmd
```

脚本参数用于覆盖默认同步路径。

---

## 开发约束

- Python 运行目标是 Python2；禁止 f-string、type hints 和 Python3-only 语法
- 涉及网易 API / JsonUI / 系统通信时必须先查本地知识库
- 跨模组通信必须使用 `clientApi.GetSystem(...)` / `serverApi.GetSystem(...)`，禁止直接 import 其他模组系统
- 动态列表、筛选、排序和动画列表必须使用稳定 `key`
- 组件专属属性写 props，布局显示属性写 `style`

## 许可证与归属要求

本项目采用 [Apache License 2.0](LICENSE) 许可证。

Minecraft 基岩版 ModSDK 项目使用 Pyreact 时，必须在服务器/存档加载界面和切换维度界面显示归属信息：

- 框架名称：Pyreact
- 作者：EnderWolf006
- GitHub 地址：https://github.com/EnderWolf006/pyreact

归属条款见 [NOTICE](NOTICE)。

## 现状

项目处于开发中，API/目录结构会随实现调整。示例脚本展示当前集成路径。
