class ComponentNode(object):
    def __init__(self, node_type, props=None):
        self.node_type = node_type
        self.props = props or {}
        self.key = self.props.get('key') if isinstance(self.props, dict) else None

    def __repr__(self):
        return "ComponentNode({}, props={})".format(self.node_type, self.props)


