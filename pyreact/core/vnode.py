class VNode(object):
    def __init__(self, node_type, props, children, key=None):
        self.node_type = node_type
        self.props = props or {}
        self.children = children or []
        self.key = key
        self._component_fn = node_type if callable(node_type) else None

    def is_component(self):
        return callable(self.node_type)

    def clone(self, props=None, children=None):
        return VNode(
            self.node_type,
            self.props if props is None else props,
            self.children if children is None else children,
            key=self.key,
        )

    def __repr__(self):
        type_name = self.node_type
        if callable(self.node_type):
            type_name = getattr(self.node_type, '__name__', 'component')
        return 'VNode(type=%r, key=%r, children=%d)' % (
            type_name,
            self.key,
            len(self.children),
        )
