# pyright: reportMissingParameterType=false, reportUnknownParameterType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from .flexbox import compute_layout, normalize_style
from .shadow_node import ShadowNode


class LayoutEngine(object):
    def __init__(self, text_measurer=None):
        self._text_measurer = text_measurer

    def _extract_style(self, vnode):
        props = getattr(vnode, "props", None)
        if not isinstance(props, dict):
            return {}
        return normalize_style(props.get("style", {}))

    def _extract_children(self, vnode):
        children = getattr(vnode, "children", None)
        if isinstance(children, (list, tuple)):
            return list(children)
        if children is not None:
            return children
        props = getattr(vnode, "props", None)
        if isinstance(props, dict):
            children = props.get("children")
            if isinstance(children, (list, tuple)):
                return list(children)
            if children is not None:
                return children
        return []

    def _extract_node_type(self, vnode):
        node_type = getattr(vnode, "node_type", None)
        if node_type is None:
            return "Panel"
        return str(node_type)

    def _extract_node_id(self, vnode, path):
        key = getattr(vnode, "key", None)
        if key is not None:
            return "k_{0}".format(self._sanitize_id_part(str(key)))
        if not path:
            return "root"
        parts = []
        for segment in path:
            parts.append(str(segment))
        return "p_{0}".format("_".join(parts))

    def _sanitize_id_part(self, value):
        if value is None:
            return ""
        out = []
        for ch in str(value):
            if ch.isalnum() or ch in ("_", "-", "."):
                out.append(ch)
            else:
                out.append("_%02x" % ord(ch))
        return "".join(out)

    def _extract_props(self, vnode):
        props = getattr(vnode, "props", None)
        if not isinstance(props, dict):
            return {}
        result = {}
        for k, v in props.items():
            if k not in ("style", "children"):
                result[k] = v
        return result

    def _build_shadow_tree(self, vnode, path=None):
        if path is None:
            path = []

        shadow_node = ShadowNode(
            node_id=self._extract_node_id(vnode, path),
            node_type=self._extract_node_type(vnode),
            style=self._extract_style(vnode),
            props=self._extract_props(vnode),
            children=[],
        )

        index = 0
        for child in self._extract_children(vnode):
            child_path = list(path)
            child_path.append(index)
            shadow_node.add_child(self._build_shadow_tree(child, child_path))
            index += 1
        return shadow_node

    def calculate(self, vnode_tree, screen_width, screen_height):
        root = self._build_shadow_tree(vnode_tree)

        compute_layout(
            root,
            x=0.0,
            y=0.0,
            available_width=float(screen_width),
            available_height=float(screen_height),
            forced_width=float(screen_width),
            forced_height=float(screen_height),
            text_measurer=self._text_measurer,
            measure_pass=True,
        )

        compute_layout(
            root,
            x=0.0,
            y=0.0,
            available_width=float(screen_width),
            available_height=float(screen_height),
            forced_width=float(screen_width),
            forced_height=float(screen_height),
            text_measurer=self._text_measurer,
            measure_pass=False,
        )

        # Stabilize parent alignment after child intrinsic sizes are resolved.
        compute_layout(
            root,
            x=0.0,
            y=0.0,
            available_width=float(screen_width),
            available_height=float(screen_height),
            forced_width=float(screen_width),
            forced_height=float(screen_height),
            text_measurer=self._text_measurer,
            measure_pass=False,
        )

        return root
