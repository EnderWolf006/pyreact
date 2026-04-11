# -*- coding: utf-8 -*-

import time

from pyreact.components.color import Color


def _perf_now():
    perf_counter = getattr(time, 'perf_counter', None)
    if callable(perf_counter):
        return perf_counter()
    clock = getattr(time, 'clock', None)
    if callable(clock):
        return clock()
    return time.time()


try:
    _UNICODE_TYPE = unicode
except NameError:
    # Python3 fallback for local tooling; runtime is Python2 in-game.
    _UNICODE_TYPE = str


class RuntimeNativeApiMixin(object):
    _TEXT_FONT_SIZE_BASE = 10.0

    def _get_native_layout_cache(self):
        cache = getattr(self, '_native_layout_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._native_layout_cache = cache
        return cache

    def _get_native_layout_cache_entry(self, path):
        safe_path = self._safe_text(path)
        if not safe_path:
            return None, None
        cache = self._get_native_layout_cache()
        entry = cache.get(safe_path)
        if not isinstance(entry, dict):
            entry = {}
            cache[safe_path] = entry
        return safe_path, entry

    def _drop_native_layout_cache(self, path_prefix=None):
        cache = self._get_native_layout_cache()
        if not path_prefix:
            cache.clear()
            return

        prefix = self._safe_text(path_prefix)
        if not prefix:
            cache.clear()
            return

        prefix_with_sep = prefix + '/'
        for cached_path in list(cache.keys()):
            safe_cached_path = self._safe_text(cached_path)
            if safe_cached_path == prefix or safe_cached_path.startswith(prefix_with_sep):
                try:
                    del cache[cached_path]
                except Exception:
                    pass

    def _get_cached_native_prop(self, path, prop_name):
        safe_path, entry = self._get_native_layout_cache_entry(path)
        if entry is None:
            return None
        return entry.get(prop_name)

    def _set_cached_native_prop(self, path, prop_name, value):
        safe_path, entry = self._get_native_layout_cache_entry(path)
        if entry is None:
            return
        entry[prop_name] = value

    def _reset_native_api_call_counts(self):
        self._native_api_call_counts = {}

    def _normalize_native_api_call_stats(self, stats):
        if isinstance(stats, dict):
            try:
                count_value = int(stats.get('count', 0))
            except Exception:
                count_value = 0
            total_ms = self._to_float(stats.get('total_ms', 0.0), 0.0)
            if total_ms < 0.0:
                total_ms = 0.0
            return {
                'count': count_value,
                'total_ms': total_ms,
            }

        try:
            count_value = int(stats)
        except Exception:
            count_value = 0
        return {
            'count': count_value,
            'total_ms': 0.0,
        }

    def _count_native_api_call(self, api_name, count=1, elapsed_ms=None):
        if not getattr(self, '_native_api_counting_active', False):
            return
        safe_name = self._safe_text(api_name)
        if not safe_name:
            return
        counts = getattr(self, '_native_api_call_counts', None)
        if not isinstance(counts, dict):
            counts = {}
            self._native_api_call_counts = counts
        try:
            inc = int(count)
        except Exception:
            inc = 1
        if inc <= 0:
            return
        elapsed_value = self._to_float(elapsed_ms, 0.0) if elapsed_ms is not None else 0.0
        if elapsed_value < 0.0:
            elapsed_value = 0.0
        entry = self._normalize_native_api_call_stats(counts.get(safe_name, {}))
        entry['count'] += inc
        entry['total_ms'] += elapsed_value
        counts[safe_name] = entry

    def _begin_native_api_call_batch(self):
        self._reset_native_api_call_counts()
        self._native_api_counting_active = bool(getattr(self, '_log_perf', False))

    def _finish_native_api_call_batch(self):
        counts = getattr(self, '_native_api_call_counts', None)
        if isinstance(counts, dict):
            normalized = {}
            for api_name, stats in counts.items():
                normalized[self._safe_text(api_name)] = self._normalize_native_api_call_stats(stats)
            counts = normalized
        else:
            counts = {}
        self._native_api_counting_active = False
        self._reset_native_api_call_counts()
        return counts

    def _merge_native_api_call_counts(self, target_counts, source_counts):
        if not isinstance(target_counts, dict) or not isinstance(source_counts, dict):
            return target_counts
        for api_name, api_stats in source_counts.items():
            safe_name = self._safe_text(api_name)
            if not safe_name:
                continue
            source_entry = self._normalize_native_api_call_stats(api_stats)
            if source_entry.get('count', 0) <= 0:
                continue
            target_entry = self._normalize_native_api_call_stats(target_counts.get(safe_name, {}))
            target_entry['count'] += source_entry.get('count', 0)
            target_entry['total_ms'] += source_entry.get('total_ms', 0.0)
            target_counts[safe_name] = target_entry
        return target_counts

    def _log_native_api_call_counts(self, title, counts):
        if not getattr(self, '_log_perf', False):
            return
        if not isinstance(counts, dict) or not counts:
            return
        try:
            print('=====> PyreactRuntime[perf] %s: <=====' % self._safe_text(title))
            items = []
            for api_name, api_stats in counts.items():
                entry = self._normalize_native_api_call_stats(api_stats)
                if entry.get('count', 0) <= 0:
                    continue
                items.append((self._safe_text(api_name), entry))
            items = sorted(items, key=lambda item: (-item[1].get('count', 0), -item[1].get('total_ms', 0.0), item[0]))
            for api_name, api_stats in items:
                print('=====> PyreactRuntime[perf]    %s: %s次, %.3fms <=====' % (
                    api_name,
                    int(api_stats.get('count', 0)),
                    self._to_float(api_stats.get('total_ms', 0.0), 0.0),
                ))
        except Exception:
            pass

    def _to_grid_control(self, control, path):
        if control and hasattr(control, 'asGrid'):
            try:
                grid_control = control.asGrid()
                if grid_control:
                    return grid_control
            except Exception:
                pass

        try:
            base_control = self._screen.GetBaseUIControl(path)
            if base_control and hasattr(base_control, 'asGrid'):
                return base_control.asGrid()
        except Exception:
            pass
        return None

    def _safe_set_grid_dimension(self, path, col_count, row_count=1, control=None):
        grid_control = self._to_grid_control(control, path)
        if not grid_control or not hasattr(grid_control, 'SetGridDimension'):
            return False

        try:
            cols = int(col_count)
        except Exception:
            cols = 1
        try:
            rows = int(row_count)
        except Exception:
            rows = 0

        if cols <= 0:
            cols = 1
        if rows < 0:
            rows = 0

        try:
            start_time = _perf_now()
            grid_control.SetGridDimension((rows, cols))
            self._count_native_api_call('SetGridDimension', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            return True
        except Exception:
            return False

    def _ensure_measure_label(self):
        measure_path = self._root_path + "/" + self._MEASURE_LABEL_NAME
        self._measure_label_path = measure_path

        control = None
        try:
            control = self._screen.GetBaseUIControl(measure_path)
        except Exception:
            control = None

        if not control:
            try:
                root_control = self._screen.GetBaseUIControl(self._root_path)
            except Exception:
                root_control = None
            if not root_control:
                return None

            def_name = "%s.%s" % (self._base_namespace, "textBase")
            try:
                control = self._screen.CreateChildControl(def_name, self._MEASURE_LABEL_NAME, root_control)
            except Exception:
                control = None
            if not control:
                return None

        self._safe_set_position(measure_path, -100000.0, -100000.0, control)
        try:
            if hasattr(control, "SetVisible"):
                start_time = _perf_now()
                control.SetVisible(True)
                self._count_native_api_call('SetVisible', elapsed_ms=(_perf_now() - start_time) * 1000.0)
        except Exception:
            pass
        try:
            if hasattr(control, "SetAlpha"):
                start_time = _perf_now()
                control.SetAlpha(0.0)
                self._count_native_api_call('SetAlpha', elapsed_ms=(_perf_now() - start_time) * 1000.0)
        except Exception:
            pass
        return control

    def _measure_text_native(self, content, style, max_width=None):
        control = self._ensure_measure_label()
        if not control:
            return None

        label_path = self._measure_label_path
        if not label_path:
            return None

        label_control = self._to_label_control(control, label_path)
        if not label_control:
            return None

        self._safe_set_text_line_padding(label_path, 0.0, label_control)
        self._safe_set_text_font_size(label_path, 1.0, label_control)
        self._safe_set_text_alignment(label_path, "left", label_control)
        self._safe_set_text_shadow(label_path, False, label_control)

        limit_width = self._to_float(max_width, 0.0)

        self._apply_label_native_props_then_text(
            path=label_path,
            label_props=style,
            text=content,
            control=label_control,
        )

        width = 0.0
        height = 0.0
        try:
            size = label_control.GetSize()
        except Exception:
            size = None

        if (not size) or len(size) < 2:
            try:
                size = self._screen.GetSize(label_path)
            except Exception:
                size = None

        if size and len(size) >= 2:
            width = self._to_float(size[0], 0.0)
            height = self._to_float(size[1], 0.0)

        if width >= 4000.0 or height >= 4000.0:
            width = 0.0
            height = 0.0

        font_scale = self._parse_text_font_scale(style.get("fontSize") if isinstance(style, dict) else None)
        if font_scale is None or font_scale <= 0.0:
            font_scale = 1.0
        if width > 0.0 and (width / font_scale) < 4.0:
            width = 4.0 * font_scale

        try:
            label_control.SetText("", True)
        except Exception:
            self._safe_set_text(label_path, "", label_control)
        self._safe_set_position(label_path, -100000.0, -100000.0, label_control)

        if width <= 0.0 or height <= 0.0:
            return None

        if limit_width > 0.0 and width > limit_width:
            width = limit_width

        return {
            "width": width,
            "height": height,
        }

    def _safe_set_text(self, path, text, control=None):
        text_value = self._safe_text(text)
        if self._get_cached_native_prop(path, 'text') == text_value:
            return
        try:
            if control and hasattr(control, "SetText"):
                try:
                    start_time = _perf_now()
                    control.SetText(text_value+"1", True)
                    control.SetText(text_value, True)
                    self._count_native_api_call('SetText', 2, elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    self._set_cached_native_prop(path, 'text', text_value)
                except TypeError:
                    start_time = _perf_now()
                    control.SetText(text_value+"1")
                    control.SetText(text_value)
                    self._count_native_api_call('SetText', 2, elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    self._set_cached_native_prop(path, 'text', text_value)
                return
            try:
                start_time = _perf_now()
                control.asLabel().SetText(text_value+"1", True)
                control.asLabel().SetText(text_value, True)
                self._count_native_api_call('SetText', 2, elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text', text_value)
            except TypeError:
                start_time = _perf_now()
                control.asLabel().SetText(text_value+"1")
                control.asLabel().SetText(text_value)
                self._count_native_api_call('SetText', 2, elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text', text_value)
        except Exception:
            pass

    def _to_text_edit_box_control(self, control, path):
        if not control:
            try:
                control = self._screen.GetBaseUIControl(path)
            except Exception:
                control = None

        if control and hasattr(control, 'asTextEditBox'):
            try:
                te = control.asTextEditBox()
                if te:
                    return te
            except Exception:
                pass
        return None

    def _safe_get_edit_text(self, path, control=None):
        te = self._to_text_edit_box_control(control, path)
        if not te:
            return None
        try:
            return te.GetEditText()
        except Exception:
            return None

    def _safe_set_edit_text(self, path, text, control=None):
        te = self._to_text_edit_box_control(control, path)
        if not te:
            return False
        try:
            start_time = _perf_now()
            te.SetEditText(self._safe_text(text))
            self._count_native_api_call('SetEditText', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            return True
        except Exception:
            return False

    def _safe_set_edit_text_max_length(self, path, max_length, control=None):
        te = self._to_text_edit_box_control(control, path)
        if not te:
            return False
        try:
            max_len = int(max_length)
        except Exception:
            return False
        if max_len <= 0:
            return False
        try:
            start_time = _perf_now()
            te.SetEditTextMaxLength(max_len)
            self._count_native_api_call('SetEditTextMaxLength', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            return True
        except Exception:
            return False

    def _apply_label_native_props_then_text(self, path, label_props, text, control=None):
        if not isinstance(label_props, dict):
            label_props = {}

        line_padding = self._parse_line_padding(label_props.get("linePadding"))
        if line_padding is not None:
            self._safe_set_text_line_padding(path, line_padding, control)

        text_font_size = self._parse_text_font_scale(label_props.get("fontSize"))
        if text_font_size is not None:
            self._safe_set_text_font_size(path, text_font_size, control)

        text_align = self._parse_text_alignment(label_props.get("textAlign"))
        if text_align:
            self._safe_set_text_alignment(path, text_align, control)

        if label_props.get("shadow") is not None:
            self._safe_set_text_shadow(path, self._to_bool(label_props.get("shadow")), control)

        text_color = self._parse_text_color(label_props.get("color"))
        if text_color is not None:
            self._safe_set_text_color(path, text_color, control)

        self._safe_set_text(path, self._safe_text(text), control)

    def _reset_pooled_widget_native_state(self, path, node_type, control=None):
        self._safe_set_alpha(path, 1.0, control)

        safe_node_type = self._safe_text(node_type)
        if safe_node_type == 'Label':
            self._safe_set_text_color(path, Color.fromRGB(255, 255, 255), control)
            self._safe_set_text_font_size(path, 1.0, control)
            self._safe_set_text_alignment(path, 'center', control)
            self._safe_set_text_shadow(path, False, control)
            self._safe_set_text_line_padding(path, 0.0, control)
            return

        if safe_node_type == 'Image':
            self._safe_set_sprite_color(path, Color.fromRGB(255, 255, 255), control)
            self._safe_set_sprite_gray(path, False, control)

    def _safe_set_sprite(self, path, sprite, control=None):
        sprite_text = self._safe_text(sprite)
        if not sprite_text:
            return False
        if self._get_cached_native_prop(path, 'sprite') == sprite_text:
            return True

        if control and hasattr(control, "asImage"):
            try:
                image_control = control.asImage()
                if image_control and hasattr(image_control, "SetSprite"):
                    start_time = _perf_now()
                    ret = image_control.SetSprite(sprite_text)
                    self._count_native_api_call('SetSprite', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    if ret is not False:
                        self._set_cached_native_prop(path, 'sprite', sprite_text)
                    return ret is not False
            except Exception:
                pass

        if control and hasattr(control, "SetSprite"):
            try:
                start_time = _perf_now()
                ret = control.SetSprite(sprite_text)
                self._count_native_api_call('SetSprite', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                if ret is not False:
                    self._set_cached_native_prop(path, 'sprite', sprite_text)
                return ret is not False
            except Exception:
                pass

        return False

    def _safe_set_sprite_color(self, path, color, control=None):
        rgb = self._to_rgb_tuple(color)
        if rgb is None:
            return
        if self._get_cached_native_prop(path, 'sprite_color') == rgb:
            return

        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteColor"):
            try:
                start_time = _perf_now()
                image_control.SetSpriteColor(rgb)
                self._count_native_api_call('SetSpriteColor', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'sprite_color', rgb)
            except Exception:
                pass

    def _safe_set_sprite_gray(self, path, gray, control=None):
        gray_value = bool(gray)
        if self._get_cached_native_prop(path, 'sprite_gray') == gray_value:
            return
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteGray"):
            try:
                start_time = _perf_now()
                image_control.SetSpriteGray(gray_value)
                self._count_native_api_call('SetSpriteGray', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'sprite_gray', gray_value)
            except Exception:
                pass

    def _safe_set_sprite_clip_ratio(self, path, ratio, control=None):
        image_control = self._to_image_control(control, path)
        if not image_control or not hasattr(image_control, "SetSpriteClipRatio"):
            return

        r = self._to_float(ratio, 0.0)
        if r < 0.0:
            r = 0.0
        if r > 1.0:
            r = 1.0
        try:
            start_time = _perf_now()
            image_control.SetSpriteClipRatio(r)
            self._count_native_api_call('SetSpriteClipRatio', elapsed_ms=(_perf_now() - start_time) * 1000.0)
        except Exception:
            pass

    def _safe_set_sprite_uv(self, path, uv, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteUV"):
            try:
                start_time = _perf_now()
                image_control.SetSpriteUV(uv)
                self._count_native_api_call('SetSpriteUV', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            except Exception:
                pass

    def _safe_set_sprite_uv_size(self, path, uv_size, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteUVSize"):
            try:
                start_time = _perf_now()
                image_control.SetSpriteUVSize(uv_size)
                self._count_native_api_call('SetSpriteUVSize', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            except Exception:
                pass

    def _safe_set_ui_item(self, path, identifier, aux_value, is_enchanted=False, user_data=None, control=None):
        item_name = self._safe_text(identifier)
        if not item_name:
            return False

        try:
            aux_number = int(aux_value)
        except Exception:
            aux_number = 0

        enchant_flag = self._to_bool(is_enchanted)
        payload_user_data = user_data
        if isinstance(payload_user_data, dict) and not payload_user_data:
            payload_user_data = None

        item_control = self._to_item_renderer_control(control, path)
        if item_control and hasattr(item_control, 'SetUiItem'):
            try:
                start_time = _perf_now()
                ok = item_control.SetUiItem(item_name, aux_number, enchant_flag, payload_user_data) is not False
                self._count_native_api_call('SetUiItem', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                return ok
            except Exception:
                pass

        try:
            start_time = _perf_now()
            ok = self._screen.SetUiItem(path, item_name, aux_number, enchant_flag, payload_user_data) is not False
            self._count_native_api_call('SetUiItem', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            return ok
        except Exception:
            return False

    def _safe_set_image_adaption_type(self, path, adaption_type, adaption_data=None, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetImageAdaptionType"):
            try:
                start_time = _perf_now()
                image_control.SetImageAdaptionType(adaption_type, adaption_data)
                self._count_native_api_call('SetImageAdaptionType', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            except Exception:
                pass

    def _safe_rotate(self, path, angle, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "Rotate"):
            try:
                start_time = _perf_now()
                image_control.Rotate(angle)
                self._count_native_api_call('Rotate', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            except Exception:
                pass

    def _safe_set_rotate_pivot(self, path, pivot, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetRotatePivot"):
            try:
                start_time = _perf_now()
                image_control.SetRotatePivot(pivot)
                self._count_native_api_call('SetRotatePivot', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            except Exception:
                pass

    def _to_image_control(self, control, path):
        if control and hasattr(control, "asImage"):
            try:
                image_control = control.asImage()
                if image_control:
                    return image_control
            except Exception:
                pass

        try:
            base_control = self._screen.GetBaseUIControl(path)
            if base_control and hasattr(base_control, "asImage"):
                return base_control.asImage()
        except Exception:
            pass
        return None

    def _to_item_renderer_control(self, control, path):
        if control and hasattr(control, 'asItemRenderer'):
            try:
                item_control = control.asItemRenderer()
                if item_control:
                    return item_control
            except Exception:
                pass

        try:
            base_control = self._screen.GetBaseUIControl(path)
            if base_control and hasattr(base_control, 'asItemRenderer'):
                return base_control.asItemRenderer()
        except Exception:
            pass
        return None

    def _to_label_control(self, control, path):
        if control and hasattr(control, "asLabel"):
            try:
                label_control = control.asLabel()
                if label_control:
                    return label_control
            except Exception:
                pass

        try:
            base_control = self._screen.GetBaseUIControl(path)
            if base_control and hasattr(base_control, "asLabel"):
                return base_control.asLabel()
        except Exception:
            pass
        return None

    def _safe_set_text_color(self, path, color, control=None):
        rgb = self._to_rgb_tuple(color)
        if rgb is None:
            return
        if self._get_cached_native_prop(path, 'text_color') == rgb:
            return

        if control and hasattr(control, "asLabel"):
            try:
                label_control = control.asLabel()
                if label_control and hasattr(label_control, "SetTextColor"):
                    start_time = _perf_now()
                    label_control.SetTextColor(rgb)
                    self._count_native_api_call('SetTextColor', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    self._set_cached_native_prop(path, 'text_color', rgb)
                    return
            except Exception:
                pass

        if control and hasattr(control, "SetTextColor"):
            try:
                start_time = _perf_now()
                control.SetTextColor(rgb)
                self._count_native_api_call('SetTextColor', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text_color', rgb)
                return
            except Exception:
                pass

        try:
            if hasattr(self._screen, "SetTextColor"):
                rgba = (rgb[0], rgb[1], rgb[2], 1.0)
                start_time = _perf_now()
                self._screen.SetTextColor(path, rgba)
                self._count_native_api_call('SetTextColor', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text_color', rgb)
        except Exception:
            pass

    def _safe_set_text_font_size(self, path, scale, control=None):
        scale_value = self._to_float(scale, 1.0)
        if self._get_cached_native_prop(path, 'text_font_size') == scale_value:
            return
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextFontSize"):
            try:
                start_time = _perf_now()
                label_control.SetTextFontSize(scale_value)
                self._count_native_api_call('SetTextFontSize', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text_font_size', scale_value)
            except Exception:
                pass

    def _safe_set_text_alignment(self, path, alignment, control=None):
        alignment_value = self._safe_text(alignment)
        if self._get_cached_native_prop(path, 'text_alignment') == alignment_value:
            return
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextAlignment"):
            try:
                start_time = _perf_now()
                label_control.SetTextAlignment(alignment_value)
                self._count_native_api_call('SetTextAlignment', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text_alignment', alignment_value)
            except Exception:
                pass

    def _safe_set_text_line_padding(self, path, text_line_padding, control=None):
        padding_value = self._to_float(text_line_padding, 0.0)
        if self._get_cached_native_prop(path, 'text_line_padding') == padding_value:
            return
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextLinePadding"):
            try:
                start_time = _perf_now()
                label_control.SetTextLinePadding(padding_value)
                self._count_native_api_call('SetTextLinePadding', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text_line_padding', padding_value)
            except Exception:
                pass

    def _safe_set_text_shadow(self, path, enabled, control=None):
        shadow_enabled = bool(enabled)
        if self._get_cached_native_prop(path, 'text_shadow') == shadow_enabled:
            return
        label_control = self._to_label_control(control, path)
        if not label_control:
            return
        try:
            if shadow_enabled and hasattr(label_control, "EnableTextShadow"):
                start_time = _perf_now()
                label_control.EnableTextShadow()
                self._count_native_api_call('EnableTextShadow', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text_shadow', shadow_enabled)
            elif (not shadow_enabled) and hasattr(label_control, "DisableTextShadow"):
                start_time = _perf_now()
                label_control.DisableTextShadow()
                self._count_native_api_call('DisableTextShadow', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'text_shadow', shadow_enabled)
        except Exception:
            pass

    def _safe_set_position(self, path, x, y, control=None):
        try:
            pos = (int(round(x)), int(round(y)))
            safe_path, cache_entry = self._get_native_layout_cache_entry(path)
            if cache_entry is not None and cache_entry.get('position') == pos:
                return
            if control:
                used_full = False
                if hasattr(control, "SetFullPosition"):
                    start_time = _perf_now()
                    ret_x = control.SetFullPosition(axis="x", paramDict={"absoluteValue": float(pos[0]), "followType": "none", "relativeValue": 0.0})
                    ret_y = control.SetFullPosition(axis="y", paramDict={"absoluteValue": float(pos[1]), "followType": "none", "relativeValue": 0.0})
                    used_full = bool(ret_x) and bool(ret_y)
                    if used_full:
                        self._count_native_api_call('SetFullPosition', 2, elapsed_ms=(_perf_now() - start_time) * 1000.0)

                if hasattr(control, "SetPosition"):
                    try:
                        start_time = _perf_now()
                        control.SetPosition(pos)
                        if not used_full:
                            self._count_native_api_call('SetPosition', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    except TypeError:
                        start_time = _perf_now()
                        control.SetPosition(float(pos[0]), float(pos[1]))
                        if not used_full:
                            self._count_native_api_call('SetPosition', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    except Exception:
                        if not used_full:
                            raise
                if cache_entry is not None:
                    cache_entry['position'] = pos
                return
            start_time = _perf_now()
            self._screen.SetPosition(path, pos)
            self._count_native_api_call('SetPosition', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            if cache_entry is not None:
                cache_entry['position'] = pos
        except Exception:
            pass

    def _safe_set_size(self, path, w, h, control=None):
        try:
            width = int(round(w))
            height = int(round(h))
            if width < 0:
                width = 0
            if height < 0:
                height = 0
            size = (width, height)
            safe_path, cache_entry = self._get_native_layout_cache_entry(path)
            if cache_entry is not None and cache_entry.get('size') == size:
                return
            if control:
                used_full = False
                if hasattr(control, "SetFullSize"):
                    start_time = _perf_now()
                    ret_w = control.SetFullSize(axis="x", paramDict={"absoluteValue": float(size[0]), "followType": "none", "relativeValue": 0.0})
                    ret_h = control.SetFullSize(axis="y", paramDict={"absoluteValue": float(size[1]), "followType": "none", "relativeValue": 0.0})
                    used_full = bool(ret_w) and bool(ret_h)
                    if used_full:
                        self._count_native_api_call('SetFullSize', 2, elapsed_ms=(_perf_now() - start_time) * 1000.0)

                if hasattr(control, "SetSize"):
                    try:
                        start_time = _perf_now()
                        control.SetSize(size, True)
                        if not used_full:
                            self._count_native_api_call('SetSize', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    except TypeError:
                        start_time = _perf_now()
                        control.SetSize(size)
                        if not used_full:
                            self._count_native_api_call('SetSize', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    except Exception:
                        if not used_full:
                            raise
                if cache_entry is not None:
                    cache_entry['size'] = size
                return
            start_time = _perf_now()
            self._screen.SetSize(path, size, True)
            self._count_native_api_call('SetSize', elapsed_ms=(_perf_now() - start_time) * 1000.0)
            if cache_entry is not None:
                cache_entry['size'] = size
        except Exception:
            pass

    def _safe_set_visible(self, path, visible, control=None, sync_refresh=None):
        visible_value = bool(visible)
        if self._get_cached_native_prop(path, 'visible') == visible_value:
            return

        requested_sync_refresh = sync_refresh
        if requested_sync_refresh is None:
            requested_sync_refresh = False
        requested_sync_refresh = bool(requested_sync_refresh)

        try:
            if control and hasattr(control, "SetVisible"):
                start_time = _perf_now()
                control.SetVisible(visible_value, requested_sync_refresh)
                self._count_native_api_call('SetVisible', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'visible', visible_value)
                if not requested_sync_refresh:
                    self._request_screen_refresh(sync_refresh=False)
                return
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetVisible"):
                start_time = _perf_now()
                base.SetVisible(visible_value, requested_sync_refresh)
                self._count_native_api_call('SetVisible', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'visible', visible_value)
                if not requested_sync_refresh:
                    self._request_screen_refresh(sync_refresh=False)
        except Exception:
            try:
                if control and hasattr(control, "SetVisible"):
                    start_time = _perf_now()
                    control.SetVisible(visible_value)
                    self._count_native_api_call('SetVisible', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    self._set_cached_native_prop(path, 'visible', visible_value)
                    return
                base = self._screen.GetBaseUIControl(path)
                if base and hasattr(base, "SetVisible"):
                    start_time = _perf_now()
                    base.SetVisible(visible_value)
                    self._count_native_api_call('SetVisible', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                    self._set_cached_native_prop(path, 'visible', visible_value)
            except Exception:
                pass

    def _safe_set_alpha(self, path, alpha, control=None):
        alpha_value = self._to_float(alpha, 1.0)
        if self._get_cached_native_prop(path, 'alpha') == alpha_value:
            return
        try:
            if control and hasattr(control, "SetAlpha"):
                start_time = _perf_now()
                control.SetAlpha(alpha_value)
                self._count_native_api_call('SetAlpha', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'alpha', alpha_value)
                return
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetAlpha"):
                start_time = _perf_now()
                base.SetAlpha(alpha_value)
                self._count_native_api_call('SetAlpha', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'alpha', alpha_value)
        except Exception:
            pass

    def _safe_set_layer(self, path, layer, control=None, sync_refresh=None, force_update=None):
        try:
            layer_value = int(round(self._to_float(layer, 0.0)))
        except Exception:
            return
        if self._get_cached_native_prop(path, 'layer') == layer_value:
            return

        use_three_args = sync_refresh is not None or force_update is not None
        if use_three_args:
            sync_val = bool(sync_refresh) if sync_refresh is not None else False
            force_val = bool(force_update) if force_update is not None else False
            if sync_val or force_val:
                try:
                    print('=====> PyreactRuntime[warn] SetLayer触发强制刷新: path=%s layer=%s syncRefresh=%s forceUpdate=%s <=====' % (
                        self._safe_text(path),
                        layer_value,
                        sync_val,
                        force_val,
                    ))
                except Exception:
                    pass

        try:
            if control and hasattr(control, "SetLayer"):
                start_time = _perf_now()
                if use_three_args:
                    control.SetLayer(layer_value, sync_val, force_val)
                else:
                    control.SetLayer(layer_value)
                self._count_native_api_call('SetLayer', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'layer', layer_value)
                return
        except Exception:
            if not use_three_args:
                pass
            else:
                try:
                    if control and hasattr(control, "SetLayer"):
                        start_time = _perf_now()
                        control.SetLayer(layer_value)
                        self._count_native_api_call('SetLayer', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                        self._set_cached_native_prop(path, 'layer', layer_value)
                        return
                except Exception:
                    pass

        try:
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetLayer"):
                start_time = _perf_now()
                if use_three_args:
                    base.SetLayer(layer_value, sync_val, force_val)
                else:
                    base.SetLayer(layer_value)
                self._count_native_api_call('SetLayer', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'layer', layer_value)
                return
        except Exception:
            if not use_three_args:
                pass
            else:
                try:
                    base = self._screen.GetBaseUIControl(path)
                    if base and hasattr(base, "SetLayer"):
                        start_time = _perf_now()
                        base.SetLayer(layer_value)
                        self._count_native_api_call('SetLayer', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                        self._set_cached_native_prop(path, 'layer', layer_value)
                        return
                except Exception:
                    pass

        try:
            if hasattr(self._screen, "SetLayer"):
                start_time = _perf_now()
                self._screen.SetLayer(path, layer_value)
                self._count_native_api_call('SetLayer', elapsed_ms=(_perf_now() - start_time) * 1000.0)
                self._set_cached_native_prop(path, 'layer', layer_value)
        except Exception:
            pass

    def _to_float(self, value, fallback):
        try:
            return float(value)
        except Exception:
            return float(fallback)

    def _parse_text_color(self, value):
        if not isinstance(value, Color):
            return None
        return value

    def _parse_text_font_size(self, value):
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text_value = self._safe_text(value).strip()
        if not text_value:
            return None

        try:
            return float(text_value)
        except Exception:
            return None

    def _parse_text_font_scale(self, value):
        font_size = self._parse_text_font_size(value)
        if font_size is None:
            return None

        base = self._TEXT_FONT_SIZE_BASE
        if base <= 0.0:
            return None

        return font_size / base

    def _parse_text_alignment(self, value):
        text_value = self._safe_text(value).strip().lower()
        if text_value in ("left", "start"):
            return "left"
        if text_value in ("right", "end"):
            return "right"
        if text_value in ("center", "middle"):
            return "center"
        return None

    def _parse_line_padding(self, value):
        if value is None or isinstance(value, bool):
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _to_rgb_tuple(self, color):
        if not isinstance(color, Color):
            return None
        return color.toRGBUnitTuple()

    def _parse_vec2(self, value):
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            return None
        return (
            self._to_float(value[0], 0.0),
            self._to_float(value[1], 0.0),
        )

    def _parse_vec4(self, value):
        if not isinstance(value, (list, tuple)) or len(value) < 4:
            return None
        return (
            self._to_float(value[0], 0.0),
            self._to_float(value[1], 0.0),
            self._to_float(value[2], 0.0),
            self._to_float(value[3], 0.0),
        )

    def _parse_image_adaption_type(self, style):
        if not isinstance(style, dict):
            return None

        explicit = self._safe_text(style.get("imageAdaptionType", "")).strip()
        if explicit in ("normal", "filled", "oldNineSlice", "originNineSlice"):
            return explicit

        resize_mode = self._safe_text(style.get("resizeMode", "")).strip().lower()
        if resize_mode in ("contain", "center"):
            return "normal"
        if resize_mode in ("cover", "stretch"):
            return "filled"
        return None

    def _to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        text = self._safe_text(value).strip().lower()
        return text in ("1", "true", "yes", "on")

    def _safe_text(self, value):
        if value is None:
            return ""
        try:
            # Prefer preserving unicode returned by engine APIs (e.g. edit_box).
            # The UI native layer typically expects UTF-8 encoded bytes in Py2.
            if isinstance(value, str):
                return value
            if isinstance(value, _UNICODE_TYPE):
                try:
                    return value.encode('utf-8')
                except Exception:
                    try:
                        return value.encode('utf-8', 'ignore')
                    except Exception:
                        return ""

            return "%s" % value
        except Exception:
            return ""
