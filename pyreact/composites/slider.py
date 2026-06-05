# -*- coding: utf-8 -*-

from pyreact.components.color import Colors
from pyreact.components.component import Component
from pyreact.components.enums import AlignItems, FlexDirection, JustifyContent, Position
from pyreact.components.primitives import Button, Image, Label, Panel
from pyreact.components.style import Style
from pyreact.core.hooks import useRef, useState


_TOUCH_UP = 0
_TOUCH_DOWN = 1
_TOUCH_CANCEL = 3
_TOUCH_MOVE = 4
_TOUCH_MOVE_OUT = 6
_TOUCH_SCREEN_EXIT = 7


def _style_dict(style):
    if style is None:
        return {}
    if isinstance(style, Style):
        return style.to_dict()
    if isinstance(style, dict):
        return dict(style)
    raise TypeError('Slider style props must be Style or dict')


def _clamp(value, low, high):
    try:
        value = float(value)
    except Exception:
        value = low
    if value < low:
        return low
    if value > high:
        return high
    return value


def _round_step(value, low, step):
    if step is None:
        return value
    try:
        step_value = float(step)
    except Exception:
        return value
    if step_value <= 0:
        return value
    return low + round((value - low) / step_value) * step_value


def _format_value(value):
    try:
        if int(value) == value:
            return str(int(value))
    except Exception:
        pass
    try:
        return ('%.2f' % value).rstrip('0').rstrip('.')
    except Exception:
        return str(value)


def _read_global_position(control):
    if control is None:
        return None
    for name in ('GetGlobalPosition', 'GetPosition'):
        if hasattr(control, name):
            try:
                pos = getattr(control, name)()
                if pos and len(pos) >= 2:
                    return (float(pos[0]), float(pos[1]))
            except Exception:
                pass
    return None


def _read_global_position_from_ref(ref_obj):
    screen = getattr(ref_obj, 'screen', None)
    path = getattr(ref_obj, 'nativePath', None)
    if screen is not None and path and hasattr(screen, 'GetGlobalPosition'):
        try:
            pos = screen.GetGlobalPosition(path)
            if pos and len(pos) >= 2:
                return (float(pos[0]), float(pos[1]))
        except Exception:
            pass
    return _read_global_position(getattr(ref_obj, 'current', None))


def _read_size(control):
    if control is None:
        return None
    if hasattr(control, 'GetSize'):
        try:
            size = control.GetSize()
            if size and len(size) >= 2:
                return (float(size[0]), float(size[1]))
        except Exception:
            pass
    return None


def _read_size_from_ref(ref_obj):
    screen = getattr(ref_obj, 'screen', None)
    path = getattr(ref_obj, 'nativePath', None)
    if screen is not None and path and hasattr(screen, 'GetSize'):
        try:
            size = screen.GetSize(path)
            if size and len(size) >= 2:
                return (float(size[0]), float(size[1]))
        except Exception:
            pass
    return _read_size(getattr(ref_obj, 'current', None))


def _set_size(control, width, height):
    if control is None:
        return False
    try:
        size = (int(round(width)), int(round(height)))
    except Exception:
        return False
    if hasattr(control, 'SetSize'):
        try:
            control.SetSize(size, True)
            return True
        except TypeError:
            try:
                control.SetSize(size)
                return True
            except Exception:
                pass
        except Exception:
            pass
    if hasattr(control, 'SetFullSize'):
        try:
            control.SetFullSize(axis='x', paramDict={'absoluteValue': float(size[0]), 'followType': 'none', 'relativeValue': 0.0})
            control.SetFullSize(axis='y', paramDict={'absoluteValue': float(size[1]), 'followType': 'none', 'relativeValue': 0.0})
            return True
        except Exception:
            pass
    return False


def _set_size_from_ref(ref_obj, width, height):
    screen = getattr(ref_obj, 'screen', None)
    path = getattr(ref_obj, 'nativePath', None)
    try:
        size = (int(round(width)), int(round(height)))
    except Exception:
        return False
    if screen is not None and path and hasattr(screen, 'SetSize'):
        try:
            screen.SetSize(path, size, True)
            return True
        except TypeError:
            try:
                screen.SetSize(path, size)
                return True
            except Exception:
                pass
        except Exception:
            pass
    return _set_size(getattr(ref_obj, 'current', None), width, height)


def _set_position(control, x, y):
    if control is None:
        return False
    try:
        pos = (int(round(x)), int(round(y)))
    except Exception:
        return False
    if hasattr(control, 'SetPosition'):
        try:
            control.SetPosition(pos)
            return True
        except TypeError:
            try:
                control.SetPosition(pos[0], pos[1])
                return True
            except Exception:
                pass
        except Exception:
            pass
    if hasattr(control, 'SetFullPosition'):
        try:
            control.SetFullPosition(axis='x', paramDict={'absoluteValue': float(pos[0]), 'followType': 'none', 'relativeValue': 0.0})
            control.SetFullPosition(axis='y', paramDict={'absoluteValue': float(pos[1]), 'followType': 'none', 'relativeValue': 0.0})
            return True
        except Exception:
            pass
    return False


def _set_position_from_ref(ref_obj, x, y):
    screen = getattr(ref_obj, 'screen', None)
    path = getattr(ref_obj, 'nativePath', None)
    try:
        pos = (int(round(x)), int(round(y)))
    except Exception:
        return False
    if screen is not None and path and hasattr(screen, 'SetPosition'):
        try:
            screen.SetPosition(path, pos)
            return True
        except Exception:
            pass
    return _set_position(getattr(ref_obj, 'current', None), x, y)


@Component
def Slider(
    value=None,
    defaultValue=0,
    min=0,
    max=100,
    step=None,
    onChange=None,
    onDragStart=None,
    onDragEnd=None,
    disabled=False,
    style=None,
    trackStyle=None,
    fillStyle=None,
    thumbStyle=None,
    trackColor=None,
    fillColor=None,
    thumbColor=None,
    showValue=False,
):
    low = float(min)
    high = float(max)
    if high < low:
        low, high = high, low
    if high == low:
        high = low + 1.0

    internal_value, set_internal_value = useState(defaultValue)
    dragging, set_dragging = useState(False)
    track_ref = useRef(None)
    fill_ref = useRef(None)
    thumb_ref = useRef(None)
    latest_value_ref = useRef(defaultValue)
    controlled = value is not None
    current_value = value if controlled else internal_value
    current_value = _clamp(_round_step(current_value, low, step), low, high)
    latest_value_ref.current = current_value
    percent = (current_value - low) * 100.0 / (high - low)
    if percent < 0:
        percent = 0.0
    if percent > 100:
        percent = 100.0

    base_style = {
        'width': 180,
        'height': 28,
        'flexDirection': FlexDirection.row,
        'alignItems': AlignItems.center,
        'justifyContent': JustifyContent.center,
    }
    base_style.update(_style_dict(style))

    bar_style = {
        'width': '100%',
        'height': 6,
        'justifyContent': JustifyContent.center,
    }
    bar_style.update(_style_dict(trackStyle))

    active_fill_style = {
        'width': '%.3f%%' % percent,
        'height': '100%',
        'position': Position.absolute,
        'left': 0,
        'top': 0,
    }
    active_fill_style.update(_style_dict(fillStyle))

    knob_style = {
        'width': 14,
        'height': 14,
        'position': Position.absolute,
        'left': '%.3f%%' % percent,
        'top': -4,
        'marginLeft': -7,
        'alignItems': AlignItems.center,
        'justifyContent': JustifyContent.center,
        'zIndex': 3,
    }
    knob_style.update(_style_dict(thumbStyle))

    if trackColor is None:
        trackColor = Colors.black.withAlpha(0.28)
    if fillColor is None:
        fillColor = Colors.dodgerBlue
    if thumbColor is None:
        thumbColor = Colors.white

    def sync_native_visual(next_value, track_pos=None, track_size=None):
        if track_pos is None:
            track_pos = _read_global_position_from_ref(track_ref)
        if track_size is None:
            track_size = _read_size_from_ref(track_ref)
        if track_pos is None or track_size is None or track_size[0] <= 0:
            return
        ratio = (next_value - low) / (high - low)
        ratio = _clamp(ratio, 0.0, 1.0)
        fill_width = track_size[0] * ratio
        thumb_size = _read_size_from_ref(thumb_ref)
        thumb_width = 14.0
        thumb_height = 14.0
        if thumb_size is not None:
            thumb_width = thumb_size[0]
            thumb_height = thumb_size[1]
        _set_size_from_ref(fill_ref, fill_width, track_size[1])
        _set_position_from_ref(thumb_ref, fill_width - thumb_width / 2.0, (track_size[1] - thumb_height) / 2.0)

    def commit_from_touch(args):
        if disabled:
            return
        pos = _read_global_position_from_ref(track_ref)
        size = _read_size_from_ref(track_ref)
        if pos is None or size is None or size[0] <= 0:
            return
        try:
            touch_x = float(args.get('TouchPosX'))
        except Exception:
            return
        ratio = (touch_x - pos[0]) / size[0]
        ratio = _clamp(ratio, 0.0, 1.0)
        next_value = low + (high - low) * ratio
        next_value = _clamp(_round_step(next_value, low, step), low, high)
        latest_value_ref.current = next_value
        sync_native_visual(next_value, pos, size)
        if not controlled:
            set_internal_value(next_value)
        if callable(onChange):
            onChange(next_value)

    def handle_touch(args):
        if args is None:
            args = {}
        event_type = args.get('TouchEvent')
        if event_type == _TOUCH_DOWN:
            set_dragging(True)
            if callable(onDragStart):
                onDragStart(current_value)
            commit_from_touch(args)
        elif event_type == _TOUCH_MOVE or event_type == _TOUCH_MOVE_OUT:
            commit_from_touch(args)
        elif event_type == _TOUCH_UP or event_type == _TOUCH_CANCEL or event_type == _TOUCH_SCREEN_EXIT:
            commit_from_touch(args)
            set_dragging(False)
            if callable(onDragEnd):
                onDragEnd(latest_value_ref.current)

    thumb_alpha = 1.0 if (dragging and not disabled) else 0.92
    if disabled:
        thumb_alpha = 0.45

    value_label = None
    if showValue:
        value_label = Label(
            style=Style(width=38, marginLeft=8),
            content=_format_value(current_value),
            color=Colors.white.withAlpha(0.85),
        )

    def touch_button_builder(state):
        return Image(
            style=Style(width='100%', height='100%'),
            color=Colors.transparent,
        )

    slider_children = [
        Panel(
            ref=track_ref,
            style=bar_style,
            children=[
                Image(
                    style=Style(position=Position.absolute, left=0, top=0, right=0, bottom=0),
                    color=trackColor,
                ),
                Image(
                    ref=fill_ref,
                    style=active_fill_style,
                    color=fillColor.withAlpha(0.45) if disabled else fillColor,
                ),
                Image(
                    ref=thumb_ref,
                    style=knob_style,
                    color=thumbColor.withAlpha(thumb_alpha),
                ),
                Button(
                    style=Style(position=Position.absolute, left=0, top=-8, right=0, bottom=-8, zIndex=5),
                    onTouch=handle_touch,
                    buttonBuilder=touch_button_builder,
                    children=[],
                ),
            ],
        ),
    ]
    if value_label is not None:
        slider_children.append(value_label)

    return Panel(
        style=base_style,
        children=slider_children,
    )
