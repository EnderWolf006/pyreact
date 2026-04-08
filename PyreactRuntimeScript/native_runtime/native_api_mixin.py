# -*- coding: utf-8 -*-

from pyreact.components.color import Color


try:
    _UNICODE_TYPE = unicode
except NameError:
    # Python3 fallback for local tooling; runtime is Python2 in-game.
    _UNICODE_TYPE = str


class RuntimeNativeApiMixin(object):
    _TEXT_FONT_SIZE_BASE = 10.0
    _NATIVE_PROP_DEFAULT = object()

    def _reset_native_api_call_counts(self):
        self._native_api_call_counts = {}

    def _count_native_api_call(self, api_name, count=1):
        if not getattr(self, '_native_api_counting_active', False):
            return
        safe_name = self._safe_text(api_name)
        if not safe_name:
            return
        counts = getattr(self, '_native_api_call_counts', None)
        if not isinstance(counts, dict):
            counts = {}
            self._native_api_call_counts = counts
        counts[safe_name] = counts.get(safe_name, 0) + int(count)

    def _log_native_api_call_counts(self):
        if not getattr(self, '_log_perf', False):
            return
        counts = getattr(self, '_native_api_call_counts', None)
        if not isinstance(counts, dict) or not counts:
            return
        try:
            print('=====> PyreactRuntime[perf] 原生接口调用统计: <=====')
            items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            for api_name, call_count in items:
                print('=====> PyreactRuntime[perf]   %s: %s <=====' % (api_name, call_count))
        except Exception:
            pass

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
                control.SetVisible(True)
                self._count_native_api_call('SetVisible')
        except Exception:
            pass
        try:
            if hasattr(control, "SetAlpha"):
                control.SetAlpha(0.0)
                self._count_native_api_call('SetAlpha')
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

    def _get_native_prop_cache(self):
        cache = getattr(self, '_native_prop_cache', None)
        if not isinstance(cache, dict):
            cache = {}
            self._native_prop_cache = cache
        return cache

    def _drop_native_prop_cache(self, path_prefix=None):
        cache = self._get_native_prop_cache()
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

    def _get_native_path_cache_entry(self, path):
        cache = self._get_native_prop_cache()
        entry = cache.get(path)
        if not isinstance(entry, dict):
            entry = {}
            cache[path] = entry
        return entry

    def _should_apply_native_prop(self, path, cache_key, value, default_value=_NATIVE_PROP_DEFAULT):
        entry = self._get_native_path_cache_entry(path)
        if entry.get(cache_key, self._NATIVE_PROP_DEFAULT) == value:
            return False
        return True

    def _remember_native_prop(self, path, cache_key, value):
        entry = self._get_native_path_cache_entry(path)
        entry[cache_key] = value

    def _begin_native_update_batch(self):
        self._reset_native_api_call_counts()
        self._native_api_counting_active = bool(getattr(self, '_log_perf', False))
        self._native_update_batch_active = True
        self._native_update_batch_dirty = False

    def _mark_native_update_dirty(self):
        if getattr(self, '_native_update_batch_active', False):
            self._native_update_batch_dirty = True

    def _flush_native_update_batch(self):
        should_flush = bool(getattr(self, '_native_update_batch_active', False) and getattr(self, '_native_update_batch_dirty', False))
        self._native_update_batch_active = False
        self._native_update_batch_dirty = False
        try:
            if should_flush and hasattr(self._screen, 'UpdateScreen'):
                self._screen.UpdateScreen(True)
                self._count_native_api_call('UpdateScreen')
        except Exception:
            pass
        try:
            self._log_native_api_call_counts()
        finally:
            self._native_api_counting_active = False

    def _safe_set_text(self, path, text, control=None):
        text_value = self._safe_text(text)
        if not self._should_apply_native_prop(path, 'text', text_value, ''):
            return
        try:
            if control and hasattr(control, "SetText"):
                try:
                    control.SetText(text_value+"1", True)
                    control.SetText(text_value, True)
                    self._count_native_api_call('SetText', 2)
                except TypeError:
                    control.SetText(text_value+"1")
                    control.SetText(text_value)
                    self._count_native_api_call('SetText', 2)
                self._remember_native_prop(path, 'text', text_value)
                return
            try:
                control.asLabel().SetText(text_value+"1", True)
                control.asLabel().SetText(text_value, True)
                self._count_native_api_call('SetText', 2)
            except TypeError:
                control.asLabel().SetText(text_value+"1")
                control.asLabel().SetText(text_value)
                self._count_native_api_call('SetText', 2)
            self._remember_native_prop(path, 'text', text_value)
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
        text_value = self._safe_text(text)
        if not self._should_apply_native_prop(path, 'editText', text_value, ''):
            return True
        te = self._to_text_edit_box_control(control, path)
        if not te:
            return False
        try:
            te.SetEditText(text_value)
            self._count_native_api_call('SetEditText')
            self._remember_native_prop(path, 'editText', text_value)
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
        if not self._should_apply_native_prop(path, 'editMaxLength', max_len):
            return True
        try:
            te.SetEditTextMaxLength(max_len)
            self._count_native_api_call('SetEditTextMaxLength')
            self._remember_native_prop(path, 'editMaxLength', max_len)
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

    def _safe_set_sprite(self, path, sprite, control=None):
        sprite_text = self._safe_text(sprite)
        if not sprite_text:
            return False
        if not self._should_apply_native_prop(path, 'sprite', sprite_text, self._DEFAULT_WHITE_TEXTURE):
            return True

        if control and hasattr(control, "asImage"):
            try:
                image_control = control.asImage()
                if image_control and hasattr(image_control, "SetSprite"):
                    ret = image_control.SetSprite(sprite_text)
                    self._count_native_api_call('SetSprite')
                    if ret is not False:
                        self._remember_native_prop(path, 'sprite', sprite_text)
                    return ret is not False
            except Exception:
                pass

        if control and hasattr(control, "SetSprite"):
            try:
                ret = control.SetSprite(sprite_text)
                self._count_native_api_call('SetSprite')
                if ret is not False:
                    self._remember_native_prop(path, 'sprite', sprite_text)
                return ret is not False
            except Exception:
                pass

        return False

    def _safe_set_sprite_color(self, path, color, control=None):
        rgb = self._to_rgb_tuple(color)
        if rgb is None:
            return
        if not self._should_apply_native_prop(path, 'spriteColor', rgb):
            return

        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteColor"):
            try:
                image_control.SetSpriteColor(rgb)
                self._count_native_api_call('SetSpriteColor')
                self._remember_native_prop(path, 'spriteColor', rgb)
            except Exception:
                pass

    def _safe_set_sprite_gray(self, path, gray, control=None):
        gray_value = bool(gray)
        if not self._should_apply_native_prop(path, 'spriteGray', gray_value, False):
            return
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteGray"):
            try:
                image_control.SetSpriteGray(gray_value)
                self._count_native_api_call('SetSpriteGray')
                self._remember_native_prop(path, 'spriteGray', gray_value)
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
        if not self._should_apply_native_prop(path, 'spriteClipRatio', r):
            return
        try:
            image_control.SetSpriteClipRatio(r)
            self._count_native_api_call('SetSpriteClipRatio')
            self._remember_native_prop(path, 'spriteClipRatio', r)
        except Exception:
            pass

    def _safe_set_sprite_uv(self, path, uv, control=None):
        if not self._should_apply_native_prop(path, 'spriteUV', uv):
            return
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteUV"):
            try:
                image_control.SetSpriteUV(uv)
                self._count_native_api_call('SetSpriteUV')
                self._remember_native_prop(path, 'spriteUV', uv)
            except Exception:
                pass

    def _safe_set_sprite_uv_size(self, path, uv_size, control=None):
        if not self._should_apply_native_prop(path, 'spriteUVSize', uv_size):
            return
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteUVSize"):
            try:
                image_control.SetSpriteUVSize(uv_size)
                self._count_native_api_call('SetSpriteUVSize')
                self._remember_native_prop(path, 'spriteUVSize', uv_size)
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
        cache_value = (item_name, aux_number, enchant_flag, payload_user_data)
        if not self._should_apply_native_prop(path, 'uiItem', cache_value):
            return True

        item_control = self._to_item_renderer_control(control, path)
        if item_control and hasattr(item_control, 'SetUiItem'):
            try:
                ok = item_control.SetUiItem(item_name, aux_number, enchant_flag, payload_user_data) is not False
                self._count_native_api_call('SetUiItem')
                if ok:
                    self._remember_native_prop(path, 'uiItem', cache_value)
                return ok
            except Exception:
                pass

        try:
            ok = self._screen.SetUiItem(path, item_name, aux_number, enchant_flag, payload_user_data) is not False
            self._count_native_api_call('SetUiItem')
            if ok:
                self._remember_native_prop(path, 'uiItem', cache_value)
            return ok
        except Exception:
            return False

    def _safe_set_image_adaption_type(self, path, adaption_type, adaption_data=None, control=None):
        image_control = self._to_image_control(control, path)
        cache_value = (adaption_type, adaption_data)
        if not self._should_apply_native_prop(path, 'imageAdaptionType', cache_value):
            return
        if image_control and hasattr(image_control, "SetImageAdaptionType"):
            try:
                image_control.SetImageAdaptionType(adaption_type, adaption_data)
                self._count_native_api_call('SetImageAdaptionType')
                self._remember_native_prop(path, 'imageAdaptionType', cache_value)
            except Exception:
                pass

    def _safe_rotate(self, path, angle, control=None):
        angle_value = self._to_float(angle, 0.0)
        if not self._should_apply_native_prop(path, 'rotation', angle_value, 0.0):
            return
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "Rotate"):
            try:
                image_control.Rotate(angle_value)
                self._count_native_api_call('Rotate')
                self._remember_native_prop(path, 'rotation', angle_value)
            except Exception:
                pass

    def _safe_set_rotate_pivot(self, path, pivot, control=None):
        if not self._should_apply_native_prop(path, 'rotatePivot', pivot):
            return
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetRotatePivot"):
            try:
                image_control.SetRotatePivot(pivot)
                self._count_native_api_call('SetRotatePivot')
                self._remember_native_prop(path, 'rotatePivot', pivot)
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
        if not self._should_apply_native_prop(path, 'textColor', rgb):
            return

        if control and hasattr(control, "asLabel"):
            try:
                label_control = control.asLabel()
                if label_control and hasattr(label_control, "SetTextColor"):
                    label_control.SetTextColor(rgb)
                    self._count_native_api_call('SetTextColor')
                    self._remember_native_prop(path, 'textColor', rgb)
                    return
            except Exception:
                pass

        if control and hasattr(control, "SetTextColor"):
            try:
                control.SetTextColor(rgb)
                self._count_native_api_call('SetTextColor')
                self._remember_native_prop(path, 'textColor', rgb)
                return
            except Exception:
                pass

        try:
            if hasattr(self._screen, "SetTextColor"):
                rgba = (rgb[0], rgb[1], rgb[2], 1.0)
                self._screen.SetTextColor(path, rgba)
                self._count_native_api_call('SetTextColor')
                self._remember_native_prop(path, 'textColor', rgb)
        except Exception:
            pass

    def _safe_set_text_font_size(self, path, scale, control=None):
        scale_value = self._to_float(scale, 1.0)
        if not self._should_apply_native_prop(path, 'textFontSize', scale_value, 1.0):
            return
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextFontSize"):
            try:
                label_control.SetTextFontSize(scale_value)
                self._count_native_api_call('SetTextFontSize')
                self._remember_native_prop(path, 'textFontSize', scale_value)
            except Exception:
                pass

    def _safe_set_text_alignment(self, path, alignment, control=None):
        alignment_value = self._safe_text(alignment).strip().lower() or 'left'
        if not self._should_apply_native_prop(path, 'textAlignment', alignment_value, 'left'):
            return
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextAlignment"):
            try:
                label_control.SetTextAlignment(alignment_value)
                self._count_native_api_call('SetTextAlignment')
                self._remember_native_prop(path, 'textAlignment', alignment_value)
            except Exception:
                pass

    def _safe_set_text_line_padding(self, path, text_line_padding, control=None):
        line_padding_value = self._to_float(text_line_padding, 0.0)
        if not self._should_apply_native_prop(path, 'textLinePadding', line_padding_value, 0.0):
            return
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextLinePadding"):
            try:
                label_control.SetTextLinePadding(line_padding_value)
                self._count_native_api_call('SetTextLinePadding')
                self._remember_native_prop(path, 'textLinePadding', line_padding_value)
            except Exception:
                pass

    def _safe_set_text_shadow(self, path, enabled, control=None):
        enabled_value = bool(enabled)
        if not self._should_apply_native_prop(path, 'textShadow', enabled_value, False):
            return
        label_control = self._to_label_control(control, path)
        if not label_control:
            return
        try:
            if enabled_value and hasattr(label_control, "EnableTextShadow"):
                label_control.EnableTextShadow()
                self._count_native_api_call('EnableTextShadow')
            elif (not enabled_value) and hasattr(label_control, "DisableTextShadow"):
                label_control.DisableTextShadow()
                self._count_native_api_call('DisableTextShadow')
            self._remember_native_prop(path, 'textShadow', enabled_value)
        except Exception:
            pass

    def _safe_set_position(self, path, x, y, control=None):
        try:
            pos = (int(round(x)), int(round(y)))
            if not self._should_apply_native_prop(path, 'position', pos):
                return
            if control:
                applied = False
                used_full = False
                if hasattr(control, "SetFullPosition"):
                    try:
                        control.SetFullPosition(axis="x", paramDict={"absoluteValue": float(pos[0]), "followType": "none", "relativeValue": 0.0})
                        control.SetFullPosition(axis="y", paramDict={"absoluteValue": float(pos[1]), "followType": "none", "relativeValue": 0.0})
                        self._count_native_api_call('SetFullPosition', 2)
                        used_full = True
                        applied = True
                    except Exception:
                        used_full = False

                if (not used_full) and hasattr(control, "SetPosition"):
                    try:
                        control.SetPosition(pos)
                        self._count_native_api_call('SetPosition')
                        applied = True
                    except TypeError:
                        control.SetPosition(float(pos[0]), float(pos[1]))
                        self._count_native_api_call('SetPosition')
                        applied = True
                if applied:
                    self._remember_native_prop(path, 'position', pos)
                return
            self._screen.SetPosition(path, pos)
            self._count_native_api_call('SetPosition')
            self._remember_native_prop(path, 'position', pos)
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
            if not self._should_apply_native_prop(path, 'size', size):
                return
            if control:
                applied = False
                used_full = False
                if hasattr(control, "SetFullSize"):
                    try:
                        control.SetFullSize(axis="x", paramDict={"absoluteValue": float(size[0]), "followType": "none", "relativeValue": 0.0})
                        control.SetFullSize(axis="y", paramDict={"absoluteValue": float(size[1]), "followType": "none", "relativeValue": 0.0})
                        self._count_native_api_call('SetFullSize', 2)
                        used_full = True
                        applied = True
                    except Exception:
                        used_full = False

                if (not used_full) and hasattr(control, "SetSize"):
                    try:
                        control.SetSize(size, True)
                        self._count_native_api_call('SetSize')
                        applied = True
                    except TypeError:
                        control.SetSize(size)
                        self._count_native_api_call('SetSize')
                        applied = True
                if applied:
                    self._remember_native_prop(path, 'size', size)
                return
            self._screen.SetSize(path, size, True)
            self._count_native_api_call('SetSize')
            self._remember_native_prop(path, 'size', size)
        except Exception:
            pass

    def _safe_set_visible(self, path, visible, control=None):
        visible_value = bool(visible)
        if not self._should_apply_native_prop(path, 'visible', visible_value, True):
            return
        try:
            is_batching = bool(getattr(self, '_native_update_batch_active', False))
            if control and hasattr(control, "SetVisible"):
                if is_batching:
                    control.SetVisible(visible_value, False)
                    self._count_native_api_call('SetVisible')
                    self._mark_native_update_dirty()
                else:
                    control.SetVisible(visible_value)
                    self._count_native_api_call('SetVisible')
                self._remember_native_prop(path, 'visible', visible_value)
                return
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetVisible"):
                if is_batching:
                    base.SetVisible(visible_value, False)
                    self._count_native_api_call('SetVisible')
                    self._mark_native_update_dirty()
                else:
                    base.SetVisible(visible_value)
                    self._count_native_api_call('SetVisible')
                self._remember_native_prop(path, 'visible', visible_value)
        except Exception:
            pass

    def _safe_set_alpha(self, path, alpha, control=None):
        alpha_value = float(alpha)
        if not self._should_apply_native_prop(path, 'alpha', alpha_value, 1.0):
            return
        try:
            if control and hasattr(control, "SetAlpha"):
                control.SetAlpha(alpha_value)
                self._count_native_api_call('SetAlpha')
                self._remember_native_prop(path, 'alpha', alpha_value)
                return
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetAlpha"):
                base.SetAlpha(alpha_value)
                self._count_native_api_call('SetAlpha')
                self._remember_native_prop(path, 'alpha', alpha_value)
        except Exception:
            pass

    def _safe_set_layer(self, path, layer, control=None):
        try:
            layer_value = int(round(self._to_float(layer, 0.0)))
        except Exception:
            return
        if not self._should_apply_native_prop(path, 'layer', layer_value, 0):
            return

        try:
            is_batching = bool(getattr(self, '_native_update_batch_active', False))
            if control and hasattr(control, "SetLayer"):
                if is_batching:
                    control.SetLayer(layer_value, False, False)
                    self._count_native_api_call('SetLayer')
                    self._mark_native_update_dirty()
                else:
                    control.SetLayer(layer_value)
                    self._count_native_api_call('SetLayer')
                self._remember_native_prop(path, 'layer', layer_value)
                return
        except Exception:
            pass

        try:
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetLayer"):
                if is_batching:
                    base.SetLayer(layer_value, False, False)
                    self._count_native_api_call('SetLayer')
                    self._mark_native_update_dirty()
                else:
                    base.SetLayer(layer_value)
                    self._count_native_api_call('SetLayer')
                self._remember_native_prop(path, 'layer', layer_value)
                return
        except Exception:
            pass

        try:
            if hasattr(self._screen, "SetLayer"):
                self._screen.SetLayer(path, layer_value)
                self._count_native_api_call('SetLayer')
                self._remember_native_prop(path, 'layer', layer_value)
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
