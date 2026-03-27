# pyright: reportConstantRedefinition=false, reportMissingParameterType=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

import types

from .shadow_node import LayoutResult


INTEGER_TYPES = (int,)
long_type = getattr(types, "LongType", None)
if long_type is not None:
    INTEGER_TYPES = (int, long_type)

NUMBER_TYPES = INTEGER_TYPES + (float,)

TEXT_TYPES = (str,)
string_types = getattr(types, "StringTypes", None)
if string_types is not None:
    TEXT_TYPES = string_types


def _safe_float(value, default_value=0.0):
    try:
        return float(value)
    except Exception:
        return float(default_value)


def normalize_style(style):
    if style is None:
        return {}
    if isinstance(style, dict):
        return dict(style)

    if hasattr(style, "to_dict") and callable(getattr(style, "to_dict")):
        try:
            maybe = style.to_dict()
            if isinstance(maybe, dict):
                return dict(maybe)
        except Exception:
            pass

    data = {}
    if hasattr(style, "__dict__"):
        for key, value in style.__dict__.items():
            if key.startswith("_"):
                continue
            if callable(value):
                continue
            data[key] = value
    return data


def parse_length(value, parent_size):
    if value is None:
        return None

    if isinstance(value, NUMBER_TYPES):
        return float(value)

    if isinstance(value, TEXT_TYPES):
        text = value.strip()
        if text.endswith("%"):
            ratio_text = text[:-1].strip()
            try:
                ratio = float(ratio_text) / 100.0
                return ratio * float(parent_size)
            except Exception:
                return None
        try:
            return float(text)
        except Exception:
            return None

    return None


def _is_absolute_position(style):
    if not isinstance(style, dict):
        return False
    pos_value = style.get("position")
    if pos_value is None:
        return False
    if isinstance(pos_value, TEXT_TYPES):
        return pos_value.strip().lower() == "absolute"
    return False


def parse_box(style, prefix, parent_width, parent_height):
    base = parse_length(style.get(prefix), parent_width)
    if base is None:
        base = 0.0

    top = parse_length(style.get(prefix + "Top"), parent_height)
    right = parse_length(style.get(prefix + "Right"), parent_width)
    bottom = parse_length(style.get(prefix + "Bottom"), parent_height)
    left = parse_length(style.get(prefix + "Left"), parent_width)

    if top is None:
        top = base
    if right is None:
        right = base
    if bottom is None:
        bottom = base
    if left is None:
        left = base

    return float(top), float(right), float(bottom), float(left)


def _parse_size_pair(value, parent_width, parent_height):
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return (
            parse_length(value[0], parent_width),
            parse_length(value[1], parent_height),
        )
    return (None, None)


def _resolve_min_max(style, parent_width, parent_height):
    min_w = parse_length(style.get("minWidth"), parent_width)
    max_w = parse_length(style.get("maxWidth"), parent_width)
    min_h = parse_length(style.get("minHeight"), parent_height)
    max_h = parse_length(style.get("maxHeight"), parent_height)

    pair_min_w, pair_min_h = _parse_size_pair(style.get("minSize"), parent_width, parent_height)
    pair_max_w, pair_max_h = _parse_size_pair(style.get("maxSize"), parent_width, parent_height)

    if min_w is None:
        min_w = pair_min_w
    if min_h is None:
        min_h = pair_min_h
    if max_w is None:
        max_w = pair_max_w
    if max_h is None:
        max_h = pair_max_h

    min_w = None if min_w is None else max(0.0, _safe_float(min_w, 0.0))
    min_h = None if min_h is None else max(0.0, _safe_float(min_h, 0.0))
    max_w = None if max_w is None else max(0.0, _safe_float(max_w, 0.0))
    max_h = None if max_h is None else max(0.0, _safe_float(max_h, 0.0))

    if min_w is not None and max_w is not None and min_w > max_w:
        max_w = min_w
    if min_h is not None and max_h is not None and min_h > max_h:
        max_h = min_h

    return (min_w, max_w, min_h, max_h)


def _clamp_axis(value, min_value, max_value):
    clamped = max(0.0, _safe_float(value, 0.0))
    if min_value is not None and clamped < min_value:
        clamped = min_value
    if max_value is not None and clamped > max_value:
        clamped = max_value
    return clamped


def _measure_label_size(node, style, text_measurer, max_width=None):
    if text_measurer is not None:
        content = ""
        measure_style = {}
        if hasattr(node, "props") and isinstance(node.props, dict):
            content = node.props.get("content", "")
            for key in ("fontSize", "font", "textAlign", "linePadding", "shadow"):
                if node.props.get(key) is not None:
                    measure_style[key] = node.props.get(key)
        measured = text_measurer.measure_text(content, measure_style, max_width=max_width)
        return (
            max(0.0, _safe_float(measured.get("width", 100.0), 100.0)),
            max(0.0, _safe_float(measured.get("height", 20.0), 20.0)),
        )
    return 100.0, 20.0


def _resolve_own_size(node, style, available_width, available_height, forced_width, forced_height, text_measurer=None, measure_pass=False):
    width = forced_width
    height = forced_height

    explicit_width = parse_length(style.get("width"), available_width)
    explicit_height = parse_length(style.get("height"), available_height)

    if width is None:
        width = explicit_width
    if height is None:
        height = explicit_height

    if (
        (not measure_pass)
        and node.node_type != "Label"
        and bool(node.children)
        and explicit_width is None
        and explicit_height is None
    ):
        if hasattr(node, "_measured_shrunk") and node._measured_shrunk and node.layout is not None:
            if width is None:
                width = node.layout.width
            if height is None:
                height = node.layout.height

    min_width, max_width, min_height, max_height = _resolve_min_max(style, available_width, available_height)

    if node.node_type == "Label" and (width is None or height is None):
        if text_measurer is not None:
            content = node.props.get("content", "")
            measure_style = {}
            if isinstance(node.props, dict):
                for key in ("fontSize", "font", "textAlign", "linePadding", "shadow"):
                    if node.props.get(key) is not None:
                        measure_style[key] = node.props.get(key)
            measure_limit = width
            if measure_limit is None:
                measure_limit = max_width
            measured = text_measurer.measure_text(content, measure_style, max_width=measure_limit)
            if width is None:
                width = measured.get("width", 100.0)
            if height is None:
                height = measured.get("height", 20.0)
        else:
            if width is None:
                width = 100.0
            if height is None:
                height = 20.0

    if width is None:
        width = float(available_width)
    if height is None:
        height = float(available_height)

    width = _clamp_axis(width, min_width, max_width)
    height = _clamp_axis(height, min_height, max_height)
    return width, height


def compute_layout(node, x, y, available_width, available_height, forced_width=None, forced_height=None, text_measurer=None, measure_pass=False):
    style = normalize_style(node.style)
    display_value = style.get("display")
    if isinstance(display_value, TEXT_TYPES) and display_value.strip().lower() == "none":
        node.layout = LayoutResult(
            x=x,
            y=y,
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
        )
        return node

    margin_top, margin_right, margin_bottom, margin_left = parse_box(
        style, "margin", available_width, available_height
    )
    padding_top, padding_right, padding_bottom, padding_left = parse_box(
        style, "padding", available_width, available_height
    )

    width, height = _resolve_own_size(
        node,
        style,
        available_width,
        available_height,
        forced_width,
        forced_height,
        text_measurer,
        measure_pass,
    )

    node.layout = LayoutResult(
        x=x,
        y=y,
        width=width,
        height=height,
        padding_top=padding_top,
        padding_right=padding_right,
        padding_bottom=padding_bottom,
        padding_left=padding_left,
        margin_top=margin_top,
        margin_right=margin_right,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
    )

    if not node.children:
        return node

    flex_direction = style.get("flexDirection", "column")
    if flex_direction in ("rowReverse", "columnReverse"):
        if flex_direction == "rowReverse":
            flex_direction = "row"
        else:
            flex_direction = "column"
    if flex_direction not in ("row", "column"):
        flex_direction = "column"

    justify_content = style.get("justifyContent", "start")
    if justify_content not in (
        "start",
        "center",
        "end",
        "spaceBetween",
        "spaceAround",
    ):
        justify_content = "start"

    align_items = style.get("alignItems", "stretch")
    if align_items not in ("start", "center", "end", "stretch"):
        align_items = "stretch"

    flex_wrap = style.get("flexWrap", "nowrap")
    if flex_wrap not in ("nowrap", "wrap"):
        flex_wrap = "nowrap"

    content_x = x + padding_left
    content_y = y + padding_top
    content_width = max(0.0, width - padding_left - padding_right)
    content_height = max(0.0, height - padding_top - padding_bottom)

    if flex_direction == "row":
        main_size = content_width
        cross_size = content_height
    else:
        main_size = content_height
        cross_size = content_width

    # Handle Scroll: children can expand in the scroll direction.
    if node.node_type == "Scroll":
        # We assume vertical scroll for now if direction is column.
        # This allows children to take as much main-axis space as they need.
        main_size = 1000000.0

    items = []
    flow_items = []
    absolute_items = []
    for child in node.children:
        child_style = normalize_style(child.style)
        c_min_w, c_max_w, c_min_h, c_max_h = _resolve_min_max(child_style, content_width, content_height)

        c_margin_top, c_margin_right, c_margin_bottom, c_margin_left = parse_box(
            child_style, "margin", content_width, content_height
        )

        c_width = parse_length(child_style.get("width"), content_width)
        c_height = parse_length(child_style.get("height"), content_height)

        if child.node_type == "Label":
            label_max_width = c_width
            if label_max_width is None:
                label_max_width = c_max_w
            elif c_max_w is not None and label_max_width > c_max_w:
                label_max_width = c_max_w

            label_width, label_height = _measure_label_size(
                child,
                child_style,
                text_measurer,
                max_width=label_max_width,
            )
            if c_width is None:
                c_width = label_width
            if c_height is None:
                c_height = label_height

        if c_width is not None:
            c_width = _clamp_axis(c_width, c_min_w, c_max_w)
        if c_height is not None:
            c_height = _clamp_axis(c_height, c_min_h, c_max_h)

        if flex_direction == "row":
            explicit_main = c_width
            explicit_cross = c_height
            min_main = c_min_w
            max_main = c_max_w
            min_cross = c_min_h
            max_cross = c_max_h
            margin_main_lead = c_margin_left
            margin_main_trail = c_margin_right
            margin_cross_lead = c_margin_top
            margin_cross_trail = c_margin_bottom
        else:
            explicit_main = c_height
            explicit_cross = c_width
            min_main = c_min_h
            max_main = c_max_h
            min_cross = c_min_w
            max_cross = c_max_w
            margin_main_lead = c_margin_top
            margin_main_trail = c_margin_bottom
            margin_cross_lead = c_margin_left
            margin_cross_trail = c_margin_right

        measured_layout = child.layout
        measured_main = None
        measured_cross = None
        if measured_layout is not None:
            if flex_direction == "row":
                measured_main = _safe_float(getattr(measured_layout, "width", 0.0), 0.0)
                measured_cross = _safe_float(getattr(measured_layout, "height", 0.0), 0.0)
            else:
                measured_main = _safe_float(getattr(measured_layout, "height", 0.0), 0.0)
                measured_cross = _safe_float(getattr(measured_layout, "width", 0.0), 0.0)

        flex_value = child_style.get("flex", 0)
        if isinstance(flex_value, NUMBER_TYPES):
            flex_value = float(flex_value)
        elif isinstance(flex_value, TEXT_TYPES):
            try:
                flex_value = float(flex_value.strip())
            except Exception:
                flex_value = 0.0
        else:
            flex_value = 0.0
        if flex_value < 0:
            flex_value = 0.0

        align_self = child_style.get("alignSelf", "auto")
        if align_self not in ("auto", "start", "center", "end", "stretch"):
            align_self = "auto"

        base_main = explicit_main
        if base_main is None and flex_value <= 0:
            if (not measure_pass) and measured_main is not None:
                base_main = measured_main
            elif measure_pass and child.children:
                base_main = main_size
            else:
                base_main = 0.0

        item = {
            "child": child,
            "style": child_style,
            "margin_top": c_margin_top,
            "margin_right": c_margin_right,
            "margin_bottom": c_margin_bottom,
            "margin_left": c_margin_left,
            "explicit_width": c_width,
            "explicit_height": c_height,
            "explicit_main": explicit_main,
            "explicit_cross": explicit_cross,
            "min_main": min_main,
            "max_main": max_main,
            "min_cross": min_cross,
            "max_cross": max_cross,
            "measured_cross": measured_cross,
            "margin_main_lead": margin_main_lead,
            "margin_main_trail": margin_main_trail,
            "margin_cross_lead": margin_cross_lead,
            "margin_cross_trail": margin_cross_trail,
            "flex": flex_value,
            "align_self": align_self,
            "base_main": max(0.0, _safe_float(base_main, 0.0)),
            "final_main": 0.0,
            "final_cross": 0.0,
            "line_cross_size": 0.0,
            "main_pos": 0.0,
            "cross_pos": 0.0,
            "cross_specified": explicit_cross is not None,
            "is_absolute": _is_absolute_position(child_style),
            "min_width": c_min_w,
            "max_width": c_max_w,
            "min_height": c_min_h,
            "max_height": c_max_h,
        }
        items.append(item)
        if item["is_absolute"]:
            absolute_items.append(item)
        else:
            flow_items.append(item)

    lines = []
    if flex_wrap == "nowrap":
        lines.append(flow_items)
    else:
        current = []
        current_used = 0.0
        for item in flow_items:
            outer_main = (
                item["base_main"] + item["margin_main_lead"] + item["margin_main_trail"]
            )
            if not current:
                current.append(item)
                current_used = outer_main
            else:
                if current_used + outer_main > main_size and main_size > 0:
                    lines.append(current)
                    current = [item]
                    current_used = outer_main
                else:
                    current.append(item)
                    current_used += outer_main
        if current:
            lines.append(current)

    line_infos = []
    for line in lines:
        fixed_total = 0.0
        total_flex = 0.0

        for item in line:
            margins = item["margin_main_lead"] + item["margin_main_trail"]
            if item["flex"] > 0:
                fixed_total += margins
                total_flex += item["flex"]
            else:
                fixed_total += item["base_main"] + margins

        remaining = main_size - fixed_total
        if remaining < 0:
            remaining = 0.0

        used_main = 0.0
        max_cross_outer = 0.0

        for item in line:
            item_main = item["base_main"]
            if item["flex"] > 0 and total_flex > 0:
                item_main = remaining * (float(item["flex"]) / float(total_flex))
            item_main = _clamp_axis(item_main, item["min_main"], item["max_main"])
            item["final_main"] = item_main

            outer_main = item_main + item["margin_main_lead"] + item["margin_main_trail"]
            used_main += outer_main

            if item["explicit_cross"] is not None:
                cross = _clamp_axis(item["explicit_cross"], item["min_cross"], item["max_cross"])
            elif (not measure_pass) and item["measured_cross"] is not None:
                cross = _clamp_axis(item["measured_cross"], item["min_cross"], item["max_cross"])
            elif measure_pass and item["child"].children:
                cross = _clamp_axis(cross_size, item["min_cross"], item["max_cross"])
            else:
                cross = _clamp_axis(0.0, item["min_cross"], item["max_cross"])

            item["final_cross"] = cross
            outer_cross = cross + item["margin_cross_lead"] + item["margin_cross_trail"]
            if outer_cross > max_cross_outer:
                max_cross_outer = outer_cross

        if flex_wrap == "nowrap":
            line_cross_size = cross_size
        else:
            line_cross_size = max_cross_outer

        line_infos.append({
            "items": line,
            "used_main": used_main,
            "line_cross_size": max(0.0, line_cross_size),
        })

    total_lines_cross = 0.0
    for info in line_infos:
        total_lines_cross += info["line_cross_size"]

    line_cross_cursor = 0.0
    if flex_wrap == "wrap" and total_lines_cross < cross_size:
        line_cross_cursor = 0.0

    for info in line_infos:
        line = info["items"]
        used_main = info["used_main"]
        line_cross_size = info["line_cross_size"]

        free_main = main_size - used_main
        if free_main < 0:
            free_main = 0.0

        count = len(line)
        offset = 0.0
        gap = 0.0
        
        if not measure_pass:
            if justify_content == "start":
                offset = 0.0
                gap = 0.0
            elif justify_content == "center":
                offset = free_main / 2.0
                gap = 0.0
            elif justify_content == "end":
                offset = free_main
                gap = 0.0
            elif justify_content == "spaceBetween":
                if count > 1:
                    gap = free_main / float(count - 1)
                else:
                    gap = 0.0
                offset = 0.0
            elif justify_content == "spaceAround":
                if count > 0:
                    gap = free_main / float(count)
                    offset = gap / 2.0
                else:
                    gap = 0.0
                    offset = 0.0

        main_cursor = offset
        for item in line:
            main_cursor += item["margin_main_lead"]
            item["main_pos"] = main_cursor

            effective_align = item["align_self"]
            if effective_align == "auto":
                effective_align = align_items

            cross = item["final_cross"]
            if effective_align == "stretch" and not item["cross_specified"]:
                cross = line_cross_size - item["margin_cross_lead"] - item["margin_cross_trail"]
                cross = _clamp_axis(cross, item["min_cross"], item["max_cross"])
                item["final_cross"] = cross

            outer_cross = cross + item["margin_cross_lead"] + item["margin_cross_trail"]

            if not measure_pass:
                if effective_align == "start" or effective_align == "stretch":
                    cross_pos = line_cross_cursor + item["margin_cross_lead"]
                elif effective_align == "center":
                    cross_pos = (
                        line_cross_cursor
                        + (line_cross_size - outer_cross) / 2.0
                        + item["margin_cross_lead"]
                    )
                else:
                    cross_pos = (
                        line_cross_cursor
                        + (line_cross_size - outer_cross)
                        + item["margin_cross_lead"]
                    )
            else:
                cross_pos = line_cross_cursor + item["margin_cross_lead"]
                
            item["cross_pos"] = cross_pos

            main_cursor += item["final_main"] + item["margin_main_trail"] + gap

        line_cross_cursor += line_cross_size

    for item in flow_items:
        if flex_direction == "row":
            child_x = content_x + item["main_pos"]
            child_y = content_y + item["cross_pos"]
            child_width = item["final_main"]
            child_height = item["final_cross"]
        else:
            child_x = content_x + item["cross_pos"]
            child_y = content_y + item["main_pos"]
            child_width = item["final_cross"]
            child_height = item["final_main"]

        child_width = max(0.0, child_width)
        child_height = max(0.0, child_height)

        compute_layout(
            item["child"],
            child_x,
            child_y,
            child_width,
            child_height,
            forced_width=child_width,
            forced_height=child_height,
            text_measurer=text_measurer,
            measure_pass=measure_pass,
        )

    for item in absolute_items:
        child_style = item["style"]

        left = parse_length(child_style.get("left"), content_width)
        right = parse_length(child_style.get("right"), content_width)
        top = parse_length(child_style.get("top"), content_height)
        bottom = parse_length(child_style.get("bottom"), content_height)

        child_width = item["explicit_width"]
        child_height = item["explicit_height"]

        if child_width is None and left is not None and right is not None:
            child_width = content_width - left - right - item["margin_left"] - item["margin_right"]
        if child_height is None and top is not None and bottom is not None:
            child_height = content_height - top - bottom - item["margin_top"] - item["margin_bottom"]

        if child_width is not None:
            child_width = _clamp_axis(child_width, item["min_width"], item["max_width"])
        if child_height is not None:
            child_height = _clamp_axis(child_height, item["min_height"], item["max_height"])

        if child_width is None:
            available_w = content_width
        else:
            available_w = child_width

        if child_height is None:
            available_h = content_height
        else:
            available_h = child_height

        child_x = content_x + item["margin_left"]
        child_y = content_y + item["margin_top"]
        if left is not None:
            child_x = content_x + left + item["margin_left"]
        elif right is not None and child_width is not None:
            child_x = content_x + content_width - right - child_width - item["margin_right"]

        if top is not None:
            child_y = content_y + top + item["margin_top"]
        elif bottom is not None and child_height is not None:
            child_y = content_y + content_height - bottom - child_height - item["margin_bottom"]

        compute_layout(
            item["child"],
            child_x,
            child_y,
            max(0.0, available_w),
            max(0.0, available_h),
            forced_width=child_width,
            forced_height=child_height,
            text_measurer=text_measurer,
            measure_pass=measure_pass,
        )

    explicit_width = parse_length(style.get("width"), available_width)
    explicit_height = parse_length(style.get("height"), available_height)

    # Calculate content bounding box for all nodes with children.
    if node.children:
        min_x = None
        min_y = None
        max_x = None
        max_y = None

        for child in node.children:
            if child.layout:
                child_left = child.layout.x
                child_top = child.layout.y
                child_right = child_left + child.layout.width
                child_bottom = child_top + child.layout.height

                if min_x is None or child_left < min_x:
                    min_x = child_left
                if min_y is None or child_top < min_y:
                    min_y = child_top
                if max_x is None or child_right > max_x:
                    max_x = child_right
                if max_y is None or child_bottom > max_y:
                    max_y = child_bottom

        if min_x is not None and max_x is not None:
            intrinsic_width = (max_x - x) + padding_right
            intrinsic_height = (max_y - y) + padding_bottom

            node.layout.content_width = max(0.0, intrinsic_width)
            node.layout.content_height = max(0.0, intrinsic_height)

            # If node has no explicit size, it shrinks to fit children (except for Label which handles itself).
            if node.node_type != "Label" and explicit_width is None and explicit_height is None:
                node.layout.width = max(0.0, intrinsic_width)
                node.layout.height = max(0.0, intrinsic_height)
                node._measured_shrunk = True

    return node
