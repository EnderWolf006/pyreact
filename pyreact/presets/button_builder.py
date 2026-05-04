# coding=utf-8
from pyreact.components import Image, ButtonState, Style

def flat_button_builder_preset(default, hover=None, pressed=None):
    if hover is None and pressed is None:
        hover = default
        pressed = default
    elif hover is None:
        hover = pressed
    else: # pressed is None
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
    return builder
