# Pyreact

面向 **网易我的世界（基岩版）ModSDK** 的 Python UI 声明式渲染框架（实验性）。

它提供类似 React 的组件函数 + Hooks 写法，把组件树（VNode）经过 Diff 与布局计算后，渲染为 **直接挂载到 `root` / `scroll_content` 的原生控件集合**。

## 特性

- **函数式组件**：通过 `@Component` 声明组件
- **Hooks**：`useState` / `useEffect` / `useMemo` / `useCallback` / `useRef`
- **基础控件**（Primitives）：`Panel` / `Image` / `Label` / `Button` / `Input` / `Scroll`
- **布局**：Flexbox 风格布局（子集），支持 `width/height/padding/margin/flexDirection/justifyContent/alignItems/...`
- **运行时桥接**：将组件树扁平渲染到 NetEase UI（通过 Runtime 系统统一管理挂载/卸载/重渲染）


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

`render_app(..., bind={'root': '/root', ...})` 默认会把控件扁平挂载到一个名为 `root` 的容器节点下；若节点位于 `Scroll` 内部，则直接挂到该 scroll 的 `scroll_content`。

从当前版本开始，`Button` / `Image` / `Input` / `Item` / `Label` 这 5 类 flat 控件在父容器存在对应 typed grid 时，会优先走 grid 批量创建，而不是逐个 `CreateChildControl`。默认要求：

- `root` 和 `scroll_content` 都继承 `PyreactBase.rootBase`
- `rootBase` 下保留 `buttonGrid` / `imageGrid` / `inputGrid` / `itemGrid` / `textGrid`
- grid item 模板保持 `xxxPanelBase -> widget@xxxBase` 结构

这 5 类 typed grid 默认会在 `JsonUI/PyreactBase.json` 里各自预分配 32 个槽位，运行时优先复用这些槽位，而不是每次 render 都把 `grid_dimensions` 重设为当前数量。只有当某类控件数量首次超过当前池容量，且仍未超过 runtime 里的该类最大池化上限时，才会额外调用一次 `SetGridDimension` 扩容。

运行时仍会在 `ScreenNode.Update()` 的下一帧里初始化新扩出来的 `widget`。因此这 5 类 grid 控件的 `size/position` 会作用在 `widget` 子节点上；其中 `Item` 的 `layer` 会设置到它的父 `panel`，避免直接给 `item_renderer` 本体设层级。上一帧用过、这一帧未使用的池化槽位会通过 `SetVisible(False, False)` 隐藏；从未使用过的预分配槽位保持 JSON 默认 `size=[0, 0]`，不会额外触发隐藏调用。对于 `Scroll` 内部的 typed grid，runtime 现在也会尽量保留已创建的 scroll 宿主与其 `scrolling_content` 子树，在 tab / 列表切换时优先复用已有 grid 实例，而不是每次都把整个宿主删掉后再重新 `SetGridDimension`。

`Panel` 现在是**纯布局节点**：它仍然是公开 primitive，用来组织 Flex / 定位 / children，但 runtime 不会为它单独创建原生 `panel` 控件。

如需打印分区式性能日志（按 `Mount/Update` 区分，展示主流程阶段、原生接口调用统计，以及存在延迟 grid 时的跨帧异步统计），可传入 `log_perf=True`。

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

同时需要在资源包 `ui/` 里提供 `PyreactBase.json`，作为运行时创建控件时的基础 type_def（`imageBase` / `textBase` / `buttonBase` / `inputBase` / `scrollBase`，以及按钮/滚动条内部模板依赖的基础定义）。如果你使用当前版本的 typed grid 优化，还需要保留 `rootBase` 及其 5 个 grid 定义，并让 JSON 里的初始 `grid_dimensions` 与 runtime 中 `_GRID_TYPE_CONFIG` 的默认池容量保持一致（当前默认初始 32、最大池化 64）。

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

