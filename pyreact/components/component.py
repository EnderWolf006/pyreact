# -*- coding: utf-8 -*-

"""Component decorator utilities.

In this project, user components are plain Python functions that *return* UI
nodes (Panel/Image/Label/...).

`@Component` makes `key` and `ref` supported without forcing the inner function
to declare `key`/`ref` parameters.
"""


def Component(component_fn):
    if not callable(component_fn):
        raise TypeError("@Component expects a callable")

    def _wrapper(*args, **kwargs):
        key = None
        ref = None
        if isinstance(kwargs, dict):
            if 'key' in kwargs:
                key = kwargs.get('key')
                try:
                    del kwargs['key']
                except Exception:
                    pass
            if 'ref' in kwargs:
                ref = kwargs.get('ref')
                try:
                    del kwargs['ref']
                except Exception:
                    pass

        # Call user component with remaining props.
        # Supported styles:
        # - def Comp(**props)
        # - def Comp(props_dict)
        # - def Comp()
        # Also supports being invoked with positional dict by ComponentInstance.
        out = None

        # Common case 1: invoked by our TreeBuilder using kwargs (def Comp(**props)).
        if (not args) and isinstance(kwargs, dict) and kwargs:
            try:
                out = component_fn(**kwargs)
            except TypeError:
                try:
                    out = component_fn(kwargs)
                except TypeError:
                    out = component_fn()

        # Common case 2: invoked by ComponentInstance using a positional props dict.
        elif len(args) == 1 and (not kwargs) and isinstance(args[0], dict):
            props = args[0]
            try:
                out = component_fn(**props)
            except TypeError:
                try:
                    out = component_fn(props)
                except TypeError:
                    out = component_fn()

        # Fallback: call as-is, then try legacy fallbacks.
        else:
            try:
                out = component_fn(*args, **kwargs)
            except TypeError:
                try:
                    out = component_fn(kwargs)
                except TypeError:
                    out = component_fn()

        if out is None:
            return None

        # Attach key/ref to the returned root node.
        # Key is promoted to an attribute so LayoutEngine can build stable node_id.
        if key is not None:
            try:
                out.key = key
            except Exception:
                pass

        if ref is not None:
            try:
                props = getattr(out, 'props', None)
                if isinstance(props, dict):
                    props['ref'] = ref
                else:
                    out.ref = ref
            except Exception:
                pass

        return out

    try:
        _wrapper.__name__ = getattr(component_fn, '__name__', 'Component')
    except Exception:
        pass
    try:
        _wrapper.__doc__ = getattr(component_fn, '__doc__', None)
    except Exception:
        pass

    # Mark for potential introspection.
    try:
        _wrapper.__pyreact_component__ = True
        _wrapper.__pyreact_inner__ = component_fn
    except Exception:
        pass

    return _wrapper
