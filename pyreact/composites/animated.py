# -*- coding: utf-8 -*-

from pyreact.components.node_base import ComponentNode
from pyreact.components.primitives import clone_component


def _normalize_children(children):
    if children is None:
        return []
    if isinstance(children, (list, tuple)):
        return list(children)
    return [children]


def _merge_animation_prop(props, animation_config):
    next_props = dict(props or {})
    if next_props.get('__animation__') is None:
        next_props['__animation__'] = animation_config
    return next_props


def _attach_animation_to_root(node, animation_config, key=None):
    if not isinstance(node, ComponentNode):
        return node
    props = getattr(node, 'props', None) or {}
    next_props = dict(props)
    next_props = _merge_animation_prop(next_props, animation_config)
    if key is not None and next_props.get('key') is None:
        next_props['key'] = key
    cloned = clone_component(node, **next_props)
    if key is not None and getattr(cloned, 'key', None) is None:
        setattr(cloned, 'key', key)
    return cloned


def Animated(children=None, enter=None, exit=None, animate=None, key=None):
    child_list = _normalize_children(children)
    if not child_list:
        return None
    if len(child_list) > 1:
        raise ValueError('Animated expects exactly one child')
    child = child_list[0]
    if not isinstance(child, ComponentNode):
        return child
    if enter is None and exit is None and animate is None:
        if key is not None and getattr(child, 'key', None) is None:
            return clone_component(child, key=key)
        return child

    animation_config = {
        'enter': enter,
        'exit': exit,
        'animate': animate,
    }
    return _attach_animation_to_root(child, animation_config, key)


setattr(Animated, '__pyreact_component__', True)
