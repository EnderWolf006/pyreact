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
    # NetEase UI runtime uses font size as a scale factor.
    # (Passed to native SetTextFontSize(scale))
    small = 0.5
    normal = 1.0
    large = 2.0
    extraLarge = 4.0


class Position(object):
    relative = "relative"
    absolute = "absolute"


class ButtonState(object):
    default = "default"
    hover = "hover"
    pressed = "pressed"
