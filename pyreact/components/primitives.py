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


def _build_node(node_type, values, include_children=False):
    props = {}
    for key, value in values.items():
        if value is None:
            continue
        if key == "style":
            value = _normalize_style(value)
        elif key == "children":
            value = _normalize_children(value)
        props[key] = value

    if include_children and "children" not in props:
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


@Component
def Panel(style=None, children=None, onClick=None):
    # type: (object, object, object) -> ComponentNode
    """Create a Panel node.

    `children` accepts a single node or a list/tuple of nodes.
    """
    return _build_node(
        "Panel",
        {
            "style": style,
            "children": children,
            "onClick": onClick,
        },
        include_children=True,
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
        include_children=True,
    )


@Component
def Label(
    style=None,
    content=None,
    color=None,
    fontSize=None,
    font=None,
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
            "content": content,
            "color": color,
            "fontSize": fontSize,
            "font": font,
            "textAlign": textAlign,
            "linePadding": linePadding,
            "shadow": shadow,
        },
    )


@Component
def Item(style=None, identifier=None, aux=None, enchant=None, userData=None, itemDict=None):
    # type: (object, object, object, object, object, object) -> ComponentNode
    """Create an Item node backed by inventory_item_renderer."""
    return _build_node(
        "Item",
        {
            "style": style,
            "identifier": identifier,
            "aux": aux,
            "enchant": enchant,
            "userData": userData,
            "itemDict": itemDict,
        },
    )


@Component
def Button(style=None, children=None, onClick=None, onLongPress=None, buttonBuilder=None):
    # type: (object, object, object, object, object) -> ComponentNode
    """Create a Button node."""
    return _build_node(
        "Button",
        {
            "style": style,
            "children": children,
            "onClick": onClick,
            "onLongPress": onLongPress,
            "buttonBuilder": buttonBuilder,
        },
        include_children=True,
    )


@Component
def Input(style=None, value=None, onChange=None, placeholder=None):
    # type: (object, object, object, object) -> ComponentNode
    """Create an Input node."""
    return _build_node(
        "Input",
        {
            "style": style,
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
        include_children=True,
    )
