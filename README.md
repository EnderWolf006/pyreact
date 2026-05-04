# Pyreact

面向 **网易我的世界（基岩版）ModSDK** 的 Python UI 声明式渲染框架（实验性）。

它提供类似 React 的组件函数 + Hooks 写法，把组件树（VNode）经过 Diff 与布局计算后，渲染为 **ScreenNode / JsonUI 控件树**。

## 特性

- **函数式组件**：通过 `@Component` 声明组件
- **Hooks**：`useState` / `useEffect` / `useMemo` / `useCallback` / `useRef`
- **基础控件**（Primitives）：`Panel` / `Image` / `Label` / `Item` / `PaperDoll` / `Button` / `Input` / `Scroll`
- **复合组件**：`FilledButton` / `ImageButton` / `Animated`
- **动画描述**：`Animation` / `Transition` / `Easing` 与 `fadeIn`、`slideInUp` 等预设，运行时按当前扁平渲染链路驱动 `opacity` / `translateX` / `translateY` / `width` / `height`
- **布局**：Flexbox 风格布局（子集），支持 `width/height/padding/margin/flexDirection/justifyContent/alignItems/position/...`
- **运行时桥接**：将组件树渲染到 NetEase UI（通过 Runtime 系统统一管理挂载/卸载/重渲染）


## 快速开始（在 ModSDK AddOn 中使用）
> 如你只想用example体验一下，可以直接改一下 `sync_to_test.cmd` 中的参数，一键开始体验
### 1) 拷贝文件到你的 AddOn

把以下目录拷贝到 **行为包（behavior_pack）** 下：

- `pyreact/`
- `PyreactRuntimeScript/`

把以下 JSON 拷贝到 **资源包（resource_pack）** 的 `ui/` 目录下：

- `JsonUI/PyreactBase.json`
- 你的 Screen JSON（可参考 `JsonUI/PyreactExample.json`）

### 2) 确保 Runtime 系统被注册

`PyreactRuntimeScript/modMain.py` 会注册 `PyreactRuntimeClientSystem`。确保该脚本作为你的 AddOn 的一部分被加载。

### 3) 注册 UI 并 PushScreen

可参考：`PyreactExampleScript/PyreactExampleClientSystem.py`

典型流程（示意）：

1. `RegisterUI(...)`
2. `PushScreen(...)`

### 4) 在 ScreenNode 中挂载 Pyreact App

可参考：`PyreactExampleScript/PyreactExampleUi.py`

一个最小计数器示例（保持 Python2 写法）：

```python
# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
from pyreact import (
    Component,
    Panel,
    Label,
    Button,
    Style,
    AlignItems,
    JustifyContent,
    Colors,
    useState,
    render_app,
)

ScreenNode = clientApi.GetScreenNodeCls()


@Component
def CounterApp():
    count, set_count = useState(0)

    return Panel(
        style=Style(
            width='100%',
            height='100%',
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        children=[
            Label(content='Count: %s' % count, color=Colors.white),
            Button(
                style=Style(width=140, height=34, marginTop=10),
                onClick=(lambda: set_count(count + 1)),
                children=[Label(content='Increment', color=Colors.white)],
            ),
        ],
    )


class MyScreen(ScreenNode):
    def Create(self):
        render_app(
            root=CounterApp,
            bind={
                'screen': self,
                'root': '/root',
                'app_id': 'pyreact_counter_demo',
                'base_namespace': 'PyreactBase',
            },
            log_perf=False,
        )

    def Destroy(self):
        runtime_system = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime_system is not None:
            runtime_system.UnmountApp({'app_id': 'pyreact_counter_demo'})
```

## JsonUI 约定

`render_app(..., bind={'root': '/root', ...})` 默认会把控件挂载到一个名为 `root` 的容器节点下。

如需打印每次更新的性能日志，可传入 `log_perf=True`：日志会输出组件执行 / VNode 构建 / Diff / 布局 / 原生 UI 应用耗时，并按总耗时降序列出本次更新中各 native API 的调用次数和总耗时。Diff 日志会额外汇总 CREATE / UPDATE / DELETE / MOVE 数量，布局日志会拆分 Shadow 树构建、measure/layout/stabilize 三轮耗时与文本测量缓存命中情况，便于定位列表/标签页切换卡顿来源。

native API 明细默认对应“应用到原生UI”阶段；`5.1` / `5.2` 会拆分原生控件应用与 `UpdateScreen`，`[native][update]` 行表示本次更新所有阶段（包括布局阶段文本测量等）触发的 native API 总耗时。

运行时会缓存重复的文本测量结果（有界 FIFO 淘汰）、原生控件/类型转换、Label/Image 属性、布局位置尺寸、按钮绑定、按钮三态槽位与 Scroll 路径，以减少列表切换等高频更新场景中的重复 native API 调用；控件删除或重建时会按路径前缀清理对应缓存。按钮 JSONUI 的 `default/hover/pressed` 三态槽位使用铺满按钮的 Image 预设：当 `buttonBuilder` 三态都返回无子节点、宽高均为 `100%` 的 `Image` 时，运行时会直接复用三态槽位自身应用 Image 属性，跳过额外子 Image 的布局与 clone；否则会把预设槽位 Image 设为透明，再按通用子树挂载逻辑渲染 builder 返回内容。`log_perf=True` 时会额外输出 `[button_slot] direct_image/subtree` 数量，便于确认按钮三态是否命中快路径。布局阶段会复用 VNode 上已标准化的 style 字典，跳过已有显式宽高 Label 的父级预测量，并在同一次三轮布局中复用上一轮已确定的 Label 尺寸，避免后续 layout/stabilize pass 反复命中文本测量缓存。首次挂载后禁止用整棵 Pyreact 子树重建兜底，Diff 后会按 mutation 计算受影响路径：结构变化提交受影响父子树，非布局属性更新只提交精确节点，未受影响分支不会进入 native commit；新建子树直接 clone/render，不再逐节点先探测已有控件。事件回调不会触发 native commit，但 `buttonBuilder` 会作为视觉生成函数参与 Diff。若一次 render 没有任何 VNode mutation，会跳过布局、native commit 与 `UpdateScreen`；若 incremental commit 后没有实际 native API 调用，也会跳过 `UpdateScreen`。

下面是一个最小 Screen JSON（同样可直接参考 `JsonUI/PyreactExample.json`）：

```json
{
  "main": {
    "type": "screen",
    "controls": [
      {
        "root": { "type": "panel", "layer": 1 }
      }
    ]
  },
  "namespace": "YourNamespace"
}
```

同时需要在资源包 `ui/` 里提供 `PyreactBase.json`，作为运行时创建控件时的基础 type_def（`panelBase` / `imageBase` / `textBase` / `itemBase` / `paperDollBase` / `buttonBase` / `inputBase` / `scrollBase`）。

## 公开组件补充

## 布局与定位

未设置 `position` 时等同于 `Position.relative`。相对定位节点仍占据原本的 Flex 流位置，然后只在视觉上按 `top/right/bottom/left` 偏移；同一轴同时设置时，`left` 优先于 `right`，`top` 优先于 `bottom`。

```python
from pyreact import Image, Position, Style

Image(style=Style(width=40, height=20, left=8, top=4))
```

`Position.absolute` 节点脱离 Flex 流，不挤占兄弟节点空间，并按父节点内容区解析 `top/right/bottom/left`。同时设置左右且未设置 `width` 时会撑满剩余宽度；同时设置上下且未设置 `height` 时会撑满剩余高度。

```python
Image(style=Style(position=Position.absolute, right=6, bottom=6, width=24, height=24))
```

### PaperDoll

`PaperDoll` 用于渲染网易纸娃娃控件。渲染类型使用 `RenderType.entity`、`RenderType.skeleton` 或 `RenderType.blockGeometry`，位置和尺寸仍写在 `style`，纸娃娃渲染参数写在 props。

```python
from pyreact import PaperDoll, RenderType, Style

PaperDoll(
    style=Style(width=80, height=100),
    renderType=RenderType.entity,
    entityIdentifier='minecraft:player',
    scale=1.0,
    initRotY=60,
)
```

常用 props：`entityId`、`entityIdentifier`、`skeletonModelName`、`animation`、`animationLooped`、`blockGeometryModelName`、`scale`、`renderDepth`、`initRotX/Y/Z`、`molangDict`、`rotationAxis`、`lightDirection`。

### 复合按钮

`FilledButton(default, hover=None, pressed=None, **kwargs)` 用纯色 Image 生成三态背景；`ImageButton(default, hover=None, pressed=None, imageBuilder=None, **kwargs)` 用自定义 `Image` 构建三态背景。两者都会继续接收普通 `Button` props，例如 `style`、`children`、`onClick`。

```python
from pyreact import FilledButton, Label, Colors, Style

FilledButton(
    default=Colors.black.withOpacity(0.5),
    hover=Colors.black.withOpacity(0.65),
    style=Style(width=120, height=32),
    children=[Label(content='OK', color=Colors.white)],
)
```

### Animated 与动画描述

`Animated` 包裹一个子节点，并把 `enter` / `animate` / `exit` 描述分发到非 `Panel` 后代。当前运行时支持 `opacity`、`translateX`、`translateY`、`width`、`height`；`Panel` 仍主要承担布局容器职责。

```python
from pyreact import Animated, Image, Style, fadeIn, Transition

Animated(
    key='notice_anim',
    enter=fadeIn(duration=180),
    animate=Transition({'translateY': 6}, duration=120),
    children=Image(style=Style(width=120, height=24)),
)
```

动画描述是 Python 侧的轻量对象；运行时按 `GameRenderTickEvent` 驱动已挂载控件，不复用废弃 grid 分支的旧布局实现。

## 目录结构

```
.
├── pyreact/                 # 框架：组件、hooks、diff、布局等
├── PyreactRuntimeScript/    # 运行时：ScreenNode 渲染桥接 & 系统
├── PyreactExampleScript/    # 示例：注册 UI、PushScreen、挂载示例 App
├── JsonUI/                  # UI JSON（基础 type_def + 示例 screen）
└── sync_to_test.cmd         # 本地同步脚本（可用参数覆盖默认路径）
```

## 现状

项目处于开发中，API/目录结构可能调整。欢迎根据示例脚本逐步集成与扩展。

