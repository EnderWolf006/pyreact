# Pyreact

面向 **网易我的世界（基岩版）ModSDK** 的 Python UI 声明式渲染框架（实验性）。

它提供类似 React 的组件函数 + Hooks 写法，把组件树（VNode）经过 Diff 与布局计算后，渲染为 **ScreenNode / JsonUI 控件树**。

## 特性

- **函数式组件**：通过 `@Component` 声明组件
- **Hooks**：`useState` / `useEffect` / `useMemo` / `useCallback` / `useRef`
- **基础控件**（Primitives）：`Panel` / `Image` / `Label` / `Button` / `Input` / `Scroll`
- **布局**：Flexbox 风格布局（子集），支持 `width/height/padding/margin/flexDirection/justifyContent/alignItems/...`
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
        )

    def Destroy(self):
        runtime_system = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime_system is not None:
            runtime_system.UnmountApp({'app_id': 'pyreact_counter_demo'})
```

## JsonUI 约定

`render_app(..., bind={'root': '/root', ...})` 默认会把控件挂载到一个名为 `root` 的容器节点下。

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

同时需要在资源包 `ui/` 里提供 `PyreactBase.json`，作为运行时创建控件时的基础 type_def（`panelBase` / `imageBase` / `textBase` / `buttonBase` / `inputBase` / `scrollBase`）。

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

