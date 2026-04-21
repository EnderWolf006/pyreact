# -*- coding: utf-8 -*-

from pyreact.components.node_base import ComponentNode
from pyreact.components.primitives import clone_component


def _is_virtual_container(node):
    """Panel 是扁平化架构里的虚拟节点，没有 native 控件。"""
    if not isinstance(node, ComponentNode):
        return False
    return getattr(node, 'node_type', None) == 'Panel'


def _extract_children(child):
    props = getattr(child, 'props', None)
    if not isinstance(props, dict):
        return []
    raw = props.get('children')
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    return [raw]


def _distribute_animation(node, anim_config, key_prefix=None, index=0):
    """Walk ``node`` and its children, attaching ``anim_config`` to every
    entity node encountered.

    See module docstring on Animated for the design rationale.
    """
    if not isinstance(node, ComponentNode):
        return node

    props = getattr(node, 'props', None) or {}
    if isinstance(props, dict) and isinstance(props.get('__animation__'), dict):
        return node

    node_key = getattr(node, 'key', None)

    # Prefix passed down to children. Must stay globally unique across
    # nested Panels (each Panel resets its child index to 0, so we fold the
    # current index into the prefix when descending past a key-less node).
    if node_key is not None:
        child_prefix = node_key
    elif key_prefix is not None:
        child_prefix = '%s_%d' % (key_prefix, index)
    else:
        child_prefix = None

    raw_children = _extract_children(node)
    new_children = None
    if raw_children:
        new_children = []
        child_index = 0
        for c in raw_children:
            new_children.append(_distribute_animation(c, anim_config, child_prefix, child_index))
            child_index += 1

    is_entity = not _is_virtual_container(node)
    clone_kwargs = {}
    if new_children is not None:
        clone_kwargs['children'] = new_children
    if is_entity:
        clone_kwargs['__animation__'] = anim_config

    if not clone_kwargs:
        return node

    cloned = clone_component(node, **clone_kwargs)
    if node_key is not None:
        try:
            cloned.key = node_key
        except Exception:
            pass
    elif is_entity and key_prefix is not None:
        try:
            cloned.key = '%s__anim_%d' % (key_prefix, index)
        except Exception:
            pass
    return cloned


def Animated(enter=None, exit=None, animate=None, children=None, key=None):
    """Declarative animation wrapper.

    Wraps a single child component and attaches an animation config to every
    entity descendant. All interpolation runs in Python on every frame via
    ``GameRenderTickEvent``; no native animation APIs are used.

    Implementation note: this is a plain function, not a ``@Component``.
    The decorator strips ``key`` before calling the inner function, but we
    need ``key`` *inside* to use as the prefix for synthesizing stable keys
    on distributed entity children. Without that prefix, sibling list
    reorders desync animations across re-renders. By being a plain function
    we receive ``key`` directly.

    Parameters
    ----------
    enter : Animation, optional
        Plays once when the wrapped node is first mounted.
    exit : Animation, optional
        Plays before the wrapped node is removed. The node remains alive
        until the animation completes; native removal is deferred.
    animate : dict or Transition, optional
        Target values for continuous transition. When the target changes
        between renders, a new tween is started from the currently
        applied value to the new target.
    children : ComponentNode
        The single component node to animate. Multi-children must be
        wrapped in a Panel first.
    key : optional
        Identity for the wrapper itself (required when used in lists).
        Also used as the prefix for synthesizing stable keys on distributed
        entity descendants.
    """
    if children is None:
        return None

    if isinstance(children, (list, tuple)):
        if not children:
            return None
        if len(children) > 1:
            raise TypeError(
                "Animated expects a single ComponentNode child; wrap multiple children in a Panel."
            )
        child = children[0]
    else:
        child = children

    if not isinstance(child, ComponentNode):
        raise TypeError("Animated children must be a ComponentNode returned by a primitive/component call")

    if enter is None and exit is None and animate is None:
        if key is not None and getattr(child, 'key', None) is None:
            try:
                child.key = key
            except Exception:
                pass
        return child

    anim_config = {
        "enter": enter,
        "exit": exit,
        "animate": animate,
    }

    # Use the explicit ``key`` argument (or the child's own key) as the prefix
    # for synthesizing stable keys on entity descendants.
    prefix = key if key is not None else getattr(child, 'key', None)
    result = _distribute_animation(child, anim_config, key_prefix=prefix, index=0)

    if isinstance(result, ComponentNode):
        if key is not None:
            try:
                result.key = key
            except Exception:
                pass
        elif getattr(result, 'key', None) is None and getattr(child, 'key', None) is not None:
            try:
                result.key = child.key
            except Exception:
                pass

    return result


# Mark Animated as a "component-like" callable so the tree builder accepts
# it without requiring the @Component decorator (we hand-roll key handling
# above, which the decorator would otherwise interfere with).
try:
    Animated.__pyreact_component__ = True
except Exception:
    pass
