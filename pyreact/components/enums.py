class AlignItems(object):
    start = "start"
    center = "center"
    end = "end"
    stretch = "stretch"


class JustifyContent(object):
    start = "start"
    center = "center"
    end = "end"
    spaceBetween = "spaceBetween"
    spaceAround = "spaceAround"


class FlexDirection(object):
    row = "row"
    column = "column"
    rowReverse = "rowReverse"
    columnReverse = "columnReverse"


class FontSize(object):
    # Usage-side fontSize is logical text size.
    # Runtime converts it to NetEase native SetTextFontSize(scale)
    # with 16 fontSize == 1.0 scale.
    small = 8
    normal = 16
    large = 32
    extraLarge = 64


class Position(object):
    relative = "relative"
    absolute = "absolute"


class ButtonState(object):
    default = "default"
    hover = "hover"
    pressed = "pressed"
