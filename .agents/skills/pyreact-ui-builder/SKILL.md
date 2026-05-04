---
name: pyreact-ui-builder
description: 指导 agents 在网易我的世界基岩版 ModSDK 环境中使用 Pyreact 编写业务 UI，而不是修改 Pyreact 框架本身。
compatibility: opencode
metadata:
  audience: agents
  domain: pyreact-ui
  platform: netease-minecraft-bedrock-modsdk
---

## 我能做什么

- 指导 agent 使用 `pyreact` 公开 API 编写业务 UI。
- 帮助判断组件能力应写在 props 还是 `style`。
- 约束网易 Minecraft Bedrock ModSDK 的挂载流程、JsonUI 容器、Python2 语法和跨系统调用方式。
- 提供 primitives、composites、hooks、动画、`key`、`ref`、布局和分辨率适配规范。

## 什么时候使用

当任务满足以下任一条件时，加载本 skill：

- 新建或修改基于 Pyreact 的页面、弹窗、HUD、列表、表单、详情面板。
- 需要正确使用 `Panel` / `Image` / `Label` / `Item` / `PaperDoll` / `Button` / `Input` / `Scroll`。
- 需要使用 `FilledButton` / `ImageButton` / `Animated`。
- 需要决定 `style`、props、`key`、`ref` 或 hooks 的写法。
- 需要把 Pyreact 页面挂载到 NetEase `ScreenNode`。

不要在以下场景只依赖本 skill：

- 用户要求修改框架内部实现（`pyreact/core`、`pyreact/layout`、`PyreactRuntimeScript`、`JsonUI/PyreactBase.json`）。这属于开发本库，必须同时遵守仓库根目录 `AGENTS.md`。
- 涉及网易 API / JsonUI 原生能力但文档未确认时。本 skill 只说明 Pyreact 公开用法，不能替代本地知识库查询。

## 第一原则：这是“用库开发 UI”

默认目标是：

1. 在业务脚本中 `from pyreact import ...` 使用公开 API。
2. 通过 `@Component` + primitives + hooks 描述页面。
3. 通过 `render_app(...)` 挂载到已有 `ScreenNode` / JsonUI root。
4. 优先修正业务组件写法，不默认下沉修改 renderer/runtime。

只有当用户明确要求“扩展框架能力 / 修改 renderer / 新增 style 属性 / 改 runtime 映射”时，才进入框架开发路径。

## 开始前必查

### 1. 判断任务层级

- **业务 UI 层**：组件、页面、弹窗、列表、交互状态。
- **JsonUI 容器层**：screen JSON 是否存在，是否有可挂载 root。
- **框架层**：primitive、layout、runtime、native mapping、动画系统。

### 2. 涉及网易 API / JsonUI 时查文档

必须遵守仓库 `AGENTS.md`：

- UI 控件操作、JsonUI、系统通信、PaperDoll 等网易 API 先查本地知识库。
- 跨系统调用使用 `clientApi.GetSystem(...)` / `serverApi.GetSystem(...)`，不要直接 import 其他模组系统。
- 不允许 import 非公开网易内部模块；只能使用暴露出来的 `clientApi` / `serverApi` 能力。

### 3. 保持 Python2 写法

- 不写 f-string。
- 不写 type hints。
- 不依赖 Python3-only 语法或库。

## 公开入口与心智模型

优先看 `pyreact/__init__.py`。

可直接使用的核心导出：

- 组件装饰器：`Component`
- primitives：`Panel`、`Image`、`Label`、`Item`、`PaperDoll`、`Button`、`Input`、`Scroll`
- composites：`FilledButton`、`ImageButton`、`Animated`
- 动画：`Animation`、`Transition`、`Easing`、`fadeIn`、`fadeOut`、`slideInUp`、`slideInDown`、`slideInLeft`、`slideInRight`、`slideOutUp`、`slideOutDown`、`slideOutLeft`、`slideOutRight`
- 样式与枚举：`Style`、`AlignItems`、`JustifyContent`、`FlexDirection`、`FlexWrap`、`FontSize`、`TextAlign`、`Position`、`ButtonState`、`RenderType`
- 颜色：`Color`、`Colors`
- hooks：`useState`、`useEffect`、`useMemo`、`useCallback`、`useRef`
- 工具：`clone_component`、`render_app`、`flat_button_builder_preset`

当前运行链路：

```text
业务组件函数
  -> VNode 树
  -> Shadow Tree + Flex 布局
  -> Diff mutations
  -> Native Runtime 增量提交
  -> NetEase ScreenNode / JsonUI 控件
```

当前分支不是废弃 grid 方案；不要把 old 分支的 grid/pool/typed-grid 经验套到当前 runtime。

## 标准挂载流程

顺序必须是：

1. 在 `UiInitFinished` 中 `RegisterUI(...)`。
2. 调用 `PushScreen(...)` 显示界面。
3. 在 `ScreenNode.Create()` 内调用 `render_app(...)`。
4. 在 `ScreenNode.Destroy()` 内调用 runtime `UnmountApp(...)`。

最小模板：

```python
# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
from pyreact import Component, Panel, Label, Style, render_app

ScreenNode = clientApi.GetScreenNodeCls()


@Component
def SimpleApp():
    return Panel(
        style=Style(width='100%', height='100%'),
        children=[Label(content='Hello Pyreact')],
    )


class MyScreen(ScreenNode):
    def Create(self):
        render_app(
            root=SimpleApp,
            bind={
                'screen': self,
                'root': '/root',
                'app_id': 'my_ui_app',
                'base_namespace': 'PyreactBase',
            },
        )

    def Destroy(self):
        runtime = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime is not None:
            runtime.UnmountApp({'app_id': 'my_ui_app'})
```

## `@Component` 规则

所有自定义业务组件都必须加 `@Component`。

原因：

- `render_app(root=...)` 会校验 root 是否带 `@Component`。
- `@Component` 负责处理 `key` / `ref`，业务函数不用手动声明它们。
- hooks 只能在组件渲染上下文中使用。

正确：

```python
@Component
def UserCard(name, level):
    return Panel(children=[Label(content='%s Lv.%s' % (name, level))])
```

不要把普通业务函数直接传给 `render_app`。

## 组件总览

### `Panel`

用途：通用容器、布局节点、动画子树根。

常用 props：

- `style`
- `children`

要点：

- 当前 runtime 会创建真实 `panelBase` 控件；不要按 old 分支把 `Panel` 理解为纯虚拟节点。
- 适合横纵布局、包裹子节点、绝对定位容器、列表行根节点。

### `Image`

用途：贴图、纯色底板、按钮背景、图标。

常用 props：

- `src`
- `color`
- `grayscale`
- `clipRatio`
- `uv` / `uvSize`
- `resizeMode`
- `imageAdaptionType`
- `nineSlice` / `nineSliceType`
- `rotation` / `rotatePivot`
- `onClick`

要点：

- 图片相关能力是 props，不是 `style`。
- `src` 为空时 runtime 回退到 `textures/ui/white_bg`，可用 `Image + color` 做纯色底。
- resize 铺满背景优先写四边绝对定位：`Style(position=Position.absolute, top=0, right=0, bottom=0, left=0)`。

### `Label`

用途：文本展示。

常用 props：

- `content`
- `color`
- `fontSize`
- `font`
- `textAlign`
- `linePadding`
- `shadow`

要点：

- 文本相关能力走 props，不走 `style`。
- 支持 `\n` 和 Minecraft `§` 格式码。
- 设置 `style.width` / `minWidth` 等宽度约束后可触发自动换行。
- 多行或多颜色文本优先考虑单个 `Label` + `\n` / 空格 / `§` 格式码，减少控件数。

### `Item`

用途：渲染物品图标。

常用 props：

- `identifier`
- `aux`
- `enchant`
- `userData`
- `itemDict`

要点：

- 可传扁平 props，也可传 `itemDict`。
- runtime 会兼容常见物品字典字段，如 `newItemName` / `itemName`、`newAuxValue` / `auxValue`。

### `PaperDoll`

用途：渲染网易纸娃娃控件，例如实体、骨骼模型或方块几何模型预览。

常用 props：

- `renderType`：优先用 `RenderType.entity` / `RenderType.skeleton` / `RenderType.blockGeometry`
- `entityId`
- `entityIdentifier`
- `skeletonModelName`
- `animation`
- `animationLooped`
- `blockGeometryModelName`
- `scale`
- `renderDepth`
- `initRotX` / `initRotY` / `initRotZ`
- `molangDict`
- `rotationAxis`
- `lightDirection`

要点：

- 位置、尺寸、透明度、层级写 `style`。
- 纸娃娃渲染参数写 props，不要写进 `style`。
- 当前模板使用普通 layer，不额外加 1000；需要层级时用 `style.zIndex`。
- PaperDoll 原生映射已按本地文档确认：`RenderEntity` / `RenderSkeletonModel` / `RenderBlockGeometryModel`。

### `Button`

用途：可点击容器，支持 `default / hover / pressed` 三态。

常用 props：

- `style`
- `children`
- `onClick`
- `buttonBuilder`

要点：

- 通常内部放 `Label` / `Image` / `Panel`。
- 不传 `buttonBuilder` 时使用默认三态。
- 传 `buttonBuilder` 时一般写 `def builder(state): return Image(...)`。
- 当三态都返回无子节点、`width='100%'`、`height='100%'` 的 `Image` 时，runtime 会直接复用 JSONUI 三态槽位；复杂三态内容会走通用子树挂载。
- 纯色三态优先用 `FilledButton`，图片三态优先用 `ImageButton`。

### `Input`

用途：文本输入。

常用 props：

- `value`
- `onChange`
- `placeholder`

要点：

- 优先使用 `value + onChange` 受控写法。
- 搜索框、昵称编辑等业务状态建议放在 `useState`。

### `Scroll`

用途：滚动列表容器。

常用 props：

- `style`
- `children`
- `showScrollbar`
- `ref`

要点：

- 长列表优先用 `Scroll`。
- 需要操作滚动位置时，使用 `ref.current.asScrollView()` 访问原生 ScrollView。

## 复合组件

### `FilledButton`

纯色三态按钮封装。

```python
FilledButton(
    default=Colors.black.withOpacity(0.45),
    hover=Colors.black.withOpacity(0.60),
    pressed=Colors.black.withOpacity(0.75),
    style=Style(width=120, height=32),
    children=[Label(content='OK', color=Colors.white)],
)
```

回退规则：只传 `default` 时三态都用 `default`；缺 `hover` 时回退到 `pressed`；缺 `pressed` 时回退到 `hover`。

### `ImageButton`

图片三态按钮封装。

```python
def build_image(src, state):
    return Image(src=src, nineSlice=(4, 4, 4, 4))

ImageButton(
    default='textures/ui/button_default',
    hover='textures/ui/button_hover',
    pressed='textures/ui/button_pressed',
    imageBuilder=build_image,
    style=Style(width=120, height=32),
    children=[Label(content='Buy', color=Colors.white)],
)
```

`imageBuilder` 支持 `imageBuilder(src)` 或 `imageBuilder(src, state)`，必须返回 `Image(...)`。

### `Animated`

声明式入场、出场和连续过渡包装器。

```python
Animated(
    key='row_42_anim',
    enter=slideInUp(distance=12, duration=180),
    exit=fadeOut(duration=140),
    children=Panel(style=Style(width='100%', height=36), children=[...]),
)
```

要点：

- 只能包一个 `ComponentNode`；多个节点先用 `Panel` 聚合。
- transform / size 动画只挂在直接子树根节点上，子内容由引擎随父节点移动。
- `opacity` 会在 runtime 中递归传播到子树和 Button 三态槽位。
- `enter` 只在真正新建逻辑节点时播放； keyed MOVE 不重放 enter，而走布局移动动画。
- 删除时 runtime 克隆独立 `__pyreact_exit_*` ghost 播放 exit，并立即释放原路径给新布局。
- 动态列表必须给 `Animated` 或根节点稳定业务 `key`，不要用随机值或易变文案。

## 动画 API

动画由 Python runtime 监听 `GameRenderTickEvent` 驱动。

### `Animation`

```python
Animation(
    duration=300,
    delay=0,
    easing=Easing.easeOutQuad,
    from_={'opacity': 0.0, 'translateY': 20.0},
    to={'opacity': 1.0, 'translateY': 0.0},
)
```

### `Transition`

```python
Animated(
    animate=Transition(values={'opacity': alpha}, duration=220),
    children=Panel(style=Style(width=120, height=40)),
)
```

### 可动画字段

- `opacity`：递归传播到子树与按钮槽位
- `translateX` / `translateY`：基于 layout 本地位置的视觉偏移，不影响兄弟布局
- `width` / `height`：通过原生 size 更新；`Label` 会跳过尺寸动画

预设包括 `fadeIn`、`fadeOut`、`slideInUp`、`slideInDown`、`slideInLeft`、`slideInRight`、`slideOutUp`、`slideOutDown`、`slideOutLeft`、`slideOutRight`。

## `props` 与 `style` 的分工

`style` 只放布局、定位和通用显示属性：

- 尺寸：`width`、`height`、`minWidth`、`maxWidth`、`minHeight`、`maxHeight`、`minSize`、`maxSize`
- 间距：`padding`、`paddingTop`、`paddingRight`、`paddingBottom`、`paddingLeft`、`margin`、`marginTop`、`marginRight`、`marginBottom`、`marginLeft`
- Flex：`flex`、`flexDirection`、`justifyContent`、`alignItems`、`alignSelf`、`flexWrap`
- 定位：`position`、`top`、`right`、`bottom`、`left`
- 显示：`opacity`、`display`、`zIndex`

以下必须写 props：

- `Image`：`src`、`color`、`grayscale`、`clipRatio`、`uv`、`uvSize`、`resizeMode`、`imageAdaptionType`、`nineSlice`、`nineSliceType`、`rotation`、`rotatePivot`
- `Label`：`content`、`color`、`fontSize`、`font`、`textAlign`、`linePadding`、`shadow`
- `Button`：`onClick`、`buttonBuilder`
- `Input`：`value`、`onChange`、`placeholder`
- `Item`：`identifier`、`aux`、`enchant`、`userData`、`itemDict`
- `PaperDoll`：`renderType`、`entityId`、`entityIdentifier`、`skeletonModelName`、`animation`、`animationLooped`、`blockGeometryModelName`、`scale`、`renderDepth`、`initRotX/Y/Z`、`molangDict`、`rotationAxis`、`lightDirection`
- `Animated`：`enter`、`animate`、`exit`

判断不清时，先查：

1. `pyreact/components/primitives.py`
2. `pyreact/components/style.py`
3. `PyreactRuntimeScript/native_runtime/props_mixin.py`

不要凭 Web/React/Unity/其他 Minecraft 平台经验猜。

## `Style(...)` 常见写法

### 自适应尺寸

不填写 `width` / `height` 时，该轴会按内容包裹：容器取非绝对子节点边界，`Label` 取文本测量结果，无内容的普通节点为 `0`。如果在 Flex 主轴上设置了 `flex`，主轴尺寸会按剩余空间分配；如果交叉轴继承或设置了 `alignItems` / `alignSelf=stretch`，且父节点该交叉轴有确定尺寸，则交叉轴会被拉伸。

### Flex 布局

```python
Panel(
    style=Style(
        flexDirection=FlexDirection.row,
        alignItems=AlignItems.center,
        justifyContent=JustifyContent.spaceBetween,
    ),
    children=[...],
)
```

### 相对定位

未设置 `position` 时等同于 `Position.relative`。相对定位节点保留原本 Flex 流占位，只按 `top/right/bottom/left` 做视觉偏移；同轴冲突时 `left` 优先于 `right`，`top` 优先于 `bottom`。

```python
Image(style=Style(width=40, height=20, left=6, top=3))
```

### 绝对定位

`Position.absolute` 会让节点脱离 Flex 流，按父节点内容区定位，不占据兄弟节点空间。左右同时设置且未设置 `width` 时会撑满剩余宽度；上下同时设置且未设置 `height` 时会撑满剩余高度。

```python
Image(
    style=Style(
        position=Position.absolute,
        top=0,
        right=0,
        bottom=0,
        left=0,
    ),
    color=Colors.black.withOpacity(0.4),
)
```

### `display` / `opacity` / `zIndex`

- `display='none'` 隐藏控件。
- `opacity` 建议使用 `0.0 ~ 1.0`。
- `zIndex` 映射到原生 layer，适合浮层微调。

## `key` 规则

动态列表、筛选结果、排序、tab 内容切换、动画列表必须使用稳定 `key`。

正确：

```python
Animated(
    key='item_%s_anim' % item['id'],
    enter=slideInUp(),
    exit=fadeOut(),
    children=Panel(key='item_%s' % item['id'], children=[...]),
)
```

不要使用随机数、当前时间、易变文案作为 key。没有稳定 key 时，列表项状态、动画状态、输入框、滚动引用都可能错位。

## `ref` 规则

需要拿到底层控件实例时使用 `useRef`：

```python
scroll_ref = useRef(None)

Scroll(
    ref=scroll_ref,
    style=Style(flex=1),
    children=[...],
)
```

调用前要判断 `ref.current` 是否已存在。

## Hooks 使用建议

- `useState`：选中项、输入框内容、弹窗显隐、筛选条件。
- `useEffect`：订阅/解绑、一次性副作用、依赖变化后同步外部系统；可返回 cleanup。
- `useMemo`：大列表过滤、昂贵映射、依赖确定的派生数据。
- `useCallback`：稳定事件回调或传给子组件的函数。
- `useRef`：原生控件引用或不触发重渲染的可变对象。

## Color / Colors

当前 `Color` API：

```python
Color(0xFFFF0000)
Color.fromRGB(255, 0, 0)
Color.fromRGBA(255, 0, 0, 0.5)
Color.fromHex('#80FF0000')
Colors.white
Colors.black.withOpacity(0.3)
```

可用属性和方法：

- `value`
- `alpha8` / `red` / `green` / `blue`
- `opacity` / `alpha`
- `withOpacity()` / `withAlpha()` / `withAlpha8()`
- `withRed()` / `withGreen()` / `withBlue()`
- `toRGBUnitTuple()` / `toRGBAUnitTuple()`

注意：当前实现没有 `fromARGB` / `fromRGBO` / `toCSSRGBA`。

## Label / 文本规范

`FontSize` 预设：

| fontSize | 数值 | 原生 scale |
| --- | ---: | ---: |
| `FontSize.small` | 5 | 0.5 |
| `FontSize.normal` | 10 | 1.0 |
| `FontSize.large` | 20 | 2.0 |
| `FontSize.extraLarge` | 40 | 4.0 |

建议：

- `extraLarge` 很大，除非特殊场景不要用。
- 中文常见宽度约 10px，英文约 5px，符号约 3px；按钮宽度要预留中英文差异。
- 多行文本用 `\n`；格式化文本用 Minecraft `§` 代码。

```python
Label(content='§a成功§r：任务完成')
```

## 《我的世界》UI 适配认知

- 画布尺寸通常等同于游戏内 UI 屏幕尺寸，不是物理像素直出。
- 固定像素会按平台 UI 适配比例缩放；百分比基于父容器尺寸。
- 手机版建议按 `320 x 210` 左右设计；PC 基岩版常见参考约 `376 x 250`。
- 顶层业务面板固定尺寸尽量控制在 `320 x 210` 内，避免手机越界。
- 高清清晰度优先交给贴图素材，不要单纯放大布局像素。

## JsonUI 容器要求

挂载 root 建议继承 `PyreactBase.rootBase`：

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

`PyreactBase.json` 当前提供：`panelBase` / `imageBase` / `textBase` / `itemBase` / `paperDollBase` / `buttonBase` / `inputBase` / `scrollBase`。

## 常见决策指南

### 什么时候用 `Panel`，什么时候用 `Image`

- 纯布局容器：优先 `Panel`。
- 需要贴图、纯色底板、九宫格背景：优先 `Image`。

### 什么时候用 `Button` 而不是 `Panel(onClick=...)`

- 需要按钮态、点击反馈、背景切换：用 `Button`。
- 只做简单容器点击：可用 `Panel(onClick=...)`，但复杂可交互元素仍优先 `Button`。

### 动画列表怎么写

- 每个业务项必须有稳定 key。
- transform 动画包在列表项根节点，不要给按钮、文字、图标分别做位移动画。
- 删除用 `exit`，新增用 `enter`；排序/删除导致的 MOVE 由 runtime 处理。

### 背景怎么写才能 resize 铺满

用四边绝对定位：

```python
Image(
    style=Style(position=Position.absolute, top=0, right=0, bottom=0, left=0),
    color=Colors.black,
)
```

## 遇到问题时先查哪里

1. 公开 API：`pyreact/__init__.py`
2. primitive 参数：`pyreact/components/primitives.py`
3. style 字段：`pyreact/components/style.py`
4. props 到原生映射：`PyreactRuntimeScript/native_runtime/props_mixin.py`
5. 布局行为：`pyreact/layout/flexbox.py`

## 禁止事项

- 不要默认修改 `pyreact/core`、`pyreact/layout`、`PyreactRuntimeScript` 来实现普通页面需求。
- 不要把 Image / Label / Item / PaperDoll 专属 props 写进 `style`。
- 不要省略 `@Component`。
- 不要在动态列表里省略稳定 `key`。
- 不要直接 import 非公开网易模块。
- 不要使用 Python3 语法。
- 文档未覆盖的网易 API，不要猜。

## 交付前自检清单

- 页面是否通过 `@Component` + primitives + hooks 编写？
- 组件 props 和 `style` 是否分工正确？
- 动态列表、动画列表、tab 内容是否有稳定 `key`？
- 背景是否需要四边绝对定位以适配 resize？
- 需要原生实例操作的地方是否用了 `ref`？
- 是否按 `RegisterUI -> PushScreen -> render_app -> UnmountApp` 顺序接入？
- 涉及网易 API 的部分是否查过知识库？
- 是否保持 Python2 写法？

## 推荐起手式

接到 Pyreact UI 任务时，按这个顺序执行：

1. 找业务 screen 脚本和对应 JsonUI 容器。
2. 看现有页面是否已用 `render_app(...)` 挂载。
3. 从 `pyreact/__init__.py` 确认可用组件、hooks、composites 和动画 API。
4. 按 props/style 分工写业务组件。
5. 动态列表和动画节点先补稳定 key。
6. 最后再考虑是否需要下沉到框架实现。
