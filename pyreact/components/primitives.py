from .node_base import ComponentNode
from .component import Component
from .style import Style


def _normalize_style(style):
    if style is None:
        return None
    if isinstance(style, Style):
        return style.to_dict()
    if isinstance(style, dict):
        return style
    raise TypeError("style must be Style or dict")


def _normalize_children(children):
    if children is None:
        return []
    if isinstance(children, (list, tuple)):
        return list(children)
    return [children]


def _build_node(node_type, values):
    props = {}
    for key, value in values.items():
        if value is None:
            continue
        if key == "style":
            value = _normalize_style(value)
        elif key == "children":
            value = _normalize_children(value)
        props[key] = value

    if "children" not in props:
        props["children"] = []

    node = ComponentNode(node_type, props=props)

    # Promote key to an attribute so LayoutEngine can build stable node_id.
    # (LayoutEngine checks vnode.key, not props['key'])
    if isinstance(props, dict) and 'key' in props:
        try:
            node.key = props.get('key')
        except Exception:
            pass
        try:
            del props['key']
        except Exception:
            pass

    return node


def _clone_value(value):
    if isinstance(value, ComponentNode):
        props = {}
        for key, prop_value in (value.props or {}).items():
            props[key] = _clone_value(prop_value)
        cloned = ComponentNode(value.node_type, props=props)
        if hasattr(value, 'key'):
            try:
                cloned.key = value.key
            except Exception:
                pass
        return cloned
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            result[key] = _clone_value(item)
        return result
    if isinstance(value, list):
        return [_clone_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple([_clone_value(item) for item in value])
    return value


def clone_component(component, **overrides):
    if not isinstance(component, ComponentNode):
        raise TypeError("clone_component expects a ComponentNode")
    cloned = _clone_value(component)
    if not isinstance(cloned, ComponentNode):
        raise TypeError("clone_component expects a ComponentNode")
    props = getattr(cloned, 'props', None)
    if not isinstance(props, dict):
        props = {}
        cloned.props = props
    for key, value in overrides.items():
        if key == 'key':
            cloned.key = value
        else:
            props[key] = value
    return cloned


@Component
def Panel(style=None, children=None):
    # type: (object, object) -> ComponentNode
    """Create a Panel node.

    `children` accepts a single node or a list/tuple of nodes.
    """
    return _build_node(
        "Panel",
        {
            "style": style,
            "children": children,
        },
    )


@Component
def Image(
    style=None,
    src=None,
    color=None,
    grayscale=None,
    clipRatio=None,
    uv=None,
    uvSize=None,
    resizeMode=None,
    imageAdaptionType=None,
    nineSlice=None,
    nineSliceType=None,
    rotation=None,
    rotatePivot=None,
    children=None,
    onClick=None,
):
    # type: (object, object, object, object, object, object, object, object, object, object, object, object, object, object, object) -> ComponentNode
    """Create an Image node.

    Image render params are passed as props instead of style.
    """
    return _build_node(
        "Image",
        {
            "style": style,
            "src": src,
            "color": color,
            "grayscale": grayscale,
            "clipRatio": clipRatio,
            "uv": uv,
            "uvSize": uvSize,
            "resizeMode": resizeMode,
            "imageAdaptionType": imageAdaptionType,
            "nineSlice": nineSlice,
            "nineSliceType": nineSliceType,
            "rotation": rotation,
            "rotatePivot": rotatePivot,
            "children": children,
            "onClick": onClick,
        },
    )


@Component
def Label(
    style=None,
    children=None,
    content=None,
    color=None,
    fontSize=None,
    textAlign=None,
    linePadding=None,
    shadow=None,
):
    # type: (object, object, object, object, object, object, object, object) -> ComponentNode
    """Create a Label node."""
    return _build_node(
        "Label",
        {
            "style": style,
            "children": children,
            "content": content,
            "color": color,
            "fontSize": fontSize,
            "textAlign": textAlign,
            "linePadding": linePadding,
            "shadow": shadow,
        },
    )


@Component
def Item(style=None, children=None, identifier=None, aux=None, enchant=None, userData=None, itemDict=None):
    # type: (object, object, object, object, object, object, object) -> ComponentNode
    """Create an Item node backed by inventory_item_renderer."""
    return _build_node(
        "Item",
        {
            "style": style,
            "children": children,
            "identifier": identifier,
            "aux": aux,
            "enchant": enchant,
            "userData": userData,
            "itemDict": itemDict,
        },
    )


@Component
def PaperDoll(
    style=None,
    renderType=None,
    entityId=None,
    entityIdentifier=None,
    skeletonModelName=None,
    animation=None,
    animationLooped=None,
    blockGeometryModelName=None,
    scale=None,
    renderDepth=None,
    initRotX=None,
    initRotY=None,
    initRotZ=None,
    molangDict=None,
    rotationAxis=None,
    lightDirection=None,
):
    return _build_node(
        "PaperDoll",
        {
            "style": style,
            "renderType": renderType,
            "entityId": entityId,
            "entityIdentifier": entityIdentifier,
            "skeletonModelName": skeletonModelName,
            "animation": animation,
            "animationLooped": animationLooped,
            "blockGeometryModelName": blockGeometryModelName,
            "scale": scale,
            "renderDepth": renderDepth,
            "initRotX": initRotX,
            "initRotY": initRotY,
            "initRotZ": initRotZ,
            "molangDict": molangDict,
            "rotationAxis": rotationAxis,
            "lightDirection": lightDirection,
        },
    )


@Component
def Button(style=None, children=None, onClick=None, buttonBuilder=None, onTouch=None):
    # type: (object, object, object, object, object) -> ComponentNode
    """Create a Button node."""
    return _build_node(
        "Button",
        {
            "style": style,
            "children": children,
            "onClick": onClick,
            "onTouch": onTouch,
            "buttonBuilder": buttonBuilder,
        },
    )


@Component
def Input(style=None, value=None, onChange=None, placeholder=None, children=None):
    # type: (object, object, object, object, object) -> ComponentNode
    """Create an Input node."""
    return _build_node(
        "Input",
        {
            "style": style,
            "children": children,
            "value": value,
            "onChange": onChange,
            "placeholder": placeholder,
        },
    )


@Component
def Scroll(
    style=None,
    children=None,
    showScrollbar=True,
):
    # type: (object, object, bool) -> ComponentNode
    """Create a Scroll node."""
    return _build_node(
        "Scroll",
        {
            "style": style,
            "children": children,
            "showScrollbar": showScrollbar,
        },
    )
