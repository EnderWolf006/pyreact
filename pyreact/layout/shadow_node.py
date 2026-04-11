# pyright: reportMissingParameterType=false, reportUnknownParameterType=false, reportImplicitOverride=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

class LayoutResult(object):
    def __init__(self,
                 x=0.0,
                 y=0.0,
                 abs_x=0.0,
                 abs_y=0.0,
                 width=0.0,
                 height=0.0,
                 padding_top=0.0,
                 padding_right=0.0,
                 padding_bottom=0.0,
                 padding_left=0.0,
                 margin_top=0.0,
                 margin_right=0.0,
                 margin_bottom=0.0,
                 margin_left=0.0,
                 final_layer=0,
                 native_depth=None,
                 native_final_layer=None,
                 content_width=0.0,
                 content_height=0.0):
        self.x = float(x)
        self.y = float(y)
        self.abs_x = float(abs_x)
        self.abs_y = float(abs_y)
        self.width = float(width)
        self.height = float(height)

        self.padding_top = float(padding_top)
        self.padding_right = float(padding_right)
        self.padding_bottom = float(padding_bottom)
        self.padding_left = float(padding_left)

        self.margin_top = float(margin_top)
        self.margin_right = float(margin_right)
        self.margin_bottom = float(margin_bottom)
        self.margin_left = float(margin_left)
        self.final_layer = int(final_layer)
        self.native_depth = native_depth
        if native_final_layer is None:
            self.native_final_layer = None
        else:
            self.native_final_layer = int(native_final_layer)

        self.content_width = float(content_width)
        self.content_height = float(content_height)

    def __repr__(self):
        return (
            "LayoutResult(x={0}, y={1}, width={2}, height={3}, content_w={4}, content_h={5})".format(
                self.x, self.y, self.width, self.height, self.content_width, self.content_height
            )
        )


class ShadowNode(object):
    def __init__(self, node_id, node_type, style=None, children=None, props=None, depth=1):
        self.node_id = node_id
        self.node_type = node_type
        self.style = style or {}
        self.props = props or {}
        self.children = children or []
        self.depth = int(depth)
        self.layout = None
        self._measured_shrunk = False

    def add_child(self, child):
        _ = self.children.append(child)

    def __repr__(self):
        return "ShadowNode(id={0}, type={1}, children={2})".format(
            self.node_id,
            self.node_type,
            len(self.children)
        )
