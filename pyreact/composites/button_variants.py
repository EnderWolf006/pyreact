from pyreact import Component, Button, Style, ButtonState, Image, ComponentNode, Color, Colors, clone_component


def _resolve_button_states(default_value, hover, pressed):
    if hover is None and pressed is None:
        hover = default_value
        pressed = default_value
    elif hover is None:
        hover = pressed
    elif pressed is None:
        pressed = hover
    return hover, pressed


def _fill_image_size(image_node):
    props = getattr(image_node, 'props', None)
    style = None
    if isinstance(props, dict):
        style = props.get('style')

    style_props = {}
    if isinstance(style, dict):
        style_props.update(style)

    style_props['height'] = '100%'
    style_props['width'] = '100%'
    return clone_component(image_node, style=style_props)

@Component
def FilledButton(default=Colors.transparent, hover=None, pressed=None, **kwargs):
    # type: (Color, Color, Color, **object) -> ComponentNode
    hover, pressed = _resolve_button_states(default, hover, pressed)

    def builder(state):
        color_map = {
            ButtonState.default: default,
            ButtonState.hover: hover,
            ButtonState.pressed: pressed
        }
        return Image(
            style=Style(
                height="100%",
                width="100%",
            ),
            color=color_map[state],
        )
    return Button(
        buttonBuilder=builder,
        **kwargs
    )


@Component
def ImageButton(default, hover=None, pressed=None, imageBuilder=None, **kwargs):
    # type: (str, str, str, object, **object) -> ComponentNode
    if not callable(imageBuilder):
        raise TypeError('ImageButton(..., imageBuilder=...) requires a callable imageBuilder')

    hover, pressed = _resolve_button_states(default, hover, pressed)

    def render_image(src, state):
        try:
            image_node = imageBuilder(src)
        except TypeError:
            image_node = imageBuilder(src, state)

        if not isinstance(image_node, ComponentNode):
            raise TypeError('ImageButton imageBuilder(src[, state]) must return a ComponentNode')

        if getattr(image_node, 'node_type', None) != 'Image':
            raise TypeError('ImageButton imageBuilder(src[, state]) must return an Image component node')

        return _fill_image_size(image_node)

    render_image(default, ButtonState.default)

    def builder(state):
        src_map = {
            ButtonState.default: default,
            ButtonState.hover: hover,
            ButtonState.pressed: pressed,
        }
        return render_image(src_map[state], state)

    return Button(
        buttonBuilder=builder,
        **kwargs
    )
