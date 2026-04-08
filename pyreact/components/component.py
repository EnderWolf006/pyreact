# -*- coding: utf-8 -*-

"""Component decorator utilities.

In this project, user components are plain Python functions that *return* UI
nodes (Panel/Image/Label/...).

`@Component` makes `key` and `ref` supported without forcing the inner function
to declare `key`/`ref` parameters.
"""

import inspect


_COMPONENT_REGISTRY = {}


def _extract_special_kwarg(kwargs, key):
    if not isinstance(kwargs, dict):
        return None
    return kwargs.pop(key, None)


def _call_with_fallbacks(component_fn, *attempts):
    last_error = None
    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    return None


def _get_component_argspec(component_fn):
    try:
        return inspect.getfullargspec(component_fn)
    except Exception:
        try:
            return inspect.getargspec(component_fn)
        except Exception:
            return None


def _accepts_kwargs(component_fn):
    spec = _get_component_argspec(component_fn)
    if spec is None:
        return False
    return bool(getattr(spec, 'varkw', None) or getattr(spec, 'keywords', None))


def _positional_arg_names(component_fn):
    spec = _get_component_argspec(component_fn)
    if spec is None:
        return []
    names = getattr(spec, 'args', None)
    if not isinstance(names, list):
        names = list(names or [])
    return names


def _invoke_component(component_fn, args, kwargs):
    if (not args) and isinstance(kwargs, dict) and kwargs:
        if _accepts_kwargs(component_fn):
            return component_fn(**kwargs)

        arg_names = _positional_arg_names(component_fn)
        if len(arg_names) == 1:
            return component_fn(kwargs)

        return component_fn(**kwargs)

    if len(args) == 1 and (not kwargs) and isinstance(args[0], dict):
        props = args[0]
        arg_names = _positional_arg_names(component_fn)
        if _accepts_kwargs(component_fn):
            return _call_with_fallbacks(
                component_fn,
                lambda: component_fn(**props),
                lambda: component_fn(props),
            )

        if len(arg_names) == 0:
            return component_fn()

        if len(arg_names) == 1:
            return _call_with_fallbacks(
                component_fn,
                lambda: component_fn(**props),
                lambda: component_fn(props),
            )

        return component_fn(**props)

    return _call_with_fallbacks(
        component_fn,
        lambda: component_fn(*args, **kwargs),
        lambda: component_fn(kwargs),
        lambda: component_fn(),
    )


def is_component(component_fn):
    return bool(_COMPONENT_REGISTRY.get(component_fn))


def Component(component_fn):
    if not callable(component_fn):
        raise TypeError("@Component expects a callable")

    def _wrapper(*args, **kwargs):
        key = _extract_special_kwarg(kwargs, 'key')
        ref = _extract_special_kwarg(kwargs, 'ref')

        # Call user component with remaining props.
        # Supported styles:
        # - def Comp(**props)
        # - def Comp(props_dict)
        # - def Comp()
        # Also supports being invoked with positional dict by ComponentInstance.
        out = _invoke_component(component_fn, args, kwargs)

        if out is None:
            return None

        # Attach key/ref to the returned root node.
        # Key is promoted to an attribute so LayoutEngine can build stable node_id.
        if key is not None:
            try:
                setattr(out, 'key', key)
            except Exception:
                pass

        if ref is not None:
            try:
                props = getattr(out, 'props', None)
                if isinstance(props, dict):
                    props['ref'] = ref
                else:
                    setattr(out, 'ref', ref)
            except Exception:
                pass

        return out

    for attr_name, fallback in [
        ('__name__', 'Component'),
        ('__doc__', None),
    ]:
        try:
            setattr(_wrapper, attr_name, getattr(component_fn, attr_name, fallback))
        except Exception:
            pass

    _COMPONENT_REGISTRY[_wrapper] = True

    return _wrapper
