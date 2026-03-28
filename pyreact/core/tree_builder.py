try:
    from .vnode import VNode
except Exception:
    from vnode import VNode


class TreeBuilder(object):
    def __init__(self):
        self.fiber_map = {}

    def build_tree(self, root_element):
        return self._build_node(root_element, [])

    def _build_node(self, element, path):
        if element is None:
            return None

        if isinstance(element, VNode):
            return element

        node_type = getattr(element, 'node_type', None)
        props = getattr(element, 'props', None) or {}

        if callable(node_type):
            self._assert_component_decorated(node_type, path)
            key = self._extract_key(element, props)
            vnode_props = self._normalize_props(props)
            rendered = self._call_component(node_type, vnode_props)
            rendered_children = self._normalize_children(rendered)
            vnode_children = self._build_children(rendered_children, path)
            vnode = VNode(node_type, vnode_props, vnode_children, key=key)
            self.fiber_map[self._path_to_str(path)] = {
                'component': node_type,
                'props': vnode_props,
                'node': vnode,
            }
            return vnode

        key = self._extract_key(element, props)
        vnode_props = self._normalize_props(props)
        raw_children = self._extract_children(props)
        vnode_children = self._build_children(raw_children, path)
        return VNode(node_type, vnode_props, vnode_children, key=key)

    def _assert_component_decorated(self, component_fn, path):
        # Components must be decorated with @Component so they can accept key/ref
        # without forcing the inner function signature.
        if getattr(component_fn, '__pyreact_component__', False):
            return

        # Provide a clear error location.
        try:
            label = self._path_to_str(path)
        except Exception:
            label = 'root'

        try:
            name = getattr(component_fn, '__name__', 'component')
        except Exception:
            name = 'component'

        raise TypeError(
            "Component '%s' at %s must be decorated with @Component (required for key/ref support)." % (
                name,
                label,
            )
        )

    def _build_children(self, children, parent_path):
        if children is None:
            return []

        if not isinstance(children, list):
            children = [children]

        result = []
        index = 0
        for child in children:
            child_path = list(parent_path)
            child_path.append(index)
            built = self._build_node(child, child_path)
            if built is not None:
                result.append(built)
            index += 1
        return result

    def _call_component(self, component_fn, props):
        try:
            return component_fn(**props)
        except TypeError:
            try:
                return component_fn(props)
            except TypeError:
                return component_fn()

    def _extract_children(self, props):
        children = props.get('children', [])
        return self._normalize_children(children)

    def _normalize_children(self, children):
        if children is None:
            return []
        if isinstance(children, (list, tuple)):
            return list(children)
        return [children]

    def _normalize_props(self, props):
        normalized = {}
        for key in props:
            if key != 'children':
                normalized[key] = props[key]
        return normalized

    def _extract_key(self, element, props):
        if hasattr(element, 'key'):
            key = getattr(element, 'key')
            if key is not None:
                return key
        return props.get('key')

    def _path_to_str(self, path):
        if not path:
            return 'root'
        return '.'.join([str(i) for i in path])


def build_tree(root_element):
    builder = TreeBuilder()
    return builder.build_tree(root_element)
