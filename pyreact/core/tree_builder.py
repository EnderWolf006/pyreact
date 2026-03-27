import warnings

try:
    from .vnode import VNode
except Exception:
    from vnode import VNode


class TreeBuilder(object):
    def __init__(self):
        self.fiber_map = {}
        self._missing_key_warnings = set()

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

        self._warn_missing_keys(children, parent_path)

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

    def _warn_missing_keys(self, children, parent_path):
        if len(children) <= 1:
            return

        parent_label = self._path_to_str(parent_path)
        index = 0
        for child in children:
            if not self._is_node_like(child):
                index += 1
                continue

            child_key = self._extract_child_key(child)
            if child_key is not None:
                index += 1
                continue

            warning_id = "%s:%s" % (parent_label, index)
            if warning_id in self._missing_key_warnings:
                index += 1
                continue

            self._missing_key_warnings.add(warning_id)
            child_type = self._child_type_name(child)
            warnings.warn(
                "Missing key for child at %s[%s] type=%s; when children has multiple elements, assign unique key for each sibling." % (
                    parent_label,
                    index,
                    child_type,
                ),
                RuntimeWarning,
            )
            index += 1

    def _extract_child_key(self, child):
        if child is None:
            return None

        if hasattr(child, 'key'):
            key = getattr(child, 'key')
            if key is not None:
                return key

        props = getattr(child, 'props', None)
        if isinstance(props, dict):
            return props.get('key')

        return None

    def _is_node_like(self, child):
        if child is None:
            return False
        if isinstance(child, VNode):
            return True
        return hasattr(child, 'node_type')

    def _child_type_name(self, child):
        if child is None:
            return 'None'
        node_type = getattr(child, 'node_type', None)
        if callable(node_type):
            return getattr(node_type, '__name__', 'component')
        if node_type is None:
            return 'unknown'
        return "%s" % node_type

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
