from pyreact import Component, Button, Style, ButtonState, Image, ComponentNode, Color, Colors


@Component
def FilledButton(default=Colors.transparent, hover=None, pressed=None, **kwargs):
    # type: (Color, Color, Color, **object) -> ComponentNode
    if hover is None and pressed is None:
        hover = default
        pressed = default
    elif hover is None:
        hover = pressed
    else:  # pressed is None
        pressed = hover

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