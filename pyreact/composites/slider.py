# -*- coding: utf-8 -*-

from pyreact.components.component import Component
from pyreact.components.enums import AlignItems, ButtonState, FlexDirection, JustifyContent, Position
from pyreact.components.node_base import ComponentNode
from pyreact.components.primitives import Button, Image, Panel, clone_component
from pyreact.components.style import Style
from pyreact.core.hooks import useRef, useState


_TOUCH_UP = 0
_TOUCH_DOWN = 1
_TOUCH_CANCEL = 3
_TOUCH_MOVE = 4
_TOUCH_MOVE_OUT = 6
_TOUCH_SCREEN_EXIT = 7
_SLIDER_LOCKED = 'locked'

_THUMB_TEXTURES = {
    ButtonState.default: 'textures/ui/slider_button_default',
    ButtonState.hover: 'textures/ui/slider_button_hover',
    ButtonState.pressed: 'textures/ui/slider_button_indent',
    _SLIDER_LOCKED: 'textures/ui/slider_button_locked',
}

_BACKGROUND_TEXTURES = {
    ButtonState.default: 'textures/ui/slider_background',
    ButtonState.hover: 'textures/ui/slider_background_hover',
    ButtonState.pressed: 'textures/ui/slider_background_hover',
    _SLIDER_LOCKED: 'textures/ui/slider_locked_transparent_fade',
}

_PROGRESS_TEXTURES = {
    ButtonState.default: 'textures/ui/slider_progress',
    ButtonState.hover: 'textures/ui/slider_progress_hover',
    ButtonState.pressed: 'textures/ui/slider_progress_hover',
    _SLIDER_LOCKED: 'textures/ui/slider_locked_transparent_fade',
}

_STEP_BACKGROUND_TEXTURES = {
    ButtonState.default: 'textures/ui/slider_step_background',
    ButtonState.hover: 'textures/ui/slider_step_background_hover',
    ButtonState.pressed: 'textures/ui/slider_step_background_hover',
    _SLIDER_LOCKED: 'textures/ui/slider_locked_transparent_fade',
}

_STEP_PROGRESS_TEXTURES = {
    ButtonState.default: 'textures/ui/slider_step_progress',
    ButtonState.hover: 'textures/ui/slider_step_progress_hover',
    ButtonState.pressed: 'textures/ui/slider_step_progress_hover',
    _SLIDER_LOCKED: 'textures/ui/slider_locked_transparent_fade',
}


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


def _slider_button_state(disabled, dragging):
    if disabled:
        return _SLIDER_LOCKED
    if dragging:
        return ButtonState.pressed
    return ButtonState.default


def _slider_state_dict(value, percent, low, high, step, disabled, dragging, stepped):
    button_state = _slider_button_state(disabled, dragging)
    ratio = percent / 100.0
    return {
        'value': value,
        'ratio': ratio,
        'percent': percent,
        'min': low,
        'max': high,
        'step': step,
        'disabled': bool(disabled),
        'dragging': bool(dragging),
        'pressed': bool(dragging),
        'locked': bool(disabled),
        'hover': False,
        'stepped': bool(stepped),
        'buttonState': button_state,
        'button_state': button_state,
        'state': button_state,
    }


def _image_builder_call(builder, state):
    if not callable(builder):
        return None
    try:
        return builder(state)
    except TypeError:
        return builder()


def _assert_image_node(node, prop_name):
    if not isinstance(node, ComponentNode) or node.node_type != 'Image':
        raise TypeError('Slider %s must return Image' % prop_name)
    return node


def _merge_required_style(node, required_style, ref=None):
    props = getattr(node, 'props', None) or {}
    user_style = props.get('style')
    merged = Style.merged(required_style, user_style)

    # Position and edge constraints are structural for Slider; user images still
    # control texture props and may override dimensions when the slot supports it.
    for key in ('position', 'left', 'top', 'right', 'bottom', 'zIndex'):
        if isinstance(required_style, Style) and key in required_style:
            setattr(merged, key, required_style.get(key))

    overrides = {'style': merged.to_dict()}
    if ref is not None:
        overrides['ref'] = ref
    return clone_component(node, **overrides)


def _state_key(state):
    if isinstance(state, dict):
        return state.get('buttonState') or state.get('state') or ButtonState.default
    return state


def _default_track_image(state):
    texture_map = _STEP_BACKGROUND_TEXTURES if state.get('stepped') else _BACKGROUND_TEXTURES
    key = _state_key(state)
    return Image(src=texture_map.get(key) or texture_map.get(ButtonState.default))


def _default_progress_image(state):
    texture_map = _STEP_PROGRESS_TEXTURES if state.get('stepped') else _PROGRESS_TEXTURES
    key = _state_key(state)
    return Image(src=texture_map.get(key) or texture_map.get(ButtonState.default))


def _default_thumb_image(state):
    key = _state_key(state)
    return Image(src=_THUMB_TEXTURES.get(key) or _THUMB_TEXTURES.get(ButtonState.default))


def _default_border_image(state):
    return Image(src='textures/ui/slider_border')


def _build_image_slot(builder, default_node, state, required_style, prop_name, ref=None):
    image_node = _image_builder_call(builder, state)
    if image_node is None:
        image_node = default_node
    image_node = _assert_image_node(image_node, prop_name)
    return _merge_required_style(image_node, required_style, ref)


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
    progressStyle=None,
    fillStyle=None,
    thumbStyle=None,
    borderStyle=None,
    trackBuilder=None,
    backgroundBuilder=None,
    progressBuilder=None,
    buttonBuilder=None,
    thumbBuilder=None,
    borderBuilder=None,
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

    if progressStyle is None:
        progressStyle = fillStyle

    stepped = step is not None
    state = _slider_state_dict(current_value, percent, low, high, step, disabled, dragging, stepped)
    if trackBuilder is None:
        trackBuilder = backgroundBuilder
    if thumbBuilder is None:
        thumbBuilder = buttonBuilder

    base_style = Style.merged(
        Style(width=180, height=28, flexDirection=FlexDirection.row, alignItems=AlignItems.center, justifyContent=JustifyContent.center),
        style,
    )
    bar_style = Style.merged(
        Style(width='100%', height=6, justifyContent=JustifyContent.center),
        trackStyle,
    )
    progress_slot_style = Style.merged(
        Style(width='%.3f%%' % percent, height='100%', position=Position.absolute, left=0, top=0),
        progressStyle,
    )
    thumb_slot_style = Style.merged(
        Style(width=14, height=14, position=Position.absolute, left='%.3f%%' % percent, top=-4, marginLeft=-7, alignItems=AlignItems.center, justifyContent=JustifyContent.center, zIndex=3),
        thumbStyle,
    )
    border_slot_style = Style.merged(
        Style(position=Position.absolute, left=0, right=0, top=0, bottom=0, zIndex=2),
        borderStyle,
    )

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
        if disabled:
            return
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

    def touch_button_builder(state):
        return Image(
            style=Style(width='100%', height='100%', opacity=0),
            src='textures/ui/white_bg',
        )

    track_image = _build_image_slot(
        trackBuilder,
        _default_track_image(state),
        state,
        Style(position=Position.absolute, left=0, right=0, top=0, bottom=0),
        'trackBuilder',
    )
    progress_image = _build_image_slot(
        progressBuilder,
        _default_progress_image(state),
        state,
        progress_slot_style,
        'progressBuilder',
        fill_ref,
    )
    border_image = _build_image_slot(
        borderBuilder,
        _default_border_image(state),
        state,
        border_slot_style,
        'borderBuilder',
    )
    thumb_image = _build_image_slot(
        thumbBuilder,
        _default_thumb_image(state),
        state,
        thumb_slot_style,
        'thumbBuilder',
        thumb_ref,
    )

    slider_children = [
        Panel(
            ref=track_ref,
            style=bar_style,
            children=[
                track_image,
                progress_image,
                border_image,
                thumb_image,
                Button(
                    style=Style(position=Position.absolute, left=0, top=-8, right=0, bottom=-8, zIndex=5),
                    onTouch=handle_touch,
                    buttonBuilder=touch_button_builder,
                    children=[],
                ),
            ],
        ),
    ]

    return Panel(
        style=base_style,
        children=slider_children,
    )
