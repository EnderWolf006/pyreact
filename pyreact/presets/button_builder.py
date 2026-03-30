from pyreact import Image, ButtonState, Style


def flat_button_builder_preset(default, hover, pressed):
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
    return builder