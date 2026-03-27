class Mutation(object):
    def __init__(self, type_, path, old_node, new_node, changed_props=None):
        self.type_ = type_
        self.path = path or []
        self.old_node = old_node
        self.new_node = new_node
        self.changed_props = changed_props or {}

    def __repr__(self):
        return 'Mutation(type_=%r, path=%r)' % (self.type_, self.path)


class Reconciler(object):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    MOVE = 'MOVE'

    def reconcile(self, old_tree, new_tree):
        mutations = []
        self._diff_node([], old_tree, new_tree, mutations)
        return mutations

    def _diff_node(self, path, old_node, new_node, mutations):
        if old_node is None and new_node is None:
            return

        if old_node is None:
            mutations.append(Mutation(self.CREATE, path, None, new_node))
            return

        if new_node is None:
            mutations.append(Mutation(self.DELETE, path, old_node, None))
            return

        if not self._can_reuse(old_node, new_node):
            mutations.append(Mutation(self.DELETE, path, old_node, None))
            mutations.append(Mutation(self.CREATE, path, None, new_node))
            return

        changed_props = self._diff_props(old_node.props, new_node.props)
        if changed_props:
            mutations.append(
                Mutation(self.UPDATE, path, old_node, new_node, changed_props=changed_props)
            )

        self._diff_children(path, old_node.children, new_node.children, mutations)

    def _can_reuse(self, old_node, new_node):
        if old_node.node_type != new_node.node_type:
            return False

        old_key = getattr(old_node, 'key', None)
        new_key = getattr(new_node, 'key', None)
        if old_key is not None or new_key is not None:
            return old_key == new_key

        return True

    def _diff_props(self, old_props, new_props):
        old_props = old_props or {}
        new_props = new_props or {}
        changed = {}

        for key in new_props:
            if key not in old_props:
                changed[key] = new_props[key]
                continue

            old_value = old_props[key]
            new_value = new_props[key]
            if callable(old_value) and callable(new_value):
                # Event callbacks are re-created each render; handler table is
                # refreshed separately, so callback identity changes should not
                # force a DOM/node replacement.
                continue

            if old_value != new_value:
                changed[key] = new_props[key]

        for key in old_props:
            if key not in new_props:
                changed[key] = None

        return changed

    def _diff_children(self, parent_path, old_children, new_children, mutations):
        old_children = old_children or []
        new_children = new_children or []

        keyed_mode = self._has_keyed_children(old_children) or self._has_keyed_children(new_children)
        if keyed_mode:
            self._diff_children_by_key(parent_path, old_children, new_children, mutations)
        else:
            self._diff_children_by_position(parent_path, old_children, new_children, mutations)

    def _diff_children_by_position(self, parent_path, old_children, new_children, mutations):
        old_len = len(old_children)
        new_len = len(new_children)
        max_len = old_len if old_len > new_len else new_len

        index = 0
        while index < max_len:
            old_node = old_children[index] if index < old_len else None
            new_node = new_children[index] if index < new_len else None
            child_path = list(parent_path)
            child_path.append(index)
            self._diff_node(child_path, old_node, new_node, mutations)
            index += 1

    def _diff_children_by_key(self, parent_path, old_children, new_children, mutations):
        old_keyed = {}
        old_unkeyed = []
        old_index = 0
        while old_index < len(old_children):
            node = old_children[old_index]
            key = getattr(node, 'key', None)
            if key is None:
                old_unkeyed.append((old_index, node))
            elif key not in old_keyed:
                old_keyed[key] = (old_index, node)
            old_index += 1

        used_old_indexes = {}
        next_old_unkeyed = 0

        new_index = 0
        while new_index < len(new_children):
            new_node = new_children[new_index]
            new_key = getattr(new_node, 'key', None)
            child_path = list(parent_path)
            child_path.append(new_index)

            if new_key is not None:
                if new_key in old_keyed:
                    old_pos, old_node = old_keyed[new_key]
                    used_old_indexes[old_pos] = True
                    if old_pos != new_index:
                        mutations.append(Mutation(self.MOVE, child_path, old_node, new_node))
                    self._diff_node(child_path, old_node, new_node, mutations)
                else:
                    self._diff_node(child_path, None, new_node, mutations)
            else:
                if next_old_unkeyed < len(old_unkeyed):
                    old_pos, old_node = old_unkeyed[next_old_unkeyed]
                    next_old_unkeyed += 1
                    used_old_indexes[old_pos] = True
                    self._diff_node(child_path, old_node, new_node, mutations)
                else:
                    self._diff_node(child_path, None, new_node, mutations)

            new_index += 1

        old_index = 0
        while old_index < len(old_children):
            if old_index not in used_old_indexes:
                child_path = list(parent_path)
                child_path.append(old_index)
                self._diff_node(child_path, old_children[old_index], None, mutations)
            old_index += 1

    def _has_keyed_children(self, children):
        index = 0
        while index < len(children):
            if getattr(children[index], 'key', None) is not None:
                return True
            index += 1
        return False
