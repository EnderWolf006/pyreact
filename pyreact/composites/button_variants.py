# -*- coding: utf-8 -*-

from pyreact.components.color import Colors
from pyreact.components.component import Component
from pyreact.components.enums import ButtonState
from pyreact.components.node_base import ComponentNode
from pyreact.components.primitives import Button, Image, clone_component


def _resolve_button_states(default_value, hover, pressed):
    if hover is None and pressed is None:
        hover = default_value
        pressed = default_value
    elif hover is None:
        hover = pressed
    elif pressed is None:
        pressed = hover
    return {
        ButtonState.default: default_value,
        ButtonState.hover: hover,
        ButtonState.pressed: pressed,
    }


def _fill_image_size(image_node):
    props = getattr(image_node, 'props', None) or {}
    style = props.get('style')
    if not isinstance(style, dict):
        style = {}
    next_style = dict(style)
    next_style['width'] = '100%'
    next_style['height'] = '100%'
    return clone_component(image_node, style=next_style)


@Component
def FilledButton(default=Colors.transparent, hover=None, pressed=None, **kwargs):
    color_map = _resolve_button_states(default, hover, pressed)

    def builder(state):
        return Image(
            style={'width': '100%', 'height': '100%'},
            color=color_map.get(state),
        )

    kwargs['buttonBuilder'] = builder
    return Button(**kwargs)


@Component
def ImageButton(default, hover=None, pressed=None, imageBuilder=None, **kwargs):
    if not callable(imageBuilder):
        raise TypeError('ImageButton requires callable imageBuilder')
    src_map = _resolve_button_states(default, hover, pressed)

    def render_image(src, state):
        try:
            image_node = imageBuilder(src)
        except TypeError:
            image_node = imageBuilder(src, state)
        if not isinstance(image_node, ComponentNode) or image_node.node_type != 'Image':
            raise TypeError('ImageButton imageBuilder must return Image')
        return _fill_image_size(image_node)

    render_image(src_map.get(ButtonState.default), ButtonState.default)

    def builder(state):
        return render_image(src_map.get(state), state)

    kwargs['buttonBuilder'] = builder
    return Button(**kwargs)
