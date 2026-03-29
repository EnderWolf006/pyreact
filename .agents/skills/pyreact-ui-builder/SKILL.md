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

- 指导 agent 用 `pyreact` 暴露的公开 API 编写业务 UI。
- 约束 agent 区分 **用库开发 UI** 与 **开发/修改框架本身** 两类任务。
- 提供组件、props、style、hooks、`key`、`ref`、挂载流程、NetEase 平台约束的实用规范。
- 补充 Label 文本、字号、自动换行、格式化代码与分辨率适配的使用建议。

## 什么时候使用

当任务满足以下任一条件时，加载本 skill：

- 新建或修改基于 Pyreact 的页面、弹窗、HUD、列表、表单、详情面板。
- 需要决定某个能力应该写在 `style` 还是组件 props 上。
- 需要在业务 UI 中正确使用 `Label` / `Image` / `Button` / `Input` / `Scroll` / `Item`。
- 需要把 Pyreact 页面挂载到 NetEase `ScreenNode` 上。

不要在以下场景只依赖本 skill：

- 你要修改框架内部实现（`pyreact/core`、`pyreact/layout`、`PyreactRuntimeScript`）。这属于“开发本库”，先看仓库根目录 `agents.md`。

## 第一原则：这是“用库开发 UI”，不是“开发本库”

你的默认目标是：

1. 在业务脚本里通过 `from pyreact import ...` 使用公开 API。
2. 通过 `@Component` + primitives + hooks 描述页面。
3. 通过 `render_app(...)` 把组件树挂到现有 `ScreenNode`。
4. 尽量不修改框架内部文件。

只有当用户明确要求“扩展框架能力 / 修改 renderer / 新增 style 属性支持 / 改 runtime 映射”时，才进入框架开发路径。

## 开始前必查

### 1. 先确认当前任务在哪一层

- **业务 UI 层**：`class XXXScreen(ScreenNode):` 业务UI类入口中调用的render_app。
- **JsonUI 容器层**：检查是否已有 screen JSON 和可挂载的 root 容器。
- **框架层**：仅在用户明确要求时进入。

### 2. 涉及网易 API / JsonUI 时先查文档

必须遵守仓库 `agents.md`：

- `GetSystem` / `BroadcastEvent` / `ListenForEvent`：先查文档再写。
- 不允许直接 import 非公开网易模块（例如 `gui`）；只能使用暴露出来的 `clientApi` / `serverApi` 能力。

### 3. 保持 Python2 写法

- 不用 f-string。
- 不写 type hints。
- 注意兼容 Python2 字符串与语法风格。

## 公开入口与最小心智模型

### 公开 API 入口

优先看：`pyreact/__init__.py`

可直接使用的核心导出包括：

- 组件装饰器：`Component`
- primitive 组件：`Panel`、`Image`、`Label`、`Item`、`Button`、`Input`、`Scroll`
- 样式与枚举：`Style`、`AlignItems`、`JustifyContent`、`FlexDirection`、`FontSize`、`Position`、`ButtonState`
- 颜色：`Color`、`Colors`
- hooks：`useState`、`useEffect`、`useMemo`、`useCallback`、`useRef`
- 挂载入口：`render_app`

### 运行链路（只需理解，不要默认去改）

业务组件函数
→ VNode / 组件树
→ Flex 布局
→ Native Runtime
→ NetEase ScreenNode 控件树

写业务 UI 时，通常只需要关心：

- 组件返回什么树
- `style` 怎么写
- 某些属性应该写进 props 还是 `style`
- 页面如何挂载/卸载

## 标准挂载流程

顺序必须是：

1. 在 `UiInitFinished` 中 `RegisterUI(...)`
2. 调用 `PushScreen(...)`
3. 在 `ScreenNode.Create()` 内调用 `render_app(...)`
4. 在 `ScreenNode.Destroy()` 中调用 `PyreactRuntimeClientSystem.UnmountApp(...)`

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
        children=[
            Label(content='Hello Pyreact'),
        ],
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
        runtime_system = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime_system is not None:
            runtime_system.UnmountApp({'app_id': 'my_ui_app'})
```

## `@Component` 规则

所有自定义组件都必须加 `@Component`。

原因：

- `render_app(root=...)` 会强校验 root 是否带 `@Component`。
- `@Component` 负责处理 `key` / `ref`，让你不用在函数签名里手动声明它们。

正确：

```python
@Component
def UserCard(name, level):
    return Panel(children=[Label(content='%s Lv.%s' % (name, level))])
```

不要把“业务组件”直接写成普通函数后传给 `render_app`。

## 组件总览

### 1. `Panel`

用途：通用容器、布局节点。

常用参数：

- `style`
- `children`
- `onClick`

适合：横纵布局、包裹子节点、绝对定位容器。

### 2. `Image`

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
- `children`
- `onClick`

要点：

- `Image` 的渲染相关属性是 **props，不是 style**。
- `src` 为空时，runtime 会回退到 `textures/ui/white_bg`，因此经常可以把 `Image + color` 当纯色面板用。
- 业务上常见写法是用 `Image(style=Style(width='100%', height='100%'), color=Color(...))` 作为背景层。

### 3. `Label`

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

- 文字相关能力走 **props**，不是 `style`。
- 位置、尺寸、margin 等走 `style`。
- 支持手动换行 `\n`。
- 当设置 `width` / `minWidth` 等约束后，可触发自动换行。
- 行距能力在本库公开 API 中对应 `linePadding`；如果外部资料写 `lineSpacing`，落到本库实现时应优先使用当前公开 prop 名。

### 4. `Item`

用途：渲染物品图标。

常用 props：

- `identifier`
- `aux`
- `enchant`
- `userData`
- `itemDict`

要点：

- 可直接传扁平 props。
- 也可传 `itemDict`，runtime 会自动兼容 `newItemName` / `itemName`、`newAuxValue` / `auxValue` 等字段。

### 5. `Button`

用途：可点击容器。

常用 props：

- `style`
- `children`
- `onClick`
- `buttonBuilder`

要点：

- 按钮本质上也是容器，通常内部塞 `Label` / `Image` / `Panel`。
- 若不传 `buttonBuilder`，runtime 会为 `default/hover/pressed` 三态渲染默认贴图。
- 若传 `buttonBuilder`，一般写成 `lambda state: Image(...)` 或函数 `def builder(state): ...`。
- `buttonBuilder` 可根据 `ButtonState.default/hover/pressed` 返回不同背景。

### 6. `Input`

用途：文本输入。

常用 props：

- `style`
- `value`
- `onChange`
- `placeholder`

要点：

- `value + onChange` 是受控写法。
- 只传 `onChange` 或不传 `value` 时，runtime 会尽量保持非受控输入在整树重渲染后的内容。
- 搜索框、昵称编辑框等都优先走受控写法，便于和 `useState` 保持一致。

### 7. `Scroll`

用途：滚动列表容器。

常用 props：

- `style`
- `children`
- `showScrollbar`
- `ref`

要点：

- 常和长列表搭配使用。
- 若需要滚动到顶部/底部，给 `Scroll(ref=...)`，再通过 `ref.current.asScrollView()` 调原生滚动接口。

## `props` 与 `style` 的分工

这是最重要的使用规则之一。

### `style` 只放布局/定位/显示层通用属性

当前公开支持（见 `pyreact/components/style.py`）：

- 尺寸：`width`、`height`、`minWidth`、`maxWidth`、`minHeight`、`maxHeight`、`minSize`、`maxSize`
- 间距：`padding`、`paddingTop`、`paddingRight`、`paddingBottom`、`paddingLeft`、`margin`、`marginTop`、`marginRight`、`marginBottom`、`marginLeft`
- Flex：`flex`、`flexDirection`、`justifyContent`、`alignItems`、`alignSelf`、`flexWrap`
- 定位：`position`、`top`、`left`、`right`、`bottom`
- 其他：`opacity`、`display`、`zIndex`

### 以下必须写到组件 props，不要误写进 `style`

#### Image props

- `src`
- `color`
- `grayscale`
- `clipRatio`
- `uv`
- `uvSize`
- `resizeMode`
- `imageAdaptionType`
- `nineSlice`
- `nineSliceType`
- `rotation`
- `rotatePivot`

#### Label props

- `content`
- `color`
- `fontSize`
- `font`
- `textAlign`
- `linePadding`
- `shadow`

#### Button props

- `onClick`
- `buttonBuilder`

#### Input props

- `value`
- `onChange`
- `placeholder`

#### Item props

- `identifier`
- `aux`
- `enchant`
- `userData`
- `itemDict`

### 判断不清时怎么做

先查两处：

1. `pyreact/components/primitives.py` —— 看 primitive 的公开参数。
2. `PyreactRuntimeScript/native_runtime/props_mixin.py` —— 看 runtime 对哪些 props 做了原生映射。

不要凭 Web/React/其他平台经验猜。

## `Style(...)` 的常见写法

### 百分比与固定像素

本库支持混合写法，例如：

```python
Style(width='100%', height=40)
```

在网易 UI 中，固定像素会参与系统缩放；百分比则基于父容器尺寸。

### Flex 布局

横向工具栏：

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

纵向表单/侧栏：

```python
Panel(
    style=Style(
        flexDirection=FlexDirection.column,
        padding=12,
    ),
    children=[...],
)
```

### 绝对定位

浮动按钮常用：

```python
Button(
    style=Style(
        position=Position.absolute,
        right=20,
        bottom=20,
        width=26,
        height=26,
        zIndex=100,
    ),
    ...
)
```

### `display` / `opacity` / `zIndex`

- `display='none'` 可直接隐藏控件。
- `opacity` 范围建议按 `0.0 ~ 1.0` 使用。
- `zIndex` 会映射到原生 layer，适合浮层和悬浮按钮。

## `key` 的使用规则

### 什么场景必须加 `key`

动态列表、筛选结果、可重排节点，一律加稳定 `key`。

- tab 按钮：`key='tab_%s' % tab_id`
- 好友列表：`key=f['id']`

### 为什么要加

primitive 在内部会把 `key` 提升到节点属性，布局与渲染层据此构建稳定 node_id。没有稳定 key 时：

- 列表项状态可能错位
- 输入框/滚动引用可能漂移
- 节点复用与更新结果会不稳定

### `key` 的要求

- 用业务唯一 ID，不要用瞬时随机值。
- 不要依赖会频繁变化的展示文案。
- 若列表稳定不可重排，索引可临时使用；只要会筛选、插入、排序，就换成业务 ID。

## `ref` 的使用规则

### 适用场景

- 需要拿到底层控件实例时

### 标准写法

例如需要控制滚动时
```python
scroll_ref = useRef(None)

Scroll(
    ref=scroll_ref,
    style=Style(flex=1),
    children=[...],
)
```

然后：

```python
def scroll_to_top():
    scroll_ref.current.asScrollView().SetScrollViewPercentValue(0)
```

### 注意

- `ref` 不需要写进组件函数签名，`@Component` 会处理。
- `ref.current` 可能在首次挂载前为空，调用前要考虑生命周期。

## Hooks 使用建议

### `useState`

适合：选中项、输入框内容、弹窗显隐、筛选条件。

```python
selected_tab, set_selected_tab = useState('all')
```

建议：

- 页面交互状态优先放在 `useState`。
- `Input` 最适合配 `value=state` + `onChange=set_state`。

### `useEffect`

适合：订阅/解绑、一次性副作用、依赖变化后同步外部系统。

注意：effect 可以返回 cleanup。

### `useMemo`

适合：

- 大列表过滤结果
- 昂贵映射表
- 依赖确定的派生数据

### `useCallback`

适合：需要稳定引用的事件回调或传给子组件的函数。

### `useRef`

适合：

- 存底层原生控件引用
- 存不触发重渲染的可变对象

## Color / Colors 类开发规范
该模块提供了一个仿 Flutter 风格的不可变颜色对象。为保证颜色处理的一致性与准确性，请遵循以下开发规范。

### 1. 颜色的创建与实例化 (Initialization)

你可以通过多种方式来创建一个 `Color` 对象：

```python
# 1. 直接传入 32-bit ARGB 整数 (0xAARRGGBB)
color1 = Color(0xFFFF0000)  # 不透明的红色

# 2. 使用 fromARGB (Alpha, Red, Green, Blue) - 取值范围 0~255
color2 = Color.fromARGB(255, 255, 0, 0)

# 3. 使用 fromRGBO (Red, Green, Blue, Opacity) - RGB 取值 0~255，Opacity 取值 0.0~1.0
color3 = Color.fromRGBO(255, 0, 0, 1.0)

# 4. 使用 fromHex (支持解析 Hex 字符串)
# 支持格式: #RGB, #ARGB, #RRGGBB, #AARRGGBB (也可以用 0x 或 0X 开头，或者不带前缀)
color_hex1 = Color.fromHex("#FF0000")    # 默认 Alpha 为 FF (即完全不透明)
color_hex2 = Color.fromHex("0xFFFF0000") # 包含 Alpha 通道
color_hex3 = Color.fromHex("#F00")       # 简写形式，等同于 #FF0000
```

### 2. 获取颜色属性 (Properties)

创建对象后，可以轻松读取颜色的各个通道值：

```python
my_color = Color.fromARGB(128, 50, 100, 150)

# 获取 32-bit 整数值
print(my_color.value)   # 返回对应的 int 值

# 获取 0~255 范围的单通道整数值
print(my_color.alpha)   # 128
print(my_color.red)     # 50
print(my_color.green)   # 100
print(my_color.blue)    # 150

# 获取 0.0~1.0 范围的不透明度
print(my_color.opacity) # 128 / 255.0 ≈ 0.5019
```

### 3. 颜色的修改与派生 (Modifiers)

由于 `Color` 是不可变对象，修改颜色属性会返回一个**全新**的 `Color` 实例：

```python
base_color = Color(0xFF00FF00) # 绿色

# 替换某个通道的值 (0~255)，其他通道保持不变
new_alpha = base_color.withAlpha(128)
new_red   = base_color.withRed(255)
new_green = base_color.withGreen(0)
new_blue  = base_color.withBlue(128)

# 替换不透明度 (0.0~1.0)
half_transparent = base_color.withOpacity(0.5) 
```

### 4. 数据导出与转换 (Export / Conversion)

如果需要将颜色传递给其他图形库或前端系统，可以使用以下导出方法：

```python
ui_color = Color.fromRGBO(255, 128, 0, 0.8)

# 1. 导出为 0.0 ~ 1.0 范围的浮点数元组 (常用于 OpenGL 等图形 API)
rgb_tuple = ui_color.toRGBUnitTuple()   # (1.0, 0.5019..., 0.0)
rgba_tuple = ui_color.toRGBAUnitTuple() # (1.0, 0.5019..., 0.0, 0.8)

# 2. 导出为 CSS 兼容的 rgba 字符串 (常用于 Web 前端)
css_str = ui_color.toCSSRGBA() # "rgba(255,128,0,0.800000)"
```

### 5. 使用预设颜色常量 (`Colors` 类)

`Colors` 类提供了一组静态的常用颜色常量，可以直接调用，无需重新实例化：

```python
# 直接使用预定义的 Color 对象
bg_color = Colors.white
text_color = Colors.black
border_color = Colors.lightGrey

# 可以搭配 Modifier 使用
shadow_color = Colors.black.withOpacity(0.2)
```

## Label / 文本开发规范

### `fontSize` 的预设值

公开枚举位于 `pyreact/components/enums.py`：

- `FontSize.small = 8`
- `FontSize.normal = 16`
- `FontSize.large = 32`
- `FontSize.extraLarge = 64`

Runtime 的映射基线是：`16 -> scale 1.0`。

因此常用映射可理解为：

| fontSize | 数值 | 原生 scale |
| --- | ---: | ---: |
| `FontSize.small` | 8 | 0.5 |
| `FontSize.normal` | 16 | 1.0 |
| `FontSize.large` | 32 | 2.0 |
| `FontSize.extraLarge` | 64 | 4.0 |

建议：

- extraLarge 4.0的缩放会导致字体非常大，除非极其特殊的情况，**禁止使用**
- 优先使用预设值，尤其在 Minecraft 字体下，整倍缩放通常更清晰。
- 若必须自定义数值，先确认视觉效果能接受，再推广。

### 文本尺寸认知

在 `scale=1.0`、行距为 0 的常见情况下：

- 实际高度大约是 10px（会继续受 UI 适配缩放影响）
- 英文常见宽度约 8px
- 中文常见宽度约 16px
- 符号常见宽度约 3px
- 字符间距约 2px

这意味着：

- 中英文混排宽度差异很大
- 做按钮或标签宽度预估时，要按“文字内容 + 字体缩放 + 平台缩放”综合估算

### 换行与行距
**注：如遇多行文本/同行文本中需间隔/不同颜色文本组合，一定要优先考虑使用一个Label控件用`\n` / `中间加空格` / `§格式代码` 以优化性能**
**注：如遇多行文本/同行文本中需间隔/不同颜色文本组合，一定要优先考虑使用一个Label控件用`\n` / `中间加空格` / `§格式代码` 以优化性能**
**注：如遇多行文本/同行文本中需间隔/不同颜色文本组合，一定要优先考虑使用一个Label控件用`\n` / `中间加空格` / `§格式代码` 以优化性能**
- 手动换行：在 `content` 里写 `\n`
- 自动换行：给 `Label` 设置 `style.width` 或 `style.minWidth` 等宽度约束
- 行距：优先使用公开 prop `linePadding`

### 文本格式化代码

Minecraft 基岩版原生支持 `§` 格式代码，可直接写进 `Label(content=...)` 中。

例如：

```python
Label(content='§a成功§r：任务完成')
```

规则：

- `§` + 特定字符为格式控制码
- `\n` 不会中断样式，除非后续遇到新的格式码或 `§r`
- `§r` 会重置为控件默认颜色/格式


## 《我的世界》UI 适配认知

写业务 UI 时，要记住网易 UI 不是物理像素直出。

### 核心概念

- 画布尺寸通常等同于屏幕大小
- 实际分辨率是游戏内像素计算基准
- 系统会计算适配比例 `a`
- 固定像素会按 `a` 被统一缩放

控件显示尺寸可理解为：

`实际显示尺寸 = (父控件尺寸 × 百分比) + (设定固定像素 × a)`

### 设计基准建议

- 手机版基准适配区域：`320 × 210`
- PC 基岩版基准适配区域：`376 × 250`
- 多端兼容优先按手机基准 `320 × 210` 设计

### 布局建议

- **顶层业务面板的固定尺寸，尽量控制在 `320 × 210` 以内，避免越界**。
- **顶层业务面板的固定尺寸，尽量控制在 `320 × 210` 以内，避免越界**。
- **顶层业务面板的固定尺寸，尽量控制在 `320 × 210` 以内，避免越界**。
- 高清清晰度优先交给贴图素材，不要简单无限放大布局像素值。
- 纯像素值不是物理分辨率概念，要按游戏 UI 实际分辨率预估。

## 常见决策指南

### 什么时候用 `Panel`，什么时候用 `Image`

- 纯布局容器：优先 `Panel`
- 需要贴图或纯色底板：优先 `Image`

### 什么时候用 `Button` 包一层，而不是 `Panel(onClick=...)`

- 需要明确按钮态、点击反馈、背景切换：用 `Button`
- 只做简单容器点击：可考虑 `Panel(onClick=...)`，但复杂可交互元素仍优先 `Button`

### 文本颜色写哪里

- 写在 `Label(color=...)`
- 不要放到 `style`

### 图片颜色蒙版写哪里

- 写在 `Image(color=...)`
- 不要放到 `style`

## 遇到问题时先查哪里

1. **某个属性是不是公开支持**：`pyreact/__init__.py`、`pyreact/components/primitives.py`、`pyreact/components/style.py`
2. **某个 props 最终如何映射到原生**：`PyreactRuntimeScript/native_runtime/props_mixin.py`

## 禁止事项

- 不要默认修改 `pyreact/core`、`pyreact/layout`、`PyreactRuntimeScript` 来“实现页面需求”。
- 不要把 Image/Label 专属 props 错写进 `style`。
- 不要省略 `@Component`。
- 不要在动态列表里省略稳定 `key`。
- 不要直接 import 非公开网易模块。
- 不要使用 Python3 语法。
- 文档没覆盖的网易 API，不要猜。

## 交付前自检清单

- 页面是否通过 `@Component` + primitives + hooks 编写？
- 组件 props 和 `style` 是否分工正确？
- 动态列表是否有稳定 `key`？
- 需要原生实例操作的地方是否用了 `ref`？
- 是否按 `RegisterUI -> PushScreen -> render_app -> UnmountApp` 顺序接入？
- 涉及网易 API 的部分是否查过知识库？
- 是否保持 Python2 写法？

## 推荐起手式

接到 Pyreact UI 任务时，按这个顺序执行：

1. 找业务 screen 脚本和对应 JSON UI 容器。
2. 看现有页面是否已用 `render_app(...)` 挂载。
3. 从 `pyreact/__init__.py` 确认可用组件与 hooks。
4. 再写业务组件，而不是一开始就下沉到 runtime。
