class Style(object):
    """Style object for DSL components.

    Only non-None fields are emitted by `to_dict()`.
    """
    _SUPPORTED_KEYS = [
        "width", "height",
        "minWidth", "maxWidth", "minHeight", "maxHeight", "minSize", "maxSize",
        "padding", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
        "margin", "marginTop", "marginRight", "marginBottom", "marginLeft",
        "flex", "flexDirection", "justifyContent", "alignItems", "alignSelf", "flexWrap",
        "position", "top", "left", "right", "bottom",
        "opacity", "display", "zIndex",
    ]

    def __init__(
        self,
        width=None,
        height=None,
        minWidth=None,
        maxWidth=None,
        minHeight=None,
        maxHeight=None,
        minSize=None,
        maxSize=None,
        padding=None,
        paddingTop=None,
        paddingRight=None,
        paddingBottom=None,
        paddingLeft=None,
        margin=None,
        marginTop=None,
        marginRight=None,
        marginBottom=None,
        marginLeft=None,
        flex=None,
        flexDirection=None,
        justifyContent=None,
        alignItems=None,
        alignSelf=None,
        flexWrap=None,
        position=None,
        top=None,
        left=None,
        right=None,
        bottom=None,
        opacity=None,
        display=None,
        zIndex=None,
    ):
        # type: (object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object, object) -> None
        self.width = width
        self.height = height
        self.minWidth = minWidth
        self.maxWidth = maxWidth
        self.minHeight = minHeight
        self.maxHeight = maxHeight
        self.minSize = minSize
        self.maxSize = maxSize

        self.padding = padding
        self.paddingTop = paddingTop
        self.paddingRight = paddingRight
        self.paddingBottom = paddingBottom
        self.paddingLeft = paddingLeft

        self.margin = margin
        self.marginTop = marginTop
        self.marginRight = marginRight
        self.marginBottom = marginBottom
        self.marginLeft = marginLeft

        self.flex = flex
        self.flexDirection = flexDirection
        self.justifyContent = justifyContent
        self.alignItems = alignItems
        self.alignSelf = alignSelf
        self.flexWrap = flexWrap

        self.position = position
        self.top = top
        self.left = left
        self.right = right
        self.bottom = bottom

        self.opacity = opacity
        self.display = display
        self.zIndex = zIndex

    def to_dict(self):
        data = {}
        for key, value in self.__dict__.items():
            if value is not None:
                data[key] = value
        return data

    @classmethod
    def from_value(cls, value):
        if value is None:
            return cls()
        if isinstance(value, Style):
            return value.copy()
        if isinstance(value, dict):
            style = cls()
            for key, item in value.items():
                setattr(style, key, item)
            return style
        raise TypeError("style must be Style or dict")

    @classmethod
    def merged(cls, *styles):
        result = cls()
        for style in styles:
            result.merge(style)
        return result

    def copy(self):
        return Style.from_value(self.to_dict())

    def merge(self, style=None, **kwargs):
        if style is not None:
            data = Style.from_value(style).to_dict()
            for key, value in data.items():
                setattr(self, key, value)
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        return self

    def __getitem__(self, key):
        return self.to_dict()[key]

    def get(self, key, default=None):
        return self.to_dict().get(key, default)

    def __contains__(self, key):
        return key in self.to_dict()
