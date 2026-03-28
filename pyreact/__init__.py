from .components import (
    Style,
    AlignItems,
    JustifyContent,
    FlexDirection,
    FontSize,
    Color,
    Colors,
    Position,
    ButtonState,
    ComponentNode,
    Component,
    Panel,
    Image,
    Label,
    Item,
    Button,
    Input,
    Scroll,
)

from .core import (
    useState,
    useEffect,
    useMemo,
    useCallback,
    useRef,
)


def render_app(
    root,
    bind=None,
):
    if bind is None:
        raise ValueError("native mode requires bind dict")

    # Enforce component decorator for the root component.
    # Reason: only @Component guarantees key/ref support and consistent behavior.
    if not callable(root):
        raise TypeError("render_app(root=...) must be a callable component")
    if not getattr(root, '__pyreact_component__', False):
        name = getattr(root, '__name__', 'root')
        raise TypeError(
            "render_app root component '%s' must be decorated with @Component (to support key/ref)." % name
        )

    if not isinstance(bind, dict):
        raise TypeError("bind must be dict")

    screen = bind.get("screen")
    root_path = bind.get("root") or bind.get("root_path") or "/root"
    app_id = bind.get("app_id") or bind.get("appId") or "pyreact_app"
    base_namespace = bind.get("base_namespace") or bind.get("baseNamespace") or "PyreactBase"

    if screen is None:
        raise ValueError("bind.screen is required in runtime mode")

    runtime_system = bind.get("runtime_system")
    if runtime_system is None:
        import mod.client.extraClientApi as clientApi
        runtime_system = clientApi.GetSystem("PyreactRuntimeMod", "PyreactRuntimeClientSystem")

    if runtime_system is None:
        raise RuntimeError("PyreactRuntimeClientSystem not found")

    return runtime_system.MountApp({
        "app_id": app_id,
        "screen": screen,
        "root_path": root_path,
        "app_fn": root,
        "base_namespace": base_namespace,
    })


__all__ = [
    "Style",
    "AlignItems",
    "JustifyContent",
    "FlexDirection",
    "FontSize",
    "Color",
    "Colors",
    "Position",
    "ButtonState",
    "ComponentNode",
    "Component",
    "Panel",
    "Image",
    "Label",
    "Item",
    "Button",
    "Input",
    "Scroll",
    "useState",
    "useEffect",
    "useMemo",
    "useCallback",
    "useRef",
    "render_app",
]
